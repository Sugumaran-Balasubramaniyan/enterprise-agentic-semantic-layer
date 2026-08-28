"""Deterministic evaluation of reviewed semantic-layer cases."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import yaml

from semantic_layer.agents import ClaimsInvestigationAgent
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
        seen.add(identifier)
        cases.append(GoldenCase(identifier, question, role, expected))
    return cases


def _triples(discovery: QueryDiscovery) -> list[str]:
    return [
        f"{edge.source}|{edge.predicate}|{edge.target}"
        for edge in discovery.relationships
    ]


def _expected_list(expected: dict[str, Any], key: str) -> list[Any] | None:
    value = expected.get(key)
    return value if isinstance(value, list) else None


def _evaluate_case(
    case: GoldenCase, registry: SemanticRegistry, repository_root: Path
) -> CaseEvaluation:
    expected = case.expected
    errors: list[str] = []
    resolution_ok = relationship_ok = product_ok = metric_ok = authorization_ok = False
    deterministic_ok = True
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

    deterministic = expected.get("deterministic", {})
    if not isinstance(deterministic, dict):
        deterministic = {}
    expected_answer = deterministic.get("answer")
    if expected_answer is not None:
        try:
            with TemporaryDirectory(prefix="semantic-layer-evaluation-") as directory:
                agent = ClaimsInvestigationAgent(
                    repository_root, provenance_path=Path(directory) / "provenance.sqlite"
                )
                actual_answer = agent.answer(
                    case.question,
                    # The agent's planner derives the country from the question. For the
                    # golden suite the role is the authenticated identity boundary.
                    agent.tools.discover(case.question, _caller_for_case(case, discovery)).caller,
                )
                answer = list(actual_answer.rows)
            deterministic_ok = answer == expected_answer
        except (ValueError, PermissionError, TypeError) as error:
            deterministic_ok = False
            errors.append(f"deterministic answer: {error}")
        if not deterministic_ok:
            errors.append(f"answer expected {expected_answer}, got {answer}")
    elif "answer_constraints" in deterministic:
        # Constraints are intentionally simple and data-independent so they can be
        # used for discovery-only cases without pretending they were executed.
        constraints = deterministic["answer_constraints"]
        deterministic_ok = isinstance(constraints, dict) and bool(constraints)
        if not deterministic_ok:
            errors.append("answer_constraints must be a non-empty mapping")

    return CaseEvaluation(
        case_id=case.id,
        resolution=resolution_ok,
        relationships=relationship_ok,
        products=product_ok,
        metrics=metric_ok,
        authorization=authorization_ok,
        deterministic_answer=deterministic_ok,
        answer=answer,
        errors=tuple(errors),
    )


def _caller_for_case(case: GoldenCase, discovery: QueryDiscovery | None):
    """Build the authenticated caller context used by a deterministic answer case."""

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
    )
