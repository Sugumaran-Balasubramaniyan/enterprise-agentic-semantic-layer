"""Signed append-only SQLite provenance derived only from verified local execution."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from uuid import uuid4

from semantic_layer.adapters.duckdb import ExecutionResult
from semantic_layer.control import _sign, _verify, digest


class _FrozenList(tuple):
    """JSON-compatible immutable representation that retains list semantics on read."""


class Provenance:
    """Signed immutable evidence envelope; public callers cannot mint or edit it."""

    __slots__ = ("_signature", "_values")

    def __init__(self, *_: object, **__: object) -> None:
        raise TypeError("Provenance records are store-issued only")

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("Provenance records are immutable")

    def __getattr__(self, name: str):
        try:
            return _thaw(self._values[name])
        except KeyError as error:
            raise AttributeError(name) from error

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Provenance) and self._signature == other._signature

    def _payload(self) -> dict[str, object]:
        return {name: _thaw(value) for name, value in self._values.items()}

    def _verify_integrity(self) -> bool:
        return _verify("Provenance", self._payload(), self._signature)


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return _FrozenList(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, _FrozenList):
        return [_thaw(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_thaw(item) for item in value)
    return value


class ProvenanceStore:
    """Expose append/read only and reject forged execution, questions, and stored rows."""

    def __init__(self, path: Path) -> None:
        self._connection = sqlite3.connect(path)
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS provenance (query_id TEXT PRIMARY KEY, document TEXT NOT NULL, signature TEXT NOT NULL)"
        )
        self._connection.commit()

    def record(self, *, question: str, execution: ExecutionResult) -> Provenance:
        """Append evidence only for an intact signed execution of the matching question."""

        if type(execution) is not ExecutionResult or not execution._verify_integrity():
            raise ValueError("execution integrity signature is invalid")
        if digest(question) != execution.question_digest:
            raise ValueError("question does not match the executed semantic plan")
        values: dict[str, object] = {
            "query_id": str(uuid4()),
            "question_digest": digest(question),
            "execution_digest": execution.digest,
            "plan_digest": execution.plan_digest,
            "query_digest": execution.query_digest,
            "parameter_digest": execution.parameter_digest,
            "caller_digest": execution.caller_digest,
            "authorization_digest": execution.authorization_digest,
            "authorization_outcome": execution.authorization_outcome,
            "quality_digest": execution.quality_digest,
            "result_digest": digest(tuple(execution)),
            "source_digests": dict(execution.source_digests),
            "local_sources": dict(execution.local_sources),
            "mapping_evidence": dict(execution.mapping_evidence),
            "concepts": tuple(execution.concepts),
            "metric_ids": tuple(execution.metric_ids),
            "data_products": list(execution.approved_products),
            "mapping_ids": tuple(execution.mapping_ids),
            "physical_sources": tuple(execution.local_sources.values()),
            "field_evidence": dict(execution.field_evidence),
            "semantic_versions": dict(execution.semantic_versions),
            "quality_status": "PASS",
            "row_count": len(execution),
            "compiled_platform": "DuckDB",
            "created_at": datetime.now(UTC).isoformat(),
        }
        record = object.__new__(Provenance)
        immutable_values = MappingProxyType({key: _freeze(value) for key, value in values.items()})
        object.__setattr__(record, "_values", immutable_values)
        object.__setattr__(record, "_signature", _sign("Provenance", record._payload()))
        self._connection.execute(
            "INSERT INTO provenance (query_id, document, signature) VALUES (?, ?, ?)",
            (record.query_id, json.dumps(record._payload(), sort_keys=True), record._signature),
        )
        self._connection.commit()
        return record

    def get(self, query_id: str) -> Provenance:
        """Read a signed immutable record and fail closed if the SQLite row was altered."""

        row = self._connection.execute(
            "SELECT document, signature FROM provenance WHERE query_id = ?", (query_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"no provenance record for query_id {query_id}")
        document, stored_signature = row
        values = json.loads(document)
        record = object.__new__(Provenance)
        immutable_values = MappingProxyType({key: _freeze(value) for key, value in values.items()})
        object.__setattr__(record, "_values", immutable_values)
        object.__setattr__(record, "_signature", _sign("Provenance", record._payload()))
        if record._signature != stored_signature:
            raise ValueError("stored provenance integrity signature is invalid")
        return record
