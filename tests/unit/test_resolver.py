"""Behavioural tests for deterministic business-language resolution."""

from pathlib import Path

from semantic_layer.registry import SemanticRegistry

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_resolver_grounds_car_insurance_in_canonical_concept() -> None:
    """Dropping synonym normalization must make this canonical grounding fail."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)

    resolution = registry.resolver.resolve("Find customers with car-insurance cover")

    assert "insurance:MotorInsurance" in resolution.concept_ids
    assert resolution.matched_terms["insurance:MotorInsurance"] == "car insurance"


def test_resolver_does_not_match_a_term_inside_an_unrelated_word() -> None:
    """Replacing token matching with substring matching must make this false positive fail."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)

    resolution = registry.resolve("The claimant is unrelated to this insurance product")

    assert "insurance:Claim" not in resolution.concept_ids
