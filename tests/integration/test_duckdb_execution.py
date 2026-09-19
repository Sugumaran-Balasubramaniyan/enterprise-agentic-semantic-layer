"""Integration tests for DuckDB execution with certified curated data."""

from pathlib import Path

from semantic_layer.adapters import LocalDuckDBAdapter
from semantic_layer.compiler import DuckDBCompiler
from semantic_layer.governance import authorize
from semantic_layer.provenance import ProvenanceStore
from semantic_layer.quality import validate_curated_data
from semantic_layer.query_planner import build_plan
from semantic_layer.registry import SemanticRegistry

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_QUESTION = (
    "Find French motor-insurance customers with at least three qualifying claims "
    "in the last 12 months and total incurred loss above EUR 20,000."
)


def _primary_execution():
    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    plan = build_plan(PRIMARY_QUESTION, role="ClaimsAnalystFR", registry=registry)
    authorization = authorize(plan, plan.caller, registry)
    compiler = DuckDBCompiler(registry)
    query = compiler.compile(plan, authorization, plan.caller, PRIMARY_QUESTION)
    data_dir = REPOSITORY_ROOT / "data" / "curated"
    quality = validate_curated_data(data_dir, registry)
    adapter = LocalDuckDBAdapter(data_dir, registry)
    rows = adapter.execute(
        query,
        authorization,
        plan.caller,
        quality,
    )
    return registry, plan, authorization, quality, rows


def test_primary_plan_executes_with_deterministic_qualifying_fr_customers() -> None:
    """Removing status, time, or metric filters must alter the governed primary result."""

    _, _, _, _, rows = _primary_execution()

    assert rows == [
        {"partner_id": "FR_001", "country": "FR", "posting_count": 3, "total_debit_loss_eur": 24000.0},
        {"partner_id": "FR_002", "country": "FR", "posting_count": 3, "total_debit_loss_eur": 25000.0},
    ]


def test_provenance_persists_semantic_sources_for_the_executed_answer(tmp_path: Path) -> None:
    """Omitting static lineage or dynamic quality data must make the answer untraceable."""

    _, _, _, _, rows = _primary_execution()
    store = ProvenanceStore(tmp_path / "provenance.sqlite")

    provenance = store.record(question=PRIMARY_QUESTION, execution=rows)

    persisted = store.get(provenance.query_id)
    assert provenance.quality_status == "PASS"
    assert provenance.data_products == ["BusinessPartners", "SalesOrders", "ACDOCAFinancials"]
    assert "ACDOCAFinancials" in provenance.data_products
    assert persisted == provenance
    assert all(source.endswith(".csv") for source in provenance.physical_sources)


def test_primary_provenance_contains_semantic_closure_and_separates_source_evidence(
    tmp_path: Path,
) -> None:
    """Primary evidence must retain all governed concepts and distinguish source roles."""

    _, _, _, _, execution = _primary_execution()
    provenance = ProvenanceStore(tmp_path / "provenance.sqlite").record(
        question=PRIMARY_QUESTION, execution=execution
    )

    assert {
        "sap:BusinessPartner",
        "sap:CompanyCode",
        "sap:Product",
        "sap:SalesOrder",
        "sap:ProductAutomotive",
        "sap:FinancialPosting",
        "sap:QualifyingPosting",
        "sap:FinancialLoss",
    } <= set(provenance.concepts)
    assert set(provenance.queried_sources) == {"business_partners.csv", "sales_orders.csv", "acdoca_financials.csv"}
    assert set(provenance.quality_validated_sources) == {
        "business_partners.csv",
        "sales_orders.csv",
        "acdoca_financials.csv",
        "billing_documents.csv",
    }
    assert set(provenance.queried_sources) < set(provenance.quality_validated_sources)
