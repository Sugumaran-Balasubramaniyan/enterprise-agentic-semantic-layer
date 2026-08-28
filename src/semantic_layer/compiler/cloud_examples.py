"""Unexecuted, documentation-only cloud SQL representations.

Cloud SQL remains an extension seam.  It is never submitted from this local
reference implementation and must be reviewed against each platform's native
security controls before use.
"""

from __future__ import annotations

from semantic_layer.compiler.base import CompiledQuery


def documented_cloud_sql(query: CompiledQuery, platform: str) -> str:
    """Return an explicitly incomplete dialect fragment; this never claims parity."""

    if platform not in {"Databricks", "Snowflake", "Microsoft Fabric"}:
        raise ValueError("unsupported documented cloud platform")
    return (
        f"-- UNEXECUTED {platform} INCOMPLETE SQL FRAGMENT: not equivalent to the "
        "governed plan; review mapping, dialect, parameters, and native security before use\n"
        f"{query.sql}"
    )
