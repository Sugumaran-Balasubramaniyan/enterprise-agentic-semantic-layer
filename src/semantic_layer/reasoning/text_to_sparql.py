"""Projection-safe W3C SPARQL 1.1 synthesis for CIFRE AQR plans."""

from __future__ import annotations

from typing import ClassVar

from semantic_layer.reasoning.query_planner import LogicalQueryPlan, TraversalPattern
from semantic_layer.research.contracts import NAMESPACE_REGISTRY


class TextToSPARQLEngine:
    """Translate a typed logical plan into deterministic SPARQL text."""

    # Dict insertion order is part of the public deterministic serialization
    # contract.  Keep neutral domain prefixes first, then W3C vocabulary.
    STANDARD_PREFIXES: ClassVar[dict[str, str]] = {
        "cifsup": NAMESPACE_REGISTRY["cifsup"],
        "cifppms": NAMESPACE_REGISTRY["cifppms"],
        "cifdata": NAMESPACE_REGISTRY["cifdata"],
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "owl": "http://www.w3.org/2002/07/owl#",
    }

    @staticmethod
    def _variables_in(pattern: TraversalPattern) -> set[str]:
        """Return variables bound by one triple pattern."""

        return {
            value
            for value in (pattern.subject, pattern.object_val)
            if value.startswith("?")
        }

    @staticmethod
    def _deduplicate(values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))

    def validate_projections(self, plan: LogicalQueryPlan) -> None:
        """Fail closed when a selected variable has no legal binding pattern."""

        selected = set(plan.select_vars)
        optional = set(plan.optional_variables)
        required = set(plan.required_variables) - optional

        # A manually constructed plan may predate the typed declarations.  A
        # selected variable is required unless it was explicitly marked
        # optional; no projection is silently discarded.
        unclassified = selected - required - optional
        required.update(unclassified)

        mandatory_bound: set[str] = set()
        for pattern in plan.patterns:
            mandatory_bound.update(self._variables_in(pattern))
        optional_bound: set[str] = set()
        for pattern in plan.optional_patterns:
            optional_bound.update(self._variables_in(pattern))

        missing_required = sorted(required - mandatory_bound)
        if missing_required:
            raise ValueError(
                "UNBOUND_REQUIRED_PROJECTION: " + ", ".join(missing_required)
            )

        missing_optional = sorted(optional - optional_bound)
        if missing_optional:
            raise ValueError(
                "UNBOUND_OPTIONAL_PROJECTION: " + ", ".join(missing_optional)
            )

        # Optional variables are allowed to occur only in OPTIONAL blocks. A
        # mandatory occurrence would turn a nullable answer field into a
        # required join and make RDFLib's unbound-row behavior observable.
        illegal_optional = sorted(optional & mandatory_bound)
        if illegal_optional:
            raise ValueError(
                "OPTIONAL_PROJECTION_IN_REQUIRED_PATTERN: "
                + ", ".join(illegal_optional)
            )

    @staticmethod
    def _render_pattern(pattern: TraversalPattern) -> str:
        return f"{pattern.subject} {pattern.predicate} {pattern.object_val} ."

    def compile(self, plan: LogicalQueryPlan) -> str:
        """Compile a logical plan after validating every projection binding."""

        self.validate_projections(plan)

        prefix_lines = [
            f"PREFIX {alias}: <{uri}>"
            for alias, uri in self.STANDARD_PREFIXES.items()
        ]

        # The planner supplies a canonical base-answer order followed by
        # qualifier projections. Preserve that order while removing repeats;
        # required/optional declaration arrays remain independently sorted.
        variables = list(dict.fromkeys(plan.select_vars))
        vars_str = " ".join(variables)

        pattern_lines: list[str] = []
        for pattern in self._deduplicate_patterns(plan.patterns):
            pattern_lines.append(f"    {self._render_pattern(pattern)}")

        for pattern in self._deduplicate_patterns(plan.optional_patterns):
            pattern_lines.append(
                f"    OPTIONAL {{ {self._render_pattern(pattern)} }}"
            )

        filter_lines: list[str] = []
        for expression in self._deduplicate(plan.filters):
            filter_lines.append(f"    FILTER ({expression})")

        body_lines = pattern_lines + filter_lines
        body = "\n".join(body_lines)
        if body:
            body += "\n"

        order_clause = f"\nORDER BY {plan.order_by}" if plan.order_by else ""
        limit_clause = f"\nLIMIT {plan.limit}" if plan.limit else ""

        return (
            "\n".join(prefix_lines)
            + "\n\n"
            + f"SELECT DISTINCT {vars_str}\n"
            + "WHERE {\n"
            + body
            + "}"
            + order_clause
            + limit_clause
        )

    @staticmethod
    def _deduplicate_patterns(patterns: list[TraversalPattern]) -> list[TraversalPattern]:
        """Deduplicate patterns while preserving the planner's stable order."""

        seen: set[tuple[str, str, str, bool]] = set()
        result: list[TraversalPattern] = []
        for pattern in patterns:
            key = (pattern.subject, pattern.predicate, pattern.object_val, pattern.optional)
            if key in seen:
                continue
            seen.add(key)
            result.append(pattern)
        return result
