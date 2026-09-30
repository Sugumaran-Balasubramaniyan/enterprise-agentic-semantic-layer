"""Unit tests for the SQLiteAdapter."""

from __future__ import annotations

import sqlite3

import pytest

from semantic_layer.adapters.sqlite import SQLiteAdapter, SQLiteExecutionResult


def test_sqlite_adapter_in_memory_lifecycle() -> None:
    with SQLiteAdapter(":memory:") as adapter:
        adapter.execute_sql(
            "CREATE TABLE products (id TEXT PRIMARY KEY, name TEXT, price REAL)"
        )
        adapter.execute_sql(
            "INSERT INTO products VALUES (?, ?, ?)", ["p1", "Widget", 19.99]
        )
        adapter.execute_sql(
            "INSERT INTO products VALUES (?, ?, ?)", ["p2", "Gadget", 29.50]
        )

        result = adapter.execute_sql(
            "SELECT id, name, price FROM products WHERE price > ? ORDER BY price DESC",
            [20.0],
        )

        assert isinstance(result, SQLiteExecutionResult)
        assert len(result) == 1
        assert result.columns == ["id", "name", "price"]
        assert result[0] == {"id": "p2", "name": "Gadget", "price": 29.50}

        payload = result.to_dict()
        assert payload["row_count"] == 1
        assert payload["rows"] == [{"id": "p2", "name": "Gadget", "price": 29.50}]


def test_sqlite_adapter_wraps_existing_connection() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE test (x INT)")
    conn.execute("INSERT INTO test VALUES (42)")

    adapter = SQLiteAdapter(conn)
    res = adapter.execute_sql("SELECT x FROM test")
    assert len(res) == 1
    assert res[0]["x"] == 42
    adapter.close()
    # The adapter should not close external connections that it does not own
    assert conn.execute("SELECT x FROM test").fetchone()[0] == 42
    conn.close()


def test_sqlite_adapter_rejects_non_finite_values() -> None:
    conn = sqlite3.connect(":memory:")
    adapter = SQLiteAdapter(conn)
    with pytest.raises(ValueError, match="execution returned non-finite value"):
        adapter._assert_finite_values([{"val": float("nan")}])
    with pytest.raises(ValueError, match="execution returned non-finite value"):
        adapter._assert_finite_values([{"val": float("inf")}])
    conn.close()
