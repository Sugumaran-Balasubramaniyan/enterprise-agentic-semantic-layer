from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest
import yaml
from rdflib import Graph

ROOT = Path(__file__).parents[2]
HISTORICAL = ROOT / "tests/research/benchmark_dataset.yaml"
LEGACY = ROOT / "tests/research/benchmark_dataset_legacy.yaml"
_SPEC = importlib.util.spec_from_file_location(
    "migrate_benchmark_v1", ROOT / "scripts/migrate_benchmark_v1.py"
)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
migrate_benchmark = _MODULE.migrate_benchmark
validate_migration_manifest = _MODULE.validate_migration_manifest
sha256_json = _MODULE._sha256_json
GRAPH_PATH = _MODULE.GRAPH_PATH


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_archival_copy_is_byte_identical() -> None:
    assert HISTORICAL.read_bytes() == LEGACY.read_bytes()
    assert hashlib.sha256(LEGACY.read_bytes()).hexdigest() == (
        "04bb3d5f7c0516c9eca400ea22026df7096281fa0df148b38cbfe81ce930307f"
    )


def test_migration_emits_normalized_v1_v2_and_signed_manifest(tmp_path: Path) -> None:
    v1 = tmp_path / "benchmark_dataset_v1.yaml"
    v2 = tmp_path / "benchmark_dataset_v2.yaml"
    manifest_path = tmp_path / "benchmark_migration_manifest_v1.yaml"

    migrate_benchmark(LEGACY, v1, v2, manifest_path)

    v1_data = load_yaml(v1)
    v2_data = load_yaml(v2)
    manifest = load_yaml(manifest_path)
    expected_fields = [
        "id",
        "corpus_id",
        "version",
        "tier",
        "category",
        "question",
        "expected_status",
        "gold_note_numbers",
        "reflection_reason",
        "strict_constraints",
        "gold_policy",
    ]
    assert list(v1_data) == ["corpus_id", "version", "records"]
    assert list(v2_data) == ["corpus_id", "version", "records"]
    assert v1_data["corpus_id"] == "cifre-synthetic-aqr-v1"
    assert v1_data["version"] == "1.0.0"
    assert v2_data["corpus_id"] == "cifre-synthetic-aqr-v2"
    assert v2_data["version"] == "2.0.0"
    assert len(v1_data["records"]) == 40
    assert len(v2_data["records"]) == 52
    assert [r["id"] for r in v1_data["records"]] == [f"Q{i:02d}" for i in range(1, 41)]
    assert [r["id"] for r in v2_data["records"]] == [f"Q{i:02d}" for i in range(1, 53)]
    assert all(list(record) == expected_fields for record in v1_data["records"])
    assert all(list(record) == expected_fields for record in v2_data["records"])
    assert {record["corpus_id"] for record in v1_data["records"]} == {"cifre-synthetic-aqr-v1"}
    assert {record["version"] for record in v1_data["records"]} == {"1.0.0"}
    assert {record["corpus_id"] for record in v2_data["records"]} == {"cifre-synthetic-aqr-v2"}
    assert {record["version"] for record in v2_data["records"]} == {"2.0.0"}
    assert v1_data["records"][24]["gold_note_numbers"] == ["3012445", "3098110"]
    assert all(v1_data["records"][i]["expected_status"] == "EMPTY_RESULT" for i in range(32, 40))
    assert all(v1_data["records"][i]["gold_note_numbers"] == [] for i in range(32, 40))

    expected_v2 = {
        "Q41": (
            "negative_unknown_token",
            "UNSUPPORTED",
            "UNKNOWN_TOKEN",
            "Find notes unlicensed oracle system.",
        ),
        "Q42": (
            "negative_unknown_token",
            "UNSUPPORTED",
            "UNKNOWN_TOKEN",
            "Which notes resolve unexplained outage?",
        ),
        "Q43": (
            "negative_unknown_entity",
            "UNSUPPORTED",
            "UNKNOWN_ENTITY",
            "Find notes alert UNKNOWN_ALERT.",
        ),
        "Q44": (
            "negative_unknown_entity",
            "UNSUPPORTED",
            "UNKNOWN_ENTITY",
            "Find notes component ZZ-UNKNOWN.",
        ),
        "Q45": (
            "negative_ambiguity",
            "UNSUPPORTED",
            "AMBIGUOUS_INPUT",
            "Find notes alert TIME_OUT alert DBSQL_NO_MORE_CONNECTION.",
        ),
        "Q46": (
            "negative_ambiguity",
            "UNSUPPORTED",
            "AMBIGUOUS_INPUT",
            "Find notes component FI component MM.",
        ),
        "Q47": (
            "negative_unsupported_intent",
            "UNSUPPORTED",
            "UNSUPPORTED_INTENT",
            "Summarize support landscape in paragraph.",
        ),
        "Q48": (
            "negative_unsupported_intent",
            "UNSUPPORTED",
            "UNSUPPORTED_INTENT",
            "Recommend patch system.",
        ),
        "Q49": (
            "negative_strict_empty",
            "EMPTY_RESULT",
            "EMPTY_STRICT_RESULT",
            "Find notes alert TIME_OUT in component MM-PUR-PO at SP99.",
        ),
        "Q50": (
            "negative_strict_empty",
            "EMPTY_RESULT",
            "EMPTY_STRICT_RESULT",
            "Find notes alert DBSQL_NO_MORE_CONNECTION in component BC-DB-HDB at SP99.",
        ),
        "Q51": (
            "negative_strict_empty",
            "EMPTY_RESULT",
            "EMPTY_STRICT_RESULT",
            "Find notes resolving alert TIME_OUT on S/4HANA 2022 in component SD-SLS.",
        ),
        "Q52": (
            "negative_strict_empty",
            "EMPTY_RESULT",
            "EMPTY_STRICT_RESULT",
            "Find notes alert CALL_FUNCTION_NOT_FOUND in component SD-SLS.",
        ),
    }
    for record in v2_data["records"][40:]:
        assert (
            record["category"],
            record["expected_status"],
            record["reflection_reason"],
            record["question"],
        ) == expected_v2[record["id"]]
        assert record["tier"] == 0
        assert record["gold_note_numbers"] == []
        assert record["strict_constraints"] is True

    assert list(manifest) == [
        "schema_version",
        "source_path",
        "archival_path",
        "normalized_path",
        "record_ids",
        "changes",
        "records",
        "review",
    ]
    validate_migration_manifest(manifest)
    assert len(manifest["records"]) == 40
    assert manifest["review"] == {
        "reviewer_id": "repository-maintainer",
        "signoff_required": True,
        "signed_off": True,
    }


def test_migration_is_byte_stable(tmp_path: Path) -> None:
    outputs = [tmp_path / name for name in ("v1.yaml", "v2.yaml", "manifest.yaml")]
    migrate_benchmark(LEGACY, *outputs)
    first = [path.read_bytes() for path in outputs]
    migrate_benchmark(LEGACY, *outputs)
    assert [path.read_bytes() for path in outputs] == first


def test_migration_rejects_alternate_source_copy_before_writing_outputs(tmp_path: Path) -> None:
    alternate = tmp_path / "benchmark_dataset.yaml"
    alternate.write_bytes(LEGACY.read_bytes())
    outputs = [tmp_path / name for name in ("v1.yaml", "v2.yaml", "manifest.yaml")]

    with pytest.raises(ValueError, match="canonical historical/archive"):
        migrate_benchmark(alternate, *outputs)

    assert all(not path.exists() for path in outputs)


def test_migration_rejects_modified_alternate_source_before_writing_outputs(
    tmp_path: Path,
) -> None:
    alternate = tmp_path / "modified-benchmark_dataset.yaml"
    alternate.write_bytes(LEGACY.read_bytes() + b"\n# altered copy\n")
    outputs = [tmp_path / name for name in ("v1.yaml", "v2.yaml", "manifest.yaml")]

    with pytest.raises(ValueError, match="canonical historical/archive"):
        migrate_benchmark(alternate, *outputs)

    assert all(not path.exists() for path in outputs)


def test_canonical_historical_input_is_accepted_and_matches_archive(tmp_path: Path) -> None:
    outputs = [tmp_path / name for name in ("v1.yaml", "v2.yaml", "manifest.yaml")]

    migrate_benchmark(HISTORICAL, *outputs)

    assert all(path.exists() for path in outputs)


def test_manifest_validation_rejects_modified_canonical_archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = [tmp_path / name for name in ("v1.yaml", "v2.yaml", "manifest.yaml")]
    migrate_benchmark(LEGACY, *paths)
    modified_archive = tmp_path / "benchmark_dataset_legacy.yaml"
    modified_archive.write_bytes(LEGACY.read_bytes() + b"\n# altered archive\n")
    monkeypatch.setattr(_MODULE, "ARCHIVAL_PATH", modified_archive)

    with pytest.raises(ValueError, match="canonical historical/archive"):
        validate_migration_manifest(load_yaml(paths[2]))


def test_manifest_validator_rejects_unsigned_or_incomplete_derivation(tmp_path: Path) -> None:
    paths = [tmp_path / name for name in ("v1.yaml", "v2.yaml", "manifest.yaml")]
    migrate_benchmark(LEGACY, *paths)
    manifest = load_yaml(paths[2])
    manifest["records"][0]["signed_off"] = False
    with pytest.raises(ValueError, match="signed_off"):
        validate_migration_manifest(manifest)

    manifest = load_yaml(paths[2])
    del manifest["records"][0]["derivation_query"]["graph_sha256"]
    with pytest.raises(ValueError, match="graph_sha256"):
        validate_migration_manifest(manifest)


def test_stored_prerequisite_queries_execute_against_checked_in_graph() -> None:
    manifest = load_yaml(ROOT / "tests/research/benchmark_migration_manifest_v1.yaml")
    graph = Graph()
    graph.parse(GRAPH_PATH, format="turtle")
    closure_ids = {"Q25", "Q26", "Q27", "Q28", "Q29", "Q30", "Q31", "Q32"}
    for record in manifest["records"]:
        if record["id"] not in closure_ids:
            continue
        derivation = record["derivation_query"]
        rows = list(graph.query(derivation["text"]))
        note_numbers = sorted({str(row[-1]) for row in rows})
        assert note_numbers == record["gold_after"]
        assert "cifsup:hasPrerequisiteNote+" in derivation["text"]
        assert "3109922" in derivation["text"] or record["id"] not in {"Q25", "Q28", "Q31"}
        assert derivation["result"]["gold_after"] == note_numbers
        assert derivation["result_sha256"] == sha256_json(derivation["result"])


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("records", 0, "gold_before"), ["9999999"]),
        (("records", 32, "status_after"), "SUCCESS"),
        (("records", 24, "derivation_query", "graph_sha256"), "0" * 64),
        (("records", 24, "derivation_query", "kind"), "policy"),
        (("records", 24, "derivation_query", "text"), "SELECT 1"),
    ],
)
def test_manifest_validator_rejects_semantic_mutations(
    path: tuple[object, ...], value: object
) -> None:
    manifest = load_yaml(ROOT / "tests/research/benchmark_migration_manifest_v1.yaml")
    target: object = manifest
    for key in path[:-1]:
        target = target[key]  # type: ignore[index]
    target[path[-1]] = value  # type: ignore[index]
    with pytest.raises(ValueError):
        validate_migration_manifest(manifest)


def test_manifest_validator_rejects_result_mutation_even_with_recomputed_hash() -> None:
    manifest = load_yaml(ROOT / "tests/research/benchmark_migration_manifest_v1.yaml")
    manifest["records"][24]["derivation_query"]["result"]["gold_after"] = ["9999999"]
    manifest["records"][24]["derivation_query"]["result_sha256"] = sha256_json(
        manifest["records"][24]["derivation_query"]["result"]
    )
    with pytest.raises(ValueError):
        validate_migration_manifest(manifest)
