"""Behavioural tests for governed logical query plans."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from semantic_layer.models import SemanticQueryPlan
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
