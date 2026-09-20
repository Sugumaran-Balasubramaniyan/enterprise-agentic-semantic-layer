"""Reproducibility and asset-boundary checks for the CIFRE prototype."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from rdflib import Graph, Literal, Namespace

from semantic_layer.validation import (
    assert_graph_isomorphic,
    run_asset_verification,
)
from semantic_layer.semantic_validation import validate_graph

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
    for row in rows.values():
        assert row["data_paths"]
        assert len(row["data_sha256"]) == len(row["data_paths"])
        assert len(row["shape_sha256"]) == len(row["shape_paths"])
    assert rows["SUPPORT_VALID"]["inference"] == "rdfs"
    assert rows["SUPPORT_INVALID"]["result"] == "EXPECTED_NONCONFORMANT"
    assert rows["ERP_INVALID"]["result"] == "EXPECTED_NONCONFORMANT"

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

    report = run_asset_verification(copy, ".venv/bin/python")

    assert report.returncode != 0
    assert report.errors
    assert fixture.read_bytes() != original
