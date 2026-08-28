"""Deterministic quality gates for local curated data products."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

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


@dataclass(frozen=True)
class QualityIssue:
    """One failed governed quality predicate."""

    code: str
    file: str
    row_number: int
    field: str
    message: str


@dataclass(frozen=True)
class QualityReport:
    """Aggregated local product quality outcome suitable for provenance."""

    status: str
    score: int
    issues: list[QualityIssue]


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


def _valid_products(registry: SemanticRegistry) -> set[str]:
    return {
        canonical
        for mapping in registry.mappings.values()
        for canonical in mapping.normalization.get("products", {}).values()
    }


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


def validate_curated_data(path: Path, registry: SemanticRegistry | None = None) -> QualityReport:
    """Validate immutable curated CSV records against governed semantic values.

    Git-versioned registry mappings remain the authority for valid canonical
    products.  A failed report is designed to block detailed execution.
    """

    registry = registry or SemanticRegistry.from_repository(_repository_root())
    issues: list[QualityIssue] = []
    valid_products = _valid_products(registry)
    files = sorted(candidate for candidate in path.glob("*.csv") if candidate.name in _ID_COLUMNS)
    if not files:
        _issue(issues, "MISSING_CURATED_DATA", path.name, 0, "path", "no governed CSV was found")
    for csv_path in files:
        file_name = csv_path.name
        id_column = _ID_COLUMNS[file_name]
        seen_ids: set[str] = set()
        with csv_path.open(newline="", encoding="utf-8") as stream:
            for row_number, row in enumerate(csv.DictReader(stream), start=2):
                identifier = (row.get(id_column) or "").strip()
                if not identifier:
                    _issue(issues, "MISSING_ID", file_name, row_number, id_column, "identifier is required")
                elif identifier in seen_ids:
                    _issue(issues, "DUPLICATE_ID", file_name, row_number, id_column, "identifier is duplicate")
                else:
                    seen_ids.add(identifier)
                country = row.get("country")
                if country not in _COUNTRIES:
                    _issue(issues, "INVALID_COUNTRY", file_name, row_number, "country", "unknown country")
                product = row.get("product")
                if product is not None and product not in valid_products:
                    _issue(
                        issues,
                        "INVALID_PRODUCT_MAPPING",
                        file_name,
                        row_number,
                        "product",
                        "product is not mapped to a governed canonical value",
                    )
                if file_name == "claims.csv":
                    if row.get("status") not in _CLAIM_STATUSES:
                        _issue(issues, "INVALID_STATUS", file_name, row_number, "status", "unknown claim status")
                    _date_is_valid(row.get("claim_date", ""), file_name, row_number, "claim_date", issues)
                    try:
                        loss = float(row.get("incurred_loss_eur", ""))
                    except ValueError:
                        _issue(issues, "INVALID_LOSS", file_name, row_number, "incurred_loss_eur", "loss is not numeric")
                    else:
                        if loss < 0:
                            _issue(issues, "NEGATIVE_LOSS", file_name, row_number, "incurred_loss_eur", "loss is negative")
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
                elif file_name == "premiums.csv":
                    _date_is_valid(row.get("premium_date", ""), file_name, row_number, "premium_date", issues)
    score = max(0, 100 - len(issues))
    return QualityReport(status="PASS" if not issues else "FAIL", score=score, issues=issues)
