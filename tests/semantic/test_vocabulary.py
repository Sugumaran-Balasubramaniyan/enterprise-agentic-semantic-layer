from pathlib import Path

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
        "insurance:Risk",
        "insurance:Coverage",
        "insurance:Premium",
        "insurance:ClaimStatus",
        "insurance:Country",
        "insurance:ActivePolicy",
        "insurance:QualifyingClaim",
        "insurance:IncurredLoss",
    }
