"""Contract tests for deterministic, fail-closed grammar grounding."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from semantic_layer.reasoning.schema_linker import SchemaLinker
from semantic_layer.research.contracts import ReasonCode

GRAMMAR = yaml.safe_load(
    (Path(__file__).with_name("grounding_grammar.yaml")).read_text(encoding="utf-8")
)
ROOT = Path(__file__).parents[2]


def _assert_entities(result, fixture: dict) -> None:
    for field in (
        "component_codes",
        "alert_codes",
        "product_versions",
        "software_components",
        "support_packages",
        "note_numbers",
        "priorities",
    ):
        assert getattr(result, field) == fixture.get(field, [])


def test_grounding_grammar_is_versioned_and_closed() -> None:
    assert GRAMMAR["schema_version"] == "1.0"
    assert "and" in GRAMMAR["filler_tokens"]
    assert "an" in GRAMMAR["filler_tokens"]
    assert GRAMMAR["unsupported_intent_marker"] == ["explain", "recommend", "summarize"]


@pytest.mark.parametrize("fixture", GRAMMAR["fixtures"][:7], ids=lambda item: item["id"])
def test_grounding_accepts_declared_templates_and_preserves_canonical_entities(fixture: dict) -> None:
    result = SchemaLinker().ground_or_abstain(fixture["query"])

    assert result.raw_query == fixture["query"]
    assert result.normalized_request == " ".join(SchemaLinker._tokens(fixture["query"]))
    assert result.intent == fixture["intent"]
    assert result.failure_class == fixture["failure_class"]
    _assert_entities(result, fixture)


def test_numeric_support_package_is_valid_but_named_unknown_is_not() -> None:
    valid = SchemaLinker().ground_or_abstain(
        "Find notes for alert TIME_OUT in component MM-PUR-PO at SP99."
    )
    invalid = SchemaLinker().ground_or_abstain(
        "Find notes for alert TIME_OUT in component MM-PUR-PO at SP_FUTURE."
    )

    assert valid.failure_class == "NONE"
    assert valid.intent == "VERSION_FILTERED_SEARCH"
    assert valid.support_packages == [99]
    assert invalid.failure_class == "UNKNOWN_ENTITY"


def test_priority_fixtures_cover_two_token_casefolding_and_invalid_values() -> None:
    fixtures = {fixture["id"]: fixture for fixture in GRAMMAR["fixtures"]}

    valid = SchemaLinker().ground_or_abstain(fixtures["alert_resolution_very_high_priority"]["query"])
    assert valid.failure_class == ReasonCode.NONE
    assert valid.intent == "ALERT_RESOLUTION"
    assert valid.priorities == ["Very High"]

    invalid = SchemaLinker().ground_or_abstain(fixtures["invalid_very_low_priority"]["query"])
    assert invalid.failure_class == ReasonCode.UNKNOWN_ENTITY
    assert invalid.intent == "UNSUPPORTED"
    assert invalid.priorities == []


@pytest.mark.parametrize(
    ("query", "failure_class"),
    [
        ("Find notes TIME_OUT.", "UNKNOWN_TOKEN"),
        ("Find notes for alert TIME_OUT 3012445.", "UNSUPPORTED_INTENT"),
        ("Find notes for alert TIME_OUT on S/4HANA 2023 3012445.", "UNSUPPORTED_INTENT"),
        (
            "Find notes for alert TIME_OUT priority HIGH in component MM-PUR-PO.",
            "UNSUPPORTED_INTENT",
        ),
    ],
)
def test_grounding_rejects_uncued_entities_and_extra_slots(
    query: str, failure_class: str
) -> None:
    result = SchemaLinker().ground_or_abstain(query)

    assert result.intent == "UNSUPPORTED"
    assert result.failure_class == failure_class
    assert isinstance(result.failure_class, ReasonCode)


@pytest.mark.parametrize(
    "fixture",
    [
        item
        for item in GRAMMAR["fixtures"] + GRAMMAR["v2_fixtures"]
        if item["failure_class"] != "NONE"
    ],
    ids=lambda item: item["id"],
)
def test_grounding_rejects_unknown_ambiguous_and_unsupported_inputs_before_planning(
    fixture: dict,
) -> None:
    result = SchemaLinker().ground_or_abstain(fixture["query"])

    assert result.raw_query == fixture["query"]
    assert result.intent == "UNSUPPORTED"
    assert result.failure_class == fixture["failure_class"]
    if "component_codes" in fixture:
        assert result.component_codes == fixture["component_codes"]
    if "alert_codes" in fixture:
        assert result.alert_codes == fixture["alert_codes"]

    # Grounding owns no planner/compiler hook: rejected input is data only and
    # cannot produce a planning opportunity or exception.
    assert not hasattr(result, "plan")
    assert not hasattr(result, "sparql")


@pytest.mark.parametrize("fixture", GRAMMAR["v2_fixtures"][:8], ids=lambda item: item["id"])
def test_v2_rejections_expose_exact_failure_class(fixture: dict) -> None:
    result = SchemaLinker().ground_or_abstain(fixture["query"])
    assert result.failure_class == fixture["failure_class"]
    assert result.intent == "UNSUPPORTED"


@pytest.mark.parametrize(
    "fixture", [item for item in GRAMMAR["v2_fixtures"] if item["failure_class"] == "NONE"],
    ids=lambda item: item["id"],
)
def test_v2_strict_empty_cases_are_valid_grounding(fixture: dict) -> None:
    result = SchemaLinker().ground_or_abstain(fixture["query"])
    assert result.failure_class == "NONE"
    assert result.intent in {"ALERT_RESOLUTION", "VERSION_FILTERED_SEARCH"}
    _assert_entities(result, fixture)


@pytest.mark.parametrize(
    "dataset_name",
    ["benchmark_dataset_v1.yaml", "benchmark_dataset_v2.yaml"],
)
def test_declared_corpus_preflight_accepts_valid_rows_and_preserves_ood_reasons(
    dataset_name: str,
) -> None:
    """Every declared positive/strict-empty row must reach a grounded intent."""

    corpus = yaml.safe_load(
        (ROOT / "tests/research" / dataset_name).read_text(encoding="utf-8")
    )
    linker = SchemaLinker()

    for record in corpus["records"]:
        grounded = linker.ground_or_abstain(record["question"])
        expected_status = record["expected_status"]
        if expected_status in {"SUCCESS", "EMPTY_RESULT"}:
            assert grounded.failure_class == ReasonCode.NONE, record["id"]
            assert grounded.intent != "UNSUPPORTED", record["id"]
        else:
            assert grounded.intent == "UNSUPPORTED", record["id"]
            assert grounded.failure_class.value == record["reflection_reason"], record["id"]


@pytest.mark.parametrize(
    "query",
    [
        "Find notes in component MM-PUR-PO at SP05 for alert TIME_OUT.",
        "Find notes for alert TIME_OUT in component MM-PUR-PO and component FI.",
    ],
)
def test_closed_parser_rejects_malformed_ordering_and_extra_entity_slots(query: str) -> None:
    result = SchemaLinker().ground_or_abstain(query)

    assert result.intent == "UNSUPPORTED"
    assert result.failure_class in {
        ReasonCode.UNSUPPORTED_INTENT,
        ReasonCode.AMBIGUOUS_INPUT,
    }
