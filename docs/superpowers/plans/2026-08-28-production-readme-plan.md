# Production README Handbook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `README.md` a complete, accurate repository handbook for local use, production design review, operations, and extension of the federated semantic layer.

**Architecture:** Keep implementation and deep domain documentation unchanged unless an accuracy correction is required. Expand the README into linked handbook sections, add only documentation-contract tests needed to prevent drift, and verify every command/API claim against the current runtime.

**Tech Stack:** Markdown, Mermaid, FastAPI OpenAPI, Makefile, pytest, Ruff, existing Python/YAML/Turtle assets.

**Spec:** `docs/superpowers/specs/2026-08-28-production-readme-design.md`

## Global Constraints

- Python 3.12+ is the supported runtime.
- DuckDB/local adapters are the only fully runnable execution path.
- Databricks, Snowflake, and Fabric integrations remain documented extension seams, not claimed live integrations.
- The demo uses synthetic data and request-body roles; production requires trusted identity and policy enforcement.
- README claims must match checked-in code and current verification output.
- Push each completed task as its own commit to `origin/feat/semantic-layer-implementation`.

---

### Task 1: Correct the API and verification contract

**Files:**
- Modify: `README.md`
- Test: `tests/unit/test_documentation_contract.py`
- Inspect: `src/semantic_layer/api/app.py`, `docs/verification-report.md`, `Makefile`

**Interfaces:**
- Consumes: FastAPI route declarations and existing documentation contract tests.
- Produces: An API table and verification section that list only implemented routes and identify the latest evidence source/date.

- [ ] **Step 1: Write failing tests** for route-table accuracy and evidence wording.
- [ ] **Step 2: Run the focused tests** and confirm they fail against the four unsupported detail routes/current evidence wording.
- [ ] **Step 3: Update README** with the exact OpenAPI route list, request/response notes, fail-closed examples, and evidence-date/source wording.
- [ ] **Step 4: Run focused documentation tests** and verify they pass.
- [ ] **Step 5: Commit and push** with `docs: align README API and verification contract`.

### Task 2: Add complete local developer and data lifecycle guidance

**Files:**
- Modify: `README.md`
- Test: `tests/unit/test_documentation_contract.py`
- Inspect: `data/generate_demo_data.py`, `data/curated/`, `data/raw/`, `pyproject.toml`, `.env.example`, `Makefile`

**Interfaces:**
- Consumes: Existing setup targets, synthetic-data generator, environment variables, and curated schemas.
- Produces: Prerequisites matrix, clean-install path, configuration matrix, data generation/fixture policy, schemas/grains/join keys, and reproducibility limitations.

- [ ] **Step 1: Add contract assertions** for Python version, no-cloud/no-LLM prerequisites, `.env` variables, raw-versus-curated data, deterministic seed/as-of behavior, and lockfile caveat.
- [ ] **Step 2: Run focused tests** to establish the missing documentation failures.
- [ ] **Step 3: Add the developer quickstart, support matrix, configuration table, data lifecycle, and reproducibility guidance.**
- [ ] **Step 4: Run setup, data generation, demo, and documentation tests.**
- [ ] **Step 5: Commit and push** with `docs: document local setup and data lifecycle`.

### Task 3: Add production deployment, security, operations, and failure runbook

**Files:**
- Modify: `README.md`
- Test: `tests/unit/test_documentation_contract.py`
- Inspect: `src/semantic_layer/governance/`, `src/semantic_layer/provenance/`, `src/semantic_layer/api/`, `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: Existing authorization, quality, provenance, signing, API, and CI behavior.
- Produces: Local-versus-production contract, target deployment topology, identity/security/privacy guidance, retention/backups, observability boundary, and failure/action matrix.

- [ ] **Step 1: Add contract assertions** for demo-only authentication, development-only reload, fail-closed cases, signing-key limitations, and observability/CI boundaries.
- [ ] **Step 2: Run focused tests** and confirm missing operational sections are detected.
- [ ] **Step 3: Add deployment topology, environment separation, production checklist, threat/privacy model, operations runbook, failure matrix, backup/restore, and upgrade guidance.**
- [ ] **Step 4: Run documentation tests and a local API smoke test.**
- [ ] **Step 5: Commit and push** with `docs: add production operations and security handbook`.

### Task 4: Add contribution, semantic release, federation onboarding, and traceability

**Files:**
- Modify: `README.md`
- Test: `tests/unit/test_documentation_contract.py`
- Inspect: `semantic/`, `data_products/`, `mappings/`, `docs/decisions/`, `tests/`, `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: Existing asset layout, ADRs, CI gates, golden evaluation corpus, and federated mappings.
- Produces: Ownership/review workflow, PR checklist, semantic compatibility/deprecation/migration policy, new-country onboarding path, capability traceability matrix, production extension matrix, and support/escalation guidance.

- [ ] **Step 1: Add contract assertions** for required links/assets, semantic versioning, CI gates, and onboarding stages.
- [ ] **Step 2: Run focused tests** and confirm they fail until the handbook content exists.
- [ ] **Step 3: Add contribution/release/federation/traceability sections** with direct links to authoritative files and tests.
- [ ] **Step 4: Run link checks, full tests, lint, semantic validation, golden evaluation, and demo.**
- [ ] **Step 5: Commit and push** with `docs: complete repository handbook and extension guide`.

### Task 5: Independent documentation review and final verification

**Files:**
- Modify: `README.md` only if review identifies an accuracy issue.
- Test: All documentation, unit, semantic, integration, and golden tests.

**Interfaces:**
- Consumes: All preceding README commits and verification evidence.
- Produces: Clean final branch with current remote, evidence-backed completion report, and no unsupported claims.

- [ ] **Step 1: Dispatch an independent read-only reviewer** to check claims, links, commands, API routes, and production boundaries.
- [ ] **Step 2: Resolve review findings with focused edits/tests.**
- [ ] **Step 3: Run the complete verification matrix from a clean-ish environment.**
- [ ] **Step 4: Commit any final correction and push.**
- [ ] **Step 5: Report repository URL, commits, exact commands, evidence, and limitations.**
