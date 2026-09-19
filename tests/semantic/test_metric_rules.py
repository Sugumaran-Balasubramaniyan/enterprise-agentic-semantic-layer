"""Regression tests for metric and rule contracts."""

from pathlib import Path

from semantic_layer.registry import SemanticRegistry

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_metrics_reference_governed_rules_and_certified_products() -> None:
    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)

    for metric in registry.metrics.values():
        assert metric.version
        assert metric.filter_rule in registry.rules
        assert metric.source_products
        assert all(
            product in registry.products
            and registry.products[product].certification.status == "CERTIFIED"
            for product in metric.source_products
        )


def test_qualifying_claim_rule_excludes_cancelled_and_duplicate() -> None:
    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    rule = registry.rules["sap:QualifyingPosting"]

    assert set(rule.include_statuses) == {"POSTED", "CLEARED"}
    assert set(rule.exclude_statuses) == {"REVERSED", "DUPLICATE"}


def test_claims_ratio_preserves_independent_aggregate_contract() -> None:
    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    metric = registry.metrics["sap:CostRevenueRatio"]

    assert metric.aggregation == "ratio_of_aggregates"
    assert metric.numerator["product"] == "ACDOCAFinancials"
    assert metric.denominator["product"] == "BillingAnalytics"
    assert metric.alignment["pre_aggregate_each_product"] is True
    assert metric.alignment["join_multiplication"] == "forbidden"
