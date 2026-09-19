"""Behavioural tests for curated-data quality controls."""

import csv
from pathlib import Path

import pytest
from pydantic import ValidationError

from semantic_layer.models import ProductQuality
from semantic_layer.quality import validate_curated_data

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_product_quality_status_is_a_governed_typed_contract() -> None:
    with pytest.raises(ValidationError):
        ProductQuality(status="UNKNOWN", checks=[])
    quality = ProductQuality(status="CERTIFIED", checks=[])
    with pytest.raises(ValidationError):
        quality.status = "UNKNOWN"


def test_curated_demo_data_passes_all_governed_quality_checks() -> None:
    """Breaking an accepted governed value must make the curated quality gate fail."""

    report = validate_curated_data(REPOSITORY_ROOT / "data" / "curated")

    assert report.status == "PASS"
    assert report.score == 100
    assert report.issues == ()


def test_claim_quality_rejects_duplicate_ids_invalid_values_and_future_dates(tmp_path: Path) -> None:
    """Removing any detail posting control must allow an unsafe detail product through."""

    (tmp_path / "acdoca_financials.csv").write_text(
        "journal_entry_id,sales_order_id,partner_id,country,product,posting_status,posting_date,amount_in_company_currency_eur\n"
        "DOC_1,SO_1,FR_001,FR,sap:ProductAutomotive,POSTED,2026-08-01,5.00\n"
        "DOC_1,SO_1,FR_001,ZZ,UNKNOWN,BAD_STATUS,2026-10-01,-1.00\n",
        encoding="utf-8",
    )

    report = validate_curated_data(tmp_path)

    assert report.status == "FAIL"
    assert report.score < 100
    assert {issue.code for issue in report.issues} >= {
        "DUPLICATE_ID",
        "INVALID_COUNTRY",
        "MISSING_EXPECTED_DATASET",
        "INVALID_PRODUCT_MAPPING",
        "INVALID_STATUS",
        "FUTURE_DATE",
        "NEGATIVE_LOSS",
    }


def test_quality_rejects_rows_using_an_unregistered_product_extension(tmp_path: Path) -> None:
    """A mapping target absent from the vocabulary cannot receive a PASS quality report."""

    for name in ("business_partners.csv", "sales_orders.csv", "billing_documents.csv"):
        source = REPOSITORY_ROOT / "data" / "curated" / name
        (tmp_path / name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "acdoca_financials.csv").write_text(
        "journal_entry_id,sales_order_id,partner_id,country,product,posting_status,posting_date,amount_in_company_currency_eur\n"
        "DOC_EXT,SO_EXT,FR_001,FR,sap:UnregisteredProduct,POSTED,2026-08-01,1.00\n",
        encoding="utf-8",
    )

    report = validate_curated_data(tmp_path)

    assert report.status == "FAIL"
    assert "INVALID_PRODUCT_MAPPING" in {issue.code for issue in report.issues}


@pytest.mark.parametrize(
    ("file_name", "field"),
    [
        ("business_partners.csv", "partner_id"),
        ("sales_orders.csv", "sales_order_id"),
        ("sales_orders.csv", "partner_id"),
        ("acdoca_financials.csv", "journal_entry_id"),
        ("acdoca_financials.csv", "sales_order_id"),
        ("acdoca_financials.csv", "partner_id"),
        ("billing_documents.csv", "billing_doc_id"),
        ("billing_documents.csv", "sales_order_id"),
        ("billing_documents.csv", "partner_id"),
    ],
)
@pytest.mark.parametrize("missing_value", ["", "null"])
def test_quality_rejects_blank_or_null_join_identifiers(
    tmp_path: Path, file_name: str, field: str, missing_value: str
) -> None:
    """Every identifier used to join governed products must be present, not only its primary key."""

    for source in (REPOSITORY_ROOT / "data" / "curated").glob("*.csv"):
        with source.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        fieldnames = list(rows[0])
        if source.name == file_name:
            rows[0][field] = missing_value
        with (tmp_path / source.name).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    report = validate_curated_data(tmp_path)

    assert report.status == "FAIL"
    assert any(issue.file == file_name and issue.field == field for issue in report.issues)
