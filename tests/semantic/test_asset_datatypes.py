"""Datatype, SHACL, and bounded prerequisite fixture contracts."""

from __future__ import annotations

from itertools import pairwise
from pathlib import Path

from rdflib import OWL, RDF, RDFS, XSD, Graph, Literal, Namespace

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
    assert (CIFSUP.hasPrerequisiteNote, RDF.type, OWL.TransitiveProperty) in graph


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


def test_every_support_and_ppms_target_class_requires_an_english_label() -> None:
    graph = Graph().parse(ROOT / "semantic/shapes/sap_support_shapes.ttl", format="turtle")
    target_classes = set(graph.objects(None, SH.targetClass))
    assert target_classes
    for target_class in target_classes:
        shapes = set(graph.subjects(SH.targetClass, target_class))
        label_shapes = {
            prop_shape
            for shape in shapes
            for prop_shape in graph.objects(shape, SH.property)
            if graph.value(prop_shape, SH.path) == RDFS.label
        }
        assert label_shapes, target_class
        for prop_shape in label_shapes:
            assert (prop_shape, SH.datatype, RDF.langString) in graph
            language_list = graph.value(prop_shape, SH.languageIn)
            assert language_list is not None
            assert list(graph.items(language_list)) == [Literal("en")]


def test_every_shape_property_has_an_english_diagnostic_message() -> None:
    for path in (
        ROOT / "semantic/shapes/sap_support_shapes.ttl",
        ROOT / "semantic/shapes/sap_erp_shapes.ttl",
    ):
        graph = Graph().parse(path, format="turtle")
        property_shapes = set(graph.objects(None, SH.property))
        assert property_shapes
        for prop_shape in property_shapes:
            messages = list(graph.objects(prop_shape, SH.message))
            assert messages, (path, prop_shape)
            assert all(message.language == "en" for message in messages)


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
