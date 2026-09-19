"""Multi-Hop Query Planner for SAP Knowledge Graph.

Deconstructs grounded user intent into formal graph traversal patterns,
specifying entity joins, version bounds, and dependency chaining.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from semantic_layer.reasoning.schema_linker import GroundedEntities


@dataclass
class TraversalPattern:
    """Single triple pattern or join in SPARQL graph traversal."""

    subject: str
    predicate: str
    object_val: str


@dataclass
class LogicalQueryPlan:
    """Formal logical plan before SPARQL synthesis."""

    target_var: str
    intent: str
    select_vars: list[str]
    patterns: list[TraversalPattern]
    filters: list[str] = field(default_factory=list)
    optional_patterns: list[TraversalPattern] = field(default_factory=list)
    order_by: str | None = None
    limit: int = 25


class QueryPlanner:
    """Transforms grounded entities into a structured multi-hop query plan."""

    def plan(self, entities: GroundedEntities) -> LogicalQueryPlan:
        patterns: list[TraversalPattern] = []
        filters: list[str] = []
        select_vars: list[str] = ["?note", "?title", "?noteNumber"]

        if entities.intent == "PREREQUISITE_CHAIN":
            # Finding prerequisites of a given note
            patterns.append(TraversalPattern("?targetNote", "rdf:type", "sap:SAPNote"))
            patterns.append(TraversalPattern("?targetNote", "sap:hasPrerequisiteNote", "?note"))
            patterns.append(TraversalPattern("?note", "sap:title", "?title"))
            patterns.append(TraversalPattern("?note", "sap:noteNumber", "?noteNumber"))

            if entities.note_numbers:
                target_num = entities.note_numbers[0]
                patterns.append(TraversalPattern("?targetNote", "sap:noteNumber", f'"{target_num}"^^xsd:string'))

            return LogicalQueryPlan(
                target_var="?note",
                intent=entities.intent,
                select_vars=select_vars + ["?prereqTitle"],
                patterns=patterns,
                filters=filters,
                order_by="?noteNumber",
            )

        # General / Alert / Component / Version queries
        patterns.append(TraversalPattern("?note", "rdf:type", "sap:SAPNote"))
        patterns.append(TraversalPattern("?note", "sap:title", "?title"))
        patterns.append(TraversalPattern("?note", "sap:noteNumber", "?noteNumber"))

        # Alert Join
        if entities.alert_codes:
            patterns.append(TraversalPattern("?note", "sap:resolvesAlert", "?alert"))
            patterns.append(TraversalPattern("?alert", "sap:alertCode", "?alertCode"))
            select_vars.append("?alertCode")
            alert_filter_terms = [f'?alertCode = "{code}"^^xsd:string' for code in entities.alert_codes]
            filters.append(" || ".join(alert_filter_terms))

        # Application Component Join (with hierarchical taxonomy traversal)
        if entities.component_codes:
            patterns.append(TraversalPattern("?note", "sap:affectsComponent/sap:parentComponent*", "?comp"))
            patterns.append(TraversalPattern("?comp", "sap:componentCode", "?compCode"))
            select_vars.append("?compCode")
            comp_filter_terms = [f'?compCode = "{c}"^^xsd:string' for c in entities.component_codes]
            filters.append(" || ".join(comp_filter_terms))

        # Product Version Join
        if entities.product_versions:
            patterns.append(TraversalPattern("?note", "sap:validForProductVersion", "?pv"))
            patterns.append(TraversalPattern("?pv", "ppms:versionCode", "?vCode"))
            select_vars.append("?vCode")
            v_filters = [f'?vCode = "{v}"^^xsd:string' for v in entities.product_versions]
            filters.append(" || ".join(v_filters))

        # Priority Filter
        if entities.priorities:
            patterns.append(TraversalPattern("?note", "sap:priority", "?priority"))
            select_vars.append("?priority")
            p_filters = [f'?priority = "{p}"^^xsd:string' for p in entities.priorities]
            filters.append(" || ".join(p_filters))

        # Support Package Bounds Filter
        if entities.support_packages:
            target_sp = entities.support_packages[0]
            patterns.append(TraversalPattern("?note", "sap:minSupportPackage", "?minSP"))
            patterns.append(TraversalPattern("?note", "sap:maxSupportPackage", "?maxSP"))
            filters.append(f"?minSP <= {target_sp} && ?maxSP >= {target_sp}")

        return LogicalQueryPlan(
            target_var="?note",
            intent=entities.intent,
            select_vars=select_vars,
            patterns=patterns,
            filters=filters,
            order_by="DESC(?noteNumber)",
        )
