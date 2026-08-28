"""Signed append-only SQLite provenance derived only from verified local execution."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from types import MappingProxyType
from uuid import uuid4

from semantic_layer.adapters.duckdb import ExecutionResult
from semantic_layer.control import _sign, _verify, digest

_GENESIS_HASH = hashlib.sha256(b"semantic-layer-provenance-chain-v1").hexdigest()
_CHAIN_ID = "semantic-layer-provenance-chain-v1"


def _chain_hash(
    *, query_id: str, document: str, stored_signature: str, sequence: int, previous_hash: str
) -> str:
    payload = json.dumps(
        {
            "query_id": query_id,
            "document": document,
            "signature": stored_signature,
            "sequence": sequence,
            "previous_hash": previous_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _checkpoint_signature(sequence: int, row_hash: str) -> str:
    return _sign(
        "ProvenanceCheckpoint",
        {"chain_id": _CHAIN_ID, "sequence": sequence, "row_hash": row_hash},
    )


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
    """Expose append/read-only provenance with a tamper-evident SQLite chain."""

    def __init__(self, path: Path) -> None:
        # FastAPI dispatches synchronous routes to worker threads.  The store
        # remains one serialized append/read chain, so permit that hand-off and
        # protect every public chain operation with one process-local lock.
        self._lock = RLock()
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS provenance (
                query_id TEXT PRIMARY KEY,
                document TEXT NOT NULL,
                signature TEXT NOT NULL,
                sequence INTEGER NOT NULL UNIQUE,
                previous_hash TEXT NOT NULL,
                row_hash TEXT NOT NULL
            )
        """)
        columns = {
            row[1] for row in self._connection.execute("PRAGMA table_info(provenance)").fetchall()
        }
        required_columns = {"query_id", "document", "signature", "sequence", "previous_hash", "row_hash"}
        if columns != required_columns:
            self._connection.close()
            raise ValueError("provenance database schema is not tamper-evident")
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS provenance_checkpoint (
                checkpoint_id INTEGER PRIMARY KEY CHECK (checkpoint_id = 1),
                sequence INTEGER NOT NULL,
                row_hash TEXT NOT NULL,
                chain_id TEXT NOT NULL,
                checkpoint_signature TEXT NOT NULL
            )
        """)
        checkpoint_columns = {
            row[1]
            for row in self._connection.execute("PRAGMA table_info(provenance_checkpoint)").fetchall()
        }
        required_checkpoint_columns = {
            "checkpoint_id", "sequence", "row_hash", "chain_id", "checkpoint_signature"
        }
        if checkpoint_columns != required_checkpoint_columns:
            self._connection.close()
            raise ValueError("provenance database checkpoint is not authenticated")
        checkpoint = self._connection.execute(
            "SELECT sequence, row_hash, chain_id, checkpoint_signature "
            "FROM provenance_checkpoint WHERE checkpoint_id = 1"
        ).fetchone()
        if checkpoint is None:
            if self._connection.execute("SELECT 1 FROM provenance LIMIT 1").fetchone() is not None:
                self._connection.close()
                raise ValueError("provenance database is missing its chain checkpoint")
            self._connection.execute(
                "INSERT INTO provenance_checkpoint "
                "(checkpoint_id, sequence, row_hash, chain_id, checkpoint_signature) VALUES (1, 0, ?, ?, ?)",
                (_GENESIS_HASH, _CHAIN_ID, _checkpoint_signature(0, _GENESIS_HASH)),
            )
        self._connection.commit()

    def _checkpoint(self) -> tuple[int, str]:
        checkpoint = self._connection.execute(
            "SELECT sequence, row_hash, chain_id, checkpoint_signature "
            "FROM provenance_checkpoint WHERE checkpoint_id = 1"
        ).fetchone()
        if checkpoint is None:
            raise ValueError("provenance chain checkpoint is missing")
        sequence, row_hash, chain_id, checkpoint_signature = checkpoint
        if (
            not isinstance(sequence, int)
            or not isinstance(row_hash, str)
            or chain_id != _CHAIN_ID
            or not isinstance(checkpoint_signature, str)
            or not _verify(
                "ProvenanceCheckpoint",
                {"chain_id": chain_id, "sequence": sequence, "row_hash": row_hash},
                checkpoint_signature,
            )
        ):
            raise ValueError("provenance checkpoint signature is invalid")
        return sequence, row_hash

    def _verify_chain(self) -> None:
        head_sequence, head_hash = self._checkpoint()
        rows = self._connection.execute(
            "SELECT query_id, document, signature, sequence, previous_hash, row_hash "
            "FROM provenance ORDER BY sequence"
        ).fetchall()
        if head_sequence != len(rows):
            raise ValueError("provenance chain checkpoint does not match stored rows")
        previous_hash = _GENESIS_HASH
        for expected_sequence, row in enumerate(rows, start=1):
            query_id, document, stored_signature, sequence, row_previous_hash, row_hash = row
            if (
                not isinstance(query_id, str)
                or not isinstance(document, str)
                or not isinstance(stored_signature, str)
                or sequence != expected_sequence
                or row_previous_hash != previous_hash
                or row_hash
                != _chain_hash(
                    query_id=query_id,
                    document=document,
                    stored_signature=stored_signature,
                    sequence=sequence,
                    previous_hash=row_previous_hash,
                )
            ):
                raise ValueError("provenance chain integrity is invalid")
            try:
                values = json.loads(document)
            except (TypeError, json.JSONDecodeError) as error:
                raise ValueError("stored provenance document is invalid") from error
            if not isinstance(values, dict) or values.get("query_id") != query_id:
                raise ValueError("stored provenance query_id does not match its SQLite key")
            if not _verify("Provenance", values, stored_signature):
                raise ValueError("stored provenance integrity signature is invalid")
            previous_hash = row_hash
        if head_hash != previous_hash:
            raise ValueError("provenance chain checkpoint hash is invalid")

    def record(self, *, question: str, execution: ExecutionResult) -> Provenance:
        """Append evidence only for an intact signed execution of the matching question."""

        with self._lock:
            self._verify_chain()
            if type(execution) is not ExecutionResult or not execution._verify_integrity():
                raise ValueError("execution integrity signature is invalid")
            if execution.authorization_outcome != "ALLOWED":
                raise ValueError("execution authorization outcome is not allowed")
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
                "queried_sources": dict(execution.queried_sources),
                "quality_validated_sources": dict(execution.quality_validated_sources),
                "mapping_evidence": dict(execution.mapping_evidence),
                "concepts": tuple(execution.concepts),
                "metric_ids": tuple(execution.metric_ids),
                "data_products": list(execution.approved_products),
                "mapping_ids": tuple(execution.mapping_ids),
                # Preserve the established physical-source envelope for
                # compatibility; the explicit source-role fields below make
                # queried versus quality-validated scope unambiguous.
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
            document = json.dumps(record._payload(), sort_keys=True)
            sequence, previous_hash = self._checkpoint()
            sequence += 1
            row_hash = _chain_hash(
                query_id=record.query_id,
                document=document,
                stored_signature=record._signature,
                sequence=sequence,
                previous_hash=previous_hash,
            )
            try:
                self._connection.execute(
                    "INSERT INTO provenance "
                    "(query_id, document, signature, sequence, previous_hash, row_hash) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (record.query_id, document, record._signature, sequence, previous_hash, row_hash),
                )
                self._connection.execute(
                    "UPDATE provenance_checkpoint SET sequence = ?, row_hash = ?, checkpoint_signature = ? "
                    "WHERE checkpoint_id = 1",
                    (sequence, row_hash, _checkpoint_signature(sequence, row_hash)),
                )
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise
            return record

    def get(self, query_id: str) -> Provenance:
        """Read a signed immutable record and fail closed if the SQLite row was altered."""

        with self._lock:
            self._verify_chain()
            row = self._connection.execute(
                "SELECT document, signature FROM provenance WHERE query_id = ?", (query_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"no provenance record for query_id {query_id}")
            document, stored_signature = row
            try:
                values = json.loads(document)
            except (TypeError, json.JSONDecodeError) as error:
                raise ValueError("stored provenance document is invalid") from error
            if not isinstance(values, dict) or values.get("query_id") != query_id:
                raise ValueError("stored provenance query_id does not match its SQLite key")
            record = object.__new__(Provenance)
            immutable_values = MappingProxyType({key: _freeze(value) for key, value in values.items()})
            object.__setattr__(record, "_values", immutable_values)
            if not isinstance(stored_signature, str) or not _verify("Provenance", record._payload(), stored_signature):
                raise ValueError("stored provenance integrity signature is invalid")
            object.__setattr__(record, "_signature", stored_signature)
            return record
