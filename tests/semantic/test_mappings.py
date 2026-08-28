"""Semantic contracts for federated local-to-group mappings."""

from pathlib import Path

import yaml

from semantic_layer.data_generation import canonical_product

MAPPING_ROOT = Path("mappings")


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
