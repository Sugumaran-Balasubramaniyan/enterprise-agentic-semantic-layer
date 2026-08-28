"""Typed, SQL-free contracts for the semantic control plane."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SemanticModel(BaseModel):
    """Base model that rejects undeclared control-plane fields."""

    model_config = ConfigDict(extra="forbid")


class ConceptRelationship(SemanticModel):
    predicate: str
    target: str
    description: str | None = None


class SemanticConcept(SemanticModel):
    id: str
    name: str
    version: str
    definition: str
    description: str
    synonyms: list[str] = Field(default_factory=list)
    domain: str
    owner: str
    classification: str
    sensitivity: dict[str, Any]
    relationships: list[ConceptRelationship] = Field(default_factory=list)
    allowed_values: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)


class Certification(SemanticModel):
    status: str
    certified_by: str
    certified_at: str


class ProductField(SemanticModel):
    name: str
    type: str
    concept: str
    nullable: bool
    pii: bool = False


class ProductQuality(SemanticModel):
    status: str
    checks: list[str] = Field(default_factory=list)


class DataProduct(SemanticModel):
    id: str
    name: str
    version: str
    owner: str
    platform: str
    location: str
    grain: str
    sla: str
    classification: str
    pii: list[str] = Field(default_factory=list)
    quality: ProductQuality
    lineage: dict[str, Any]
    concepts: list[str]
    schema_: list[ProductField] = Field(alias="schema")
    certification: Certification


class MappingField(SemanticModel):
    physical_name: str
    concept: str
    pii: bool = False
    canonical_subset: str | None = None


class DataProductMapping(SemanticModel):
    id: str
    version: str
    owner: str
    platform: str
    location: str
    data_products: list[str]
    source: dict[str, Any]
    fields: dict[str, MappingField]
    normalization: dict[str, dict[str, str]]
    lineage: dict[str, Any]


class Metric(SemanticModel):
    id: str
    name: str
    version: str
    definition: str
    concept: str
    expression: str
    aggregation: str
    unit: str
    filter_rule: str | None = None
    source_products: list[str]
    dependencies: list[str] = Field(default_factory=list)
    numerator: dict[str, Any] | None = None
    denominator: dict[str, Any] | None = None
    alignment: dict[str, Any] | None = None


class GovernedRule(SemanticModel):
    id: str
    name: str
    version: str
    applies_to: str
    definition: str
    include_statuses: list[str] = Field(default_factory=list)
    exclude_statuses: list[str] = Field(default_factory=list)
    predicate: str
    rationale: str


class Resolution(SemanticModel):
    text: str
    concept_ids: list[str] = Field(default_factory=list)
    matched_terms: dict[str, str] = Field(default_factory=dict)


class CallerContext(SemanticModel):
    role: str
    country: str | None = None
    purpose: str = "semantic_query"


class Filter(SemanticModel):
    concept_id: str
    operator: Literal["=", "!=", ">", ">=", "<", "<=", "IN"]
    value: str | int | float | list[str]


class MetricPredicate(SemanticModel):
    metric_id: str
    operator: Literal["=", "!=", ">", ">=", "<", "<="]
    value: int | float


class RelationshipPath(SemanticModel):
    source: str
    predicate: str
    target: str


class TimeContext(SemanticModel):
    window: Literal["last_12_months", "current_year"]
    months: int | None = Field(default=None, ge=1)


class SemanticQueryPlan(SemanticModel):
    """A validated logical plan; physical SQL is intentionally not representable."""

    root_entity: str
    projected_dimensions: list[str] = Field(default_factory=list)
    filters: list[Filter] = Field(default_factory=list)
    relationships: list[RelationshipPath] = Field(default_factory=list)
    metric_predicates: list[MetricPredicate] = Field(default_factory=list)
    time_context: TimeContext | None = None
    selected_products: list[str] = Field(default_factory=list)
    caller: CallerContext
    target_platform: str = "DuckDB"
