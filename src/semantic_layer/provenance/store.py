"""SQLite-backed provenance persistence for local semantic answers."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from semantic_layer.compiler.base import CompiledQuery
from semantic_layer.governance.policy import AuthorizationDecision
from semantic_layer.lineage.service import LineageEnvelope
from semantic_layer.models import SemanticQueryPlan
from semantic_layer.quality.checks import QualityReport


@dataclass(frozen=True)
class Provenance:
    """Static and dynamic evidence needed to trace one governed answer."""

    query_id: str
    question: str
    concepts: list[str]
    metric_ids: list[str]
    data_products: list[str]
    mapping_ids: list[str]
    physical_sources: list[str]
    semantic_versions: dict[str, str]
    authorization_outcome: str
    quality_status: str
    row_count: int
    compiled_platform: str
    created_at: str


class ProvenanceStore:
    """Persist and retrieve provenance records in a caller-owned SQLite database."""

    def __init__(self, path: Path) -> None:
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS provenance (query_id TEXT PRIMARY KEY, document TEXT NOT NULL)"
        )
        self.connection.commit()

    def record(
        self,
        *,
        question: str,
        plan: SemanticQueryPlan,
        authorization: AuthorizationDecision,
        quality: QualityReport,
        lineage: LineageEnvelope,
        compiled_query: CompiledQuery,
        row_count: int,
    ) -> Provenance:
        """Store a dynamic execution record paired with registry-derived lineage."""

        if not authorization.allowed:
            raise ValueError("cannot create provenance for a denied authorization decision")
        if quality.status != "PASS":
            raise ValueError("cannot create provenance for failed curated-data quality")
        if tuple(lineage.data_products) != compiled_query.approved_products:
            raise ValueError("compiled query products do not match static lineage")
        record = Provenance(
            query_id=str(uuid4()),
            question=question,
            concepts=[plan.root_entity, *plan.projected_dimensions],
            metric_ids=lineage.metric_ids,
            data_products=lineage.data_products,
            mapping_ids=lineage.mapping_ids,
            physical_sources=lineage.physical_sources,
            semantic_versions=lineage.semantic_versions,
            authorization_outcome=authorization.reason_code,
            quality_status=quality.status,
            row_count=row_count,
            compiled_platform=compiled_query.target_platform,
            created_at=datetime.now(UTC).isoformat(),
        )
        self.connection.execute(
            "INSERT INTO provenance (query_id, document) VALUES (?, ?)",
            (record.query_id, json.dumps(asdict(record), sort_keys=True)),
        )
        self.connection.commit()
        return record

    def get(self, query_id: str) -> Provenance:
        """Retrieve one immutable provenance record or fail explicitly when absent."""

        row = self.connection.execute(
            "SELECT document FROM provenance WHERE query_id = ?", (query_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"no provenance record for query_id {query_id}")
        return Provenance(**json.loads(row[0]))
