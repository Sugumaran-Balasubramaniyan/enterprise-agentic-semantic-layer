"""Tests for SAP Knowledge Graph loading, RDF parsing, and W3C SHACL validation."""

from __future__ import annotations

import pytest
from rdflib import RDF, XSD, Literal, URIRef

from semantic_layer.kg.loader import CIFPPMS, CIFSUP, SAPKnowledgeGraph
from semantic_layer.reasoning.query_planner import QueryPlanner
from semantic_layer.reasoning.schema_linker import GroundedEntities, SchemaLinker
from semantic_layer.reasoning.text_to_sparql import TextToSPARQLEngine


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


def test_shacl_scope_selects_the_graph_partition_it_labels() -> None:
    kg = SAPKnowledgeGraph()
    kg.load_ontologies(
        [
            "semantic/ontology/sap_ppms.ttl",
            "semantic/ontology/sap_support.ttl",
            "semantic/data/support-graph-invalid.ttl",
            "semantic/ontology/sap_erp.ttl",
            "semantic/ontology/sample-graph-invalid.ttl",
        ]
    )

    support_report = kg.validate_shacl(
        "semantic/shapes/sap_support_shapes.ttl", scope="support"
    )
    erp_partition_with_support_shapes = kg.validate_shacl(
        "semantic/shapes/sap_support_shapes.ttl", scope="erp"
    )
    erp_report = kg.validate_shacl("semantic/shapes/sap_erp_shapes.ttl", scope="erp")

    assert support_report.scope == "support"
    assert support_report.conforms is False
    assert erp_partition_with_support_shapes.conforms is True
    assert erp_report.scope == "erp"
    assert erp_report.conforms is False


def test_shacl_catches_invalid_note() -> None:
    """Verify that SHACL shape flags a note with missing mandatory component or invalid priority."""
    kg = SAPKnowledgeGraph()
    kg.load_ontologies([
        "semantic/ontology/sap_ppms.ttl",
        "semantic/ontology/sap_support.ttl",
    ])

    # Inject invalid note: missing affectsComponent and invalid priority
    bad_note = URIRef("https://example.org/cifre-kg/data/support/note/BAD_NOTE")
    kg.graph.add((bad_note, RDF.type, CIFSUP.SAPNote))
    kg.graph.add((bad_note, CIFSUP.noteNumber, Literal("9999999", datatype=XSD.string)))
    kg.graph.add((bad_note, CIFSUP.title, Literal("Invalid Note Without Component", lang="en")))
    kg.graph.add((bad_note, CIFSUP.priority, Literal("INVALID_PRIORITY", datatype=XSD.string)))

    conforms, report = kg.validate_shacl("semantic/shapes/sap_support_shapes.ttl")
    assert conforms is False
    assert "Priority must be Very High, High, Medium, or Low." in report or "affectsComponent" in report


def test_shacl_rejects_product_version_without_included_component(
    sap_kg: SAPKnowledgeGraph,
) -> None:
    """Require every product version to include at least one component version."""
    for product_version, _, component_version in list(
        sap_kg.graph.triples((None, CIFPPMS.includesComponent, None))
    ):
        sap_kg.graph.remove((product_version, CIFPPMS.includesComponent, component_version))

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


def test_bounded_prerequisite_closure_excludes_target_and_deduplicates(
    sap_kg: SAPKnowledgeGraph,
) -> None:
    """The production fixture returns each transitive prerequisite once."""

    entities = SchemaLinker().ground(
        "What are the prerequisite notes required for SAP Note 3109922?"
    )
    plan = QueryPlanner().plan(entities)
    rows = sap_kg.query_sparql(TextToSPARQLEngine().compile(plan))

    note_numbers = [row["noteNumber"] for row in rows]
    assert note_numbers == ["3012445", "3098110"]
    assert "3109922" not in note_numbers
    assert len(note_numbers) == len(set(note_numbers))


def test_bounded_prerequisite_closure_terminates_on_cycle() -> None:
    """Finite path alternatives terminate on A -> B -> C -> A."""

    kg = SAPKnowledgeGraph()
    kg.load_file("semantic/data/support-prerequisite-cycle.ttl")
    for note_id in ("A", "B", "C"):
        note = URIRef(f"https://example.org/cifre-kg/data/support/note/{note_id}")
        kg.graph.add((note, RDF.type, CIFSUP.SAPNote))
        kg.graph.add((note, CIFSUP.noteNumber, Literal(note_id, datatype=XSD.string)))
        kg.graph.add((note, CIFSUP.title, Literal(f"Synthetic note {note_id}", lang="en")))

    entities = GroundedEntities(
        raw_query="cycle A",
        intent="PREREQUISITE_CLOSURE",
        note_numbers=["A"],
    )
    plan = QueryPlanner().plan(entities)
    rows = kg.query_sparql(TextToSPARQLEngine().compile(plan))

    note_numbers = [row["noteNumber"] for row in rows]
    assert note_numbers == ["B", "C"]
    assert "A" not in note_numbers
