"""Behavioural tests for deterministic business-language resolution."""

from pathlib import Path

import pytest

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


def test_resolver_quarantines_an_unknown_mapping_target() -> None:
    """Trusting an unregistered mapping target must leak an ungrounded concept ID."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    registry.mappings["DatabricksFranceMapping"].normalization["products"]["MTR"] = (
        "insurance:UnknownLocalProduct"
    )

    resolution = registry.resolve("Find MTR customers")

    assert "insurance:UnknownLocalProduct" not in resolution.concept_ids
    assert "insurance:MotorInsurance" not in resolution.concept_ids


def test_resolver_quarantines_unregistered_local_extension_targets() -> None:
    """A forward-compatible local extension must not become a public canonical result."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)

    resolution = registry.resolve("Find HOME customers")

    assert "insurance:HomeInsurance" not in resolution.concept_ids


@pytest.mark.parametrize("local_value", ["MTR", "AUTO"])
def test_resolver_grounds_local_mapping_values_in_motor_insurance(local_value: str) -> None:
    """Ignoring mapping normalization must break local product grounding."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)

    resolution = registry.resolve(f"Find {local_value} customers")

    assert resolution.matched_terms["insurance:MotorInsurance"] == local_value.casefold()
