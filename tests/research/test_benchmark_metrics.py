"""Focused contracts for the deterministic CIFRE benchmark metrics."""

from __future__ import annotations

from pathlib import Path

import pytest

from semantic_layer.research.benchmark_runner import (
    QueryRecord,
    _validate_corpus,
    aggregate_metrics,
    build_hash_manifest,
    score_query,
    validate_hash_manifest,
    validate_result_id_references,
)
from semantic_layer.research.contracts import CONDITIONS, Status


def test_status_gated_metric_hand_fixtures() -> None:
    fixtures = [
        (Status.SUCCESS, Status.SUCCESS, ["1", "2"], ["1", "3"], False, "0.500000"),
        (Status.SUCCESS, Status.EMPTY_RESULT, ["1"], [], False, None),
        (Status.EMPTY_RESULT, Status.EMPTY_RESULT, [], [], False, None),
        (Status.UNSUPPORTED, Status.SUCCESS, [], [], False, None),
        (Status.SUCCESS, Status.SUCCESS, ["1", "2"], ["1", "2"], True, "1.000000"),
    ]

    for expected, observed, gold, predicted, exact, value in fixtures:
        metrics = score_query(expected, observed, gold, predicted)
        assert metrics.applicable is (expected is Status.SUCCESS and observed is Status.SUCCESS)
        assert metrics.exact_set is exact if metrics.applicable else metrics.exact_set is None
        assert metrics.precision == value
        assert metrics.recall == value
        assert metrics.f1 == value

    both_empty = score_query(Status.SUCCESS, Status.SUCCESS, [], [])
    assert both_empty.applicable is True
    assert both_empty.exact_set is True
    assert both_empty.precision == "1.000000"
    assert both_empty.recall == "1.000000"
    assert both_empty.f1 == "1.000000"

    one_empty = score_query(Status.SUCCESS, Status.SUCCESS, ["1"], [])
    assert one_empty.precision == "0.000000"
    assert one_empty.recall == "0.000000"
    assert one_empty.f1 == "0.000000"


def test_aggregate_metrics_is_status_gated_and_relaxed_candidates_never_score() -> None:
    records = [
        QueryRecord(
            corpus_id="cifre-synthetic-aqr-v2",
            query_id="Q01",
            condition=CONDITIONS[1],
            expected_status=Status.SUCCESS,
            observed_status=Status.SUCCESS,
            gold_note_numbers=("3345100",),
            predicted_note_numbers=("3345100",),
            relaxed_candidates=("9999999",),
        ),
        QueryRecord(
            corpus_id="cifre-synthetic-aqr-v2",
            query_id="Q02",
            condition=CONDITIONS[1],
            expected_status=Status.SUCCESS,
            observed_status=Status.EMPTY_RESULT,
            gold_note_numbers=("2765001",),
            predicted_note_numbers=(),
            relaxed_candidates=("2765001",),
        ),
    ]
    aggregate = aggregate_metrics(records)

    assert aggregate["query_count"] == 2
    assert aggregate["status_counts"] == {
        "SUCCESS": 1,
        "UNSUPPORTED": 0,
        "SYNTAX_ERROR": 0,
        "EXECUTION_ERROR": 0,
        "EMPTY_RESULT": 1,
    }
    assert aggregate["answer_metrics"]["applicable_count"] == 1
    assert aggregate["answer_metrics"]["not_applicable_count"] == 1
    assert aggregate["answer_metrics"]["exact_set"]["value"] == "1.000000"
    assert aggregate["operational_metrics"]["strict_empty_rate"]["value"] == "0.500000"


def test_recovery_success_rate_uses_recovery_attempts_as_denominator() -> None:
    records = [
        QueryRecord(
            corpus_id="cifre-synthetic-aqr-v1",
            query_id="Q01",
            condition=CONDITIONS[1],
            expected_status=Status.SUCCESS,
            observed_status=Status.SUCCESS,
            recovery_attempted=True,
            recovery_success=True,
        ),
        QueryRecord(
            corpus_id="cifre-synthetic-aqr-v1",
            query_id="Q02",
            condition=CONDITIONS[1],
            expected_status=Status.UNSUPPORTED,
            observed_status=Status.UNSUPPORTED,
        ),
    ]

    metric = aggregate_metrics(records)["operational_metrics"]["recovery_success_rate"]

    assert metric == {"value": "1.000000", "numerator": 1, "denominator": 1}


def test_hash_manifest_includes_tracked_examples_files(tmp_path: Path) -> None:
    import subprocess

    example = tmp_path / "examples" / "nested" / "fixture.txt"
    example.parent.mkdir(parents=True)
    example.write_text("tracked example\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "examples/nested/fixture.txt"], cwd=tmp_path, check=True)

    manifest = build_hash_manifest(tmp_path)

    assert [entry["path"] for entry in manifest.entries] == ["examples/nested/fixture.txt"]


def test_corpus_validation_requires_exact_corpus_and_query_ids() -> None:
    valid_records = [
        {"id": f"Q{index:02d}", "corpus_id": "cifre-synthetic-aqr-v1"} for index in range(1, 41)
    ]
    valid = {"corpus_id": "cifre-synthetic-aqr-v1", "records": valid_records}
    _validate_corpus(valid)

    wrong_corpus = {**valid, "corpus_id": "other-aqr-v1"}
    with pytest.raises(ValueError, match="exact corpus ID"):
        _validate_corpus(wrong_corpus)

    wrong_query_ids = {
        **valid,
        "records": [*valid_records[:-1], {**valid_records[-1], "id": "Q41"}],
    }
    with pytest.raises(ValueError, match="exact query IDs"):
        _validate_corpus(wrong_query_ids)

    _validate_corpus(
        {
            "corpus_id": "cifre-synthetic-aqr-v2",
            "records": [
                {"id": f"Q{index:02d}", "corpus_id": "cifre-synthetic-aqr-v2"}
                for index in range(1, 53)
            ],
        }
    )


def test_result_ids_are_unique_and_reference_composite_keys() -> None:
    result = {
        "corpus_runs": [
            {
                "corpus_id": "cifre-synthetic-aqr-v1",
                "result_ids": ["cifre-synthetic-aqr-v1:deterministic_bounded_repair:Q01"],
            }
        ],
        "per_query": [
            {
                "corpus_id": "cifre-synthetic-aqr-v1",
                "condition": "deterministic_bounded_repair",
                "query_id": "Q01",
            }
        ],
    }
    validate_result_id_references(result)

    duplicate_tuple = {
        **result,
        "per_query": [*result["per_query"], dict(result["per_query"][0])],
    }
    with pytest.raises(ValueError, match="duplicate"):
        validate_result_id_references(duplicate_tuple)

    wrong_reference = {
        **result,
        "corpus_runs": [
            {
                "corpus_id": "cifre-synthetic-aqr-v1",
                "result_ids": ["Q01"],
            }
        ],
    }
    with pytest.raises(ValueError, match="result ID"):
        validate_result_id_references(wrong_reference)


def test_result_hash_manifest_rejects_mutated_input(tmp_path: Path) -> None:
    import subprocess

    source = tmp_path / "semantic" / "ontology" / "fixture.ttl"
    source.parent.mkdir(parents=True)
    source.write_text("@prefix ex: <https://example.org/> .\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "semantic/ontology/fixture.ttl"], cwd=tmp_path, check=True)

    manifest = build_hash_manifest(tmp_path)
    artifact = {"hash_manifest": manifest}
    source.write_text("@prefix ex: <https://example.org/mutated/> .\n", encoding="utf-8")

    with pytest.raises(ValueError, match="hash manifest"):
        validate_hash_manifest(artifact, tmp_path)


def test_runner_no_longer_exposes_fake_comparative_paradigms() -> None:
    import semantic_layer.research.benchmark_runner as runner_module

    assert not hasattr(runner_module, "ParadigmMetrics")
    assert not hasattr(runner_module, "EvaluationReport")
    assert not hasattr(runner_module, "vector_rag")
    assert not hasattr(runner_module, "hallucination")
    assert not hasattr(runner_module, "VSR")
