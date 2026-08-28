"""Recognize supported question patterns and emit logical, SQL-free plans."""

from __future__ import annotations

import re

from semantic_layer.models import (
    CallerContext,
    Filter,
    MetricPredicate,
    RelationshipPath,
    SemanticQueryPlan,
    TimeContext,
)
from semantic_layer.resolver.service import normalize

_COUNTRIES = {
    "french": "FR",
    "france": "FR",
    "uk": "GB",
    "united kingdom": "GB",
    "british": "GB",
    "german": "DE",
    "germany": "DE",
}


def _country_for(question: str) -> str | None:
    for term, country in _COUNTRIES.items():
        if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", question):
            return country
    return None


def _money_threshold(question: str) -> int | None:
    match = re.search(
        r"(?:above|over|greater than)\s+(?:eur\s*)?([\d,]+)(?:\s*eur)?", question
    )
    return int(match.group(1).replace(",", "")) if match else None


def _claim_count_threshold(question: str) -> int | None:
    match = re.search(r"(?:at least|more than|over)\s+(\d+|three)\s+qualifying claims", question)
    if not match:
        return None
    return 3 if match.group(1) == "three" else int(match.group(1))


def _caller(role: str, country: str | None) -> CallerContext:
    role_country = "FR" if role == "ClaimsAnalystFR" else None
    return CallerContext(role=role, country=country or role_country)


def _certified(registry, product_ids: list[str]) -> list[str]:
    missing = [
        product_id
        for product_id in product_ids
        if product_id not in registry.products
        or registry.products[product_id].certification.status != "CERTIFIED"
    ]
    if missing:
        raise ValueError(f"plan requires unavailable certified products: {', '.join(missing)}")
    return product_ids


def build_plan(question: str, role: str, registry) -> SemanticQueryPlan:
    """Build a governed plan for supported claims and active-policy questions.

    This control-plane function deliberately produces no executable SQL. Physical
    query compilation is a later, mapping-governed responsibility.
    """

    normalized_question = normalize(question)
    country = _country_for(normalized_question)
    filters: list[Filter] = []
    if country:
        filters.append(Filter(concept_id="insurance:Country", operator="=", value=country))
    if "motor insurance" in normalized_question or "car insurance" in normalized_question or "auto insurance" in normalized_question:
        filters.append(
            Filter(
                concept_id="insurance:InsuranceProduct",
                operator="=",
                value="insurance:MotorInsurance",
            )
        )
    if "last 12 months" in normalized_question:
        time_context = TimeContext(window="last_12_months", months=12)
    elif "current year" in normalized_question or "this year" in normalized_question:
        time_context = TimeContext(window="current_year")
    else:
        time_context = None

    relationships = [
        RelationshipPath(
            source="insurance:Customer",
            predicate="insurance:ownsPolicy",
            target="insurance:Policy",
        )
    ]
    metric_predicates: list[MetricPredicate] = []
    selected_products = ["Customer360", "PolicyMaster"]

    claim_threshold = _claim_count_threshold(normalized_question)
    incurred_threshold = _money_threshold(normalized_question) if "incurred loss" in normalized_question else None
    if claim_threshold is not None or incurred_threshold is not None:
        relationships.append(
            RelationshipPath(
                source="insurance:Policy",
                predicate="insurance:submitsClaim",
                target="insurance:Claim",
            )
        )
        selected_products.append("ClaimsAnalytics")
        if claim_threshold is not None:
            operator = ">" if "more than" in normalized_question or "over" in normalized_question else ">="
            metric_predicates.append(
                MetricPredicate(
                    metric_id="insurance:ClaimCount", operator=operator, value=claim_threshold
                )
            )
        if incurred_threshold is not None:
            metric_predicates.append(
                MetricPredicate(
                    metric_id="insurance:TotalIncurredLoss", operator=">", value=incurred_threshold
                )
            )
    elif "active polic" in normalized_question:
        metric_predicates.append(
            MetricPredicate(metric_id="insurance:ActivePolicyCount", operator=">", value=0)
        )
    elif "claims ratio" in normalized_question:
        relationships.append(
            RelationshipPath(
                source="insurance:Policy",
                predicate="insurance:submitsClaim",
                target="insurance:Claim",
            )
        )
        selected_products.extend(["ClaimsAnalytics", "PremiumAnalytics"])
        metric_predicates.append(MetricPredicate(metric_id="insurance:ClaimsRatio", operator=">", value=0))
    else:
        raise ValueError("unsupported question pattern; no governed metric could be resolved")

    for predicate in metric_predicates:
        if predicate.metric_id not in registry.metrics:
            raise ValueError(f"unknown governed metric: {predicate.metric_id}")
    return SemanticQueryPlan(
        root_entity="insurance:Customer",
        projected_dimensions=["insurance:Customer", "insurance:Country"],
        filters=filters,
        relationships=relationships,
        metric_predicates=metric_predicates,
        time_context=time_context,
        selected_products=_certified(registry, selected_products),
        caller=_caller(role, country),
    )
