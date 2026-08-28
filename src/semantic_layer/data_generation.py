"""Deterministic demo data and local product normalization.

The generated records are intentionally small enough to inspect in an
interview while still exercising the semantic rules: multiple policies,
qualifying and excluded claims, three jurisdictions, and raw quality failures.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping
from datetime import date, timedelta
from pathlib import Path

import yaml

_CANONICAL_MOTOR = "insurance:MotorInsurance"
_PLATFORM_DIRECTORIES = {
    "databricks": "databricks/france.yaml",
    "snowflake": "snowflake/united_kingdom.yaml",
    "fabric": "fabric/germany.yaml",
    "microsoft fabric": "fabric/germany.yaml",
}


def canonical_product(platform: str, value: str) -> str:
    """Normalize a local product code to a governed insurance concept.

    Unknown platforms and values fail closed rather than silently passing an
    unmapped local code into a semantic query.
    """

    platform_key = platform.strip().casefold()
    value_key = value.strip().casefold()
    relative_path = _PLATFORM_DIRECTORIES.get(platform_key)
    if relative_path is None:
        raise ValueError(f"unsupported mapping platform: {platform}")

    mapping_path = Path(__file__).resolve().parents[2] / "mappings" / relative_path
    try:
        document = yaml.safe_load(mapping_path.read_text())
    except FileNotFoundError as error:
        raise ValueError(f"mapping asset not found for platform: {platform}") from error

    products = document.get("normalization", {}).get("products", {})
    for local_value, canonical_value in products.items():
        if str(local_value).strip().casefold() == value_key:
            return str(canonical_value)
    raise ValueError(f"unmapped product {value!r} for platform {platform!r}")


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _records(as_of: date) -> dict[str, list[dict[str, object]]]:
    """Return stable records anchored to ``as_of`` rather than wall-clock time."""

    d = lambda days: (as_of - timedelta(days=days)).isoformat()
    future = (as_of + timedelta(days=1)).isoformat()

    customers = [
        {"customer_id": "FR_001", "customer_name": "Camille Martin", "country": "FR", "email": "camille.martin@example.test"},
        {"customer_id": "FR_002", "customer_name": "Julien Bernard", "country": "FR", "email": "julien.bernard@example.test"},
        {"customer_id": "FR_003", "customer_name": "Aline Petit", "country": "FR", "email": "aline.petit@example.test"},
        {"customer_id": "UK_001", "customer_name": "Oliver Smith", "country": "GB", "email": "oliver.smith@example.test"},
        {"customer_id": "DE_001", "customer_name": "Anna Schmidt", "country": "DE", "email": "anna.schmidt@example.test"},
    ]
    policies = [
        {"policy_id": "FR_POL_001", "customer_id": "FR_001", "country": "FR", "product": _CANONICAL_MOTOR, "policy_status": "ACTIVE", "effective_date": d(720), "expiry_date": d(-10), "annual_premium_eur": "1350.00"},
        {"policy_id": "FR_POL_002", "customer_id": "FR_001", "country": "FR", "product": _CANONICAL_MOTOR, "policy_status": "LAPSED", "effective_date": d(900), "expiry_date": d(400), "annual_premium_eur": "850.00"},
        {"policy_id": "FR_POL_003", "customer_id": "FR_002", "country": "FR", "product": _CANONICAL_MOTOR, "policy_status": "ACTIVE", "effective_date": d(500), "expiry_date": d(-40), "annual_premium_eur": "1490.00"},
        {"policy_id": "FR_POL_004", "customer_id": "FR_003", "country": "FR", "product": "insurance:HomeInsurance", "policy_status": "ACTIVE", "effective_date": d(300), "expiry_date": d(-100), "annual_premium_eur": "620.00"},
        {"policy_id": "UK_POL_001", "customer_id": "UK_001", "country": "GB", "product": _CANONICAL_MOTOR, "policy_status": "ACTIVE", "effective_date": d(650), "expiry_date": d(-20), "annual_premium_eur": "1120.00"},
        {"policy_id": "DE_POL_001", "customer_id": "DE_001", "country": "DE", "product": _CANONICAL_MOTOR, "policy_status": "ACTIVE", "effective_date": d(600), "expiry_date": d(-30), "annual_premium_eur": "980.00"},
    ]
    claims = [
        {"claim_id": "FR_CLM_001", "policy_id": "FR_POL_001", "customer_id": "FR_001", "country": "FR", "product": _CANONICAL_MOTOR, "status": "OPEN", "claim_date": d(30), "incurred_loss_eur": "9000.00"},
        {"claim_id": "FR_CLM_002", "policy_id": "FR_POL_001", "customer_id": "FR_001", "country": "FR", "product": _CANONICAL_MOTOR, "status": "SETTLED", "claim_date": d(120), "incurred_loss_eur": "8000.00"},
        {"claim_id": "FR_CLM_003", "policy_id": "FR_POL_001", "customer_id": "FR_001", "country": "FR", "product": _CANONICAL_MOTOR, "status": "PENDING", "claim_date": d(200), "incurred_loss_eur": "7000.00"},
        {"claim_id": "FR_CLM_004", "policy_id": "FR_POL_001", "customer_id": "FR_001", "country": "FR", "product": _CANONICAL_MOTOR, "status": "CANCELLED", "claim_date": d(45), "incurred_loss_eur": "50000.00"},
        {"claim_id": "FR_CLM_005", "policy_id": "FR_POL_001", "customer_id": "FR_001", "country": "FR", "product": _CANONICAL_MOTOR, "status": "DUPLICATE", "claim_date": d(46), "incurred_loss_eur": "50000.00"},
        {"claim_id": "FR_CLM_006", "policy_id": "FR_POL_001", "customer_id": "FR_001", "country": "FR", "product": _CANONICAL_MOTOR, "status": "SETTLED", "claim_date": d(400), "incurred_loss_eur": "12000.00"},
        {"claim_id": "FR_CLM_007", "policy_id": "FR_POL_003", "customer_id": "FR_002", "country": "FR", "product": _CANONICAL_MOTOR, "status": "OPEN", "claim_date": d(60), "incurred_loss_eur": "12000.00"},
        {"claim_id": "FR_CLM_008", "policy_id": "FR_POL_003", "customer_id": "FR_002", "country": "FR", "product": _CANONICAL_MOTOR, "status": "PENDING", "claim_date": d(160), "incurred_loss_eur": "11000.00"},
        {"claim_id": "FR_CLM_009", "policy_id": "FR_POL_003", "customer_id": "FR_002", "country": "FR", "product": _CANONICAL_MOTOR, "status": "SETTLED", "claim_date": d(240), "incurred_loss_eur": "2000.00"},
        {"claim_id": "FR_CLM_010", "policy_id": "FR_POL_004", "customer_id": "FR_003", "country": "FR", "product": "insurance:HomeInsurance", "status": "OPEN", "claim_date": d(90), "incurred_loss_eur": "2500.00"},
        {"claim_id": "UK_CLM_001", "policy_id": "UK_POL_001", "customer_id": "UK_001", "country": "GB", "product": _CANONICAL_MOTOR, "status": "OPEN", "claim_date": d(75), "incurred_loss_eur": "4200.00"},
        {"claim_id": "DE_CLM_001", "policy_id": "DE_POL_001", "customer_id": "DE_001", "country": "DE", "product": _CANONICAL_MOTOR, "status": "SETTLED", "claim_date": d(180), "incurred_loss_eur": "7600.00"},
        {"claim_id": "DE_CLM_002", "policy_id": "DE_POL_001", "customer_id": "DE_001", "country": "DE", "product": _CANONICAL_MOTOR, "status": "CANCELLED", "claim_date": d(190), "incurred_loss_eur": "1800.00"},
    ]
    premiums = [
        {"premium_id": "FR_PREM_001", "policy_id": "FR_POL_001", "customer_id": "FR_001", "country": "FR", "product": _CANONICAL_MOTOR, "premium_date": d(20), "premium_eur": "1350.00"},
        {"premium_id": "FR_PREM_002", "policy_id": "FR_POL_003", "customer_id": "FR_002", "country": "FR", "product": _CANONICAL_MOTOR, "premium_date": d(20), "premium_eur": "1490.00"},
        {"premium_id": "FR_PREM_003", "policy_id": "FR_POL_004", "customer_id": "FR_003", "country": "FR", "product": "insurance:HomeInsurance", "premium_date": d(20), "premium_eur": "620.00"},
        {"premium_id": "UK_PREM_001", "policy_id": "UK_POL_001", "customer_id": "UK_001", "country": "GB", "product": _CANONICAL_MOTOR, "premium_date": d(20), "premium_eur": "1120.00"},
        {"premium_id": "DE_PREM_001", "policy_id": "DE_POL_001", "customer_id": "DE_001", "country": "DE", "product": _CANONICAL_MOTOR, "premium_date": d(20), "premium_eur": "980.00"},
    ]
    raw_customers = [*customers, {"customer_id": "", "customer_name": "Invalid Customer", "country": "FR", "email": "invalid@example.test"}]
    raw_policies = [*policies, {**policies[0], "policy_id": "RAW_NEGATIVE", "annual_premium_eur": "-1.00"}]
    raw_claims = [
        *claims,
        {**claims[0], "claim_id": "RAW_FUTURE", "claim_date": future},
        {**claims[0], "claim_id": "RAW_NEGATIVE", "incurred_loss_eur": "-10.00"},
        {**claims[0], "claim_id": "RAW_STATUS", "status": "UNKNOWN"},
        {**claims[0], "claim_id": "FR_CLM_001", "claim_date": d(31)},
    ]
    raw_premiums = [*premiums, {**premiums[0], "premium_id": "RAW_NEGATIVE", "premium_eur": "-25.00"}]
    return {
        "customers": customers,
        "policies": policies,
        "claims": claims,
        "premiums": premiums,
        "raw_customers": raw_customers,
        "raw_policies": raw_policies,
        "raw_claims": raw_claims,
        "raw_premiums": raw_premiums,
    }


def generate_demo_data(output_dir: Path, as_of: date) -> None:
    """Write deterministic curated and intentionally imperfect raw CSVs."""

    records = _records(as_of)
    columns = {
        "customers": ["customer_id", "customer_name", "country", "email"],
        "policies": ["policy_id", "customer_id", "country", "product", "policy_status", "effective_date", "expiry_date", "annual_premium_eur"],
        "claims": ["claim_id", "policy_id", "customer_id", "country", "product", "status", "claim_date", "incurred_loss_eur"],
        "premiums": ["premium_id", "policy_id", "customer_id", "country", "product", "premium_date", "premium_eur"],
    }
    destination = Path(output_dir)
    for name, fieldnames in columns.items():
        _write_csv(destination / "curated" / f"{name}.csv", fieldnames, records[name])
        _write_csv(destination / "raw" / f"{name}.csv", fieldnames, records[f"raw_{name}"])


__all__ = ["canonical_product", "generate_demo_data"]
