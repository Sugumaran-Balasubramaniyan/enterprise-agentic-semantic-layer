"""Registry-derived static lineage for governed semantic plans."""

from __future__ import annotations

from dataclasses import dataclass

from semantic_layer.models import SemanticQueryPlan
from semantic_layer.registry import SemanticRegistry


@dataclass(frozen=True)
class LineageEnvelope:
    """Static contract lineage selected by one logical plan."""

    data_products: list[str]
    metric_ids: list[str]
    mapping_ids: list[str]
    physical_sources: list[str]
    semantic_versions: dict[str, str]


class LineageService:
    """Build lineage exclusively from reviewed registry assets."""

    def __init__(self, registry: SemanticRegistry) -> None:
        self.registry = registry

    def for_plan(self, plan: SemanticQueryPlan) -> LineageEnvelope:
        """Return static lineage without inventing a source outside registered mappings."""

        country = next(
            (
                query_filter.value
                for query_filter in plan.filters
                if query_filter.concept_id == "insurance:Country" and query_filter.operator == "="
            ),
            None,
        )
        mappings = [mapping for mapping in self.registry.mappings.values() if mapping.location == country]
        if len(mappings) != 1:
            raise ValueError("lineage requires one registered mapping for plan country")
        mapping = mappings[0]
        if not set(plan.selected_products).issubset(mapping.data_products):
            raise ValueError("lineage cannot bypass selected product mapping")
        sources = list(mapping.lineage.get("physical_sources", []))
        metric_ids = [predicate.metric_id for predicate in plan.metric_predicates]
        versions = {"vocabulary": "1.0.0", "mapping": mapping.version}
        versions.update(
            {f"metric:{metric_id}": self.registry.metrics[metric_id].version for metric_id in metric_ids}
        )
        return LineageEnvelope(
            data_products=list(plan.selected_products),
            metric_ids=metric_ids,
            mapping_ids=[mapping.id],
            physical_sources=sources,
            semantic_versions=versions,
        )
