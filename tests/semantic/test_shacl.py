from pathlib import Path

from pyshacl import validate as shacl_validate
from rdflib import RDF, RDFS, Graph, Namespace

from semantic_layer import validation
from semantic_layer.semantic_validation import ValidationResult, validate_graph

ROOT = Path(__file__).parents[2]
SHAPES = ROOT / "semantic" / "shapes" / "insurance-shapes.ttl"
VALID_GRAPH = ROOT / "semantic" / "ontology" / "sample-graph-valid.ttl"
INVALID_GRAPH = ROOT / "semantic" / "ontology" / "sample-graph-invalid.ttl"
ONTOLOGY = ROOT / "semantic" / "ontology" / "insurance.ttl"
TAXONOMY = ROOT / "semantic" / "taxonomy" / "insurance-products.ttl"


def test_invalid_claim_graph_fails_shacl_validation() -> None:
    result = validate_graph(INVALID_GRAPH, SHAPES)
    assert result.conforms is False
    assert "claimDate" in result.report_text


def test_valid_claim_graph_conforms_to_shacl_shapes() -> None:
    result = validate_graph(VALID_GRAPH, SHAPES)
    assert result.conforms is True


def test_valid_graph_contains_relationship_links_and_country_context() -> None:
    graph = Graph().parse(VALID_GRAPH, format="turtle")
    insurance = Namespace("https://globalsure.example/insurance/")
    customer = insurance["customer-FR-001"]
    policy = insurance["policy-FR-001"]
    claim = insurance["claim-FR-001"]

    assert (customer, insurance.ownsPolicy, policy) in graph
    assert (customer, insurance.submitsClaim, claim) in graph
    assert (claim, insurance.relatesToPolicy, policy) in graph
    assert (customer, insurance.countryCode, None) in graph
    assert (policy, insurance.countryCode, None) in graph


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
    insurance = Namespace("https://globalsure.example/insurance/")
    owl = Namespace("http://www.w3.org/2002/07/owl#")
    assert (insurance[""], RDF.type, owl.Ontology) in graph
    assert (insurance[""], owl.versionInfo, None) in graph
    for name, domain, range_ in (
        ("ownsPolicy", "Customer", "Policy"),
        ("submitsClaim", "Customer", "Claim"),
        ("relatesToPolicy", "Claim", "Policy"),
        ("hasProduct", "Policy", "InsuranceProduct"),
        ("coversRisk", "Policy", "Risk"),
        ("hasCoverage", "Policy", "Coverage"),
        ("generatesPremium", "Policy", "Premium"),
        ("hasClaimStatus", "Claim", "ClaimStatus"),
        ("hasIncurredLoss", "Claim", "IncurredLoss"),
    ):
        predicate = insurance[name]
        assert (predicate, RDF.type, owl.ObjectProperty) in graph
        assert (predicate, Namespace("http://www.w3.org/2000/01/rdf-schema#").domain, insurance[domain]) in graph
        assert (predicate, Namespace("http://www.w3.org/2000/01/rdf-schema#").range, insurance[range_]) in graph
    assert (insurance.MotorInsurance, RDFS.subClassOf, insurance.InsuranceProduct) in graph


def test_country_code_domain_is_a_superclass_and_combined_instance_graph_conforms() -> None:
    ontology = Graph().parse(ONTOLOGY, format="turtle")
    insurance = Namespace("https://globalsure.example/insurance/")
    rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
    domains = set(ontology.objects(insurance.countryCode, rdfs.domain))
    assert domains == {insurance.CountryCodedEntity}
    assert (insurance.Customer, RDFS.subClassOf, insurance.CountryCodedEntity) in ontology
    assert (insurance.Policy, RDFS.subClassOf, insurance.CountryCodedEntity) in ontology

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
    insurance = Namespace("https://globalsure.example/insurance/")
    skos = Namespace("http://www.w3.org/2004/02/skos/core#")
    owl = Namespace("http://www.w3.org/2002/07/owl#")
    assert (insurance.InsuranceProductScheme, owl.versionInfo, None) in graph
    assert (insurance.MotorInsurance, skos.broader, insurance.InsuranceProduct) in graph
    assert (insurance.InsuranceProduct, skos.narrower, insurance.MotorInsurance) in graph
    assert (insurance.MotorInsurance, skos.altLabel, None) in graph


def test_shapes_and_sample_graphs_declare_semantic_versions() -> None:
    owl = Namespace("http://www.w3.org/2002/07/owl#")
    insurance = Namespace("https://globalsure.example/insurance/")
    for path, subject in (
        (SHAPES, insurance.InsuranceShapes),
        (VALID_GRAPH, insurance.SampleGraphValid),
        (INVALID_GRAPH, insurance.SampleGraphInvalid),
    ):
        graph = Graph().parse(path, format="turtle")
        assert (subject, owl.versionInfo, None) in graph
