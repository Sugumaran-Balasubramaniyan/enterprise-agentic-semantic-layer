"""Run the primary governed claims investigation without an LLM or cloud account."""

from __future__ import annotations

import json

from semantic_layer.agents import ClaimsInvestigationAgent
from semantic_layer.models import CallerContext

PRIMARY_QUESTION = (
    "Find French motor-insurance customers with at least three qualifying claims "
    "in the last 12 months and total incurred loss above EUR 20,000."
)


def _print_section(heading: str, value: object) -> None:
    print(heading)
    print(json.dumps(value, indent=2, sort_keys=True, default=str))


def main() -> None:
    """Print each deterministic control-plane stage for the primary question."""

    answer = ClaimsInvestigationAgent().answer(PRIMARY_QUESTION, CallerContext(role="ClaimsAnalystFR"))
    rendered = answer.to_dict()
    _print_section("BUSINESS QUESTION", rendered["question"])
    _print_section("SEMANTIC RESOLUTION", rendered["resolution"])
    _print_section("DATA PRODUCTS", rendered["data_products"])
    _print_section("SEMANTIC QUERY PLAN", rendered["plan"])
    _print_section("PHYSICAL MAPPING", rendered["compiled_query"]["mapping_ids"])
    _print_section("GENERATED SQL", rendered["compiled_query"])
    _print_section("VALIDATION", rendered["quality"])
    _print_section("RESULT", rendered["result"])
    _print_section("PROVENANCE", rendered["provenance"])


if __name__ == "__main__":
    main()
