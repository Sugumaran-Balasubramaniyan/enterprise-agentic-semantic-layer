"""Local DuckDB compiler for one fully represented synthetic SAP ERP audit plan."""

from __future__ import annotations

from datetime import date
from types import MappingProxyType

from semantic_layer.compiler.base import CompiledQuery
from semantic_layer.control import _sign, digest, registry_digest
from semantic_layer.governance import AuthorizationDecision
from semantic_layer.lineage import LineageService
from semantic_layer.models import CallerContext, SemanticQueryPlan
from semantic_layer.query_planner import build_plan
from semantic_layer.registry import SemanticRegistry

_AS_OF_DATE = date(2026, 8, 28)
_PRIMARY_PRODUCTS = ("BusinessPartners", "SalesOrders", "ACDOCAFinancials")
_PRIMARY_DIMENSIONS = ("ciferp:BusinessPartner", "ciferp:CompanyCode")
_PRIMARY_EDGES = (
    ("ciferp:BusinessPartner", "ciferp:hasSalesOrder", "ciferp:SalesOrder"),
    ("ciferp:BusinessPartner", "ciferp:hasFinancialPosting", "ciferp:FinancialPosting"),
    ("ciferp:FinancialPosting", "ciferp:referencesSalesOrder", "ciferp:SalesOrder"),
)
_COUNTRY_CONCEPT = "ciferp:CompanyCode"
_PRODUCT_CONCEPT = "ciferp:Product"
_POSTING_COUNT = "ciferp:PostingCount"
_TOTAL_LOSS = "ciferp:TotalDebitLossEur"
_USED_FIELDS = (
    "partner_id",
    "sales_order_id",
    "journal_entry_id",
    "country",
    "product",
    "posting_status",
    "posting_date",
    "amount_in_company_currency_eur",
)
_LOCAL_FIELD_SOURCES = {
    "partner_id": ("business_partners.csv:partner_id", "sales_orders.csv:partner_id", "acdoca_financials.csv:partner_id"),
    "sales_order_id": ("sales_orders.csv:sales_order_id", "acdoca_financials.csv:sales_order_id"),
    "journal_entry_id": ("acdoca_financials.csv:journal_entry_id",),
    "country": ("business_partners.csv:country", "sales_orders.csv:country", "acdoca_financials.csv:country"),
    "product": ("sales_orders.csv:product", "acdoca_financials.csv:product"),
    "posting_status": ("acdoca_financials.csv:posting_status",),
    "posting_date": ("acdoca_financials.csv:posting_date",),
    "amount_in_company_currency_eur": ("acdoca_financials.csv:amount_in_company_currency_eur",),
}


class DuckDBCompiler:
    """Compile a capability only after exact plan and authorization validation."""

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

    def _validate(
        self, plan: SemanticQueryPlan
    ) -> tuple[str, str, int | float, int | float, str, dict[str, str], dict[str, str]]:
        if type(plan) is not SemanticQueryPlan:
            raise TypeError("compiler accepts validated SemanticQueryPlan instances only")
        if plan.target_platform != "DuckDB":
            raise ValueError("DuckDB compiler cannot compile a non-DuckDB plan")
        if plan.root_entity != "ciferp:BusinessPartner":
            raise ValueError("unsupported root entity for trusted SAP ERP audit template")
        if tuple(plan.projected_dimensions) != _PRIMARY_DIMENSIONS:
            raise ValueError("unsupported projected dimensions are not represented by trusted SQL")
        if tuple(plan.selected_products) != _PRIMARY_PRODUCTS:
            raise ValueError("plan must select the approved certified SAP ERP products")
        if len(plan.filters) != 2:
            raise ValueError("unsupported filters are not represented by trusted SQL")
        if any(product not in self.registry.products for product in plan.selected_products):
            raise ValueError("plan names an unapproved product")
        if any(
            self.registry.products[product].certification.status != "CERTIFIED"
            or self.registry.products[product].quality.status != "CERTIFIED"
            for product in plan.selected_products
        ):
            raise ValueError("plan selects a product that is not certified or has unsafe quality")
        if plan.time_context is None or plan.time_context.window != "last_12_months":
            raise ValueError("trusted SAP ERP audit template requires a last_12_months context")
        if (
            tuple((edge.source, edge.predicate, edge.target) for edge in plan.relationships)
            != _PRIMARY_EDGES
        ):
            raise ValueError("plan relationships do not exactly match the approved SAP ERP join path")
        expected_metrics = (_POSTING_COUNT, _TOTAL_LOSS)
        if tuple(predicate.metric_id for predicate in plan.metric_predicates) != expected_metrics:
            raise ValueError("plan metrics must exactly match the trusted SAP ERP audit template")
        predicates = {predicate.metric_id: predicate for predicate in plan.metric_predicates}
        if predicates[_POSTING_COUNT].operator not in {">=", ">"} or predicates[_TOTAL_LOSS].operator != ">":
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
        if not set(_USED_FIELDS).issubset(mapping.fields):
            raise ValueError("country mapping omits a field required by the trusted template")
        if product not in set(mapping.normalization.get("products", {}).values()):
            raise ValueError("plan product has no approved local mapping")
        field_evidence = {
            f"field:{field_name}": "local CSV columns: " + ", ".join(_LOCAL_FIELD_SOURCES[field_name])
            for field_name in _USED_FIELDS
        }
        versions = {
            f"product:{product_id}": self.registry.products[product_id].version
            for product_id in _PRIMARY_PRODUCTS
        }
        versions[f"mapping:{mapping.id}"] = mapping.version
        versions["rule:ciferp:QualifyingPosting"] = self.registry.rules[
            "ciferp:QualifyingPosting"
        ].version
        versions["policy:authorization"] = "1.0.0"
        return (
            country,
            product,
            predicates[_POSTING_COUNT].value,
            predicates[_TOTAL_LOSS].value,
            predicates[_POSTING_COUNT].operator,
            field_evidence,
            versions,
        )

    def compile(
        self,
        plan: SemanticQueryPlan,
        authorization: AuthorizationDecision,
        caller: CallerContext,
        question: str,
    ) -> CompiledQuery:
        """Emit a parameterized capability bound to plan, caller, policy, and assets."""

        if type(authorization) is not AuthorizationDecision:
            raise TypeError("authorization decision is required before compilation")
        if type(caller) is not CallerContext:
            raise TypeError("compiler requires a validated caller context")
        if not authorization._matches(plan, caller, self.registry):
            raise ValueError("authorization decision does not match plan, caller, or reviewed assets")
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question is required to bind compilation to the requested semantic intent")
        country, product, posting_count, total_loss, posting_count_operator, field_evidence, versions = self._validate(plan)
        expected_plan = build_plan(question, caller.role, self.registry)
        if digest(expected_plan) != digest(plan):
            raise ValueError("question does not resolve to the submitted semantic plan")
        start_date = _AS_OF_DATE.replace(year=_AS_OF_DATE.year - 1)
        statuses = self.registry.rules["ciferp:QualifyingPosting"].include_statuses
        if not statuses:
            raise ValueError("QualifyingPosting rule must specify governed included statuses")
        status_parameters = tuple(statuses)
        status_placeholders = ", ".join("?" for _ in status_parameters)
        sql = f"""
SELECT
    partner.partner_id,
    partner.country,
    COUNT(DISTINCT posting.journal_entry_id) AS posting_count,
    SUM(posting.amount_in_company_currency_eur) AS total_debit_loss_eur
FROM business_partners AS partner
JOIN sales_orders AS ord
    ON partner.partner_id = ord.partner_id
JOIN acdoca_financials AS posting
    ON ord.sales_order_id = posting.sales_order_id
WHERE posting.posting_status IN ({status_placeholders})
    AND posting.posting_date >= CAST(? AS DATE)
    AND posting.posting_date <= CAST(? AS DATE)
    AND partner.country = ?
    AND ord.country = ?
    AND posting.country = ?
    AND ord.product = ?
    AND posting.product = ?
GROUP BY partner.partner_id, partner.country
HAVING COUNT(DISTINCT posting.journal_entry_id) {posting_count_operator} ?
    AND SUM(posting.amount_in_company_currency_eur) > ?
ORDER BY partner.partner_id
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
            posting_count,
            total_loss,
        )
        lineage = LineageService(self.registry).for_plan(plan)
        versions.update(lineage.semantic_versions)
        concepts_seen: set[str] = set()

        def add_concept(concept_id: str) -> None:
            if concept_id in self.registry.concepts:
                concepts_seen.add(concept_id)

        add_concept(plan.root_entity)
        for concept_id in plan.projected_dimensions:
            add_concept(concept_id)
        for query_filter in plan.filters:
            add_concept(query_filter.concept_id)
            if isinstance(query_filter.value, str):
                add_concept(query_filter.value)
        for relationship in plan.relationships:
            add_concept(relationship.source)
            add_concept(relationship.target)
        for predicate in plan.metric_predicates:
            add_concept(predicate.metric_id)
            metric = self.registry.metrics.get(predicate.metric_id)
            if metric is not None:
                add_concept(metric.concept)
                if metric.filter_rule:
                    rule = self.registry.rules.get(metric.filter_rule)
                    if rule is not None:
                        add_concept(rule.applies_to)

        result = object.__new__(CompiledQuery)
        payload = {
            "sql": sql,
            "parameters": parameters,
            "target_platform": "DuckDB",
            "plan_digest": digest(plan),
            "caller_digest": digest(caller),
            "authorization_digest": digest(
                {
                    "plan": authorization.plan_digest,
                    "caller": authorization.caller_digest,
                    "registry": authorization.registry_digest,
                    "outcome": authorization.reason_code,
                }
            ),
            "authorization_outcome": authorization.reason_code,
            "registry_digest": registry_digest(self.registry),
            "question_digest": digest(question),
            "concepts": tuple(sorted(concepts_seen)),
            "query_digest": digest({"sql": sql, "parameters": parameters}),
            "parameter_digest": digest(parameters),
            "field_evidence": MappingProxyType(dict(sorted(field_evidence.items()))),
            "semantic_versions": MappingProxyType(dict(sorted(versions.items()))),
            "approved_products": tuple(plan.selected_products),
            "mapping_ids": tuple(lineage.mapping_ids),
            "metric_ids": tuple(predicate.metric_id for predicate in plan.metric_predicates),
        }
        for name, value in payload.items():
            object.__setattr__(result, name, value)
        object.__setattr__(result, "_signature", _sign("CompiledQuery", result._payload()))
        return result
