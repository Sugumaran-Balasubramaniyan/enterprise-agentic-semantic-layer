from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from semantic_layer.semantic_validation import load_vocabulary

ROOT = Path(__file__).parents[2]
VOCABULARY = ROOT / "semantic" / "vocabulary" / "sap_erp.yaml"


def test_claim_vocabulary_has_required_governance_metadata() -> None:
    posting = next(c for c in load_vocabulary(VOCABULARY) if c.id == "ciferp:FinancialPosting")
    assert posting.version == "1.0.0"
    assert "Journal Entry" in posting.synonyms
    assert posting.sensitivity.classification == "Confidential"


def test_vocabulary_contains_all_canonical_concepts() -> None:
    concepts = load_vocabulary(VOCABULARY)
    assert {concept.id for concept in concepts} == {
        "ciferp:BusinessPartner",
        "ciferp:SalesOrder",
        "ciferp:FinancialPosting",
        "ciferp:Product",
        "ciferp:ProductAutomotive",
        "ciferp:ProductCommercial",
        "ciferp:Risk",
        "ciferp:Coverage",
        "ciferp:BillingDocument",
        "ciferp:PostingStatus",
        "ciferp:CompanyCode",
        "ciferp:ActiveSalesOrder",
        "ciferp:QualifyingPosting",
        "ciferp:FinancialLoss",
    }


def test_vocabulary_retains_document_governance_metadata() -> None:
    vocabulary = load_vocabulary(VOCABULARY)
    assert vocabulary.version == "1.0.0"
    assert vocabulary.namespace == "ciferp"
    assert vocabulary.owner == "repository-maintained synthetic contract"
    assert vocabulary.metadata.version == "1.0.0"


def test_vocabulary_rejects_non_semver_concept_version(tmp_path: Path) -> None:
    document = yaml.safe_load(VOCABULARY.read_text(encoding="utf-8"))
    document["concepts"][0]["version"] = "v1"
    invalid_path = tmp_path / "invalid-vocabulary.yaml"
    invalid_path.write_text(yaml.safe_dump(document), encoding="utf-8")

    with pytest.raises(ValidationError):
        load_vocabulary(invalid_path)


def test_vocabulary_rejects_leading_zero_numeric_prerelease(tmp_path: Path) -> None:
    document = yaml.safe_load(VOCABULARY.read_text(encoding="utf-8"))
    document["concepts"][0]["version"] = "1.0.0-01"
    invalid_path = tmp_path / "invalid-prerelease.yaml"
    invalid_path.write_text(yaml.safe_dump(document), encoding="utf-8")

    with pytest.raises(ValidationError):
        load_vocabulary(invalid_path)


def test_vocabulary_accepts_valid_semver_prerelease(tmp_path: Path) -> None:
    document = yaml.safe_load(VOCABULARY.read_text(encoding="utf-8"))
    document["concepts"][0]["version"] = "1.0.0-rc.1"
    prerelease_path = tmp_path / "prerelease-vocabulary.yaml"
    prerelease_path.write_text(yaml.safe_dump(document), encoding="utf-8")

    bp = next(c for c in load_vocabulary(prerelease_path) if c.id == "ciferp:BusinessPartner")
    assert bp.version == "1.0.0-rc.1"


def test_claim_relationships_use_canonical_object_targets() -> None:
    posting = next(c for c in load_vocabulary(VOCABULARY) if c.id == "ciferp:FinancialPosting")
    relationships = {relationship.predicate: relationship.target for relationship in posting.relationships}
    assert relationships["ciferp:hasPostingStatus"] == "ciferp:PostingStatus"
    assert relationships["ciferp:hasFinancialLoss"] == "ciferp:FinancialLoss"


def test_vocabulary_declares_canonical_customer_claim_and_policy_coverage_edges() -> None:
    """The vocabulary must express the Group relationship contract used by OWL and plans."""

    concepts = {concept.id: concept for concept in load_vocabulary(VOCABULARY)}
    bp_edges = {
        relationship.predicate: relationship.target
        for relationship in concepts["ciferp:BusinessPartner"].relationships
    }
    order_edges = {
        relationship.predicate: relationship.target
        for relationship in concepts["ciferp:SalesOrder"].relationships
    }

    assert bp_edges["ciferp:hasSalesOrder"] == "ciferp:SalesOrder"
    assert bp_edges["ciferp:hasFinancialPosting"] == "ciferp:FinancialPosting"
    assert order_edges["ciferp:hasProduct"] == "ciferp:Product"
    assert order_edges["ciferp:coversRisk"] == "ciferp:Risk"
    assert order_edges["ciferp:hasCoverage"] == "ciferp:Coverage"
