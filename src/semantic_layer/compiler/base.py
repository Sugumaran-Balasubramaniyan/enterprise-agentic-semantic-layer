"""Signed immutable compiler capabilities; issuance remains module-private."""

from __future__ import annotations

from semantic_layer.control import _verify, digest


class CompiledQuery:
    """A signed, immutable query capability bound to one reviewed execution context."""

    __slots__ = (
        "_signature",
        "approved_products",
        "authorization_digest",
        "authorization_outcome",
        "caller_digest",
        "concepts",
        "field_evidence",
        "mapping_ids",
        "metric_ids",
        "parameter_digest",
        "parameters",
        "plan_digest",
        "query_digest",
        "question_digest",
        "registry_digest",
        "semantic_versions",
        "sql",
        "target_platform",
    )

    def __init__(self, *_: object, **__: object) -> None:
        raise TypeError("CompiledQuery artifacts are compiler-issued only")

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("CompiledQuery capabilities are immutable")

    def _payload(self) -> dict[str, object]:
        return {
            "sql": self.sql,
            "parameters": self.parameters,
            "approved_products": self.approved_products,
            "plan_digest": self.plan_digest,
            "question_digest": self.question_digest,
            "concepts": self.concepts,
            "caller_digest": self.caller_digest,
            "authorization_digest": self.authorization_digest,
            "authorization_outcome": self.authorization_outcome,
            "registry_digest": self.registry_digest,
            "mapping_ids": self.mapping_ids,
            "metric_ids": self.metric_ids,
            "field_evidence": self.field_evidence,
            "semantic_versions": self.semantic_versions,
        }

    def _verify_integrity(self) -> bool:
        return (
            self.parameter_digest == digest(self.parameters)
            and self.query_digest == digest({"sql": self.sql, "parameters": self.parameters})
            and _verify("CompiledQuery", self._payload(), self._signature)
        )
