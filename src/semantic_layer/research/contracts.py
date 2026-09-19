"""Canonical contracts shared by the deterministic research pipeline."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path
from typing import Any

import jsonschema

NAMESPACE_REGISTRY: Mapping[str, str] = {
    "cifsup": "https://example.org/cifre-kg/support#",
    "cifppms": "https://example.org/cifre-kg/ppms#",
    "cifdata": "https://example.org/cifre-kg/data/",
    "ciferp": "https://example.org/cifre-kg/erp#",
    "cifskos": "https://example.org/cifre-kg/vocabulary#",
    "cifmeta": "https://example.org/cifre-kg/meta#",
    "cifmetaid": "https://example.org/cifre-kg/id/meta/",
}

CONDITIONS = (
    "deterministic_no_reflection_ablation",
    "deterministic_bounded_repair",
)


class Status(StrEnum):
    """Closed set of final per-query statuses."""

    SUCCESS = "SUCCESS"
    UNSUPPORTED = "UNSUPPORTED"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    EMPTY_RESULT = "EMPTY_RESULT"


class ReasonCode(StrEnum):
    """Closed set of final per-query and artifact diagnostics."""

    NONE = "NONE"
    UNKNOWN_TOKEN = "UNKNOWN_TOKEN"
    UNKNOWN_ENTITY = "UNKNOWN_ENTITY"
    AMBIGUOUS_INPUT = "AMBIGUOUS_INPUT"
    AMBIGUOUS_INTENT = "AMBIGUOUS_INTENT"
    MULTIPLE_DISTINCT_ENTITIES = "MULTIPLE_DISTINCT_ENTITIES"
    UNSUPPORTED_INTENT = "UNSUPPORTED_INTENT"
    MISSING_REQUIRED_ENTITY = "MISSING_REQUIRED_ENTITY"
    UNBOUND_REQUIRED_PROJECTION = "UNBOUND_REQUIRED_PROJECTION"
    SPARQL_SYNTAX = "SPARQL_SYNTAX"
    SPARQL_EXECUTION = "SPARQL_EXECUTION"
    EMPTY_STRICT_RESULT = "EMPTY_STRICT_RESULT"
    RELAX_SUPPORT_PACKAGE = "RELAX_SUPPORT_PACKAGE"
    WIDEN_COMPONENT = "WIDEN_COMPONENT"
    REPAIR_BUDGET_EXHAUSTED = "REPAIR_BUDGET_EXHAUSTED"
    PROVENANCE_MISSING = "PROVENANCE_MISSING"
    HASH_MISMATCH = "HASH_MISMATCH"
    INVALID_DATASET = "INVALID_DATASET"
    NO_OP_REPAIR = "NO_OP_REPAIR"
    PREREQUISITE_DEPTH_EXCEEDED = "PREREQUISITE_DEPTH_EXCEEDED"


def canonical_json(value: object) -> bytes:
    """Serialize a value using the artifact's deterministic JSON contract."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase hexadecimal SHA-256 digest of *data*."""

    return hashlib.sha256(data).hexdigest()


def _schema_path() -> Path:
    return Path(__file__).resolve().parents[3] / "tests/research/result_schema.json"


def load_and_validate_result(path: Path) -> dict[str, Any]:
    """Load and validate a deterministic result against the root schema."""

    document = json.loads(path.read_bytes())
    schema = json.loads(_schema_path().read_bytes())
    jsonschema.Draft202012Validator(schema).validate(document)
    if not isinstance(document, dict):
        raise TypeError("research result root must be a JSON object")
    return document


__all__ = [
    "CONDITIONS",
    "NAMESPACE_REGISTRY",
    "ReasonCode",
    "Status",
    "canonical_json",
    "load_and_validate_result",
    "sha256_bytes",
]
