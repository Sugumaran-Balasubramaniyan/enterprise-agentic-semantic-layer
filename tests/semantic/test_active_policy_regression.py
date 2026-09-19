"""Semantic-version regression guard for the ActiveSalesOrder subset."""

from pathlib import Path

from semantic_layer.registry import SemanticRegistry

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_active_policy_definition_and_rule_remain_semantically_aligned() -> None:
    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    concept = registry.concepts["sap:ActiveSalesOrder"]
    rule = registry.rules["sap:ActiveSalesOrder"]
    metric = registry.metrics["sap:ActiveSalesOrderCount"]

    assert concept.version == "1.0.0"
    assert rule.version == "1.0.0"
    assert metric.version == "1.0.0"
    assert concept.definition == "A sales order whose governed lifecycle status is RELEASED."
    assert rule.include_statuses == ["RELEASED"]
    assert rule.exclude_statuses == ["CLOSED", "CANCELLED"]
    assert rule.predicate == "order_status = 'RELEASED'"
    assert metric.filter_rule == "sap:ActiveSalesOrder"
