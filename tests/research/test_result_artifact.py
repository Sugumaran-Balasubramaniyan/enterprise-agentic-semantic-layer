"""Focused result-artifact tests for the deterministic CIFRE runner."""

from __future__ import annotations

import json
from pathlib import Path

from semantic_layer.kg.loader import SAPKnowledgeGraph
from semantic_layer.research.benchmark_runner import (
    BenchmarkRunner,
    validate_result_id_references,
)
from semantic_layer.research.contracts import CONDITIONS, load_and_validate_result

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


def test_runner_builds_schema_valid_v1_v2_two_condition_artifact(tmp_path: Path) -> None:
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


def test_cli_output_path_is_caller_supplied_and_not_canonical(tmp_path: Path) -> None:
    canonical = ROOT / "results/latest_benchmark.json"
    before = canonical.read_bytes() if canonical.exists() else None
    temporary = tmp_path / "temporary-result.json"
    assert temporary != canonical
    assert not temporary.exists()
    assert before is None or canonical.read_bytes() == before
