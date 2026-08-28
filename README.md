# Federated Semantic Layer for Agentic AI

A locally runnable reference implementation of a governed semantic layer for
GlobalSure Insurance Group. It maps business concepts to certified data
products and deterministic platform adapters without requiring cloud
credentials or an LLM key.

## What this repository proves

The primary local path answers this business question end to end:

> Find French motor-insurance customers with at least three qualifying claims
> in the last 12 months and total incurred loss above EUR 20,000.

The deterministic agent resolves canonical concepts, selects certified data
products, authorizes the caller, builds a typed SQL-free plan, compiles trusted
DuckDB SQL, validates quality, and returns provenance. The data is synthetic.

DuckDB is the only fully implemented execution platform. Databricks,
Snowflake, and Microsoft Fabric mappings and SQL are extension artifacts and
are explicitly not executed or benchmarked here. No AXA data, paid cloud
account, production credential, or LLM key is required.

## How to run

```bash
python3 -m pip install -e '.[dev]'
make PYTHON=python3 test
make PYTHON=python3 demo
```

Supported commands are `make setup`, `make test`, `make lint`,
`make validate-semantic`, `make demo`, `make evaluate`, and `make run-api`.
When `python` is not on PATH, prefix each command with `PYTHON=python3` as
shown above. `make validate-semantic` reports the valid graph as conforming
and the invalid fixture as an expected failure.

## 5-minute interview demo

Use the full narrative in [the interview demo guide](docs/interview-demo-guide.md).
The short version is:

```bash
python3 -m pip install -e '.[dev]'
make PYTHON=python3 validate-semantic
make PYTHON=python3 demo
```

In the `RESULT` section, the deterministic answer is:

```json
[
  {"customer_id": "FR_001", "country": "FR", "claim_count": 3, "total_incurred_loss_eur": 24000.0},
  {"customer_id": "FR_002", "country": "FR", "claim_count": 3, "total_incurred_loss_eur": 25000.0}
]
```

To show the HTTP boundary, run `make PYTHON=python3 run-api` in one terminal,
then:

```bash
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/execute \
  -H 'content-type: application/json' \
  -d '{"question":"Find French motor-insurance customers with at least three qualifying claims in the last 12 months and total incurred loss above EUR 20,000.","role":"ClaimsAnalystFR"}'
```

The stable health output is `{"status":"ok"}`. The execute response includes
the typed plan, generated SQL, `PASS` quality, the two rows, and a runtime
`provenance.query_id`. Retrieve that evidence with
`curl -s http://127.0.0.1:8000/provenance/{query_id}`; the ID and digests are
deliberately runtime values rather than copied fixtures.

## Architecture

Read [architecture](docs/architecture.md) for the control-plane boundary and
diagrams, [agent architecture](docs/agent-architecture.md) for workflow and
tool contracts, and [federated semantics](docs/federated-semantics.md) for
Group/local ownership. [Governance](docs/governance.md) covers authorization,
quality, security, lineage, and semantic versioning.

The distinction matters: RAG can retrieve explanatory text, but only governed
semantic assets define canonical meaning, joins, metrics, access, and physical
field mappings. The ontology supplies typed relationships and SHACL validates
graphs; certified analytical products and compilers handle aggregation.

## Provenance

Every successful answer carries a provenance envelope containing the question
and plan digests, canonical concepts, metrics, selected products, mappings,
physical CSV sources, semantic versions, authorization and quality outcomes,
row count, timestamp, and integrity evidence. The API exposes the envelope at
`/provenance/{query_id}`. A local signing key can be configured for restart
safe demo signatures; production should use an external KMS or signing
service.

## Implemented, simulated, and next

- **Implemented:** local YAML/Turtle asset loading; deterministic resolution;
  typed planning; authorization; quality gates; DuckDB execution; FastAPI;
  agent workflow; provenance; SHACL; golden evaluation; CI checks.
- **Simulated/documented:** cloud dialect SQL and Databricks, Snowflake, and
  Fabric adapters. They require credentials and native platform security and
  are not claimed as executed.
- **Production extension:** connect one adapter at a time behind the compiler
  interface, delegate identity and row-level security to the platform, and
  retain the same semantic contracts and evidence-producing tests.

See [implementation plan](docs/implementation-plan.md) and the
[architecture decision records](docs/decisions/) for the production path.

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
