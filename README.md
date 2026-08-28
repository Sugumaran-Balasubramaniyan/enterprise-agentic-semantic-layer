# Federated Semantic Layer for Agentic AI

A locally runnable reference implementation of a governed semantic layer for
GlobalSure Insurance Group. It maps business concepts to certified data
products and deterministic platform adapters without requiring cloud
credentials or an LLM key.

## Quick start

```bash
python -m pip install -e '.[dev]'
make test
make demo
```

Supported commands are `make setup`, `make test`, `make lint`,
`make validate-semantic`, `make demo`, `make evaluate`, and `make run-api`.
DuckDB is the local execution platform; Databricks, Snowflake, and Fabric
outputs are documented adapter artifacts and are not claimed as executed.
