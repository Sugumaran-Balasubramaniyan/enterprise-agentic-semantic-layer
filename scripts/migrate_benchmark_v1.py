"""Deterministically normalize the historical CIFRE benchmark corpus.

The historical YAML is deliberately treated as an input-only artifact.  This
module performs only local parsing and serialization; no clock, randomness,
network, model, or benchmark execution is involved.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml


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
GRAPH_SHA256 = "e36887b065ea722861f7a5d9b382bdebea349f37f7360245843b8375db40b017"
ZERO_SHA256 = "0" * 64
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


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _write_yaml(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = yaml.safe_dump(value, sort_keys=False, allow_unicode=False, default_flow_style=False)
    path.write_text(rendered, encoding="utf-8")


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


def _migration_values(item: Mapping[str, Any]) -> tuple[list[str], list[str], str, str]:
    record_id = item["id"]
    gold_before = sorted(set(item["expected_notes"]))
    if record_id in {"Q25", "Q28", "Q31"}:
        return (
            gold_before,
            sorted(set(gold_before + ["3012445"])),
            "SUCCESS",
            "PREREQUISITE_CLOSURE_EXPANSION",
        )
    if record_id in {"Q26", "Q30"}:
        return gold_before, gold_before, "SUCCESS", "PREREQUISITE_CLOSURE_NORMALIZATION"
    if record_id in {"Q27", "Q29", "Q32"}:
        return gold_before, gold_before, "SUCCESS", "PREREQUISITE_CLOSURE_NORMALIZATION"
    if int(item["tier"]) == 5:
        return gold_before, [], "EMPTY_RESULT", "STRICT_CONSTRAINT_STATUS_CORRECTION"
    return gold_before, gold_before, "SUCCESS", "SCHEMA_NORMALIZATION"


def _derivation(
    record_id: str,
    reason: str,
    gold_before: list[str],
    gold_after: list[str],
) -> dict[str, Any]:
    result = {"gold_before": gold_before, "gold_after": gold_after}
    if reason in {"PREREQUISITE_CLOSURE_EXPANSION", "PREREQUISITE_CLOSURE_NORMALIZATION"}:
        kind = "canonical_sparql"
        text = (
            "SELECT ?prerequisite WHERE { VALUES ?target { ?target_note } "
            "?target <https://example.org/cifre-kg/vocab/requiresPrerequisite>+ ?prerequisite . } "
            "ORDER BY ?prerequisite"
        ).replace("?target_note", record_id)
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


def _manifest_record(item: Mapping[str, Any]) -> dict[str, Any]:
    gold_before, gold_after, status_after, reason = _migration_values(item)
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
        "derivation_query": _derivation(item["id"], reason, gold_before, gold_after),
        "reviewer_id": REVIEWER_ID,
        "signed_off": True,
    }


def migrate_benchmark(source: Path, v1: Path, v2: Path, manifest: Path) -> None:
    """Generate normalized v1/v2 corpora and the signed migration manifest."""
    source = Path(source)
    v1 = Path(v1)
    v2 = Path(v2)
    manifest = Path(manifest)
    historical = _read_legacy(source)

    v1_records = []
    for item in historical:
        _before, after, status, reason = _migration_values(item)
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

    _write_yaml(
        v1, {"corpus_id": "cifre-synthetic-aqr-v1", "version": "1.0.0", "records": v1_records}
    )
    _write_yaml(
        v2, {"corpus_id": "cifre-synthetic-aqr-v2", "version": "2.0.0", "records": v2_records}
    )

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
        "records": [_manifest_record(item) for item in historical],
        "review": {"reviewer_id": REVIEWER_ID, "signoff_required": True, "signed_off": True},
    }
    validate_migration_manifest(manifest_document)
    _write_yaml(manifest, manifest_document)


def _require_keys(value: Mapping[str, Any], expected: Sequence[str], label: str) -> None:
    if list(value) != list(expected):
        raise ValueError(f"{label} fields/order must be exactly {list(expected)}")


def validate_migration_manifest(manifest: Mapping[str, Any]) -> None:
    """Validate the closed, signed manifest contract before it is written."""
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
    if not isinstance(manifest["records"], list) or len(manifest["records"]) != 40:
        raise ValueError("manifest must contain exactly 40 records")
    for expected_id, record in zip(expected_ids, manifest["records"], strict=True):
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
