"""Synthetic SAP-inspired Knowledge Graph package.

Provides RDF/OWL graph management, SPARQL 1.1 execution, SHACL validation,
and deterministic synthetic dataset generation for SAP Service & Support concepts.
"""

from semantic_layer.kg.loader import SAPKnowledgeGraph

__all__ = ["SAPKnowledgeGraph"]
