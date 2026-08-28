"""Fail-closed RBAC, ABAC, and projection-derived PII controls."""

from __future__ import annotations

from semantic_layer.control import digest, has_valid_signature, registry_digest, signature
from semantic_layer.models import CallerContext, SemanticQueryPlan
from semantic_layer.registry import SemanticRegistry

_COUNTRY_CONCEPT = "insurance:Country"
_ROLE_PRODUCTS = {
    "ClaimsAnalystFR": {"Customer360", "PolicyMaster", "ClaimsAnalytics"},
    "ClaimsManagerGroup": {"Customer360", "PolicyMaster", "ClaimsAnalytics"},
    "FinanceAnalyst": {"PremiumAnalytics"},
}
class AuthorizationDecision:
    """Opaque authorization capability issued only by :func:`authorize`."""

    __slots__ = (
        "_signature",
        "allowed",
        "caller_digest",
        "message",
        "plan_digest",
        "reason_code",
        "registry_digest",
    )

    def __init__(self, *_: object, **__: object) -> None:
        raise TypeError("AuthorizationDecision instances are authorization-issued only")

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("AuthorizationDecision capabilities are immutable")

    def _payload(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "reason_code": self.reason_code,
            "message": self.message,
            "plan_digest": self.plan_digest,
            "caller_digest": self.caller_digest,
            "registry_digest": self.registry_digest,
        }

    def _matches(self, plan: SemanticQueryPlan, caller: CallerContext, registry: SemanticRegistry) -> bool:
        return (
            self._verify_integrity()
            and self.allowed
            and self.plan_digest == digest(plan)
            and self.caller_digest == digest(caller)
            and self.registry_digest == registry_digest(registry)
        )

    def _is_issued(self) -> bool:
        return self._verify_integrity()

    def _verify_integrity(self) -> bool:
        return has_valid_signature("AuthorizationDecision", self._payload(), self._signature)


def _countries_in(plan: SemanticQueryPlan) -> set[str]:
    return {
        str(query_filter.value)
        for query_filter in plan.filters
        if query_filter.concept_id == _COUNTRY_CONCEPT and query_filter.operator == "="
    }


def _projected_pii_fields(plan: SemanticQueryPlan, registry: SemanticRegistry) -> set[str]:
    """Derive requested sensitive fields from semantic projection and reviewed mappings."""

    projected_concepts = set(plan.projected_dimensions)
    countries = _countries_in(plan)
    mappings = [
        mapping
        for mapping in registry.mappings.values()
        if not countries or mapping.location in countries
    ]
    return {
        field_name
        for mapping in mappings
        for field_name, field in mapping.fields.items()
        if field.pii and field.concept in projected_concepts
    }


def authorize(
    plan: SemanticQueryPlan,
    caller: CallerContext,
    registry: SemanticRegistry,
) -> AuthorizationDecision:
    """Issue an authorization capability for exactly one plan/caller/asset context."""

    if type(plan) is not SemanticQueryPlan or type(caller) is not CallerContext:
        raise TypeError("authorization requires validated plan and authenticated caller contexts")
    if type(registry) is not SemanticRegistry:
        raise TypeError("authorization requires the repository-issued semantic registry")

    def issue(*, allowed: bool, reason_code: str, message: str) -> AuthorizationDecision:
        decision = object.__new__(AuthorizationDecision)
        payload = {
            "allowed": allowed,
            "reason_code": reason_code,
            "message": message,
            "plan_digest": digest(plan),
            "caller_digest": digest(caller),
            "registry_digest": registry_digest(registry),
        }
        for name, value in payload.items():
            object.__setattr__(decision, name, value)
        object.__setattr__(decision, "_signature", signature("AuthorizationDecision", decision._payload()))
        return decision

    allowed_products = _ROLE_PRODUCTS.get(caller.role)
    if allowed_products is None:
        return issue(
            allowed=False,
            reason_code="ROLE_DENIED",
            message=f"role {caller.role} has no semantic query permission",
        )
    if plan.caller.model_dump() != caller.model_dump():
        return issue(
            allowed=False,
            reason_code="CALLER_CONTEXT_MISMATCH",
            message="plan caller does not match the authenticated caller context",
        )
    if not set(plan.selected_products).issubset(allowed_products):
        return issue(
            allowed=False,
            reason_code="PRODUCT_DENIED",
            message="role cannot access one or more selected data products",
        )
    countries = _countries_in(plan)
    if caller.country is not None and countries != {caller.country}:
        return issue(
            allowed=False,
            reason_code="COUNTRY_SCOPE_DENIED",
            message="plan country scope does not match the authenticated caller",
        )
    if caller.role == "ClaimsAnalystFR" and countries != {"FR"}:
        return issue(
            allowed=False,
            reason_code="COUNTRY_SCOPE_DENIED",
            message="ClaimsAnalystFR is limited to French records",
        )
    pii_fields = _projected_pii_fields(plan, registry)
    if caller.role == "FinanceAnalyst" and pii_fields:
        return issue(
            allowed=False,
            reason_code="PII_FIELD_DENIED",
            message=f"FinanceAnalyst cannot retrieve derived PII fields: {sorted(pii_fields)}",
        )
    return issue(
        allowed=True,
        reason_code="ALLOWED",
        message="governed access granted",
    )
