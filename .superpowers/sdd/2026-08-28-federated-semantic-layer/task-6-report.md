# Task 6 report: deterministic agent workflow, CLI, and FastAPI API

## Delivered scope

- Added `ClaimsInvestigationAgent.answer(question, caller) -> AgentAnswer`.
  Its explicit stages are intent parse, deterministic resolution,
  relationship/product selection, authorization, typed plan, trusted compile,
  local execution, result validation, provenance, and answer formatting. The
  agent has no LLM integration and no arbitrary-SQL tool.
- Added the governed tool layer required by the design: concept search and
  resolution, definitions, relationships, certified-product selection, metric
  metadata, typed planning, governed execution, and provenance retrieval.
- Added thin FastAPI routes: `/health`, `/concepts`, `/metrics`,
  `/data-products`, `/mappings`, `/resolve`, `/query-plan`, `/execute`,
  `/validate`, and `/provenance/{query_id}`. Denied execution returns HTTP 403
  before quality, compilation, or local data execution.
- Added `python -m semantic_layer.demo`, which prints the required headings:
  BUSINESS QUESTION, SEMANTIC RESOLUTION, DATA PRODUCTS, SEMANTIC QUERY PLAN,
  PHYSICAL MAPPING, GENERATED SQL, VALIDATION, RESULT, and PROVENANCE.
- Added public API/E2E tests, example questions, and the generated primary
  logical plan. The primary result remains exactly `FR_001` (3 / EUR 24,000)
  and `FR_002` (3 / EUR 25,000).

## TDD evidence

### RED

After creating the Task 6 integration tests and before creating the agent/API
modules, the required focused command failed during collection as expected:

```text
.venv/bin/python -m pytest tests/integration/test_agent_e2e.py tests/integration/test_api.py -q
ModuleNotFoundError: No module named 'semantic_layer.agents'
ModuleNotFoundError: No module named 'semantic_layer.api'
```

The first implementation run exposed a real transport regression rather than
being suppressed: FastAPI executed `/execute` in a worker thread while the
SQLite provenance connection had been created in the app-construction thread.
The reproducible error was `sqlite3.ProgrammingError: SQLite objects created
in a thread can only be used in that same thread`.

### GREEN

The provenance store now opens its one local SQLite connection with
`check_same_thread=False` and serializes both public append and read operations
with an `RLock`. This fixes the actual app/store boundary while retaining the
existing chain verification before every operation and the transactional
checkpoint update.

```text
.venv/bin/python -m pytest tests/integration/test_agent_e2e.py tests/integration/test_api.py -q
5 passed, 1 warning in 1.22s
```

## Fresh final verification

```text
.venv/bin/ruff check .
All checks passed!

.venv/bin/python -m pytest -q
105 passed, 1 warning in 6.74s

.venv/bin/python -m semantic_layer.demo
# output includes all nine required headings

# TestClient /execute followed by /provenance/{query_id}
API smoke: PASS

git diff --check
# no output; exit 0
```

## Review remediation round 2 of 5: guard query-plan transport

### Finding addressed

`/query-plan` previously called the final-plan tool directly. It discovered and
returned a `SemanticQueryPlan` for an unknown role because that route did not
obtain the pre-authorization capability added in round 1.

`SemanticAgentTools.build_query_plan` now always discovers the request,
obtains (or verifies a supplied) signed `DiscoveryAuthorizationDecision`, and
rejects denial or a context/signature mismatch before it calls the final
`build_plan` constructor. The agent supplies its already-issued capability;
the HTTP route uses exactly the same gate. No route can therefore return a
final plan to an unauthorized caller. The SQL-guard prose was also narrowed to
the supported primary-question phrase rather than an unqualified `customers
with three claims` example.

### TDD and verification evidence

RED:

```text
.venv/bin/python -m pytest tests/integration/test_api.py -q
test_query_plan_endpoint_denies_unknown_role_before_final_plan
expected 403, received 200
1 failed, 12 passed, 1 warning in 1.97s
```

GREEN:

```text
.venv/bin/python -m pytest tests/integration/test_api.py tests/integration/test_agent_e2e.py -q
15 passed, 1 warning in 2.15s

.venv/bin/ruff check src tests
All checks passed!

.venv/bin/python -m pytest tests/unit/test_authorization.py tests/unit/test_query_planner.py tests/integration/test_agent_e2e.py tests/integration/test_api.py -q
32 passed, 1 warning in 2.66s

.venv/bin/python -m pytest -q
115 passed, 1 warning in 7.61s

git diff --check
# no output; exit 0
```

The only warning is FastAPI/Starlette's installed TestClient deprecation notice
for the current `httpx` compatibility layer; it does not produce a test
failure.

## Security and scope notes

- API request schemas reject undeclared fields. `CallerContext` still enforces
  the closed `semantic_query` purpose; plan/caller conflicts are denied.
- The transport delegates to the existing signed authorization, quality,
  compiler, adapter, and provenance capabilities. It does not introduce a
  bypass, raw-SQL parameter, cloud execution, or external LLM call.
- The SQLite change is a scoped compatibility repair needed for synchronous
  FastAPI routes; it does not weaken the signed provenance envelope or the
  authenticated checkpoint chain.

## Review remediation round 1 of 5: stage and question boundaries

### Findings addressed

- The workflow previously constructed `SemanticQueryPlan` before authorization.
  It now performs deterministic `QueryDiscovery` first, authorizes that
  non-executable discovery against role, country, products, and projected PII,
  and constructs the final typed plan only after an allowed decision. The
  existing signed plan-bound authorization remains in place before compilation.
  A denied `PermissionError` carries the completed trace through `authorize`;
  it cannot reach final-plan construction, compile, quality, execution, or
  provenance.
- `QuestionRequest` now invokes the shared SQL-shape guard with the
  natural-language mode used by the agent/planner boundary. It rejects SQL
  statement tokens, comments, semicolons, `PRAGMA`, `ATTACH`, and `VACUUM`
  before `/execute` reaches the workflow. Natural-language `customers with
  three claims` remains valid while CTE-shaped `WITH name AS (...)` input is
  rejected.

### TDD evidence

RED: the new integration regression monkeypatched all post-authorization
stages to fail. An unknown role reached `build_query_plan` first, proving the
old ordering defect. The parameterized `/execute` regression also showed all
nine SQL-shaped inputs returning `200` rather than the required `422`.

```text
.venv/bin/python -m pytest tests/integration/test_agent_e2e.py tests/integration/test_api.py -q
10 failed, 4 passed, 1 warning in 2.89s
```

The first implementation attempt exposed and corrected an existing guard
ambiguity: its generic logical-plan matcher matched ordinary `with` in the
documented primary question. The natural-language variant now retains every
required executable marker and detects CTE syntax specifically.

GREEN:

```text
.venv/bin/python -m pytest tests/integration/test_agent_e2e.py tests/integration/test_api.py -q
14 passed, 1 warning in 2.02s

.venv/bin/ruff check src tests
All checks passed!

.venv/bin/python -m pytest tests/unit/test_authorization.py tests/unit/test_query_planner.py tests/unit/test_execution_controls_security.py tests/integration/test_agent_e2e.py tests/integration/test_api.py -q
42 passed, 1 warning in 3.22s

.venv/bin/python -m pytest -q
114 passed, 1 warning in 7.41s

git diff --check
# no output; exit 0
```
