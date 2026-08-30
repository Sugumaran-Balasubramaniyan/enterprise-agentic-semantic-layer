from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from semantic_layer.semantic_validation import load_vocabulary

ROOT = Path(__file__).parents[2]
VOCABULARY = ROOT / "semantic" / "vocabulary" / "insurance.yaml"


def test_claim_vocabulary_has_required_governance_metadata() -> None:
    claim = next(c for c in load_vocabulary(VOCABULARY) if c.id == "insurance:Claim")
    assert claim.version == "1.0.0"
    assert "Insurance Claim" in claim.synonyms
    assert claim.sensitivity.classification == "Confidential"


def test_vocabulary_contains_all_canonical_concepts() -> None:
    concepts = load_vocabulary(VOCABULARY)
    assert {concept.id for concept in concepts} == {
        "insurance:Customer",
        "insurance:Policy",
        "insurance:Claim",
        "insurance:InsuranceProduct",
        "insurance:MotorInsurance",
        "insurance:HomeInsurance",
        "insurance:Risk",
        "insurance:Coverage",
        "insurance:Premium",
        "insurance:ClaimStatus",
        "insurance:Country",
        "insurance:ActivePolicy",
        "insurance:QualifyingClaim",
        "insurance:IncurredLoss",
    }


def test_vocabulary_retains_document_governance_metadata() -> None:
    vocabulary = load_vocabulary(VOCABULARY)
    assert vocabulary.version == "1.0.0"
    assert vocabulary.namespace == "insurance"
    assert vocabulary.owner == "GlobalSure Insurance Group"
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

    customer = next(c for c in load_vocabulary(prerelease_path) if c.id == "insurance:Customer")
    assert customer.version == "1.0.0-rc.1"


def test_claim_relationships_use_canonical_object_targets() -> None:
    claim = next(c for c in load_vocabulary(VOCABULARY) if c.id == "insurance:Claim")
    relationships = {relationship.predicate: relationship.target for relationship in claim.relationships}
    assert relationships["insurance:hasClaimStatus"] == "insurance:ClaimStatus"
    assert relationships["insurance:hasIncurredLoss"] == "insurance:IncurredLoss"


def test_vocabulary_declares_canonical_customer_claim_and_policy_coverage_edges() -> None:
    """The vocabulary must express the Group relationship contract used by OWL and plans."""

    concepts = {concept.id: concept for concept in load_vocabulary(VOCABULARY)}
    customer_edges = {
        relationship.predicate: relationship.target
        for relationship in concepts["insurance:Customer"].relationships
    }
    policy_edges = {
        relationship.predicate: relationship.target
        for relationship in concepts["insurance:Policy"].relationships
    }

    assert customer_edges["insurance:ownsPolicy"] == "insurance:Policy"
    assert customer_edges["insurance:submitsClaim"] == "insurance:Claim"
    assert policy_edges["insurance:hasProduct"] == "insurance:InsuranceProduct"
    assert policy_edges["insurance:coversRisk"] == "insurance:Risk"
    assert policy_edges["insurance:hasCoverage"] == "insurance:Coverage"
