from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest
import yaml

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
