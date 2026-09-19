"""Integration tests for AQRReflectiveAgent execution, multi-hop reasoning, and self-correction."""

from __future__ import annotations

import pytest

from semantic_layer.kg.loader import SAPKnowledgeGraph
from semantic_layer.reasoning.reflective_agent import AQRReflectiveAgent


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
    query = "Which SAP Note resolves dump TSV_TNEW_PAGE_ALLOC_FAILED on S/4HANA 2023 in component FI-GL?"
    result = agent.run(query)

    assert len(result.results) >= 1
    found_nums = [r.get("noteNumber") for r in result.results]
    assert "3109922" in found_nums
    assert "SAP Note 3109922" in result.provenance_citations
    assert "ACDOCA" in result.answer


def test_agent_prerequisite_chain_traversal(agent: AQRReflectiveAgent) -> None:
    query = "What are the prerequisite notes required for SAP Note 3109922?"
    result = agent.run(query)

    assert len(result.results) == 1
    assert result.results[0].get("noteNumber") == "3098110"
    assert "Memory paging buffer expansion" in result.results[0].get("title", "")


def test_agent_reflective_self_correction_recovery(agent: AQRReflectiveAgent) -> None:
    query = "Find notes for alert TIME_OUT in component MM-PUR-PO at SP05"
    result = agent.run(query)

    assert result.recovery_succeeded is True
    assert len(result.reflection_history) >= 1
    assert result.reflection_history[0].failure_type == "EMPTY_RESULT"
    found_nums = [r.get("noteNumber") for r in result.results]
    assert "3201440" in found_nums
