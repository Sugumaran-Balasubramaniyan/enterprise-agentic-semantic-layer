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
    RelationshipPath,
)
from semantic_layer.resolver.service import DeterministicResolver
from semantic_layer.semantic_validation import Concept, load_vocabulary


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


class SemanticRegistry:
    """Validated Git assets plus a disposable SQLite-backed registry cache."""

    def __init__(
        self,
        *,
        root: Path,
        concepts: dict[str, Concept],
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
        vocabulary = load_vocabulary(root / "semantic" / "vocabulary" / "insurance.yaml")
        concepts = {concept.id: concept for concept in vocabulary}
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
        cls._validate_asset_references(concepts, products, mappings, metrics, rules)
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

    @staticmethod
    def _validate_asset_references(
        concepts: dict[str, Concept],
        products: dict[str, DataProduct],
        mappings: dict[str, DataProductMapping],
        metrics: dict[str, Metric],
        rules: dict[str, GovernedRule],
    ) -> None:
        for concept in concepts.values():
            unknown_relationship_targets = {
                relationship.target
                for relationship in concept.relationships
                if relationship.target not in concepts
            }
            if unknown_relationship_targets:
                raise ValueError(
                    f"concept {concept.id} references unknown relationship targets: "
                    f"{sorted(unknown_relationship_targets)}"
                )
        for product in products.values():
            unknown = set(product.concepts) - set(concepts)
            if unknown:
                raise ValueError(f"product {product.id} references unknown concepts: {sorted(unknown)}")
        for mapping in mappings.values():
            unknown_products = set(mapping.data_products) - set(products)
            if unknown_products:
                raise ValueError(f"mapping {mapping.id} references unknown products: {sorted(unknown_products)}")
            unknown_concepts = {field.concept for field in mapping.fields.values()} - set(concepts)
            if unknown_concepts:
                raise ValueError(f"mapping {mapping.id} references unknown concepts: {sorted(unknown_concepts)}")
            unknown_subsets = {
                field.canonical_subset
                for field in mapping.fields.values()
                if field.canonical_subset is not None and field.canonical_subset not in concepts
            }
            if unknown_subsets:
                raise ValueError(
                    f"mapping {mapping.id} references unknown canonical subsets: "
                    f"{sorted(unknown_subsets)}"
                )
            unknown_normalization_targets = (
                set(mapping.normalization.get("products", {}).values()) - set(concepts)
            )
            if unknown_normalization_targets:
                raise ValueError(
                    f"mapping {mapping.id} product normalization references unknown concepts: "
                    f"{sorted(unknown_normalization_targets)}"
                )
        for metric in metrics.values():
            unknown_products = set(metric.source_products) - set(products)
            if unknown_products:
                raise ValueError(f"metric {metric.id} references unknown products: {sorted(unknown_products)}")
            if metric.concept not in concepts:
                raise ValueError(f"metric {metric.id} references unknown concept: {metric.concept}")
            if metric.filter_rule and metric.filter_rule not in rules:
                raise ValueError(f"metric {metric.id} references unknown rule: {metric.filter_rule}")
            unknown_dependencies = set(metric.dependencies) - set(metrics)
            if unknown_dependencies:
                raise ValueError(
                    f"metric {metric.id} references unknown dependencies: "
                    f"{sorted(unknown_dependencies)}"
                )
        for rule in rules.values():
            if rule.applies_to not in concepts:
                raise ValueError(
                    f"rule {rule.id} references unknown applies_to concept: {rule.applies_to}"
                )

    def resolve(self, text: str):
        """Resolve business language through the deterministic registry resolver."""

        return self.resolver.resolve(text)

    def certified_products_for(self, concept_id: str) -> list[DataProduct]:
        """Return only currently certified products that expose the given concept."""

        return [
            product
            for product in self.products.values()
            if product.certification.status == "CERTIFIED"
            and product.quality.status == "CERTIFIED"
            and concept_id in product.concepts
        ]

    def concept_id_named(self, name: str) -> str:
        """Find a canonical ID through vocabulary data rather than caller literals."""

        for concept in self.concepts.values():
            if concept.name.casefold() == name.casefold():
                return concept.id
        raise ValueError(f"unknown canonical concept name: {name}")

    def metric_id_named(self, name: str) -> str:
        """Find a metric identifier through registered metric metadata."""

        for metric in self.metrics.values():
            if metric.name.casefold() == name.casefold():
                return metric.id
        raise ValueError(f"unknown governed metric name: {name}")

    def relationship_path(self, source: str, target: str) -> RelationshipPath:
        """Read a validated relationship edge from the canonical vocabulary."""

        concept = self.concepts.get(source)
        if concept is None:
            raise ValueError(f"unknown relationship source: {source}")
        for relationship in concept.relationships:
            if relationship.target == target:
                return RelationshipPath(
                    source=source, predicate=relationship.predicate, target=target
                )
        raise ValueError(f"no governed relationship from {source} to {target}")

    def product_for_entity(self, concept_id: str) -> str:
        """Select the certified product whose asset declares the entity's grain."""

        concept = self.concepts.get(concept_id)
        if concept is None:
            raise ValueError(f"unknown canonical concept: {concept_id}")
        expected_grain = f"one row per {concept.name.casefold()}"
        candidates = [
            product.id
            for product in self.certified_products_for(concept_id)
            if expected_grain == product.grain.casefold()
        ]
        if len(candidates) != 1:
            raise ValueError(f"expected one certified product at {expected_grain}, found: {candidates}")
        return candidates[0]

    def products_for_plan(self, entity_ids: list[str], metric_ids: list[str]) -> list[str]:
        """Resolve entity grains and metric sources to unique certified products."""

        product_ids = [self.product_for_entity(entity_id) for entity_id in entity_ids]
        for metric_id in metric_ids:
            metric = self.metrics.get(metric_id)
            if metric is None:
                raise ValueError(f"unknown governed metric: {metric_id}")
            for product_id in metric.source_products:
                product = self.products.get(product_id)
                if (
                    product is None
                    or product.certification.status != "CERTIFIED"
                    or product.quality.status != "CERTIFIED"
                ):
                    raise ValueError(
                        f"metric {metric_id} references unavailable certified product: {product_id}"
                    )
                product_ids.append(product_id)
        return list(dict.fromkeys(product_ids))

    def local_product_terms(self) -> set[str]:
        """Return normalized product spellings supplied by mapping assets."""

        from semantic_layer.resolver.service import normalize

        return {
            normalize(local_value)
            for mapping in self.mappings.values()
            for local_value in mapping.normalization.get("products", {})
        }
