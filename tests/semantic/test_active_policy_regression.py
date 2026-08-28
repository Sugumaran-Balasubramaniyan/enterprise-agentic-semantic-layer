"""Semantic-version regression guard for the ActivePolicy subset."""

from pathlib import Path

from semantic_layer.registry import SemanticRegistry

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_active_policy_definition_and_rule_remain_semantically_aligned() -> None:
    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    concept = registry.concepts["insurance:ActivePolicy"]
    rule = registry.rules["insurance:ActivePolicy"]
    metric = registry.metrics["insurance:ActivePolicyCount"]

    assert concept.version == "1.0.0"
    assert rule.version == "1.0.0"
    assert metric.version == "1.0.0"
    assert concept.definition == "A policy whose governed lifecycle status is ACTIVE."
    assert rule.include_statuses == ["ACTIVE"]
    assert rule.exclude_statuses == ["LAPSED", "CANCELLED"]
    assert rule.predicate == "policy_status = 'ACTIVE'"
    assert metric.filter_rule == "insurance:ActivePolicy"
