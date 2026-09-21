"""W3C SHACL validation tests for the neutral synthetic fixtures."""

from pathlib import Path

from rdflib import OWL, RDF, RDFS, Graph, Namespace

from semantic_layer import validation
from semantic_layer.semantic_validation import ValidationResult, validate_graph

ROOT = Path(__file__).resolve().parents[2]
SHAPES = ROOT / "semantic/shapes/sap_erp_shapes.ttl"
VALID_GRAPH = ROOT / "semantic/ontology/sample-graph-valid.ttl"
INVALID_GRAPH = ROOT / "semantic/ontology/sample-graph-invalid.ttl"
ONTOLOGY = ROOT / "semantic/ontology/sap_erp.ttl"
TAXONOMY = ROOT / "semantic/taxonomy/sap_products.ttl"
CIFERP = Namespace("https://example.org/cifre-kg/erp#")
CIFSKOS = Namespace("https://example.org/cifre-kg/vocabulary#")
CIFDATA = Namespace("https://example.org/cifre-kg/data/")
CIFMETAID = Namespace("https://example.org/cifre-kg/id/meta/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")


def test_invalid_claim_graph_fails_shacl_validation() -> None:
    result = validate_graph(INVALID_GRAPH, SHAPES)
    assert result.conforms is False
    assert "amountInCompanyCurrency" in result.report_text or "postingDate" in result.report_text


def test_valid_claim_graph_conforms_to_shacl_shapes() -> None:
    result = validate_graph(VALID_GRAPH, SHAPES)
    assert result.conforms is True, result.report_text


def test_valid_graph_contains_relationship_links_and_country_context() -> None:
    graph = Graph().parse(VALID_GRAPH, format="turtle")
    bp = CIFDATA["erp/partner-FR-001"]
    order = CIFDATA["erp/order-FR-001"]
    doc = CIFDATA["erp/doc-FR-001"]
    assert (bp, CIFERP.hasSalesOrder, order) in graph
    assert (bp, CIFERP.hasFinancialPosting, doc) in graph
    assert (doc, CIFERP.referencesSalesOrder, order) in graph
    assert (bp, CIFERP.countryCode, None) in graph
    assert (order, CIFERP.countryCode, None) in graph


def test_shacl_validation_reports_fixture_paths() -> None:
    result = validate_graph(INVALID_GRAPH, SHAPES)
    assert result.data_path == INVALID_GRAPH
    assert result.shapes_path == SHAPES


def test_validation_cli_rejects_nonconforming_valid_fixture(monkeypatch) -> None:
    outcomes = iter((False, False))

    def fake_validate_graph(*_args, **_kwargs) -> ValidationResult:
        return ValidationResult(
            conforms=next(outcomes), report_text="test report", data_path=INVALID_GRAPH, shapes_path=SHAPES
        )

    monkeypatch.setattr(validation, "validate_graph", fake_validate_graph)
    assert validation.main(ROOT) == 1


def test_validation_cli_rejects_conforming_invalid_fixture(monkeypatch) -> None:
    outcomes = iter((True, True))

    def fake_validate_graph(*_args, **_kwargs) -> ValidationResult:
        return ValidationResult(
            conforms=next(outcomes), report_text="test report", data_path=INVALID_GRAPH, shapes_path=SHAPES
        )

    monkeypatch.setattr(validation, "validate_graph", fake_validate_graph)
    assert validation.main(ROOT) == 1


def test_validation_cli_accepts_expected_fixture_outcomes(monkeypatch) -> None:
    outcomes = iter((True, False))

    def fake_validate_graph(*_args, **_kwargs) -> ValidationResult:
        return ValidationResult(
            conforms=next(outcomes), report_text="test report", data_path=INVALID_GRAPH, shapes_path=SHAPES
        )

    monkeypatch.setattr(validation, "validate_graph", fake_validate_graph)
    assert validation.main(ROOT) == 0


def test_ontology_declares_versions_domains_ranges_and_subclasses() -> None:
    graph = Graph().parse(ONTOLOGY, format="turtle")
    assert (CIFERP[""], RDF.type, OWL.Ontology) in graph
    assert (CIFERP[""], OWL.versionInfo, None) in graph
    for name, domain, range_ in (
        ("hasSalesOrder", "BusinessPartner", "SalesOrder"),
        ("hasFinancialPosting", "BusinessPartner", "FinancialPosting"),
        ("referencesSalesOrder", "FinancialPosting", "SalesOrder"),
        ("hasProduct", "SalesOrder", "Product"),
        ("coversRisk", "SalesOrder", "Risk"),
        ("hasCoverage", "SalesOrder", "Coverage"),
        ("generatesBilling", "SalesOrder", "BillingDocument"),
        ("hasPostingStatus", "FinancialPosting", "PostingStatus"),
        ("hasFinancialLoss", "FinancialPosting", "FinancialLoss"),
    ):
        predicate = CIFERP[name]
        assert (predicate, RDF.type, OWL.ObjectProperty) in graph
        assert (predicate, RDFS.domain, CIFERP[domain]) in graph
        assert (predicate, RDFS.range, CIFERP[range_]) in graph
    assert (CIFERP.ProductAutomotive, RDFS.subClassOf, CIFERP.Product) in graph
    assert (CIFERP.ProductCommercial, RDFS.subClassOf, CIFERP.Product) in graph


def test_country_code_domain_is_a_superclass_and_combined_instance_graph_conforms() -> None:
    ontology = Graph().parse(ONTOLOGY, format="turtle")
    assert set(ontology.objects(CIFERP.countryCode, RDFS.domain)) == {CIFERP.CountryCodedEntity}
    assert (CIFERP.BusinessPartner, RDFS.subClassOf, CIFERP.CountryCodedEntity) in ontology
    assert (CIFERP.SalesOrder, RDFS.subClassOf, CIFERP.CountryCodedEntity) in ontology


def test_taxonomy_declares_version_and_skos_hierarchy_and_alternatives() -> None:
    graph = Graph().parse(TAXONOMY, format="turtle")
    assert (CIFSKOS.ProductScheme, OWL.versionInfo, None) in graph
    assert (CIFSKOS.ProductAutomotive, SKOS.broader, CIFSKOS.Product) in graph
    assert (CIFSKOS.ProductCommercial, SKOS.broader, CIFSKOS.Product) in graph
    assert (CIFSKOS.Product, SKOS.narrower, CIFSKOS.ProductAutomotive) in graph
    assert (CIFSKOS.Product, SKOS.narrower, CIFSKOS.ProductCommercial) in graph
    assert (CIFSKOS.ProductAutomotive, SKOS.altLabel, None) in graph
    assert (CIFSKOS.ProductCommercial, SKOS.altLabel, None) in graph


def test_shapes_and_sample_graphs_declare_semantic_versions() -> None:
    for path, subject in (
        (SHAPES, CIFERP.ERPShapes),
        (VALID_GRAPH, CIFMETAID["sample-graph-valid"]),
        (INVALID_GRAPH, CIFMETAID["sample-graph-invalid"]),
    ):
        graph = Graph().parse(path, format="turtle")
        assert (subject, OWL.versionInfo, None) in graph
