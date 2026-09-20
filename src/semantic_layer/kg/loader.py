"""W3C RDF/OWL Knowledge Graph Manager for SAP Enterprise Support.

Handles ontology loading, triplestore querying via SPARQL 1.1, and
SHACL validation with pyshacl.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pyshacl
import rdflib
import yaml
from rdflib import Graph, Namespace, URIRef
from rdflib.plugins.sparql.processor import SPARQLResult

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class ValidationReport:
    """Structured SHACL result with an explicit validation scope."""

    conforms: bool
    report_text: str
    shapes_path: Path
    scope: str = "support"
    inference: str = "rdfs"

    def __iter__(self):
        """Retain the historical ``conforms, report`` unpacking API."""

        yield self.conforms
        yield self.report_text


class SAPKnowledgeGraph:
    """Enterprise Knowledge Graph engine backed by RDFLib."""

    def __init__(self) -> None:
        self.graph = Graph()
        self._bind_standard_namespaces()

    def _bind_standard_namespaces(self) -> None:
        """Bind common prefixes for clean serialization and SPARQL parsing."""
        self.graph.bind("cifsup", CIFSUP)
        self.graph.bind("cifppms", CIFPPMS)
        self.graph.bind("cifdata", CIFDATA)
        self.graph.bind("ciferp", CIFERP)
        self.graph.bind("cifskos", CIFSKOS)
        self.graph.bind("cifmeta", CIFMETA)
        self.graph.bind("cifmetaid", CIFMETAID)
        self.graph.bind("rdf", rdflib.RDF)
        self.graph.bind("rdfs", rdflib.RDFS)
        self.graph.bind("owl", rdflib.OWL)
        self.graph.bind("xsd", rdflib.XSD)
        self.graph.bind("sh", Namespace("http://www.w3.org/ns/shacl#"))

    def load_file(self, file_path: str | Path, format: str = "turtle") -> int:
        """Load an RDF file into the graph. Returns total triple count."""
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"Knowledge graph file not found: {p}")
        self.graph.parse(location=str(p), format=format)
        return len(self.graph)

    def load_ontologies(self, paths: list[str | Path]) -> int:
        """Load multiple ontology and data files."""
        for path in paths:
            self.load_file(path)
        return len(self.graph)

    def validate_shacl(
        self, shapes_path: str | Path, *, scope: str = "support"
    ) -> ValidationReport:
        """Validate current graph against W3C SHACL shapes.

        Returns a structured report and preserves tuple unpacking for callers
        written against the original loader API.
        """
        if scope not in {"support", "erp", "combined"}:
            raise ValueError("scope must be one of: support, erp, combined")
        shapes_p = Path(shapes_path)
        if not shapes_p.exists():
            raise FileNotFoundError(f"SHACL shapes file not found: {shapes_p}")

        shapes_graph = Graph()
        shapes_graph.parse(location=str(shapes_p), format="turtle")

        conforms, _, results_text = pyshacl.validate(
            data_graph=self.graph,
            shacl_graph=shapes_graph,
            inference="rdfs",
            abort_on_first=False,
            meta_shacl=False,
            advanced=False,
            js=False,
            debug=False,
        )
        return ValidationReport(
            conforms=bool(conforms),
            report_text=str(results_text),
            shapes_path=shapes_p,
            scope=scope,
        )

    def query_sparql(self, sparql_query: str) -> list[dict[str, Any]]:
        """Execute a SPARQL 1.1 SELECT query and return list of variable bindings."""
        prepared_query = self._ensure_prefixes(sparql_query)
        result = self.graph.query(prepared_query)

        if not isinstance(result, SPARQLResult):
            return []

        rows: list[dict[str, Any]] = []
        for binding in result.bindings:
            row: dict[str, Any] = {}
            for var, term in binding.items():
                var_name = str(var)
                if isinstance(term, URIRef):
                    row[var_name] = str(term)
                elif isinstance(term, rdflib.Literal):
                    row[var_name] = term.toPython()
                else:
                    row[var_name] = str(term)
            rows.append(row)
        return rows

    def query_ask(self, sparql_query: str) -> bool:
        """Execute a SPARQL ASK query returning boolean."""
        prepared_query = self._ensure_prefixes(sparql_query)
        result = self.graph.query(prepared_query)
        return bool(result.askAnswer)

    def _ensure_prefixes(self, query: str) -> str:
        """Inject standard prefixes if missing from the query."""
        prefixes = [
            f"PREFIX cifsup: <{CIFSUP}>",
            f"PREFIX cifppms: <{CIFPPMS}>",
            f"PREFIX cifdata: <{CIFDATA}>",
            f"PREFIX ciferp: <{CIFERP}>",
            f"PREFIX cifskos: <{CIFSKOS}>",
            f"PREFIX cifmeta: <{CIFMETA}>",
            f"PREFIX cifmetaid: <{CIFMETAID}>",
            "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>",
            "PREFIX owl: <http://www.w3.org/2002/07/owl#>",
            "PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>",
        ]
        missing_prefixes = [p for p in prefixes if p.split()[1] not in query]
        if missing_prefixes:
            return "\n".join(missing_prefixes) + "\n\n" + query
        return query

    def serialize(self, destination: str | Path | None = None, format: str = "turtle") -> str:
        """Serialize graph to string or file."""
        if destination:
            p = Path(destination)
            p.parent.mkdir(parents=True, exist_ok=True)
            self.graph.serialize(destination=str(p), format=format)
            return str(p)
        return self.graph.serialize(format=format)

    def __len__(self) -> int:
        return len(self.graph)


def _load_namespace_registry() -> Mapping[str, str]:
    """Load Task 2's registry, with a dependency-light local fallback.

    Importing ``semantic_layer.research.contracts`` normally exposes the
    canonical registry.  The shared checkout environment used for semantic
    asset checks may intentionally omit the optional JSON Schema dependency,
    so read the checked-in provenance contract only for that environment
    bootstrap case.  No namespace literals are duplicated here.
    """

    try:
        from semantic_layer.research.contracts import NAMESPACE_REGISTRY
    except ModuleNotFoundError as error:
        if error.name != "jsonschema":
            raise
        provenance_path = Path(__file__).resolve().parents[3] / "semantic/provenance/synthetic_source.yaml"
        document = yaml.safe_load(provenance_path.read_text(encoding="utf-8"))
        return MappingProxyType(dict(document["namespace_registry"]))
    return NAMESPACE_REGISTRY


NAMESPACE_REGISTRY = _load_namespace_registry()
CIFSUP = Namespace(NAMESPACE_REGISTRY["cifsup"])
CIFPPMS = Namespace(NAMESPACE_REGISTRY["cifppms"])
CIFDATA = Namespace(NAMESPACE_REGISTRY["cifdata"])
CIFERP = Namespace(NAMESPACE_REGISTRY["ciferp"])
CIFSKOS = Namespace(NAMESPACE_REGISTRY["cifskos"])
CIFMETA = Namespace(NAMESPACE_REGISTRY["cifmeta"])
CIFMETAID = Namespace(NAMESPACE_REGISTRY["cifmetaid"])
