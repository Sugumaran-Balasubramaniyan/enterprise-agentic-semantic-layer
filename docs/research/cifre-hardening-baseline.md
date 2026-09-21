# CIFRE research-prototype hardening: historical baseline

**Recorded:** 2026-09-19 (UTC)
**Execution baseline (branch start):** `2bd69ee7ffa1adbd9d16ce070a8fe461b8f21f95`
**Approved specification milestone:** `f8b720e` (historical specification milestone only; it is **not** the execution HEAD)
**Branch:** `feat/cifre-research-hardening`
**Status:** Read-only historical evidence captured before hardening. No value in this record is post-change evidence, a current benchmark result, or an authorization/ownership claim.

This inventory records what the branch-start checkout contained so later tasks
can distinguish preserved input from newly generated evidence. It describes an
independent synthetic research prototype; the SAP-shaped names below are
fixtures and source-language observations, not official SAP assets.

## Commands and outcomes

Commands were run from the repository root with the checkout's `.venv` (a
symlink to the parent environment) and `PYTHONPATH=src` where Python modules
are involved.

| Command | Branch-start outcome |
| --- | --- |
| `git rev-parse HEAD` | `2bd69ee7ffa1adbd9d16ce070a8fe461b8f21f95` |
| `PYTHONPATH=src .venv/bin/pytest -q` | **218 collected; 217 passed; 1 failed; 2 deprecation warnings.** The pre-existing failure is `tests/unit/test_documentation_contract.py::test_repository_markdown_excludes_legacy_demo_script_language`: the approved spec and plan quote legacy `interview` wording and the documentation control scans them. This control-document drift is retained as baseline evidence and is not hidden. |
| `PYTHONPATH=src .venv/bin/ruff check .` | `All checks passed!` |
| `PYTHONPATH=src make PYTHON=.venv/bin/python validate-semantic` | Vocabulary: 14 concepts loaded. `sample-graph-valid.ttl: CONFORMS (conforms)`. `sample-graph-invalid.ttl: DOES NOT CONFORM (fails expected)`. The negative fixture reports the expected missing posting date and negative amount violations. |
| `PYTHONPATH=src .venv/bin/python -m semantic_layer.research` | Completed and printed the legacy SAP-KGBench table below. This output is historical runner output only and must not be reused as a post-change result. |

The focused Task 1 test was intentionally added after the branch-start
baseline. Before this inventory existed it failed with `FileNotFoundError` at
`docs/research/cifre-hardening-baseline.md`; after this file was created it
passed. The post-addition full suite therefore includes that focused test in
addition to the one pre-existing documentation drift failure.

## Current paths and corpus identity

- Research runner: `src/semantic_layer/research/benchmark_runner.py`.
- Runner entry point: `src/semantic_layer/research/__main__.py`.
- Historical corpus: `tests/research/benchmark_dataset.yaml` (the later plan
  preserves this file as historical input; it is not silently rewritten).
- Historical corpus metadata declares `SAP-KGBench`, version `1.0.0`, and
  `total_queries: 40`.
- Related semantic fixtures: `semantic/ontology/`, `semantic/data/`,
  `semantic/shapes/`, and `semantic/taxonomy/`.
- Existing verification narrative: `docs/verification-report.md`.

The exact historical query IDs are:

`Q01`, `Q02`, `Q03`, `Q04`, `Q05`, `Q06`, `Q07`, `Q08`, `Q09`, `Q10`,
`Q11`, `Q12`, `Q13`, `Q14`, `Q15`, `Q16`, `Q17`, `Q18`, `Q19`, `Q20`,
`Q21`, `Q22`, `Q23`, `Q24`, `Q25`, `Q26`, `Q27`, `Q28`, `Q29`, `Q30`,
`Q31`, `Q32`, `Q33`, `Q34`, `Q35`, `Q36`, `Q37`, `Q38`, `Q39`, `Q40`.

## Three current runner branches

The current `BenchmarkRunner` reports three branches. They are implementation
observations, not validated comparative systems:

1. **Vector RAG** (`Naive Vector RAG`): a hard-coded tier/query-text
   conditional in `benchmark_runner.py`; there is no chunk store, embedding
   model, vector index, or retrieval execution. Its historical output labels
   include `VSR`, `Hallucination (%)`, and fabricated tier scores.
2. **Naive One-Shot Text-to-SPARQL** (`Naive One-Shot Text-to-SPARQL`): the
   same deterministic linker, planner, and compiler with reflection disabled.
   It is not an LLM text-generation experiment.
3. **Agentic AQR** (`Proposed: Agentic AQR (Ours)`): the deterministic
   `AQRReflectiveAgent` with bounded hand-written repair/relaxation heuristics.
   It is not a learned agent and is not evidence of a solved research
   problem.

The historical command printed this exact comparison shape and values:

| Paradigm | Overall EA (%) | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Tier 5 | VSR (%) | Hallucination (%) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `Naive Vector RAG` | 10.0% | 37.5% | 12.5% | 0.0% | 0.0% | 0.0% | 40.0% | 90.0% |
| `Naive One-Shot Text-to-SPARQL` | 80.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% | 0.0% |
| `Proposed: Agentic AQR (Ours)` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% |

These numbers are retained only to identify and remove the old output surface.
They have no defined independent baseline, annotation protocol, exact-set
policy, or reproducible result artifact, and must not be called current
evidence.

## Legacy namespace families

The branch-start checkout contains each of these official-looking or
placeholder namespace families. Every occurrence is a migration target unless
it is quoted in the approved control documents (`f8b720e`'s specification and
plan, plus this historical inventory):

### `http://ontology.sap.com/`

Observed in `semantic/ontology/sap_ppms.ttl`,
`semantic/ontology/sap_support.ttl`, `semantic/shapes/sap_support_shapes.ttl`,
`semantic/data/sap_support_graph.ttl`,
`src/semantic_layer/kg/loader.py`,
`src/semantic_layer/kg/sap_dataset_generator.py`,
`src/semantic_layer/reasoning/text_to_sparql.py`,
`tests/semantic/test_sap_kg.py`, and `tests/unit/test_sap_reasoning.py`.

### `http://data.sap.com/`

Observed in `semantic/data/sap_support_graph.ttl`,
`src/semantic_layer/kg/sap_dataset_generator.py`, and
`tests/semantic/test_sap_kg.py`.

### `https://sap.example/erp/`

Observed in `semantic/ontology/sap_erp.ttl`,
`semantic/ontology/sample-graph-valid.ttl`,
`semantic/ontology/sample-graph-invalid.ttl`,
`semantic/shapes/sap_erp_shapes.ttl`, `semantic/taxonomy/sap_products.ttl`,
`tests/semantic/test_shacl.py`.

### `https://help.sap.com/`

Observed strictly at branch-start in `semantic/data/sap_support_graph.ttl`
and `src/semantic_layer/kg/sap_dataset_generator.py`. This is a separate
official-looking documentation-host namespace. This list is limited to
branch-start runtime/data occurrences; it does not assert that the URI is
absent from normative control documents.

The approved specification and plan also quote the three legacy families above
as control text and quote `help.sap.com` as a forbidden migration/scan term.
Those normative references are control text, not additional branch-start
source occurrences; the documents are evidence about the migration, not source
assets;
their quoted occurrences are intentionally allowlisted for later claim scans.

## Unsupported claim inventory for later tasks

The following are current claim surfaces found by the baseline search. They
are catalogued here so later tasks can replace or label them; this section does
not endorse any of them.

### Ownership, affiliation, official status, and certification

- `README.md` presents a CIFRE PhD showcase at SAP Labs France with academic
  collaborators, calls data products certified, and uses SAP ownership and
  publication language throughout the architecture and operating sections.
- `docs/research/cifre_phd_proposal.md` presents an SAP Labs France host,
  academic affiliations, official support concepts, and empirical conclusions
  without the independent-candidate disclaimer.
- `docs/verification-report.md` describes SAP-oriented benchmark and
  verification outcomes without the final evidence contract.
- `semantic/metrics/metrics.yaml`, `semantic/rules/financial_postings.yaml`,
  `semantic/vocabulary/sap_erp.yaml`, `tests/golden/questions.yaml`, and
  `tests/research/benchmark_dataset.yaml` use `SAP SE` as `owner` or domain
  authority in synthetic assets.
- `src/semantic_layer/__init__.py`, `src/semantic_layer/agents/__init__.py`,
  `src/semantic_layer/kg/__init__.py`, `src/semantic_layer/research/__init__.py`,
  and `src/semantic_layer/demo_sap.py` describe SAP-owned or SAP-branded
  implementation surfaces.
- `data_products/acdoca_financials.yaml`, `billing_analytics.yaml`,
  `business_partners.yaml`, and `sales_orders.yaml` contain owner,
  certification, SLA, or publication wording that is not evidence of an
  external certified product.
- `examples/README.md`, `examples/example_questions.md`,
  `examples/generated_query_plans/primary_erp_plan.json`,
  `examples/generated_sql/README.md`, and the three generated SQL files use
  platform, ownership, or certification language without executed adapters.
- `mappings/databricks/france.yaml`, `mappings/fabric/germany.yaml`, and
  `mappings/snowflake/united_kingdom.yaml` describe illustrative mappings as
  if platform connections or certifications existed.
- `docs/agent-architecture.md`, `docs/architecture.md`,
  `docs/data-products.md`, `docs/federated-semantics.md`,
  `docs/governance.md`, `docs/ontology.md`, `docs/semantic-layer.md`,
  `docs/implementation-plan.md`, `docs/evaluation.md`, and ADR-001 through
  ADR-008 contain ownership, certification, production-readiness, or platform
  claims that must be recast as local behavior or proposed work.

### LLM, neural, vector, hallucination, and benchmark-comparison claims

- `README.md` claims a neurosymbolic/LLM research framework, says it solves
  Vector RAG failure modes, and reports 100.0% AQR, 10.0% Vector RAG, 80.0%
  one-shot, VSR, and zero-hallucination comparisons.
- `docs/research/cifre_phd_proposal.md` describes LLM-powered AQR-Reflect,
  Vector RAG failures, and the same unsupported empirical superiority.
- `src/semantic_layer/demo_sap.py:88` prints the explicit result claim
  `100% GROUNDED RETRIEVAL (0% HALLUCINATION)` despite the deterministic,
  synthetic demo path and no groundedness annotation protocol.
- `docs/verification-report.md:17` reports the explicit benchmark claim
  `100.0% Execution Accuracy (40/40), 0.0% Hallucination`; this is historical
  documentation text, not an independently reproduced result artifact.
- `src/semantic_layer/research/benchmark_runner.py` exposes the fake Vector
  RAG branch, `hallucinated_queries`, VSR, and comparative output fields.
- `tests/research/benchmark_dataset.yaml` and its comments call the corpus
  `SAP-KGBench` and frame it as an enterprise-support Text-to-SPARQL benchmark
  without a controlled learned-baseline protocol.
- `src/semantic_layer/reasoning/` and `src/semantic_layer/research/` contain
  AQR/LLM/vector wording that must be reconciled with the deterministic
  implementation by their owning later tasks, not silently edited here.
- `docs/architecture.md`, `docs/agent-architecture.md`, `docs/evaluation.md`,
  and related ADRs describe optional LLM enhancement or vector/cloud paths;
  current code has no LLM call, embedding model, vector index, vector
  retriever, hosted model, or neural baseline.

### Production, cloud, hosted-service, and deployment claims

- `README.md` calls the framework production-grade or production-tested and
  contains production deployment, operating-model, certification, cloud
  adapter, KMS, identity, and rollout language. Those sections describe
  future posture, not executed evidence.
- `docs/agent-architecture.md`, `docs/architecture.md`,
  `docs/data-products.md`, `docs/federated-semantics.md`,
  `docs/governance.md`, `docs/implementation-plan.md`, and ADR-001 through
  ADR-008 describe production or cloud integrations that are not executed in
  this checkout.
- `src/semantic_layer/adapters/`, `src/semantic_layer/api/`,
  `src/semantic_layer/compiler/`, `src/semantic_layer/control.py`,
  `src/semantic_layer/governance/`, `src/semantic_layer/lineage/`,
  `src/semantic_layer/provenance/`, `src/semantic_layer/quality/`,
  `src/semantic_layer/registry/`, and `src/semantic_layer/resolver/` contain
  production/platform/certification wording around local demo behavior.
- The example SQL, mapping, and data-product files listed above are
  unexecuted simulations or synthetic contracts, not cloud connections,
  production data, or certified products.

### Claim-scan scope and ownership boundaries

Tasks 3–8 own the semantic assets, reasoning, result lifecycle, corpus, and
runner files. Task 10 owns non-publication source/examples/mappings/data
products and must scan (rather than concurrently edit) AQR files owned by
Tasks 3–8. Task 11 owns README, package metadata, architecture/docs, and ADRs.
Task 12 owns the proposal, interview brief, verification report, and this
historical baseline only for a final pointer. Task 13 owns final artifact and
claim/secret/format gates. This inventory is the handoff boundary; no later
task may treat the historical runner table or baseline counts as changed-state
evidence.

The exact non-publication claim-scan surface is the following: `src/semantic_layer/__init__.py`,
`src/semantic_layer/adapters/__init__.py`, `src/semantic_layer/adapters/cloud.py`,
`src/semantic_layer/adapters/duckdb.py`, `src/semantic_layer/agents/__init__.py`,
`src/semantic_layer/agents/workflow.py`, `src/semantic_layer/api/__init__.py`,
`src/semantic_layer/api/app.py`, `src/semantic_layer/compiler/__init__.py`,
`src/semantic_layer/compiler/base.py`, `src/semantic_layer/compiler/cloud_examples.py`,
`src/semantic_layer/compiler/duckdb.py`, `src/semantic_layer/control.py`,
`src/semantic_layer/data_generation.py`, `src/semantic_layer/demo.py`,
`src/semantic_layer/demo_sap.py`, `src/semantic_layer/governance/__init__.py`,
`src/semantic_layer/governance/policy.py`, `src/semantic_layer/kg/__init__.py`,
`src/semantic_layer/kg/loader.py`, `src/semantic_layer/kg/sap_dataset_generator.py`,
`src/semantic_layer/lineage/__init__.py`, `src/semantic_layer/lineage/service.py`,
`src/semantic_layer/models.py`, `src/semantic_layer/provenance/__init__.py`,
`src/semantic_layer/provenance/store.py`, `src/semantic_layer/quality/__init__.py`,
`src/semantic_layer/quality/checks.py`, `src/semantic_layer/query_planner/__init__.py`,
`src/semantic_layer/query_planner/service.py`, `src/semantic_layer/registry/__init__.py`,
`src/semantic_layer/registry/service.py`, `src/semantic_layer/research/__init__.py`,
`src/semantic_layer/research/benchmark_runner.py`, `src/semantic_layer/resolver/__init__.py`,
`src/semantic_layer/resolver/service.py`, and `src/semantic_layer/reasoning/text_to_sparql.py`.
The same scan covers `examples/README.md`, `examples/example_questions.md`,
`examples/generated_query_plans/primary_erp_plan.json`,
`examples/generated_sql/README.md`, `examples/generated_sql/databricks.sql`,
`examples/generated_sql/microsoft-fabric.sql`, `examples/generated_sql/snowflake.sql`,
`mappings/databricks/france.yaml`, `mappings/fabric/germany.yaml`,
`mappings/snowflake/united_kingdom.yaml`, and all four `data_products/*.yaml`
contracts. Task 10 must retain structure while replacing unsupported platform,
ownership, certification, production, and namespace wording in this list.

The exact publication claim-scan surface is `README.md`, `pyproject.toml`,
`docs/agent-architecture.md`, `docs/architecture.md`, `docs/data-products.md`,
`docs/evaluation.md`, `docs/federated-semantics.md`, `docs/governance.md`,
`docs/implementation-plan.md`, `docs/ontology.md`, `docs/semantic-layer.md`,
and `docs/decisions/ADR-001-canonical-group-model.md` through
`docs/decisions/ADR-008-certified-data-products.md`. Task 11 must remove or
label claims containing **production-grade**, **production-tested**, **certified
data product**, **SAP Labs/academic affiliation**, **official/publication or
endorsement**, **Vector RAG**, **hallucination guarantee**, **benchmark
superiority**, **cloud/hosted endpoint**, and **LLM integration** unless the
claim is explicitly a future proposal backed by an executable check.

Task 12's handoff surfaces are `docs/research/cifre_phd_proposal.md`,
`docs/verification-report.md`, `docs/research/cifre-interview-brief.md`, and
`docs/research/technical_design_and_research_questions.md` (the latter two do
not yet exist at this baseline). They must preserve this record's historical
status while removing solved-PhD, affiliation, official SAP, production,
zero-hallucination, fake-vector, and invented-final-metric language.

## Review concerns

- This record contains no credentials, tokens, private keys, or mutable
  external-system claims.
- The three legacy namespace strings and historical benchmark labels are
  intentionally present so migration and claim-scan tests can prove they were
  addressed. The approved spec and plan are separate control documents and
  remain the explicit legacy-URI allowlist.
- The one baseline pytest failure is documentation-control drift caused by
  quoted plan/spec language. It is pre-existing at execution baseline and is
  recorded for the later documentation repair task.
- No implementation, benchmark corpus, semantic asset, remote, or deployment
  state was changed by this baseline capture.

## Final handoff pointer (appended by Task 12)

The historical evidence above is unchanged. The current research handoff is
now documented in the [proposal](cifre_phd_proposal.md),
[technical design and research questions](technical_design_and_research_questions.md),
[interview brief](cifre-interview-brief.md), and
[verification report](../verification-report.md). Task 13 owns the final
`results/latest_benchmark.json` artifact, exact commit and SHA-256 manifest,
and final `make PYTHON=.venv/bin/python research-verify` result.
