"""Local DuckDB execution guarded by compiler, authorization, and quality capabilities."""

from __future__ import annotations

import math
from collections.abc import Iterator, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any

import duckdb

from semantic_layer.compiler.base import CompiledQuery
from semantic_layer.control import digest, file_digest, registry_digest
from semantic_layer.governance import AuthorizationDecision
from semantic_layer.models import CallerContext
from semantic_layer.quality import QualityReport
from semantic_layer.registry import SemanticRegistry

_VIEWS = {"customers": "customers.csv", "policies": "policies.csv", "claims": "claims.csv"}
_EXECUTION_ISSUER = object()


class ExecutionResult(Sequence[dict[str, Any]]):
    """Immutable, execution-issued result carrying source and control fingerprints."""

    __slots__ = (
        "_issuer",
        "_rows",
        "approved_products",
        "authorization_digest",
        "authorization_outcome",
        "caller_digest",
        "digest",
        "field_evidence",
        "lineage",
        "local_sources",
        "mapping_evidence",
        "parameter_digest",
        "plan_digest",
        "quality_digest",
        "query_digest",
        "semantic_versions",
        "source_digests",
    )

    def __init__(self, *_: object, **__: object) -> None:
        raise TypeError("ExecutionResult instances are adapter-issued only")

    @classmethod
    def _issue(
        cls,
        *,
        rows: list[dict[str, Any]],
        query: CompiledQuery,
        source_digests: dict[str, str],
        local_sources: dict[str, str],
        quality: QualityReport,
    ) -> ExecutionResult:
        result = object.__new__(cls)
        immutable_rows = tuple(dict(row) for row in rows)
        object.__setattr__(result, "_rows", immutable_rows)
        object.__setattr__(result, "source_digests", dict(sorted(source_digests.items())))
        object.__setattr__(result, "local_sources", dict(sorted(local_sources.items())))
        object.__setattr__(result, "mapping_evidence", dict(quality.mapping_evidence))
        object.__setattr__(result, "quality_digest", quality.digest)
        object.__setattr__(result, "plan_digest", query.plan_digest)
        object.__setattr__(result, "caller_digest", query.caller_digest)
        object.__setattr__(result, "authorization_digest", query.authorization_digest)
        object.__setattr__(result, "authorization_outcome", query.authorization_outcome)
        object.__setattr__(result, "query_digest", query.query_digest)
        object.__setattr__(result, "parameter_digest", query.parameter_digest)
        object.__setattr__(result, "lineage", query.lineage)
        object.__setattr__(result, "field_evidence", dict(query.field_evidence))
        object.__setattr__(result, "semantic_versions", dict(query.semantic_versions))
        object.__setattr__(result, "approved_products", query.approved_products)
        object.__setattr__(
            result,
            "digest",
            digest(
                {
                    "rows": immutable_rows,
                    "sources": source_digests,
                    "local_sources": local_sources,
                    "mappings": quality.mapping_evidence,
                    "quality": quality.digest,
                    "query": query.query_digest,
                    "parameters": query.parameter_digest,
                    "authorization": query.authorization_digest,
                }
            ),
        )
        object.__setattr__(result, "_issuer", _EXECUTION_ISSUER)
        return result

    def _is_issued(self) -> bool:
        return self._issuer is _EXECUTION_ISSUER

    def __len__(self) -> int:
        return len(self._rows)

    def __getitem__(self, index: int | slice) -> dict[str, Any] | tuple[dict[str, Any], ...]:
        if isinstance(index, slice):
            return tuple(dict(row) for row in self._rows[index])
        return dict(self._rows[index])

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(tuple(dict(row) for row in self._rows))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ExecutionResult):
            return self.digest == other.digest
        if isinstance(other, list):
            return list(self) == other
        return NotImplemented


class LocalDuckDBAdapter:
    """Execute only compiler-issued artifacts against quality-bound curated data."""

    def __init__(self, curated_data_path: Path, registry: SemanticRegistry) -> None:
        self.curated_data_path = curated_data_path.resolve()
        self.registry = registry
        if not self.curated_data_path.is_dir():
            raise ValueError("curated data path must be an existing directory")

    @staticmethod
    def _sql_literal(path: Path) -> str:
        return str(path).replace("'", "''")

    def _source_digests(self) -> dict[str, str]:
        return {
            name: file_digest(self.curated_data_path / name)
            for name in sorted({*self._required_quality_datasets()})
        }

    def _local_sources(self) -> dict[str, str]:
        return {
            name: str((self.curated_data_path / name).resolve())
            for name in self._required_quality_datasets()
        }

    @staticmethod
    def _required_quality_datasets() -> tuple[str, ...]:
        return ("claims.csv", "customers.csv", "policies.csv", "premiums.csv")

    @staticmethod
    def _assert_finite_rows(rows: list[dict[str, Any]]) -> None:
        for row in rows:
            for field, value in row.items():
                if isinstance(value, Decimal) and not value.is_finite():
                    raise ValueError(f"execution returned non-finite value for {field}")
                if isinstance(value, float) and not math.isfinite(value):
                    raise ValueError(f"execution returned non-finite value for {field}")

    def execute(
        self,
        query: CompiledQuery,
        authorization: AuthorizationDecision,
        caller: CallerContext,
        quality: QualityReport,
    ) -> ExecutionResult:
        """Execute only matching compiler/auth/quality capabilities; raw SQL is impossible here."""

        if not isinstance(query, CompiledQuery) or not query._is_issued():
            raise TypeError("LocalDuckDBAdapter executes compiler-issued CompiledQuery artifacts only")
        if query.target_platform != "DuckDB" or query.registry_digest != registry_digest(self.registry):
            raise ValueError("compiled query is not bound to this local execution context")
        if not isinstance(authorization, AuthorizationDecision) or not authorization._is_issued():
            raise ValueError("authorization capability does not match execution context")
        if (
            not authorization.allowed
            or authorization.plan_digest != query.plan_digest
            or authorization.caller_digest != query.caller_digest
            or authorization.caller_digest != digest(caller)
            or authorization.registry_digest != registry_digest(self.registry)
            or query.authorization_digest
            != digest(
            {
                "plan": authorization.plan_digest,
                "caller": authorization.caller_digest,
                "registry": authorization.registry_digest,
                "outcome": authorization.reason_code,
            }
            )
        ):
            raise ValueError("authorization capability does not match compiled query")
        if not isinstance(quality, QualityReport) or not quality._matches(
            self.curated_data_path, self.registry
        ):
            raise ValueError("quality report does not match complete current source data")
        if quality.source_digests != self._source_digests():
            raise ValueError("quality source digests do not match current execution data")
        connection = duckdb.connect(database=":memory:")
        try:
            for view, filename in _VIEWS.items():
                csv_path = self.curated_data_path / filename
                connection.execute(
                    f"CREATE VIEW {view} AS SELECT * FROM read_csv_auto('{self._sql_literal(csv_path)}', HEADER=TRUE)"
                )
            cursor = connection.execute(query.sql, query.parameters)
            columns = [column[0] for column in cursor.description]
            rows = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
            self._assert_finite_rows(rows)
            return ExecutionResult._issue(
                rows=rows,
                query=query,
                source_digests=self._source_digests(),
                local_sources=self._local_sources(),
                quality=quality,
            )
        finally:
            connection.close()
