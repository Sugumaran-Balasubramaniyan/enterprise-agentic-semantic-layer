"""W3C SPARQL 1.1 Synthesis Engine for SAP Enterprise Support.

Compiles logical query plans into standard, optimized SPARQL queries.
"""

from __future__ import annotations

from typing import ClassVar

from semantic_layer.reasoning.query_planner import LogicalQueryPlan


class TextToSPARQLEngine:
    """Translates logical graph plans into valid W3C SPARQL 1.1 queries."""

    STANDARD_PREFIXES: ClassVar[dict[str, str]] = {
        "ppms": "http://ontology.sap.com/ppms#",
        "sap": "http://ontology.sap.com/support#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
    }

    def compile(self, plan: LogicalQueryPlan) -> str:
        """Compile a logical plan into a complete SPARQL SELECT query."""
        prefix_lines = [f"PREFIX {alias}: <{uri}>" for alias, uri in self.STANDARD_PREFIXES.items()]

        # Unique select vars
        vars_str = " ".join(dict.fromkeys(plan.select_vars))

        pattern_lines = [f"    {p.subject} {p.predicate} {p.object_val} ." for p in plan.patterns]

        for opt in plan.optional_patterns:
            pattern_lines.append(f"    OPTIONAL {{ {opt.subject} {opt.predicate} {opt.object_val} . }}")

        filter_lines = [f"    FILTER ({f})" for f in plan.filters]

        body = "\n".join(pattern_lines + filter_lines)

        order_clause = f"\nORDER BY {plan.order_by}" if plan.order_by else ""
        limit_clause = f"\nLIMIT {plan.limit}" if plan.limit else ""

        query = (
            f"{chr(10).join(prefix_lines)}\n\n"
            f"SELECT DISTINCT {vars_str}\n"
            f"WHERE {{\n"
            f"{body}\n"
            f"}}{order_clause}{limit_clause}"
        )
        return query
