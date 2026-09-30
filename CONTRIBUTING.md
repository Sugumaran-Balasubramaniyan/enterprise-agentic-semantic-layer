# Contributing to Enterprise Agentic Semantic Layer (EASL)

Thank you for your interest in contributing to the **Enterprise Agentic Semantic Layer (EASL)**! This project provides zero-trust semantic governance and neurosymbolic reasoning for AI agents interacting with enterprise data products and knowledge graphs.

---

## Code of Conduct

All contributors and maintainers are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior to the project maintainers.

---

## Development Setup

### Prerequisites

- Python 3.12+
- `git`
- `make`

### Installation

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/Sugumaran-Balasubramaniyan/enterprise-agentic-semantic-layer.git
   cd enterprise-agentic-semantic-layer
   ```

2. Create and activate a virtual environment:
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

3. Install pinned dependencies:
   ```bash
   make setup
   # Or install editable directly:
   pip install -e ".[dev]"
   ```

4. Verify your setup:
   ```bash
   make test
   make lint
   ```

---

## Architecture Overview

EASL enforces a fail-closed, multi-stage semantic pipeline:

```
[ Natural Language Query ]
            │
            ▼
[ Deterministic Resolver ] ─── Grounding against governed canonical vocabulary
            │
            ▼
[ Query Planner ] ──────────── Synthesizes typed SemanticQueryPlan (no SQL)
            │
            ▼
[ Governance Policy ] ──────── Evaluates Role-Based Access Control (RBAC) & market scope
            │
            ▼
[ Zero-SQL Security ] ──────── SqlFreeSemanticModel recursively purges SQL tokens & CTEs
            │
            ▼
[ Execution Compiler ] ─────── Compiles plan into parameterized DuckDB / SQLite SQL
            │
            ▼
[ Execution Adapter ] ──────── Runs query with input data digests and finite value checks
            │
            ▼
[ Provenance Envelope ] ────── HMAC-SHA256 signs query, plan, authorization, and data digests
```

---

## How to Contribute

### 1. Adding a New Data Product

1. Create a declarative YAML contract in `data_products/<product_name>.yaml`:
   ```yaml
   id: YourDataProduct
   description: Domain data product description
   grain: one row per entity
   classification: Confidential
   upstream_sources:
     - your_source_table
   semantic_concepts:
     - ciferp:YourEntity
   ```
2. Register associated metrics in `semantic/metrics/metrics.yaml`.
3. Validate your additions:
   ```bash
   easl validate
   ```

### 2. Adding a New Database Adapter

1. Implement your adapter under `src/semantic_layer/adapters/<adapter_name>.py`.
2. Follow the security and finite-value contract pattern demonstrated in `src/semantic_layer/adapters/sqlite.py` and `duckdb.py`.
3. Add unit tests in `tests/unit/test_<adapter_name>_adapter.py`.

---

## Testing & Verification Gates

Before submitting a pull request, ensure all verification gates pass:

```bash
# 1. Run full test suite
make test

# 2. Check code style and formatting
make lint

# 3. Verify YAML syntax
make check-yaml

# 4. Run reproducibility and research verification
make research-verify
```

---

## Pull Request Guidelines

1. Create a focused topic branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Commit with descriptive, conventional commit messages (`feat: ...`, `fix: ...`, `docs: ...`, `test: ...`).
3. Ensure all tests and lint checks pass locally.
4. Open a pull request against the `main` branch using our pull request template.
