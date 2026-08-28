"""Behavioural tests for curated-data quality controls."""

from pathlib import Path

from semantic_layer.quality import validate_curated_data

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_curated_demo_data_passes_all_governed_quality_checks() -> None:
    """Breaking an accepted governed value must make the curated quality gate fail."""

    report = validate_curated_data(REPOSITORY_ROOT / "data" / "curated")

    assert report.status == "PASS"
    assert report.score == 100
    assert report.issues == []


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
        "INVALID_PRODUCT_MAPPING",
        "INVALID_STATUS",
        "FUTURE_DATE",
        "NEGATIVE_LOSS",
    }
