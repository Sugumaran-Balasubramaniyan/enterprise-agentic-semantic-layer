"""Deterministic evaluation of reviewed semantic-layer cases."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Literal, cast

import yaml

from semantic_layer.agents import ClaimsInvestigationAgent
from semantic_layer.control import digest
from semantic_layer.governance import authorize_discovery
from semantic_layer.query_planner import QueryDiscovery, discover_question
from semantic_layer.registry import SemanticRegistry


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


GOLDEN_CASES = _repository_root() / "tests" / "golden" / "questions.yaml"


@dataclass(frozen=True)
class GoldenCase:
    """One declarative business-question expectation."""

    id: str
    question: str
    role: str
    expected: dict[str, Any]
    deterministic: DeterministicContract


DeterministicMode = Literal[
    "discovery_only", "governed_primary_variant", "governed_threshold_variant"
]


@dataclass(frozen=True)
class DeterministicContract:
    """Typed evidence contract for one golden case's deterministic dimension."""

    mode: DeterministicMode
    answer: tuple[dict[str, Any], ...] | None = None
    answer_constraints: dict[str, Any] | None = None


@dataclass(frozen=True)
class DimensionReport:
    """Pass/fail counts for one independently evaluated contract dimension."""

    total: int
    passed: int
    failed_case_ids: tuple[str, ...]

    @property
    def failed(self) -> int:
        return self.total - self.passed

    @property
    def accuracy(self) -> float:
        return self.passed / self.total if self.total else 1.0


@dataclass(frozen=True)
class CaseEvaluation:
    """Evidence for every dimension of one golden case."""

    case_id: str
    resolution: bool
    relationships: bool
    products: bool
    metrics: bool
    authorization: bool
    deterministic_answer: bool
    discovery_only: bool = False
    answer: list[dict[str, Any]] | None = None
    errors: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return all(
            (
                self.resolution,
                self.relationships,
                self.products,
                self.metrics,
                self.authorization,
                self.deterministic_answer,
            )
        )


@dataclass(frozen=True)
class EvaluationReport:
    """Measured local evaluation output; no external benchmark is implied."""

    total_cases: int
    passed_cases: int
    failed_cases: list[str]
    results: list[CaseEvaluation]
    resolution: DimensionReport
    relationships: DimensionReport
    products: DimensionReport
    metrics: DimensionReport
    authorization: DimensionReport
    deterministic_answers: DimensionReport
    discovery_only: DimensionReport

    @property
    def failed_count(self) -> int:
        return len(self.failed_cases)

    @property
    def relationship(self) -> DimensionReport:
        """Singular compatibility alias for the relationship dimension."""

        return self.relationships

    @property
    def product(self) -> DimensionReport:
        """Singular compatibility alias for the product dimension."""

        return self.products

    @property
    def metric(self) -> DimensionReport:
        """Singular compatibility alias for the metric dimension."""

        return self.metrics

    @property
    def deterministic_answer(self) -> DimensionReport:
        """Singular compatibility alias for deterministic answer evidence."""

        return self.deterministic_answers

    @property
    def resolution_accuracy(self) -> float:
        return self.resolution.accuracy

    @property
    def relationship_accuracy(self) -> float:
        return self.relationships.accuracy

    @property
    def product_accuracy(self) -> float:
        return self.products.accuracy

    @property
    def metric_accuracy(self) -> float:
        return self.metrics.accuracy

    @property
    def authorization_accuracy(self) -> float:
        return self.authorization.accuracy

    @property
    def deterministic_answer_accuracy(self) -> float:
        return self.deterministic_answers.accuracy

    @property
    def case_results(self) -> list[CaseEvaluation]:
        """Alias useful to callers that prefer an explicit result collection name."""

        return self.results

    @property
    def success_rate(self) -> float:
        return self.passed_cases / self.total_cases if self.total_cases else 1.0

    def summary(self) -> str:
        dimensions = (
            ("resolution", self.resolution),
            ("relationships", self.relationships),
            ("products", self.products),
            ("metrics", self.metrics),
            ("authorization", self.authorization),
            ("deterministic_answers", self.deterministic_answers),
            ("discovery_only", self.discovery_only),
        )
        details = ", ".join(f"{name}={item.passed}/{item.total}" for name, item in dimensions)
        return f"Golden evaluation: {self.passed_cases}/{self.total_cases} cases passed ({details})"


def load_golden_cases(path: Path | str) -> list[GoldenCase]:
    """Load and minimally validate the YAML golden-case contract."""

    source = Path(path)
    with source.open(encoding="utf-8") as stream:
        document = yaml.safe_load(stream)
    if not isinstance(document, dict) or not isinstance(document.get("questions"), list):
        raise TypeError("golden questions must contain a questions list")
    cases: list[GoldenCase] = []
    seen: set[str] = set()
    for item in document["questions"]:
        if not isinstance(item, dict):
            raise TypeError("each golden question must be a mapping")
        identifier = item.get("id")
        question = item.get("question")
        role = item.get("role", "ClaimsAnalystFR")
        expected = item.get("expected", {})
        if not isinstance(identifier, str) or not identifier.strip() or identifier in seen:
            raise ValueError(f"golden question has invalid or duplicate id: {identifier!r}")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"golden question {identifier} has no question")
        if not isinstance(role, str) or not role.strip() or not isinstance(expected, dict):
            raise ValueError(f"golden question {identifier} has invalid role or expected fields")
        required = ("concepts", "relationships", "products", "metrics", "authorization")
        missing = [field for field in required if field not in expected]
        if missing:
            raise ValueError(f"golden question {identifier} missing expected field: {missing[0]}")
        for field in required[:-1]:
            if not isinstance(expected[field], list):
                raise TypeError(f"golden question {identifier} expected {field} must be a list")
        if not isinstance(expected["authorization"], dict):
            raise TypeError(f"golden question {identifier} expected authorization must be a mapping")
        for field in ("allowed", "reason_code"):
            if field not in expected["authorization"]:
                raise ValueError(
                    f"golden question {identifier} authorization missing expected field: {field}"
                )
        if not isinstance(expected["authorization"]["allowed"], bool):
            raise TypeError(f"golden question {identifier} authorization allowed must be boolean")
        if not isinstance(expected["authorization"]["reason_code"], str):
            raise TypeError(f"golden question {identifier} authorization reason_code must be a string")
        deterministic = expected.get("deterministic")
        if not isinstance(deterministic, dict):
            raise TypeError(f"golden question {identifier} missing deterministic contract")
        has_answer = "answer" in deterministic
        has_constraints = "answer_constraints" in deterministic
        if has_answer == has_constraints:
            raise ValueError(
                f"golden question {identifier} deterministic contract must contain exactly one evidence form"
            )
        if has_answer:
            answer = deterministic["answer"]
            if not isinstance(answer, list) or any(
                not isinstance(row, dict)
                or set(row) != {"customer_id", "country", "claim_count", "total_incurred_loss_eur"}
                or not isinstance(row["customer_id"], str)
                or not isinstance(row["country"], str)
                or not isinstance(row["claim_count"], int)
                or not isinstance(row["total_incurred_loss_eur"], (int, float))
                for row in answer
            ):
                raise TypeError(f"golden question {identifier} deterministic answer must be typed rows")
        else:
            constraints = deterministic["answer_constraints"]
            if not isinstance(constraints, dict):
                raise TypeError(f"golden question {identifier} answer_constraints must be a mapping")
            unknown_fields = set(constraints) - {
                "mode", "metric", "required_metrics", "rule", "required_rules"
            }
            if unknown_fields:
                raise ValueError(
                    f"golden question {identifier} deterministic contract has unknown fields: "
                    f"{sorted(unknown_fields)}"
                )
            mode = constraints.get("mode")
            if mode not in {"discovery_only", "governed_primary_variant", "governed_threshold_variant"}:
                raise ValueError(f"golden question {identifier} has invalid deterministic mode: {mode!r}")
            if mode == "discovery_only" and not (
                isinstance(constraints.get("metric"), str) or isinstance(constraints.get("rule"), str)
            ):
                raise ValueError(f"golden question {identifier} discovery_only requires metric or rule evidence")
            if mode != "discovery_only":
                required_metrics = constraints.get("required_metrics")
                if (
                    not isinstance(required_metrics, list)
                    or not required_metrics
                    or any(not isinstance(metric, str) for metric in required_metrics)
                ):
                    raise TypeError(
                        f"golden question {identifier} executable variants require typed required_metrics"
                    )
        contract = DeterministicContract(
            mode=("governed_primary_variant" if has_answer else cast(DeterministicMode, mode)),
            answer=tuple(answer) if has_answer else None,
            answer_constraints=constraints if has_constraints else None,
        )
        seen.add(identifier)
        cases.append(GoldenCase(identifier, question, role, expected, contract))
    questions = [case.question for case in cases]
    if len(set(questions)) != len(questions):
        raise ValueError("golden questions must have unique natural-language question text")
    return cases


def _triples(discovery: QueryDiscovery) -> list[str]:
    return [
        f"{edge.source}|{edge.predicate}|{edge.target}"
        for edge in discovery.relationships
    ]


def _expected_list(expected: dict[str, Any], key: str) -> list[Any] | None:
    value = expected.get(key)
    return value if isinstance(value, list) else None


def _validate_answer_constraints(
    constraints: Any, registry: SemanticRegistry, discovery: QueryDiscovery | None
) -> tuple[bool, list[str]]:
    """Validate constraint references and semantics against registry discovery."""

    if not isinstance(constraints, dict):
        return False, ["answer_constraints must be a mapping"]
    mode = constraints.get("mode")
    if mode not in {"discovery_only", "governed_primary_variant", "governed_threshold_variant"}:
        return False, [f"unknown answer constraint mode: {mode!r}"]
    errors: list[str] = []
    if mode != "discovery_only" and not isinstance(constraints.get("required_metrics"), list):
        errors.append("executable answer constraints require required_metrics")
    actual_metrics = (
        {predicate.metric_id for predicate in discovery.metric_predicates}
        if discovery is not None
        else set()
    )
    actual_rules = {
        registry.metrics[metric_id].filter_rule
        for metric_id in actual_metrics
        if metric_id in registry.metrics and registry.metrics[metric_id].filter_rule
    }

    metric_ids: list[str] = []
    if "metric" in constraints:
        metric_ids.append(constraints["metric"])
    required_metrics = constraints.get("required_metrics", [])
    if not isinstance(required_metrics, list):
        errors.append("required_metrics must be a list")
    else:
        metric_ids.extend(required_metrics)
    for metric_id in metric_ids:
        if not isinstance(metric_id, str) or metric_id not in registry.metrics:
            errors.append(f"unknown governed metric: {metric_id}")
        elif metric_id not in actual_metrics:
            errors.append(f"metric {metric_id} is not present in discovered metrics")

    rule_ids: list[str] = []
    if "rule" in constraints:
        rule_ids.append(constraints["rule"])
    required_rules = constraints.get("required_rules", [])
    if not isinstance(required_rules, list):
        errors.append("required_rules must be a list")
    else:
        rule_ids.extend(required_rules)
    for rule_id in rule_ids:
        if not isinstance(rule_id, str) or rule_id not in registry.rules:
            errors.append(f"unknown governed rule: {rule_id}")
        elif rule_id not in actual_rules:
            errors.append(f"rule {rule_id} is not present in discovered metrics")

    if mode == "discovery_only" and not metric_ids and not rule_ids:
        errors.append("discovery_only constraints must reference a metric or rule")
    return not errors, errors


def _execute_case(
    case: GoldenCase, registry: SemanticRegistry, repository_root: Path, discovery: QueryDiscovery
) -> tuple[list[dict[str, Any]], list[str]]:
    """Run an executable golden variant and return rows plus evidence failures."""

    errors: list[str] = []
    try:
        with TemporaryDirectory(prefix="semantic-layer-evaluation-") as directory:
            agent = ClaimsInvestigationAgent(
                repository_root, provenance_path=Path(directory) / "provenance.sqlite"
            )
            actual = agent.answer(case.question, discovery.caller)
        rows = list(actual.rows)
        quality = actual.quality
        authorization = actual.authorization
        compiled_query = actual.compiled_query
        provenance = actual.provenance
        if quality.status != "PASS":
            errors.append(f"execution quality evidence is {quality.status}, not PASS")
        if provenance.quality_digest != quality.digest:
            errors.append("execution provenance quality evidence does not match quality report")
        if not authorization.allowed or authorization.reason_code != "ALLOWED":
            errors.append("execution authorization evidence is not an allowed decision")
        expected_metrics = tuple(predicate.metric_id for predicate in actual.plan.metric_predicates)
        if tuple(compiled_query.metric_ids) != expected_metrics or not expected_metrics:
            errors.append("compiled query metric evidence does not match the plan")
        if not provenance.query_id or not provenance._verify_integrity():
            errors.append("execution provenance evidence is missing or invalid")
        if provenance.plan_digest != compiled_query.plan_digest:
            errors.append("execution provenance plan evidence does not match compiled query")
        if provenance.query_digest != compiled_query.query_digest:
            errors.append("execution provenance query evidence does not match compiled query")
        if provenance.result_digest != digest(tuple(rows)):
            errors.append("execution provenance result evidence does not match returned rows")
        if tuple(provenance.metric_ids) != tuple(compiled_query.metric_ids):
            errors.append("execution provenance metric evidence does not match compiled query")
        return rows, errors
    except (AttributeError, TypeError, ValueError, PermissionError) as error:
        errors.append(f"execution evidence is unavailable: {error}")
        return [], errors


def _evaluate_case(
    case: GoldenCase, registry: SemanticRegistry, repository_root: Path
) -> CaseEvaluation:
    expected = case.expected
    errors: list[str] = []
    resolution_ok = relationship_ok = product_ok = metric_ok = authorization_ok = False
    deterministic_ok = False
    deterministic = expected.get("deterministic", {})
    if not isinstance(deterministic, dict):
        deterministic = {}
    deterministic_constraints = deterministic.get("answer_constraints")
    discovery_only = (
        isinstance(deterministic_constraints, dict)
        and deterministic_constraints.get("mode") == "discovery_only"
    )
    answer: list[dict[str, Any]] | None = None
    discovery: QueryDiscovery | None = None
    try:
        resolution = registry.resolve(case.question)
        expected_concepts = _expected_list(expected, "concepts")
        resolution_ok = expected_concepts is None or resolution.concept_ids == expected_concepts
        if not resolution_ok:
            errors.append(f"concepts expected {expected_concepts}, got {resolution.concept_ids}")
        discovery = discover_question(case.question, case.role, registry)
        expected_relationships = _expected_list(expected, "relationships")
        relationship_ok = expected_relationships is None or _triples(discovery) == expected_relationships
        if not relationship_ok:
            errors.append(f"relationships expected {expected_relationships}, got {_triples(discovery)}")
        expected_products = _expected_list(expected, "products")
        product_ok = expected_products is None or list(discovery.selected_products) == expected_products
        if not product_ok:
            errors.append(f"products expected {expected_products}, got {list(discovery.selected_products)}")
        expected_metrics = _expected_list(expected, "metrics")
        actual_metrics = [predicate.metric_id for predicate in discovery.metric_predicates]
        metric_ok = expected_metrics is None or actual_metrics == expected_metrics
        if not metric_ok:
            errors.append(f"metrics expected {expected_metrics}, got {actual_metrics}")
        authorization = authorize_discovery(discovery, discovery.caller, registry)
        expected_auth = expected.get("authorization", {})
        expected_allowed = expected_auth.get("allowed") if isinstance(expected_auth, dict) else None
        expected_reason = expected_auth.get("reason_code") if isinstance(expected_auth, dict) else None
        authorization_ok = (
            (expected_allowed is None or authorization.allowed == expected_allowed)
            and (expected_reason is None or authorization.reason_code == expected_reason)
        )
        if not authorization_ok:
            errors.append(
                f"authorization expected {expected_auth}, got "
                f"{{'allowed': {authorization.allowed}, 'reason_code': '{authorization.reason_code}'}}"
            )
    except (ValueError, PermissionError) as error:
        errors.append(str(error))

    expected_answer = deterministic.get("answer")
    if expected_answer is not None:
        try:
            if discovery is None:
                raise ValueError("deterministic answer requires successful semantic discovery")
            answer, execution_errors = _execute_case(case, registry, repository_root, discovery)
            errors.extend(execution_errors)
            deterministic_ok = not execution_errors and answer == expected_answer
        except (ValueError, PermissionError, TypeError) as error:
            deterministic_ok = False
            errors.append(f"deterministic answer: {error}")
        if not deterministic_ok:
            errors.append(f"answer expected {expected_answer}, got {answer}")
    elif "answer_constraints" in deterministic:
        constraints = deterministic["answer_constraints"]
        deterministic_ok, constraint_errors = _validate_answer_constraints(
            deterministic["answer_constraints"], registry, discovery
        )
        errors.extend(constraint_errors)
        if deterministic_ok and constraints.get("mode") == "discovery_only":
            discovery_only = True
        elif deterministic_ok and discovery is not None:
            try:
                answer, execution_errors = _execute_case(case, registry, repository_root, discovery)
                errors.extend(execution_errors)
                deterministic_ok = not execution_errors
                required_metrics = constraints.get("required_metrics", [])
                actual_metrics = [predicate.metric_id for predicate in discovery.metric_predicates]
                if not set(required_metrics).issubset(actual_metrics):
                    deterministic_ok = False
                    errors.append(
                        f"required metric evidence expected {required_metrics}, got {actual_metrics}"
                    )
            except (ValueError, PermissionError, TypeError) as error:
                deterministic_ok = False
                errors.append(f"deterministic variant execution: {error}")

    return CaseEvaluation(
        case_id=case.id,
        resolution=resolution_ok,
        relationships=relationship_ok,
        products=product_ok,
        metrics=metric_ok,
        authorization=authorization_ok,
        deterministic_answer=deterministic_ok,
        discovery_only=discovery_only,
        answer=answer,
        errors=tuple(errors),
    )


def _caller_for_case(case: GoldenCase, discovery: QueryDiscovery | None):
    """Build the simulated caller context used by a deterministic answer case."""

    if discovery is not None:
        return discovery.caller
    from semantic_layer.models import CallerContext

    return CallerContext(role=case.role)


def _dimension(results: list[CaseEvaluation], attribute: str) -> DimensionReport:
    failed = tuple(result.case_id for result in results if not getattr(result, attribute))
    return DimensionReport(len(results), len(results) - len(failed), failed)


def run_evaluation(registry: SemanticRegistry) -> EvaluationReport:
    """Evaluate the checked-in golden suite against one reviewed registry."""

    if type(registry) is not SemanticRegistry:
        raise TypeError("run_evaluation requires a SemanticRegistry")
    case_path = registry.root / "tests" / "golden" / "questions.yaml"
    if not case_path.is_file():
        case_path = GOLDEN_CASES
    cases = load_golden_cases(case_path)
    results = [_evaluate_case(case, registry, registry.root) for case in cases]
    failed_cases = [result.case_id for result in results if not result.passed]
    return EvaluationReport(
        total_cases=len(results),
        passed_cases=len(results) - len(failed_cases),
        failed_cases=failed_cases,
        results=results,
        resolution=_dimension(results, "resolution"),
        relationships=_dimension(results, "relationships"),
        products=_dimension(results, "products"),
        metrics=_dimension(results, "metrics"),
        authorization=_dimension(results, "authorization"),
        deterministic_answers=_dimension(results, "deterministic_answer"),
        discovery_only=_dimension(
            [result for result in results if result.discovery_only], "deterministic_answer"
        ),
    )
