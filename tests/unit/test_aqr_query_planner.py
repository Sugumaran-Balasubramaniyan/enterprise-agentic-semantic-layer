"""Contract tests for the closed AQR planner and SPARQL compiler."""

from __future__ import annotations

import pytest

from semantic_layer.reasoning.query_planner import (
    MAX_PREREQUISITE_DEPTH,
    LogicalQueryPlan,
    QueryPlanner,
    TraversalPattern,
)
from semantic_layer.reasoning.schema_linker import GroundedEntities, SchemaLinker
from semantic_layer.reasoning.text_to_sparql import TextToSPARQLEngine


def _ground(query: str) -> GroundedEntities:
    return SchemaLinker().ground(query)


def _bound_variables(plan: LogicalQueryPlan) -> tuple[set[str], set[str]]:
    required = set()
    optional = set()
    for pattern in plan.patterns:
        for value in (pattern.subject, pattern.object_val):
            if value.startswith("?"):
                required.add(value)
    for pattern in plan.optional_patterns:
        for value in (pattern.subject, pattern.object_val):
            if value.startswith("?"):
                optional.add(value)
    return required, optional


def test_prerequisite_cycle_and_depth_contract() -> None:
    """Prerequisites use a finite closure, exclude the target, and carry depth evidence."""

    entities = _ground("What are the prerequisite notes required for SAP Note 3109922?")
    plan = QueryPlanner().plan(entities)
    query = TextToSPARQLEngine().compile(plan)

    assert plan.intent == "PREREQUISITE_CLOSURE"
    assert plan.select_vars == ["?note", "?noteNumber", "?title"]
    assert plan.required_variables == ["?note", "?noteNumber", "?title"]
    assert plan.optional_variables == []

    closure = next(
        pattern
        for pattern in plan.patterns
        if pattern.subject == "?targetNote" and pattern.object_val == "?note"
    )
    paths = closure.predicate.removeprefix("(").removesuffix(")").split("|")
    assert len(paths) == MAX_PREREQUISITE_DEPTH == 16
    assert [path.count("cifsup:hasPrerequisiteNote") for path in paths] == list(
        range(1, MAX_PREREQUISITE_DEPTH + 1)
    )
    assert all("+" not in path for path in paths)
    assert any("?note != ?targetNote" in item for item in plan.filters)
    assert any("PREREQUISITE_DEPTH_EXCEEDED" in item for item in plan.filters)
    assert "PREREQUISITE_DEPTH_EXCEEDED" in query
    assert "cifsup:hasPrerequisiteNote+" not in query
    assert "?prereqTitle" not in query


def test_all_projected_variables_have_patterns() -> None:
    """Every selected variable is bound by exactly the declared pattern class."""

    queries = [
        "Retrieve the title and details for SAP Note 3012445.",
        "Which note resolves alert DBSQL_NO_MORE_CONNECTION in component BC-DB-HDB?",
        "Find notes for alert TIME_OUT in component MM-PUR-PO on S/4HANA 2023.",
        "Find notes for alert TIME_OUT in component MM-PUR-PO at SP99.",
        "What are the prerequisite notes required for SAP Note 3109922?",
    ]

    planner = QueryPlanner()
    compiler = TextToSPARQLEngine()
    for query_text in queries:
        plan = planner.plan(_ground(query_text))
        compiler.validate_projections(plan)
        required_bound, optional_bound = _bound_variables(plan)

        assert set(plan.select_vars) == set(plan.required_variables) | set(plan.optional_variables)
        assert not set(plan.required_variables) & set(plan.optional_variables)
        assert set(plan.required_variables) <= required_bound
        assert set(plan.optional_variables) <= optional_bound
        compiled = compiler.compile(plan)
        assert "http://ontology." + "sap.com" not in compiled


def test_combined_anchor_and_optional_projection_contract() -> None:
    """Combined anchors stay mandatory while optional output is rendered in OPTIONAL only."""

    entities = GroundedEntities(
        raw_query="Find notes for alert TIME_OUT in component BC-DB-HDB on S/4HANA 2023 at SP99.",
        intent="VERSION_FILTERED_SEARCH",
        alert_codes=["TIME_OUT"],
        component_codes=["BC-DB-HDB"],
        product_versions=["S4HANA_2023"],
        support_packages=[99],
    )
    planner = QueryPlanner()
    plan = planner.plan(entities)

    predicates = {pattern.predicate for pattern in plan.patterns}
    assert "cifsup:resolvesAlert" in predicates
    assert any(
        predicate.startswith("cifsup:affectsComponent") for predicate in predicates
    )
    assert "cifsup:validForProductVersion" in predicates
    assert "cifppms:versionCode" in predicates
    package_filters = [item for item in plan.filters if "minSP" in item]
    assert package_filters == ["?minSP <= 99 && ?maxSP >= 99"]

    optional_plan = LogicalQueryPlan(
        target_var="?note",
        intent="ALERT_RESOLUTION",
        select_vars=["?note", "?noteNumber", "?title", "?priority"],
        patterns=[
            TraversalPattern("?note", "rdf:type", "cifsup:SAPNote"),
            TraversalPattern("?note", "cifsup:noteNumber", "?noteNumber"),
            TraversalPattern("?note", "cifsup:title", "?title"),
        ],
        optional_patterns=[
            TraversalPattern("?note", "cifsup:priority", "?priority", optional=True),
        ],
        required_variables=["?note", "?noteNumber", "?title"],
        optional_variables=["?priority"],
        order_by="?noteNumber",
        limit=25,
    )
    compiler = TextToSPARQLEngine()
    compiled = compiler.compile(optional_plan)
    compiler.validate_projections(optional_plan)
    assert "OPTIONAL { ?note cifsup:priority ?priority . }" in compiled
    assert "?priority cifsup:priority" not in compiled
    assert compiled.index("ORDER BY ?noteNumber") < compiled.index("LIMIT 25")


def test_compiler_rejects_unbound_required_projection() -> None:
    """Missing mandatory bindings fail closed before any SPARQL is emitted."""

    plan = LogicalQueryPlan(
        target_var="?note",
        intent="NOTE_LOOKUP",
        select_vars=["?note", "?noteNumber", "?title"],
        patterns=[TraversalPattern("?note", "cifsup:noteNumber", "?noteNumber")],
        required_variables=["?note", "?noteNumber", "?title"],
    )

    compiler = TextToSPARQLEngine()
    with pytest.raises(ValueError, match="UNBOUND_REQUIRED_PROJECTION"):
        compiler.compile(plan)
