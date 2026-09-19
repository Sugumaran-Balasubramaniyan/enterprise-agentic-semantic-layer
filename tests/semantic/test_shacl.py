from pathlib import Path

from pyshacl import validate as shacl_validate
from rdflib import RDF, RDFS, Graph, Namespace

from semantic_layer import validation
from semantic_layer.semantic_validation import ValidationResult, validate_graph

ROOT = Path(__file__).parents[2]
SHAPES = ROOT / "semantic" / "shapes" / "sap_erp_shapes.ttl"
VALID_GRAPH = ROOT / "semantic" / "ontology" / "sample-graph-valid.ttl"
INVALID_GRAPH = ROOT / "semantic" / "ontology" / "sample-graph-invalid.ttl"
ONTOLOGY = ROOT / "semantic" / "ontology" / "sap_erp.ttl"
TAXONOMY = ROOT / "semantic" / "taxonomy" / "sap_products.ttl"


def test_invalid_claim_graph_fails_shacl_validation() -> None:
    result = validate_graph(INVALID_GRAPH, SHAPES)
    assert result.conforms is False
    assert "amountInCompanyCurrency" in result.report_text or "postingDate" in result.report_text


def test_valid_claim_graph_conforms_to_shacl_shapes() -> None:
    result = validate_graph(VALID_GRAPH, SHAPES)
    assert result.conforms is True


def test_valid_graph_contains_relationship_links_and_country_context() -> None:
    graph = Graph().parse(VALID_GRAPH, format="turtle")
    sap = Namespace("https://sap.example/erp/")
    bp = sap["partner-FR-001"]
    order = sap["order-FR-001"]
    doc = sap["doc-FR-001"]

    assert (bp, sap.hasSalesOrder, order) in graph
    assert (bp, sap.hasFinancialPosting, doc) in graph
    assert (doc, sap.referencesSalesOrder, order) in graph
    assert (bp, sap.countryCode, None) in graph
    assert (order, sap.countryCode, None) in graph


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
    sap = Namespace("https://sap.example/erp/")
    owl = Namespace("http://www.w3.org/2002/07/owl#")
    assert (sap[""], RDF.type, owl.Ontology) in graph
    assert (sap[""], owl.versionInfo, None) in graph
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
        predicate = sap[name]
        assert (predicate, RDF.type, owl.ObjectProperty) in graph
        assert (predicate, Namespace("http://www.w3.org/2000/01/rdf-schema#").domain, sap[domain]) in graph
        assert (predicate, Namespace("http://www.w3.org/2000/01/rdf-schema#").range, sap[range_]) in graph
    assert (sap.ProductAutomotive, RDFS.subClassOf, sap.Product) in graph
    assert (sap.ProductCommercial, RDFS.subClassOf, sap.Product) in graph


def test_country_code_domain_is_a_superclass_and_combined_instance_graph_conforms() -> None:
    ontology = Graph().parse(ONTOLOGY, format="turtle")
    sap = Namespace("https://sap.example/erp/")
    rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
    domains = set(ontology.objects(sap.countryCode, rdfs.domain))
    assert domains == {sap.CountryCodedEntity}
    assert (sap.BusinessPartner, RDFS.subClassOf, sap.CountryCodedEntity) in ontology
    assert (sap.SalesOrder, RDFS.subClassOf, sap.CountryCodedEntity) in ontology

    instance = Graph().parse(VALID_GRAPH, format="turtle")
    shapes = Graph().parse(SHAPES, format="turtle")
    conforms, _, _ = shacl_validate(
        instance,
        shacl_graph=shapes,
        ont_graph=ontology,
        inference="rdfs",
        abort_on_first=False,
        advanced=False,
    )
    assert conforms is True


def test_taxonomy_declares_version_and_skos_hierarchy_and_alternatives() -> None:
    graph = Graph().parse(TAXONOMY, format="turtle")
    sap = Namespace("https://sap.example/erp/")
    skos = Namespace("http://www.w3.org/2004/02/skos/core#")
    owl = Namespace("http://www.w3.org/2002/07/owl#")
    assert (sap.ProductScheme, owl.versionInfo, None) in graph
    assert (sap.ProductAutomotive, skos.broader, sap.Product) in graph
    assert (sap.ProductCommercial, skos.broader, sap.Product) in graph
    assert (sap.Product, skos.narrower, sap.ProductAutomotive) in graph
    assert (sap.Product, skos.narrower, sap.ProductCommercial) in graph
    assert (sap.ProductAutomotive, skos.altLabel, None) in graph
    assert (sap.ProductCommercial, skos.altLabel, None) in graph


def test_shapes_and_sample_graphs_declare_semantic_versions() -> None:
    owl = Namespace("http://www.w3.org/2002/07/owl#")
    sap = Namespace("https://sap.example/erp/")
    for path, subject in (
        (SHAPES, sap.ERPAShapes),
        (VALID_GRAPH, sap.SampleGraphValid),
        (INVALID_GRAPH, sap.SampleGraphInvalid),
    ):
        graph = Graph().parse(path, format="turtle")
        assert (subject, owl.versionInfo, None) in graph
