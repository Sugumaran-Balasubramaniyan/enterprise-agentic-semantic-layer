"""Narrow deterministic tools available to the semantic investigation workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from semantic_layer.adapters import ExecutionResult, LocalDuckDBAdapter
from semantic_layer.compiler import CompiledQuery, DuckDBCompiler
from semantic_layer.governance import (
    AuthorizationDecision,
    DiscoveryAuthorizationDecision,
    authorize,
    authorize_discovery,
)
from semantic_layer.models import CallerContext, Resolution, SemanticQueryPlan, contains_sql_shape
from semantic_layer.provenance import Provenance, ProvenanceStore
from semantic_layer.quality import QualityReport, validate_curated_data
from semantic_layer.query_planner import QueryDiscovery, build_plan, discover_question
from semantic_layer.registry import SemanticRegistry
from semantic_layer.semantic_validation import Concept, Relationship


@dataclass(frozen=True)
class ExecutionArtifacts:
    """The signed artifacts issued by one permitted local semantic execution."""

    quality: QualityReport
    compiled_query: CompiledQuery
    execution: ExecutionResult


class SemanticAgentTools:
    """Expose governed services without an arbitrary-SQL or LLM tool."""

    def __init__(
        self,
        registry: SemanticRegistry,
        curated_data_path: Path,
        provenance_store: ProvenanceStore,
    ) -> None:
        self.registry = registry
        self.curated_data_path = curated_data_path.resolve()
        self.provenance_store = provenance_store

    def search_concept(self, text: str) -> list[Concept]:
        """Return only canonical concepts lexically grounded in *text*."""

        return [self.registry.concepts[item] for item in self.resolve_business_term(text).concept_ids]

    def resolve_business_term(self, text: str) -> Resolution:
        """Resolve a business phrase through the reviewed deterministic registry."""

        if not isinstance(text, str) or not text.strip():
            raise ValueError("a non-empty business question is required")
        if contains_sql_shape(text, natural_language=True):
            raise ValueError("business question cannot contain SQL-shaped values")
        return self.registry.resolve(text)

    def get_business_definition(self, concept_id: str) -> str:
        """Return one reviewed canonical definition."""

        try:
            return self.registry.concepts[concept_id].definition
        except KeyError:
            raise ValueError(f"unknown canonical concept: {concept_id}") from None

    def get_relationships(self, concept_id: str) -> list[Relationship]:
        """Return reviewed outgoing relationships for a canonical concept."""

        try:
            return list(self.registry.concepts[concept_id].relationships)
        except KeyError:
            raise ValueError(f"unknown canonical concept: {concept_id}") from None

    def find_certified_data_product(self, concept_id: str) -> list[str]:
        """Select only product IDs whose contracts are currently certified."""

        return [product.id for product in self.registry.certified_products_for(concept_id)]

    def get_metric_definition(self, metric_id: str) -> dict[str, object]:
        """Return governed metric metadata, never an executable expression."""

        try:
            return self.registry.metrics[metric_id].model_dump(mode="json")
        except KeyError:
            raise ValueError(f"unknown governed metric: {metric_id}") from None

    def discover(self, question: str, caller: CallerContext) -> QueryDiscovery:
        """Discover only the semantic controls required for pre-plan authorization."""

        if type(caller) is not CallerContext:
            raise TypeError("agent tools require a validated CallerContext")
        discovery = discover_question(question, caller.role, self.registry)
        if caller.country is not None and caller.country != discovery.caller.country:
            raise PermissionError("CALLER_COUNTRY_MISMATCH: question country conflicts with caller scope")
        if caller.purpose != discovery.caller.purpose:
            raise PermissionError("CALLER_PURPOSE_MISMATCH: caller purpose is not authorized for the plan")
        return discovery

    def authorize_discovery(self, discovery: QueryDiscovery) -> DiscoveryAuthorizationDecision:
        """Authorize discovery before a final typed plan is allowed to exist."""

        return authorize_discovery(discovery, discovery.caller, self.registry)

    def build_query_plan(
        self,
        question: str,
        caller: CallerContext,
        *,
        discovery: QueryDiscovery | None = None,
    ) -> SemanticQueryPlan:
        """Build the final typed plan after the caller's scope has been checked."""

        discovery = discovery or self.discover(question, caller)
        if discovery.caller.model_dump() != caller.model_copy(
            update={"country": discovery.caller.country}
        ).model_dump():
            raise PermissionError("CALLER_CONTEXT_MISMATCH: discovery is not bound to the caller")
        return build_plan(question, caller.role, self.registry, discovery=discovery)

    def authorize(self, plan: SemanticQueryPlan) -> AuthorizationDecision:
        """Issue authorization for the planner-derived caller context only."""

        return authorize(plan, plan.caller, self.registry)

    def execute_semantic_query(
        self,
        question: str,
        plan: SemanticQueryPlan,
        authorization: AuthorizationDecision,
    ) -> ExecutionArtifacts:
        """Compile and execute only a signed, quality-bound semantic plan."""

        if not authorization.allowed:
            raise PermissionError(f"{authorization.reason_code}: {authorization.message}")
        quality = validate_curated_data(self.curated_data_path, self.registry)
        if quality.status != "PASS":
            raise ValueError("CURATED_DATA_QUALITY_FAILED: local data cannot be executed")
        compiled_query = DuckDBCompiler(self.registry).compile(plan, authorization, plan.caller, question)
        execution = LocalDuckDBAdapter(self.curated_data_path, self.registry).execute(
            compiled_query, authorization, plan.caller, quality
        )
        return ExecutionArtifacts(quality=quality, compiled_query=compiled_query, execution=execution)

    def get_provenance(self, query_id: str) -> Provenance:
        """Read a tamper-evident provenance record by its generated query ID."""

        return self.provenance_store.get(query_id)

    def record_provenance(self, question: str, execution: ExecutionResult) -> Provenance:
        """Persist provenance only from a verified local execution capability."""

        return self.provenance_store.record(question=question, execution=execution)
