"""Explicit deterministic workflow for governed claims investigations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import gettempdir
from uuid import uuid4

from semantic_layer.agents.tools import SemanticAgentTools
from semantic_layer.compiler import CompiledQuery
from semantic_layer.governance import AuthorizationDecision
from semantic_layer.models import CallerContext, Resolution, SemanticQueryPlan
from semantic_layer.provenance import Provenance, ProvenanceStore
from semantic_layer.quality import QualityReport
from semantic_layer.registry import SemanticRegistry

_STAGES = (
    "intent_parse",
    "resolve",
    "relationships_and_products",
    "authorize",
    "plan",
    "compile",
    "execute",
    "result_validation",
    "provenance",
    "answer_formatting",
)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def provenance_as_dict(provenance: Provenance) -> dict[str, object]:
    """Return the reviewed, serializable provenance envelope without internals."""

    fields = (
        "query_id",
        "question_digest",
        "execution_digest",
        "plan_digest",
        "query_digest",
        "parameter_digest",
        "caller_digest",
        "authorization_digest",
        "authorization_outcome",
        "quality_digest",
        "result_digest",
        "source_digests",
        "local_sources",
        "mapping_evidence",
        "concepts",
        "metric_ids",
        "data_products",
        "mapping_ids",
        "physical_sources",
        "field_evidence",
        "semantic_versions",
        "quality_status",
        "row_count",
        "compiled_platform",
        "created_at",
    )
    return {field: getattr(provenance, field) for field in fields}


@dataclass(frozen=True)
class AgentAnswer:
    """Traceable response issued only after every governed workflow stage succeeds."""

    question: str
    caller: CallerContext
    resolution: Resolution
    relationships: list[dict[str, str | None]]
    data_products: list[str]
    plan: SemanticQueryPlan
    authorization: AuthorizationDecision
    quality: QualityReport
    compiled_query: CompiledQuery
    rows: list[dict[str, object]]
    provenance: Provenance
    stages: tuple[str, ...] = _STAGES

    def to_dict(self) -> dict[str, object]:
        """Format the answer for CLI or HTTP without exposing capability internals."""

        return {
            "question": self.question,
            "caller": self.caller.model_dump(mode="json"),
            "resolution": self.resolution.model_dump(mode="json"),
            "relationships": self.relationships,
            "data_products": self.data_products,
            "plan": self.plan.model_dump(mode="json"),
            "authorization": {
                "allowed": self.authorization.allowed,
                "reason_code": self.authorization.reason_code,
                "message": self.authorization.message,
            },
            "compiled_query": {
                "target_platform": self.compiled_query.target_platform,
                "sql": self.compiled_query.sql,
                "parameters": list(self.compiled_query.parameters),
                "mapping_ids": list(self.compiled_query.mapping_ids),
                "metric_ids": list(self.compiled_query.metric_ids),
                "field_evidence": dict(self.compiled_query.field_evidence),
            },
            "quality": {
                "status": self.quality.status,
                "score": self.quality.score,
                "issues": [asdict(issue) for issue in self.quality.issues],
            },
            "result": self.rows,
            "provenance": provenance_as_dict(self.provenance),
            "stages": list(self.stages),
        }


class ClaimsInvestigationAgent:
    """Orchestrate governed services; this class has neither an LLM nor a SQL tool."""

    def __init__(
        self,
        repository_root: Path | None = None,
        *,
        provenance_path: Path | None = None,
    ) -> None:
        root = (repository_root or _repository_root()).resolve()
        provenance_path = provenance_path or (gettempdir() and Path(gettempdir()) / f"semantic-layer-{uuid4()}.sqlite")
        registry = SemanticRegistry.from_repository(root)
        self.tools = SemanticAgentTools(
            registry,
            root / "data" / "curated",
            ProvenanceStore(provenance_path),
        )

    def answer(self, question: str, caller: CallerContext) -> AgentAnswer:
        """Return a deterministic answer or fail before data execution."""

        if not isinstance(question, str) or not question.strip():
            raise ValueError("a non-empty business question is required")
        if type(caller) is not CallerContext:
            raise TypeError("answer requires a validated CallerContext")

        resolution = self.tools.resolve_business_term(question)
        plan = self.tools.build_query_plan(question, caller)
        relationships = [relationship.model_dump(mode="json") for relationship in plan.relationships]
        data_products = list(plan.selected_products)
        authorization = self.tools.authorize(plan)
        if not authorization.allowed:
            raise PermissionError(f"{authorization.reason_code}: {authorization.message}")
        artifacts = self.tools.execute_semantic_query(question, plan, authorization)
        if artifacts.quality.status != "PASS" or not artifacts.execution._verify_integrity():
            raise ValueError("RESULT_VALIDATION_FAILED: execution output is not quality-bound")
        provenance = self.tools.record_provenance(question, artifacts.execution)
        return AgentAnswer(
            question=question,
            caller=plan.caller,
            resolution=resolution,
            relationships=relationships,
            data_products=data_products,
            plan=plan,
            authorization=authorization,
            quality=artifacts.quality,
            compiled_query=artifacts.compiled_query,
            rows=list(artifacts.execution),
            provenance=provenance,
        )
