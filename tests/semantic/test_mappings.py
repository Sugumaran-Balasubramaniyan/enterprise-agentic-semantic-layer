"""Semantic contracts for federated local-to-group mappings."""

from pathlib import Path

import pytest
import yaml

from semantic_layer.data_generation import canonical_product

MAPPING_ROOT = Path("mappings")
PRODUCT_ROOT = Path("data_products")

MAPPING_FILES = (
    MAPPING_ROOT / "databricks" / "france.yaml",
    MAPPING_ROOT / "snowflake" / "united_kingdom.yaml",
    MAPPING_ROOT / "fabric" / "germany.yaml",
)
PRODUCT_FILES = tuple(sorted(PRODUCT_ROOT.glob("*.yaml")))


def test_all_local_motor_codes_normalize_to_group_motor_insurance() -> None:
    assert canonical_product("databricks", "MTR") == "insurance:MotorInsurance"
    assert canonical_product("snowflake", "CAR") == "insurance:MotorInsurance"
    assert canonical_product("fabric", "MotorInsurance") == "insurance:MotorInsurance"


def test_mapping_assets_declare_platform_location_and_field_mappings() -> None:
    expected = {
        "databricks/france.yaml": ("Databricks", "FR"),
        "snowflake/united_kingdom.yaml": ("Snowflake", "GB"),
        "fabric/germany.yaml": ("Microsoft Fabric", "DE"),
    }
    for relative_path, (platform, country) in expected.items():
        document = yaml.safe_load((MAPPING_ROOT / relative_path).read_text())
        assert document["platform"] == platform
        assert document["location"] == country
        assert document["version"] == "1.0.0"
        assert document["fields"]
        assert document["normalization"]["products"]
        assert document["normalization"]["statuses"]


def test_unknown_local_product_is_rejected() -> None:
    try:
        canonical_product("databricks", "UNKNOWN")
    except ValueError as error:
        assert "UNKNOWN" in str(error)
    else:  # pragma: no cover - assertion keeps the behavior explicit
        raise AssertionError("unknown local product must fail closed")


def test_unregistered_home_extension_is_not_a_governed_product() -> None:
    with pytest.raises(ValueError, match="HomeInsurance|unregistered"):
        canonical_product("databricks", "HOME")


@pytest.mark.parametrize("mapping_path", MAPPING_FILES)
@pytest.mark.parametrize("product_path", PRODUCT_FILES)
def test_each_platform_maps_every_certified_product_schema_field(
    mapping_path: Path, product_path: Path
) -> None:
    schema = yaml.safe_load(product_path.read_text())["schema"]
    mapping = yaml.safe_load(mapping_path.read_text())
    for field in schema:
        field_mapping = mapping["fields"].get(field["name"])
        assert field_mapping and field_mapping["physical_name"], (
            mapping_path,
            product_path,
            field["name"],
        )


@pytest.mark.parametrize(
    ("mapping_path", "expected"),
    [
        (
            MAPPING_ROOT / "databricks" / "france.yaml",
            {"EN_COURS": "ACTIVE", "ECHUE": "LAPSED", "ANNULEE": "CANCELLED"},
        ),
        (
            MAPPING_ROOT / "snowflake" / "united_kingdom.yaml",
            {"IN_FORCE": "ACTIVE", "LAPSED": "LAPSED", "CANCELLED": "CANCELLED"},
        ),
        (
            MAPPING_ROOT / "fabric" / "germany.yaml",
            {"AKTIV": "ACTIVE", "ABGELAUFEN": "LAPSED", "STORNIERT": "CANCELLED"},
        ),
    ],
)
def test_policy_statuses_normalize_to_active_policy_values(
    mapping_path: Path, expected: dict[str, str]
) -> None:
    mapping = yaml.safe_load(mapping_path.read_text())
    assert mapping["fields"]["policy_status"]["concept"] == "insurance:Policy"
    statuses = mapping["normalization"].get("policy_statuses", {})
    assert statuses.items() >= expected.items()


def test_claims_ratio_preaggregates_each_product_before_aligned_ratio() -> None:
    metric = yaml.safe_load(Path("semantic/metrics/metrics.yaml").read_text())["metrics"][-1]
    assert metric["id"] == "insurance:ClaimsRatio"
    assert metric["aggregation"] == "ratio_of_aggregates"
    assert metric["alignment"]["pre_aggregate_each_product"] is True
    assert metric["alignment"]["join_multiplication"] == "forbidden"
    assert metric["alignment"]["dimensions"] == ["customer_id", "country", "product"]
    assert metric["numerator"]["product"] == "ClaimsAnalytics"
    assert metric["denominator"]["product"] == "PremiumAnalytics"
    assert metric["numerator"]["filter_rule"] == "insurance:QualifyingClaim"
    assert "SUM(incurred_loss_eur) /" not in metric["expression"]
