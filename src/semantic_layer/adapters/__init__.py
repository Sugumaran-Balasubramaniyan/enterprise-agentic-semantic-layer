"""Execution-plane adapters with DuckDB and SQLite implementations."""

from semantic_layer.adapters.duckdb import ExecutionResult, LocalDuckDBAdapter
from semantic_layer.adapters.sqlite import SQLiteAdapter, SQLiteExecutionResult

__all__ = ["ExecutionResult", "LocalDuckDBAdapter", "SQLiteAdapter", "SQLiteExecutionResult"]
