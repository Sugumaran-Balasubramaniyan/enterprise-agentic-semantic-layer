"""Integration tests for AQRReflectiveAgent execution, multi-hop reasoning, and self-correction."""

from __future__ import annotations

import pytest

from semantic_layer.kg.loader import SAPKnowledgeGraph
from semantic_layer.reasoning.reflective_agent import AQRReflectiveAgent
from semantic_layer.research.contracts import ReasonCode, Status


@pytest.fixture
def agent() -> AQRReflectiveAgent:
    kg = SAPKnowledgeGraph()
    kg.load_ontologies([
        "semantic/ontology/sap_ppms.ttl",
        "semantic/ontology/sap_support.ttl",
        "semantic/data/sap_support_graph.ttl",
    ])
    return AQRReflectiveAgent(kg)


def test_agent_multihop_resolution(agent: AQRReflectiveAgent) -> None:
    # The closed grammar requires the alert cue; retain the same scenario while
    # migrating the legacy integration surface to the typed result contract.
    query = "Which SAP Note resolves alert TSV_TNEW_PAGE_ALLOC_FAILED on S/4HANA 2023 in component FI-GL?"
    result = agent.run(query)

    assert result.status is Status.SUCCESS
    assert result.reason_code is ReasonCode.NONE
    assert len(result.bindings) >= 1
    found_nums = [r.get("noteNumber") for r in result.bindings]
    assert "3109922" in found_nums
    assert result.provenance["official"] is False
    assert result.provenance["dataset_id"] == "cifre-synthetic-support-ppms-v1"
    assert "ACDOCA" in result.answer


def test_agent_prerequisite_chain_traversal(agent: AQRReflectiveAgent) -> None:
    query = "What are the prerequisite notes required for SAP Note 3109922?"
    result = agent.run(query)

    assert result.status is Status.SUCCESS
    assert result.reason_code is ReasonCode.NONE
    found_nums = {row.get("noteNumber") for row in result.bindings}
    assert {"3012445", "3098110"}.issubset(found_nums)
    assert any("Memory paging buffer expansion" in row.get("title", "") for row in result.bindings)


def test_agent_reflective_self_correction_recovery(agent: AQRReflectiveAgent) -> None:
    query = "Find notes for alert TIME_OUT in component MM-PUR-PO at SP05"
    result = agent.run(query)

    assert result.status is Status.EMPTY_RESULT
    assert result.reason_code is ReasonCode.RELAX_SUPPORT_PACKAGE
    assert result.answer_scope == "relaxed_candidates"
    assert result.repair.recovery_success is False
    found_nums = [r.get("noteNumber") for r in result.relaxed_candidates]
    assert "3201440" in found_nums
    assert result.bindings == []
    assert result.predicted_note_numbers == []
