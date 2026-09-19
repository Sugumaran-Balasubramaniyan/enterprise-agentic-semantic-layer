"""Deterministic logical planning for the closed CIFRE AQR grammar.

The planner is intentionally small and typed. Grounding has already rejected
anything outside the finite grammar; this module only maps accepted slots to
the neutral synthetic vocabulary and never invents a URI or predicate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from semantic_layer.reasoning.schema_linker import GroundedEntities

MAX_PREREQUISITE_DEPTH = 16
_PREREQUISITE_PREDICATE = "cifsup:hasPrerequisiteNote"


def _property_path(predicate: str, depth: int) -> str:
    """Return a fixed-length SPARQL property path."""

    return "/".join([predicate] * depth)


PREREQUISITE_CLOSURE = "(" + "|".join(
    _property_path(_PREREQUISITE_PREDICATE, depth)
    for depth in range(1, MAX_PREREQUISITE_DEPTH + 1)
) + ")"
PREREQUISITE_DEPTH_EXCEEDED = "PREREQUISITE_DEPTH_EXCEEDED"
PREREQUISITE_DEPTH_MARKER = f"[{PREREQUISITE_DEPTH_EXCEEDED}]"


def _unique_sorted(values: list[str]) -> list[str]:
    """Deduplicate projection names and make their order reproducible."""

    return sorted(dict.fromkeys(values))


@dataclass
class TraversalPattern:
    """Single triple pattern or join in a SPARQL graph traversal."""

    subject: str
    predicate: str
    object_val: str
    optional: bool = False


@dataclass
class LogicalQueryPlan:
    """Typed logical plan before SPARQL synthesis.

    ``required_variables`` and ``optional_variables`` are explicit so the
    compiler can reject an accidental unbound projection before handing text
    to RDFLib. Defaults retain construction compatibility for recovery
    helpers that predate the projection contract.
    """

    target_var: str
    intent: str
    select_vars: list[str]
    patterns: list[TraversalPattern]
    filters: list[str] = field(default_factory=list)
    optional_patterns: list[TraversalPattern] = field(default_factory=list)
    required_variables: list[str] = field(default_factory=list)
    optional_variables: list[str] = field(default_factory=list)
    order_by: str | None = None
    limit: int = 25

    def __post_init__(self) -> None:
        """Normalize projection declarations without changing public fields."""

        selected = list(dict.fromkeys(self.select_vars))
        optional = _unique_sorted(self.optional_variables)
        declared_required = _unique_sorted(self.required_variables)

        # Older recovery constructors provide only ``select_vars``. Treat
        # every selected variable not explicitly optional as required, so a
        # later compiler invocation remains fail-closed.
        if not declared_required:
            declared_required = _unique_sorted(
                [variable for variable in selected if variable not in optional]
            )
        else:
            declared_required = _unique_sorted(
                [variable for variable in declared_required if variable not in optional]
            )

        # A selected variable must belong to one of the two declared sets.
        # Unclassified selections are mandatory by default; this avoids
        # silently dropping a caller's projection during compilation.
        declared = set(declared_required) | set(optional)
        declared_required.extend(
            variable for variable in selected if variable not in declared
        )
        self.select_vars = selected
        self.required_variables = _unique_sorted(declared_required)
        self.optional_variables = optional


class QueryPlanner:
    """Transform grounded entities into a neutral, deterministic query plan."""

    _BASE_SELECT_VARS: ClassVar[list[str]] = ["?note", "?noteNumber", "?title"]
    _SUPPORTED_INTENTS: ClassVar[frozenset[str]] = frozenset(
        {
            "NOTE_LOOKUP",
            "ALERT_RESOLUTION",
            "COMPONENT_SEARCH",
            "VERSION_FILTERED_SEARCH",
            "PREREQUISITE_CLOSURE",
            "GENERAL_SEARCH",
        }
    )

    @staticmethod
    def _literal(value: str) -> str:
        """Render a canonical xsd:string literal for a finite entity value."""

        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"^^xsd:string'

    @staticmethod
    def _or_filter(variable: str, values: list[str]) -> str:
        """Render a stable equality filter for one finite slot."""

        terms = [
            f"{variable} = {QueryPlanner._literal(value)}"
            for value in sorted(set(values))
        ]
        return " || ".join(terms)

    @staticmethod
    def _note_number_pattern(note_var: str, number: str) -> TraversalPattern:
        return TraversalPattern(
            note_var,
            "cifsup:noteNumber",
            QueryPlanner._literal(number),
        )

    def _base_patterns(self) -> list[TraversalPattern]:
        """Return mandatory answer fields in their canonical order."""

        return [
            TraversalPattern("?note", "rdf:type", "cifsup:SAPNote"),
            TraversalPattern("?note", "cifsup:noteNumber", "?noteNumber"),
            TraversalPattern("?note", "cifsup:title", "?title"),
        ]

    def _prerequisite_plan(self, entities: GroundedEntities) -> LogicalQueryPlan:
        """Plan bounded transitive prerequisites for exactly one target note.

        The finite union gives RDFLib a cycle-safe upper bound. A metadata
        marker is carried in ``filters`` and rendered as a SPARQL comment by
        the compiler; the graph-algorithm validation task turns a reachable
        seventeenth edge into ``EMPTY_RESULT`` with the corresponding reason.
        It is deliberately not a ``NOT EXISTS`` query predicate because a
        cycle can revisit a node at hop 17 without exceeding the acyclic depth
        contract.
        """

        patterns = [
            TraversalPattern("?targetNote", "rdf:type", "cifsup:SAPNote"),
            TraversalPattern("?targetNote", "cifsup:noteNumber", "?targetNoteNumber"),
            TraversalPattern("?targetNote", PREREQUISITE_CLOSURE, "?note"),
            TraversalPattern("?note", "cifsup:noteNumber", "?noteNumber"),
            TraversalPattern("?note", "cifsup:title", "?title"),
        ]
        filters = ["?note != ?targetNote", PREREQUISITE_DEPTH_MARKER]
        if entities.note_numbers:
            patterns.append(self._note_number_pattern("?targetNote", entities.note_numbers[0]))

        return LogicalQueryPlan(
            target_var="?note",
            intent="PREREQUISITE_CLOSURE",
            select_vars=list(self._BASE_SELECT_VARS),
            patterns=patterns,
            filters=filters,
            required_variables=list(self._BASE_SELECT_VARS),
            optional_variables=[],
            order_by="?noteNumber",
            limit=25,
        )

    def plan(self, entities: GroundedEntities) -> LogicalQueryPlan:
        """Build a typed plan from one accepted ``GroundedEntities`` result."""

        failure = getattr(entities.failure_class, "value", entities.failure_class)
        if entities.intent not in self._SUPPORTED_INTENTS:
            raise ValueError(f"unsupported grounded request: {entities.intent}")
        if failure not in (None, "NONE"):
            raise ValueError(f"unsupported grounded request: {failure or entities.intent}")

        required_slots = {
            "NOTE_LOOKUP": entities.note_numbers,
            "GENERAL_SEARCH": entities.note_numbers,
            "ALERT_RESOLUTION": entities.alert_codes,
            "COMPONENT_SEARCH": entities.component_codes,
            "PREREQUISITE_CLOSURE": entities.note_numbers,
        }
        if entities.intent in required_slots and len(required_slots[entities.intent]) != 1:
            raise ValueError(f"missing required entity for {entities.intent}")
        if entities.intent == "VERSION_FILTERED_SEARCH" and not (
            len(entities.alert_codes) == 1 or len(entities.component_codes) == 1
        ):
            raise ValueError("missing required anchor for VERSION_FILTERED_SEARCH")
        if entities.intent == "VERSION_FILTERED_SEARCH" and not (
            len(entities.product_versions) == 1 or len(entities.support_packages) == 1
        ):
            raise ValueError("missing required qualifier for VERSION_FILTERED_SEARCH")

        if entities.intent == "PREREQUISITE_CLOSURE":
            return self._prerequisite_plan(entities)

        patterns = self._base_patterns()
        filters: list[str] = []
        select_vars = list(self._BASE_SELECT_VARS)

        # A direct note lookup is still constrained by the selected note; a
        # general-search grounding is only emitted by the closed parser for a
        # single note number and follows the same deterministic path.
        if entities.note_numbers:
            filters.append(self._or_filter("?noteNumber", entities.note_numbers))

        if entities.alert_codes:
            patterns.extend(
                [
                    TraversalPattern("?note", "cifsup:resolvesAlert", "?alert"),
                    TraversalPattern("?alert", "cifsup:alertCode", "?alertCode"),
                ]
            )
            select_vars.append("?alertCode")
            filters.append(self._or_filter("?alertCode", entities.alert_codes))

        if entities.component_codes:
            patterns.extend(
                [
                    TraversalPattern(
                        "?note",
                        "cifsup:affectsComponent/cifsup:parentComponent*",
                        "?comp",
                    ),
                    TraversalPattern("?comp", "cifsup:componentCode", "?compCode"),
                ]
            )
            select_vars.append("?compCode")
            filters.append(self._or_filter("?compCode", entities.component_codes))

        if entities.product_versions:
            patterns.extend(
                [
                    TraversalPattern("?note", "cifsup:validForProductVersion", "?pv"),
                    TraversalPattern("?pv", "cifppms:versionCode", "?vCode"),
                ]
            )
            select_vars.append("?vCode")
            filters.append(self._or_filter("?vCode", entities.product_versions))

        if entities.priorities:
            patterns.append(TraversalPattern("?note", "cifsup:priority", "?priority"))
            select_vars.append("?priority")
            filters.append(self._or_filter("?priority", entities.priorities))

        if entities.support_packages:
            # Support package values are intentionally numeric: the graph
            # stores xsd:integer bounds and SP99 remains a valid strict query
            # that can deterministically return EMPTY_RESULT.
            package = entities.support_packages[0]
            patterns.extend(
                [
                    TraversalPattern("?note", "cifsup:minSupportPackage", "?minSP"),
                    TraversalPattern("?note", "cifsup:maxSupportPackage", "?maxSP"),
                ]
            )
            filters.append(f"?minSP <= {package} && ?maxSP >= {package}")

        return LogicalQueryPlan(
            target_var="?note",
            intent=entities.intent,
            select_vars=select_vars,
            patterns=patterns,
            filters=filters,
            required_variables=select_vars,
            optional_variables=[],
            order_by="DESC(?noteNumber)",
            limit=25,
        )
