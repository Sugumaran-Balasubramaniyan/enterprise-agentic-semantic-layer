"""Datatype, SHACL, and bounded prerequisite fixture contracts."""

from __future__ import annotations

from itertools import pairwise
from pathlib import Path

from rdflib import RDF, RDFS, XSD, Graph, Literal, Namespace

from semantic_layer.semantic_validation import validate_graph

ROOT = Path(__file__).resolve().parents[2]
CIFSUP = Namespace("https://example.org/cifre-kg/support#")
CIFPPMS = Namespace("https://example.org/cifre-kg/ppms#")
CIFMETA = Namespace("https://example.org/cifre-kg/meta#")
CIFMETAID = Namespace("https://example.org/cifre-kg/id/meta/")
CIFDATA = Namespace("https://example.org/cifre-kg/data/")
SH = Namespace("http://www.w3.org/ns/shacl#")


def test_support_ontology_declares_human_fields_as_english_lang_strings() -> None:
    graph = Graph().parse(ROOT / "semantic/ontology/sap_support.ttl", format="turtle")
    human_fields = (
        CIFSUP.title,
        CIFSUP.symptom,
        CIFSUP.rootCause,
        CIFSUP.resolution,
        CIFSUP.componentDescription,
        CIFSUP.categoryName,
    )
    for field in human_fields:
        assert (field, RDFS.range, RDF.langString) in graph


def test_support_shapes_require_english_lang_strings_without_or_workaround() -> None:
    graph = Graph().parse(ROOT / "semantic/shapes/sap_support_shapes.ttl", format="turtle")
    assert not list(graph.triples((None, SH.or_, None)))
    human_paths = {
        CIFSUP.title,
        CIFSUP.symptom,
        CIFSUP.rootCause,
        CIFSUP.resolution,
        CIFSUP.componentDescription,
        CIFSUP.categoryName,
        RDFS.label,
    }
    property_shapes = set(graph.objects(None, SH.property))
    matching = [shape for shape in property_shapes if graph.value(shape, SH.path) in human_paths]
    assert matching
    for shape in matching:
        assert (shape, SH.datatype, RDF.langString) in graph
        language_list = graph.value(shape, SH.languageIn)
        assert language_list is not None
        assert list(graph.items(language_list)) == [Literal("en")]


def test_machine_fields_keep_declared_string_and_numeric_datatypes() -> None:
    ontology = Graph().parse(ROOT / "semantic/ontology/sap_support.ttl", format="turtle")
    for field in (CIFSUP.noteNumber, CIFSUP.alertCode, CIFSUP.priority, CIFSUP.componentCode):
        assert (field, RDFS.range, XSD.string) in ontology
    for field in (CIFSUP.minSupportPackage, CIFSUP.maxSupportPackage):
        assert (field, RDFS.range, XSD.integer) in ontology
    ppms = Graph().parse(ROOT / "semantic/ontology/sap_ppms.ttl", format="turtle")
    assert (CIFPPMS.releaseYear, RDFS.range, XSD.integer) in ppms


def test_support_shacl_matrix_fixtures_have_expected_outcomes() -> None:
    shapes = ROOT / "semantic/shapes/sap_support_shapes.ttl"
    valid = validate_graph(ROOT / "semantic/data/sap_support_graph.ttl", shapes)
    invalid = validate_graph(ROOT / "semantic/data/support-graph-invalid.ttl", shapes)
    assert valid.conforms is True, valid.report_text
    assert invalid.conforms is False


def test_erp_shacl_matrix_fixtures_have_expected_outcomes() -> None:
    shapes = ROOT / "semantic/shapes/sap_erp_shapes.ttl"
    valid = validate_graph(ROOT / "semantic/ontology/sample-graph-valid.ttl", shapes)
    invalid = validate_graph(ROOT / "semantic/ontology/sample-graph-invalid.ttl", shapes)
    assert valid.conforms is True, valid.report_text
    assert invalid.conforms is False


def test_prerequisite_cycle_fixture_is_bounded_and_excludes_target() -> None:
    graph = Graph().parse(ROOT / "semantic/data/support-prerequisite-cycle.ttl", format="turtle")
    start = CIFDATA["support/note/A"]
    expected = {CIFDATA["support/note/B"], CIFDATA["support/note/C"]}
    reachable = set(graph.objects(start, CIFSUP.hasPrerequisiteNote))
    reachable.update(
        graph.objects(CIFDATA["support/note/B"], CIFSUP.hasPrerequisiteNote)
    )
    assert reachable == expected
    assert start not in reachable
    assert (start, CIFSUP.hasPrerequisiteNote, CIFDATA["support/note/B"]) in graph
    assert (CIFDATA["support/note/B"], CIFSUP.hasPrerequisiteNote, CIFDATA["support/note/C"]) in graph
    assert (CIFDATA["support/note/C"], CIFSUP.hasPrerequisiteNote, start) in graph


def test_prerequisite_depth17_fixture_contains_exact_chain() -> None:
    graph = Graph().parse(ROOT / "semantic/data/support-prerequisite-depth17.ttl", format="turtle")
    nodes = [CIFDATA[f"support/note/N{i}"] for i in range(18)]
    for left, right in pairwise(nodes):
        assert (left, CIFSUP.hasPrerequisiteNote, right) in graph
    assert len(list(graph.triples((None, CIFSUP.hasPrerequisiteNote, None)))) == 17
