"""Deterministic demo-data generation contracts."""

import csv
from datetime import date
from pathlib import Path

from semantic_layer.data_generation import generate_demo_data


def test_generated_data_contains_primary_use_case_candidates(tmp_path: Path) -> None:
    generate_demo_data(tmp_path, date(2026, 8, 28))

    acdoca_path = tmp_path / "curated" / "acdoca_financials.csv"
    assert acdoca_path.exists()
    postings = list(csv.DictReader(acdoca_path.open(newline="")))

    cutoff = date(2025, 8, 29)
    qualifying = [
        posting
        for posting in postings
        if posting["country"] == "FR"
        and posting["product"] == "ciferp:ProductAutomotive"
        and posting["posting_status"] not in {"REVERSED", "DUPLICATE"}
        and cutoff <= date.fromisoformat(posting["posting_date"]) <= date(2026, 8, 28)
    ]
    by_partner: dict[str, list[dict[str, str]]] = {}
    for posting in qualifying:
        by_partner.setdefault(posting["partner_id"], []).append(posting)

    candidates = {
        partner_id
        for partner_id, partner_postings in by_partner.items()
        if len(partner_postings) >= 3
        and sum(float(posting["amount_in_company_currency_eur"]) for posting in partner_postings) > 20_000
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
        Path("curated/business_partners.csv"),
        Path("curated/sales_orders.csv"),
        Path("curated/acdoca_financials.csv"),
        Path("curated/billing_documents.csv"),
        Path("raw/business_partners.csv"),
        Path("raw/sales_orders.csv"),
        Path("raw/acdoca_financials.csv"),
        Path("raw/billing_documents.csv"),
    }
    for relative_path in relative_files:
        assert (first / relative_path).read_bytes() == (second / relative_path).read_bytes()


def test_curated_data_contains_multiple_countries_and_exclusion_statuses(tmp_path: Path) -> None:
    generate_demo_data(tmp_path, date(2026, 8, 28))
    postings = list(csv.DictReader((tmp_path / "curated" / "acdoca_financials.csv").open(newline="")))
    assert {posting["country"] for posting in postings} == {"FR", "GB", "DE"}
    assert {posting["posting_status"] for posting in postings} >= {"REVERSED", "DUPLICATE"}


def test_raw_claims_include_quality_failure_fixtures(tmp_path: Path) -> None:
    generate_demo_data(tmp_path, date(2026, 8, 28))
    postings = list(csv.DictReader((tmp_path / "raw" / "acdoca_financials.csv").open(newline="")))
    assert any(float(posting["amount_in_company_currency_eur"]) < 0 for posting in postings)
    assert any(posting["posting_status"] == "UNKNOWN" for posting in postings)
    ids = [posting["journal_entry_id"] for posting in postings]
    assert len(ids) != len(set(ids))
