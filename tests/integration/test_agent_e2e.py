"""End-to-end coverage for the deterministic investigation workflow."""

from pathlib import Path

import pytest

from semantic_layer.agents import ClaimsInvestigationAgent
from semantic_layer.models import CallerContext

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_QUESTION = (
    "Find French motor-insurance customers with at least three qualifying claims "
    "in the last 12 months and total incurred loss above EUR 20,000."
)


@pytest.fixture
def agent(tmp_path: Path) -> ClaimsInvestigationAgent:
    return ClaimsInvestigationAgent(REPOSITORY_ROOT, provenance_path=tmp_path / "provenance.sqlite")


def test_agent_returns_answer_plan_sql_and_provenance(agent: ClaimsInvestigationAgent) -> None:
    """Skipping a governed workflow stage would leave the answer untraceable."""

    answer = agent.answer(PRIMARY_QUESTION, CallerContext(role="ClaimsAnalystFR"))

    assert answer.authorization.allowed is True
    assert answer.plan.root_entity == "insurance:Customer"
    assert "SELECT" in answer.compiled_query.sql
    assert answer.quality.status == "PASS"
    assert answer.provenance.query_id
    assert answer.rows == [
        {"customer_id": "FR_001", "country": "FR", "claim_count": 3, "total_incurred_loss_eur": 24000.0},
        {"customer_id": "FR_002", "country": "FR", "claim_count": 3, "total_incurred_loss_eur": 25000.0},
    ]
    assert answer.stages == (
        "intent_parse",
        "resolve",
        "relationships_and_products",
        "authorize",
        "plan",
        "compile",
        "execute",
        "result_validation",
        "provenance",
        "answer_formatting",
    )


def test_agent_rejects_unsupported_customer_restriction(agent: ClaimsInvestigationAgent) -> None:
    with pytest.raises(ValueError, match="customer restrictions"):
        agent.answer(PRIMARY_QUESTION + " for customer FR_001", CallerContext(role="ClaimsAnalystFR"))


def test_denied_caller_stops_after_pre_authorization_before_final_plan(
    agent: ClaimsInvestigationAgent, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Moving authorization after plan creation would expose denied callers to later stages."""

    def later_stage(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("denied caller reached a final-plan or execution stage")

    monkeypatch.setattr(agent.tools, "build_query_plan", later_stage)
    monkeypatch.setattr(agent.tools, "execute_semantic_query", later_stage)
    monkeypatch.setattr(agent.tools, "record_provenance", later_stage)

    with pytest.raises(PermissionError, match="ROLE_DENIED") as error:
        agent.answer(PRIMARY_QUESTION, CallerContext(role="UnknownRole"))

    assert error.value.stages == (
        "intent_parse",
        "resolve",
        "relationships_and_products",
        "authorize",
    )
