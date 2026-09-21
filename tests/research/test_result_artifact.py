"""Focused result-artifact tests for the deterministic CIFRE runner."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import jsonschema
import pytest
import yaml

import semantic_layer.research.benchmark_runner as benchmark_runner_module
from semantic_layer.kg.loader import SAPKnowledgeGraph
from semantic_layer.research.benchmark_runner import (
    _VALIDATION_DATA_PATHS,
    _VALIDATION_SHAPE_PATHS,
    BenchmarkRunner,
    _reject_metadata_nulls,
    _validate_corpus,
    build_hash_manifest,
    build_validation_metadata,
    validate_result_id_references,
)
from semantic_layer.research.contracts import CONDITIONS, canonical_json, load_and_validate_result
from semantic_layer.validation import finalize_research_artifact

ROOT = Path(__file__).parents[2]


def _knowledge_graph() -> SAPKnowledgeGraph:
    graph = SAPKnowledgeGraph()
    graph.load_ontologies(
        [
            ROOT / "semantic/ontology/sap_ppms.ttl",
            ROOT / "semantic/ontology/sap_support.ttl",
            ROOT / "semantic/data/sap_support_graph.ttl",
        ]
    )
    return graph


def test_runner_builds_schema_valid_v1_v2_two_condition_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    validation_calls: list[Path] = []
    original_validation_builder = benchmark_runner_module.build_validation_metadata

    def record_validation_builder(root: Path) -> dict[str, object]:
        validation_calls.append(root)
        return original_validation_builder(root)

    monkeypatch.setattr(
        benchmark_runner_module,
        "build_validation_metadata",
        record_validation_builder,
    )
    result_path = tmp_path / "cifre-benchmark-result.json"
    runner = BenchmarkRunner(
        _knowledge_graph(),
        dataset_paths=(
            ROOT / "tests/research/benchmark_dataset_v1.yaml",
            ROOT / "tests/research/benchmark_dataset_v2.yaml",
        ),
        result_path=result_path,
    )

    result = runner.run()

    assert result_path.is_file()
    assert result["schema_version"] == "1.0.0"
    assert [run["corpus_id"] for run in result["corpus_runs"]] == [
        "cifre-synthetic-aqr-v1",
        "cifre-synthetic-aqr-v2",
    ]
    assert len(result["corpus_runs"]) == 2
    assert len(result["per_query"]) == (40 + 52) * 2
    for corpus_run in result["corpus_runs"]:
        assert corpus_run["conditions"] == list(CONDITIONS)
        assert corpus_run["query_count"] in {40, 52}
        assert corpus_run["aggregate"]["condition_ids"] == list(CONDITIONS)
        assert set(corpus_run["aggregate"]["by_condition"]) == set(CONDITIONS)
        assert len(corpus_run["result_ids"]) == corpus_run["query_count"] * 2

    validate_result_id_references(result)
    loaded = load_and_validate_result(result_path)
    assert loaded == result
    assert validation_calls == [ROOT]


def test_result_metadata_is_deterministic_and_has_no_timestamp_or_nan(
    tmp_path: Path,
) -> None:
    result_path = tmp_path / "cifre-benchmark-result.json"
    result = BenchmarkRunner(
        _knowledge_graph(),
        dataset_paths=(
            ROOT / "tests/research/benchmark_dataset_v1.yaml",
            ROOT / "tests/research/benchmark_dataset_v2.yaml",
        ),
        result_path=result_path,
    ).run()
    encoded = json.dumps(result, sort_keys=True, allow_nan=False)

    assert "timestamp" not in encoded.casefold()
    assert '"nan"' not in encoded.casefold()
    assert result["environment"]["lock_sha256"]
    assert result["hash_manifest"]["entries"]
    assert result["namespace_registry"]["legacy_uris_rejected"]
    assert result["validation"]["combined_graph"]["inference"] == "rdfs"
    assert all(value is not None for value in result["environment"].values())


def test_validation_metadata_records_truthful_complete_matrix() -> None:
    metadata = build_validation_metadata(ROOT)
    assert build_validation_metadata(ROOT) == metadata
    rows = {row["check_id"]: row for row in metadata["checks"]}

    assert list(rows) == [
        "SUPPORT_VALID",
        "SUPPORT_INVALID",
        "ERP_VALID",
        "ERP_INVALID",
        "COMBINED_VALID",
        "PREREQUISITE_CYCLE_DEPTH",
    ]
    assert rows["SUPPORT_VALID"]["observed_conforms"] is True
    assert rows["SUPPORT_INVALID"]["observed_conforms"] is False
    assert rows["ERP_VALID"]["observed_conforms"] is True
    assert rows["ERP_INVALID"]["observed_conforms"] is False
    assert rows["COMBINED_VALID"]["observed_conforms"] is True
    assert rows["SUPPORT_INVALID"]["result"] == "EXPECTED_NONCONFORMANT"
    assert rows["ERP_INVALID"]["result"] == "EXPECTED_NONCONFORMANT"
    assert {row["scope"] for row in rows.values()} == {"support", "erp", "combined"}
    algorithm_cases = rows["PREREQUISITE_CYCLE_DEPTH"]["algorithm_cases"]
    assert algorithm_cases[0] == {
        "fixture": "support-prerequisite-cycle.ttl",
        "provenance_dataset_id": "cifre-synthetic-support-prerequisite-cycle-v1",
        "cycle_detected": True,
        "cycle_edges": [["A", "B"], ["B", "C"], ["C", "A"]],
        "reachable_unique": ["B", "C"],
        "target_excluded": True,
        "depth_limit": 16,
        "truncated": False,
        "status": "SUCCESS",
        "reason": None,
    }
    assert algorithm_cases[1] == {
        "fixture": "support-prerequisite-depth17.ttl",
        "provenance_dataset_id": "cifre-synthetic-support-prerequisite-depth17-v1",
        "cycle_detected": False,
        "cycle_edges": [],
        "reachable_unique": [f"N{index}" for index in range(1, 17)],
        "target_excluded": True,
        "depth_limit": 16,
        "truncated": True,
        "status": "EMPTY_RESULT",
        "reason": "PREREQUISITE_DEPTH_EXCEEDED",
    }
    for row in rows.values():
        assert "violation_count" in row
        assert row["data_sha256"]
        assert len(row["data_sha256"]) == len(row["data_paths"])
        assert len(row["shape_sha256"]) == len(row["shape_paths"])

    combined = metadata["combined_graph"]
    assert combined["construction_order"] == [
        "semantic/ontology/sap_support.ttl",
        "semantic/ontology/sap_ppms.ttl",
        "semantic/data/sap_support_graph.ttl",
        "semantic/ontology/sap_erp.ttl",
        "semantic/ontology/sample-graph-valid.ttl",
        "semantic/shapes/sap_support_shapes.ttl",
        "semantic/shapes/sap_erp_shapes.ttl",
    ]
    assert combined["data_paths"] == list(_VALIDATION_DATA_PATHS) + [
        "semantic/ontology/sample-graph-valid.ttl"
    ]
    assert combined["shape_paths"] == list(_VALIDATION_SHAPE_PATHS)
    assert combined["conforms"] is True


def test_validation_scope_is_required_and_closed_in_result_schema() -> None:
    schema = json.loads((ROOT / "tests/research/result_schema.json").read_bytes())
    row_schema = schema["$defs"]["validation"]["properties"]["checks"]["items"]

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(row_schema).validate({"check_id": "SUPPORT_VALID"})
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(row_schema).validate(
            {"check_id": "SUPPORT_VALID", "scope": "algorithm"}
        )


def test_corpus_preflight_fails_closed_when_declared_success_loses_grounding() -> None:
    corpus = yaml.safe_load(
        (ROOT / "tests/research/benchmark_dataset_v1.yaml").read_text(encoding="utf-8")
    )
    corpus["records"][0]["question"] = "Find notes for alert UNKNOWN_ALERT."

    with pytest.raises(ValueError, match="does not reach a supported grounded intent"):
        _validate_corpus(corpus)


@pytest.mark.parametrize("forbidden", ["None", "NaN", "Infinity", "-Infinity"])
def test_result_rejects_forbidden_string_sentinels_recursively(forbidden: str) -> None:
    metadata = {
        "environment": {},
        "namespace_registry": {},
        "validation": {},
        "hash_manifest": {},
        "nested": [{"value": forbidden}],
    }

    with pytest.raises(ValueError, match="forbidden"):
        _reject_metadata_nulls(metadata)


@pytest.mark.parametrize("forbidden", [float("nan"), float("inf"), float("-inf")])
def test_result_rejects_non_finite_floats_recursively(forbidden: float) -> None:
    metadata = {
        "environment": {},
        "namespace_registry": {},
        "validation": {},
        "hash_manifest": {},
        "nested": [{"value": forbidden}],
    }

    with pytest.raises(ValueError, match="forbidden"):
        _reject_metadata_nulls(metadata)


def test_result_allows_legitimate_json_nulls_recursively() -> None:
    metadata = {
        "environment": {},
        "namespace_registry": {},
        "validation": {},
        "hash_manifest": {},
        "nested": [{"value": None}],
    }

    _reject_metadata_nulls(metadata)


@pytest.mark.parametrize("timestamp_key", ["timestamp", "generated_at", "created_at"])
def test_result_rejects_nested_timestamp_keys_across_artifact(timestamp_key: str) -> None:
    metadata = {
        "environment": {},
        "namespace_registry": {},
        "validation": {},
        "hash_manifest": {},
        "per_query": [{"provenance": {timestamp_key: "2026-09-20T00:00:00Z"}}],
    }

    with pytest.raises(ValueError, match="timestamp key"):
        _reject_metadata_nulls(metadata)


def test_cli_output_path_is_caller_supplied_and_not_canonical(tmp_path: Path) -> None:
    canonical = ROOT / "results/latest_benchmark.json"
    before = canonical.read_bytes() if canonical.exists() else None
    temporary = tmp_path / "temporary-result.json"
    assert temporary != canonical
    assert not temporary.exists()
    assert before is None or canonical.read_bytes() == before


def test_finalizer_rejects_unsupported_environment_without_replacing_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "results/latest_benchmark.json"
    destination.parent.mkdir()
    sentinel = b"previous canonical artifact\n"
    destination.write_bytes(sentinel)
    invalid = json.loads((ROOT / "results/latest_benchmark.json").read_bytes())
    invalid["environment"]["pip_version"] = "24.0"
    real_run = subprocess.run
    real_run(["git", "init", "-q"], cwd=tmp_path, check=True)

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "--output" not in command:
            return real_run(command, **kwargs)
        output = Path(command[command.index("--output") + 1])
        invalid["hash_manifest"] = build_hash_manifest(tmp_path).to_dict()
        output.write_bytes(canonical_json(invalid) + b"\n")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("semantic_layer.validation.subprocess.run", fake_run)

    with pytest.raises(ValueError, match="pip_version"):
        finalize_research_artifact(tmp_path)

    assert destination.read_bytes() == sentinel
