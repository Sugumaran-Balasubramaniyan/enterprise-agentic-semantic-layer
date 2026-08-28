"""Regression tests for final semantic-layer readiness boundaries."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from semantic_layer.evaluation import GOLDEN_CASES, load_golden_cases, run_evaluation, runner
from semantic_layer.registry import SemanticRegistry

ROOT = Path(__file__).resolve().parents[2]


def test_explicit_answer_evaluation_uses_evidence_checked_executor(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = SemanticRegistry.from_repository(ROOT)
    case = next(case for case in load_golden_cases(GOLDEN_CASES) if case.id == "primary-claims")
    called = False

    def fake_execute(*_args: object, **_kwargs: object) -> tuple[list[dict[str, object]], list[str]]:
        nonlocal called
        called = True
        return list(case.deterministic.answer or ()), []

    monkeypatch.setattr(runner, "_execute_case", fake_execute)
    result = runner._evaluate_case(case, registry, ROOT)

    assert called is True
    assert result.deterministic_answer is True


def test_rows_only_fake_execution_result_fails_deterministic_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = SemanticRegistry.from_repository(ROOT)
    case = next(case for case in load_golden_cases(GOLDEN_CASES) if case.id == "primary-claims")

    class FakeAgent:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def answer(self, *_args: object, **_kwargs: object) -> object:
            return SimpleNamespace(rows=list(case.deterministic.answer or ()))

    monkeypatch.setattr(runner, "ClaimsInvestigationAgent", FakeAgent)
    result = runner._evaluate_case(case, registry, ROOT)

    assert result.deterministic_answer is False
    assert any("evidence" in error for error in result.errors)


def test_discovery_only_denominator_includes_failed_applicable_cases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = SemanticRegistry.from_repository(ROOT)

    def fail_discovery_case(case: object, *_args: object) -> runner.CaseEvaluation:
        typed_case = case
        constraints = typed_case.deterministic.answer_constraints  # type: ignore[attr-defined]
        discovery_only = isinstance(constraints, dict) and constraints.get("mode") == "discovery_only"
        return runner.CaseEvaluation(
            case_id=typed_case.id,  # type: ignore[attr-defined]
            resolution=False,
            relationships=False,
            products=False,
            metrics=False,
            authorization=False,
            deterministic_answer=False,
            discovery_only=discovery_only,
        )

    monkeypatch.setattr(runner, "_evaluate_case", fail_discovery_case)
    report = run_evaluation(registry)

    assert report.discovery_only.total == 10
    assert report.discovery_only.passed == 0
