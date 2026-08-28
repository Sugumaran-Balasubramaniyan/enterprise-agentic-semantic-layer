"""Load versioned repository assets into a local SQLite query cache."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import yaml

from semantic_layer.models import (
    DataProduct,
    DataProductMapping,
    GovernedRule,
    Metric,
    SemanticConcept,
)
from semantic_layer.resolver.service import DeterministicResolver


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


class SemanticRegistry:
    """Validated Git assets plus a disposable SQLite-backed registry cache."""

    def __init__(
        self,
        *,
        root: Path,
        concepts: dict[str, SemanticConcept],
        products: dict[str, DataProduct],
        mappings: dict[str, DataProductMapping],
        metrics: dict[str, Metric],
        rules: dict[str, GovernedRule],
        connection: sqlite3.Connection,
    ) -> None:
        self.root = root
        self.concepts = concepts
        self.products = products
        self.mappings = mappings
        self.metrics = metrics
        self.rules = rules
        self.connection = connection
        self.resolver = DeterministicResolver(self)

    @classmethod
    def from_repository(cls, root: Path) -> SemanticRegistry:
        """Read authoritative Git assets, validate them, and populate a SQLite cache."""

        root = root.resolve()
        vocabulary = _read_yaml(root / "semantic" / "vocabulary" / "insurance.yaml")
        concepts = {
            concept.id: concept
            for concept in (
                SemanticConcept.model_validate(item) for item in vocabulary["concepts"]
            )
        }
        products = {
            product.id: product
            for product in (
                DataProduct.model_validate(_read_yaml(path))
                for path in sorted((root / "data_products").glob("*.yaml"))
            )
        }
        mappings = {
            mapping.id: mapping
            for mapping in (
                DataProductMapping.model_validate(_read_yaml(path))
                for path in sorted((root / "mappings").glob("*/*.yaml"))
            )
        }
        metrics_document = _read_yaml(root / "semantic" / "metrics" / "metrics.yaml")
        metrics = {
            metric.id: metric
            for metric in (Metric.model_validate(item) for item in metrics_document["metrics"])
        }
        rules_document = _read_yaml(root / "semantic" / "rules" / "claims.yaml")
        rules = {
            rule.id: rule
            for rule in (GovernedRule.model_validate(item) for item in rules_document["rules"])
        }
        connection = sqlite3.connect(":memory:")
        cls._cache_assets(connection, "concepts", concepts)
        cls._cache_assets(connection, "products", products)
        cls._cache_assets(connection, "mappings", mappings)
        cls._cache_assets(connection, "metrics", metrics)
        cls._cache_assets(connection, "rules", rules)
        return cls(
            root=root,
            concepts=concepts,
            products=products,
            mappings=mappings,
            metrics=metrics,
            rules=rules,
            connection=connection,
        )

    @staticmethod
    def _cache_assets(connection: sqlite3.Connection, table: str, assets: dict[str, Any]) -> None:
        connection.execute(f"CREATE TABLE {table} (id TEXT PRIMARY KEY, document TEXT NOT NULL)")
        connection.executemany(
            f"INSERT INTO {table} (id, document) VALUES (?, ?)",
            ((identifier, asset.model_dump_json(by_alias=True)) for identifier, asset in assets.items()),
        )
        connection.commit()

    def resolve(self, text: str):
        """Resolve business language through the deterministic registry resolver."""

        return self.resolver.resolve(text)

    def certified_products_for(self, concept_id: str) -> list[DataProduct]:
        """Return only currently certified products that expose the given concept."""

        return [
            product
            for product in self.products.values()
            if product.certification.status == "CERTIFIED" and concept_id in product.concepts
        ]
