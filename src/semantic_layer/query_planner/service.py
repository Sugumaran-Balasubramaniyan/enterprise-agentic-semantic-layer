"""Recognize supported question patterns and emit logical, SQL-free plans."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from semantic_layer.models import (
    CallerContext,
    Filter,
    MetricPredicate,
    RelationshipPath,
    Resolution,
    SemanticQueryPlan,
    TimeContext,
    contains_sql_shape,
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
_UNSUPPORTED_COUNTRIES = {
    "austrian", "austria", "belgian", "belgium", "canadian", "canada",
    "dutch", "italian", "italy", "portuguese", "portugal", "spanish", "spain",
    "swiss", "switzerland", "american", "united states", "us",
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

_NUMBER_TOKEN = r"(?:\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten|"
_NUMBER_TOKEN += r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)"
_COUNTRY_TOKEN = r"(?:french|france|fr|uk|united kingdom|british|german|germany|de|gb)"
_PRODUCT_TOKEN = r"(?:motor insurance|motor cover|car insurance|mtr|motorinsurance)"
_SUBJECT_TOKEN = r"(?:customers|policyholders|insured customers)"
_CLAIMS_QUESTION = re.compile(
    rf"^find {_COUNTRY_TOKEN} {_PRODUCT_TOKEN} {_SUBJECT_TOKEN} with "
    rf"(?:at least {_NUMBER_TOKEN}|more than {_NUMBER_TOKEN}|over {_NUMBER_TOKEN}) "
    rf"qualifying claims in the last 12 months and total incurred loss above eur [\d,]+"
    rf"(?: for (?:claim loss|inclusion|policy|loss|claims state|contract) review)?\.$"
)
_ACTIVE_QUESTION = re.compile(
    rf"^(?:how many|find) {_COUNTRY_TOKEN} {_PRODUCT_TOKEN} {_SUBJECT_TOKEN} "
    r"(?:have|with) active policies (?:this year|in the current year)[.?]$"
)
_RATIO_QUESTION = re.compile(
    rf"^show the claims ratio for {_COUNTRY_TOKEN} {_PRODUCT_TOKEN} {_SUBJECT_TOKEN} "
    r"in the current year(?: for finance planning)?\.$"
)


@dataclass(frozen=True)
class QueryDiscovery:
    """Non-executable semantic discovery used to authorize before final plan construction."""

    question: str
    role: str
    caller: CallerContext
    resolution: Resolution
    root_entity: str
    projected_dimensions: tuple[str, ...]
    filters: tuple[Filter, ...]
    relationships: tuple[RelationshipPath, ...]
    metric_predicates: tuple[MetricPredicate, ...]
    time_context: TimeContext | None
    selected_products: tuple[str, ...]


def _country_for(question: str, registry: SemanticRegistry) -> str | None:
    country_id = registry.concept_id_named("Country")
    allowed_values = set(registry.concepts[country_id].allowed_values)
    for term, country in _COUNTRIES.items():
        if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", question):
            if country not in allowed_values:
                raise ValueError(f"country value is not governed by {country_id}: {country}")
            return country
    code = re.search(r"(?<!\w)(fr|gb|de)(?!\w)", question)
    if code:
        country = code.group(1).upper()
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


def _validate_supported_constraints(question: str, registry: SemanticRegistry) -> None:
    """Reject constraint language that this bounded grammar cannot represent."""

    country_terms = [
        country
        for country in _COUNTRIES
        if re.search(rf"(?<!\w){re.escape(country)}(?!\w)", question)
    ]
    countries = {_COUNTRIES[term] for term in country_terms}
    code_terms = re.findall(r"(?<!\w)(?:fr|gb|de)(?!\w)", question)
    countries.update(code.upper() for code in code_terms)
    if len(countries) > 1:
        raise ValueError("unsupported country scope: multiple countries are not representable")
    for term in _UNSUPPORTED_COUNTRIES:
        if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", question):
            raise ValueError(f"unsupported country scope: {term}")

    if re.search(r"\b(?:claim|claims|policy|policies)\s+status\b|\bwith\s+status\b", question):
        raise ValueError("unsupported constraint: status filters are not representable")
    if re.search(r"\bfor\s+customer(?:\s+(?:id|number))?\b", question):
        raise ValueError("unsupported constraint: customer restrictions are not representable")

    if re.search(
        r"\bexcluding\s+(?:pending claims|customer\s+[A-Za-z0-9_-]+)\b|"
        r"\bfor\s+customers\s+named\s+[A-Za-z][A-Za-z -]*|"
        r"\bclaim dates?\s+(?:before|after|on|between)\b",
        question,
    ):
        raise ValueError("unsupported constraint: residual exclusions and date filters are not representable")

    if not (_CLAIMS_QUESTION.fullmatch(question) or _ACTIVE_QUESTION.fullmatch(question) or _RATIO_QUESTION.fullmatch(question)):
        raise ValueError("unsupported residual constraint language")

    has_claim_count = _claim_count_threshold(question) is not None
    has_loss = "incurred loss" in question and _money_threshold(question) is not None
    has_active = "active polic" in question
    has_ratio = "claims ratio" in question
    intent_count = sum((has_claim_count or has_loss, has_active, has_ratio))
    if intent_count != 1:
        raise ValueError("unsupported mixed clauses: question combines or omits governed intents")
    if has_claim_count != has_loss and not has_active and not has_ratio:
        raise ValueError("unsupported constraint: claims queries require count and loss thresholds")
    if has_claim_count or has_loss:
        if "last 12 months" not in question:
            raise ValueError("unsupported constraint: claims queries require last 12 months")
        if question.count(" and ") != 1:
            raise ValueError("unsupported mixed clauses: only one governed claims conjunction is supported")
    if re.search(r"\bor\b|\b(?:where|having|whose|with\s+email)\b", question):
        raise ValueError("unsupported residual constraint language")


def discover_question(question: str, role: str, registry: SemanticRegistry) -> QueryDiscovery:
    """Resolve governed intent without constructing a final execution plan.

    Discovery is sufficient for fail-closed authorization (role, country,
    projected concepts, and selected products) but cannot be compiled or
    executed. The final ``SemanticQueryPlan`` is constructed only after this
    discovery has been authorized.
    """

    if not isinstance(question, str) or not question.strip():
        raise ValueError("a non-empty business question is required")
    if contains_sql_shape(question, natural_language=True):
        raise ValueError("business question cannot contain SQL-shaped values")
    normalized_question = normalize(question)
    _validate_supported_constraints(normalized_question, registry)
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

    return QueryDiscovery(
        question=question,
        role=role,
        caller=_caller(role, country),
        resolution=resolution,
        root_entity=customer_id,
        projected_dimensions=(customer_id, country_id),
        filters=tuple(filters),
        relationships=tuple(relationships),
        metric_predicates=tuple(metric_predicates),
        time_context=_time_context(normalized_question),
        selected_products=tuple(registry.products_for_plan([customer_id, policy_id], metric_ids)),
    )


def build_plan(
    question: str,
    role: str,
    registry: SemanticRegistry,
    *,
    discovery: QueryDiscovery | None = None,
) -> SemanticQueryPlan:
    """Construct a final typed plan from fresh or previously authorized discovery."""

    discovery = discovery or discover_question(question, role, registry)
    if discovery.question != question or discovery.role != role:
        raise ValueError("discovery is not bound to the requested question and role")
    return SemanticQueryPlan(
        root_entity=discovery.root_entity,
        projected_dimensions=list(discovery.projected_dimensions),
        filters=list(discovery.filters),
        relationships=list(discovery.relationships),
        metric_predicates=list(discovery.metric_predicates),
        time_context=discovery.time_context,
        selected_products=list(discovery.selected_products),
        caller=discovery.caller,
    )
