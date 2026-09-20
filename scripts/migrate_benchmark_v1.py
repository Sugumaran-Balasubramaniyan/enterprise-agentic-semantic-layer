"""Deterministically normalize the historical CIFRE benchmark corpus.

The historical YAML is deliberately treated as an input-only artifact.  This
module performs only local parsing and serialization; no clock, randomness,
network, model, or benchmark execution is involved.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml
from rdflib import Graph, Namespace, URIRef

RECORD_FIELDS = (
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
)
MANIFEST_FIELDS = (
    "schema_version",
    "source_path",
    "archival_path",
    "normalized_path",
    "record_ids",
    "changes",
    "records",
    "review",
)
MANIFEST_RECORD_FIELDS = (
    "id",
    "category_before",
    "category_after",
    "gold_before",
    "gold_after",
    "status_before",
    "status_after",
    "schema_before",
    "schema_after",
    "migration_reason",
    "policy_citation",
    "derivation_query",
    "reviewer_id",
    "signed_off",
)
DERIVATION_FIELDS = ("kind", "text", "graph_sha256", "result", "result_sha256")
CHANGE_FIELDS = (
    "change_id",
    "record_ids",
    "before",
    "after",
    "migration_reason",
    "policy_citation",
    "derivation_query",
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = REPOSITORY_ROOT / "semantic/data/sap_support_graph.ttl"
HISTORICAL_PATH = REPOSITORY_ROOT / "tests/research/benchmark_dataset.yaml"
ARCHIVAL_PATH = REPOSITORY_ROOT / "tests/research/benchmark_dataset_legacy.yaml"
# Both checked-in inputs are intentionally byte-identical and immutable for
# this migration contract.  A caller-supplied same-shaped copy is not enough.
CANONICAL_SOURCE_SHA256 = "04bb3d5f7c0516c9eca400ea22026df7096281fa0df148b38cbfe81ce930307f"
LEGACY_PATH = ARCHIVAL_PATH
GRAPH_SHA256 = hashlib.sha256(GRAPH_PATH.read_bytes()).hexdigest()
ZERO_SHA256 = "0" * 64
MAX_PREREQUISITE_DEPTH = 16
CIFSUP = Namespace("https://example.org/cifre-kg/support#")
CIFRE_DATA = "https://example.org/cifre-kg/data/support/note/"
REVIEWER_ID = "repository-maintainer"
MIGRATION_REASONS = {
    "SCHEMA_NORMALIZATION",
    "PREREQUISITE_CLOSURE_EXPANSION",
    "PREREQUISITE_CLOSURE_NORMALIZATION",
    "STRICT_CONSTRAINT_STATUS_CORRECTION",
}
POLICY_CITATIONS = {
    "SCHEMA_NORMALIZATION": "Sections 26.1-26.2",
    "PREREQUISITE_CLOSURE_EXPANSION": "Sections 6.3 and 26.1",
    "PREREQUISITE_CLOSURE_NORMALIZATION": "Sections 6.3 and 26.1",
    "STRICT_CONSTRAINT_STATUS_CORRECTION": "Sections 7.1, 18.1, and 26.1",
}
SCHEMA_BEFORE = {
    "id": "string",
    "tier": "integer",
    "category": "string",
    "question": "string",
    "expected_notes": "array[string]",
    "requires_reflection": "boolean",
}
SCHEMA_AFTER = {
    "id": "string",
    "corpus_id": "string",
    "version": "string",
    "tier": "integer",
    "category": "string",
    "question": "string",
    "expected_status": "string",
    "gold_note_numbers": "array[string]",
    "reflection_reason": "string",
    "strict_constraints": "boolean",
    "gold_policy": "string",
}

V2_FIXTURES = (
    (
        "Q41",
        "negative_unknown_token",
        "UNSUPPORTED",
        "UNKNOWN_TOKEN",
        "Find notes unlicensed oracle system.",
    ),
    (
        "Q42",
        "negative_unknown_token",
        "UNSUPPORTED",
        "UNKNOWN_TOKEN",
        "Which notes resolve unexplained outage?",
    ),
    (
        "Q43",
        "negative_unknown_entity",
        "UNSUPPORTED",
        "UNKNOWN_ENTITY",
        "Find notes alert UNKNOWN_ALERT.",
    ),
    (
        "Q44",
        "negative_unknown_entity",
        "UNSUPPORTED",
        "UNKNOWN_ENTITY",
        "Find notes component ZZ-UNKNOWN.",
    ),
    (
        "Q45",
        "negative_ambiguity",
        "UNSUPPORTED",
        "AMBIGUOUS_INPUT",
        "Find notes alert TIME_OUT alert DBSQL_NO_MORE_CONNECTION.",
    ),
    (
        "Q46",
        "negative_ambiguity",
        "UNSUPPORTED",
        "AMBIGUOUS_INPUT",
        "Find notes component FI component MM.",
    ),
    (
        "Q47",
        "negative_unsupported_intent",
        "UNSUPPORTED",
        "UNSUPPORTED_INTENT",
        "Summarize support landscape in paragraph.",
    ),
    (
        "Q48",
        "negative_unsupported_intent",
        "UNSUPPORTED",
        "UNSUPPORTED_INTENT",
        "Recommend patch system.",
    ),
    (
        "Q49",
        "negative_strict_empty",
        "EMPTY_RESULT",
        "EMPTY_STRICT_RESULT",
        "Find notes alert TIME_OUT in component MM-PUR-PO at SP99.",
    ),
    (
        "Q50",
        "negative_strict_empty",
        "EMPTY_RESULT",
        "EMPTY_STRICT_RESULT",
        "Find notes alert DBSQL_NO_MORE_CONNECTION in component BC-DB-HDB at SP99.",
    ),
    (
        "Q51",
        "negative_strict_empty",
        "EMPTY_RESULT",
        "EMPTY_STRICT_RESULT",
        "Find notes resolving alert TIME_OUT on S/4HANA 2022 in component SD-SLS.",
    ),
    (
        "Q52",
        "negative_strict_empty",
        "EMPTY_RESULT",
        "EMPTY_STRICT_RESULT",
        "Find notes alert CALL_FUNCTION_NOT_FOUND in component SD-SLS.",
    ),
)
CLOSURE_TARGETS = {
    "Q25": "3109922",
    "Q28": "3109922",
    "Q31": "3109922",
    "Q26": "3098110",
    "Q30": "3098110",
    "Q27": "3201440",
    "Q29": "3201440",
    "Q32": "3201440",
}


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _canonical_closure_query(target_note: str) -> str:
    target_iri = f"{CIFRE_DATA}{target_note}"
    return (
        "PREFIX cifsup: <https://example.org/cifre-kg/support#> "
        "PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> "
        "SELECT ?prerequisite ?noteNumber WHERE { "
        f"VALUES ?targetNote {{ <{target_iri}> }} "
        "?targetNote cifsup:hasPrerequisiteNote+ ?prerequisite . "
        "?prerequisite cifsup:noteNumber ?noteNumber . "
        "FILTER (datatype(?noteNumber) = xsd:string) "
        "} ORDER BY ?noteNumber"
    )


def _load_graph() -> Graph:
    graph = Graph()
    graph.parse(GRAPH_PATH, format="turtle")
    return graph


def _bounded_closure(graph: Graph, target_note: str) -> set[URIRef]:
    """Return prerequisite nodes with an explicit finite depth bound."""
    target = URIRef(f"{CIFRE_DATA}{target_note}")
    visited: set[URIRef] = set()
    frontier: set[URIRef] = {target}
    for _depth in range(MAX_PREREQUISITE_DEPTH):
        next_frontier = {
            prerequisite
            for node in frontier
            for prerequisite in graph.objects(node, CIFSUP.hasPrerequisiteNote)
            if isinstance(prerequisite, URIRef) and prerequisite not in visited
        }
        if not next_frontier:
            break
        visited.update(next_frontier)
        frontier = next_frontier
    else:
        raise ValueError(f"prerequisite closure exceeded depth {MAX_PREREQUISITE_DEPTH}")
    return visited


def _derive_closure(graph: Graph, target_note: str) -> list[str]:
    bounded_nodes = _bounded_closure(graph, target_note)
    rows = list(graph.query(_canonical_closure_query(target_note)))
    query_nodes = {row[0] for row in rows}
    if query_nodes != bounded_nodes:
        raise ValueError(f"canonical prerequisite query exceeded bounded closure for {target_note}")
    numbers = sorted(str(row[1]) for row in rows)
    if len(numbers) != len(set(numbers)) or any(
        len(number) != 7 or not number.isdigit() for number in numbers
    ):
        raise ValueError(
            f"canonical prerequisite query returned invalid note numbers for {target_note}"
        )
    return numbers


def _closure_results(graph: Graph) -> dict[str, list[str]]:
    return {
        record_id: _derive_closure(graph, target) for record_id, target in CLOSURE_TARGETS.items()
    }


def _serialize_yaml(value: Mapping[str, Any]) -> bytes:
    rendered = yaml.safe_dump(value, sort_keys=False, allow_unicode=False, default_flow_style=False)
    return rendered.encode("utf-8")


def _fsync_directory(directory: Path) -> None:
    """Best-effort directory durability after an atomic replacement."""
    try:
        directory_fd = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    except OSError:
        pass
    finally:
        os.close(directory_fd)


def _write_yaml(path: Path, payload: bytes) -> None:
    """Publish a complete UTF-8 YAML payload with an atomic destination swap."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path: Path | None = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as temporary:
            descriptor = -1
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
        _fsync_directory(path.parent)
    finally:
        if descriptor != -1:
            os.close(descriptor)
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except OSError:
                pass


def _read_legacy(source: Path) -> list[dict[str, Any]]:
    try:
        document = yaml.safe_load(source.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"cannot read historical benchmark: {source}: {exc}") from exc
    if not isinstance(document, Mapping) or not isinstance(document.get("queries"), list):
        raise ValueError("historical benchmark must contain a queries list")
    queries = document["queries"]
    expected_ids = [f"Q{i:02d}" for i in range(1, 41)]
    if [item.get("id") if isinstance(item, Mapping) else None for item in queries] != expected_ids:
        raise ValueError("historical benchmark IDs must be exactly Q01 through Q40")
    for item in queries:
        if not isinstance(item, Mapping) or not {
            "id",
            "tier",
            "category",
            "question",
            "expected_notes",
        }.issubset(item):
            raise ValueError("historical benchmark record is missing required fields")
        if not isinstance(item["expected_notes"], list) or any(
            not isinstance(note, str) or len(note) != 7 or not note.isdigit()
            for note in item["expected_notes"]
        ):
            raise ValueError(f"invalid historical note set for {item.get('id')}")
    return [dict(item) for item in queries]


def _verify_canonical_inputs() -> None:
    """Require the checked-in historical and archival bytes to remain canonical."""

    if Path(LEGACY_PATH).absolute() != ARCHIVAL_PATH.absolute():
        raise ValueError("canonical historical/archive path identity changed")
    try:
        historical_bytes = HISTORICAL_PATH.read_bytes()
        archival_bytes = ARCHIVAL_PATH.read_bytes()
    except OSError as exc:
        raise ValueError("canonical historical/archive inputs are unavailable") from exc
    for label, data in (("historical", historical_bytes), ("archive", archival_bytes)):
        digest = hashlib.sha256(data).hexdigest()
        if digest != CANONICAL_SOURCE_SHA256:
            raise ValueError(f"canonical {label} benchmark bytes do not match the pinned hash")
    if historical_bytes != archival_bytes:
        raise ValueError("canonical historical/archive inputs must be byte-identical")


def _output_identity(path: Path, label: str) -> tuple[int, int] | None:
    try:
        link_metadata = os.lstat(path)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ValueError(f"cannot inspect {label} output path") from exc
    if stat.S_ISLNK(link_metadata.st_mode):
        raise ValueError(f"{label} output path must not be a symbolic link")
    try:
        metadata = os.stat(path, follow_symlinks=False)
    except FileNotFoundError as exc:
        raise ValueError(f"{label} output path changed during validation") from exc
    except OSError as exc:
        raise ValueError(f"cannot inspect {label} output path") from exc
    if stat.S_ISLNK(metadata.st_mode):
        raise ValueError(f"{label} output path must not be a symbolic link")
    return metadata.st_dev, metadata.st_ino


def _file_identity(path: Path) -> tuple[int, int] | None:
    try:
        metadata = os.stat(path, follow_symlinks=True)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ValueError(f"cannot inspect canonical input path: {path}") from exc
    return metadata.st_dev, metadata.st_ino


def _validate_output_paths(v1: Path, v2: Path, manifest: Path) -> tuple[Path, Path, Path]:
    """Reject input destinations and aliases before any migration work or write."""
    outputs = (("v1", v1), ("v2", v2), ("manifest", manifest))
    canonical_paths = {HISTORICAL_PATH.resolve(), ARCHIVAL_PATH.resolve()}
    resolved_outputs: list[Path] = []
    output_identities: list[tuple[int, int] | None] = []
    for label, path in outputs:
        resolved = path.resolve(strict=False)
        if resolved in canonical_paths:
            raise ValueError(
                f"{label} output cannot overwrite canonical historical/archive input"
            )
        resolved_outputs.append(resolved)
        output_identities.append(_output_identity(path, label))
    if len(set(resolved_outputs)) != len(resolved_outputs):
        raise ValueError("migration output paths must be distinct")
    canonical_identities = {
        identity
        for identity in (_file_identity(HISTORICAL_PATH), _file_identity(ARCHIVAL_PATH))
        if identity is not None
    }
    for (label, _path), identity in zip(outputs, output_identities, strict=True):
        if identity in canonical_identities:
            raise ValueError(
                f"{label} output cannot overwrite canonical historical/archive input"
            )
    unique_identities = [identity for identity in output_identities if identity is not None]
    if len(set(unique_identities)) != len(unique_identities):
        raise ValueError("migration output paths must be distinct")
    return resolved_outputs[0], resolved_outputs[1], resolved_outputs[2]


def _verify_canonical_source(source: Path) -> None:
    """Verify the caller selected one of the canonical paths and exact bytes."""

    _verify_canonical_inputs()
    source_path = Path(source).absolute()
    canonical_paths = {HISTORICAL_PATH.absolute(), ARCHIVAL_PATH.absolute()}
    if source_path not in canonical_paths:
        raise ValueError("source must be one of the canonical historical/archive paths")
    try:
        digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ValueError("canonical historical/archive source is unavailable") from exc
    if digest != CANONICAL_SOURCE_SHA256:
        raise ValueError("source bytes do not match the canonical historical/archive hash")


def _normalized_record(
    item: Mapping[str, Any],
    *,
    corpus_id: str,
    version: str,
    expected_status: str,
    gold_note_numbers: Sequence[str],
    reflection_reason: str,
) -> dict[str, Any]:
    return {
        "id": item["id"],
        "corpus_id": corpus_id,
        "version": version,
        "tier": int(item["tier"]),
        "category": item["category"],
        "question": item["question"],
        "expected_status": expected_status,
        "gold_note_numbers": sorted(set(gold_note_numbers)),
        "reflection_reason": reflection_reason,
        "strict_constraints": True,
        "gold_policy": "exact_set",
    }


def _migration_values(
    item: Mapping[str, Any], closure_results: Mapping[str, Sequence[str]]
) -> tuple[list[str], list[str], str, str]:
    record_id = item["id"]
    gold_before = sorted(set(item["expected_notes"]))
    if record_id in CLOSURE_TARGETS:
        reason = (
            "PREREQUISITE_CLOSURE_EXPANSION"
            if record_id in {"Q25", "Q28", "Q31"}
            else "PREREQUISITE_CLOSURE_NORMALIZATION"
        )
        return gold_before, sorted(closure_results[record_id]), "SUCCESS", reason
    if int(item["tier"]) == 5:
        return gold_before, [], "EMPTY_RESULT", "STRICT_CONSTRAINT_STATUS_CORRECTION"
    return gold_before, gold_before, "SUCCESS", "SCHEMA_NORMALIZATION"


def _derivation(
    record_id: str,
    reason: str,
    gold_before: list[str],
    gold_after: list[str],
    closure_results: Mapping[str, Sequence[str]],
) -> dict[str, Any]:
    result: dict[str, Any] = {"gold_before": gold_before, "gold_after": gold_after}
    if reason in {"PREREQUISITE_CLOSURE_EXPANSION", "PREREQUISITE_CLOSURE_NORMALIZATION"}:
        kind = "canonical_sparql"
        target_note = CLOSURE_TARGETS[record_id]
        text = _canonical_closure_query(target_note)
        result["target_note"] = target_note
        result["max_depth"] = MAX_PREREQUISITE_DEPTH
        if sorted(closure_results[record_id]) != gold_after:
            raise ValueError(f"closure result mismatch for {record_id}")
        graph_sha256 = GRAPH_SHA256
    else:
        kind = "policy"
        text = {
            "SCHEMA_NORMALIZATION": "Convert legacy expected_notes to sorted gold_note_numbers.",
            "STRICT_CONSTRAINT_STATUS_CORRECTION": "Apply strict constraints without semantic relaxation.",
        }[reason]
        graph_sha256 = ZERO_SHA256
    return {
        "kind": kind,
        "text": text,
        "graph_sha256": graph_sha256,
        "result": result,
        "result_sha256": _sha256_json(result),
    }


def _manifest_record(
    item: Mapping[str, Any], closure_results: Mapping[str, Sequence[str]]
) -> dict[str, Any]:
    gold_before, gold_after, status_after, reason = _migration_values(item, closure_results)
    return {
        "id": item["id"],
        "category_before": item["category"],
        "category_after": item["category"],
        "gold_before": gold_before,
        "gold_after": gold_after,
        "status_before": "SUCCESS",
        "status_after": status_after,
        "schema_before": dict(SCHEMA_BEFORE),
        "schema_after": dict(SCHEMA_AFTER),
        "migration_reason": reason,
        "policy_citation": POLICY_CITATIONS[reason],
        "derivation_query": _derivation(
            item["id"], reason, gold_before, gold_after, closure_results
        ),
        "reviewer_id": REVIEWER_ID,
        "signed_off": True,
    }


def migrate_benchmark(source: Path, v1: Path, v2: Path, manifest: Path) -> None:
    """Generate normalized v1/v2 corpora and the signed migration manifest."""
    source = Path(source)
    v1 = Path(v1)
    v2 = Path(v2)
    manifest = Path(manifest)
    v1, v2, manifest = _validate_output_paths(v1, v2, manifest)
    _verify_canonical_source(source)
    historical = _read_legacy(source)
    graph = _load_graph()
    closure_results = _closure_results(graph)

    v1_records = []
    for item in historical:
        _before, after, status, reason = _migration_values(item, closure_results)
        v1_records.append(
            _normalized_record(
                item,
                corpus_id="cifre-synthetic-aqr-v1",
                version="1.0.0",
                expected_status=status,
                gold_note_numbers=after,
                reflection_reason="STRICT_EMPTY_SEMANTIC_RELAXATION"
                if reason == "STRICT_CONSTRAINT_STATUS_CORRECTION"
                else "NONE",
            )
        )
    # Copy record mappings so changing v2 provenance cannot mutate v1 output.
    v2_records = [dict(record) for record in v1_records]
    for record_id, category, status, reason, question in V2_FIXTURES:
        v2_records.append(
            {
                "id": record_id,
                "corpus_id": "cifre-synthetic-aqr-v2",
                "version": "2.0.0",
                "tier": 0,
                "category": category,
                "question": question,
                "expected_status": status,
                "gold_note_numbers": [],
                "reflection_reason": reason,
                "strict_constraints": True,
                "gold_policy": "exact_set",
            }
        )
    # v2 is a distinct corpus; do not leave v1 provenance on its shared records.
    for record in v2_records[:40]:
        record["corpus_id"] = "cifre-synthetic-aqr-v2"
        record["version"] = "2.0.0"

    ids = [f"Q{i:02d}" for i in range(1, 41)]
    changes = [
        {
            "change_id": "normalized_schema_v1",
            "record_ids": ids,
            "before": {"field": "expected_notes", "type": "legacy_yaml"},
            "after": {"field": "gold_note_numbers", "type": "sorted_unique_string_array"},
            "migration_reason": "SCHEMA_NORMALIZATION",
            "policy_citation": "Section 26.2",
            "derivation_query": {
                "kind": "policy",
                "text": "Convert legacy expected_notes sorted gold_note_numbers.",
                "graph_sha256": ZERO_SHA256,
                "result": {"gold_before": [], "gold_after": []},
                "result_sha256": ZERO_SHA256,
            },
        }
    ]
    manifest_document = {
        "schema_version": "1.0",
        "source_path": "tests/research/benchmark_dataset.yaml",
        "archival_path": "tests/research/benchmark_dataset_legacy.yaml",
        "normalized_path": "tests/research/benchmark_dataset_v1.yaml",
        "record_ids": ids,
        "changes": changes,
        "records": [_manifest_record(item, closure_results) for item in historical],
        "review": {"reviewer_id": REVIEWER_ID, "signoff_required": True, "signed_off": True},
    }
    validate_migration_manifest(manifest_document)
    v1_payload = _serialize_yaml(
        {"corpus_id": "cifre-synthetic-aqr-v1", "version": "1.0.0", "records": v1_records}
    )
    v2_payload = _serialize_yaml(
        {"corpus_id": "cifre-synthetic-aqr-v2", "version": "2.0.0", "records": v2_records}
    )
    manifest_payload = _serialize_yaml(manifest_document)

    # Revalidate destinations and canonical inputs after complete serialization,
    # immediately before the ordered atomic replacements.  The manifest is last.
    v1, v2, manifest = _validate_output_paths(v1, v2, manifest)
    _verify_canonical_source(source)
    _write_yaml(v1, v1_payload)
    _write_yaml(v2, v2_payload)
    _write_yaml(manifest, manifest_payload)


def _require_keys(value: Mapping[str, Any], expected: Sequence[str], label: str) -> None:
    if list(value) != list(expected):
        raise ValueError(f"{label} fields/order must be exactly {list(expected)}")


def validate_migration_manifest(manifest: Mapping[str, Any]) -> None:
    """Validate the closed, signed manifest contract before it is written."""
    _verify_canonical_inputs()
    if not isinstance(manifest, Mapping):
        raise ValueError("manifest must be a mapping")
    _require_keys(manifest, MANIFEST_FIELDS, "manifest")
    if manifest["schema_version"] != "1.0":
        raise ValueError("schema_version must be 1.0")
    expected_ids = [f"Q{i:02d}" for i in range(1, 41)]
    if manifest["record_ids"] != expected_ids:
        raise ValueError("record_ids must be exactly Q01 through Q40")
    if manifest["source_path"] != "tests/research/benchmark_dataset.yaml":
        raise ValueError("source_path must identify the immutable historical input")
    if manifest["archival_path"] != "tests/research/benchmark_dataset_legacy.yaml":
        raise ValueError("archival_path must identify the byte-identical archive")
    if manifest["normalized_path"] != "tests/research/benchmark_dataset_v1.yaml":
        raise ValueError("normalized_path must identify normalized v1")
    if not isinstance(manifest["changes"], list) or len(manifest["changes"]) != 1:
        raise ValueError("manifest must contain the normalized_schema_v1 change")
    change = manifest["changes"][0]
    if not isinstance(change, Mapping):
        raise ValueError("manifest change must be a mapping")
    _require_keys(change, CHANGE_FIELDS, "manifest change")
    if change["change_id"] != "normalized_schema_v1" or change["record_ids"] != expected_ids:
        raise ValueError("normalized_schema_v1 must cover Q01 through Q40")
    if change["before"] != {"field": "expected_notes", "type": "legacy_yaml"}:
        raise ValueError("normalized_schema_v1 before schema is invalid")
    if change["after"] != {"field": "gold_note_numbers", "type": "sorted_unique_string_array"}:
        raise ValueError("normalized_schema_v1 after schema is invalid")
    if (
        change["migration_reason"] != "SCHEMA_NORMALIZATION"
        or change["policy_citation"] != "Section 26.2"
    ):
        raise ValueError("normalized_schema_v1 policy is invalid")
    change_derivation = change["derivation_query"]
    if not isinstance(change_derivation, Mapping):
        raise ValueError("normalized_schema_v1 derivation_query is missing")
    _require_keys(change_derivation, DERIVATION_FIELDS, "normalized_schema_v1 derivation_query")
    if change_derivation["kind"] != "policy" or any(
        not isinstance(change_derivation[key], str)
        or len(change_derivation[key]) != 64
        or any(char not in "0123456789abcdef" for char in change_derivation[key])
        for key in ("graph_sha256", "result_sha256")
    ):
        raise ValueError("normalized_schema_v1 derivation hashes are invalid")
    expected_change = {
        "change_id": "normalized_schema_v1",
        "record_ids": expected_ids,
        "before": {"field": "expected_notes", "type": "legacy_yaml"},
        "after": {"field": "gold_note_numbers", "type": "sorted_unique_string_array"},
        "migration_reason": "SCHEMA_NORMALIZATION",
        "policy_citation": "Section 26.2",
        "derivation_query": {
            "kind": "policy",
            "text": "Convert legacy expected_notes sorted gold_note_numbers.",
            "graph_sha256": ZERO_SHA256,
            "result": {"gold_before": [], "gold_after": []},
            "result_sha256": ZERO_SHA256,
        },
    }
    if dict(change) != expected_change:
        raise ValueError("normalized_schema_v1 change evidence does not match the canonical policy")
    historical = _read_legacy(ARCHIVAL_PATH)
    closure_results = _closure_results(_load_graph())
    if not isinstance(manifest["records"], list) or len(manifest["records"]) != 40:
        raise ValueError("manifest must contain exactly 40 records")
    for expected_id, item, record in zip(
        expected_ids, historical, manifest["records"], strict=True
    ):
        if not isinstance(record, Mapping):
            raise ValueError("manifest record must be a mapping")
        _require_keys(record, MANIFEST_RECORD_FIELDS, f"manifest record {expected_id}")
        if record["id"] != expected_id:
            raise ValueError("manifest record IDs must be ordered Q01 through Q40")
        if record["migration_reason"] not in MIGRATION_REASONS:
            raise ValueError(f"invalid migration_reason for {expected_id}")
        if record["policy_citation"] != POLICY_CITATIONS[record["migration_reason"]]:
            raise ValueError(f"invalid policy_citation for {expected_id}")
        if record["category_before"] != record["category_after"]:
            raise ValueError(f"category changed without a supported migration for {expected_id}")
        if record["reviewer_id"] != REVIEWER_ID or record["signed_off"] is not True:
            raise ValueError(f"signed_off reviewer contract failed for {expected_id}")
        if record["schema_before"] != SCHEMA_BEFORE or record["schema_after"] != SCHEMA_AFTER:
            raise ValueError(f"schema field/type contract failed for {expected_id}")
        derivation = record["derivation_query"]
        if not isinstance(derivation, Mapping):
            raise ValueError(f"derivation_query missing for {expected_id}")
        _require_keys(derivation, DERIVATION_FIELDS, f"derivation_query {expected_id}")
        if derivation["kind"] not in {"canonical_sparql", "policy"}:
            raise ValueError(f"invalid derivation kind for {expected_id}")
        for key in ("graph_sha256", "result_sha256"):
            value = derivation[key]
            if (
                not isinstance(value, str)
                or len(value) != 64
                or any(c not in "0123456789abcdef" for c in value)
            ):
                raise ValueError(f"invalid {key} for {expected_id}")
        if derivation["result_sha256"] != _sha256_json(derivation["result"]):
            raise ValueError(f"result_sha256 mismatch for {expected_id}")
        expected_record = _manifest_record(item, closure_results)
        if dict(record) != expected_record:
            raise ValueError(f"canonical migration evidence mismatch for {expected_id}")
    review = manifest["review"]
    if list(review) != ["reviewer_id", "signoff_required", "signed_off"]:
        raise ValueError("review fields/order must be exact")
    if review != {"reviewer_id": REVIEWER_ID, "signoff_required": True, "signed_off": True}:
        raise ValueError("manifest review must be signed off by repository-maintainer")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("v1", type=Path)
    parser.add_argument("v2", type=Path)
    parser.add_argument(
        "manifest",
        type=Path,
        nargs="?",
        default=Path("tests/research/benchmark_migration_manifest_v1.yaml"),
    )
    args = parser.parse_args()
    migrate_benchmark(args.source, args.v1, args.v2, args.manifest)


if __name__ == "__main__":
    main()
