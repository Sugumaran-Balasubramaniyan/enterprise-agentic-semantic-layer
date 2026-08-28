"""Fail-closed placeholders for unconfigured cloud execution platforms."""

from __future__ import annotations


class CloudAdapterConfigurationError(RuntimeError):
    """Raised instead of silently executing a cloud query without configuration."""


class _DocumentedCloudAdapter:
    platform = "cloud"

    def execute(self, _query: object) -> None:
        raise CloudAdapterConfigurationError(
            f"{self.platform} credentials and configuration are required; cloud execution is disabled"
        )


class DatabricksAdapter(_DocumentedCloudAdapter):
    platform = "Databricks"


class SnowflakeAdapter(_DocumentedCloudAdapter):
    platform = "Snowflake"


class MicrosoftFabricAdapter(_DocumentedCloudAdapter):
    platform = "Microsoft Fabric"
