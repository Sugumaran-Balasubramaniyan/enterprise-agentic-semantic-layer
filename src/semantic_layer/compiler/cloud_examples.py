"""Unexecuted, documentation-only cloud SQL representations.

Cloud SQL remains an extension seam.  It is never submitted from this local
reference implementation and must be reviewed against each platform's native
security controls before use.
"""

from __future__ import annotations

from semantic_layer.compiler.base import CompiledQuery


def documented_cloud_sql(query: CompiledQuery, platform: str) -> str:
    """Return a clearly marked dialect example; this function never executes it."""

    if platform not in {"Databricks", "Snowflake", "Microsoft Fabric"}:
        raise ValueError("unsupported documented cloud platform")
    return f"-- UNEXECUTED {platform} EXAMPLE: review native security before use\n{query.sql}"
