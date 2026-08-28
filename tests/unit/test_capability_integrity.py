"""Adversarial integrity tests for issued execution capabilities and provenance."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

import semantic_layer.adapters.duckdb as duckdb_adapter
import semantic_layer.compiler.base as compiler_base
import semantic_layer.control as control_module
import semantic_layer.governance.policy as policy_module
import semantic_layer.provenance.store as provenance_module
import semantic_layer.quality.checks as quality_module
from semantic_layer.adapters import LocalDuckDBAdapter
from semantic_layer.compiler import CompiledQuery, DuckDBCompiler
from semantic_layer.governance import AuthorizationDecision, authorize
from semantic_layer.models import CallerContext, RelationshipPath
from semantic_layer.provenance import ProvenanceStore
from semantic_layer.quality import QualityReport, validate_curated_data
from semantic_layer.query_planner import build_plan
from semantic_layer.registry import SemanticRegistry

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_QUESTION = (
    "Find French motor-insurance customers with at least three qualifying claims "
    "in the last 12 months and total incurred loss above EUR 20,000."
)


def _issued_context():
    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    plan = build_plan(PRIMARY_QUESTION, role="ClaimsAnalystFR", registry=registry)
    caller = CallerContext(role="ClaimsAnalystFR", country="FR")
    decision = authorize(plan, caller, registry)
    query = DuckDBCompiler(registry).compile(plan, decision, caller, PRIMARY_QUESTION)
    quality = validate_curated_data(REPOSITORY_ROOT / "data" / "curated", registry)
    adapter = LocalDuckDBAdapter(REPOSITORY_ROOT / "data" / "curated", registry)
    return registry, plan, caller, decision, query, quality, adapter


def test_signing_authority_is_not_part_of_the_public_package_api() -> None:
    """The capability signer must stay behind the internal control-plane boundary."""

    import semantic_layer

    assert "signature" not in getattr(semantic_layer, "__all__", ())
    assert "has_valid_signature" not in getattr(semantic_layer, "__all__", ())
    assert not hasattr(semantic_layer, "signature")
    assert not hasattr(semantic_layer, "has_valid_signature")
    assert not hasattr(control_module, "_SIGNING_KEY")
    assert not hasattr(control_module, "signature")
    assert not hasattr(control_module, "has_valid_signature")
    assert "_sign" not in control_module.__all__


def test_capabilities_expose_no_callable_issue_helpers() -> None:
    """A public issuance helper must allow an attacker to mint an execution capability."""

    for capability in (CompiledQuery, AuthorizationDecision, QualityReport):
        assert not hasattr(capability, "_issue")
    for module, helper in (
        (compiler_base, "_create_compiled_query"),
        (policy_module, "_issue"),
        (quality_module, "_create_quality_report"),
        (duckdb_adapter, "_create_execution_result"),
        (provenance_module, "_create_provenance"),
    ):
        assert not hasattr(module, helper)


def test_issued_query_decision_and_quality_are_immutable() -> None:
    """Mutable capability fields must let callers alter SQL, policy, or quality after issuance."""

    _, _, _, decision, query, quality, _ = _issued_context()

    with pytest.raises(AttributeError):
        query.sql = "SELECT 'forged'"
    with pytest.raises(AttributeError):
        query.parameters += ("forged",)
    with pytest.raises(AttributeError):
        decision.allowed = False
    with pytest.raises(AttributeError):
        quality.status = "FAIL"
    with pytest.raises(TypeError):
        query.field_evidence["field:claim_id"] = "forged"
    with pytest.raises(TypeError):
        quality.source_digests["claims.csv"] = "forged"


def test_adapter_detects_low_level_query_decision_and_quality_tampering() -> None:
    """Rebinding slots with object internals must fail integrity verification before DuckDB runs."""

    _, _, caller, decision, query, quality, adapter = _issued_context()
    object.__setattr__(query, "sql", "SELECT 'forged'")

    with pytest.raises(ValueError, match="integrity|signature"):
        adapter.execute(query, decision, caller, quality)


def test_compiler_rejects_capability_subclasses_that_override_integrity() -> None:
    """An attacker must not bypass signed authorization by overriding a virtual check."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    plan = build_plan(PRIMARY_QUESTION, role="ClaimsAnalystFR", registry=registry)
    caller = CallerContext(role="ClaimsAnalystFR", country="FR")

    class ForgedDecision(AuthorizationDecision):
        allowed = True
        plan_digest = "forged"
        caller_digest = "forged"
        registry_digest = "forged"
        reason_code = "ALLOWED"

        def __init__(self) -> None:
            pass

        def _matches(self, *_args: object, **_kwargs: object) -> bool:
            return True

    with pytest.raises((TypeError, ValueError), match="authorization|capability"):
        DuckDBCompiler(registry).compile(plan, ForgedDecision(), caller, PRIMARY_QUESTION)


def test_adapter_rejects_capability_subclasses_that_override_integrity() -> None:
    """Execution must accept only exact issued query and policy artifact types."""

    _, _, caller, decision, query, quality, adapter = _issued_context()

    class ForgedQuery(CompiledQuery):
        def _verify_integrity(self) -> bool:
            return True

    forged = object.__new__(ForgedQuery)
    with pytest.raises((TypeError, ValueError), match="query|capability|integrity"):
        adapter.execute(forged, decision, caller, quality)

    _, _, caller, decision, query, quality, adapter = _issued_context()
    object.__setattr__(decision, "allowed", False)

    with pytest.raises(ValueError, match="integrity|signature"):
        adapter.execute(query, decision, caller, quality)

    _, _, caller, decision, query, quality, adapter = _issued_context()
    object.__setattr__(quality, "status", "FAIL")

    with pytest.raises(ValueError, match="integrity|signature"):
        adapter.execute(query, decision, caller, quality)


def test_quality_rejects_missing_required_csv_schema_field(tmp_path: Path) -> None:
    """A report must not pass when a required canonical source column is absent."""

    for source in (REPOSITORY_ROOT / "data" / "curated").glob("*.csv"):
        contents = source.read_text(encoding="utf-8")
        if source.name == "claims.csv":
            contents = contents.replace(",incurred_loss_eur", "", 1)
            contents = "\n".join(",".join(row.split(",")[:-1]) for row in contents.splitlines()) + "\n"
        (tmp_path / source.name).write_text(contents, encoding="utf-8")

    report = validate_curated_data(tmp_path)

    assert report.status == "FAIL"
    assert "MISSING_SCHEMA_FIELD" in {issue.code for issue in report.issues}


def test_compiler_rejects_a_relationship_with_correct_nodes_but_wrong_predicate() -> None:
    """Comparing only source/target must let an ungoverned relationship change the query meaning."""

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    plan = build_plan(PRIMARY_QUESTION, role="ClaimsAnalystFR", registry=registry)
    mutated = plan.model_copy(
        update={
            "relationships": [
                RelationshipPath(
                    source="insurance:Customer",
                    predicate="insurance:submitsClaim",
                    target="insurance:Policy",
                ),
                plan.relationships[1],
            ]
        }
    )
    caller = CallerContext(role="ClaimsAnalystFR", country="FR")
    decision = authorize(mutated, caller, registry)

    with pytest.raises(ValueError, match="relationship"):
        DuckDBCompiler(registry).compile(mutated, decision, caller, PRIMARY_QUESTION)


def test_question_and_concepts_are_bound_to_plan_execution_and_local_provenance(tmp_path: Path) -> None:
    """A different question or cloud mapping name must not be attested for a local execution."""

    _, _, caller, decision, query, quality, adapter = _issued_context()
    execution = adapter.execute(query, decision, caller, quality)
    store = ProvenanceStore(tmp_path / "provenance.sqlite")

    with pytest.raises(ValueError, match="question"):
        store.record(question="Find German claims.", execution=execution)
    provenance = store.record(question=PRIMARY_QUESTION, execution=execution)

    assert provenance.concepts
    assert provenance.question_digest == query.question_digest
    assert provenance.physical_sources == tuple(provenance.local_sources.values())
    assert all("databricks://" not in source for source in provenance.physical_sources)
    assert all("customer_id" in evidence or "claim" in evidence or "policy" in evidence for evidence in provenance.field_evidence.values())


def test_provenance_detects_mutated_execution_and_signed_storage_rows(tmp_path: Path) -> None:
    """Forged execution objects or altered SQLite documents must never be attested as real results."""

    _, _, caller, decision, query, quality, adapter = _issued_context()
    execution = adapter.execute(query, decision, caller, quality)
    object.__setattr__(execution, "plan_digest", "forged")
    store = ProvenanceStore(tmp_path / "provenance.sqlite")

    with pytest.raises(ValueError, match="integrity|signature"):
        store.record(question=PRIMARY_QUESTION, execution=execution)


def test_authorization_outcome_is_bound_through_execution_and_provenance(tmp_path: Path) -> None:
    """An altered authorization outcome must invalidate execution evidence before storage."""

    _, _, caller, decision, query, quality, adapter = _issued_context()
    execution = adapter.execute(query, decision, caller, quality)
    assert execution.authorization_outcome == decision.reason_code == "ALLOWED"
    object.__setattr__(execution, "authorization_outcome", "DENIED")

    assert execution._verify_integrity() is False
    with pytest.raises(ValueError, match="integrity|signature"):
        ProvenanceStore(tmp_path / "provenance.sqlite").record(
            question=PRIMARY_QUESTION, execution=execution
        )


def test_provenance_nested_metadata_is_defensive_and_immutable(tmp_path: Path) -> None:
    """Mutating a returned metadata container must not alter the signed record."""

    _, _, caller, decision, query, quality, adapter = _issued_context()
    execution = adapter.execute(query, decision, caller, quality)
    store = ProvenanceStore(tmp_path / "provenance.sqlite")
    provenance = store.record(question=PRIMARY_QUESTION, execution=execution)
    original_products = list(provenance.data_products)
    products = provenance.data_products
    products.append("ForgedProduct")
    sources = provenance.source_digests
    sources["claims.csv"] = "forged"

    assert provenance.data_products == original_products
    assert provenance.source_digests == execution.source_digests
    assert provenance._verify_integrity()


def test_execution_uses_the_validated_snapshot_when_source_changes_after_digest_check(tmp_path: Path) -> None:
    """A source race after validation must not change the rows that are attested."""

    registry, _, caller, decision, query, _, _ = _issued_context()
    data_dir = tmp_path / "curated"
    data_dir.mkdir()
    for source in (REPOSITORY_ROOT / "data" / "curated").glob("*.csv"):
        (data_dir / source.name).write_bytes(source.read_bytes())
    quality = validate_curated_data(data_dir, registry)
    adapter = LocalDuckDBAdapter(data_dir, registry)
    original_source_digests = adapter._source_digests
    changed = False

    def digest_then_replace() -> dict[str, str]:
        nonlocal changed
        digests = original_source_digests()
        if not changed:
            changed = True
            claims = data_dir / "claims.csv"
            claims.write_text(claims.read_text(encoding="utf-8").replace("9000.00", "9001.00", 1), encoding="utf-8")
        return digests

    adapter._source_digests = digest_then_replace
    execution = adapter.execute(query, decision, caller, quality)

    assert execution == [
        {"customer_id": "FR_001", "country": "FR", "claim_count": 3, "total_incurred_loss_eur": 24000.0},
        {"customer_id": "FR_002", "country": "FR", "claim_count": 3, "total_incurred_loss_eur": 25000.0},
    ]


def test_provenance_can_be_reopened_in_a_new_process_with_a_configured_key(tmp_path: Path) -> None:
    """A configured signing key lets a second process verify persisted evidence."""

    database = tmp_path / "provenance.sqlite"
    key_file = tmp_path / "signing-key"
    key_file.write_text("11" * 32, encoding="ascii")
    source_root = REPOSITORY_ROOT.as_posix()
    script = """
from pathlib import Path
from semantic_layer.adapters import LocalDuckDBAdapter
from semantic_layer.compiler import DuckDBCompiler
from semantic_layer.governance import authorize
from semantic_layer.provenance import ProvenanceStore
from semantic_layer.quality import validate_curated_data
from semantic_layer.query_planner import build_plan
from semantic_layer.registry import SemanticRegistry

root = Path(__import__("os").environ["SEMANTIC_LAYER_ROOT"])
question = "Find French motor-insurance customers with at least three qualifying claims in the last 12 months and total incurred loss above EUR 20,000."
registry = SemanticRegistry.from_repository(root)
plan = build_plan(question, role="ClaimsAnalystFR", registry=registry)
authorization = authorize(plan, plan.caller, registry)
compiled = DuckDBCompiler(registry).compile(plan, authorization, plan.caller, question)
quality = validate_curated_data(root / "data" / "curated", registry)
execution = LocalDuckDBAdapter(root / "data" / "curated", registry).execute(compiled, authorization, plan.caller, quality)
store = ProvenanceStore(Path(__import__("os").environ["SEMANTIC_LAYER_DB"]))
record = store.record(question=question, execution=execution)
print(record.query_id)
"""
    env = os.environ | {
        "PYTHONPATH": str(REPOSITORY_ROOT / "src"),
        "SEMANTIC_LAYER_ROOT": source_root,
        "SEMANTIC_LAYER_DB": str(database),
        "SEMANTIC_LAYER_SIGNING_KEY_FILE": str(key_file),
    }
    created = subprocess.run([sys.executable, "-c", script], check=True, capture_output=True, text=True, env=env)
    query_id = created.stdout.strip()
    reopened = subprocess.run(
        [
            sys.executable,
            "-c",
            "from semantic_layer.provenance import ProvenanceStore; import os; from pathlib import Path; print(ProvenanceStore(Path(os.environ['SEMANTIC_LAYER_DB'])).get(os.environ['SEMANTIC_LAYER_QUERY_ID']).quality_status)",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env | {"SEMANTIC_LAYER_QUERY_ID": query_id},
    )

    assert reopened.stdout.strip() == "PASS"


def test_provenance_rejects_signed_record_substitution(tmp_path: Path) -> None:
    """A valid signed document copied under another SQLite key must fail closed."""

    _, _, caller, decision, query, quality, adapter = _issued_context()
    execution = adapter.execute(query, decision, caller, quality)
    store = ProvenanceStore(tmp_path / "provenance.sqlite")
    first = store.record(question=PRIMARY_QUESTION, execution=execution)
    second = store.record(question=PRIMARY_QUESTION, execution=execution)
    document, stored_signature = store._connection.execute(
        "SELECT document, signature FROM provenance WHERE query_id = ?", (first.query_id,)
    ).fetchone()
    store._connection.execute(
        "UPDATE provenance SET document = ?, signature = ? WHERE query_id = ?",
        (document, stored_signature, second.query_id),
    )
    store._connection.commit()

    with pytest.raises(ValueError, match="query_id|integrity|chain"):
        store.get(second.query_id)


def test_provenance_detects_deletion_from_the_sqlite_chain(tmp_path: Path) -> None:
    """Deleting a persisted record must invalidate the durable chain checkpoint."""

    _, _, caller, decision, query, quality, adapter = _issued_context()
    execution = adapter.execute(query, decision, caller, quality)
    store = ProvenanceStore(tmp_path / "provenance.sqlite")
    first = store.record(question=PRIMARY_QUESTION, execution=execution)
    second = store.record(question=PRIMARY_QUESTION, execution=execution)
    store._connection.execute("DELETE FROM provenance WHERE query_id = ?", (second.query_id,))
    store._connection.commit()

    with pytest.raises(ValueError, match="chain|checkpoint|integrity"):
        store.get(first.query_id)


def test_provenance_rejects_checkpoint_rewrite_without_a_valid_signature(tmp_path: Path) -> None:
    """A deleted tail plus a forged shortened checkpoint must remain detectable."""

    _, _, caller, decision, query, quality, adapter = _issued_context()
    execution = adapter.execute(query, decision, caller, quality)
    store = ProvenanceStore(tmp_path / "provenance.sqlite")
    first = store.record(question=PRIMARY_QUESTION, execution=execution)
    second = store.record(question=PRIMARY_QUESTION, execution=execution)
    store._connection.execute("DELETE FROM provenance WHERE query_id = ?", (second.query_id,))
    first_hash = store._connection.execute(
        "SELECT row_hash FROM provenance WHERE query_id = ?", (first.query_id,)
    ).fetchone()[0]
    store._connection.execute(
        "UPDATE provenance_checkpoint SET sequence = 1, row_hash = ? WHERE checkpoint_id = 1",
        (first_hash,),
    )
    store._connection.commit()

    with pytest.raises(ValueError, match="checkpoint|signature|integrity"):
        store.get(first.query_id)
