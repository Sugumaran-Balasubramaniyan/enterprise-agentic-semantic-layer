"""Behavioural tests for deterministic business-language resolution."""

from pathlib import Path

import pytest

from semantic_layer.registry import SemanticRegistry

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_resolver_grounds_car_insurance_in_canonical_concept() -> None:
    """Dropping synonym normalization must make this canonical grounding fail."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)

    resolution = registry.resolver.resolve("Find customers with car-insurance cover")

    assert "sap:ProductAutomotive" in resolution.concept_ids
    assert resolution.matched_terms["sap:ProductAutomotive"] == "car insurance"


def test_resolver_does_not_match_a_term_inside_an_unrelated_word() -> None:
    """Replacing token matching with substring matching must make this false positive fail."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)

    resolution = registry.resolve("The claimant is unrelated to this insurance product")

    assert "sap:FinancialPosting" not in resolution.concept_ids


def test_resolver_quarantines_an_unknown_mapping_target() -> None:
    """Trusting an unregistered mapping target must leak an ungrounded concept ID."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    registry.mappings["DatabricksFranceMapping"].normalization["products"]["MTR"] = (
        "sap:UnknownLocalProduct"
    )

    resolution = registry.resolve("Find MTR customers")

    assert "sap:UnknownLocalProduct" not in resolution.concept_ids
    assert "sap:ProductAutomotive" not in resolution.concept_ids


def test_resolver_grounds_registered_home_insurance_mapping_targets() -> None:
    """Dropping governed CommercialProduct must leave an active mapping target unresolved."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)

    resolution = registry.resolve("Find HOME customers")

    assert "sap:ProductCommercial" in resolution.concept_ids
    assert resolution.matched_terms["sap:ProductCommercial"] == "home"


@pytest.mark.parametrize("local_value", ["MTR", "AUTO"])
def test_resolver_grounds_local_mapping_values_in_motor_insurance(local_value: str) -> None:
    """Ignoring mapping normalization must break local product grounding."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)

    resolution = registry.resolve(f"Find {local_value} customers")

    assert resolution.matched_terms["sap:ProductAutomotive"] == local_value.casefold()


def test_resolver_grounds_governed_plural_business_terms() -> None:
    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)

    resolution = registry.resolve(
        "Find French customers with qualifying claims and active policies."
    )

    assert {
        "sap:ActiveSalesOrder",
        "sap:FinancialPosting",
        "sap:BusinessPartner",
        "sap:SalesOrder",
        "sap:QualifyingPosting",
    }.issubset(resolution.concept_ids)
