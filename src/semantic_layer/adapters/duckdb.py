"""Local DuckDB execution guarded by signed compiler, policy, and quality capabilities."""

from __future__ import annotations

import math
from collections.abc import Iterator, Sequence
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any

import duckdb

from semantic_layer.compiler.base import CompiledQuery
from semantic_layer.control import (
    digest,
    file_digest,
    has_valid_signature,
    registry_digest,
    signature,
)
from semantic_layer.governance import AuthorizationDecision
from semantic_layer.models import CallerContext
from semantic_layer.quality import QualityReport
from semantic_layer.registry import SemanticRegistry

_VIEWS = {"customers": "customers.csv", "policies": "policies.csv", "claims": "claims.csv"}


class ExecutionResult(Sequence[dict[str, Any]]):
    """Signed immutable output from one verified local DuckDB execution."""

    __slots__ = (
        "_rows",
        "_signature",
        "approved_products",
        "authorization_digest",
        "authorization_outcome",
        "caller_digest",
        "concepts",
        "digest",
        "field_evidence",
        "local_sources",
        "mapping_evidence",
        "mapping_ids",
        "metric_ids",
        "parameter_digest",
        "plan_digest",
        "quality_digest",
        "query_digest",
        "question_digest",
        "semantic_versions",
        "source_digests",
    )

    def __init__(self, *_: object, **__: object) -> None:
        raise TypeError("ExecutionResult instances are adapter-issued only")

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("ExecutionResult capabilities are immutable")

    def _payload(self) -> dict[str, object]:
        return {
            "rows": self._rows,
            "sources": self.source_digests,
            "local_sources": self.local_sources,
            "mappings": self.mapping_evidence,
            "quality": self.quality_digest,
            "question": self.question_digest,
            "concepts": self.concepts,
            "query": self.query_digest,
            "parameters": self.parameter_digest,
            "authorization": self.authorization_digest,
            "plan": self.plan_digest,
            "caller": self.caller_digest,
            "products": self.approved_products,
            "mapping_ids": self.mapping_ids,
            "metrics": self.metric_ids,
            "fields": self.field_evidence,
            "versions": self.semantic_versions,
        }

    def _verify_integrity(self) -> bool:
        return self.digest == digest(self._payload()) and has_valid_signature(
            "ExecutionResult", self._payload(), self._signature
        )

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
    """Execute only signed capabilities against complete quality-bound local CSV sources."""

    def __init__(self, curated_data_path: Path, registry: SemanticRegistry) -> None:
        if type(registry) is not SemanticRegistry:
            raise TypeError("local execution requires the repository-issued semantic registry")
        self.curated_data_path = curated_data_path.resolve()
        self.registry = registry
        if not self.curated_data_path.is_dir():
            raise ValueError("curated data path must be an existing directory")

    @staticmethod
    def _sql_literal(path: Path) -> str:
        return str(path).replace("'", "''")

    def _source_digests(self) -> dict[str, str]:
        return {name: file_digest(self.curated_data_path / name) for name in self._required_quality_datasets()}

    def _local_sources(self) -> dict[str, str]:
        return {name: str((self.curated_data_path / name).resolve()) for name in self._required_quality_datasets()}

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
        """Verify every transition before executing parameterized SQL against local canonical views."""

        if type(query) is not CompiledQuery or not query._verify_integrity():
            raise ValueError("compiled query integrity signature is invalid")
        if query.target_platform != "DuckDB" or query.registry_digest != registry_digest(self.registry):
            raise ValueError("compiled query is not bound to this local execution context")
        if type(authorization) is not AuthorizationDecision or not authorization._verify_integrity():
            raise ValueError("authorization integrity signature is invalid")
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
        if type(quality) is not QualityReport or not quality._matches(self.curated_data_path, self.registry):
            raise ValueError("quality report integrity signature does not match complete current source data")
        if dict(quality.source_digests) != self._source_digests():
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
            result = object.__new__(ExecutionResult)
            frozen_rows = tuple(MappingProxyType(dict(row)) for row in rows)
            payload = {
                "_rows": frozen_rows,
                "source_digests": MappingProxyType(dict(sorted(self._source_digests().items()))),
                "local_sources": MappingProxyType(dict(sorted(self._local_sources().items()))),
                "mapping_evidence": MappingProxyType(dict(quality.mapping_evidence)),
                "quality_digest": quality.digest,
                "question_digest": query.question_digest,
                "concepts": tuple(query.concepts),
                "plan_digest": query.plan_digest,
                "caller_digest": query.caller_digest,
                "authorization_digest": query.authorization_digest,
                "authorization_outcome": query.authorization_outcome,
                "query_digest": query.query_digest,
                "parameter_digest": query.parameter_digest,
                "field_evidence": MappingProxyType(dict(query.field_evidence)),
                "semantic_versions": MappingProxyType(dict(query.semantic_versions)),
                "approved_products": tuple(query.approved_products),
                "mapping_ids": tuple(query.mapping_ids),
                "metric_ids": tuple(query.metric_ids),
            }
            for name, value in payload.items():
                object.__setattr__(result, name, value)
            object.__setattr__(result, "digest", digest(result._payload()))
            object.__setattr__(result, "_signature", signature("ExecutionResult", result._payload()))
            return result
        finally:
            connection.close()
