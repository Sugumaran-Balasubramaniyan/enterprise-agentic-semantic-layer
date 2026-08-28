"""Golden semantic-contract evaluation coverage."""

from pathlib import Path

import pytest

from semantic_layer.evaluation import GOLDEN_CASES, load_golden_cases, run_evaluation
from semantic_layer.evaluation.runner import _evaluate_case
from semantic_layer.registry import SemanticRegistry

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_golden_suite_has_at_least_thirty_governed_questions() -> None:
    cases = load_golden_cases(GOLDEN_CASES)
    assert len(cases) >= 30

    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    report = run_evaluation(registry)

    assert report.total_cases == len(cases)
    assert report.failed_cases == []
    assert report.passed_cases == len(cases)


def test_golden_report_exposes_each_governance_dimension() -> None:
    report = run_evaluation(SemanticRegistry.from_repository(REPOSITORY_ROOT))

    assert report.resolution.total == report.total_cases
    assert report.relationships.total == report.total_cases
    assert report.products.total == report.total_cases
    assert report.metrics.total == report.total_cases
    assert report.authorization.total == report.total_cases
    assert report.deterministic_answers.total == report.total_cases


def test_primary_golden_answer_is_deterministic() -> None:
    report = run_evaluation(SemanticRegistry.from_repository(REPOSITORY_ROOT))

    primary = next(result for result in report.results if result.case_id == "primary-claims")
    assert primary.answer == [
        {"customer_id": "FR_001", "country": "FR", "claim_count": 3, "total_incurred_loss_eur": 24000.0},
        {"customer_id": "FR_002", "country": "FR", "claim_count": 3, "total_incurred_loss_eur": 25000.0},
    ]


def test_golden_questions_are_natural_language_unique() -> None:
    cases = load_golden_cases(GOLDEN_CASES)
    assert len({case.question for case in cases}) == len(cases)


@pytest.mark.parametrize("missing", ["concepts", "relationships", "products", "metrics", "authorization"])
def test_golden_loader_requires_every_governance_expectation(tmp_path: Path, missing: str) -> None:
    expected = {
        "concepts": [],
        "relationships": [],
        "products": [],
        "metrics": [],
        "authorization": {"allowed": True, "reason_code": "ALLOWED"},
    }
    del expected[missing]
    source = tmp_path / "questions.yaml"
    source.write_text(
        "questions:\n  - id: incomplete\n    question: A unique governed question\n    role: ClaimsAnalystFR\n    expected:\n"
        + "\n".join(f"      {key}: {value!r}" for key, value in expected.items()),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=f"missing expected field: {missing}"):
        load_golden_cases(source)


def test_secondary_constraints_reference_existing_semantic_assets() -> None:
    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    case = next(case for case in load_golden_cases(GOLDEN_CASES) if case.id == "secondary-01-active-french")
    case.expected["deterministic"]["answer_constraints"]["rule"] = "insurance:NotARealRule"

    result = _evaluate_case(case, registry, REPOSITORY_ROOT)

    assert result.deterministic_answer is False
    assert any("unknown governed rule" in error for error in result.errors)


def test_secondary_constraints_must_match_discovered_metric() -> None:
    registry = SemanticRegistry.from_repository(REPOSITORY_ROOT)
    case = next(case for case in load_golden_cases(GOLDEN_CASES) if case.id == "secondary-01-active-french")
    case.expected["deterministic"]["answer_constraints"]["metric"] = "insurance:ClaimsRatio"

    result = _evaluate_case(case, registry, REPOSITORY_ROOT)

    assert result.deterministic_answer is False
    assert any("not present in discovered metrics" in error for error in result.errors)
