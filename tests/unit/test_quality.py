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
    """Removing any claim control must allow an unsafe detail product through."""

    (tmp_path / "claims.csv").write_text(
        "claim_id,policy_id,customer_id,country,product,status,claim_date,incurred_loss_eur\n"
        "C_1,P_1,FR_001,FR,insurance:MotorInsurance,OPEN,2026-08-01,5.00\n"
        "C_1,P_1,FR_001,ZZ,UNKNOWN,BAD_STATUS,2026-09-01,-1.00\n",
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

    for name in ("customers.csv", "policies.csv", "premiums.csv"):
        source = REPOSITORY_ROOT / "data" / "curated" / name
        (tmp_path / name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "claims.csv").write_text(
        "claim_id,policy_id,customer_id,country,product,status,claim_date,incurred_loss_eur\n"
        "C_TRAVEL,P_TRAVEL,FR_001,FR,insurance:TravelInsurance,OPEN,2026-08-01,1.00\n",
        encoding="utf-8",
    )

    report = validate_curated_data(tmp_path)

    assert report.status == "FAIL"
    assert "INVALID_PRODUCT_MAPPING" in {issue.code for issue in report.issues}


@pytest.mark.parametrize(
    ("file_name", "field"),
    [
        ("customers.csv", "customer_id"),
        ("policies.csv", "policy_id"),
        ("policies.csv", "customer_id"),
        ("claims.csv", "claim_id"),
        ("claims.csv", "policy_id"),
        ("claims.csv", "customer_id"),
        ("premiums.csv", "premium_id"),
        ("premiums.csv", "policy_id"),
        ("premiums.csv", "customer_id"),
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
