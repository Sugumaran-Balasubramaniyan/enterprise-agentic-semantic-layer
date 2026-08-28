"""Append-only SQLite provenance derived only from an actual execution result."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from semantic_layer.adapters.duckdb import ExecutionResult
from semantic_layer.control import digest


@dataclass(frozen=True)
class Provenance:
    """An immutable evidence envelope correlated to one local execution capability."""

    query_id: str
    question_digest: str
    execution_digest: str
    plan_digest: str
    query_digest: str
    parameter_digest: str
    caller_digest: str
    authorization_digest: str
    authorization_outcome: str
    quality_digest: str
    result_digest: str
    source_digests: dict[str, str]
    local_sources: dict[str, str]
    mapping_evidence: dict[str, str]
    concepts: list[str]
    metric_ids: list[str]
    data_products: list[str]
    mapping_ids: list[str]
    physical_sources: list[str]
    field_evidence: dict[str, str]
    semantic_versions: dict[str, str]
    quality_status: str
    row_count: int
    compiled_platform: str
    created_at: str


class ProvenanceStore:
    """Expose append and read operations only; mutation handles stay private."""

    def __init__(self, path: Path) -> None:
        self._connection = sqlite3.connect(path)
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS provenance (query_id TEXT PRIMARY KEY, document TEXT NOT NULL)"
        )
        self._connection.commit()

    def record(self, *, question: str, execution: ExecutionResult) -> Provenance:
        """Append provenance only from an adapter-issued execution result."""

        if not isinstance(execution, ExecutionResult) or not execution._is_issued():
            raise TypeError("provenance requires an adapter-issued ExecutionResult")
        lineage = execution.lineage
        provenance = Provenance(
            query_id=str(uuid4()),
            question_digest=digest(question),
            execution_digest=execution.digest,
            plan_digest=execution.plan_digest,
            query_digest=execution.query_digest,
            parameter_digest=execution.parameter_digest,
            caller_digest=execution.caller_digest,
            authorization_digest=execution.authorization_digest,
            authorization_outcome=execution.authorization_outcome,
            quality_digest=execution.quality_digest,
            result_digest=digest(tuple(execution)),
            source_digests=execution.source_digests,
            local_sources=execution.local_sources,
            mapping_evidence=execution.mapping_evidence,
            concepts=[],
            metric_ids=lineage.metric_ids,
            data_products=lineage.data_products,
            mapping_ids=lineage.mapping_ids,
            physical_sources=lineage.physical_sources,
            field_evidence=execution.field_evidence,
            semantic_versions=execution.semantic_versions,
            quality_status="PASS",
            row_count=len(execution),
            compiled_platform="DuckDB",
            created_at=datetime.now(UTC).isoformat(),
        )
        self._connection.execute(
            "INSERT INTO provenance (query_id, document) VALUES (?, ?)",
            (provenance.query_id, json.dumps(asdict(provenance), sort_keys=True)),
        )
        self._connection.commit()
        return provenance

    def get(self, query_id: str) -> Provenance:
        """Read a previously appended provenance record without exposing mutation APIs."""

        row = self._connection.execute(
            "SELECT document FROM provenance WHERE query_id = ?", (query_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"no provenance record for query_id {query_id}")
        return Provenance(**json.loads(row[0]))
