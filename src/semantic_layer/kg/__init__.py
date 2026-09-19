"""SAP Knowledge Graph package.

Provides RDF/OWL graph management, SPARQL 1.1 execution, SHACL validation,
and high-fidelity enterprise dataset generation for SAP Service & Support.
"""

from semantic_layer.kg.loader import SAPKnowledgeGraph

__all__ = ["SAPKnowledgeGraph"]
