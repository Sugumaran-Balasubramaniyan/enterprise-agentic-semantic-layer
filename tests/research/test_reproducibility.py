"""Reproducibility and asset-boundary checks for the CIFRE prototype."""

from __future__ import annotations

import shutil
import hashlib
from pathlib import Path
import sys

import pytest
from rdflib import Graph, Literal, Namespace

from semantic_layer.validation import (
    assert_graph_isomorphic,
    run_asset_verification,
)
from semantic_layer.semantic_validation import validate_graph
import semantic_layer.research.benchmark_runner as benchmark_runner

ROOT = Path(__file__).resolve().parents[2]
CIFDATA = Namespace("https://example.org/cifre-kg/data/")


def test_validation_result_records_explicit_scope_and_asset_identity() -> None:
    result = validate_graph(
        ROOT / "semantic/data/sap_support_graph.ttl",
        ROOT / "semantic/shapes/sap_support_shapes.ttl",
        scope="support",
    )

    assert result.scope == "support"
    assert result.graph_scope == "support"
    assert len(result.data_sha256) == 64
    assert len(result.shapes_sha256) == 64
    assert result.provenance_dataset_id == "cifre-synthetic-support-ppms-v1"


def test_graph_parity_rejects_a_changed_generated_triple() -> None:
    checked_in = Graph().parse(ROOT / "semantic/data/sap_support_graph.ttl", format="turtle")
    generated = Graph().parse(ROOT / "semantic/data/sap_support_graph.ttl", format="turtle")
    generated.add((CIFDATA["support/test-drift"], CIFDATA.label, Literal("drift")))

    with pytest.raises(AssertionError, match="isomorphic"):
        assert_graph_isomorphic(generated, checked_in)


def test_asset_verification_reports_complete_validation_evidence() -> None:
    report = run_asset_verification(ROOT, ".venv/bin/python")

    assert report.returncode == 0
    assert report.scope == "assets"
    assert report.interpreter == str((ROOT / ".venv/bin/python").absolute())
    assert report.parity is not None
    assert report.parity["generated_reloaded"] is True
    assert report.validation is not None
    rows = {row["check_id"]: row for row in report.validation["checks"]}
    assert list(rows) == [
        "SUPPORT_VALID",
        "SUPPORT_INVALID",
        "ERP_VALID",
        "ERP_INVALID",
        "COMBINED_VALID",
        "PREREQUISITE_CYCLE_DEPTH",
    ]
    expected = {
        "SUPPORT_VALID": (
            ["semantic/data/sap_support_graph.ttl"],
            ["semantic/shapes/sap_support_shapes.ttl"],
            "support",
            True,
            "PASS",
        ),
        "SUPPORT_INVALID": (
            ["semantic/data/support-graph-invalid.ttl"],
            ["semantic/shapes/sap_support_shapes.ttl"],
            "support",
            False,
            "EXPECTED_NONCONFORMANT",
        ),
        "ERP_VALID": (
            ["semantic/ontology/sample-graph-valid.ttl"],
            ["semantic/shapes/sap_erp_shapes.ttl"],
            "erp",
            True,
            "PASS",
        ),
        "ERP_INVALID": (
            ["semantic/ontology/sample-graph-invalid.ttl"],
            ["semantic/shapes/sap_erp_shapes.ttl"],
            "erp",
            False,
            "EXPECTED_NONCONFORMANT",
        ),
        "COMBINED_VALID": (
            [
                "semantic/ontology/sap_support.ttl",
                "semantic/ontology/sap_ppms.ttl",
                "semantic/data/sap_support_graph.ttl",
                "semantic/ontology/sap_erp.ttl",
                "semantic/ontology/sample-graph-valid.ttl",
            ],
            ["semantic/shapes/sap_support_shapes.ttl", "semantic/shapes/sap_erp_shapes.ttl"],
            "combined",
            True,
            "PASS",
        ),
        "PREREQUISITE_CYCLE_DEPTH": (
            [
                "semantic/data/support-prerequisite-cycle.ttl",
                "semantic/data/support-prerequisite-depth17.ttl",
            ],
            [],
            "algorithm",
            None,
            "PASS",
        ),
    }
    assert list(rows) == list(expected)
    for check_id, (data_paths, shape_paths, scope, expected_conforms, result) in expected.items():
        row = rows[check_id]
        assert row["data_paths"] == data_paths
        assert row["shape_paths"] == shape_paths
        assert row["scope"] == scope
        assert row["inference"] == ("algorithm" if scope == "algorithm" else "rdfs")
        assert row["expected_conforms"] is expected_conforms
        assert row["observed_conforms"] is expected_conforms
        assert row["result"] == result
        assert row["data_sha256"] == [
            hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in data_paths
        ]
        assert row["shape_sha256"] == [
            hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in shape_paths
        ]

    algorithm = rows["PREREQUISITE_CYCLE_DEPTH"]["algorithm_cases"]
    assert algorithm[0]["fixture"] == "support-prerequisite-cycle.ttl"
    assert algorithm[0]["cycle_detected"] is True
    assert algorithm[0]["cycle_edges"] == [["A", "B"], ["B", "C"], ["C", "A"]]
    assert algorithm[0]["reachable_unique"] == ["B", "C"]
    assert algorithm[1]["fixture"] == "support-prerequisite-depth17.ttl"
    assert algorithm[1]["reachable_unique"] == [f"N{index}" for index in range(1, 17)]
    assert algorithm[1]["reason"] == "PREREQUISITE_DEPTH_EXCEEDED"


def test_asset_verification_fails_on_fixture_drift_without_replacing_source(
    tmp_path: Path,
) -> None:
    copy = tmp_path / "checkout"
    shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".venv", ".git"))
    fixture = copy / "semantic/data/sap_support_graph.ttl"
    original = fixture.read_bytes()
    fixture.write_bytes(
        original + b"\n<https://example.org/cifre-kg/data/support/test-drift> "
        b'<https://example.org/cifre-kg/data/label> "drift" .\n'
    )

    report = run_asset_verification(copy, sys.executable)

    assert report.returncode != 0
    assert report.errors
    assert fixture.read_bytes() != original


def test_asset_verification_fails_on_hash_only_fixture_drift(tmp_path: Path) -> None:
    copy = tmp_path / "checkout"
    shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".venv", ".git"))
    fixture = copy / "semantic/data/support-prerequisite-cycle.ttl"
    fixture.write_bytes(fixture.read_bytes() + b"\n# hash-only drift\n")

    report = run_asset_verification(copy, sys.executable)

    assert report.returncode != 0
    assert any("canonical asset" in error for error in report.errors)


def test_asset_verification_fails_closed_on_unexpected_validation_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = benchmark_runner.build_validation_metadata

    def failed_metadata(root: Path) -> dict[str, object]:
        metadata = original(root)
        metadata["checks"][0]["result"] = "FAIL"
        return metadata

    monkeypatch.setattr(benchmark_runner, "build_validation_metadata", failed_metadata)
    report = run_asset_verification(ROOT, ".venv/bin/python")

    assert report.returncode != 0
    assert any("unexpected validation result" in error for error in report.errors)


def test_asset_verification_fails_on_hash_only_metadata_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = benchmark_runner.build_validation_metadata

    def stale_hash_metadata(root: Path) -> dict[str, object]:
        metadata = original(root)
        metadata["checks"][0]["data_sha256"][0] = "0" * 64
        return metadata

    monkeypatch.setattr(benchmark_runner, "build_validation_metadata", stale_hash_metadata)
    report = run_asset_verification(ROOT, ".venv/bin/python")

    assert report.returncode != 0
    assert any("hash mismatch" in error for error in report.errors)


def test_asset_verification_rejects_an_invalid_interpreter() -> None:
    report = run_asset_verification(ROOT, "/definitely/not-a-python")

    assert report.returncode != 0
    assert any("interpreter" in error for error in report.errors)
