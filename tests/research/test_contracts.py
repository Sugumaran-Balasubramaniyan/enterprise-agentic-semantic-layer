"""Tests for the canonical CIFRE research contracts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import jsonschema
import pytest
import yaml

from semantic_layer.research.contracts import (
    CONDITIONS,
    NAMESPACE_REGISTRY,
    ReasonCode,
    Status,
    canonical_json,
    load_and_validate_result,
)
from semantic_layer.validation import scan_repository_legacy_uris

ROOT = Path(__file__).parents[2]

LEGACY_URI_FAMILIES = (
    "http://data." + "sap" + ".com/",
    "http://ontology." + "sap" + ".com/",
    "https://" + "sap.example/erp/",
)
LEGACY_URI_SURFACE_FAMILIES = (*LEGACY_URI_FAMILIES, "https://help." + "sap" + ".com/")
LEGACY_URI_CONTROL_DOCUMENTS = frozenset(
    {
        "docs/superpowers/specs/2026-09-19-cifre-research-prototype-hardening-design.md",
        "docs/superpowers/plans/2026-09-19-cifre-research-prototype-hardening.md",
        "docs/research/cifre-hardening-baseline.md",
    }
)
GENERATED_RESULT_ARTIFACT = "results/latest_benchmark.json"


def _schema_valid_result() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "artifact_id": "artifact-1",
        "generated_by": "tests",
        "canonicalization": {
            "encoding": "UTF-8",
            "key_order": "lexicographic",
            "metric_precision": 6,
        },
        "hash_manifest": {
            "manifest_version": "1.0",
            "entries": [],
            "digest_sha256": "0" * 64,
        },
        "environment": {
            "python_version": "3.12.0",
            "platform_system": "Linux",
            "platform_machine": "x86_64",
            "pip_version": "25.2",
            "lock_sha256": "0" * 64,
            "packages": {"pip": "25.2"},
        },
        "namespace_registry": {
            **NAMESPACE_REGISTRY,
            "legacy_uris_rejected": list(LEGACY_URI_FAMILIES),
        },
        "validation": {"checks": [], "combined_graph": {}},
        "corpus_runs": [],
        "per_query": [],
    }


def test_namespace_registry_is_the_closed_neutral_registry() -> None:
    assert NAMESPACE_REGISTRY == {
        "cifsup": "https://example.org/cifre-kg/support#",
        "cifppms": "https://example.org/cifre-kg/ppms#",
        "cifdata": "https://example.org/cifre-kg/data/",
        "ciferp": "https://example.org/cifre-kg/erp#",
        "cifskos": "https://example.org/cifre-kg/vocabulary#",
        "cifmeta": "https://example.org/cifre-kg/meta#",
        "cifmetaid": "https://example.org/cifre-kg/id/meta/",
    }


def test_status_and_reason_contracts_are_closed() -> None:
    assert [member.name for member in Status] == [
        "SUCCESS",
        "UNSUPPORTED",
        "SYNTAX_ERROR",
        "EXECUTION_ERROR",
        "EMPTY_RESULT",
    ]
    assert [member.name for member in ReasonCode] == [
        "NONE",
        "UNKNOWN_TOKEN",
        "UNKNOWN_ENTITY",
        "AMBIGUOUS_INPUT",
        "AMBIGUOUS_INTENT",
        "MULTIPLE_DISTINCT_ENTITIES",
        "UNSUPPORTED_INTENT",
        "MISSING_REQUIRED_ENTITY",
        "UNBOUND_REQUIRED_PROJECTION",
        "SPARQL_SYNTAX",
        "SPARQL_EXECUTION",
        "EMPTY_STRICT_RESULT",
        "RELAX_SUPPORT_PACKAGE",
        "WIDEN_COMPONENT",
        "REPAIR_BUDGET_EXHAUSTED",
        "PROVENANCE_MISSING",
        "HASH_MISMATCH",
        "INVALID_DATASET",
        "NO_OP_REPAIR",
        "PREREQUISITE_DEPTH_EXCEEDED",
    ]
    assert CONDITIONS == (
        "deterministic_no_reflection_ablation",
        "deterministic_bounded_repair",
    )


def test_canonical_json_is_utf8_sorted_and_compact() -> None:
    assert canonical_json({"b": 1, "a": 2}) == b'{"a":2,"b":1}'


def test_synthetic_provenance_has_exact_top_level_contract() -> None:
    path = ROOT / "semantic/provenance/synthetic_source.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert set(document) == {
        "schema_version",
        "dataset_id",
        "source_kind",
        "authority",
        "official",
        "source_license",
        "generator",
        "graph_path",
        "namespace_registry",
        "synthetic_label_policy",
    }
    assert document["official"] is False
    assert document["source_kind"] == "synthetic_fixture"
    assert document["generator"] == (
        "src/semantic_layer/kg/sap_dataset_generator.py:build_sap_support_graph"
    )
    assert document["graph_path"] == "semantic/data/sap_support_graph.ttl"
    assert document["namespace_registry"] == NAMESPACE_REGISTRY


def test_result_loader_rejects_wrong_schema_version(tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    path.write_text(json.dumps({"schema_version": "0.9.0"}), encoding="utf-8")
    with pytest.raises(jsonschema.ValidationError):
        load_and_validate_result(path)


def test_result_loader_accepts_a_schema_valid_result(tmp_path: Path) -> None:
    schema = json.loads((ROOT / "tests/research/result_schema.json").read_text(encoding="utf-8"))
    result = _schema_valid_result()
    # Keep this fixture coupled to the authoritative schema, not to incidental
    # implementation details of the loader.
    assert schema["$id"] == "https://example.org/cifre-kg/schema/research-result-root-1.0.0.json"
    path = tmp_path / "result.json"
    path.write_bytes(canonical_json(result))
    assert load_and_validate_result(path) == result


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("pip_version", "24.0"),
        ("lock_sha256", "not-a-sha"),
        ("packages", {"pip": None}),
    ],
)
def test_result_schema_rejects_unsupported_environment_without_loader(
    field: str, value: object
) -> None:
    schema = json.loads((ROOT / "tests/research/result_schema.json").read_bytes())
    result = _schema_valid_result()
    result["environment"][field] = value  # type: ignore[index]

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(result)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("pip_version", "24.0"),
        ("pip_version", "unavailable"),
        ("platform_system", "Darwin"),
        ("platform_machine", "arm64"),
        ("python_version", "3.12"),
        ("python_version", "3.13.0"),
        ("python_version", "3.12.patch"),
    ],
)
def test_result_loader_rejects_unsupported_publication_environment(
    tmp_path: Path, field: str, value: str
) -> None:
    result = _schema_valid_result()
    result["environment"][field] = value  # type: ignore[index]
    path = tmp_path / "unsupported-environment.json"
    path.write_bytes(canonical_json(result))

    with pytest.raises(jsonschema.ValidationError):
        load_and_validate_result(path)


def test_committed_result_loader_rejects_noncanonical_bytes(tmp_path: Path) -> None:
    committed = ROOT / "results/latest_benchmark.json"
    document = json.loads(committed.read_bytes())
    reformatted = tmp_path / "reformatted-result.json"
    reformatted.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="canonical"):
        load_and_validate_result(reformatted, require_canonical_bytes=True)


def test_result_loader_rejects_artifact_only_reason_code_per_query(tmp_path: Path) -> None:
    result = {
        "schema_version": "1.0.0",
        "artifact_id": "artifact-1",
        "generated_by": "tests",
        "canonicalization": {
            "encoding": "UTF-8",
            "key_order": "lexicographic",
            "metric_precision": 6,
        },
        "hash_manifest": {
            "manifest_version": "1.0",
            "entries": [],
            "digest_sha256": "0" * 64,
        },
        "environment": {
            "python_version": "3.12.0",
            "platform_system": "Linux",
            "platform_machine": "x86_64",
            "pip_version": "25.2",
            "lock_sha256": "0" * 64,
            "packages": {"pip": "25.2"},
        },
        "namespace_registry": {
            **NAMESPACE_REGISTRY,
            "legacy_uris_rejected": [
                "http://data." + "sap" + ".com/",
                "http://ontology." + "sap" + ".com/",
                "https://" + "sap.example/erp/",
            ],
        },
        "validation": {"checks": [], "combined_graph": {}},
        "corpus_runs": [],
        "per_query": [
            {
                "schema_version": "1.0.0",
                "corpus_id": "cifre-synthetic-aqr-v1",
                "query_id": "Q01",
                "condition": CONDITIONS[0],
                "question": "synthetic question",
                "normalized_request": "synthetic request",
                "expected_status": "UNSUPPORTED",
                "observed_status": "UNSUPPORTED",
                "reason_code": "INVALID_DATASET",
                "original_constraints": {},
                "grounding": {},
                "plan": None,
                "sparql": None,
                "attempts": 0,
                "repair": {},
                "relaxation": {},
                "answer_scope": "none",
                "relaxed_candidates": [],
                "bindings": [],
                "predicted_note_numbers": [],
                "gold_note_numbers": [],
                "metrics": {
                    "applicable": False,
                    "exact_set": None,
                    "precision": None,
                    "recall": None,
                    "f1": None,
                },
                "provenance": {
                    "dataset_id": "cifre-synthetic-support-ppms-v1",
                    "source_kind": "synthetic_fixture",
                    "official": False,
                    "graph_sha256": "0" * 64,
                    "citation": "synthetic fixture",
                },
            }
        ],
    }
    path = tmp_path / "artifact-reason.json"
    path.write_bytes(canonical_json(result))
    with pytest.raises(jsonschema.ValidationError, match="INVALID_DATASET"):
        load_and_validate_result(path)


def test_legacy_uri_contract_decodes_exact_values_and_scans_tracked_surfaces() -> None:
    schema = json.loads((ROOT / "tests/research/result_schema.json").read_bytes())
    decoded = schema["properties"]["namespace_registry"]["properties"][
        "legacy_uris_rejected"
    ]["const"]
    assert decoded == list(LEGACY_URI_FAMILIES)

    tracked = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout.split(b"\0")
    for raw_path in tracked:
        if not raw_path:
            continue
        relative = raw_path.decode("utf-8")
        if relative in LEGACY_URI_CONTROL_DOCUMENTS or relative == GENERATED_RESULT_ARTIFACT:
            continue
        text = (ROOT / relative).read_bytes().decode("utf-8", errors="ignore")
        assert not any(uri in text for uri in LEGACY_URI_SURFACE_FAMILIES), relative


def test_legacy_uri_scan_allows_only_exact_registry_values_and_rejects_other_fields(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "results/latest_benchmark.json"
    artifact.parent.mkdir()
    allowed = {
        "namespace_registry": {"legacy_uris_rejected": list(LEGACY_URI_FAMILIES)},
        "question": "synthetic fixture",
    }
    artifact.write_text(json.dumps(allowed), encoding="utf-8")
    assert scan_repository_legacy_uris(tmp_path, paths=[artifact]) == []

    allowed["question"] = LEGACY_URI_FAMILIES[0]
    artifact.write_text(json.dumps(allowed), encoding="utf-8")
    findings = scan_repository_legacy_uris(tmp_path, paths=[artifact])
    assert findings
    assert "legacy-uri" in findings[0]
