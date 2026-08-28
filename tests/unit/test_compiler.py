"""Behavioural tests for trusted physical-query compilation."""

from pathlib import Path

import pytest

from semantic_layer.adapters.cloud import CloudAdapterConfigurationError, DatabricksAdapter
from semantic_layer.compiler import DuckDBCompiler
from semantic_layer.governance import authorize
from semantic_layer.query_planner import build_plan
from semantic_layer.registry import SemanticRegistry

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_QUESTION = (
    "Find French motor-insurance customers with at least three qualifying claims "
    "in the last 12 months and total incurred loss above EUR 20,000."
)


def test_duckdb_compiler_uses_the_approved_claims_join_and_bound_parameters() -> None:
    """Replacing the trusted template with ungoverned joins or interpolation must fail."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    plan = build_plan(PRIMARY_QUESTION, role="ClaimsAnalystFR", registry=registry)
    authorization = authorize(plan, plan.caller, registry)

    compiled = DuckDBCompiler(registry).compile(plan, authorization, plan.caller)

    assert compiled.approved_products == ("Customer360", "PolicyMaster", "ClaimsAnalytics")
    assert "JOIN policies" in compiled.sql
    assert "JOIN claims" in compiled.sql
    assert "CANCELLED" not in compiled.sql
    assert "DUPLICATE" not in compiled.sql
    assert "?" in compiled.sql
    assert "FR" in compiled.parameters
    assert 3 in compiled.parameters
    assert 20000 in compiled.parameters


def test_compiler_rejects_a_plan_that_names_an_unapproved_product() -> None:
    """Skipping product validation must let a caller select an unreviewed source."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    plan = build_plan(PRIMARY_QUESTION, role="ClaimsAnalystFR", registry=registry)
    unapproved = plan.model_copy(update={"selected_products": ["Customer360", "Unapproved"]})
    authorization = authorize(unapproved, unapproved.caller, registry)

    with pytest.raises(ValueError, match="authorization|certified|approved"):
        DuckDBCompiler(registry).compile(unapproved, authorization, unapproved.caller)


def test_documented_cloud_adapter_fails_closed_without_configuration() -> None:
    """Replacing the documented cloud seam with a local fallback must conceal missing credentials."""

    with pytest.raises(CloudAdapterConfigurationError, match="credentials|configuration"):
        DatabricksAdapter().execute("SELECT 1")
