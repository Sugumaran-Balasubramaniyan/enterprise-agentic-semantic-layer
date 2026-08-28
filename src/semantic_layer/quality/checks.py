"""Deterministic, source-bound quality gates for complete curated data products."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from types import MappingProxyType

from semantic_layer.control import (
    _sign,
    _verify,
    digest,
    file_digest,
    registry_digest,
)
from semantic_layer.registry import SemanticRegistry

AS_OF_DATE = date(2026, 8, 28)
_COUNTRIES = {"FR", "GB", "DE"}
_CLAIM_STATUSES = {"OPEN", "PENDING", "SETTLED", "CANCELLED", "DUPLICATE"}
_POLICY_STATUSES = {"ACTIVE", "LAPSED", "CANCELLED"}
_ID_COLUMNS = {
    "claims.csv": "claim_id",
    "customers.csv": "customer_id",
    "policies.csv": "policy_id",
    "premiums.csv": "premium_id",
}
_REQUIRED_FIELDS = {
    "claims.csv": {
        "claim_id", "policy_id", "customer_id", "country", "product", "status", "claim_date", "incurred_loss_eur"
    },
    "customers.csv": {"customer_id", "customer_name", "country", "email"},
    "policies.csv": {
        "policy_id", "customer_id", "country", "product", "policy_status", "effective_date", "expiry_date", "annual_premium_eur"
    },
    "premiums.csv": {"premium_id", "policy_id", "customer_id", "country", "product", "premium_date", "premium_eur"},
}


@dataclass(frozen=True)
class QualityIssue:
    """One failed governed quality predicate."""

    code: str
    file: str
    row_number: int
    field: str
    message: str


class QualityReport:
    """Opaque passing capability bound to exact expected source-file contents."""

    __slots__ = (
        "_signature",
        "_source_snapshots",
        "digest",
        "expected_datasets",
        "issues",
        "mapping_evidence",
        "registry_digest",
        "score",
        "source_digests",
        "status",
    )

    def __init__(self, *_: object, **__: object) -> None:
        raise TypeError("QualityReport instances are validator-issued only")

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("QualityReport capabilities are immutable")

    def _payload(self) -> dict[str, object]:
        return {
            "status": self.status,
            "score": self.score,
            "issues": self.issues,
            "expected_datasets": self.expected_datasets,
            "source_digests": self.source_digests,
            "mapping_evidence": self.mapping_evidence,
            "registry_digest": self.registry_digest,
            "source_snapshots": self._source_snapshots,
        }

    def _verify_integrity(self) -> bool:
        return self.digest == digest(self._payload()) and _verify(
            "QualityReport", self._payload(), self._signature
        )

    def _matches(self, path: Path, registry: SemanticRegistry) -> bool:
        if not self._verify_integrity() or self.status != "PASS":
            return False
        if self.registry_digest != registry_digest(registry):
            return False
        if set(self.expected_datasets) != set(_ID_COLUMNS) or not self.expected_datasets:
            return False
        if set(self.source_digests) != set(_ID_COLUMNS) or set(self._source_snapshots) != set(_ID_COLUMNS):
            return False
        return all(
            (path / name).is_file()
            and file_digest(path / name) == expected_digest
            and hashlib.sha256(self._source_bytes(name)).hexdigest() == expected_digest
            for name, expected_digest in self.source_digests.items()
        )

    def _source_bytes(self, name: str) -> bytes:
        """Return the exact bytes validated when this quality capability was issued."""

        if not self._verify_integrity() or name not in self._source_snapshots:
            raise ValueError("quality source snapshot integrity is invalid")
        try:
            content = base64.b64decode(self._source_snapshots[name], validate=True)
        except (ValueError, TypeError):
            raise ValueError("quality source snapshot encoding is invalid") from None
        if hashlib.sha256(content).hexdigest() != self.source_digests.get(name):
            raise ValueError("quality source snapshot digest is invalid")
        return content


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _issue(
    issues: list[QualityIssue],
    code: str,
    file_name: str,
    row_number: int,
    field: str,
    message: str,
) -> None:
    issues.append(QualityIssue(code, file_name, row_number, field, message))


def _date_is_valid(
    value: str, file_name: str, row_number: int, field: str, issues: list[QualityIssue]
) -> None:
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        _issue(issues, "INVALID_DATE", file_name, row_number, field, "date must be ISO-8601")
        return
    if parsed > AS_OF_DATE:
        _issue(issues, "FUTURE_DATE", file_name, row_number, field, "date is after demo as-of date")


def _nonnegative_finite(
    value: str, file_name: str, row_number: int, field: str, issues: list[QualityIssue]
) -> None:
    try:
        number = float(value)
    except ValueError:
        _issue(issues, "INVALID_NUMBER", file_name, row_number, field, "value is not numeric")
        return
    if not math.isfinite(number):
        _issue(issues, "NONFINITE_VALUE", file_name, row_number, field, "value must be finite")
    elif number < 0:
        _issue(issues, "NEGATIVE_LOSS", file_name, row_number, field, "value is negative")


def _country_mapping(registry: SemanticRegistry, country: str):
    matches = [mapping for mapping in registry.mappings.values() if mapping.location == country]
    return matches[0] if len(matches) == 1 else None


def validate_curated_data(path: Path, registry: SemanticRegistry | None = None) -> QualityReport:
    """Validate every expected curated dataset and bind its passing result to file digests."""

    registry = registry or SemanticRegistry.from_repository(_repository_root())
    if type(registry) is not SemanticRegistry:
        raise TypeError("quality validation requires the repository-issued semantic registry")
    issues: list[QualityIssue] = []
    source_digests: dict[str, str] = {}
    source_snapshots: dict[str, str] = {}
    mapping_evidence: dict[str, str] = {}
    expected_datasets = tuple(sorted(_ID_COLUMNS))
    for file_name in expected_datasets:
        csv_path = path / file_name
        if not csv_path.is_file():
            _issue(issues, "MISSING_EXPECTED_DATASET", file_name, 0, "path", "required curated CSV is missing")
            continue
        content = csv_path.read_bytes()
        source_digests[file_name] = hashlib.sha256(content).hexdigest()
        source_snapshots[file_name] = base64.b64encode(content).decode("ascii")
        id_column = _ID_COLUMNS[file_name]
        seen_ids: set[str] = set()
        row_count = 0
        with io.StringIO(content.decode("utf-8", errors="strict"), newline="") as stream:
            reader = csv.DictReader(stream)
            present_fields = set(reader.fieldnames or [])
            for missing_field in sorted(_REQUIRED_FIELDS[file_name] - present_fields):
                _issue(
                    issues,
                    "MISSING_SCHEMA_FIELD",
                    file_name,
                    1,
                    missing_field,
                    "required canonical CSV field is missing",
                )
            for row_number, row in enumerate(reader, start=2):
                row_count += 1
                identifier = (row.get(id_column) or "").strip()
                if not identifier:
                    _issue(issues, "MISSING_ID", file_name, row_number, id_column, "identifier is required")
                elif identifier in seen_ids:
                    _issue(issues, "DUPLICATE_ID", file_name, row_number, id_column, "identifier is duplicate")
                else:
                    seen_ids.add(identifier)
                country = row.get("country")
                mapping = _country_mapping(registry, country or "")
                if country not in _COUNTRIES or mapping is None:
                    _issue(issues, "INVALID_COUNTRY", file_name, row_number, "country", "unknown country")
                    if row.get("product") is not None:
                        _issue(
                            issues,
                            "INVALID_PRODUCT_MAPPING",
                            file_name,
                            row_number,
                            "product",
                            "product cannot be mapped without a valid row country",
                        )
                else:
                    mapping_evidence[f"{file_name}:{row_number}"] = f"{mapping.id}@{mapping.version}"
                    product = row.get("product")
                    if product is not None and product not in set(
                        mapping.normalization.get("products", {}).values()
                    ):
                        _issue(
                            issues,
                            "INVALID_PRODUCT_MAPPING",
                            file_name,
                            row_number,
                            "product",
                            "product is not mapped for the row country",
                        )
                if file_name == "claims.csv":
                    if row.get("status") not in _CLAIM_STATUSES:
                        _issue(issues, "INVALID_STATUS", file_name, row_number, "status", "unknown claim status")
                    _date_is_valid(row.get("claim_date", ""), file_name, row_number, "claim_date", issues)
                    _nonnegative_finite(
                        row.get("incurred_loss_eur", ""), file_name, row_number, "incurred_loss_eur", issues
                    )
                elif file_name == "policies.csv":
                    if row.get("policy_status") not in _POLICY_STATUSES:
                        _issue(
                            issues,
                            "INVALID_STATUS",
                            file_name,
                            row_number,
                            "policy_status",
                            "unknown policy status",
                        )
                    _date_is_valid(
                        row.get("effective_date", ""), file_name, row_number, "effective_date", issues
                    )
                    _nonnegative_finite(
                        row.get("annual_premium_eur", ""), file_name, row_number, "annual_premium_eur", issues
                    )
                elif file_name == "premiums.csv":
                    _date_is_valid(row.get("premium_date", ""), file_name, row_number, "premium_date", issues)
                    _nonnegative_finite(
                        row.get("premium_eur", ""), file_name, row_number, "premium_eur", issues
                    )
        if row_count == 0:
            _issue(issues, "EMPTY_EXPECTED_DATASET", file_name, 1, "path", "curated CSV has no rows")
    score = max(0, 100 - len(issues))
    report = object.__new__(QualityReport)
    payload = {
        "status": "PASS" if not issues else "FAIL",
        "score": score,
        "issues": tuple(issues),
        "expected_datasets": tuple(expected_datasets),
        "source_digests": MappingProxyType(dict(sorted(source_digests.items()))),
        "mapping_evidence": MappingProxyType(dict(sorted(mapping_evidence.items()))),
        "registry_digest": registry_digest(registry),
        "source_snapshots": MappingProxyType(dict(sorted(source_snapshots.items()))),
    }
    for name, value in payload.items():
        object.__setattr__(report, "_source_snapshots" if name == "source_snapshots" else name, value)
    object.__setattr__(report, "digest", digest(report._payload()))
    object.__setattr__(report, "_signature", _sign("QualityReport", report._payload()))
    return report
