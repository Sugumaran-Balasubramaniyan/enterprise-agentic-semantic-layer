"""Fail-closed RBAC and ABAC checks for logical semantic plans."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from semantic_layer.models import CallerContext, SemanticQueryPlan

_COUNTRY_CONCEPT = "insurance:Country"
_PII_FIELDS = {"customer_id", "customer_name", "email"}
_ROLE_PRODUCTS = {
    "ClaimsAnalystFR": {"Customer360", "PolicyMaster", "ClaimsAnalytics"},
    "ClaimsManagerGroup": {"Customer360", "PolicyMaster", "ClaimsAnalytics"},
    "FinanceAnalyst": {"PremiumAnalytics"},
}


@dataclass(frozen=True)
class AuthorizationDecision:
    """Auditable authorization result; a denial is explicit and non-executable."""

    allowed: bool
    reason_code: str
    message: str


def _countries_in(plan: SemanticQueryPlan) -> set[str]:
    return {
        str(query_filter.value)
        for query_filter in plan.filters
        if query_filter.concept_id == _COUNTRY_CONCEPT and query_filter.operator == "="
    }


def _deny(reason_code: str, message: str) -> AuthorizationDecision:
    return AuthorizationDecision(allowed=False, reason_code=reason_code, message=message)


def authorize(
    plan: SemanticQueryPlan,
    caller: CallerContext,
    requested_fields: Iterable[str] = (),
) -> AuthorizationDecision:
    """Authorize a typed plan using role, country, product, and PII attributes.

    Authorization deliberately accepts a :class:`SemanticQueryPlan`, never SQL or
    a physical table name.  Unknown roles, unsupported products, and absent
    country scope for the French analyst are denied.
    """

    allowed_products = _ROLE_PRODUCTS.get(caller.role)
    if allowed_products is None:
        return _deny("ROLE_DENIED", f"role {caller.role} has no semantic query permission")
    if plan.caller.role != caller.role:
        return _deny("CALLER_CONTEXT_MISMATCH", "plan caller does not match authenticated caller")
    if not set(plan.selected_products).issubset(allowed_products):
        return _deny("PRODUCT_DENIED", "role cannot access one or more selected data products")

    countries = _countries_in(plan)
    if caller.role == "ClaimsAnalystFR" and countries != {"FR"}:
        return _deny("COUNTRY_SCOPE_DENIED", "ClaimsAnalystFR is limited to French records")
    if caller.role == "FinanceAnalyst" and set(requested_fields) & _PII_FIELDS:
        return _deny("PII_FIELD_DENIED", "FinanceAnalyst cannot retrieve customer PII")

    return AuthorizationDecision(allowed=True, reason_code="ALLOWED", message="governed access granted")
