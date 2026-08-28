# Interview demo guide

This guide uses the primary question:

> Find French motor-insurance customers with at least three qualifying claims
> in the last 12 months and total incurred loss above EUR 20,000.

The data is synthetic, deterministic, and local. The only executed adapter is
DuckDB. Databricks, Snowflake, and Microsoft Fabric mappings and SQL examples
are interfaces; they are not executed in this repository.

## 30-second narrative

“The semantic layer is a governed contract, not an LLM-to-SQL shortcut. The
agent resolves business terms to canonical concepts, chooses certified data
products, checks the caller, builds a typed plan, compiles trusted DuckDB SQL,
validates the result, and returns provenance. The same Group concepts normalize
French, UK, and German local product values.”

## 2-minute narrative

Run `make demo` and point out the stable headings: `SEMANTIC RESOLUTION`,
`DATA PRODUCTS`, `SEMANTIC QUERY PLAN`, `GENERATED SQL`, `VALIDATION`,
`RESULT`, and `PROVENANCE`. Explain that `QualifyingClaim` excludes
`CANCELLED` and `DUPLICATE`, and that the answer contains two deterministic
French customers:

```text
FR_001 | FR | 3 claims | EUR 24000.0
FR_002 | FR | 3 claims | EUR 25000.0
```

## 5-minute interview demo

From the repository root, install dependencies and run the complete local
path:

```bash
python3 -m pip install -e '.[dev]'
make PYTHON=python3 validate-semantic
make PYTHON=python3 demo
```

The first command installs only local Python dependencies. The validation
command reports the valid graph as conforming and the deliberately invalid
graph as failing its expected SHACL constraints. The demo's result section is
expected to contain exactly:

```json
[
  {"claim_count": 3, "country": "FR", "customer_id": "FR_001", "total_incurred_loss_eur": 24000.0},
  {"claim_count": 3, "country": "FR", "customer_id": "FR_002", "total_incurred_loss_eur": 25000.0}
]
```

Then show one API request in a second terminal:

```bash
make PYTHON=python3 run-api
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/execute \
  -H 'content-type: application/json' \
  -d '{"question":"Find French motor-insurance customers with at least three qualifying claims in the last 12 months and total incurred loss above EUR 20,000.","role":"ClaimsAnalystFR"}'
```

The stable health output is:

```json
{"status":"ok"}
```

The execute response includes `plan.root_entity` equal to
`insurance:Customer`, `authorization.allowed` equal to `true`, quality
`PASS`, the two rows above, generated SQL, and a provenance `query_id`. Use
that ID with `GET /provenance/{query_id}` to demonstrate independently
retrievable evidence. Query IDs and digests are intentionally runtime values;
they should not be copied as fixed demo output.

## 10-minute deep dive

Open [architecture](architecture.md), [agent architecture](agent-architecture.md),
and [governance](governance.md). Trace one claim from local mapping through
`ClaimsAnalytics`, the `QualifyingClaim` rule, the typed plan, the DuckDB
compiler, quality checks, and the provenance envelope. Show that an unknown
role receives HTTP 403 and that SQL-shaped request text receives HTTP 422.
Close with the federation boundary: cloud artifacts are documented but not
executed, and no benchmark or production-data claim is made.

## Questions to invite

- Why keep an ontology if the query runs in DuckDB? (Relationships and
  validation are distinct from analytical execution.)
- Why not let an LLM write SQL? (Typed plans, policy, mappings, and provenance
  make the answer reviewable and fail closed.)
- What changes for a cloud rollout? (Native identity/security and an adapter,
  while preserving the semantic contract and tests.)
