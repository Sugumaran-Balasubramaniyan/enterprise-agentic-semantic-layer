"""Execution-plane SQLite adapter for local and embedded analytical queries."""

from __future__ import annotations

import math
import sqlite3
import types
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any, Self


class SQLiteExecutionResult(Sequence[dict[str, Any]]):
    """Immutable output from one verified SQLite query execution."""

    __slots__ = ("_rows", "columns", "row_count")

    def __init__(self, rows: list[dict[str, Any]], columns: list[str]) -> None:
        self._rows = rows
        self.columns = columns
        self.row_count = len(rows)

    def __len__(self) -> int:
        return len(self._rows)

    def __getitem__(self, index: int | slice) -> Any:
        return self._rows[index]

    def to_dict(self) -> dict[str, Any]:
        return {
            "columns": self.columns,
            "row_count": self.row_count,
            "rows": self._rows,
        }


class SQLiteAdapter:
    """Execute parameterized SQL queries against a SQLite database connection or file."""

    def __init__(self, database: str | Path | sqlite3.Connection = ":memory:") -> None:
        if isinstance(database, sqlite3.Connection):
            self._connection = database
            self._owns_connection = False
        else:
            self._connection = sqlite3.connect(str(database))
            self._connection.row_factory = sqlite3.Row
            self._owns_connection = True

    def close(self) -> None:
        if self._owns_connection and self._connection:
            self._connection.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        self.close()

    @staticmethod
    def _assert_finite_values(rows: list[dict[str, Any]]) -> None:
        for row in rows:
            for field, value in row.items():
                if isinstance(value, Decimal) and not value.is_finite():
                    raise ValueError(f"execution returned non-finite value for {field}")
                if isinstance(value, float) and not math.isfinite(value):
                    raise ValueError(f"execution returned non-finite value for {field}")

    def execute_sql(self, sql: str, parameters: Sequence[Any] | None = None) -> SQLiteExecutionResult:
        """Execute parameterized SQL statement and return typed rows."""
        cursor = self._connection.cursor()
        params = list(parameters) if parameters is not None else []
        cursor.execute(sql, params)
        if cursor.description is None:
            return SQLiteExecutionResult([], [])

        columns = [desc[0] for desc in cursor.description]
        rows = [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]
        self._assert_finite_values(rows)
        return SQLiteExecutionResult(rows, columns)
