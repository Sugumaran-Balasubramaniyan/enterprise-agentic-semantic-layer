"""Opaque compiler artifacts that carry a bound execution context."""

from __future__ import annotations

from typing import Any

from semantic_layer.control import digest

_QUERY_ISSUER = object()


class CompiledQuery:
    """A non-forgeable, compiler-issued SQL capability for one execution context."""

    __slots__ = (
        "_issuer",
        "approved_products",
        "authorization_digest",
        "authorization_outcome",
        "caller_digest",
        "field_evidence",
        "lineage",
        "parameter_digest",
        "parameters",
        "plan_digest",
        "query_digest",
        "registry_digest",
        "semantic_versions",
        "sql",
        "target_platform",
    )

    def __init__(self, *_: object, **__: object) -> None:
        raise TypeError("CompiledQuery artifacts are compiler-issued only")

    @classmethod
    def _issue(
        cls,
        *,
        sql: str,
        parameters: tuple[Any, ...],
        approved_products: tuple[str, ...],
        plan_digest: str,
        caller_digest: str,
        authorization_digest: str,
        authorization_outcome: str,
        registry_digest: str,
        lineage: object,
        field_evidence: dict[str, str],
        semantic_versions: dict[str, str],
    ) -> CompiledQuery:
        query = object.__new__(cls)
        object.__setattr__(query, "sql", sql)
        object.__setattr__(query, "parameters", parameters)
        object.__setattr__(query, "approved_products", approved_products)
        object.__setattr__(query, "target_platform", "DuckDB")
        object.__setattr__(query, "plan_digest", plan_digest)
        object.__setattr__(query, "caller_digest", caller_digest)
        object.__setattr__(query, "authorization_digest", authorization_digest)
        object.__setattr__(query, "authorization_outcome", authorization_outcome)
        object.__setattr__(query, "registry_digest", registry_digest)
        object.__setattr__(query, "parameter_digest", digest(parameters))
        object.__setattr__(query, "query_digest", digest({"sql": sql, "parameters": parameters}))
        object.__setattr__(query, "lineage", lineage)
        object.__setattr__(query, "field_evidence", dict(sorted(field_evidence.items())))
        object.__setattr__(query, "semantic_versions", dict(sorted(semantic_versions.items())))
        object.__setattr__(query, "_issuer", _QUERY_ISSUER)
        return query

    def _is_issued(self) -> bool:
        return self._issuer is _QUERY_ISSUER
