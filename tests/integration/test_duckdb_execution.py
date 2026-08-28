"""Integration tests for the governed local DuckDB execution path."""

from pathlib import Path

from semantic_layer.adapters import LocalDuckDBAdapter
from semantic_layer.compiler import DuckDBCompiler
from semantic_layer.governance import authorize
from semantic_layer.lineage import LineageService
from semantic_layer.provenance import ProvenanceStore
from semantic_layer.quality import validate_curated_data
from semantic_layer.query_planner import build_plan
from semantic_layer.registry import SemanticRegistry

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_QUESTION = (
    "Find French motor-insurance customers with at least three qualifying claims "
    "in the last 12 months and total incurred loss above EUR 20,000."
)


def _primary_execution() -> tuple[SemanticRegistry, object, object, object, list[dict[str, object]]]:
    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    plan = build_plan(PRIMARY_QUESTION, role="ClaimsAnalystFR", registry=registry)
    authorization = authorize(plan, plan.caller)
    assert authorization.allowed is True
    quality = validate_curated_data(REPOSITORY_ROOT / "data" / "curated")
    assert quality.status == "PASS"
    compiled = DuckDBCompiler(registry).compile(plan)
    rows = LocalDuckDBAdapter(REPOSITORY_ROOT / "data" / "curated").execute(compiled)
    return registry, plan, authorization, quality, rows


def test_primary_plan_executes_with_deterministic_qualifying_fr_customers() -> None:
    """Removing status, time, or metric filters must alter the governed primary result."""

    _, _, _, _, rows = _primary_execution()

    assert rows == [
        {"customer_id": "FR_001", "country": "FR", "claim_count": 3, "total_incurred_loss_eur": 24000.0},
        {"customer_id": "FR_002", "country": "FR", "claim_count": 3, "total_incurred_loss_eur": 25000.0},
    ]


def test_provenance_persists_semantic_sources_for_the_executed_answer(tmp_path: Path) -> None:
    """Omitting static lineage or dynamic quality data must make the answer untraceable."""

    registry, plan, authorization, quality, rows = _primary_execution()
    compiled = DuckDBCompiler(registry).compile(plan)
    lineage = LineageService(registry).for_plan(plan)
    store = ProvenanceStore(tmp_path / "provenance.sqlite")

    provenance = store.record(
        question=PRIMARY_QUESTION,
        plan=plan,
        authorization=authorization,
        quality=quality,
        lineage=lineage,
        compiled_query=compiled,
        row_count=len(rows),
    )

    persisted = store.get(provenance.query_id)
    assert provenance.quality_status == "PASS"
    assert provenance.data_products == ["Customer360", "PolicyMaster", "ClaimsAnalytics"]
    assert "ClaimsAnalytics" in provenance.data_products
    assert persisted == provenance
    assert any(source.startswith("databricks://") for source in provenance.physical_sources)
