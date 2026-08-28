"""Behavioural tests for the Git-sourced semantic registry."""

from pathlib import Path

from semantic_layer.registry import SemanticRegistry

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_registry_loads_governed_assets_into_a_sqlite_cache() -> None:
    """Removing an asset or bypassing the cache must break this contract."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)

    assert registry.concepts["insurance:Customer"].name == "Customer"
    assert registry.products["ClaimsAnalytics"].certification.status == "CERTIFIED"
    assert registry.metrics["insurance:ClaimCount"].source_products == ["ClaimsAnalytics"]
    assert registry.connection.execute("SELECT COUNT(*) FROM concepts").fetchone()[0] == 13
    assert registry.connection.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 4


def test_registry_selects_only_certified_products_for_a_concept() -> None:
    """Changing certification filtering must make this product lookup unsafe."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)

    products = registry.certified_products_for("insurance:QualifyingClaim")

    assert [product.id for product in products] == ["ClaimsAnalytics"]
