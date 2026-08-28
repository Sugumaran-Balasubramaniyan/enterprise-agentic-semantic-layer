"""Trusted DuckDB compiler for the supported governed claims investigation."""

from __future__ import annotations

from datetime import date

from semantic_layer.compiler.base import CompiledQuery
from semantic_layer.models import SemanticQueryPlan
from semantic_layer.registry import SemanticRegistry

_AS_OF_DATE = date(2026, 8, 28)
_PRIMARY_PRODUCTS = ("Customer360", "PolicyMaster", "ClaimsAnalytics")
_COUNTRY_CONCEPT = "insurance:Country"
_PRODUCT_CONCEPT = "insurance:InsuranceProduct"
_CLAIM_COUNT = "insurance:ClaimCount"
_TOTAL_LOSS = "insurance:TotalIncurredLoss"


class DuckDBCompiler:
    """Compile only registry-approved claims plans into a fixed SQL template."""

    def __init__(self, registry: SemanticRegistry) -> None:
        self.registry = registry

    @staticmethod
    def _filter_value(plan: SemanticQueryPlan, concept_id: str) -> str:
        matches = [
            query_filter.value
            for query_filter in plan.filters
            if query_filter.concept_id == concept_id and query_filter.operator == "="
        ]
        if len(matches) != 1 or not isinstance(matches[0], str):
            raise ValueError(f"plan requires exactly one governed {concept_id} equality filter")
        return matches[0]

    def _validate(self, plan: SemanticQueryPlan) -> tuple[str, str, int | float, int | float]:
        if not isinstance(plan, SemanticQueryPlan):
            raise TypeError("compiler accepts validated SemanticQueryPlan instances only")
        if plan.target_platform != "DuckDB":
            raise ValueError("DuckDB compiler cannot compile a non-DuckDB plan")
        if plan.root_entity != "insurance:Customer":
            raise ValueError("unsupported root entity for trusted claims template")
        if tuple(plan.selected_products) != _PRIMARY_PRODUCTS:
            raise ValueError("plan must select the approved certified claims products")
        if any(product not in self.registry.products for product in plan.selected_products):
            raise ValueError("plan names an unapproved product")
        if any(
            self.registry.products[product].certification.status != "CERTIFIED"
            for product in plan.selected_products
        ):
            raise ValueError("plan selects a product that is not certified")
        if plan.time_context is None or plan.time_context.window != "last_12_months":
            raise ValueError("trusted claims template requires a last_12_months context")
        required_edges = {
            ("insurance:Customer", "insurance:Policy"),
            ("insurance:Policy", "insurance:Claim"),
        }
        if {(edge.source, edge.target) for edge in plan.relationships} != required_edges:
            raise ValueError("plan relationships do not match the approved claims join path")
        predicates = {predicate.metric_id: predicate for predicate in plan.metric_predicates}
        if set(predicates) != {_CLAIM_COUNT, _TOTAL_LOSS}:
            raise ValueError("plan metrics do not match the trusted claims template")
        if predicates[_CLAIM_COUNT].operator != ">=" or predicates[_TOTAL_LOSS].operator != ">":
            raise ValueError("plan metric predicate operators are not governed")
        country = self._filter_value(plan, _COUNTRY_CONCEPT)
        product = self._filter_value(plan, _PRODUCT_CONCEPT)
        if country != plan.caller.country:
            raise ValueError("plan country filter must match caller's governed scope")
        mappings = [mapping for mapping in self.registry.mappings.values() if mapping.location == country]
        if len(mappings) != 1:
            raise ValueError("no unique approved mapping exists for plan country")
        mapping = mappings[0]
        if not set(_PRIMARY_PRODUCTS).issubset(mapping.data_products):
            raise ValueError("country mapping does not approve all selected data products")
        required_fields = {"customer_id", "policy_id", "claim_id", "country", "product", "status", "claim_date"}
        if not required_fields.issubset(mapping.fields):
            raise ValueError("country mapping omits a field required by the trusted template")
        if product not in set(mapping.normalization.get("products", {}).values()):
            raise ValueError("plan product has no approved local mapping")
        return country, product, predicates[_CLAIM_COUNT].value, predicates[_TOTAL_LOSS].value

    def compile(self, plan: SemanticQueryPlan) -> CompiledQuery:
        """Emit the only executable local query supported by this compiler."""

        country, product, claim_count, total_loss = self._validate(plan)
        start_date = _AS_OF_DATE.replace(year=_AS_OF_DATE.year - 1)
        statuses = self.registry.rules["insurance:QualifyingClaim"].include_statuses
        if not statuses:
            raise ValueError("QualifyingClaim rule must specify governed included statuses")
        status_parameters = tuple(statuses)
        status_placeholders = ", ".join("?" for _ in status_parameters)
        sql = f"""
SELECT
    customer.customer_id,
    customer.country,
    COUNT(DISTINCT claim.claim_id) AS claim_count,
    SUM(claim.incurred_loss_eur) AS total_incurred_loss_eur
FROM customers AS customer
JOIN policies AS policy
    ON customer.customer_id = policy.customer_id
JOIN claims AS claim
    ON policy.policy_id = claim.policy_id
WHERE claim.status IN ({status_placeholders})
    AND claim.claim_date >= CAST(? AS DATE)
    AND claim.claim_date <= CAST(? AS DATE)
    AND customer.country = ?
    AND policy.country = ?
    AND claim.country = ?
    AND policy.product = ?
    AND claim.product = ?
GROUP BY customer.customer_id, customer.country
HAVING COUNT(DISTINCT claim.claim_id) >= ?
    AND SUM(claim.incurred_loss_eur) > ?
ORDER BY customer.customer_id
""".strip()
        parameters = (
            *status_parameters,
            start_date.isoformat(),
            _AS_OF_DATE.isoformat(),
            country,
            country,
            country,
            product,
            product,
            claim_count,
            total_loss,
        )
        return CompiledQuery(
            sql=sql,
            parameters=parameters,
            approved_products=_PRIMARY_PRODUCTS,
        )
