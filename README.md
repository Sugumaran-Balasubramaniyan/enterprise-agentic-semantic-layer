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
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
make PYTHON=.venv/bin/python test
make PYTHON=.venv/bin/python demo
```

Supported targets are `setup`, `test`, `lint`, `validate-semantic`, `demo`,
`evaluate`, and `run-api`; invoke any target as
`make PYTHON=.venv/bin/python <target>`.
The virtual environment keeps project dependencies isolated from Ubuntu's
PEP 668 externally managed system Python. The `validate-semantic` target reports
the valid graph as conforming and the invalid fixture as an expected failure.

## 5-minute interview demo

Use the full narrative in [the interview demo guide](docs/interview-demo-guide.md).
The short version is:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
make PYTHON=.venv/bin/python validate-semantic
make PYTHON=.venv/bin/python demo
```

In the `RESULT` section, the deterministic answer is:

```json
[
  {"customer_id": "FR_001", "country": "FR", "claim_count": 3, "total_incurred_loss_eur": 24000.0},
  {"customer_id": "FR_002", "country": "FR", "claim_count": 3, "total_incurred_loss_eur": 25000.0}
]
```

To show the HTTP boundary, run `make PYTHON=.venv/bin/python run-api` in one terminal,
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
queried physical CSV sources separately from all quality-validated CSV sources,
semantic versions, authorization and quality outcomes, row count, timestamp,
and integrity evidence. The API exposes the envelope at
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

## Architecture at a glance

```mermaid
flowchart TB
    User[User or application] --> Agent[Deterministic agent workflow]
    Agent --> Access[Semantic access layer]
    Access --> Resolve[Resolver and typed planner]
    Resolve --> Registry[Git-backed semantic registry]
    Registry --> Assets[Vocabulary, taxonomy, ontology, SHACL, metrics, rules]
    Registry --> Products[Certified products and mappings]
    Access --> Policy[Authorization and quality gates]
    Resolve --> Compiler[Platform SQL compiler]
    Compiler --> DuckDB[Local DuckDB adapter]
    Compiler -. documented extension .-> Cloud[Databricks / Snowflake / Fabric]
    DuckDB --> Evidence[Lineage and signed provenance]
```

The stable contract is the semantic plan. It contains canonical concepts,
relationships, filters, metric predicates, time context, caller context, and
approved products—but no SQL. Only the compiler knows physical field names and
produces parameterized SQL for a selected execution platform.

### Runtime sequence

```mermaid
sequenceDiagram
    participant Q as Question
    participant A as Agent
    participant R as Resolver
    participant G as Governance
    participant P as Planner
    participant C as Compiler
    participant X as DuckDB
    participant V as Provenance
    Q->>A: Business language
    A->>R: Concepts, synonyms, relationships
    R-->>A: Canonical IDs
    A->>G: Pre-authorization discovery
    G-->>A: ALLOWED or denied
    A->>P: Build final typed plan
    P->>C: Compile governed plan
    C->>X: Trusted parameterized SQL
    X-->>A: Result rows
    A->>G: Quality and result validation
    A->>V: Append signed evidence
    V-->>A: Query ID
    A-->>Q: Answer with provenance
```

## The semantic contract

The canonical vocabulary includes `Customer`, `Policy`, `Claim`,
`InsuranceProduct`, `MotorInsurance`, `Risk`, `Coverage`, `Premium`,
`ClaimStatus`, `Country`, `ActivePolicy`, `QualifyingClaim`, and
`IncurredLoss`. The compact ontology models:

```text
Customer ownsPolicy Policy
Customer submitsClaim Claim
Claim relatesToPolicy Policy
Policy hasProduct InsuranceProduct
Policy coversRisk Risk
Policy hasCoverage Coverage
Policy generatesPremium Premium
MotorInsurance subclassOf InsuranceProduct
```

Governed metrics are defined in `semantic/metrics/metrics.yaml`:

| Metric | Meaning |
| --- | --- |
| `ClaimCount` | Count of qualifying claims |
| `TotalIncurredLoss` | Sum of qualifying incurred loss |
| `AverageClaimAmount` | Average qualifying claim amount |
| `ActivePolicyCount` | Policies satisfying the ActivePolicy rule |
| `ClaimsRatio` | Separately aggregated loss divided by earned premium |

`QualifyingClaim` excludes `CANCELLED` and `DUPLICATE`. This is a versioned
semantic rule, not an instruction for an LLM to invent.

## Federation: one meaning, different implementations

GlobalSure’s Group model owns canonical labels, relationships, interoperability
rules, and governance. Country domains own local products, physical schemas,
mappings, extensions, and regulatory rules.

| Country | Platform example | Local motor codes | Canonical value |
| --- | --- | --- | --- |
| France | Databricks | `MOTOR`, `MTR` | `insurance:MotorInsurance` |
| UK | Snowflake | `AUTO`, `CAR` | `insurance:MotorInsurance` |
| Germany | Microsoft Fabric | `MotorInsurance` | `insurance:MotorInsurance` |

The same Group plan can compile against different physical columns and code
systems without making the agent rediscover joins.

## Governance and data quality

The local policy engine demonstrates RBAC and ABAC patterns for
`ClaimsAnalystFR`, `ClaimsManagerGroup`, `FinanceAnalyst`, and the synthetic
`AgentService` context. Country scope, purpose, product classification, and
PII access are checked before final planning and execution. The request-body
role is a simulator, not production identity authentication.

Quality checks reject missing or duplicate identifiers, blank join keys,
invalid countries/products/statuses, future dates, negative or non-finite loss,
and degraded/unsafe products. A failed quality capability cannot be passed to
the DuckDB adapter. Provenance records the plan, query, parameters, semantic
closure, selected products, queried sources, quality-validated sources,
authorization outcome, quality result, and integrity evidence.

## API endpoints

Run `make PYTHON=.venv/bin/python run-api`, then open
`http://127.0.0.1:8000/docs` for generated OpenAPI documentation.

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Service health |
| `GET /concepts`, `/concepts/{id}` | Vocabulary discovery and definitions |
| `GET /concepts/{id}/relationships` | Governed relationship lookup |
| `GET /metrics`, `/metrics/{id}` | Metric definitions and ownership |
| `GET /data-products`, `/data-products/{id}` | Certified product contracts |
| `GET /mappings/{concept}` | Platform mappings |
| `POST /resolve` | Deterministic business-term resolution |
| `POST /query-plan` | Authorized typed logical plan |
| `POST /execute` | Governed local execution |
| `POST /validate` | Semantic/data-quality validation |
| `GET /provenance/{query_id}` | Signed runtime evidence |

SQL-shaped questions, unsupported residual constraints, unauthorized roles, and
degraded products fail closed.

## Testing and evaluation

The golden corpus contains 31 distinct governed questions, including the ten
secondary scenarios in the project brief. It measures concept resolution,
relationship resolution, certified-product selection, metrics, authorization,
deterministic executable answers, and discovery-only constraints.

```bash
make test
make lint
make validate-semantic
make check-yaml
make check-mappings-quality
make check-golden
make check-compiler
make evaluate
make PYTHON=.venv/bin/python demo
```

The verified local run reports 195 passing tests, 31/31 golden cases, and
10/10 discovery-only cases. The single warning is a third-party FastAPI/
Starlette `TestClient` deprecation notice, not a project failure.

## Repository map

```text
semantic/                  Versioned vocabulary, taxonomy, ontology, SHACL, rules and metrics
data_products/             Certified product contracts and SLAs
mappings/                  Databricks, Snowflake and Fabric field/value mappings
data/                      Deterministic synthetic raw and curated CSV generation
src/semantic_layer/
  registry/                Git-backed registry and SQLite cache
  resolver/                Synonym and local-code grounding
  query_planner/           Typed logical plans and closed grammar
  compiler/                Trusted DuckDB compiler and cloud artifacts
  adapters/                Local execution and cloud extension seams
  governance/quality/      Authorization and quality gates
  lineage/provenance/      Source lineage and signed evidence
  agents/                  Workflow and governed tools
  api/                     FastAPI transport
tests/                     Unit, semantic, integration, golden and security tests
docs/                      Architecture, ADRs, governance, interview guide, verification
examples/                  Plans, questions and SQL artifacts
```

## Semantic assets as software

Semantic assets are version-controlled and tested like code:

- **Patch:** metadata or documentation correction with unchanged meaning.
- **Minor:** compatible synonym, relationship, or concept addition.
- **Major:** changed definition, metric semantics, join contract, or interpretation.

Changing `ActivePolicy`, `QualifyingClaim`, a mapping value, or a metric
definition requires updated regression and golden evidence. CI runs linting,
YAML parsing, ontology/SHACL checks, mapping and quality tests, compiler tests,
API tests, golden evaluation, and the complete suite.

## Production evolution

This is a local reference implementation, not a claim of live cloud integration.

1. Replace synthetic caller roles with trusted identity, purpose, and policy
   decision services.
2. Keep Group vocabulary, ontology, metrics, and product contracts in Git with
   semantic versioning and review gates.
3. Connect one platform adapter at a time: Unity Catalog/Delta and Metric Views
   for Databricks; governed semantic views, RBAC, masking and query history for
   Snowflake; OneLake, Fabric semantic models and lineage for Fabric.
4. Delegate row/column security to the underlying platform rather than bypassing
   it through the semantic service.
5. Move signing to an external KMS/HSM or privileged signing service and add
   observability for plan decisions, quality, latency, cost, and provenance.
6. Onboard additional domains through certified products and golden tests,
   preserving local autonomy while maintaining Group interoperability.

## Interview walkthrough

Use [docs/interview-demo-guide.md](docs/interview-demo-guide.md) for the full
script. The concise narrative is:

1. Start with the business question, not ontology technology.
2. Show the resolver grounding “car insurance” and “loss amount”.
3. Show the typed plan and certified products.
4. Show FR/UK/DE mapping normalization.
5. Show authorization, quality, SQL, result, and provenance.
6. Explain why direct LLM-to-SQL, RAG alone, or a graph alone is insufficient.
7. Close with semantic versioning, CI, and federated ownership.

For design rationale, see [architecture](docs/architecture.md),
[semantic layer](docs/semantic-layer.md), [governance](docs/governance.md),
[federated semantics](docs/federated-semantics.md), the
[implementation plan](docs/implementation-plan.md), and the
[architecture decision records](docs/decisions/).

## Implemented versus simulated

**Implemented locally:** semantic assets, SHACL, deterministic resolver and
planner, registry, metrics/rules, authorization, quality, DuckDB execution,
FastAPI, agent workflow, provenance, synthetic data, evaluation, and CI.

**Simulated or documented:** Databricks, Snowflake, and Fabric connections and
execution; production identity authentication; external KMS/HSM signing;
enterprise-scale performance; and benchmark claims.

No confidential data, credentials, paid cloud account, or hosted LLM is required.

## License

MIT. See [LICENSE](LICENSE).
