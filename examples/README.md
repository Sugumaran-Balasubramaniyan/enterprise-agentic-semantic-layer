# Example index

This index separates executable local evidence from discovery contracts and
unimplemented extension seams. The local runtime is deterministic and does not
need a cloud account, MCP server, or LLM.

## Checked-in artifacts

| Artifact | Status | Purpose |
| --- | --- | --- |
| [Primary query plan](generated_query_plans/primary_claims_plan.json) | Checked in and exercised by the primary local path | Typed, SQL-free plan for the governed French claims question |
| [Generated SQL index](generated_sql/README.md) | DuckDB is executed; cloud dialect files are incomplete documentation artifacts | Physical compiler output and bounded adapter examples |
| [Governed questions](example_questions.md) | Primary question executes; active-policy and ClaimsRatio examples are discovery-only | Supported grammar and explicit authorization/execution limits |

## Route, request, and response examples

Start the local API with `make PYTHON=.venv/bin/python run-api`. Caller fields in
request bodies are simulation context, not authentication.

### Successful response

`POST /resolve` deterministically grounds business language without creating a
plan or executing SQL.

```bash
curl -s -X POST http://127.0.0.1:8000/resolve \
  -H 'content-type: application/json' \
  -d '{"question":"car insurance"}'
```

The stable response is:

```json
{
  "text": "car insurance",
  "concept_ids": ["insurance:MotorInsurance"],
  "matched_terms": {"insurance:MotorInsurance": "car insurance"}
}
```

### Fail-closed response

`POST /execute` rejects a role that has no semantic query policy before final
plan construction or SQL execution.

```bash
curl -s -X POST http://127.0.0.1:8000/execute \
  -H 'content-type: application/json' \
  -d '{"question":"Find French motor-insurance customers with at least three qualifying claims in the last 12 months and total incurred loss above EUR 20,000.","role":"UnknownRole"}'
```

The response status is `403` and the body is:

```json
{
  "detail": "ROLE_DENIED: role UnknownRole has no semantic query permission"
}
```

The complete implemented route list and request boundaries are in the
[README API section](../README.md#api-endpoints), with transport regressions in
[API integration tests](../tests/integration/test_api.py).

## Optional extension seams

MCP transport is not implemented. A future adapter may expose only the bounded
typed semantic tools documented in [agent architecture](../docs/agent-architecture.md),
must derive trusted caller context outside tool arguments, and must preserve
authorization, compiler, quality, and provenance gates. It must not provide an
arbitrary-SQL tool.

LLM integration is not implemented. A future model may propose an
interpretation or explanation, but deterministic resolution, typed plan
validation, policy, compilation, and provenance remain authoritative. Model
output cannot create SQL or override a fail-closed decision.
