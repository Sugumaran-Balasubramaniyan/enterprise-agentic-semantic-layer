"""Tests for SAP Knowledge Graph loading, RDF parsing, and W3C SHACL validation."""

from __future__ import annotations

import pytest
from rdflib import RDF, XSD, Literal, Namespace, URIRef

from semantic_layer.kg.loader import SAPKnowledgeGraph

SAP = Namespace("https://example.org/cifre-kg/support#")
PPMS = Namespace("https://example.org/cifre-kg/ppms#")


@pytest.fixture
def sap_kg() -> SAPKnowledgeGraph:
    """Fixture providing initialized SAP knowledge graph."""
    kg = SAPKnowledgeGraph()
    kg.load_ontologies([
        "semantic/ontology/sap_ppms.ttl",
        "semantic/ontology/sap_support.ttl",
        "semantic/data/sap_support_graph.ttl",
    ])
    return kg


def test_kg_loads_triples(sap_kg: SAPKnowledgeGraph) -> None:
    """Ensure knowledge graph loads expected minimum triple count."""
    assert len(sap_kg) >= 400


def test_shacl_validation_conforms(sap_kg: SAPKnowledgeGraph) -> None:
    """Verify that the generated enterprise graph conforms to all SHACL shapes."""
    conforms, report = sap_kg.validate_shacl("semantic/shapes/sap_support_shapes.ttl")
    assert conforms is True, f"SHACL validation failed:\n{report}"


def test_shacl_catches_invalid_note() -> None:
    """Verify that SHACL shape flags a note with missing mandatory component or invalid priority."""
    kg = SAPKnowledgeGraph()
    kg.load_ontologies([
        "semantic/ontology/sap_ppms.ttl",
        "semantic/ontology/sap_support.ttl",
    ])

    # Inject invalid note: missing affectsComponent and invalid priority
    bad_note = URIRef("https://example.org/cifre-kg/data/support/note/BAD_NOTE")
    kg.graph.add((bad_note, RDF.type, SAP.SAPNote))
    kg.graph.add((bad_note, SAP.noteNumber, Literal("9999999", datatype=XSD.string)))
    kg.graph.add((bad_note, SAP.title, Literal("Invalid Note Without Component", lang="en")))
    kg.graph.add((bad_note, SAP.priority, Literal("INVALID_PRIORITY", datatype=XSD.string)))

    conforms, report = kg.validate_shacl("semantic/shapes/sap_support_shapes.ttl")
    assert conforms is False
    assert "Priority must be Very High, High, Medium, or Low." in report or "affectsComponent" in report


def test_shacl_rejects_product_version_without_included_component(
    sap_kg: SAPKnowledgeGraph,
) -> None:
    """Require every product version to include at least one component version."""
    for product_version, _, component_version in list(
        sap_kg.graph.triples((None, PPMS.includesComponent, None))
    ):
        sap_kg.graph.remove((product_version, PPMS.includesComponent, component_version))

    conforms, report = sap_kg.validate_shacl("semantic/shapes/sap_support_shapes.ttl")

    assert conforms is False
    assert "includes at least one software component version" in report.lower()


def test_sparql_query_execution(sap_kg: SAPKnowledgeGraph) -> None:
    """Test standard SPARQL 1.1 query execution."""
    sparql = """
    SELECT ?note ?num WHERE {
            ?note rdf:type cifsup:SAPNote .
            ?note cifsup:noteNumber ?num .
    } LIMIT 5
    """
    rows = sap_kg.query_sparql(sparql)
    assert len(rows) == 5
    assert "num" in rows[0]
