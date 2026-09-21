"""Research-contract tests for binding-derived answers and provenance."""

from __future__ import annotations

from dataclasses import dataclass

from semantic_layer.reasoning.reflective_agent import AQRReflectiveAgent
from semantic_layer.research.contracts import ReasonCode, Status


@dataclass
class BindingKnowledgeGraph:
    rows: list[dict[str, object]]

    def query_sparql(self, query: str) -> list[dict[str, object]]:
        return list(self.rows)


def test_answer_and_citations_are_binding_derived_and_synthetic() -> None:
    result = AQRReflectiveAgent(
        BindingKnowledgeGraph(
            [
                {
                    "note": "https://example.org/cifre-kg/data/support/note/3345100",
                    "noteNumber": "3345100",
                    "title": "Synthetic connection remediation",
                    "priority": "Very High",
                }
            ]
        )
    ).run("Which note resolves alert DBSQL_NO_MORE_CONNECTION?")

    assert result.status is Status.SUCCESS
    assert result.reason_code is ReasonCode.NONE
    assert result.predicted_note_numbers == ["3345100"]
    assert result.provenance["dataset_id"] == "cifre-synthetic-support-ppms-v1"
    assert result.provenance["official"] is False
    assert result.provenance["citation"].startswith(
        "Synthetic fixture cifre-synthetic-support-ppms-v1; not official data."
    )
    assert "Synthetic connection remediation" in result.answer
    assert "3345100" in result.answer
    assert "SAP Note" not in result.answer
    assert "SAP Note" not in str(result.provenance)


def test_unsupported_and_error_paths_have_no_factual_answer() -> None:
    unsupported = AQRReflectiveAgent(BindingKnowledgeGraph([])).run(
        "Find notes for an invented alert NEVER_SEEN"
    )
    assert unsupported.status is Status.UNSUPPORTED
    assert unsupported.answer == ""
    assert unsupported.bindings == []
    assert unsupported.predicted_note_numbers == []

    class BrokenKnowledgeGraph:
        def query_sparql(self, query: str) -> list[dict[str, object]]:
            raise RuntimeError("connection password=secret")

    failed = AQRReflectiveAgent(BrokenKnowledgeGraph()).run(
        "Which note resolves alert TIME_OUT?"
    )
    assert failed.status is Status.EXECUTION_ERROR
    assert failed.answer == ""
    assert failed.bindings == []
    assert failed.predicted_note_numbers == []


def test_relaxed_candidates_are_disclosed_separately_from_strict_answer() -> None:
    class RelaxedKnowledgeGraph:
        def __init__(self) -> None:
            self.calls = 0

        def query_sparql(self, query: str) -> list[dict[str, object]]:
            self.calls += 1
            if self.calls == 1:
                return []
            return [
                {
                    "note": "https://example.org/cifre-kg/data/support/note/3201440",
                    "noteNumber": "3201440",
                    "title": "Synthetic timeout candidate",
                }
            ]

    result = AQRReflectiveAgent(RelaxedKnowledgeGraph()).run(
        "Find notes for alert TIME_OUT in component MM-PUR-PO at SP05"
    )

    assert result.status is Status.EMPTY_RESULT
    assert result.answer_scope == "relaxed_candidates"
    assert result.bindings == []
    assert result.predicted_note_numbers == []
    assert result.relaxed_candidates[0]["noteNumber"] == "3201440"
    assert "3201440" in result.answer
    assert "candidate" in result.answer.lower()
