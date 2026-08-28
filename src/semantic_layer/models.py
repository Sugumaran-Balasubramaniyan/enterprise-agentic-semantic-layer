"""Typed, SQL-free contracts for the semantic control plane."""

from __future__ import annotations

import re
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

CanonicalSemanticId = Annotated[
    str, StringConstraints(pattern=r"^[a-z][a-z0-9_-]*:[A-Za-z][A-Za-z0-9_-]*$")
]
CanonicalValue = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9:_-]+$")]
ProductId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9]*$")]
RoleId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9]*$")]
CountryCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")]
_SQL_TOKEN = re.compile(
    r"(?:;|--|/\*|\*/|\b(?:alter|create|delete|drop|execute|insert|select|union|update|with)\b)",
    re.IGNORECASE,
)


class SemanticModel(BaseModel):
    """Base model that rejects undeclared control-plane fields."""

    model_config = ConfigDict(extra="forbid")


def _contains_sql_shape(value: Any) -> bool:
    if isinstance(value, str):
        return bool(_SQL_TOKEN.search(value))
    if isinstance(value, dict):
        return any(_contains_sql_shape(item) for pair in value.items() for item in pair)
    if isinstance(value, (list, tuple, set)):
        return any(_contains_sql_shape(item) for item in value)
    return False


class SqlFreeSemanticModel(SemanticModel):
    """Reject SQL-shaped strings recursively before logical-plan coercion."""

    @model_validator(mode="before")
    @classmethod
    def reject_sql_shaped_values(cls, value: Any) -> Any:
        if _contains_sql_shape(value):
            raise ValueError("logical semantic contracts cannot contain SQL-shaped values")
        return value


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


class CallerContext(SqlFreeSemanticModel):
    role: RoleId
    country: CountryCode | None = None
    purpose: str = "semantic_query"


class Filter(SqlFreeSemanticModel):
    concept_id: CanonicalSemanticId
    operator: Literal["=", "!=", ">", ">=", "<", "<=", "IN"]
    value: CanonicalValue | int | float | list[CanonicalValue]


class MetricPredicate(SqlFreeSemanticModel):
    metric_id: CanonicalSemanticId
    operator: Literal["=", "!=", ">", ">=", "<", "<="]
    value: int | float


class RelationshipPath(SqlFreeSemanticModel):
    source: CanonicalSemanticId
    predicate: CanonicalSemanticId
    target: CanonicalSemanticId


class TimeContext(SqlFreeSemanticModel):
    window: Literal["last_12_months", "current_year"]
    months: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def require_unambiguous_window(self) -> TimeContext:
        if self.window == "last_12_months" and self.months != 12:
            raise ValueError("last_12_months requires months=12")
        if self.window == "current_year" and self.months is not None:
            raise ValueError("current_year must not specify months")
        return self


class SemanticQueryPlan(SqlFreeSemanticModel):
    """A validated logical plan; physical SQL is intentionally not representable."""

    root_entity: CanonicalSemanticId
    projected_dimensions: list[CanonicalSemanticId] = Field(default_factory=list)
    filters: list[Filter] = Field(default_factory=list)
    relationships: list[RelationshipPath] = Field(default_factory=list)
    metric_predicates: list[MetricPredicate] = Field(default_factory=list)
    time_context: TimeContext | None = None
    selected_products: list[ProductId] = Field(default_factory=list)
    caller: CallerContext
    target_platform: str = "DuckDB"
