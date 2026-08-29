"""Behavioural tests for the Git-sourced semantic registry."""

import shutil
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from semantic_layer.registry import SemanticRegistry

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_registry_loads_governed_assets_into_a_sqlite_cache() -> None:
    """Removing an asset or bypassing the cache must break this contract."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)

    assert registry.concepts["insurance:Customer"].name == "Customer"
    assert registry.products["ClaimsAnalytics"].certification.status == "CERTIFIED"
    assert registry.metrics["insurance:ClaimCount"].source_products == ["ClaimsAnalytics"]
    assert registry.connection.execute("SELECT COUNT(*) FROM concepts").fetchone()[0] == 14
    assert registry.connection.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 4


def test_registry_selects_only_certified_products_for_a_concept() -> None:
    """Changing certification filtering must make this product lookup unsafe."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)

    products = registry.certified_products_for("insurance:QualifyingClaim")

    assert [product.id for product in products] == ["ClaimsAnalytics"]


def test_registry_reuses_vocabulary_validation_and_rejects_dangling_mapping_targets(
    tmp_path: Path,
) -> None:
    """Weakening asset validation must permit invalid Git-sourced contracts."""

    repository = tmp_path / "repository"
    shutil.copytree(REPOSITORY_ROOT, repository, ignore=shutil.ignore_patterns(".git", ".venv"))
    vocabulary_path = repository / "semantic" / "vocabulary" / "insurance.yaml"
    document = yaml.safe_load(vocabulary_path.read_text())
    document["version"] = "1.0.0-01"
    vocabulary_path.write_text(yaml.safe_dump(document, sort_keys=False))

    with pytest.raises(ValidationError):
        SemanticRegistry.from_repository(repository)

    dangling_repository = tmp_path / "dangling-repository"
    shutil.copytree(
        REPOSITORY_ROOT,
        dangling_repository,
        ignore=shutil.ignore_patterns(".git", ".venv"),
    )
    mapping_path = dangling_repository / "mappings" / "databricks" / "france.yaml"
    mapping = yaml.safe_load(mapping_path.read_text())
    mapping["normalization"]["products"]["UNKNOWN"] = "insurance:UnknownProduct"
    mapping_path.write_text(yaml.safe_dump(mapping, sort_keys=False))

    with pytest.raises(ValueError, match="normalization.*unknown concept|UnknownProduct"):
        SemanticRegistry.from_repository(dangling_repository)
