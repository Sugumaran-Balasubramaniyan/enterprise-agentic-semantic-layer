"""Autonomous Query Reasoning (AQR) Package for SAP Enterprise Knowledge Graph.

Provides ontology grounding, multi-hop query planning, Text-to-SPARQL generation,
and reflective agentic self-correction over W3C RDF triplestores.
"""

from semantic_layer.reasoning.reflective_agent import AQRReflectiveAgent, ReasoningResult
from semantic_layer.reasoning.schema_linker import SchemaLinker
from semantic_layer.reasoning.text_to_sparql import TextToSPARQLEngine

__all__ = [
    "AQRReflectiveAgent",
    "ReasoningResult",
    "SchemaLinker",
    "TextToSPARQLEngine",
]
