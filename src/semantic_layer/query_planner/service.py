"""Recognize supported question patterns and emit logical, SQL-free plans."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from semantic_layer.models import (
    CallerContext,
    Filter,
    MetricPredicate,
    SemanticQueryPlan,
    TimeContext,
)
from semantic_layer.resolver.service import normalize

if TYPE_CHECKING:
    from semantic_layer.registry.service import SemanticRegistry

_COUNTRIES = {
    "french": "FR",
    "france": "FR",
    "uk": "GB",
    "united kingdom": "GB",
    "british": "GB",
    "german": "DE",
    "germany": "DE",
}
_NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}


def _country_for(question: str, registry: SemanticRegistry) -> str | None:
    country_id = registry.concept_id_named("Country")
    allowed_values = set(registry.concepts[country_id].allowed_values)
    for term, country in _COUNTRIES.items():
        if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", question):
            if country not in allowed_values:
                raise ValueError(f"country value is not governed by {country_id}: {country}")
            return country
    return None


def _money_threshold(question: str) -> int | None:
    match = re.search(
        r"(?:above|over|greater than)\s+(?:eur\s*)?([\d,]+)(?:\s*eur)?", question
    )
    return int(match.group(1).replace(",", "")) if match else None


def _claim_count_threshold(question: str) -> int | None:
    match = re.search(
        r"(?:at least|more than|over)\s+(\d+|[a-z]+)\s+qualifying claims", question
    )
    if not match:
        return None
    token = match.group(1)
    return int(token) if token.isdecimal() else _NUMBER_WORDS.get(token)


def _caller(role: str, country: str | None) -> CallerContext:
    role_country = "FR" if role == "ClaimsAnalystFR" else None
    return CallerContext(role=role, country=country or role_country)


def _time_context(question: str) -> TimeContext | None:
    if "last 12 months" in question:
        return TimeContext(window="last_12_months", months=12)
    if "current year" in question or "this year" in question:
        return TimeContext(window="current_year")
    return None


def _requires_mapped_product(question: str, registry: SemanticRegistry) -> bool:
    return any(
        re.search(rf"(?<!\w){re.escape(term)}(?!\w)", question)
        for term in registry.local_product_terms()
    )


def build_plan(question: str, role: str, registry: SemanticRegistry) -> SemanticQueryPlan:
    """Build an asset-derived plan for supported claims and active-policy questions.

    The grammar recognizes documented intent, while all canonical identifiers,
    relationships, metric sources, and product selections come from the registry.
    It deliberately never creates executable SQL.
    """

    normalized_question = normalize(question)
    resolution = registry.resolve(question)
    customer_id = registry.concept_id_named("Customer")
    policy_id = registry.concept_id_named("Policy")
    claim_id = registry.concept_id_named("Claim")
    country_id = registry.concept_id_named("Country")
    motor_id = registry.concept_id_named("Motor Insurance")
    country = _country_for(normalized_question, registry)
    filters: list[Filter] = []
    if country:
        filters.append(Filter(concept_id=country_id, operator="=", value=country))
    if motor_id in resolution.concept_ids:
        filters.append(Filter(concept_id=registry.concept_id_named("Insurance Product"), operator="=", value=motor_id))
    elif _requires_mapped_product(normalized_question, registry):
        raise ValueError(f"unresolved governed product: {motor_id}")

    claim_threshold = _claim_count_threshold(normalized_question)
    incurred_threshold = _money_threshold(normalized_question) if "incurred loss" in normalized_question else None
    relationships = [registry.relationship_path(customer_id, policy_id)]
    metric_predicates: list[MetricPredicate] = []
    metric_ids: list[str] = []
    if claim_threshold is not None or incurred_threshold is not None:
        relationships.append(registry.relationship_path(policy_id, claim_id))
        if claim_threshold is not None:
            claim_count_id = registry.metric_id_named("ClaimCount")
            operator = ">" if "more than" in normalized_question or "over" in normalized_question else ">="
            metric_predicates.append(
                MetricPredicate(metric_id=claim_count_id, operator=operator, value=claim_threshold)
            )
            metric_ids.append(claim_count_id)
        if incurred_threshold is not None:
            total_loss_id = registry.metric_id_named("TotalIncurredLoss")
            metric_predicates.append(
                MetricPredicate(metric_id=total_loss_id, operator=">", value=incurred_threshold)
            )
            metric_ids.append(total_loss_id)
    elif "active polic" in normalized_question:
        active_policy_count_id = registry.metric_id_named("ActivePolicyCount")
        metric_predicates.append(
            MetricPredicate(metric_id=active_policy_count_id, operator=">", value=0)
        )
        metric_ids.append(active_policy_count_id)
    elif "claims ratio" in normalized_question:
        relationships.append(registry.relationship_path(policy_id, claim_id))
        claims_ratio_id = registry.metric_id_named("ClaimsRatio")
        metric_predicates.append(MetricPredicate(metric_id=claims_ratio_id, operator=">", value=0))
        metric_ids.append(claims_ratio_id)
    else:
        raise ValueError("unsupported question pattern; no governed metric could be resolved")

    return SemanticQueryPlan(
        root_entity=customer_id,
        projected_dimensions=[customer_id, country_id],
        filters=filters,
        relationships=relationships,
        metric_predicates=metric_predicates,
        time_context=_time_context(normalized_question),
        selected_products=registry.products_for_plan([customer_id, policy_id], metric_ids),
        caller=_caller(role, country),
    )
