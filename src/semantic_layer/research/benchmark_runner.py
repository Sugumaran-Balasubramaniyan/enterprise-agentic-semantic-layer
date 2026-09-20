"""Deterministic, status-gated CIFRE benchmark execution.

The research benchmark has two deliberately narrow conditions. Both use the
same typed AQR path and differ only in whether the bounded repair budget is
available. This module contains no external baseline, model, or comparative
claims; all answer metrics are calculated from strict executed bindings.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import platform
import re
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from typing import Any

import jsonschema
import yaml
from pyshacl import validate as shacl_validate
from rdflib import RDF, Graph, Namespace
from rdflib.compare import to_canonical_graph

from semantic_layer.kg.loader import SAPKnowledgeGraph
from semantic_layer.reasoning.query_planner import (
    MAX_PREREQUISITE_DEPTH,
    evaluate_prerequisite_traversal,
)
from semantic_layer.reasoning.reflective_agent import AQRReflectiveAgent, ReasoningResult
from semantic_layer.reasoning.schema_linker import SchemaLinker
from semantic_layer.research.contracts import (
    CONDITIONS,
    NAMESPACE_REGISTRY,
    ReasonCode,
    Status,
    canonical_json,
)

_SIX_PLACES = Decimal("0.000001")
_STATUS_NAMES = tuple(status.value for status in Status)
_EXPECTED_CORPUS_QUERY_IDS = {
    "cifre-synthetic-aqr-v1": tuple(f"Q{index:02d}" for index in range(1, 41)),
    "cifre-synthetic-aqr-v2": tuple(f"Q{index:02d}" for index in range(1, 53)),
}
_LEGACY_URIS = [
    "http://data." + "sap" + ".com/",
    "http://ontology." + "sap" + ".com/",
    "https://" + "sap.example/erp/",
]
_MANIFEST_GLOBS = (
    ".github/workflows/ci.yml",
    "Makefile",
    "pyproject.toml",
    "constraints/py312.txt",
    "scripts/**/*.py",
    "semantic/**/*.ttl",
    "semantic/**/*.yaml",
    "semantic/**/*.json",
    "src/semantic_layer/**/*.py",
    "data/**/*.py",
    "tests/**/*.py",
    "tests/**/*.yaml",
    "tests/**/*.json",
    "README.md",
    "docs/**/*.md",
    "docs/**/*.json",
    "docs/**/*.sql",
    "mappings/**/*.yaml",
    "data_products/**/*.yaml",
    "examples/**/*",
    "results/**/*.json",
    "results/**/*.sql",
)
_EXCLUDED_MANIFEST_PATHS = {"results/latest_" + "benchmark.json"}
_CANONICAL_RESULT_NAME = next(iter(_EXCLUDED_MANIFEST_PATHS)).rsplit("/", 1)[-1]
_VALIDATION_DATA_PATHS = (
    "semantic/ontology/sap_support.ttl",
    "semantic/ontology/sap_ppms.ttl",
    "semantic/data/sap_support_graph.ttl",
    "semantic/ontology/sap_erp.ttl",
)
_VALIDATION_SAMPLE_DATA_PATH = "semantic/ontology/sample-graph-valid.ttl"
_VALIDATION_SHAPE_PATHS = (
    "semantic/shapes/sap_support_shapes.ttl",
    "semantic/shapes/sap_erp_shapes.ttl",
)
_PREREQUISITE_FIXTURE_MANIFEST = "semantic/data/support-prerequisite-fixtures.yaml"
_CIFMETA = Namespace("https://example.org/cifre-kg/meta#")
_CIFDATA = Namespace("https://example.org/cifre-kg/data/")
_SH = Namespace("http://www.w3.org/ns/shacl#")


def _as_status(value: Status | str) -> Status:
    if isinstance(value, Status):
        return value
    try:
        return Status(str(value))
    except ValueError as error:
        raise ValueError(f"unknown benchmark status: {value!r}") from error


def _validate_corpus(corpus: Mapping[str, Any]) -> None:
    """Require one of the two canonical corpora and its exact query IDs."""

    if not isinstance(corpus, Mapping):
        raise ValueError("benchmark corpus must be an object")  # noqa: TRY004
    corpus_id = corpus.get("corpus_id")
    if not isinstance(corpus_id, str) or corpus_id not in _EXPECTED_CORPUS_QUERY_IDS:
        raise ValueError(f"benchmark corpus must use an exact corpus ID: {corpus_id!r}")
    records = corpus.get("records")
    if not isinstance(records, list):
        raise TypeError(f"benchmark corpus {corpus_id} records must be an array")
    expected_query_ids = _EXPECTED_CORPUS_QUERY_IDS[corpus_id]
    if len(records) != len(expected_query_ids):
        raise ValueError(
            f"benchmark corpus {corpus_id} must contain exactly {len(expected_query_ids)} records"
        )
    query_ids: list[str] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise ValueError(f"invalid record in {corpus_id}")  # noqa: TRY004
        if record.get("corpus_id") != corpus_id:
            raise ValueError(f"record corpus mismatch in {corpus_id}")
        query_id = record.get("id")
        if not isinstance(query_id, str) or not query_id:
            raise ValueError(f"record in {corpus_id} is missing a query ID")
        query_ids.append(query_id)
    if sorted(query_ids) != list(expected_query_ids):
        raise ValueError(
            f"benchmark corpus {corpus_id} must use exact query IDs "
            f"{expected_query_ids[0]}–{expected_query_ids[-1]}"
        )
    linker = SchemaLinker()
    for record in records:
        expected_status = str(record.get("expected_status"))
        grounded = linker.ground_or_abstain(str(record.get("question", "")))
        if expected_status in {Status.SUCCESS.value, Status.EMPTY_RESULT.value}:
            if grounded.failure_class is not ReasonCode.NONE or grounded.intent == "UNSUPPORTED":
                raise ValueError(
                    f"corpus {corpus_id} record {record['id']} does not reach a supported "
                    f"grounded intent: {grounded.failure_class.value}"
                )
            continue
        if expected_status == Status.UNSUPPORTED.value:
            expected_reason = str(record.get("reflection_reason", ""))
            if grounded.intent != "UNSUPPORTED" or grounded.failure_class.value != expected_reason:
                raise ValueError(
                    f"corpus {corpus_id} record {record['id']} changed its declared "
                    f"unsupported contract: expected {expected_reason!r}, observed "
                    f"{grounded.failure_class.value!r}"
                )


def _decimal(value: Decimal | int | str) -> Decimal:
    return Decimal(str(value)).quantize(_SIX_PLACES, rounding=ROUND_HALF_EVEN)


def _decimal_string(value: Decimal | int | str) -> str:
    return f"{_decimal(value):.6f}"


def _ratio(numerator: Decimal | int, denominator: Decimal | int) -> str | None:
    if denominator == 0:
        return None
    return _decimal_string(Decimal(numerator) / Decimal(denominator))


def _metric(
    numerator: int | Decimal,
    denominator: int | Decimal,
    *,
    decimal_operands: bool = False,
) -> dict[str, Any]:
    value = _ratio(numerator, denominator)
    if decimal_operands:
        rendered_numerator: int | str = _decimal_string(numerator)
        rendered_denominator: int | str = _decimal_string(denominator)
    else:
        rendered_numerator = int(numerator)
        rendered_denominator = int(denominator)
    return {
        "value": value,
        "numerator": rendered_numerator,
        "denominator": rendered_denominator,
    }


@dataclass(frozen=True)
class QueryMetrics:
    """Status-gated strict answer metrics for one query."""

    applicable: bool
    exact_set: bool | None
    precision: str | None
    recall: str | None
    f1: str | None
    status_correct: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "applicable": self.applicable,
            "exact_set": self.exact_set,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
        }


@dataclass(frozen=True)
class QueryRecord:
    """Minimal typed input consumed by :func:`aggregate_metrics`."""

    corpus_id: str
    query_id: str
    condition: str
    expected_status: Status
    observed_status: Status
    gold_note_numbers: Sequence[str] = ()
    predicted_note_numbers: Sequence[str] = ()
    relaxed_candidates: Sequence[Any] = ()
    tier: int | None = None
    category: str | None = None
    attempts: int = 1
    recovery_attempted: bool = False
    recovery_success: bool = False
    binding_count: int = 0
    optional_binding_count: int = 0
    metrics: QueryMetrics | None = None
    gold: Sequence[str] | None = None
    predicted: Sequence[str] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "expected_status", _as_status(self.expected_status))
        object.__setattr__(self, "observed_status", _as_status(self.observed_status))
        object.__setattr__(self, "gold_note_numbers", tuple(self.gold_note_numbers))
        object.__setattr__(self, "predicted_note_numbers", tuple(self.predicted_note_numbers))
        object.__setattr__(self, "relaxed_candidates", tuple(self.relaxed_candidates))

    @property
    def gold_values(self) -> tuple[str, ...]:
        return tuple(self.gold if self.gold is not None else self.gold_note_numbers)

    @property
    def predicted_values(self) -> tuple[str, ...]:
        return tuple(self.predicted if self.predicted is not None else self.predicted_note_numbers)

    def scored_metrics(self) -> QueryMetrics:
        return self.metrics or score_query(
            self.expected_status,
            self.observed_status,
            self.gold_values,
            self.predicted_values,
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> QueryRecord:
        return cls(
            corpus_id=str(value["corpus_id"]),
            query_id=str(value["query_id"]),
            condition=str(value["condition"]),
            expected_status=_as_status(value["expected_status"]),
            observed_status=_as_status(value["observed_status"]),
            gold_note_numbers=tuple(value.get("gold_note_numbers", value.get("gold", ()))),
            predicted_note_numbers=tuple(
                value.get("predicted_note_numbers", value.get("predicted", ()))
            ),
            relaxed_candidates=tuple(value.get("relaxed_candidates", ())),
            tier=value.get("tier"),
            category=value.get("category"),
            attempts=int(value.get("attempts", 1)),
            recovery_attempted=bool(value.get("recovery_attempted", False)),
            recovery_success=bool(value.get("recovery_success", False)),
            binding_count=int(value.get("binding_count", 0)),
            optional_binding_count=int(value.get("optional_binding_count", 0)),
        )


@dataclass(frozen=True)
class HashManifest(Mapping[str, Any]):
    """Canonical byte manifest for the complete Spec §26.6 input scope."""

    manifest_version: str
    entries: tuple[dict[str, Any], ...]
    digest_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "entries": [dict(entry) for entry in self.entries],
            "digest_sha256": self.digest_sha256,
        }

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __iter__(self):
        return iter(("manifest_version", "entries", "digest_sha256"))

    def __len__(self) -> int:
        return 3


ConditionAggregate = dict[str, Any]


def score_query(
    expected_status: Status,
    observed_status: Status,
    gold: Sequence[str],
    predicted: Sequence[str],
) -> QueryMetrics:
    """Score one strict prediction using status-gated exact-set semantics."""

    expected = _as_status(expected_status)
    observed = _as_status(observed_status)
    status_correct = expected is observed
    applicable = expected is Status.SUCCESS and observed is Status.SUCCESS
    if not applicable:
        return QueryMetrics(False, None, None, None, None, status_correct)

    gold_set = {str(item) for item in gold}
    predicted_set = {str(item) for item in predicted}
    intersection = len(gold_set & predicted_set)
    exact = gold_set == predicted_set
    if not gold_set and not predicted_set:
        precision = recall = f1 = "1.000000"
    elif not gold_set or not predicted_set:
        precision = recall = f1 = "0.000000"
    else:
        precision_decimal = Decimal(intersection) / Decimal(len(predicted_set))
        recall_decimal = Decimal(intersection) / Decimal(len(gold_set))
        f1_decimal = (
            Decimal(0)
            if precision_decimal + recall_decimal == 0
            else (Decimal(2) * precision_decimal * recall_decimal)
            / (precision_decimal + recall_decimal)
        )
        precision = _decimal_string(precision_decimal)
        recall = _decimal_string(recall_decimal)
        f1 = _decimal_string(f1_decimal)
    return QueryMetrics(True, exact, precision, recall, f1, status_correct)


def _status_counts(records: Sequence[QueryRecord]) -> dict[str, int]:
    counts = {name: 0 for name in _STATUS_NAMES}
    for record in records:
        counts[record.observed_status.value] += 1
    return counts


def _macro_metric_group(records: Sequence[QueryRecord]) -> dict[str, Any]:
    applicable = [record for record in records if record.scored_metrics().applicable]
    if not applicable:
        null_metric = _metric(0, 0)
        return {name: null_metric for name in ("exact_set", "precision", "recall", "f1")}
    metrics = [record.scored_metrics() for record in applicable]
    return {
        "exact_set": _metric(sum(bool(metric.exact_set) for metric in metrics), len(metrics)),
        "precision": _metric(
            sum(Decimal(metric.precision or "0") for metric in metrics),
            len(metrics),
            decimal_operands=True,
        ),
        "recall": _metric(
            sum(Decimal(metric.recall or "0") for metric in metrics),
            len(metrics),
            decimal_operands=True,
        ),
        "f1": _metric(
            sum(Decimal(metric.f1 or "0") for metric in metrics),
            len(metrics),
            decimal_operands=True,
        ),
    }


def _micro_metric_group(records: Sequence[QueryRecord]) -> dict[str, Any]:
    applicable = [record for record in records if record.scored_metrics().applicable]
    if not applicable:
        null_metric = _metric(0, 0)
        return {name: null_metric for name in ("exact_set", "precision", "recall", "f1")}
    true_positive = predicted_total = gold_total = exact_numerator = 0
    for record in applicable:
        gold = set(record.gold_values)
        predicted = set(record.predicted_values)
        true_positive += len(gold & predicted)
        predicted_total += len(predicted)
        gold_total += len(gold)
        exact_numerator += int(gold == predicted)
    if predicted_total == 0 and gold_total == 0:
        precision = recall = f1 = "1.000000"
    elif predicted_total == 0 or gold_total == 0:
        precision = recall = f1 = "0.000000"
    else:
        precision_decimal = Decimal(true_positive) / Decimal(predicted_total)
        recall_decimal = Decimal(true_positive) / Decimal(gold_total)
        f1_decimal = (
            Decimal(0)
            if precision_decimal + recall_decimal == 0
            else (Decimal(2) * precision_decimal * recall_decimal)
            / (precision_decimal + recall_decimal)
        )
        precision = _decimal_string(precision_decimal)
        recall = _decimal_string(recall_decimal)
        f1 = _decimal_string(f1_decimal)
    return {
        "exact_set": _metric(exact_numerator, len(applicable)),
        "precision": {
            "value": precision,
            "numerator": _decimal_string(true_positive),
            "denominator": _decimal_string(predicted_total),
        },
        "recall": {
            "value": recall,
            "numerator": _decimal_string(true_positive),
            "denominator": _decimal_string(gold_total),
        },
        "f1": {
            "value": f1,
            "numerator": _decimal_string(Decimal(2) * true_positive),
            "denominator": _decimal_string(predicted_total + gold_total),
        },
    }


def _optional_binding_rate(records: Sequence[QueryRecord]) -> dict[str, Any]:
    numerator = sum(record.optional_binding_count for record in records)
    denominator = sum(record.binding_count for record in records)
    return _metric(numerator, denominator)


def _aggregate_slice(records: Sequence[QueryRecord]) -> dict[str, Any]:
    macro = _macro_metric_group(records)
    return {
        "query_count": len(records),
        "status_counts": _status_counts(records),
        "applicable_count": sum(record.scored_metrics().applicable for record in records),
        "not_applicable_count": sum(not record.scored_metrics().applicable for record in records),
        "exact_set": macro["exact_set"],
        "precision": macro["precision"],
        "recall": macro["recall"],
        "f1": macro["f1"],
        "micro": _micro_metric_group(records),
        "macro": macro,
        "optional_binding_rate": _optional_binding_rate(records),
    }


def aggregate_metrics(records: Sequence[QueryRecord]) -> ConditionAggregate:
    """Aggregate one condition without ever scoring relaxed candidates."""

    normalized = [
        record if isinstance(record, QueryRecord) else QueryRecord.from_mapping(record)
        for record in records
    ]
    macro = _macro_metric_group(normalized)
    micro = _micro_metric_group(normalized)
    applicable_count = sum(record.scored_metrics().applicable for record in normalized)
    not_applicable_count = len(normalized) - applicable_count
    expected_unsupported = sum(
        record.expected_status is Status.UNSUPPORTED for record in normalized
    )
    observed = [record.observed_status for record in normalized]
    operational = {
        "syntax_success_rate": _metric(
            sum(status is not Status.SYNTAX_ERROR for status in observed), len(normalized)
        ),
        "execution_success_rate": _metric(
            sum(status in {Status.SUCCESS, Status.EMPTY_RESULT} for status in observed),
            len(normalized),
        ),
        "recovery_attempt_rate": _metric(
            sum(record.recovery_attempted for record in normalized), len(normalized)
        ),
        "recovery_success_rate": _metric(
            sum(record.recovery_success for record in normalized),
            sum(record.recovery_attempted for record in normalized),
        ),
        "strict_empty_rate": _metric(
            sum(status is Status.EMPTY_RESULT for status in observed), len(normalized)
        ),
        "unsupported_rejection_rate": _metric(
            sum(
                record.expected_status is Status.UNSUPPORTED
                and record.observed_status is Status.UNSUPPORTED
                for record in normalized
            ),
            expected_unsupported,
        ),
        "optional_binding_rate": _optional_binding_rate(normalized),
    }
    by_tier = {
        str(tier): _aggregate_slice([record for record in normalized if record.tier == tier])
        for tier in sorted({record.tier for record in normalized if record.tier is not None})
    }
    by_category = {
        str(category): _aggregate_slice(
            [record for record in normalized if record.category == category]
        )
        for category in sorted(
            {record.category for record in normalized if record.category is not None}
        )
    }
    return {
        "query_count": len(normalized),
        "status_counts": _status_counts(normalized),
        "status_accuracy": _metric(
            sum(record.scored_metrics().status_correct for record in normalized),
            len(normalized),
        ),
        "answer_metrics": {
            "applicable_count": applicable_count,
            "not_applicable_count": not_applicable_count,
            "exact_set": macro["exact_set"],
            "precision": macro["precision"],
            "recall": macro["recall"],
            "f1": macro["f1"],
            "micro": micro,
            "macro": macro,
            "by_tier": by_tier,
            "by_category": by_category,
        },
        "operational_metrics": operational,
    }


def _tracked_paths(root: Path) -> set[str]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise ValueError(f"cannot enumerate tracked hash inputs under {root}") from error
    return {path for path in completed.stdout.decode("utf-8").split("\0") if path}


def _manifest_candidates(root: Path) -> list[str]:
    tracked = _tracked_paths(root)
    candidates: set[str] = set()
    for pattern in _MANIFEST_GLOBS:
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            if relative in tracked and relative not in _EXCLUDED_MANIFEST_PATHS:
                candidates.add(relative)
    if any(path.startswith((".git/", ".venv/")) for path in candidates):
        raise ValueError("forbidden hash-manifest path")
    return sorted(candidates)


def build_hash_manifest(root: Path) -> HashManifest:
    """Build the sorted byte manifest required by Spec §26.6."""

    repository_root = Path(root).resolve()
    entries: list[dict[str, Any]] = []
    digest_lines: list[bytes] = []
    for relative in _manifest_candidates(repository_root):
        data = (repository_root / relative).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        entries.append({"path": relative, "sha256": digest, "byte_length": len(data)})
        digest_lines.append(f"{relative}\0{digest}\0{len(data)}\n".encode())
    return HashManifest(
        manifest_version="1.0",
        entries=tuple(entries),
        digest_sha256=hashlib.sha256(b"".join(digest_lines)).hexdigest(),
    )


def _manifest_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, HashManifest):
        return value.to_dict()
    if not isinstance(value, Mapping):
        raise ValueError("hash manifest must be an object")  # noqa: TRY004
    return {
        "manifest_version": value.get("manifest_version"),
        "entries": value.get("entries"),
        "digest_sha256": value.get("digest_sha256"),
    }


def validate_hash_manifest(result: Mapping[str, Any], root: Path) -> None:
    """Fail closed when any manifest-covered input changed."""

    if not isinstance(result, Mapping) or "hash_manifest" not in result:
        raise ValueError("result has no hash manifest")
    expected = _manifest_dict(result["hash_manifest"])
    actual = build_hash_manifest(root).to_dict()
    if expected != actual:
        raise ValueError("hash manifest does not match current input bytes")


def _result_key(value: Mapping[str, Any]) -> str:
    for field in ("corpus_id", "condition", "query_id"):
        if not isinstance(value.get(field), str) or not value[field]:
            raise ValueError(f"per-query record missing {field}")
    return f"{value['corpus_id']}:{value['condition']}:{value['query_id']}"


def validate_result_id_references(result: Mapping[str, Any]) -> None:
    """Validate exact composite result IDs and reject duplicates/fabrication."""

    if not isinstance(result, Mapping):
        raise ValueError("result must be a mapping")  # noqa: TRY004
    per_query = result.get("per_query")
    corpus_runs = result.get("corpus_runs")
    if not isinstance(per_query, Sequence) or isinstance(per_query, (str, bytes)):
        raise ValueError("per_query must be an array")  # noqa: TRY004
    if not isinstance(corpus_runs, Sequence) or isinstance(corpus_runs, (str, bytes)):
        raise ValueError("corpus_runs must be an array")  # noqa: TRY004
    keys: set[str] = set()
    by_corpus: dict[str, set[str]] = {}
    for value in per_query:
        if not isinstance(value, Mapping):
            raise ValueError("per-query record must be an object")  # noqa: TRY004
        key = _result_key(value)
        if key in keys:
            raise ValueError(f"duplicate composite result ID: {key}")
        keys.add(key)
        by_corpus.setdefault(str(value["corpus_id"]), set()).add(key)
    seen_ids: set[str] = set()
    referenced: set[str] = set()
    for corpus_run in corpus_runs:
        if not isinstance(corpus_run, Mapping):
            raise ValueError("corpus run must be an object")  # noqa: TRY004
        corpus_id = corpus_run.get("corpus_id")
        result_ids = corpus_run.get("result_ids")
        if not isinstance(corpus_id, str) or not isinstance(result_ids, Sequence):
            raise ValueError("corpus run result_ids must be an array")  # noqa: TRY004
        expected_for_corpus = by_corpus.get(corpus_id, set())
        local: set[str] = set()
        for result_id in result_ids:
            if not isinstance(result_id, str):
                raise ValueError("result ID must be a string")  # noqa: TRY004
            if result_id in local or result_id in seen_ids:
                raise ValueError(f"duplicate result ID: {result_id}")
            local.add(result_id)
            seen_ids.add(result_id)
            if result_id not in keys or not result_id.startswith(f"{corpus_id}:"):
                raise ValueError(f"result ID does not reference a composite result ID: {result_id}")
            if len(result_id.split(":")) != 3:
                raise ValueError(f"result ID is not an exact composite key: {result_id}")
            referenced.add(result_id)
        if local != expected_for_corpus:
            raise ValueError(f"result IDs for corpus {corpus_id} do not match per_query")
    if referenced != keys:
        missing = sorted(keys - referenced)
        raise ValueError(f"unreferenced composite result IDs: {missing}")


def _schema_path() -> Path:
    return Path(__file__).resolve().parents[3] / "tests/research/result_schema.json"


def _walk_mapping_keys(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key)
            yield from _walk_mapping_keys(item)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            yield from _walk_mapping_keys(item)


_FORBIDDEN_STRING_SENTINELS = frozenset({"None", "NaN", "Infinity", "-Infinity"})


def _reject_forbidden_values(value: Any, *, path: str = "result") -> None:
    """Reject non-JSON finite values and string sentinels at every depth."""

    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"forbidden non-finite value at {path}")
    if isinstance(value, str) and value in _FORBIDDEN_STRING_SENTINELS:
        raise ValueError(f"forbidden sentinel value at {path}")
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_forbidden_values(str(key), path=f"{path}.<key>")
            _reject_forbidden_values(item, path=f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, item in enumerate(value):
            _reject_forbidden_values(item, path=f"{path}[{index}]")


def _reject_metadata_nulls(value: Mapping[str, Any]) -> None:
    _reject_forbidden_values(value)
    for section in ("environment", "namespace_registry", "validation", "hash_manifest"):
        if section not in value:
            raise ValueError(f"result missing metadata section: {section}")
    if any(
        str(key).casefold() in {"timestamp", "generated_at", "created_at"}
        for key in _walk_mapping_keys(value)
    ):
        raise ValueError("timestamp key is forbidden in result artifact")


def _validate_result_mapping(result: Mapping[str, Any]) -> None:
    if not isinstance(result, Mapping):
        raise ValueError("result artifact must be a mapping")  # noqa: TRY004
    _reject_metadata_nulls(result)
    validate_result_id_references(result)
    schema = json.loads(_schema_path().read_bytes())
    jsonschema.Draft202012Validator(schema).validate(dict(result))
    canonical_json(result)


def write_result_artifact(result: Mapping[str, Any], path: Path) -> None:
    """Validate and write one caller-selected canonical temporary artifact."""

    normalized = _json_payload(result)
    if not isinstance(normalized, Mapping):
        raise ValueError("result artifact must be a mapping")  # noqa: TRY004
    _validate_result_mapping(normalized)
    destination = Path(path)
    if destination.exists() and destination.is_dir():
        raise ValueError("result artifact path is a directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(canonical_json(dict(normalized)) + b"\n")


def _sha256_file(root: Path, relative: str) -> str:
    path = root / relative
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "0" * 64


def _environment(root: Path) -> dict[str, Any]:
    lock_path = root / "constraints/py312.txt"
    packages: dict[str, str] = {}
    if lock_path.exists():
        for line in lock_path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^([A-Za-z0-9_.-]+)==([^\s\\]+)", line.strip())
            if match:
                packages[match.group(1)] = match.group(2)
    try:
        pip_version = importlib.metadata.version("pip")
    except importlib.metadata.PackageNotFoundError:
        pip_version = "unavailable"
    return {
        "python_version": platform.python_version(),
        "platform_system": platform.system(),
        "platform_machine": platform.machine(),
        "pip_version": pip_version,
        "lock_sha256": _sha256_file(root, "constraints/py312.txt"),
        "packages": dict(sorted(packages.items())),
    }


def _load_rdf_graph(root: Path, paths: Sequence[str]) -> Graph:
    graph = Graph()
    for relative in paths:
        path = root / relative
        if not path.is_file():
            raise ValueError(f"validation asset is missing: {relative}")
        graph.parse(path, format="turtle")
    return graph


def _canonical_graph_sha256(graph: Graph) -> str:
    serialized = to_canonical_graph(graph).serialize(format="nt")
    text = serialized.decode("utf-8") if isinstance(serialized, bytes) else str(serialized)
    lines = sorted(line.strip() for line in text.splitlines() if line.strip())
    return hashlib.sha256(("\n".join(lines) + "\n").encode("utf-8")).hexdigest()


def _validation_dataset_id(graph: Graph) -> str:
    dataset_ids = sorted({str(value) for value in graph.objects(None, _CIFMETA.datasetId)})
    if not dataset_ids:
        raise ValueError("validation graph is missing synthetic dataset provenance")
    return "+".join(dataset_ids)


def _run_shacl(data_graph: Graph, shapes_graph: Graph) -> tuple[bool, int]:
    conforms, report_graph, _ = shacl_validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        abort_on_first=False,
        advanced=False,
        js=False,
        meta_shacl=False,
    )
    violation_count = len(set(report_graph.subjects(RDF.type, _SH.ValidationResult)))
    return bool(conforms), violation_count


def _validation_result(expected: bool, observed: bool) -> str:
    if expected == observed:
        return "PASS" if expected else "EXPECTED_NONCONFORMANT"
    return "FAIL"


def _load_prerequisite_fixture_manifest(root: Path) -> dict[str, dict[str, str]]:
    path = root / _PREREQUISITE_FIXTURE_MANIFEST
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, Mapping) or document.get("schema_version") != "1.0":
        raise ValueError("invalid prerequisite fixture manifest")
    if document.get("source_kind") != "synthetic_fixture":
        raise ValueError("prerequisite fixture manifest must be synthetic")
    fixtures = document.get("fixtures")
    if not isinstance(fixtures, list):
        raise TypeError("prerequisite fixture manifest has no fixture list")
    indexed: dict[str, dict[str, str]] = {}
    for fixture in fixtures:
        if not isinstance(fixture, Mapping):
            raise TypeError("invalid prerequisite fixture manifest entry")
        required = {"path", "dataset_id", "target"}
        if set(fixture) != required:
            raise ValueError("prerequisite fixture manifest entry fields are incomplete")
        relative = str(fixture["path"])
        if not (root / relative).is_file():
            raise ValueError(f"prerequisite fixture is missing: {relative}")
        indexed[relative] = {
            "dataset_id": str(fixture["dataset_id"]),
            "target": str(fixture["target"]),
        }
    return indexed


def _shacl_check(
    root: Path,
    check_id: str,
    data_paths: Sequence[str],
    shape_paths: Sequence[str],
    expected: bool,
    *,
    scope: str,
    data_graph: Graph | None = None,
    shapes_graph: Graph | None = None,
) -> dict[str, Any]:
    if data_graph is None:
        data_graph = _load_rdf_graph(root, data_paths)
    if shapes_graph is None:
        shapes_graph = _load_rdf_graph(root, shape_paths)
    observed, violation_count = _run_shacl(data_graph, shapes_graph)
    return {
        "check_id": check_id,
        "data_paths": list(data_paths),
        "shape_paths": list(shape_paths),
        "inference": "rdfs",
        "expected_conforms": expected,
        "observed_conforms": observed,
        "conforms": observed,
        "violation_count": violation_count,
        "data_sha256": [_sha256_file(root, path) for path in data_paths],
        "shape_sha256": [_sha256_file(root, path) for path in shape_paths],
        "provenance_dataset_id": _validation_dataset_id(data_graph),
        "scope": scope,
        "result": _validation_result(expected, observed),
    }


def _prerequisite_algorithm_case(
    root: Path, fixture: str, target: str, provenance_dataset_id: str
) -> dict[str, Any]:
    graph = _load_rdf_graph(root, (fixture,))
    evidence = evaluate_prerequisite_traversal(
        graph,
        _CIFDATA[target],
        depth_limit=MAX_PREREQUISITE_DEPTH,
    )
    return {
        "fixture": Path(fixture).name,
        "provenance_dataset_id": provenance_dataset_id,
        "cycle_detected": evidence.cycle_detected,
        "cycle_edges": [list(edge) for edge in evidence.cycle_edges],
        "reachable_unique": list(evidence.reachable_unique),
        "target_excluded": evidence.target_excluded,
        "depth_limit": evidence.depth_limit,
        "truncated": evidence.truncated,
        "status": evidence.status.value,
        "reason": evidence.reason.value if evidence.reason is not None else None,
    }


def build_validation_metadata(root: Path) -> dict[str, Any]:
    """Build the single-source validation evidence consumed by the artifact.

    The benchmark artifact and later repository verification must call this
    interface rather than reimplementing the SHACL matrix or prerequisite
    cycle/depth evidence.
    """

    combined_data_paths = (*_VALIDATION_DATA_PATHS, _VALIDATION_SAMPLE_DATA_PATH)
    combined_shape_paths = _VALIDATION_SHAPE_PATHS
    combined_graph = _load_rdf_graph(root, combined_data_paths)
    combined_shapes = _load_rdf_graph(root, combined_shape_paths)
    combined_check = _shacl_check(
        root,
        "COMBINED_VALID",
        combined_data_paths,
        combined_shape_paths,
        True,
        scope="combined",
        data_graph=combined_graph,
        shapes_graph=combined_shapes,
    )
    checks = [
        _shacl_check(
            root,
            "SUPPORT_VALID",
            ("semantic/data/sap_support_graph.ttl",),
            ("semantic/shapes/sap_support_shapes.ttl",),
            True,
            scope="support",
        ),
        _shacl_check(
            root,
            "SUPPORT_INVALID",
            ("semantic/data/support-graph-invalid.ttl",),
            ("semantic/shapes/sap_support_shapes.ttl",),
            False,
            scope="support",
        ),
        _shacl_check(
            root,
            "ERP_VALID",
            (_VALIDATION_SAMPLE_DATA_PATH,),
            ("semantic/shapes/sap_erp_shapes.ttl",),
            True,
            scope="erp",
        ),
        _shacl_check(
            root,
            "ERP_INVALID",
            ("semantic/ontology/sample-graph-invalid.ttl",),
            ("semantic/shapes/sap_erp_shapes.ttl",),
            False,
            scope="erp",
        ),
        combined_check,
    ]
    fixture_manifest = _load_prerequisite_fixture_manifest(root)
    algorithm_fixtures = (
        "semantic/data/support-prerequisite-cycle.ttl",
        "semantic/data/support-prerequisite-depth17.ttl",
    )
    checks.append(
        {
            "check_id": "PREREQUISITE_CYCLE_DEPTH",
            "data_paths": list(algorithm_fixtures),
            "shape_paths": [],
            "fixture_manifest": _PREREQUISITE_FIXTURE_MANIFEST,
            "fixture_manifest_sha256": _sha256_file(root, _PREREQUISITE_FIXTURE_MANIFEST),
            "inference": "algorithm",
            "expected_conforms": None,
            "observed_conforms": None,
            "conforms": None,
            "violation_count": 0,
            "data_sha256": [_sha256_file(root, path) for path in algorithm_fixtures],
            "shape_sha256": [],
            "provenance_dataset_id": "cifre-synthetic-support-prerequisite-fixtures",
            "scope": "support",
            "algorithm_cases": [
                _prerequisite_algorithm_case(
                    root,
                    algorithm_fixtures[0],
                    fixture_manifest[algorithm_fixtures[0]]["target"],
                    fixture_manifest[algorithm_fixtures[0]]["dataset_id"],
                ),
                _prerequisite_algorithm_case(
                    root,
                    algorithm_fixtures[1],
                    fixture_manifest[algorithm_fixtures[1]]["target"],
                    fixture_manifest[algorithm_fixtures[1]]["dataset_id"],
                ),
            ],
            "result": "PASS",
        }
    )
    return {
        "checks": checks,
        "combined_graph": {
            "data_paths": list(combined_data_paths),
            "shape_paths": list(combined_shape_paths),
            "construction_order": [*combined_data_paths, *combined_shape_paths],
            "combined_graph_sha256": _canonical_graph_sha256(combined_graph),
            "combined_shapes_sha256": _canonical_graph_sha256(combined_shapes),
            "inference": "rdfs",
            "conforms": combined_check["observed_conforms"],
            "violation_count": combined_check["violation_count"],
        },
    }


def _normalise_note_numbers(values: Sequence[Any]) -> list[str]:
    return sorted({str(value) for value in values if value is not None})


def _json_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_payload(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [_json_payload(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (Status, ReasonCode)):
        return value.value
    return str(value)


def _record_payload(
    corpus: Mapping[str, Any],
    item: Mapping[str, Any],
    condition: str,
    result: ReasoningResult,
) -> tuple[dict[str, Any], QueryRecord]:
    expected = _as_status(item["expected_status"])
    observed = result.status
    strict_predicted = _normalise_note_numbers(result.predicted_note_numbers)
    gold = _normalise_note_numbers(item.get("gold_note_numbers", ()))
    metrics = score_query(expected, observed, gold, strict_predicted)
    serialized = result.to_dict()
    grounding = serialized.get("grounding")
    if observed is Status.UNSUPPORTED:
        grounding = None
    sparql = None
    if (
        observed is not Status.UNSUPPORTED
        or serialized.get("sparql_initial")
        or serialized.get("sparql_final")
    ):
        sparql = {
            "initial": serialized.get("sparql_initial"),
            "final": serialized.get("sparql_final"),
        }
    bindings = _json_payload(serialized.get("bindings", []))
    relaxed = _json_payload(serialized.get("relaxed_candidates", []))
    optional_count = sum(
        1
        for binding in bindings
        if isinstance(binding, Mapping) and any(value is None for value in binding.values())
    )
    record = QueryRecord(
        corpus_id=str(corpus["corpus_id"]),
        query_id=str(item["id"]),
        condition=condition,
        expected_status=expected,
        observed_status=observed,
        gold_note_numbers=tuple(gold),
        predicted_note_numbers=tuple(strict_predicted),
        relaxed_candidates=tuple(relaxed),
        tier=int(item.get("tier", 0)),
        category=str(item.get("category", "")),
        attempts=int(result.attempts),
        recovery_attempted=bool(result.repair.recovery_attempt),
        recovery_success=bool(result.repair.recovery_success),
        binding_count=len(bindings),
        optional_binding_count=optional_count,
        metrics=metrics,
    )
    payload = {
        "schema_version": "1.0.0",
        "corpus_id": str(corpus["corpus_id"]),
        "query_id": str(item["id"]),
        "condition": condition,
        "question": str(item["question"]),
        "normalized_request": str(serialized.get("normalized_request", "")),
        "expected_status": expected.value,
        "observed_status": observed.value,
        "reason_code": result.reason_code.value,
        "original_constraints": _json_payload(serialized.get("original_constraints", {})),
        "grounding": _json_payload(grounding),
        "plan": _json_payload(serialized.get("plan")),
        "sparql": _json_payload(sparql),
        "attempts": int(result.attempts),
        "repair": _json_payload(serialized.get("repair", {})),
        "relaxation": _json_payload(serialized.get("relaxation", {})),
        "answer_scope": str(serialized.get("answer_scope", "none")),
        "relaxed_candidates": relaxed,
        "bindings": bindings,
        "predicted_note_numbers": strict_predicted,
        "gold_note_numbers": gold,
        "metrics": metrics.to_dict(),
        "provenance": _json_payload(serialized.get("provenance", {})),
    }
    return payload, record


class BenchmarkRunner:
    """Run exactly the v1/v2 synthetic corpora under two deterministic conditions."""

    def __init__(
        self,
        knowledge_graph: SAPKnowledgeGraph,
        dataset_paths: Sequence[Path] | None = None,
        result_path: Path | None = None,
        *,
        dataset_path: str | Path | None = None,
    ) -> None:
        if dataset_paths is None:
            if dataset_path is None:
                raise ValueError("dataset_paths and result_path are caller-supplied")
            dataset_paths = (Path(dataset_path),)
        if result_path is None:
            raise ValueError("result_path must be caller-supplied and temporary")
        self.kg = knowledge_graph
        self.dataset_paths = tuple(Path(path) for path in dataset_paths)
        self.result_path = Path(result_path)
        if (
            self.result_path.name == _CANONICAL_RESULT_NAME
            and self.result_path.parent.name == "results"
        ):
            raise ValueError("the canonical result path is reserved for final publication")
        if len(self.dataset_paths) != 2:
            raise ValueError("benchmark runner requires exactly v1 and v2 datasets")
        self.root = Path(__file__).resolve().parents[3]
        self.agent = AQRReflectiveAgent(knowledge_graph)

    def _load_dataset(self, path: Path) -> dict[str, Any]:
        resolved = path if path.is_absolute() else self.root / path
        if not resolved.exists():
            raise FileNotFoundError(f"benchmark dataset not found: {resolved}")
        # The migrated corpora contain plain scalar questions ending in ``?``.
        # PyYAML's C loader preserves those records as mappings consistently
        # across the supported Python 3.12 environments; the pure-Python
        # loader misinterprets some of them as flow-style mapping keys.
        loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
        value = yaml.load(resolved.read_text(encoding="utf-8"), Loader=loader)
        if not isinstance(value, Mapping) or not isinstance(value.get("records"), list):
            raise ValueError(f"invalid benchmark dataset: {resolved}")  # noqa: TRY004
        return dict(value)

    def _build_result(self) -> dict[str, Any]:
        loaded_datasets = [(path, self._load_dataset(path)) for path in self.dataset_paths]
        loaded_datasets.sort(key=lambda pair: str(pair[1]["corpus_id"]))
        corpus_ids = [str(corpus.get("corpus_id")) for _, corpus in loaded_datasets]
        if sorted(corpus_ids) != sorted(_EXPECTED_CORPUS_QUERY_IDS):
            raise ValueError(
                "benchmark runner requires exactly the v1 and v2 corpus IDs "
                f"{sorted(_EXPECTED_CORPUS_QUERY_IDS)}"
            )
        per_query: list[dict[str, Any]] = []
        corpus_runs: list[dict[str, Any]] = []
        for dataset_path, corpus in loaded_datasets:
            records = corpus["records"]
            corpus_id = str(corpus["corpus_id"])
            _validate_corpus(corpus)
            internal_by_condition: dict[str, list[QueryRecord]] = {}
            ids_by_condition: dict[str, list[str]] = {}
            for condition in CONDITIONS:
                condition_records: list[QueryRecord] = []
                for item in records:
                    if not isinstance(item, Mapping):
                        raise ValueError(f"invalid record in {corpus_id}")  # noqa: TRY004
                    if str(item.get("corpus_id")) != corpus_id:
                        raise ValueError(f"record corpus mismatch in {corpus_id}")
                    repair_budget = 0 if condition == CONDITIONS[0] else 3
                    reasoning = self.agent.run(
                        str(item["question"]),
                        condition=condition,
                        max_repairs=repair_budget,
                    )
                    payload, internal = _record_payload(corpus, item, condition, reasoning)
                    per_query.append(payload)
                    condition_records.append(internal)
                internal_by_condition[condition] = condition_records
                ids_by_condition[condition] = [
                    f"{corpus_id}:{condition}:{record.query_id}" for record in condition_records
                ]
            aggregate = {
                "condition_ids": list(CONDITIONS),
                "by_condition": {
                    condition: aggregate_metrics(internal_by_condition[condition])
                    for condition in CONDITIONS
                },
            }
            resolved_dataset = (
                dataset_path if dataset_path.is_absolute() else self.root / dataset_path
            )
            corpus_runs.append(
                {
                    "corpus_id": corpus_id,
                    "version": str(corpus["version"]),
                    "path": resolved_dataset.relative_to(self.root).as_posix()
                    if resolved_dataset.is_relative_to(self.root)
                    else resolved_dataset.as_posix(),
                    "dataset_sha256": hashlib.sha256(resolved_dataset.read_bytes()).hexdigest(),
                    "query_count": len(records),
                    "query_ids": sorted(str(item["id"]) for item in records),
                    "conditions": list(CONDITIONS),
                    "aggregate": aggregate,
                    "result_ids": sorted(
                        result_id
                        for condition_ids in ids_by_condition.values()
                        for result_id in condition_ids
                    ),
                }
            )
        per_query.sort(
            key=lambda record: (record["corpus_id"], record["condition"], record["query_id"])
        )
        result = {
            "schema_version": "1.0.0",
            "artifact_id": "cifre-aqr-benchmark-results",
            "generated_by": "semantic_layer.research.benchmark_runner",
            "canonicalization": {
                "encoding": "UTF-8",
                "key_order": "lexicographic",
                "metric_precision": 6,
            },
            "hash_manifest": build_hash_manifest(self.root).to_dict(),
            "environment": _environment(self.root),
            "namespace_registry": {
                **NAMESPACE_REGISTRY,
                "legacy_uris_rejected": list(_LEGACY_URIS),
            },
            "validation": build_validation_metadata(self.root),
            "corpus_runs": corpus_runs,
            "per_query": per_query,
        }
        validate_result_id_references(result)
        return result

    def run(self) -> dict[str, Any]:
        """Evaluate and write the caller-selected temporary result artifact."""

        result = self._build_result()
        write_result_artifact(result, self.result_path)
        return result


__all__ = [
    "BenchmarkRunner",
    "ConditionAggregate",
    "HashManifest",
    "QueryMetrics",
    "QueryRecord",
    "aggregate_metrics",
    "build_hash_manifest",
    "build_validation_metadata",
    "score_query",
    "validate_hash_manifest",
    "validate_result_id_references",
    "write_result_artifact",
]
