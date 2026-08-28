# Federated Semantic Layer for Agentic AI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a locally runnable, governed semantic-layer reference project that answers the GlobalSure claims-investigation use case end to end.

**Architecture:** Declarative Git assets define canonical insurance semantics and local platform mappings. A deterministic Python control plane resolves business language, validates a typed plan, authorizes it, compiles trusted DuckDB SQL, and returns quality-aware provenance through an agent and FastAPI interface.

**Tech Stack:** Python 3.12, Pydantic v2, FastAPI, DuckDB, RDFLib, pySHACL, PyYAML, pytest, httpx, Ruff, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-28-federated-semantic-layer-design.md`

## Global Constraints

- Keep every runnable path local; do not require paid cloud accounts or an LLM key.
- Use `GlobalSure Insurance Group`; never use AXA data or claim real cloud execution.
- Write production behavior test-first and verify its red/green cycle.
- Use typed Pydantic v2 contracts; never accept arbitrary SQL from an agent.
- Prefer certified data products and fail closed on authorization or unsafe quality state.
- Create a meaningful commit after each independently testable task.
- Keep semantic assets in Git and assign an explicit semantic version.

---

## File Structure

| Path | Responsibility |
| --- | --- |
| `semantic/` | Versioned vocabulary, taxonomy, ontology, SHACL, graph, rules, metrics and synonyms |
| `data_products/`, `mappings/` | Certified product contracts and platform-specific semantic normalization |
| `data/` | Deterministic raw/curated insurance demo data |
| `src/semantic_layer/models.py` | Shared Pydantic contracts and typed query plan |
| `src/semantic_layer/{registry,resolver,query_planner,compiler,adapters}` | Semantic control and execution path |
| `src/semantic_layer/{governance,quality,lineage,provenance,agents,api}` | Controls, traceability, orchestration and transport |
| `tests/` | Unit, semantic, integration and golden contracts |
| `docs/`, `README.md` | Architecture, governance, production evolution and interview narrative |

### Task 1: Bootstrap the local project and test harness

**Files:**
- Create: `pyproject.toml`, `Makefile`, `.gitignore`, `.env.example`, `LICENSE`, `src/semantic_layer/__init__.py`, `tests/conftest.py`, `tests/unit/test_project_contract.py`, `.github/workflows/ci.yml`
- Modify: `README.md`

**Interfaces:**
- Produces the installable package `semantic_layer` and commands `make setup`, `make test`, `make lint`, `make validate-semantic`, `make demo`, `make evaluate`, `make run-api`.

- [ ] **Step 1: Write the failing project contract test**

```python
from importlib.metadata import version

def test_distribution_exposes_semantic_layer_package() -> None:
    assert version("enterprise-agentic-semantic-layer") == "0.1.0"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/unit/test_project_contract.py -q`

Expected: FAIL because the distribution is not installed.

- [ ] **Step 3: Add the minimal packaging and tooling configuration**

Use `setuptools` package discovery under `src`; declare runtime dependencies `duckdb`, `fastapi`, `pydantic`, `PyYAML`, `rdflib`, `pyshacl`, and `uvicorn`; declare test/lint extras `pytest`, `httpx`, and `ruff`. Make targets call `python -m pytest`, `ruff check .`, `python -m semantic_layer.validation`, `python -m semantic_layer.demo`, `python -m semantic_layer.evaluation`, and Uvicorn. CI installs `[dev]` and runs the matching commands.

- [ ] **Step 4: Install editable dependencies and run the test**

Run: `python -m pip install -e '.[dev]' && python -m pytest tests/unit/test_project_contract.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml Makefile .gitignore .env.example LICENSE README.md src tests .github
git commit -m "chore: initialize semantic layer project"
```

### Task 2: Add canonical semantic assets, ontology and SHACL validation

**Files:**
- Create: `semantic/vocabulary/insurance.yaml`, `semantic/taxonomy/insurance-products.ttl`, `semantic/ontology/insurance.ttl`, `semantic/shapes/insurance-shapes.ttl`, `semantic/ontology/sample-graph-valid.ttl`, `semantic/ontology/sample-graph-invalid.ttl`, `src/semantic_layer/semantic_validation.py`, `src/semantic_layer/validation.py`, `tests/semantic/test_vocabulary.py`, `tests/semantic/test_shacl.py`, `docs/ontology.md`, `docs/semantic-layer.md`

**Interfaces:**
- Produces `load_vocabulary(path: Path) -> list[Concept]` and `validate_graph(data_path: Path, shapes_path: Path) -> ValidationResult`.

- [ ] **Step 1: Write failing semantic tests**

```python
def test_claim_vocabulary_has_required_governance_metadata() -> None:
    claim = next(c for c in load_vocabulary(VOCABULARY) if c.id == "insurance:Claim")
    assert claim.version == "1.0.0"
    assert "Insurance Claim" in claim.synonyms
    assert claim.sensitivity.classification == "Confidential"

def test_invalid_claim_graph_fails_shacl_validation() -> None:
    result = validate_graph(INVALID_GRAPH, SHAPES)
    assert result.conforms is False
    assert "claimDate" in result.report_text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/semantic/test_vocabulary.py tests/semantic/test_shacl.py -q`

Expected: FAIL because assets and loader functions do not exist.

- [ ] **Step 3: Implement compact, valid semantic assets and loader**

Create all thirteen required canonical concepts with ID, name, version, definition, description, synonyms, domain, owner, classification, sensitivity, relationships/allowed values, examples. Model SKOS broader/narrower and alternatives for Motor Insurance. Model specified OWL classes/properties/domain/range. Shapes require Claim ID/date/status/policy and non-negative loss; Policy ID/product/status. Create one conforming and one non-conforming graph. Load YAML into Pydantic models and validate SHACL through pySHACL.

- [ ] **Step 4: Run semantic tests and CLI validation**

Run: `python -m pytest tests/semantic/test_vocabulary.py tests/semantic/test_shacl.py -q && python -m semantic_layer.validation`

Expected: PASS, with valid graph conforming and invalid graph failing as an expected fixture.

- [ ] **Step 5: Commit**

```bash
git add semantic src/semantic_layer/semantic_validation.py src/semantic_layer/validation.py tests/semantic docs
git commit -m "feat: add insurance ontology and semantic validation"
```

### Task 3: Define data products, federated mappings, governed metrics and deterministic data

**Files:**
- Create: `data_products/customer360.yaml`, `data_products/policy_master.yaml`, `data_products/claims_analytics.yaml`, `data_products/premium_analytics.yaml`, `mappings/databricks/france.yaml`, `mappings/snowflake/united_kingdom.yaml`, `mappings/fabric/germany.yaml`, `semantic/metrics/metrics.yaml`, `semantic/rules/claims.yaml`, `data/generate_demo_data.py`, `src/semantic_layer/data_generation.py`, `tests/semantic/test_mappings.py`, `tests/unit/test_data_generation.py`, `docs/data-products.md`, `docs/federated-semantics.md`

**Interfaces:**
- Produces `generate_demo_data(output_dir: Path, as_of: date) -> None` and mapping normalization `canonical_product(platform: str, value: str) -> str`.

- [ ] **Step 1: Write failing data/mapping tests**

```python
def test_all_local_motor_codes_normalize_to_group_motor_insurance() -> None:
    assert canonical_product("databricks", "MTR") == "insurance:MotorInsurance"
    assert canonical_product("snowflake", "CAR") == "insurance:MotorInsurance"
    assert canonical_product("fabric", "MotorInsurance") == "insurance:MotorInsurance"

def test_generated_data_contains_primary_use_case_candidates(tmp_path: Path) -> None:
    generate_demo_data(tmp_path, date(2026, 8, 28))
    assert (tmp_path / "curated" / "claims.csv").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/semantic/test_mappings.py tests/unit/test_data_generation.py -q`

Expected: FAIL because mapping and generation APIs do not exist.

- [ ] **Step 3: Implement deterministic assets and records**

Define certified contracts with owner, platform, location, schema, grain, SLA, quality, classification, PII, lineage, concepts and version. Create mapping metadata for physical fields and local product/status normalization. Define ClaimCount, TotalIncurredLoss, AverageClaimAmount, ActivePolicyCount and ClaimsRatio; qualifying claims exclude CANCELLED/DUPLICATE. Generate reproducible FR/UK/DE CSVs including multiple policies, qualifying French candidates above threshold, cancellations, duplicates, and raw invalid records.

- [ ] **Step 4: Run tests and inspect generated files**

Run: `python -m pytest tests/semantic/test_mappings.py tests/unit/test_data_generation.py -q && python data/generate_demo_data.py`

Expected: PASS and four curated CSV files exist under `data/curated`.

- [ ] **Step 5: Commit**

```bash
git add data data_products mappings semantic/metrics semantic/rules src/semantic_layer/data_generation.py tests docs
git commit -m "feat: add federated products mappings and demo data"
```

### Task 4: Implement typed registry, resolver and query planner

**Files:**
- Create: `src/semantic_layer/models.py`, `src/semantic_layer/registry/__init__.py`, `src/semantic_layer/registry/service.py`, `src/semantic_layer/resolver/__init__.py`, `src/semantic_layer/resolver/service.py`, `src/semantic_layer/query_planner/__init__.py`, `src/semantic_layer/query_planner/service.py`, `tests/unit/test_registry.py`, `tests/unit/test_resolver.py`, `tests/unit/test_query_planner.py`

**Interfaces:**
- Produces `SemanticRegistry.from_repository(root: Path) -> SemanticRegistry`, `resolve(text: str) -> Resolution`, and `build_plan(question: str, role: str) -> SemanticQueryPlan`.

- [ ] **Step 1: Write failing plan/resolution tests**

```python
def test_resolver_grounds_car_insurance_in_canonical_concept(registry: SemanticRegistry) -> None:
    assert "insurance:MotorInsurance" in registry.resolver.resolve("car insurance").concept_ids

def test_primary_question_produces_typed_governed_plan(registry: SemanticRegistry) -> None:
    plan = build_plan(PRIMARY_QUESTION, role="ClaimsAnalystFR", registry=registry)
    assert plan.root_entity == "insurance:Customer"
    assert plan.metric_predicates[0].metric_id == "insurance:ClaimCount"
    assert plan.selected_products == ["Customer360", "PolicyMaster", "ClaimsAnalytics"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_registry.py tests/unit/test_resolver.py tests/unit/test_query_planner.py -q`

Expected: FAIL because typed models and services do not exist.

- [ ] **Step 3: Implement registry and deterministic language control plane**

Use Pydantic models for concepts, products, mappings, metrics, caller context, filter, metric predicate and plan. Registry loads assets into a SQLite cache but reads Git assets as source of truth. Resolver applies normalized exact token/synonym matching. Planner recognizes the primary and secondary question patterns, resolves canonical IDs, relationship path, certified products, current-year/last-12-months time filters, and never stores raw SQL.

- [ ] **Step 4: Run unit tests**

Run: `python -m pytest tests/unit/test_registry.py tests/unit/test_resolver.py tests/unit/test_query_planner.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/semantic_layer/models.py src/semantic_layer/registry src/semantic_layer/resolver src/semantic_layer/query_planner tests/unit
git commit -m "feat: add semantic registry resolver and query planning"
```

### Task 5: Add authorization, quality, compiler, local execution and provenance

**Files:**
- Create: `src/semantic_layer/governance/__init__.py`, `src/semantic_layer/governance/policy.py`, `src/semantic_layer/quality/__init__.py`, `src/semantic_layer/quality/checks.py`, `src/semantic_layer/compiler/__init__.py`, `src/semantic_layer/compiler/base.py`, `src/semantic_layer/compiler/duckdb.py`, `src/semantic_layer/compiler/cloud_examples.py`, `src/semantic_layer/adapters/__init__.py`, `src/semantic_layer/adapters/duckdb.py`, `src/semantic_layer/adapters/cloud.py`, `src/semantic_layer/lineage/__init__.py`, `src/semantic_layer/lineage/service.py`, `src/semantic_layer/provenance/__init__.py`, `src/semantic_layer/provenance/store.py`, `tests/unit/test_authorization.py`, `tests/unit/test_quality.py`, `tests/unit/test_compiler.py`, `tests/integration/test_duckdb_execution.py`, `examples/generated_sql/README.md`

**Interfaces:**
- Produces `authorize(plan, caller) -> AuthorizationDecision`, `validate_curated_data(path) -> QualityReport`, `DuckDBCompiler.compile(plan) -> CompiledQuery`, `LocalDuckDBAdapter.execute(query) -> list[dict]`, and `ProvenanceStore.record(...) -> Provenance`.

- [ ] **Step 1: Write failing control-path tests**

```python
def test_fr_analyst_is_denied_non_fr_customer_data(plan: SemanticQueryPlan) -> None:
    denied = authorize(plan.with_country("DE"), CallerContext(role="ClaimsAnalystFR"))
    assert denied.allowed is False

def test_primary_plan_executes_without_cancelled_or_duplicate_claims(local_runtime) -> None:
    rows = local_runtime.execute_primary(PRIMARY_QUESTION, role="ClaimsAnalystFR")
    assert {row["customer_id"] for row in rows} >= {"FR_001", "FR_002"}

def test_provenance_records_semantic_sources(local_runtime) -> None:
    provenance = local_runtime.execute_primary(PRIMARY_QUESTION, role="ClaimsAnalystFR").provenance
    assert provenance.quality_status == "PASS"
    assert "ClaimsAnalytics" in provenance.data_products
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_authorization.py tests/unit/test_quality.py tests/unit/test_compiler.py tests/integration/test_duckdb_execution.py -q`

Expected: FAIL because controls and adapter do not exist.

- [ ] **Step 3: Implement controls and compilers**

Implement RBAC/ABAC policy checks, field-level PII denial for finance, and country filtering. Implement checks for IDs, non-negative loss, date, status, country and product mapping with a quality score. Compile only validated plan types using approved joins/mappings and query parameters; create cloud dialect example files while cloud adapters raise a clear credential/configuration error. Persist provenance in local SQLite with static source-to-product-to-metric lineage plus dynamic query data.

- [ ] **Step 4: Run tests and generated SQL examples**

Run: `python -m pytest tests/unit/test_authorization.py tests/unit/test_quality.py tests/unit/test_compiler.py tests/integration/test_duckdb_execution.py -q`

Expected: PASS, returning deterministic FR results and stored provenance.

- [ ] **Step 5: Commit**

```bash
git add src/semantic_layer/governance src/semantic_layer/quality src/semantic_layer/compiler src/semantic_layer/adapters src/semantic_layer/lineage src/semantic_layer/provenance tests examples
git commit -m "feat: add governed compilation local execution and provenance"
```

### Task 6: Build the deterministic agent workflow, CLI demo and FastAPI API

**Files:**
- Create: `src/semantic_layer/agents/__init__.py`, `src/semantic_layer/agents/workflow.py`, `src/semantic_layer/agents/tools.py`, `src/semantic_layer/demo.py`, `src/semantic_layer/api/__init__.py`, `src/semantic_layer/api/app.py`, `tests/integration/test_agent_e2e.py`, `tests/integration/test_api.py`, `examples/example_questions.md`, `examples/generated_query_plans/primary_claims_plan.json`

**Interfaces:**
- Produces `ClaimsInvestigationAgent.answer(question: str, caller: CallerContext) -> AgentAnswer` and FastAPI `app`.

- [ ] **Step 1: Write failing end-to-end and API tests**

```python
def test_agent_returns_answer_plan_sql_and_provenance() -> None:
    answer = agent.answer(PRIMARY_QUESTION, CallerContext(role="ClaimsAnalystFR"))
    assert answer.authorization.allowed is True
    assert answer.plan.root_entity == "insurance:Customer"
    assert "SELECT" in answer.compiled_query.sql
    assert answer.provenance.query_id

def test_execute_endpoint_returns_traceable_agent_answer(client: TestClient) -> None:
    response = client.post("/execute", json={"question": PRIMARY_QUESTION, "role": "ClaimsAnalystFR"})
    assert response.status_code == 200
    assert response.json()["provenance"]["quality_status"] == "PASS"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/integration/test_agent_e2e.py tests/integration/test_api.py -q`

Expected: FAIL because agent workflow and HTTP application do not exist.

- [ ] **Step 3: Implement agent orchestration and HTTP transport**

Make workflow stages explicit: intent parse, resolve, relationships/product selection, authorization, plan, compile, execute, result validation, provenance and answer formatting. Expose read endpoints and request endpoints named in the spec. Keep API as a thin adapter around services. The CLI prints the headings BUSINESS QUESTION, SEMANTIC RESOLUTION, DATA PRODUCTS, SEMANTIC QUERY PLAN, PHYSICAL MAPPING, GENERATED SQL, VALIDATION, RESULT and PROVENANCE.

- [ ] **Step 4: Run integration tests and the demo**

Run: `python -m pytest tests/integration/test_agent_e2e.py tests/integration/test_api.py -q && python -m semantic_layer.demo`

Expected: PASS and readable deterministic end-to-end output.

- [ ] **Step 5: Commit**

```bash
git add src/semantic_layer/agents src/semantic_layer/api src/semantic_layer/demo.py tests/integration examples
git commit -m "feat: add semantic agent workflow and API"
```

### Task 7: Create golden evaluation, regression tests and CI semantic checks

**Files:**
- Create: `tests/golden/questions.yaml`, `tests/golden/test_evaluation.py`, `tests/semantic/test_metric_rules.py`, `tests/semantic/test_active_policy_regression.py`, `src/semantic_layer/evaluation/__init__.py`, `src/semantic_layer/evaluation/runner.py`, `docs/evaluation.md`
- Modify: `.github/workflows/ci.yml`, `Makefile`

**Interfaces:**
- Produces `run_evaluation(registry: SemanticRegistry) -> EvaluationReport` with resolution, relationship, product, metric, authorization and deterministic-answer fields.

- [ ] **Step 1: Write a failing golden evaluation test**

```python
def test_golden_suite_has_at_least_thirty_governed_questions() -> None:
    cases = load_golden_cases(GOLDEN_CASES)
    assert len(cases) >= 30
    report = run_evaluation(runtime)
    assert report.total_cases == len(cases)
    assert report.failed_cases == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/golden/test_evaluation.py tests/semantic/test_metric_rules.py tests/semantic/test_active_policy_regression.py -q`

Expected: FAIL because the golden dataset and runner do not exist.

- [ ] **Step 3: Implement evaluation and regression coverage**

Author at least 30 questions, including all ten specified secondary examples; each records expected concepts, relationships, products, metrics, authorization and deterministic constraints/answers where applicable. Add a primary answer assertion and ActivePolicy semantic-version regression assertion. Update CI and Makefile to run YAML parsing, SHACL, mapping/data quality, golden tests, compiler tests and pytest.

- [ ] **Step 4: Run evaluation and semantic tests**

Run: `make validate-semantic && make evaluate && python -m pytest tests/golden tests/semantic -q`

Expected: PASS with an actual local evaluation summary and no fabricated benchmark claim.

- [ ] **Step 5: Commit**

```bash
git add tests/golden tests/semantic src/semantic_layer/evaluation docs/evaluation.md .github/workflows/ci.yml Makefile
git commit -m "test: add golden semantic evaluation suite"
```

### Task 8: Finish production-oriented documentation, diagrams and ADRs

**Files:**
- Create: `docs/architecture.md`, `docs/agent-architecture.md`, `docs/governance.md`, `docs/implementation-plan.md`, `docs/interview-demo-guide.md`, `docs/decisions/ADR-001-canonical-group-model.md`, `docs/decisions/ADR-002-semantic-assets-in-git.md`, `docs/decisions/ADR-003-ontology-runtime-boundary.md`, `docs/decisions/ADR-004-typed-query-plans.md`, `docs/decisions/ADR-005-platform-compilation-boundary.md`, `docs/decisions/ADR-006-duckdb-local-demo.md`, `docs/decisions/ADR-007-deterministic-core.md`, `docs/decisions/ADR-008-certified-data-products.md`
- Modify: `README.md`, `docs/data-products.md`, `docs/federated-semantics.md`, `docs/ontology.md`, `docs/semantic-layer.md`

**Interfaces:**
- Produces a complete README with verified commands and a demo guide with 30-second, 2-minute, 5-minute and 10-minute narratives.

- [ ] **Step 1: Write failing documentation contract tests**

```python
def test_readme_contains_required_interview_sections() -> None:
    readme = Path("README.md").read_text()
    for heading in ["5-minute interview demo", "Architecture", "How to run", "Provenance"]:
        assert heading in readme

def test_architecture_docs_contain_six_mermaid_diagrams() -> None:
    diagrams = sum(path.read_text().count("```mermaid") for path in Path("docs").rglob("*.md"))
    assert diagrams >= 6
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_documentation_contract.py -q`

Expected: FAIL because documentation is incomplete.

- [ ] **Step 3: Write the documentation**

Document what is implemented, simulated, and production extension separately. Add high-level, request-flow, federated, mapping, agent sequence and CI lifecycle Mermaid diagrams. Explain RAG vs semantics, graph role, platform independence, Group/local ownership, quality and security. Include exact cURL commands and output excerpts based only on executed demo data. Write the implementation phases and 30/60/90-day plan. Each ADR has context, decision, alternatives and consequences.

- [ ] **Step 4: Run documentation tests and link/diagram fence checks**

Run: `python -m pytest tests/unit/test_documentation_contract.py -q && rg -n '```mermaid|```' README.md docs`

Expected: PASS and all Mermaid fences are balanced.

- [ ] **Step 5: Commit**

```bash
git add README.md docs tests/unit/test_documentation_contract.py
git commit -m "docs: add interview guide architecture and ADRs"
```

### Task 9: Run final verification, security checks and prepare publication handoff

**Files:**
- Create: `docs/verification-report.md`

**Interfaces:**
- Produces evidence-backed final report; publication occurs only after checking authentication/remotes and never overwrites an existing repository.

- [ ] **Step 1: Write a verification report skeleton with required evidence headings**

```markdown
## Commands and results
## Main end-to-end claims demonstration
## Semantic validation and SHACL
## Golden evaluation
## Security and secret scan
## Documentation review
## Known limitations
```

- [ ] **Step 2: Run the full local verification matrix**

Run: `make lint && make test && make validate-semantic && make evaluate && make demo && git diff --check && rg -n -i '(api[_-]?key|secret|password|token)\s*[:=]' --glob '!*.lock' .`

Expected: each command exits zero; any secret-scan findings are reviewed so benign field names are not represented as credentials.

- [ ] **Step 3: Record actual command output and limitations**

Do not write “PASS” until each command has completed in this task. State cloud adapters are unexecuted simulations, deterministic parsing is intentionally bounded, and the local data set is synthetic.

- [ ] **Step 4: Commit verification evidence**

```bash
git add docs/verification-report.md
git commit -m "docs: add verification evidence"
```

- [ ] **Step 5: Check GitHub availability without changing remote state**

Run: `git remote -v && gh auth status`

Expected: identify whether safe public repository creation/push can be offered; if unavailable, provide exact manual commands rather than attempting publication.

## Plan Self-Review

Coverage: Tasks 1–2 cover project foundation and semantic/SHACL assets; Task 3 covers data, products, metrics and federation; Tasks 4–6 cover the full controlled runtime and API; Task 7 covers golden evaluation/CI; Task 8 covers architecture, ADRs and interview narrative; Task 9 covers evidence and publication handoff. No production feature is left without an owner task.

Consistency: all runtime tasks consume `SemanticRegistry`, `SemanticQueryPlan`, approved mappings and `CallerContext`; no task introduces direct model-to-SQL execution. Tests are placed before their corresponding production behavior.

Scope ruling: the optional Streamlit UI is intentionally excluded. The specified core is already a complete proof of concept and the UI would reduce time available for evidence, governance, and documentation.
