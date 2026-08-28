"""Behavioural tests for semantic query authorization."""

from pathlib import Path

from semantic_layer.governance import authorize
from semantic_layer.models import CallerContext, SemanticQueryPlan
from semantic_layer.query_planner import build_plan
from semantic_layer.registry import SemanticRegistry

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_QUESTION = (
    "Find French motor-insurance customers with at least three qualifying claims "
    "in the last 12 months and total incurred loss above EUR 20,000."
)


def test_fr_analyst_is_denied_non_fr_customer_data() -> None:
    """Removing country ABAC must let a French analyst cross a market boundary."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    plan = build_plan(PRIMARY_QUESTION, role="ClaimsAnalystFR", registry=registry)

    denied = authorize(plan.with_country("DE"), CallerContext(role="ClaimsAnalystFR"))

    assert denied.allowed is False
    assert denied.reason_code == "COUNTRY_SCOPE_DENIED"


def test_finance_analyst_cannot_request_customer_pii_but_can_request_aggregate_scope() -> None:
    """Dropping field classification checks must expose customer identifiers to finance."""

    plan = SemanticQueryPlan(
        root_entity="insurance:Customer",
        projected_dimensions=["insurance:Country"],
        selected_products=["PremiumAnalytics"],
        caller=CallerContext(role="FinanceAnalyst"),
    )
    finance = CallerContext(role="FinanceAnalyst")

    pii_denied = authorize(plan, finance, requested_fields=["customer_id"])
    aggregate_allowed = authorize(plan, finance, requested_fields=["country"])

    assert pii_denied.allowed is False
    assert pii_denied.reason_code == "PII_FIELD_DENIED"
    assert aggregate_allowed.allowed is True


def test_unknown_role_is_denied_by_default() -> None:
    """Changing default-deny policy must allow an unauthorised role into a plan."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    plan = build_plan(PRIMARY_QUESTION, role="ClaimsAnalystFR", registry=registry)

    decision = authorize(plan, CallerContext(role="UntrustedRole"))

    assert decision.allowed is False
    assert decision.reason_code == "ROLE_DENIED"
