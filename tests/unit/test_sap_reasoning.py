"""Unit tests for SAP ontology grounding, query planning, and Text-to-SPARQL compilation."""

from __future__ import annotations

from semantic_layer.reasoning.query_planner import QueryPlanner
from semantic_layer.reasoning.schema_linker import SchemaLinker
from semantic_layer.reasoning.text_to_sparql import TextToSPARQLEngine


def test_schema_linker_extracts_components_and_alerts() -> None:
    linker = SchemaLinker()
    query = "Find notes for alert TIME_OUT in component MM-PUR-PO on S/4HANA 2023"
    entities = linker.ground_or_abstain(query)

    assert "MM-PUR-PO" in entities.component_codes
    assert "TIME_OUT" in entities.alert_codes
    assert "S4HANA_2023" in entities.product_versions
    assert entities.intent == "VERSION_FILTERED_SEARCH"
    assert entities.failure_class == "NONE"


def test_schema_linker_extracts_prerequisite_intent() -> None:
    linker = SchemaLinker()
    query = "What are the prerequisite notes for 3109922?"
    entities = linker.ground_or_abstain(query)

    assert "3109922" in entities.note_numbers
    assert entities.intent == "PREREQUISITE_CLOSURE"
    assert entities.failure_class == "NONE"


def test_query_planner_and_compiler() -> None:
    linker = SchemaLinker()
    planner = QueryPlanner()
    compiler = TextToSPARQLEngine()

    query = "Which note resolves DBSQL_NO_MORE_CONNECTION in component BC-DB-HDB?"
    entities = linker.ground_or_abstain(query)
    plan = planner.plan(entities)
    sparql = compiler.compile(plan)

    assert "PREFIX sap: <http://ontology.sap.com/support#>" in sparql
    assert "PREFIX ppms: <http://ontology.sap.com/ppms#>" in sparql
    assert "SELECT DISTINCT ?note ?title ?noteNumber" in sparql
    assert "DBSQL_NO_MORE_CONNECTION" in sparql
    assert "BC-DB-HDB" in sparql
