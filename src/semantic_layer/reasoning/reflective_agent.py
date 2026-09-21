"""Deterministic, bounded AQR execution with typed lifecycle evidence.

The reasoner deliberately has no model or open-ended repair policy.  Grounding,
planning, compilation, execution, and the small set of constraint relaxations
are all finite operations whose outcomes are represented in the result ledger.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Literal

from semantic_layer.kg.loader import SAPKnowledgeGraph
from semantic_layer.reasoning.query_planner import LogicalQueryPlan, QueryPlanner
from semantic_layer.reasoning.schema_linker import GroundedEntities, SchemaLinker
from semantic_layer.reasoning.text_to_sparql import TextToSPARQLEngine
from semantic_layer.research.contracts import (
    CONDITIONS,
    ReasonCode,
    Status,
    canonical_json,
    sha256_bytes,
)

MAX_REPAIRS = 3
AnswerScope = Literal["strict", "relaxed_candidates", "none"]
OperationKind = Literal[
    "initial",
    "syntax_repair",
    "execution_repair",
    "semantic_relaxation",
    "abstention",
    "compile_failure",
]


def sanitize_diagnostic(text: str, limit: int = 512) -> str:
    """Bound and redact diagnostics before they enter a result artifact."""

    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
        raise ValueError("diagnostic limit must be a non-negative integer")
    value = str(text)
    value = re.sub(
        r"(?i)(authorization\s*[:=]\s*(?:bearer|basic)\s+)[^\s,;]+",
        r"\1[REDACTED]",
        value,
    )
    value = re.sub(
        r"(?i)\b(basic|bearer)\s+[^\s,;]+",
        lambda match: f"{match.group(1).capitalize()} [REDACTED]",
        value,
    )
    value = re.sub(
        r"(?i)(\b(?:password|passwd|secret|token|api[_-]?key|credential)\s*[:=]\s*)[^\s,;]+",
        r"\1[REDACTED]",
        value,
    )
    value = re.sub(
        r"(?i)\b([a-z][a-z0-9+.-]*://)([^\s/@:]*):([^\s/@]+)@",
        r"\1[REDACTED]@",
        value,
    )
    return value[:limit]


@dataclass(frozen=True)
class ReflectionStep:
    """Compatibility view of one failed execution/repair transition."""

    iteration: int
    draft_sparql: str
    failure_type: str
    diagnostic_feedback: str
    repaired_sparql: str | None = None


@dataclass(frozen=True)
class RepairOperation:
    """One append-only lifecycle ledger entry.

    The fields mirror Spec §18.2.  ``sparql_text`` is retained in addition to
    its digest because Spec §26.5 requires every attempted query to remain
    retrievable from the result artifact.
    """

    attempt_index: int
    operation_kind: OperationKind
    reason_code: ReasonCode
    status_before: Status
    status_after: Status
    query_sha256: str
    plan_sha256: str | None
    sparql_sha256: str | None
    changed_constraints: list[str]
    binding_count: int
    error_class: str | None
    diagnostic: str
    sparql_text: str | None = None


@dataclass
class RepairLedger:
    """Bounded repair metadata and its ordered operation history."""

    max_repairs: int = MAX_REPAIRS
    recovered: bool = False
    recovery_attempt: int = 0
    recovery_success: bool = False
    relaxation_attempted: bool = False
    operations: list[RepairOperation] = field(default_factory=list)


@dataclass
class RelaxationDisclosure:
    """Strict outcome plus separately disclosed relaxed executions."""

    attempted: bool = False
    strict_status: Status = Status.SUCCESS
    operations: list[RepairOperation] = field(default_factory=list)


@dataclass
class ReasoningResult:
    """Complete typed response from one deterministic AQR invocation."""

    query: str
    normalized_request: str
    grounding: GroundedEntities | None
    plan: LogicalQueryPlan | None
    sparql_initial: str | None
    sparql_final: str | None
    status: Status
    reason_code: ReasonCode
    attempts: int
    repair: RepairLedger
    relaxation: RelaxationDisclosure
    answer_scope: AnswerScope
    relaxed_candidates: list[dict[str, Any]]
    bindings: list[dict[str, Any]]
    predicted_note_numbers: list[str]
    provenance: dict[str, Any]
    answer: str = ""

    @property
    def grounded_entities(self) -> GroundedEntities | None:
        return self.grounding

    @property
    def results(self) -> list[dict[str, Any]]:
        """Strict bindings only; relaxed candidates never masquerade as results."""

        return self.bindings

    @property
    def final_sparql(self) -> str | None:
        return self.sparql_final

    @property
    def execution_status(self) -> str:
        return self.status.value

    @property
    def recovery_succeeded(self) -> bool:
        return self.repair.recovery_success

    @property
    def provenance_citations(self) -> list[str]:
        """Synthetic citations derived only from executed binding rows."""

        rows = self.bindings or self.relaxed_candidates
        prefix = str(self.provenance.get("citation", ""))
        citations: list[str] = []
        for row in rows:
            number = row.get("noteNumber")
            if number is not None:
                citations.append(f"{prefix} Note {number}")
        return citations

    @property
    def reflection_history(self) -> list[ReflectionStep]:
        """Compatibility projection of repair failures, in ledger order."""

        history: list[ReflectionStep] = []
        for operation in self.repair.operations:
            if operation.operation_kind == "abstention":
                continue
            if (
                operation.operation_kind == "initial"
                and operation.reason_code is ReasonCode.NONE
                and operation.status_after is Status.SUCCESS
            ):
                continue
            if operation.error_class is None and operation.binding_count > 0:
                continue
            history.append(
                ReflectionStep(
                    iteration=operation.attempt_index,
                    draft_sparql=operation.sparql_text or "",
                    failure_type=operation.reason_code.value,
                    diagnostic_feedback=operation.diagnostic,
                )
            )
        return history

    @property
    def original_constraints(self) -> dict[str, list[Any]]:
        """Expose the strict grounding slots retained through relaxation."""

        if self.grounding is None:
            return {}
        return {
            "component_code": list(self.grounding.component_codes),
            "alert_code": list(self.grounding.alert_codes),
            "product_version": list(self.grounding.product_versions),
            "software_component": list(self.grounding.software_components),
            "support_package": list(self.grounding.support_packages),
            "note_number": list(self.grounding.note_numbers),
            "priority": list(self.grounding.priorities),
            "predicates": _original_constraint_predicates(self.plan),
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize the typed result without exposing compatibility aliases."""

        return {
            "query": self.query,
            "normalized_request": self.normalized_request,
            "grounding": _grounding_payload(self.grounding),
            "plan": _plan_payload(self.plan),
            "original_constraints": self.original_constraints,
            "sparql_initial": self.sparql_initial,
            "sparql_final": self.sparql_final,
            "status": self.status.value,
            "reason_code": self.reason_code.value,
            "attempts": self.attempts,
            "repair": _repair_payload(self.repair),
            "relaxation": _relaxation_payload(self.relaxation),
            "answer_scope": self.answer_scope,
            "relaxed_candidates": self.relaxed_candidates,
            "bindings": self.bindings,
            "predicted_note_numbers": self.predicted_note_numbers,
            "provenance": dict(self.provenance),
            "answer": self.answer,
        }


def _original_constraint_predicates(plan: LogicalQueryPlan | None) -> list[str]:
    """Return sorted predicates that encode the original plan constraints.

    Projection scaffolding (``rdf:type``, title, and unfiltered note number)
    is not a user constraint.  Filter variables are traced backwards through
    the original typed plan so joins such as alert/component/version retain
    every predicate in their path.  Literal anchor patterns cover note lookup
    and prerequisite targets.  The helper is intentionally given only the
    original plan; relaxed plans can therefore never replace this evidence.
    """

    if plan is None:
        return []

    patterns = [*plan.patterns, *plan.optional_patterns]
    reverse_edges: dict[str, list[tuple[str, str]]] = {}
    incoming: set[str] = set()
    for pattern in patterns:
        subject = pattern.subject
        object_value = pattern.object_val
        if subject.startswith("?") and object_value.startswith("?"):
            reverse_edges.setdefault(object_value, []).append((subject, pattern.predicate))
            incoming.add(object_value)

    roots: set[str] = set()
    if plan.target_var not in incoming:
        roots.add(plan.target_var)
    roots.update(
        pattern.subject
        for pattern in patterns
        if pattern.subject.startswith("?") and pattern.subject not in incoming
    )
    constrained_variables: set[str] = set()
    for expression in plan.filters:
        constrained_variables.update(re.findall(r"\?[A-Za-z_][A-Za-z0-9_]*", expression))

    predicates: set[str] = {
        pattern.predicate
        for pattern in patterns
        if pattern.object_val.startswith('"')
    }
    for variable in sorted(constrained_variables):
        stack: list[tuple[str, tuple[str, ...]]] = [(variable, ())]
        visited: set[tuple[str, tuple[str, ...]]] = set()
        while stack:
            current, path = stack.pop()
            state = (current, path)
            if state in visited:
                continue
            visited.add(state)
            if current in roots:
                predicates.update(path)
                continue
            for parent, predicate in reverse_edges.get(current, []):
                if len(path) < len(patterns):
                    stack.append((parent, (*path, predicate)))

    return sorted(predicates)


def _grounding_payload(grounding: GroundedEntities | None) -> dict[str, Any] | None:
    if grounding is None:
        return None
    payload = asdict(grounding)
    failure = payload.get("failure_class")
    if isinstance(failure, ReasonCode):
        payload["failure_class"] = failure.value
    return payload


def _plan_payload(plan: LogicalQueryPlan | None) -> dict[str, Any] | None:
    if plan is None:
        return None
    return asdict(plan)


def _operation_payload(operation: RepairOperation) -> dict[str, Any]:
    payload = asdict(operation)
    payload["reason_code"] = operation.reason_code.value
    payload["status_before"] = operation.status_before.value
    payload["status_after"] = operation.status_after.value
    return payload


def _repair_payload(repair: RepairLedger) -> dict[str, Any]:
    return {
        "max_repairs": repair.max_repairs,
        "recovered": repair.recovered,
        "recovery_attempt": repair.recovery_attempt,
        "recovery_success": repair.recovery_success,
        "relaxation_attempted": repair.relaxation_attempted,
        "operations": [_operation_payload(operation) for operation in repair.operations],
    }


def _relaxation_payload(relaxation: RelaxationDisclosure) -> dict[str, Any]:
    return {
        "attempted": relaxation.attempted,
        "strict_status": relaxation.strict_status.value,
        "operations": [_operation_payload(operation) for operation in relaxation.operations],
    }


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _synthetic_provenance() -> dict[str, Any]:
    """Return the checked-in synthetic provenance envelope."""

    dataset_path = _repository_root() / "semantic/data/sap_support_graph.ttl"
    graph_sha = sha256_bytes(dataset_path.read_bytes()) if dataset_path.exists() else sha256_bytes(b"")
    return {
        "dataset_id": "cifre-synthetic-support-ppms-v1",
        "source_kind": "synthetic_fixture",
        "official": False,
        "graph_sha256": graph_sha,
        "citation": "Synthetic fixture cifre-synthetic-support-ppms-v1; not official data.",
    }


def _plan_hash(plan: LogicalQueryPlan | None) -> str | None:
    if plan is None:
        return None
    return sha256_bytes(canonical_json(_plan_payload(plan)))


def _query_hash(query: str) -> str:
    return sha256_bytes(query.encode("utf-8"))


def _sparql_hash(sparql: str | None) -> str | None:
    return None if sparql is None else sha256_bytes(sparql.encode("utf-8"))


def _value_for_json(value: Any) -> Any:
    """Normalize RDFLib scalar values without inventing missing bindings."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


class AQRReflectiveAgent:
    """Translate closed-grammar requests through a bounded repair state machine."""

    def __init__(self, knowledge_graph: SAPKnowledgeGraph) -> None:
        self.kg = knowledge_graph
        self.linker = SchemaLinker()
        self.planner = QueryPlanner()
        self.compiler = TextToSPARQLEngine()

    def run(
        self,
        query_text: str,
        condition: str = "deterministic_bounded_repair",
        max_repairs: int = MAX_REPAIRS,
        *,
        max_reflections: int | None = None,
    ) -> ReasoningResult:
        """Execute one grounded query with at most three repair transitions."""

        # The old benchmark runner used this keyword. Keep it as a narrow
        # migration shim while exposing the typed max_repairs contract.
        if max_reflections is not None:
            max_repairs = max_reflections
        if condition not in CONDITIONS:
            raise ValueError(f"unsupported AQR condition: {condition}")
        if not isinstance(max_repairs, int) or isinstance(max_repairs, bool) or max_repairs < 0:
            raise ValueError("max_repairs must be a non-negative integer")

        repair_budget = min(max_repairs, MAX_REPAIRS)
        bounded = condition == "deterministic_bounded_repair"
        provenance = _synthetic_provenance()
        entities = self.linker.ground_or_abstain(query_text)
        normalized = entities.normalized_request
        operations: list[RepairOperation] = []
        reflections: list[ReflectionStep] = []

        # Grammar failure is an explicit abstention: no plan, query, or graph
        # execution is allowed to occur, and attempts remains zero.
        if entities.failure_class is not None and entities.failure_class is not ReasonCode.NONE:
            reason = entities.failure_class
            operation = self._make_operation(
                query_text=query_text,
                plan=None,
                sparql=None,
                attempt_index=0,
                operation_kind="abstention",
                reason_code=reason,
                status_before=Status.UNSUPPORTED,
                status_after=Status.UNSUPPORTED,
                changed_constraints=[],
                binding_count=0,
                error_class=None,
                diagnostic=f"grounding abstained: {reason.value}",
            )
            operations.append(operation)
            repair = RepairLedger(max_repairs=MAX_REPAIRS, operations=operations)
            relaxation = RelaxationDisclosure(
                attempted=False,
                strict_status=Status.UNSUPPORTED,
                operations=[],
            )
            return ReasoningResult(
                query=query_text,
                normalized_request=normalized,
                grounding=entities,
                plan=None,
                sparql_initial=None,
                sparql_final=None,
                status=Status.UNSUPPORTED,
                reason_code=reason,
                attempts=0,
                repair=repair,
                relaxation=relaxation,
                answer_scope="none",
                relaxed_candidates=[],
                bindings=[],
                predicted_note_numbers=[],
                provenance=provenance,
                answer="",
            )

        # A supported request is planned and compiled before its initial
        # execution attempt.  Compilation failures are represented as syntax
        # failures, not as an unsupported grounding result.
        try:
            original_plan = self.planner.plan(entities)
            current_plan = original_plan
            current_sparql = self.compiler.compile(current_plan)
        except Exception as error:  # noqa: BLE001 - typed below by message
            reason = (
                ReasonCode.UNBOUND_REQUIRED_PROJECTION
                if "UNBOUND_REQUIRED_PROJECTION" in str(error)
                else ReasonCode.SPARQL_SYNTAX
            )
            diagnostic = sanitize_diagnostic(str(error))
            failed_plan = locals().get("current_plan")
            operation = self._make_operation(
                query_text=query_text,
                plan=failed_plan,
                sparql=None,
                attempt_index=0,
                operation_kind="compile_failure",
                reason_code=reason,
                status_before=Status.SYNTAX_ERROR,
                status_after=Status.SYNTAX_ERROR,
                changed_constraints=[],
                binding_count=0,
                error_class=type(error).__name__,
                diagnostic=diagnostic,
            )
            operations.append(operation)
            repair = RepairLedger(max_repairs=MAX_REPAIRS, operations=operations)
            return ReasoningResult(
                query=query_text,
                normalized_request=normalized,
                grounding=entities,
                plan=failed_plan,
                sparql_initial=None,
                sparql_final=None,
                status=Status.SYNTAX_ERROR,
                reason_code=reason,
                attempts=0,
                repair=repair,
                relaxation=RelaxationDisclosure(
                    attempted=False,
                    strict_status=Status.SYNTAX_ERROR,
                    operations=[],
                ),
                answer_scope="none",
                relaxed_candidates=[],
                bindings=[],
                predicted_note_numbers=[],
                provenance=provenance,
                answer="",
            )

        sparql_initial = current_sparql
        attempts = 0
        repair_count = 0
        strict_bindings: list[dict[str, Any]] = []
        relaxed_candidates: list[dict[str, Any]] = []
        final_status = Status.EXECUTION_ERROR
        final_reason = ReasonCode.SPARQL_EXECUTION
        answer_scope: AnswerScope = "none"
        recovered = False
        recovery_attempt = 0
        recovery_success = False
        relaxation = RelaxationDisclosure(
            attempted=False,
            strict_status=Status.SUCCESS,
            operations=[],
        )
        last_status = Status.SUCCESS
        last_error_kind: str | None = None

        while True:
            operation_kind: OperationKind = (
                "initial"
                if not operations
                else (
                    "syntax_repair"
                    if last_error_kind == "syntax"
                    else "execution_repair"
                    if last_error_kind == "execution"
                    else "semantic_relaxation"
                )
            )
            try:
                attempts += 1
                raw_rows = self.kg.query_sparql(current_sparql)
                rows = self._normalize_bindings(raw_rows, current_plan)
            except Exception as error:  # noqa: BLE001 - backend exceptions are classified below
                error_kind = self._classify_error(error)
                event_status = (
                    Status.SYNTAX_ERROR if error_kind == "syntax" else Status.EXECUTION_ERROR
                )
                event_reason = (
                    ReasonCode.SPARQL_SYNTAX if error_kind == "syntax" else ReasonCode.SPARQL_EXECUTION
                )
                diagnostic = sanitize_diagnostic(str(error))
                operation = self._make_operation(
                    query_text=query_text,
                    plan=current_plan,
                    sparql=current_sparql,
                    attempt_index=len(operations),
                    operation_kind=operation_kind,
                    reason_code=event_reason,
                    status_before=event_status if not operations else last_status,
                    status_after=event_status,
                    changed_constraints=[],
                    binding_count=0,
                    error_class=type(error).__name__,
                    diagnostic=diagnostic,
                )
                operations.append(operation)
                reflections.append(
                    ReflectionStep(
                        iteration=operation.attempt_index,
                        draft_sparql=current_sparql,
                        failure_type=event_status.value,
                        diagnostic_feedback=diagnostic,
                    )
                )
                final_status = event_status
                final_reason = event_reason
                last_status = event_status
                last_error_kind = error_kind

                if not bounded or repair_count >= repair_budget:
                    if bounded and repair_count >= repair_budget and repair_count > 0:
                        final_reason = ReasonCode.REPAIR_BUDGET_EXHAUSTED
                    break

                repair_count += 1
                repaired_sparql = (
                    self._repair_syntax_error(current_sparql, str(error))
                    if error_kind == "syntax"
                    else self._repair_execution_error(current_sparql, str(error))
                )
                if repaired_sparql == current_sparql:
                    no_op = self._make_operation(
                        query_text=query_text,
                        plan=current_plan,
                        sparql=current_sparql,
                        attempt_index=len(operations),
                        operation_kind=(
                            "syntax_repair" if error_kind == "syntax" else "execution_repair"
                        ),
                        reason_code=ReasonCode.NO_OP_REPAIR,
                        status_before=event_status,
                        status_after=event_status,
                        changed_constraints=[],
                        binding_count=0,
                        error_class=type(error).__name__,
                        diagnostic="repair produced the same query and plan",
                    )
                    operations.append(no_op)
                    final_reason = ReasonCode.NO_OP_REPAIR
                    break
                current_sparql = repaired_sparql
                continue

            # Successful execution, including a strict empty result, is now a
            # typed operation.  Relaxation is handled below as a separate
            # operation so strict bindings remain immutable and auditable.
            if rows:
                operation = self._make_operation(
                    query_text=query_text,
                    plan=current_plan,
                    sparql=current_sparql,
                    attempt_index=len(operations),
                    operation_kind=operation_kind,
                    reason_code=ReasonCode.NONE,
                    status_before=Status.SUCCESS if not operations else last_status,
                    status_after=Status.SUCCESS,
                    changed_constraints=[],
                    binding_count=len(rows),
                    error_class=None,
                    diagnostic="",
                )
                operations.append(operation)
                final_status = Status.SUCCESS
                final_reason = ReasonCode.NONE
                strict_bindings = rows
                answer_scope = "strict"
                if repair_count > 0 and last_error_kind in {"syntax", "execution"}:
                    recovered = True
                    recovery_attempt = repair_count
                    recovery_success = True
                break

            operation = self._make_operation(
                query_text=query_text,
                plan=current_plan,
                sparql=current_sparql,
                attempt_index=len(operations),
                operation_kind=operation_kind,
                reason_code=ReasonCode.EMPTY_STRICT_RESULT,
                status_before=Status.EMPTY_RESULT if not operations else last_status,
                status_after=Status.EMPTY_RESULT,
                changed_constraints=[],
                binding_count=0,
                error_class=None,
                diagnostic="strict query returned no bindings",
            )
            operations.append(operation)
            final_status = Status.EMPTY_RESULT
            final_reason = ReasonCode.EMPTY_STRICT_RESULT
            last_status = Status.EMPTY_RESULT
            last_error_kind = None
            relaxation.strict_status = Status.EMPTY_RESULT

            if not bounded or repair_count >= repair_budget:
                break

            relaxation_operation = self._run_relaxation(
                query_text=query_text,
                entities=entities,
                current_plan=current_plan,
                current_sparql=current_sparql,
                attempt_index=len(operations),
                operation_limit=repair_budget - repair_count,
            )
            if relaxation_operation is None:
                break

            relaxation.attempted = True

            (
                relaxation_plan,
                relaxation_sparql,
                relaxation_ops,
                relaxation_rows,
                used_repairs,
            ) = relaxation_operation
            operations.extend(relaxation_ops)
            relaxation.operations.extend(relaxation_ops)
            repair_count += used_repairs
            attempts += used_repairs
            current_plan = relaxation_plan
            current_sparql = relaxation_sparql
            if relaxation_rows:
                relaxed_candidates = relaxation_rows
                answer_scope = "relaxed_candidates"
            if relaxation_ops and relaxation_ops[-1].reason_code in {
                ReasonCode.RELAX_SUPPORT_PACKAGE,
                ReasonCode.WIDEN_COMPONENT,
            }:
                final_reason = relaxation_ops[-1].reason_code
            break

        strict_bindings = self._normalize_bindings(strict_bindings, original_plan)
        relaxed_candidates = self._normalize_bindings(relaxed_candidates, current_plan)
        predicted = self._predicted_notes(strict_bindings)
        if not relaxation.attempted:
            relaxation.strict_status = final_status
        repair = RepairLedger(
            max_repairs=MAX_REPAIRS,
            recovered=recovered,
            recovery_attempt=recovery_attempt,
            recovery_success=recovery_success,
            relaxation_attempted=relaxation.attempted,
            operations=operations,
        )
        if final_status in {Status.SUCCESS, Status.EMPTY_RESULT}:
            if answer_scope != "relaxed_candidates":
                answer_scope = "strict"
        else:
            answer_scope = "none"
        rows_for_answer = strict_bindings if answer_scope == "strict" else relaxed_candidates
        answer = self._synthesize(rows_for_answer, entities, answer_scope, provenance)

        return ReasoningResult(
            query=query_text,
            normalized_request=normalized,
            grounding=entities,
            plan=original_plan,
            sparql_initial=sparql_initial,
            sparql_final=current_sparql,
            status=final_status,
            reason_code=final_reason,
            attempts=attempts,
            repair=repair,
            relaxation=relaxation,
            answer_scope=answer_scope,
            relaxed_candidates=relaxed_candidates,
            bindings=strict_bindings,
            predicted_note_numbers=predicted,
            provenance=provenance,
            answer=answer,
        )

    def _make_operation(
        self,
        *,
        query_text: str,
        plan: LogicalQueryPlan | None,
        sparql: str | None,
        attempt_index: int,
        operation_kind: OperationKind,
        reason_code: ReasonCode,
        status_before: Status,
        status_after: Status,
        changed_constraints: list[str],
        binding_count: int,
        error_class: str | None,
        diagnostic: str,
    ) -> RepairOperation:
        return RepairOperation(
            attempt_index=attempt_index,
            operation_kind=operation_kind,
            reason_code=reason_code,
            status_before=status_before,
            status_after=status_after,
            query_sha256=_query_hash(query_text),
            plan_sha256=_plan_hash(plan),
            sparql_sha256=_sparql_hash(sparql),
            changed_constraints=sorted(set(changed_constraints)),
            binding_count=binding_count,
            error_class=error_class,
            diagnostic=sanitize_diagnostic(diagnostic),
            sparql_text=sparql,
        )

    @staticmethod
    def _classify_error(error: Exception) -> Literal["syntax", "execution"]:
        name = type(error).__name__.casefold()
        text = str(error).casefold()
        if isinstance(error, SyntaxError) or "syntax" in name or "parse" in name:
            return "syntax"
        if any(marker in text for marker in ("syntax", "parse error", "malformed query")):
            return "syntax"
        return "execution"

    @staticmethod
    def _normalize_bindings(
        rows: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        plan: LogicalQueryPlan,
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        optional = {variable.lstrip("?") for variable in plan.optional_variables}
        for source in rows:
            row = {str(key).lstrip("?"): _value_for_json(value) for key, value in source.items()}
            for variable in optional:
                row.setdefault(variable, None)
            normalized.append(row)
        normalized.sort(
            key=lambda row: (
                str(row.get("noteNumber") or ""),
                str(row.get("note") or ""),
                canonical_json(row),
            )
        )
        return normalized

    @staticmethod
    def _predicted_notes(rows: list[dict[str, Any]]) -> list[str]:
        return sorted(
            {
                str(row["noteNumber"])
                for row in rows
                if row.get("noteNumber") is not None
            }
        )

    def _relax_support_package_filter(self, plan: LogicalQueryPlan) -> LogicalQueryPlan:
        """Remove numeric support-package bounds in a deterministic first step."""

        new_patterns = [
            pattern
            for pattern in plan.patterns
            if pattern.predicate not in {"cifsup:minSupportPackage", "cifsup:maxSupportPackage"}
        ]
        new_filters = [
            expression
            for expression in plan.filters
            if "minSP" not in expression and "maxSP" not in expression
        ]
        return replace(plan, patterns=new_patterns, filters=new_filters)

    def _relax_to_parent_component(
        self,
        plan: LogicalQueryPlan,
        entities: GroundedEntities,
    ) -> LogicalQueryPlan:
        """Widen one leaf component to its immediate finite parent."""

        parent_codes: list[str] = []
        for component in entities.component_codes:
            parts = component.split("-")
            if len(parts) > 1:
                parent_codes.append("-".join(parts[:-1]))
        if not parent_codes:
            return plan

        new_filters: list[str] = []
        changed = False
        for expression in plan.filters:
            if "compCode" in expression:
                terms = [
                    f'?compCode = "{parent.replace(chr(92), chr(92) + chr(92)).replace(chr(34), chr(92) + chr(34))}"^^xsd:string'
                    for parent in sorted(set(parent_codes))
                ]
                new_filters.append(" || ".join(terms))
                changed = True
            else:
                new_filters.append(expression)
        return replace(plan, filters=new_filters) if changed else plan

    def _run_relaxation(
        self,
        *,
        query_text: str,
        entities: GroundedEntities,
        current_plan: LogicalQueryPlan,
        current_sparql: str,
        attempt_index: int,
        operation_limit: int,
    ) -> tuple[LogicalQueryPlan, str, list[RepairOperation], list[dict[str, Any]], int] | None:
        """Try support-package removal, then component widening, in that order."""

        operations: list[RepairOperation] = []
        plan = current_plan
        sparql = current_sparql
        used = 0
        rows: list[dict[str, Any]] = []
        attempted_kinds: set[str] = set()

        while used < operation_limit:
            candidate_plan: LogicalQueryPlan | None = None
            diagnostic = ""
            reason = ReasonCode.EMPTY_STRICT_RESULT
            changed: list[str] = []

            # The order is part of the research contract.  Build the second
            # candidate from the first candidate's plan so component widening
            # never accidentally restores a removed support-package bound.
            if (
                "support_package" not in attempted_kinds
                and entities.support_packages
                and any(
                    "minSP" in expression or "maxSP" in expression
                    for expression in plan.filters
                )
            ):
                candidate_plan = self._relax_support_package_filter(plan)
                diagnostic = "remove support-package bounds"
                reason = ReasonCode.RELAX_SUPPORT_PACKAGE
                changed = ["support_package"]
                attempted_kinds.add("support_package")
            else:
                widened = self._relax_to_parent_component(plan, entities)
                if "component" in attempted_kinds or widened is plan:
                    break
                candidate_plan = widened
                diagnostic = "widen component to parent"
                reason = ReasonCode.WIDEN_COMPONENT
                changed = ["component"]
                attempted_kinds.add("component")

            if candidate_plan is None:
                break
            candidate_sparql = self.compiler.compile(candidate_plan)
            if candidate_sparql == sparql and _plan_hash(candidate_plan) == _plan_hash(plan):
                operation = self._make_operation(
                    query_text=query_text,
                    plan=candidate_plan,
                    sparql=candidate_sparql,
                    attempt_index=attempt_index + used,
                    operation_kind="semantic_relaxation",
                    reason_code=ReasonCode.NO_OP_REPAIR,
                    status_before=Status.EMPTY_RESULT,
                    status_after=Status.EMPTY_RESULT,
                    changed_constraints=changed,
                    binding_count=0,
                    error_class=None,
                    diagnostic="semantic relaxation produced the same query and plan",
                )
                operations.append(operation)
                used += 1
                break

            used += 1
            try:
                raw_rows = self.kg.query_sparql(candidate_sparql)
                rows = self._normalize_bindings(raw_rows, candidate_plan)
                error_class = None
                event_diagnostic = diagnostic if rows else f"{diagnostic}; no bindings"
            except Exception as error:  # noqa: BLE001 - relaxed output remains strict-empty
                rows = []
                error_class = type(error).__name__
                event_diagnostic = f"{diagnostic}; {sanitize_diagnostic(str(error))}"

            operation = self._make_operation(
                query_text=query_text,
                plan=candidate_plan,
                sparql=candidate_sparql,
                attempt_index=attempt_index + used - 1,
                operation_kind="semantic_relaxation",
                reason_code=reason,
                status_before=Status.EMPTY_RESULT,
                status_after=Status.EMPTY_RESULT,
                changed_constraints=changed,
                binding_count=len(rows),
                error_class=error_class,
                diagnostic=event_diagnostic,
            )
            operations.append(operation)
            plan = candidate_plan
            sparql = candidate_sparql
            if rows:
                break

        if not operations:
            return None
        return plan, sparql, operations, rows, used

    @staticmethod
    def _repair_allowlisted_structure(sparql: str, error_msg: str) -> str:
        """Apply only an explicitly diagnosed, approved structural repair."""

        diagnostic = str(error_msg)
        prefix_alias: str | None = None
        for pattern in (
            r"(?i)\b(?:unknown|undefined|undeclared|missing)\s+prefix\s*[:=]?\s*['\"`]?([A-Za-z][\w-]*)",
            r"(?i)\bprefix\s+['\"`]?([A-Za-z][\w-]*)['\"`]?\s+(?:is\s+)?(?:not\s+defined|undefined|unknown|missing)",
        ):
            match = re.search(pattern, diagnostic)
            if match:
                prefix_alias = match.group(1).casefold()
                break
        if prefix_alias is None:
            return sparql

        prefix_uri = TextToSPARQLEngine.STANDARD_PREFIXES.get(prefix_alias)
        if prefix_uri is None:
            return sparql
        if re.search(rf"(?im)^\s*PREFIX\s+{re.escape(prefix_alias)}\s*:", sparql):
            return sparql
        prefix_line = f"PREFIX {prefix_alias}: <{prefix_uri}>"
        return f"{prefix_line}\n{sparql}"

    @classmethod
    def _repair_syntax_error(cls, sparql: str, error_msg: str) -> str:
        """Repair a diagnosed missing approved prefix, otherwise no-op."""

        return cls._repair_allowlisted_structure(sparql, error_msg)

    @classmethod
    def _repair_execution_error(cls, sparql: str, error_msg: str) -> str:
        """Repair a diagnosed missing approved prefix, otherwise no-op."""

        return cls._repair_allowlisted_structure(sparql, error_msg)

    def _synthesize(
        self,
        rows: list[dict[str, Any]],
        entities: GroundedEntities,
        answer_scope: AnswerScope,
        provenance: dict[str, Any],
    ) -> str:
        """Render only scalar values present in executed graph bindings."""

        if answer_scope == "none" or not rows:
            return ""
        lines = [str(provenance["citation"])]
        if answer_scope == "relaxed_candidates":
            lines.append("Relaxed candidates outside the requested constraints:")
        elif entities.intent == "PREREQUISITE_CLOSURE":
            lines.append(f"Identified {len(rows)} prerequisite note(s) in the dependency chain:")
        else:
            lines.append(f"Identified {len(rows)} note(s) matching the requested constraints:")
        for row in rows:
            number = row.get("noteNumber")
            title = row.get("title")
            if number is None and title is None:
                continue
            suffix = f": {title}" if title is not None else ""
            lines.append(f"- Note {number if number is not None else '[unidentified]'}{suffix}")
        return "\n".join(lines)


__all__ = [
    "MAX_REPAIRS",
    "AQRReflectiveAgent",
    "AnswerScope",
    "ReasoningResult",
    "ReflectionStep",
    "RelaxationDisclosure",
    "RepairLedger",
    "RepairOperation",
    "sanitize_diagnostic",
]
