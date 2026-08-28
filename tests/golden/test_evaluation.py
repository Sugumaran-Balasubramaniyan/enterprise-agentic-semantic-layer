"""Golden semantic-contract evaluation coverage."""

from pathlib import Path

from semantic_layer.evaluation import GOLDEN_CASES, load_golden_cases, run_evaluation
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
