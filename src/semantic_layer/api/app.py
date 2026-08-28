"""Thin FastAPI transport around the deterministic governed services."""

from __future__ import annotations

from pathlib import Path
from tempfile import gettempdir
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from semantic_layer.agents import ClaimsInvestigationAgent
from semantic_layer.agents.workflow import provenance_as_dict
from semantic_layer.models import CallerContext, contains_sql_shape


class QuestionRequest(BaseModel):
    """A constrained transport request containing business language only."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)

    @field_validator("question")
    @classmethod
    def reject_sql_shaped_question(cls, value: str) -> str:
        """Fail before routing untrusted SQL-shaped text into agent services."""

        if contains_sql_shape(value, natural_language=True):
            raise ValueError("business question cannot contain SQL-shaped values")
        return value


class SemanticRequest(QuestionRequest):
    """Business question plus an authenticated role and optional country scope."""

    role: str = Field(min_length=1)
    country: str | None = None
    purpose: str = "semantic_query"

    def caller(self) -> CallerContext:
        return CallerContext(role=self.role, country=self.country, purpose=self.purpose)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _error(error: Exception) -> HTTPException:
    if isinstance(error, PermissionError):
        return HTTPException(status_code=403, detail=str(error))
    if isinstance(error, KeyError):
        return HTTPException(status_code=404, detail=str(error))
    return HTTPException(status_code=422, detail=str(error))


def create_app(repository_root: Path | None = None, *, provenance_path: Path | None = None) -> FastAPI:
    """Create an application whose routes delegate to one deterministic agent."""

    root = (repository_root or _repository_root()).resolve()
    store_path = provenance_path or (Path(gettempdir()) / f"semantic-layer-api-{uuid4()}.sqlite")
    agent = ClaimsInvestigationAgent(root, provenance_path=store_path)
    application = FastAPI(title="Federated Semantic Layer", version="0.1.0")
    application.state.agent = agent

    def current_agent(request: Request) -> ClaimsInvestigationAgent:
        return request.app.state.agent

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/concepts")
    def concepts(request: Request) -> list[dict[str, object]]:
        return [concept.model_dump(mode="json") for concept in current_agent(request).tools.registry.concepts.values()]

    @application.get("/concepts/{concept_id}")
    def concept(concept_id: str, request: Request) -> dict[str, object]:
        try:
            return current_agent(request).tools.registry.concepts[concept_id].model_dump(mode="json")
        except KeyError:
            raise HTTPException(status_code=404, detail=f"unknown canonical concept: {concept_id}") from None

    @application.get("/metrics")
    def metrics(request: Request) -> list[dict[str, object]]:
        return [metric.model_dump(mode="json") for metric in current_agent(request).tools.registry.metrics.values()]

    @application.get("/data-products")
    def data_products(request: Request) -> list[dict[str, object]]:
        return [product.model_dump(mode="json") for product in current_agent(request).tools.registry.products.values()]

    @application.get("/mappings")
    def mappings(request: Request) -> list[dict[str, object]]:
        return [mapping.model_dump(mode="json") for mapping in current_agent(request).tools.registry.mappings.values()]

    @application.post("/resolve")
    def resolve(payload: QuestionRequest, request: Request) -> dict[str, object]:
        try:
            return current_agent(request).tools.resolve_business_term(payload.question).model_dump(mode="json")
        except (TypeError, ValueError, PermissionError) as error:
            raise _error(error) from None

    @application.post("/query-plan")
    def query_plan(payload: SemanticRequest, request: Request) -> dict[str, object]:
        try:
            return current_agent(request).tools.build_query_plan(payload.question, payload.caller()).model_dump(mode="json")
        except (TypeError, ValueError, PermissionError) as error:
            raise _error(error) from None

    @application.post("/execute")
    def execute(payload: SemanticRequest, request: Request) -> dict[str, object]:
        try:
            return current_agent(request).answer(payload.question, payload.caller()).to_dict()
        except (TypeError, ValueError, PermissionError) as error:
            raise _error(error) from None

    @application.post("/validate")
    def validate(request: Request) -> dict[str, object]:
        from semantic_layer.quality import validate_curated_data

        result = validate_curated_data(
            current_agent(request).tools.curated_data_path,
            current_agent(request).tools.registry,
        )
        return {
            "status": result.status,
            "score": result.score,
            "issues": [issue.__dict__ for issue in result.issues],
        }

    @application.get("/provenance/{query_id}")
    def provenance(query_id: str, request: Request) -> dict[str, object]:
        try:
            return provenance_as_dict(current_agent(request).tools.get_provenance(query_id))
        except (KeyError, ValueError) as error:
            raise _error(error) from None

    return application


app = create_app()
