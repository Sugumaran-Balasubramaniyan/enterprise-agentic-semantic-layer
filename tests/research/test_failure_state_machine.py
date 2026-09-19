"""Research-contract tests for the bounded AQR failure lifecycle."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from semantic_layer.reasoning.reflective_agent import (
    AQRReflectiveAgent,
    RepairOperation,
    sanitize_diagnostic,
)
from semantic_layer.research.contracts import ReasonCode, Status


@dataclass
class FakeKnowledgeGraph:
    """Small deterministic KG double that exposes actual query attempts."""

    responses: list[object]

    def __post_init__(self) -> None:
        self.calls: list[str] = []

    def query_sparql(self, query: str) -> list[dict[str, object]]:
        self.calls.append(query)
        response = self.responses[min(len(self.calls) - 1, len(self.responses) - 1)]
        if isinstance(response, BaseException):
            raise response
        return response  # type: ignore[return-value]


def test_bounded_execution_records_initial_and_three_repairs() -> None:
    kg = FakeKnowledgeGraph(
        [RuntimeError("password=super-secret token=Bearer abcdef")] * 4
    )
    result = AQRReflectiveAgent(kg).run(
        "Find notes for alert TIME_OUT in component MM-PUR-PO at SP05"
    )

    assert result.status is Status.EXECUTION_ERROR
    assert result.reason_code is ReasonCode.REPAIR_BUDGET_EXHAUSTED
    assert result.attempts == 4
    assert [op.attempt_index for op in result.repair.operations] == [0, 1, 2, 3]
    assert [op.operation_kind for op in result.repair.operations] == [
        "initial",
        "execution_repair",
        "execution_repair",
        "execution_repair",
    ]
    assert all(isinstance(op, RepairOperation) for op in result.repair.operations)
    assert all(len(op.diagnostic) <= 512 for op in result.repair.operations)
    assert all("super-secret" not in op.diagnostic for op in result.repair.operations)
    assert all(op.sparql_text for op in result.repair.operations)


def test_no_reflection_empty_is_final_strict_empty() -> None:
    kg = FakeKnowledgeGraph([[]])
    result = AQRReflectiveAgent(kg).run(
        "Find notes for alert TIME_OUT in component MM-PUR-PO at SP05",
        condition="deterministic_no_reflection_ablation",
    )

    assert result.status is Status.EMPTY_RESULT
    assert result.reason_code is ReasonCode.EMPTY_STRICT_RESULT
    assert result.attempts == 1
    assert result.repair.recovered is False
    assert [op.attempt_index for op in result.repair.operations] == [0]
    assert result.answer_scope == "none"


def test_syntax_repair_can_recover_strict_bindings() -> None:
    kg = FakeKnowledgeGraph(
        [
            SyntaxError("fixed parser diagnostic"),
            [{"note": "urn:note:3345100", "noteNumber": "3345100", "title": "Synthetic note"}],
        ]
    )
    result = AQRReflectiveAgent(kg).run("Which note resolves alert TIME_OUT?")

    assert result.status is Status.SUCCESS
    assert result.reason_code is ReasonCode.NONE
    assert result.attempts == 2
    assert result.repair.recovered is True
    assert result.repair.recovery_attempt == 1
    assert result.repair.recovery_success is True
    assert [op.operation_kind for op in result.repair.operations] == [
        "initial",
        "syntax_repair",
    ]


def test_relaxed_candidates_never_become_strict_success() -> None:
    kg = FakeKnowledgeGraph(
        [
            [],
            [],
            [{"note": "urn:note:3201440", "noteNumber": "3201440", "title": "Synthetic note"}],
        ]
    )
    result = AQRReflectiveAgent(kg).run(
        "Find notes for alert TIME_OUT in component MM-PUR-PO at SP05"
    )

    assert result.status is Status.EMPTY_RESULT
    assert result.reason_code is ReasonCode.WIDEN_COMPONENT
    assert result.answer_scope == "relaxed_candidates"
    assert result.attempts == 3
    assert result.bindings == []
    assert result.predicted_note_numbers == []
    assert result.relaxed_candidates[0]["noteNumber"] == "3201440"
    assert result.original_constraints["support_package"] == [5]
    assert result.original_constraints["component_code"] == ["MM-PUR-PO"]
    assert [op.changed_constraints for op in result.repair.operations] == [
        [],
        ["support_package"],
        ["component"],
    ]


def test_no_op_repair_is_explicit_and_diagnostic_is_bounded() -> None:
    kg = FakeKnowledgeGraph([SyntaxError("syntax error")])
    agent = AQRReflectiveAgent(kg)
    agent._repair_syntax_error = lambda sparql, error: sparql  # type: ignore[method-assign]

    result = agent.run("Which SAP Note resolves alert TIME_OUT?")

    assert result.status is Status.SYNTAX_ERROR
    assert result.reason_code is ReasonCode.NO_OP_REPAIR
    assert result.attempts == 1
    assert result.repair.operations[-1].reason_code is ReasonCode.NO_OP_REPAIR
    assert len(sanitize_diagnostic("x" * 600)) == 512


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        (Status.SUCCESS, ReasonCode.NONE),
        (Status.UNSUPPORTED, ReasonCode.UNKNOWN_TOKEN),
        (Status.SYNTAX_ERROR, ReasonCode.SPARQL_SYNTAX),
        (Status.EXECUTION_ERROR, ReasonCode.SPARQL_EXECUTION),
        (Status.EMPTY_RESULT, ReasonCode.EMPTY_STRICT_RESULT),
    ],
)
def test_final_status_reason_pairs_are_closed(status: Status, reason: ReasonCode) -> None:
    """Keep the test module's contract vocabulary explicit for reviewers."""

    assert status.value in {item.value for item in Status}
    assert reason.value in {item.value for item in ReasonCode}
