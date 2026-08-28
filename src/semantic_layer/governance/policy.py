"""Fail-closed RBAC, ABAC, and projection-derived PII controls."""

from __future__ import annotations

from semantic_layer.control import digest, registry_digest
from semantic_layer.models import CallerContext, SemanticQueryPlan
from semantic_layer.registry import SemanticRegistry

_COUNTRY_CONCEPT = "insurance:Country"
_ROLE_PRODUCTS = {
    "ClaimsAnalystFR": {"Customer360", "PolicyMaster", "ClaimsAnalytics"},
    "ClaimsManagerGroup": {"Customer360", "PolicyMaster", "ClaimsAnalytics"},
    "FinanceAnalyst": {"PremiumAnalytics"},
}
_DECISION_ISSUER = object()


class AuthorizationDecision:
    """Opaque authorization capability issued only by :func:`authorize`."""

    __slots__ = (
        "_issuer",
        "allowed",
        "caller_digest",
        "message",
        "plan_digest",
        "reason_code",
        "registry_digest",
    )

    def __init__(self, *_: object, **__: object) -> None:
        raise TypeError("AuthorizationDecision instances are authorization-issued only")

    @classmethod
    def _issue(
        cls,
        *,
        allowed: bool,
        reason_code: str,
        message: str,
        plan_digest: str,
        caller_digest: str,
        registry_fingerprint: str,
    ) -> AuthorizationDecision:
        decision = object.__new__(cls)
        object.__setattr__(decision, "allowed", allowed)
        object.__setattr__(decision, "reason_code", reason_code)
        object.__setattr__(decision, "message", message)
        object.__setattr__(decision, "plan_digest", plan_digest)
        object.__setattr__(decision, "caller_digest", caller_digest)
        object.__setattr__(decision, "registry_digest", registry_fingerprint)
        object.__setattr__(decision, "_issuer", _DECISION_ISSUER)
        return decision

    def _matches(self, plan: SemanticQueryPlan, caller: CallerContext, registry: SemanticRegistry) -> bool:
        return (
            self._issuer is _DECISION_ISSUER
            and self.allowed
            and self.plan_digest == digest(plan)
            and self.caller_digest == digest(caller)
            and self.registry_digest == registry_digest(registry)
        )

    def _is_issued(self) -> bool:
        return self._issuer is _DECISION_ISSUER


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


def _issue(
    *,
    allowed: bool,
    reason_code: str,
    message: str,
    plan: SemanticQueryPlan,
    caller: CallerContext,
    registry: SemanticRegistry,
) -> AuthorizationDecision:
    return AuthorizationDecision._issue(
        allowed=allowed,
        reason_code=reason_code,
        message=message,
        plan_digest=digest(plan),
        caller_digest=digest(caller),
        registry_fingerprint=registry_digest(registry),
    )


def authorize(
    plan: SemanticQueryPlan,
    caller: CallerContext,
    registry: SemanticRegistry,
) -> AuthorizationDecision:
    """Issue an authorization capability for exactly one plan/caller/asset context."""

    if not isinstance(plan, SemanticQueryPlan) or not isinstance(caller, CallerContext):
        raise TypeError("authorization requires validated plan and authenticated caller contexts")
    allowed_products = _ROLE_PRODUCTS.get(caller.role)
    if allowed_products is None:
        return _issue(
            allowed=False,
            reason_code="ROLE_DENIED",
            message=f"role {caller.role} has no semantic query permission",
            plan=plan,
            caller=caller,
            registry=registry,
        )
    if plan.caller.model_dump() != caller.model_dump():
        return _issue(
            allowed=False,
            reason_code="CALLER_CONTEXT_MISMATCH",
            message="plan caller does not match the authenticated caller context",
            plan=plan,
            caller=caller,
            registry=registry,
        )
    if not set(plan.selected_products).issubset(allowed_products):
        return _issue(
            allowed=False,
            reason_code="PRODUCT_DENIED",
            message="role cannot access one or more selected data products",
            plan=plan,
            caller=caller,
            registry=registry,
        )
    countries = _countries_in(plan)
    if caller.country is not None and countries != {caller.country}:
        return _issue(
            allowed=False,
            reason_code="COUNTRY_SCOPE_DENIED",
            message="plan country scope does not match the authenticated caller",
            plan=plan,
            caller=caller,
            registry=registry,
        )
    if caller.role == "ClaimsAnalystFR" and countries != {"FR"}:
        return _issue(
            allowed=False,
            reason_code="COUNTRY_SCOPE_DENIED",
            message="ClaimsAnalystFR is limited to French records",
            plan=plan,
            caller=caller,
            registry=registry,
        )
    pii_fields = _projected_pii_fields(plan, registry)
    if caller.role == "FinanceAnalyst" and pii_fields:
        return _issue(
            allowed=False,
            reason_code="PII_FIELD_DENIED",
            message=f"FinanceAnalyst cannot retrieve derived PII fields: {sorted(pii_fields)}",
            plan=plan,
            caller=caller,
            registry=registry,
        )
    return _issue(
        allowed=True,
        reason_code="ALLOWED",
        message="governed access granted",
        plan=plan,
        caller=caller,
        registry=registry,
    )
