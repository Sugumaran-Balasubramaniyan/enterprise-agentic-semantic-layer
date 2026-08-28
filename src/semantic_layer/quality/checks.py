"""Deterministic, source-bound quality gates for complete curated data products."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from semantic_layer.control import digest, file_digest, registry_digest
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
_REPORT_ISSUER = object()


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
        "_issuer",
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

    @classmethod
    def _issue(
        cls,
        *,
        status: str,
        score: int,
        issues: list[QualityIssue],
        expected_datasets: tuple[str, ...],
        source_digests: dict[str, str],
        mapping_evidence: dict[str, str],
        registry_fingerprint: str,
    ) -> QualityReport:
        report = object.__new__(cls)
        object.__setattr__(report, "status", status)
        object.__setattr__(report, "score", score)
        object.__setattr__(report, "issues", tuple(issues))
        object.__setattr__(report, "expected_datasets", expected_datasets)
        object.__setattr__(report, "source_digests", dict(sorted(source_digests.items())))
        object.__setattr__(report, "mapping_evidence", dict(sorted(mapping_evidence.items())))
        object.__setattr__(report, "registry_digest", registry_fingerprint)
        object.__setattr__(
            report,
            "digest",
            digest(
                {
                    "status": status,
                    "issues": issues,
                    "expected_datasets": expected_datasets,
                    "source_digests": source_digests,
                    "mapping_evidence": mapping_evidence,
                    "registry": registry_fingerprint,
                }
            ),
        )
        object.__setattr__(report, "_issuer", _REPORT_ISSUER)
        return report

    def _matches(self, path: Path, registry: SemanticRegistry) -> bool:
        if self._issuer is not _REPORT_ISSUER or self.status != "PASS":
            return False
        if self.registry_digest != registry_digest(registry):
            return False
        if set(self.expected_datasets) != set(_ID_COLUMNS) or not self.expected_datasets:
            return False
        return all(
            (path / name).is_file() and file_digest(path / name) == expected_digest
            for name, expected_digest in self.source_digests.items()
        )


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
    issues: list[QualityIssue] = []
    source_digests: dict[str, str] = {}
    mapping_evidence: dict[str, str] = {}
    expected_datasets = tuple(sorted(_ID_COLUMNS))
    for file_name in expected_datasets:
        csv_path = path / file_name
        if not csv_path.is_file():
            _issue(issues, "MISSING_EXPECTED_DATASET", file_name, 0, "path", "required curated CSV is missing")
            continue
        source_digests[file_name] = file_digest(csv_path)
        id_column = _ID_COLUMNS[file_name]
        seen_ids: set[str] = set()
        row_count = 0
        with csv_path.open(newline="", encoding="utf-8") as stream:
            for row_number, row in enumerate(csv.DictReader(stream), start=2):
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
    return QualityReport._issue(
        status="PASS" if not issues else "FAIL",
        score=score,
        issues=issues,
        expected_datasets=expected_datasets,
        source_digests=source_digests,
        mapping_evidence=mapping_evidence,
        registry_fingerprint=registry_digest(registry),
    )
