"""Namespace and provenance contracts for the synthetic semantic assets."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

import pytest
from rdflib import OWL, RDF, RDFS, Graph, Namespace, URIRef
from rdflib.compare import isomorphic

from semantic_layer.kg.loader import (
    CIFDATA,
    CIFERP,
    CIFMETA,
    CIFMETAID,
    CIFPPMS,
    CIFSKOS,
    CIFSUP,
)
from semantic_layer.kg.loader import (
    NAMESPACE_REGISTRY as LOADER_NAMESPACE_REGISTRY,
)
from semantic_layer.kg.sap_dataset_generator import (
    NAMESPACE_REGISTRY as GENERATOR_NAMESPACE_REGISTRY,
)
from semantic_layer.kg.sap_dataset_generator import (
    build_sap_support_graph,
)

ROOT = Path(__file__).resolve().parents[2]
NAMESPACE_REGISTRY = {
    "cifsup": "https://example.org/cifre-kg/support#",
    "cifppms": "https://example.org/cifre-kg/ppms#",
    "cifdata": "https://example.org/cifre-kg/data/",
    "ciferp": "https://example.org/cifre-kg/erp#",
    "cifskos": "https://example.org/cifre-kg/vocabulary#",
    "cifmeta": "https://example.org/cifre-kg/meta#",
    "cifmetaid": "https://example.org/cifre-kg/id/meta/",
}
APPROVED_BASES = frozenset(NAMESPACE_REGISTRY.values())
W3C_BASES = (
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "http://www.w3.org/2000/01/rdf-schema#",
    "http://www.w3.org/2002/07/owl#",
    "http://www.w3.org/2001/XMLSchema#",
    "http://www.w3.org/ns/shacl#",
    "http://www.w3.org/2004/02/skos/core#",
)
RDF_ASSETS = (
    ROOT / "semantic/ontology/sample-graph-invalid.ttl",
    ROOT / "semantic/ontology/sample-graph-valid.ttl",
    ROOT / "semantic/ontology/sap_erp.ttl",
    ROOT / "semantic/ontology/sap_ppms.ttl",
    ROOT / "semantic/ontology/sap_support.ttl",
    ROOT / "semantic/shapes/sap_erp_shapes.ttl",
    ROOT / "semantic/shapes/sap_support_shapes.ttl",
    ROOT / "semantic/taxonomy/sap_products.ttl",
    ROOT / "semantic/data/sap_support_graph.ttl",
    ROOT / "semantic/data/support-graph-invalid.ttl",
    ROOT / "semantic/data/support-prerequisite-cycle.ttl",
    ROOT / "semantic/data/support-prerequisite-depth17.ttl",
)
TEXT_ASSETS = (
    ROOT / "src/semantic_layer/kg/loader.py",
    ROOT / "src/semantic_layer/kg/sap_dataset_generator.py",
    ROOT / "data/generate_demo_data.py",
    ROOT / "semantic/metrics/metrics.yaml",
    ROOT / "semantic/rules/financial_postings.yaml",
    ROOT / "semantic/vocabulary/sap_erp.yaml",
    ROOT / "data_products/acdoca_financials.yaml",
    ROOT / "data_products/billing_analytics.yaml",
    ROOT / "data_products/business_partners.yaml",
    ROOT / "data_products/sales_orders.yaml",
    ROOT / "tests/semantic/test_active_policy_regression.py",
    ROOT / "tests/semantic/test_mappings.py",
    ROOT / "tests/semantic/test_metric_rules.py",
    ROOT / "tests/semantic/test_sap_kg.py",
    ROOT / "tests/semantic/test_shacl.py",
    ROOT / "tests/semantic/test_vocabulary.py",
)
LOGICAL_CONSUMERS = (
    ROOT / "src/semantic_layer/compiler/duckdb.py",
    ROOT / "src/semantic_layer/governance/policy.py",
    ROOT / "src/semantic_layer/models.py",
    ROOT / "src/semantic_layer/lineage/service.py",
    ROOT / "semantic/metrics/metrics.yaml",
    ROOT / "semantic/rules/financial_postings.yaml",
    ROOT / "semantic/vocabulary/sap_erp.yaml",
    ROOT / "data_products/acdoca_financials.yaml",
    ROOT / "data_products/billing_analytics.yaml",
    ROOT / "data_products/business_partners.yaml",
    ROOT / "data_products/sales_orders.yaml",
    ROOT / "tests/semantic/test_active_policy_regression.py",
    ROOT / "tests/semantic/test_mappings.py",
    ROOT / "tests/semantic/test_metric_rules.py",
    ROOT / "tests/semantic/test_vocabulary.py",
    ROOT / "tests/golden/questions.yaml",
    ROOT / "tests/golden/test_evaluation.py",
    ROOT / "tests/unit/test_data_generation.py",
    ROOT / "tests/unit/test_final_readiness.py",
    ROOT / "tests/unit/test_registry.py",
    ROOT / "tests/unit/test_resolver.py",
    ROOT / "tests/integration/test_agent_e2e.py",
    ROOT / "tests/integration/test_api.py",
    ROOT / "tests/integration/test_duckdb_execution.py",
    ROOT / "tests/unit/test_authorization.py",
    ROOT / "tests/unit/test_execution_controls_security.py",
)

INTENTIONAL_LEGACY_FIXTURE_MARKERS = {
    ROOT / "tests/unit/test_execution_controls_security.py": (
        'Filter(concept_id="sap:PostingStatus", operator="!=", value="REVERSED")',
        '"projected_dimensions": [*plan.projected_dimensions, "sap:SalesOrder"]',
        'source="sap:BusinessPartner",',
        'predicate="sap:hasSalesOrder",',
        'target="sap:SalesOrder",',
        '"DOC_1,SO_1,FR_001,FR,sap:ProductAutomotive,POSTED,2026-08-01,nan\\n",',
        '"DE_DOC_1,DE_SO_1,DE_1,DE,sap:ProductCommercial,POSTED,2026-08-01,1.00\\n",',
    ),
}


def _legacy_uris() -> tuple[str, ...]:
    # Keep the forbidden families out of this test's own source scan.
    return (
        "".join(("http", "://", "ontology", ".", "sap", ".", "com/")),  # noqa: FLY002
        "".join(("http", "://", "data", ".", "sap", ".", "com/")),  # noqa: FLY002
        "".join(("https", "://", "sap", ".", "example", "/erp/")),  # noqa: FLY002
        "".join(("https", "://", "help", ".", "sap", ".", "com/")),  # noqa: FLY002
    )


def _assert_neutral_term(term: URIRef, path: Path) -> None:
    value = str(term)
    assert any(value.startswith(base) for base in (*APPROVED_BASES, *W3C_BASES)), (path, value)


def test_registry_exposes_exact_neutral_namespace_contract() -> None:
    assert NAMESPACE_REGISTRY == {
        "cifsup": "https://example.org/cifre-kg/support#",
        "cifppms": "https://example.org/cifre-kg/ppms#",
        "cifdata": "https://example.org/cifre-kg/data/",
        "ciferp": "https://example.org/cifre-kg/erp#",
        "cifskos": "https://example.org/cifre-kg/vocabulary#",
        "cifmeta": "https://example.org/cifre-kg/meta#",
        "cifmetaid": "https://example.org/cifre-kg/id/meta/",
    }
    assert CIFSUP == Namespace(NAMESPACE_REGISTRY["cifsup"])
    assert CIFPPMS == Namespace(NAMESPACE_REGISTRY["cifppms"])
    assert CIFDATA == Namespace(NAMESPACE_REGISTRY["cifdata"])
    assert CIFERP == Namespace(NAMESPACE_REGISTRY["ciferp"])
    assert CIFSKOS == Namespace(NAMESPACE_REGISTRY["cifskos"])
    assert CIFMETA == Namespace(NAMESPACE_REGISTRY["cifmeta"])
    assert CIFMETAID == Namespace(NAMESPACE_REGISTRY["cifmetaid"])
    assert LOADER_NAMESPACE_REGISTRY is GENERATOR_NAMESPACE_REGISTRY


def test_namespace_registry_is_immutable_and_shared_by_loader_and_generator() -> None:
    assert isinstance(LOADER_NAMESPACE_REGISTRY, MappingProxyType)
    assert LOADER_NAMESPACE_REGISTRY is GENERATOR_NAMESPACE_REGISTRY

    with pytest.raises(TypeError):
        LOADER_NAMESPACE_REGISTRY["cifsup"] = "https://example.org/changed#"  # type: ignore[index]
    with pytest.raises(TypeError):
        LOADER_NAMESPACE_REGISTRY["new"] = "https://example.org/new#"  # type: ignore[index]


def test_tracked_rdf_assets_use_only_neutral_or_w3c_iris() -> None:
    for path in RDF_ASSETS:
        graph = Graph().parse(path, format="turtle")
        for subject, predicate, obj in graph:
            for term in (subject, predicate, obj):
                if isinstance(term, URIRef):
                    _assert_neutral_term(term, path)


def test_runtime_and_yaml_assets_contain_no_legacy_uri_family() -> None:
    legacy = _legacy_uris()
    for path in TEXT_ASSETS:
        text = path.read_text(encoding="utf-8")
        assert not any(uri in text for uri in legacy), path


def test_logical_consumers_have_no_legacy_sap_aliases() -> None:
    legacy_alias = "".join((chr(115), chr(97), chr(112), ":"))
    for path in LOGICAL_CONSUMERS:
        text = path.read_text(encoding="utf-8")
        for marker in INTENTIONAL_LEGACY_FIXTURE_MARKERS.get(path, ()):
            text = text.replace(marker, "")
        assert legacy_alias not in text, path


def test_generated_graph_is_neutral_and_provenanced() -> None:
    graph = build_sap_support_graph()
    for subject, predicate, obj in graph:
        for term in (subject, predicate, obj):
            if isinstance(term, URIRef):
                _assert_neutral_term(term, Path("generated"))

    metadata = CIFMETAID["dataset-cifre-synthetic-support-ppms-v1"]
    assert (metadata, RDF.type, CIFMETA.SyntheticDataset) in graph
    assert (metadata, CIFMETA.sourceKind, None) in graph
    assert graph.value(metadata, CIFMETA.sourceKind).toPython() == "synthetic_fixture"
    assert graph.value(metadata, CIFMETA.official).toPython() is False
    assert graph.value(metadata, CIFMETA.datasetId).toPython() == "cifre-synthetic-support-ppms-v1"


def test_generated_graph_is_rdf_isomorphic_to_checked_in_support_graph() -> None:
    generated = build_sap_support_graph()
    checked_in = Graph().parse(ROOT / "semantic/data/sap_support_graph.ttl", format="turtle")
    assert isomorphic(generated, checked_in)


def test_generator_derives_instance_iris_from_cifdata() -> None:
    source = (ROOT / "src/semantic_layer/kg/sap_dataset_generator.py").read_text(encoding="utf-8")
    assert "https://example.org/cifre-kg/data/" not in source
    assert "CIFDATA[f\"" in source


def test_erp_skos_crosswalk_keeps_class_and_concept_disjoint() -> None:
    graph = Graph().parse(ROOT / "semantic/ontology/sap_erp.ttl", format="turtle")
    graph.parse(ROOT / "semantic/taxonomy/sap_products.ttl", format="turtle")
    entry = CIFMETAID["crosswalk-entry-product-automotive"]

    assert (entry, RDF.type, CIFMETA.CrosswalkEntry) in graph
    assert (entry, CIFMETA.sourceResource, CIFERP.ProductAutomotive) in graph
    assert (entry, CIFMETA.targetConcept, CIFSKOS.ProductAutomotive) in graph
    assert (entry, CIFMETA.crosswalkVersion, None) in graph
    assert (CIFSKOS.ProductAutomotive, RDF.type, Namespace("http://www.w3.org/2004/02/skos/core#").Concept) in graph
    assert (CIFSKOS.ProductAutomotive, RDF.type, OWL.Class) not in graph
    assert (CIFSKOS.ProductAutomotive, RDFS.subClassOf, None) not in graph
    assert (CIFERP.ProductAutomotive, RDF.type, OWL.Class) in graph


def test_invalid_support_fixture_has_synthetic_provenance() -> None:
    graph = Graph().parse(ROOT / "semantic/data/support-graph-invalid.ttl", format="turtle")
    metadata = CIFMETAID["dataset-cifre-synthetic-support-ppms-v1"]
    assert graph.value(metadata, CIFMETA.sourceKind).toPython() == "synthetic_fixture"
    assert graph.value(metadata, CIFMETA.official).toPython() is False
