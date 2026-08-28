"""Behavioural tests for governed logical query plans."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from semantic_layer.models import SemanticQueryPlan, TimeContext
from semantic_layer.query_planner import build_plan
from semantic_layer.registry import SemanticRegistry

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_QUESTION = (
    "Find French motor-insurance customers with at least three qualifying claims "
    "in the last 12 months and total incurred loss above EUR 20,000."
)


def test_primary_question_produces_typed_governed_plan() -> None:
    """Dropping a governed metric, relationship, or product must fail this plan contract."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)

    plan = build_plan(PRIMARY_QUESTION, role="ClaimsAnalystFR", registry=registry)

    assert plan.root_entity == "insurance:Customer"
    assert [predicate.metric_id for predicate in plan.metric_predicates] == [
        "insurance:ClaimCount",
        "insurance:TotalIncurredLoss",
    ]
    assert [predicate.operator for predicate in plan.metric_predicates] == [">=", ">"]
    assert [predicate.value for predicate in plan.metric_predicates] == [3, 20000]
    assert plan.selected_products == ["Customer360", "PolicyMaster", "ClaimsAnalytics"]
    assert plan.time_context.window == "last_12_months"
    assert plan.caller.role == "ClaimsAnalystFR"
    assert [(path.source, path.target) for path in plan.relationships] == [
        ("insurance:Customer", "insurance:Policy"),
        ("insurance:Policy", "insurance:Claim"),
    ]


def test_active_policy_question_uses_current_year_and_never_carries_raw_sql() -> None:
    """Adding raw SQL or selecting claims products for this policy plan must fail."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)

    plan = build_plan(
        "Find French motor insurance customers with active policies in the current year.",
        role="ClaimsAnalystFR",
        registry=registry,
    )

    assert plan.metric_predicates[0].metric_id == "insurance:ActivePolicyCount"
    assert plan.selected_products == ["Customer360", "PolicyMaster"]
    assert plan.time_context.window == "current_year"
    with pytest.raises(ValidationError):
        SemanticQueryPlan.model_validate({"root_entity": "insurance:Customer", "sql": "SELECT 1"})


@pytest.mark.parametrize(
    "field, value",
    [
        ("root_entity", "insurance:Customer; SELECT customer_id FROM customers"),
        ("projected_dimensions", ["insurance:Customer", "SELECT customer_id FROM customers"]),
        (
            "filters",
            [
                {
                    "concept_id": "insurance:Country",
                    "operator": "=",
                    "value": "FR' OR 1=1 --",
                }
            ],
        ),
        (
            "metric_predicates",
            [
                {
                    "metric_id": "insurance:ClaimCount; DELETE FROM claims",
                    "operator": ">=",
                    "value": 3,
                }
            ],
        ),
    ],
)
def test_semantic_query_plan_rejects_sql_shaped_values_everywhere(field: str, value: object) -> None:
    """Removing recursive SQL validation must admit an executable payload."""

    plan = {
        "root_entity": "insurance:Customer",
        "projected_dimensions": ["insurance:Customer"],
        "filters": [{"concept_id": "insurance:Country", "operator": "=", "value": "FR"}],
        "metric_predicates": [
            {"metric_id": "insurance:ClaimCount", "operator": ">=", "value": 3}
        ],
        "caller": {"role": "ClaimsAnalystFR", "country": "FR"},
    }
    plan[field] = value

    with pytest.raises(ValidationError):
        SemanticQueryPlan.model_validate(plan)


@pytest.mark.parametrize(
    "field, value",
    [
        ("caller", {"role": "ClaimsAnalystFR", "country": "FR", "purpose": "PRAGMA database_list"}),
        ("target_platform", "ATTACH DATABASE 'untrusted.db' AS injected"),
        ("target_platform", "VACUUM"),
    ],
)
def test_semantic_query_plan_rejects_executable_text_in_remaining_plan_channels(
    field: str, value: object
) -> None:
    """Relaxing the plan enums must reopen an executable SQL text channel."""

    plan = {
        "root_entity": "insurance:Customer",
        "caller": {"role": "ClaimsAnalystFR", "country": "FR"},
    }
    plan[field] = value

    with pytest.raises(ValidationError):
        SemanticQueryPlan.model_validate(plan)


@pytest.mark.parametrize(
    "window, months",
    [("last_12_months", 11), ("current_year", 12)],
)
def test_time_context_rejects_inconsistent_window_state(window: str, months: int) -> None:
    """Removing the window invariant must allow ambiguous compiler inputs."""

    with pytest.raises(ValidationError):
        TimeContext(window=window, months=months)


def test_planner_uses_mapping_normalization_instead_of_product_name_literals() -> None:
    """Hard-coding MotorInsurance must hide a broken local mapping asset."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    registry.mappings["DatabricksFranceMapping"].normalization["products"]["MTR"] = "insurance:Claim"

    with pytest.raises(ValueError, match="insurance:MotorInsurance"):
        build_plan(PRIMARY_QUESTION.replace("motor-insurance", "MTR"), "ClaimsAnalystFR", registry)


def test_planner_rejects_an_asset_metric_with_an_uncertified_source_product() -> None:
    """Bypassing metric source-product validation must select a non-governed product."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    registry.metrics["insurance:ClaimCount"].source_products = ["UncertifiedClaims"]

    with pytest.raises(ValueError, match="UncertifiedClaims"):
        build_plan(PRIMARY_QUESTION, "ClaimsAnalystFR", registry)


def test_planner_parses_number_words_beyond_three() -> None:
    """Limiting grammar to the original word three must make this threshold wrong."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)

    plan = build_plan(
        PRIMARY_QUESTION.replace("at least three", "at least twelve"), "ClaimsAnalystFR", registry
    )

    assert plan.metric_predicates[0].value == 12
