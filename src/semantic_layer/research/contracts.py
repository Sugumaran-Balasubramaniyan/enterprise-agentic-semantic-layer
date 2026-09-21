"""Canonical contracts shared by the deterministic research pipeline."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any

import jsonschema

NAMESPACE_REGISTRY: Mapping[str, str] = MappingProxyType(
    {
        "cifsup": "https://example.org/cifre-kg/support#",
        "cifppms": "https://example.org/cifre-kg/ppms#",
        "cifdata": "https://example.org/cifre-kg/data/",
        "ciferp": "https://example.org/cifre-kg/erp#",
        "cifskos": "https://example.org/cifre-kg/vocabulary#",
        "cifmeta": "https://example.org/cifre-kg/meta#",
        "cifmetaid": "https://example.org/cifre-kg/id/meta/",
    }
)

CONDITIONS = (
    "deterministic_no_reflection_ablation",
    "deterministic_bounded_repair",
)

_ENVIRONMENT_FIELDS = frozenset(
    {
        "python_version",
        "platform_system",
        "platform_machine",
        "pip_version",
        "lock_sha256",
        "packages",
    }
)
_PYTHON_VERSION_PATTERN = re.compile(r"3\.12\.[0-9]+")
_SUPPORTED_PLATFORM_MACHINES = frozenset({"aarch64", "x86_64"})


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


def validate_environment_contract(
    environment: Mapping[str, Any], *, label: str = "environment"
) -> None:
    """Reject runtime metadata outside the supported publication contract."""

    if not isinstance(environment, Mapping):
        raise TypeError(f"{label} must be an object")
    if set(environment) != _ENVIRONMENT_FIELDS:
        raise ValueError(f"{label} fields are incomplete")
    python_version = environment["python_version"]
    if (
        not isinstance(python_version, str)
        or _PYTHON_VERSION_PATTERN.fullmatch(python_version) is None
    ):
        raise ValueError(f"{label} python_version must match 3.12.<numeric patch>")
    if environment["platform_system"] != "Linux":
        raise ValueError(f"{label} platform_system must be Linux")
    if environment["platform_machine"] not in _SUPPORTED_PLATFORM_MACHINES:
        raise ValueError(
            f"{label} platform_machine must be one of {sorted(_SUPPORTED_PLATFORM_MACHINES)}"
        )
    if environment["pip_version"] != "25.2":
        raise ValueError(f"{label} pip_version must be exactly 25.2")


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase hexadecimal SHA-256 digest of *data*."""

    return hashlib.sha256(data).hexdigest()


def _schema_path() -> Path:
    return Path(__file__).resolve().parents[3] / "tests/research/result_schema.json"


def load_and_validate_result(
    path: Path, *, require_canonical_bytes: bool = False
) -> dict[str, Any]:
    """Load and validate a deterministic result against the root schema.

    ``require_canonical_bytes`` is reserved for checked-in publication
    artifacts. Temporary fixtures may intentionally omit the final newline,
    while a committed artifact must exactly match the canonical serializer.
    """

    raw = path.read_bytes()
    document = json.loads(raw)
    schema = json.loads(_schema_path().read_bytes())
    jsonschema.Draft202012Validator(schema).validate(document)
    if not isinstance(document, dict):
        raise TypeError("research result root must be a JSON object")
    if require_canonical_bytes and raw != canonical_json(document) + b"\n":
        raise ValueError("result artifact bytes are not canonical UTF-8 JSON")
    validate_environment_contract(document["environment"])
    return document


__all__ = [
    "CONDITIONS",
    "NAMESPACE_REGISTRY",
    "ReasonCode",
    "Status",
    "canonical_json",
    "load_and_validate_result",
    "sha256_bytes",
    "validate_environment_contract",
]
