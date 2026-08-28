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

## Durable provenance signing

Capability and provenance signatures are issued by an internal control-plane
authority and are intentionally absent from the public package API. Internal
Python names are an organization boundary, not a hard security boundary; a
production deployment must replace this local demo authority with an external
KMS or signing service and keep its key outside the application process.

For a local process or demo that needs provenance to survive a restart, set
`SEMANTIC_LAYER_SIGNING_KEY_FILE` to a file containing either 32 raw bytes or
64 hexadecimal characters. `SEMANTIC_LAYER_SIGNING_KEY` accepts the same key
as hexadecimal text. Configure exactly one of these variables before starting
the process. If neither is configured, a fresh process-local key is generated;
that default is suitable only when persisted signatures do not need to be
verified after the process exits.
