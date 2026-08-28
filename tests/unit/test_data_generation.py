"""Deterministic demo-data generation contracts."""

import csv
from datetime import date
from pathlib import Path

from semantic_layer.data_generation import generate_demo_data


def test_generated_data_contains_primary_use_case_candidates(tmp_path: Path) -> None:
    generate_demo_data(tmp_path, date(2026, 8, 28))

    claims_path = tmp_path / "curated" / "claims.csv"
    assert claims_path.exists()
    claims = list(csv.DictReader(claims_path.open(newline="")))

    cutoff = date(2025, 8, 29)
    qualifying = [
        claim
        for claim in claims
        if claim["country"] == "FR"
        and claim["product"] == "insurance:MotorInsurance"
        and claim["status"] not in {"CANCELLED", "DUPLICATE"}
        and cutoff <= date.fromisoformat(claim["claim_date"]) <= date(2026, 8, 28)
    ]
    by_customer: dict[str, list[dict[str, str]]] = {}
    for claim in qualifying:
        by_customer.setdefault(claim["customer_id"], []).append(claim)

    candidates = {
        customer_id
        for customer_id, customer_claims in by_customer.items()
        if len(customer_claims) >= 3
        and sum(float(claim["incurred_loss_eur"]) for claim in customer_claims) > 20_000
    }
    assert {"FR_001", "FR_002"} <= candidates


def test_generation_is_reproducible_and_writes_curated_and_raw_data(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    as_of = date(2026, 8, 28)
    generate_demo_data(first, as_of)
    generate_demo_data(second, as_of)

    relative_files = {
        path.relative_to(first)
        for path in first.rglob("*.csv")
    }
    assert relative_files == {
        Path("curated/customers.csv"),
        Path("curated/policies.csv"),
        Path("curated/claims.csv"),
        Path("curated/premiums.csv"),
        Path("raw/customers.csv"),
        Path("raw/policies.csv"),
        Path("raw/claims.csv"),
        Path("raw/premiums.csv"),
    }
    for relative_path in relative_files:
        assert (first / relative_path).read_bytes() == (second / relative_path).read_bytes()


def test_curated_data_contains_multiple_countries_and_exclusion_statuses(tmp_path: Path) -> None:
    generate_demo_data(tmp_path, date(2026, 8, 28))
    claims = list(csv.DictReader((tmp_path / "curated" / "claims.csv").open(newline="")))
    assert {claim["country"] for claim in claims} == {"FR", "GB", "DE"}
    assert {claim["status"] for claim in claims} >= {"CANCELLED", "DUPLICATE"}


def test_raw_claims_include_quality_failure_fixtures(tmp_path: Path) -> None:
    generate_demo_data(tmp_path, date(2026, 8, 28))
    claims = list(csv.DictReader((tmp_path / "raw" / "claims.csv").open(newline="")))
    assert any(float(claim["incurred_loss_eur"]) < 0 for claim in claims)
    assert any(claim["status"] == "UNKNOWN" for claim in claims)
    ids = [claim["claim_id"] for claim in claims]
    assert len(ids) != len(set(ids))
