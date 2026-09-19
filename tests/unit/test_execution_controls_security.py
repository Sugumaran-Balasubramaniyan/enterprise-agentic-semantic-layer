"""Adversarial regression tests for the fail-closed execution control chain."""

from pathlib import Path

import pytest

from semantic_layer.adapters import LocalDuckDBAdapter
from semantic_layer.compiler import CompiledQuery, DuckDBCompiler
from semantic_layer.governance import authorize
from semantic_layer.models import CallerContext, Filter, RelationshipPath
from semantic_layer.provenance import ProvenanceStore
from semantic_layer.quality import validate_curated_data
from semantic_layer.query_planner import build_plan
from semantic_layer.registry import SemanticRegistry

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_QUESTION = (
    "Find French motor-insurance customers with at least three qualifying claims "
    "in the last 12 months and total incurred loss above EUR 20,000."
)


def _primary_plan_and_registry() -> tuple[SemanticRegistry, object]:
    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    return registry, build_plan(PRIMARY_QUESTION, role="ClaimsAnalystFR", registry=registry)


def test_compiled_query_cannot_be_publicly_constructed() -> None:
    """Exposing a public SQL artifact constructor must permit arbitrary local SQL execution."""

    with pytest.raises(TypeError, match="compiler-issued"):
        CompiledQuery("SELECT 'forged'", (), (), "DuckDB")


def test_compilation_requires_a_matching_allowed_decision_and_authenticated_caller() -> None:
    """Omitting authorization or swapping the authenticated caller must block compilation."""

    registry, plan = _primary_plan_and_registry()
    compiler = DuckDBCompiler(registry)
    caller = CallerContext(role="ClaimsAnalystFR", country="FR")
    allowed = authorize(plan, caller, registry)

    with pytest.raises(TypeError, match="authorization"):
        compiler.compile(plan)
    with pytest.raises(ValueError, match="caller|authorization"):
        compiler.compile(plan, allowed, CallerContext(role="ClaimsAnalystFR", country="DE"), PRIMARY_QUESTION)


@pytest.mark.parametrize("quality_status", ["DEGRADED", "UNSAFE"])
def test_non_healthy_product_quality_blocks_compilation_and_execution(quality_status: str) -> None:
    registry, plan = _primary_plan_and_registry()
    caller = CallerContext(role="ClaimsAnalystFR", country="FR")
    allowed = authorize(plan, caller, registry)
    compiled = DuckDBCompiler(registry).compile(plan, allowed, caller, PRIMARY_QUESTION)
    quality = validate_curated_data(REPOSITORY_ROOT / "data" / "curated", registry)
    registry.products["ACDOCAFinancials"].quality.status = quality_status
    decision = authorize(plan, caller, registry)

    assert decision.allowed is False
    assert quality_status in decision.message
    with pytest.raises(ValueError, match="authorization"):
        DuckDBCompiler(registry).compile(plan, decision, caller, PRIMARY_QUESTION)
    with pytest.raises(ValueError, match="context|quality|integrity"):
        LocalDuckDBAdapter(REPOSITORY_ROOT / "data" / "curated", registry).execute(
            compiled, allowed, caller, quality
        )


def test_authorization_requires_authenticated_country_and_derives_pii_from_projection() -> None:
    """Ignoring caller country or optional PII arguments must let finance cross controls."""

    registry, plan = _primary_plan_and_registry()
    wrong_country = authorize(plan, CallerContext(role="ClaimsAnalystFR", country="DE"), registry)
    finance_plan = plan.model_copy(
        update={
            "projected_dimensions": ["sap:BusinessPartner"],
            "selected_products": ["BillingAnalytics"],
            "caller": CallerContext(role="FinanceAnalyst"),
        }
    )
    finance = authorize(finance_plan, CallerContext(role="FinanceAnalyst"), registry)

    assert wrong_country.allowed is False
    assert wrong_country.reason_code == "CALLER_CONTEXT_MISMATCH"
    assert finance.allowed is False
    assert finance.reason_code == "PII_FIELD_DENIED"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda plan: plan.model_copy(
            update={
                "filters": [
                    *plan.filters,
                    Filter(concept_id="sap:PostingStatus", operator="!=", value="REVERSED"),
                ]
            }
        ),
        lambda plan: plan.model_copy(
            update={"projected_dimensions": [*plan.projected_dimensions, "sap:SalesOrder"]}
        ),
        lambda plan: plan.model_copy(
            update={
                "relationships": [
                    *plan.relationships,
                    RelationshipPath(
                        source="sap:BusinessPartner",
                        predicate="sap:hasSalesOrder",
                        target="sap:SalesOrder",
                    ),
                ]
            }
        ),
        lambda plan: plan.model_copy(update={"metric_predicates": [*plan.metric_predicates, plan.metric_predicates[0]]}),
    ],
)
def test_compiler_rejects_every_unrepresented_plan_constraint(mutation) -> None:
    """Silently ignoring a filter, dimension, edge, or duplicate metric changes query meaning."""

    registry, plan = _primary_plan_and_registry()
    mutated = mutation(plan)
    caller = CallerContext(role="ClaimsAnalystFR", country="FR")
    decision = authorize(mutated, caller, registry)

    assert decision.allowed is True
    with pytest.raises(ValueError, match="unsupported|exactly|approved|relationships|metrics"):
        DuckDBCompiler(registry).compile(mutated, decision, caller, PRIMARY_QUESTION)


def test_quality_requires_all_nonempty_expected_datasets_and_rejects_nonfinite_loss(tmp_path: Path) -> None:
    """Partial or non-finite curated data must not produce a reusable passing report."""

    (tmp_path / "acdoca_financials.csv").write_text(
        "journal_entry_id,sales_order_id,partner_id,country,product,posting_status,posting_date,amount_in_company_currency_eur\n"
        "DOC_1,SO_1,FR_001,FR,sap:ProductAutomotive,POSTED,2026-08-01,nan\n",
        encoding="utf-8",
    )

    report = validate_curated_data(tmp_path)

    assert report.status == "FAIL"
    assert {issue.code for issue in report.issues} >= {
        "MISSING_EXPECTED_DATASET",
        "NONFINITE_VALUE",
    }


def test_quality_checks_mapping_for_each_rows_country(tmp_path: Path) -> None:
    """Using global product values must accept a product not mapped for that market."""

    for name in ("business_partners.csv", "sales_orders.csv", "billing_documents.csv"):
        source = REPOSITORY_ROOT / "data" / "curated" / name
        (tmp_path / name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "acdoca_financials.csv").write_text(
        "journal_entry_id,sales_order_id,partner_id,country,product,posting_status,posting_date,amount_in_company_currency_eur\n"
        "DE_DOC_1,DE_SO_1,DE_1,DE,sap:ProductCommercial,POSTED,2026-08-01,1.00\n",
        encoding="utf-8",
    )

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    registry.mappings["FabricGermanyMapping"].normalization["products"].pop("HomeInsurance")

    report = validate_curated_data(tmp_path, registry)

    assert "INVALID_PRODUCT_MAPPING" in {issue.code for issue in report.issues}


def test_adapter_requires_current_quality_and_rejects_changed_source_data(tmp_path: Path) -> None:
    """A passing report from different data must not authorize execution after a source change."""

    registry, plan = _primary_plan_and_registry()
    caller = CallerContext(role="ClaimsAnalystFR", country="FR")
    decision = authorize(plan, caller, registry)
    compiled = DuckDBCompiler(registry).compile(plan, decision, caller, PRIMARY_QUESTION)
    data_dir = tmp_path / "curated"
    data_dir.mkdir()
    for source in (REPOSITORY_ROOT / "data" / "curated").glob("*.csv"):
        (data_dir / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    quality = validate_curated_data(data_dir, registry)
    (data_dir / "acdoca_financials.csv").write_text(
        (data_dir / "acdoca_financials.csv").read_text(encoding="utf-8").replace("9000.00", "9001.00", 1),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="quality|digest|source"):
        LocalDuckDBAdapter(data_dir, registry).execute(compiled, decision, caller, quality)


def test_provenance_is_append_only_and_bound_to_the_actual_execution(tmp_path: Path) -> None:
    """Accepting caller-assembled provenance must permit an answer to be falsely attributed."""

    registry, plan = _primary_plan_and_registry()
    caller = CallerContext(role="ClaimsAnalystFR", country="FR")
    decision = authorize(plan, caller, registry)
    compiled = DuckDBCompiler(registry).compile(plan, decision, caller, PRIMARY_QUESTION)
    quality = validate_curated_data(REPOSITORY_ROOT / "data" / "curated", registry)
    execution = LocalDuckDBAdapter(REPOSITORY_ROOT / "data" / "curated", registry).execute(
        compiled, decision, caller, quality
    )
    store = ProvenanceStore(tmp_path / "provenance.sqlite")

    provenance = store.record(question=PRIMARY_QUESTION, execution=execution)

    assert provenance.execution_digest == execution.digest
    assert provenance.plan_digest == compiled.plan_digest
    assert provenance.parameter_digest == compiled.parameter_digest
    assert provenance.source_digests == execution.source_digests
    assert set(provenance.local_sources) == {"acdoca_financials.csv", "billing_documents.csv", "business_partners.csv", "sales_orders.csv"}
    assert provenance.mapping_evidence
    assert "field:amount_in_company_currency_eur" in provenance.field_evidence
    assert "rule:sap:QualifyingPosting" in provenance.semantic_versions
    assert provenance.semantic_versions["policy:authorization"] == "1.0.0"
    assert provenance.authorization_outcome == "ALLOWED"
    assert not hasattr(store, "connection")
