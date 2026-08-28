"""Local, read-only DuckDB execution of compiler-produced queries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from semantic_layer.compiler.base import CompiledQuery

_VIEWS = {"customers": "customers.csv", "policies": "policies.csv", "claims": "claims.csv"}


class LocalDuckDBAdapter:
    """Register only curated local CSV files and execute a trusted compiled query."""

    def __init__(self, curated_data_path: Path) -> None:
        self.curated_data_path = curated_data_path.resolve()
        if not self.curated_data_path.is_dir():
            raise ValueError("curated data path must be an existing directory")

    @staticmethod
    def _sql_literal(path: Path) -> str:
        return str(path).replace("'", "''")

    def execute(self, query: CompiledQuery) -> list[dict[str, Any]]:
        """Execute a parameterized compiler result; raw SQL is never accepted here."""

        if not isinstance(query, CompiledQuery):
            raise TypeError("LocalDuckDBAdapter executes CompiledQuery instances only")
        if query.target_platform != "DuckDB":
            raise ValueError("local adapter only executes DuckDB compiled queries")
        connection = duckdb.connect(database=":memory:")
        try:
            for view, filename in _VIEWS.items():
                csv_path = self.curated_data_path / filename
                if not csv_path.is_file():
                    raise ValueError(f"required curated source is missing: {filename}")
                connection.execute(
                    f"CREATE VIEW {view} AS SELECT * FROM read_csv_auto('{self._sql_literal(csv_path)}', HEADER=TRUE)"
                )
            cursor = connection.execute(query.sql, query.parameters)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
        finally:
            connection.close()
