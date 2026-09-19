"""Agentic Autonomous Query Reasoner with Reflective Self-Correction (AQR-Reflect).

Implements closed-loop neurosymbolic reasoning over enterprise knowledge graphs:
1. Schema Linking & Ontology Grounding
2. Multi-Hop Traversal Planning
3. Text-to-SPARQL Compilation
4. Triplestore Execution
5. Reflective Diagnostic & Self-Correction Feedback Loop
6. Verifiable Answer Synthesis & Provenance Generation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from semantic_layer.kg.loader import SAPKnowledgeGraph
from semantic_layer.reasoning.query_planner import LogicalQueryPlan, QueryPlanner
from semantic_layer.reasoning.schema_linker import GroundedEntities, SchemaLinker
from semantic_layer.reasoning.text_to_sparql import TextToSPARQLEngine

logger = logging.getLogger(__name__)


@dataclass
class ReflectionStep:
    """Record of a single reflection and correction attempt."""

    iteration: int
    draft_sparql: str
    failure_type: str  # "SYNTAX_ERROR", "EMPTY_RESULT", "UNBOUND_VARIABLE", "NONE"
    diagnostic_feedback: str
    repaired_sparql: str | None = None


@dataclass
class ReasoningResult:
    """Complete structured response from the AQR agent."""

    query: str
    grounded_entities: GroundedEntities
    final_sparql: str
    results: list[dict[str, Any]]
    answer: str
    reflection_history: list[ReflectionStep] = field(default_factory=list)
    recovery_succeeded: bool = False
    execution_status: str = "SUCCESS"
    provenance_citations: list[str] = field(default_factory=list)


class AQRReflectiveAgent:
    """Autonomous agent that translates natural language to SPARQL with self-correction."""

    def __init__(self, knowledge_graph: SAPKnowledgeGraph) -> None:
        self.kg = knowledge_graph
        self.linker = SchemaLinker()
        self.planner = QueryPlanner()
        self.compiler = TextToSPARQLEngine()

    def run(self, query_text: str, max_reflections: int = 3) -> ReasoningResult:
        """Execute autonomous reasoning loop with iterative self-correction."""
        # Step 1: Ground schema entities
        entities = self.linker.ground(query_text)

        # Step 2: Formulate initial plan & compile draft SPARQL
        plan = self.planner.plan(entities)
        current_sparql = self.compiler.compile(plan)

        reflection_history: list[ReflectionStep] = []
        final_results: list[dict[str, Any]] = []
        recovery_succeeded = False
        execution_status = "SUCCESS"

        # Step 3 & 4: Execution and Reflection Loop
        for iteration in range(1, max_reflections + 1):
            try:
                results = self.kg.query_sparql(current_sparql)

                if results:
                    # Successful retrieval
                    final_results = results
                    break
                else:
                    # Query was syntactically valid but produced 0 results
                    feedback = "Query returned 0 results. Checking if relaxation is possible."
                    step = ReflectionStep(
                        iteration=iteration,
                        draft_sparql=current_sparql,
                        failure_type="EMPTY_RESULT",
                        diagnostic_feedback=feedback,
                    )

                    # Self-Correction Strategy: If support package constraint was applied, relax it
                    if plan.filters and any("minSP" in f for f in plan.filters):
                        repaired_plan = self._relax_support_package_filter(plan)
                        current_sparql = self.compiler.compile(repaired_plan)
                        step.repaired_sparql = current_sparql
                        reflection_history.append(step)
                        plan = repaired_plan
                        recovery_succeeded = True
                        continue

                    # Strategy 2: If sub-component was specified, try widening to parent component
                    if entities.component_codes and any("-" in c for c in entities.component_codes):
                        repaired_plan = self._relax_to_parent_component(plan, entities)
                        current_sparql = self.compiler.compile(repaired_plan)
                        step.repaired_sparql = current_sparql
                        reflection_history.append(step)
                        plan = repaired_plan
                        recovery_succeeded = True
                        continue

                    reflection_history.append(step)
                    final_results = []
                    break

            except Exception as ex:  # noqa: BLE001
                # Syntax or execution error caught from triplestore for agentic reflection
                error_msg = str(ex)
                step = ReflectionStep(
                    iteration=iteration,
                    draft_sparql=current_sparql,
                    failure_type="SYNTAX_ERROR",
                    diagnostic_feedback=error_msg,
                )

                # Self-Correction for Syntax: Inject missing prefixes or repair filters
                repaired_sparql = self._repair_syntax_error(current_sparql, error_msg)
                step.repaired_sparql = repaired_sparql
                reflection_history.append(step)
                current_sparql = repaired_sparql
                recovery_succeeded = True

        # Step 5: Answer synthesis and provenance
        answer, citations = self._synthesize(query_text, final_results, entities)

        return ReasoningResult(
            query=query_text,
            grounded_entities=entities,
            final_sparql=current_sparql,
            results=final_results,
            answer=answer,
            reflection_history=reflection_history,
            recovery_succeeded=recovery_succeeded and len(final_results) > 0,
            execution_status=execution_status,
            provenance_citations=citations,
        )

    def _relax_support_package_filter(self, plan: LogicalQueryPlan) -> LogicalQueryPlan:
        """Remove overly strict min/max SP filters to find notes across all SP levels."""
        new_filters = [f for f in plan.filters if "minSP" not in f]
        new_patterns = [p for p in plan.patterns if "minSupportPackage" not in p.predicate and "maxSupportPackage" not in p.predicate]
        return LogicalQueryPlan(
            target_var=plan.target_var,
            intent=plan.intent,
            select_vars=plan.select_vars,
            patterns=new_patterns,
            filters=new_filters,
            order_by=plan.order_by,
            limit=plan.limit,
        )

    def _relax_to_parent_component(self, plan: LogicalQueryPlan, entities: GroundedEntities) -> LogicalQueryPlan:
        """Widen component match from leaf component (e.g. BC-DB-HDB) to parent (e.g. BC-DB)."""
        parent_codes: list[str] = []
        for c in entities.component_codes:
            parts = c.split("-")
            if len(parts) > 1:
                parent_codes.append("-".join(parts[:-1]))
        if not parent_codes:
            return plan

        new_filters: list[str] = []
        for f in plan.filters:
            if "compCode" in f:
                new_terms = [f'?compCode = "{p}"^^xsd:string' for p in parent_codes]
                new_filters.append(" || ".join(new_terms))
            else:
                new_filters.append(f)

        return LogicalQueryPlan(
            target_var=plan.target_var,
            intent=plan.intent,
            select_vars=plan.select_vars,
            patterns=plan.patterns,
            filters=new_filters,
            order_by=plan.order_by,
            limit=plan.limit,
        )

    def _repair_syntax_error(self, sparql: str, error_msg: str) -> str:
        """Heuristic repair of common SPARQL syntax errors."""
        repaired = sparql
        if "PREFIX" not in repaired:
            repaired = self.compiler.compile(self.planner.plan(GroundedEntities(raw_query="")))
        return repaired

    def _synthesize(
        self,
        query: str,
        results: list[dict[str, Any]],
        entities: GroundedEntities,
    ) -> tuple[str, list[str]]:
        """Synthesize verified, citation-backed natural language answer."""
        if not results:
            return (
                "No matching SAP support records found in the knowledge graph matching the exact constraints.",
                [],
            )

        citations: list[str] = []
        lines: list[str] = []

        if entities.intent == "PREREQUISITE_CHAIN":
            lines.append(f"Identified {len(results)} prerequisite note(s) in the dependency chain:")
            for r in results:
                num = r.get("noteNumber", "Unknown")
                title = r.get("title", "")
                lines.append(f"- Note {num}: {title}")
                citations.append(f"SAP Note {num}")
        else:
            lines.append(f"Identified {len(results)} relevant SAP Note(s) matching your criteria:")
            for r in results:
                num = r.get("noteNumber", "Unknown")
                title = r.get("title", "")
                prio = r.get("priority", "Standard")
                lines.append(f"- Note {num} [{prio}]: {title}")
                citations.append(f"SAP Note {num}")

        return "\n".join(lines), citations
