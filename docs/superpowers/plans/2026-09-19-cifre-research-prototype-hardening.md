# CIFRE Research Prototype Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task. Each task ends at an independently reviewable commit; every implementation step is TDD and uses checkbox syntax.

**Goal:** Turn the synthetic Support/PPMS AQR path into a neutral-namespace, fail-closed, deterministic research prototype whose benchmark, graph, result artifact, documentation, and verification command are reproducible from a clean checkout.

**Architecture:** A closed namespace/provenance registry and typed research contracts feed deterministic grammar grounding, typed logical planning, bounded SPARQL compilation/execution, and an explicit status/repair state machine. A versioned v1/v2 synthetic corpus is scored with status-gated exact-set metrics into a canonical hashed JSON artifact; one locked `research-verify` target validates assets, SHACL scopes, graph parity, benchmarks, claims, tests, and lint.

**Tech Stack:** Python 3.12; RDFLib; pySHACL; Pydantic; PyYAML; pytest; Ruff; JSON Schema draft 2020-12; Make; GitHub Actions; DuckDB/FastAPI remain supported secondary-path dependencies.

**Spec:** [`docs/superpowers/specs/2026-09-19-cifre-research-prototype-hardening-design.md`](../specs/2026-09-19-cifre-research-prototype-hardening-design.md)

## Global Constraints

- Use only the exact neutral IRIs `https://example.org/cifre-kg/support#`, `https://example.org/cifre-kg/ppms#`, `https://example.org/cifre-kg/data/`, `https://example.org/cifre-kg/erp#`, `https://example.org/cifre-kg/vocabulary#`, `https://example.org/cifre-kg/meta#`, and `https://example.org/cifre-kg/id/meta/` for synthetic domain resources; no aliases, dual emission, `owl:sameAs`, or legacy parser.
- Keep the current implementation model-free: no LLM, embedding/vector package, vector service, cloud endpoint, API key, model download, production integration, or official/affiliation/endorsement claim.
- Install exactly with Python 3.12, `pip==25.2`, `pip install --require-hashes --constraint constraints/py312.txt -e '.[dev]'`; update the lock and its hash in the same commit as dependency changes.
- Use English `rdf:langString` plus `sh:datatype rdf:langString`/`sh:languageIn ("en")` for human-readable synthetic labels; identifiers, codes, statuses, and numeric bounds retain their declared machine datatypes.
- Keep ERP OWL classes under `ciferp:` and SKOS concepts under `cifskos:`; a reviewed `cifmeta:CrosswalkEntry` is the only class-to-concept crosswalk and never an implicit type assertion.
- Compile prerequisite closure with a bounded union of `cifsup:hasPrerequisiteNote` paths of lengths 1 through `MAX_PREREQUISITE_DEPTH = 16`, excluding the target and reporting `PREREQUISITE_DEPTH_EXCEEDED` at hop 17.
- The closed final statuses are `SUCCESS`, `UNSUPPORTED`, `SYNTAX_ERROR`, `EXECUTION_ERROR`, and `EMPTY_RESULT`; `max_repairs` is exactly `3`, with attempts `0` for abstention, `1` initially, and at most `4` including repairs.
- Strict answer metrics use exact set equality only when expected and observed status are both `SUCCESS` and status-correct; relaxed candidates never contribute to strict predicted sets.
- v1 is exactly Q01-Q40 in `cifre-synthetic-aqr-v1`; v2 is exactly Q01-Q52 in `cifre-synthetic-aqr-v2`; legacy `tests/research/benchmark_dataset.yaml` remains historical input and is never evaluated.
- `results/latest_benchmark.json` is canonical UTF-8, lexicographically keyed, six-decimal `Decimal` metrics, no timestamp in hashed content, and contains exactly v1/v2 corpus runs and the two measured conditions.
- `make PYTHON=.venv/bin/python research-verify` must generate temporary assets, check graph isomorphism, run all five validation-matrix checks, run both corpora/conditions, validate JSON/claims, run pytest and Ruff, and fail non-zero on drift or stale hashes.
- Implementers use `apply_patch`, preserve unrelated work, commit only their task files, and do not push or mutate GitHub metadata/remotes/releases/topics.

## Review Focus

- Unknown, ambiguous, unsupported, and uncued tokens must abstain before planning with no invented URI or query; pinned by Task 4 `test_grounding_rejects_unknown_ambiguous_and_unsupported_inputs_before_planning`.
- A strict empty result with a successful relaxed candidate must remain `EMPTY_RESULT` and disclose the ordered relaxation ledger; pinned by Task 6 `test_relaxed_candidates_never_become_strict_success`.
- A transitive prerequisite cycle and depth-17 chain must terminate deterministically, exclude the target, and emit the exact cycle/depth evidence; pinned by Task 5 `test_prerequisite_cycle_and_depth_contract`.
- A stale or mutated input must invalidate the result artifact through the full manifest rather than silently reuse checked-in numbers; pinned by Task 8 `test_result_hash_manifest_rejects_mutated_input`.
- Public claims and links must expose the independent synthetic boundary and executable verification path, while retaining the federated layer as secondary; pinned by Task 11 `test_publication_claim_contract_and_links`.

## Dependency Graph and Safe Luna Waves

Tasks own the files listed below exclusively. A reviewer runs the task’s focused command and full relevant regression command before the next dependent wave. No two agents edit a shared file in the same wave.

```text
T1 baseline inventory
  -> T2 lock + canonical contracts/provenance/schema
       -> T3 neutral namespaces/assets/SHACL fixtures  -┐
       -> T4 grammar/grounding/status contracts ---------┼-> T5 planner/SPARQL/closure/projections
                                                         └-> T6 repair state machine/answers
T5 + T6 -> T7 corpus migration/v1-v2 negatives -> T8 benchmark/metrics/result artifact
T3 + T8 -> T9 reproducibility target/validation matrix/CI
T8 + T9 -> T10 README/package/claim sanitation + federated-secondary positioning
T10 -> T11 proposal/interview brief/verification report/documentation tests
T11 -> T12 final audit and release-readiness verification
```

Safe waves are: Wave 0 `{T1}`; Wave 1 `{T2}`; Wave 2 `{T3, T4}`; Wave 3 `{T5}`; Wave 4 `{T6}`; Wave 5 `{T7}`; Wave 6 `{T8}`; Wave 7 `{T9}`; Wave 8 `{T10}`; Wave 9 `{T11}`; Wave 10 `{T12}`. T3 and T4 may run concurrently only because their implementation files and focused tests are disjoint; all other waves are serialized where a shared contract or file is consumed.

### Task 1: Freeze baseline evidence and claim inventory

**Files:**
- Create: `docs/research/cifre-hardening-baseline.md`
- Test: `tests/unit/test_project_contract.py` (new baseline-inventory assertions only)

**Interfaces:**
- Consumes: HEAD `f8b720e`, current `Makefile` targets, `src/semantic_layer/reasoning/*`, `src/semantic_layer/research/benchmark_runner.py`, tracked semantic assets, and current claim-bearing files.
- Produces: a checked-in, read-only baseline record naming the commit, commands, current test/lint/semantic outcomes, 40 IDs, three current runner branches, every legacy namespace family, and every unsupported ownership/LLM/vector/production claim targeted by later tasks. No implementation task may treat historical counts as post-change evidence.

- [ ] **Step 1: Write the failing inventory test.** Add `test_baseline_inventory_names_current_evidence()` that reads the baseline document and asserts it contains `f8b720e`, `benchmark_dataset.yaml`, `Vector RAG`, `Naive One-Shot Text-to-SPARQL`, `Agentic AQR`, all strings `Q01` through `Q40`, and each forbidden family `http://ontology.sap.com/`, `http://data.sap.com/`, and `https://sap.example/erp/`.
- [ ] **Step 2: Run the focused test to verify it fails.** Run `pytest tests/unit/test_project_contract.py::test_baseline_inventory_names_current_evidence -q`; expected: `FileNotFoundError` or assertion failure because the inventory file does not exist.
- [ ] **Step 3: Capture the baseline.** Run `git rev-parse HEAD`, `pytest -q`, `ruff check .`, `make validate-semantic`, and `PYTHONPATH=src python -m semantic_layer.research`; record exact output summaries, date, command lines, current paths, and claim/namespace search results in `docs/research/cifre-hardening-baseline.md`. Do not edit implementation or reinterpret historical benchmark values.
- [ ] **Step 4: Make the test pass and verify.** Run the focused test, then `pytest tests/unit/test_project_contract.py -q`; expected: PASS, with the document explicitly labelled historical baseline.
- [ ] **Step 5: Commit and review.** `git add docs/research/cifre-hardening-baseline.md tests/unit/test_project_contract.py && git commit -m "docs: record CIFRE hardening baseline"`. A fresh reviewer checks the inventory is complete and contains no credentials or mutable claims; review is a gate, not an implementation step.

### Task 2: Lock dependencies and establish canonical research contracts

**Files:**
- Create: `constraints/py312.txt`, `semantic/provenance/synthetic_source.yaml`, `src/semantic_layer/research/contracts.py`, `tests/research/result_schema.json`
- Modify: `pyproject.toml:12-15` to add the pinned JSON Schema validator used by the authoritative artifact contract
- Test: `tests/research/test_contracts.py`

**Interfaces:**
- Consumes: the seven neutral namespace IRIs and provenance fields in Spec §§5.1, 20, and 21.
- Produces: `NAMESPACE_REGISTRY: Mapping[str, str]`; `Status` enum; `ReasonCode` enum including `AMBIGUOUS_INPUT`, `NO_OP_REPAIR`, and `PREREQUISITE_DEPTH_EXCEEDED`; `CONDITIONS = ("deterministic_no_reflection_ablation", "deterministic_bounded_repair")`; `canonical_json(value: object) -> bytes`; `sha256_bytes(data: bytes) -> str`; `load_and_validate_result(path: Path) -> dict[str, Any]`; and the authoritative root JSON Schema `$id` `https://example.org/cifre-kg/schema/research-result-root-1.0.0.json`.

- [ ] **Step 1: Write failing contract tests.** In `tests/research/test_contracts.py`, assert the registry equals the exact seven IRI mapping, every status/reason enum value is closed, `canonical_json({"b": 1, "a": 2}) == b'{"a":2,"b":1}'`, provenance has exactly the Spec §20 top-level keys and `official is False`, and a root result with `schema_version != "1.0.0"` is rejected by `load_and_validate_result`.
- [ ] **Step 2: Verify the failures.** Run `pytest tests/research/test_contracts.py -q`; expected: import failure for `semantic_layer.research.contracts`, missing lock/provenance/schema paths, and missing schema validation.
- [ ] **Step 3: Add the schema validator and generate the lock.** Add the reviewed `jsonschema` version to the development dependencies, then in a clean Python 3.12 environment install `pip==25.2`, install `pip-tools==7.4.1`, run `.venv/bin/pip-compile --extra=dev --generate-hashes --output-file=constraints/py312.txt pyproject.toml`, and verify every direct/transitive distribution is pinned with hashes. The plan executor must not upgrade unrelated dependencies.
- [ ] **Step 4: Implement contracts and schema.** Add exact enums, namespace constants, canonical JSON serialization (UTF-8, sorted keys, no insignificant whitespace), SHA-256 helpers, provenance loader, and the complete Spec §26.4 root schema with `additionalProperties: false`, nullable fields, condition/status enums, composite result-ID requirements, metric precision, validation matrix, corpus runs, and per-query definitions.
- [ ] **Step 5: Add provenance and verify.** Write `semantic/provenance/synthetic_source.yaml` with exactly the Spec §20 fields, including `official: false`, `source_kind: synthetic_fixture`, exact generator/graph paths, namespace registry, and forbidden official-label policy. Run `pytest tests/research/test_contracts.py -q` (expected PASS), then `python -m json.tool tests/research/result_schema.json` (expected valid JSON).
- [ ] **Step 6: Commit and review.** `git add constraints/py312.txt semantic/provenance/synthetic_source.yaml src/semantic_layer/research/contracts.py tests/research/result_schema.json tests/research/test_contracts.py && git commit -m "build: lock CIFRE research contracts"`. Review verifies no unpinned dependency, root schema completeness, and exact contract names before T3/T4.

### Task 3: Migrate neutral namespaces and synthetic semantic assets

**Files:**
- Modify: `src/semantic_layer/kg/loader.py:20-120`, `src/semantic_layer/kg/sap_dataset_generator.py:18-end`, all `semantic/ontology/**/*.ttl`, `semantic/data/**/*.ttl`, `semantic/shapes/**/*.ttl`, `semantic/vocabulary/**/*.yaml`, `semantic/taxonomy/**/*.ttl`, `data/**/*.py`, `data_products/**/*.yaml`, and their direct tests in `tests/semantic/test_sap_kg.py`, `tests/semantic/test_shacl.py`, `tests/semantic/test_vocabulary.py`
- Create: `semantic/data/support-graph-invalid.ttl`, `semantic/data/support-prerequisite-cycle.ttl`, `semantic/data/support-prerequisite-depth17.ttl`
- Test: `tests/semantic/test_namespace_contract.py`, `tests/semantic/test_asset_datatypes.py`

**Interfaces:**
- Consumes: `NAMESPACE_REGISTRY` from Task 2 and `SAPKnowledgeGraph`/`build_sap_support_graph` current APIs.
- Produces: `NamespaceRegistry`-backed constants `CIFSUP`, `CIFPPMS`, `CIFDATA`, `CIFERP`, `CIFSKOS`, `CIFMETA`, `CIFMETAID`; `build_sap_support_graph(ontology_paths: list[str | Path] | None = None) -> Graph` emitting only neutral IRIs; `SAPKnowledgeGraph.validate_shacl(shapes_path: str | Path, *, scope: str = "support") -> ValidationReport`; and synthetic metadata/crosswalk triples with disjoint OWL/SKOS resources.

- [ ] **Step 1: Add failing namespace/data tests.** Assert every tracked synthetic RDF/YAML resource IRI is under an approved base, no file except the design spec contains forbidden families, graph metadata has `cifmeta:sourceKind "synthetic_fixture"` and `cifmeta:official false`, human labels are English `rdf:langString`, and `cifskos:ProductAutomotive` is a `skos:Concept` but not an OWL class/type.
- [ ] **Step 2: Verify failure before migration.** Run `pytest tests/semantic/test_namespace_contract.py tests/semantic/test_asset_datatypes.py -q`; expected: failures for old namespace bindings/IRIs, absent provenance, old `sh:or` datatype workaround, and SKOS/OWL collisions.
- [ ] **Step 3: Migrate constants and fixtures in one clean break.** Replace `PPMS`/`SAP` with the neutral registry; map instance bases exactly to `data/support`, `data/ppms`, `data/erp`; remove `help.sap.com`; split ERP OWL `ciferp:` from SKOS `cifskos:`; add `cifmetaid:crosswalk-entry-product-automotive` with the exact `CrosswalkEntry` shape; update all direct consumers/tests/examples/docs generated semantic IDs. Do not add aliases.
- [ ] **Step 4: Correct semantic asset datatypes and negative fixtures.** Change human-readable ranges/shapes to `rdf:langString` with `sh:languageIn ("en")`, keep machine fields `xsd:string`/numeric, add the invalid support graph with provenance, and add exact A→B→C→A and N0→…→N17 fixtures.
- [ ] **Step 5: Regenerate and test.** Generate the checked-in support graph with `PYTHONPATH=src .venv/bin/python -m semantic_layer.kg.sap_dataset_generator`, parse every changed RDF/YAML asset, run focused namespace/datatype tests (expected PASS), then `pytest tests/semantic -q` (expected no namespace/asset regressions).
- [ ] **Step 6: Commit and review.** `git add semantic src/semantic_layer/kg data data_products tests/semantic && git commit -m "refactor: migrate CIFRE synthetic namespaces"`. Review scans for aliases, official-looking IRIs, missing provenance, and shared files before accepting T3.

### Task 4: Implement deterministic grammar grounding and fail-closed result types

**Files:**
- Modify: `src/semantic_layer/reasoning/schema_linker.py:14-145`
- Create: `tests/research/grounding_grammar.yaml`, `tests/research/test_grounding_contract.py`
- Test: `tests/unit/test_sap_reasoning.py` (replace regex-intent expectations with grammar/status expectations)

**Interfaces:**
- Consumes: neutral vocabulary constants from Task 3 and `Status`/`ReasonCode` from Task 2.
- Produces: `GroundedEntities` fields `raw_query`, `normalized_request`, `intent`, `failure_class`, `component_codes`, `alert_codes`, `product_versions`, `software_components`, `support_packages`, `note_numbers`, `priorities`; `SchemaLinker.ground(query_text: str) -> GroundedEntities`; and `SchemaLinker.ground_or_abstain(query_text: str) -> GroundedEntities` that raises no exception and returns `failure_class` for rejected grammar.

- [ ] **Step 1: Write failing grammar tests.** Add `test_grounding_rejects_unknown_ambiguous_and_unsupported_inputs_before_planning`; load the exact filler/templates from Spec §16 and test the 12 listed accepted/rejected fixtures plus v2 Q41-Q52 classification: `UNKNOWN_TOKEN`, `UNKNOWN_ENTITY`, `AMBIGUOUS_INPUT`, `UNSUPPORTED_INTENT`, and valid numeric `SP99`. Assert rejected results have no planner/compiler call opportunity and preserve canonical entity spellings.
- [ ] **Step 2: Verify failure.** Run `pytest tests/research/test_grounding_contract.py tests/unit/test_sap_reasoning.py -q`; expected: missing grammar file and failures because current regex extraction accepts uncued words, aliases intents, and has no failure class.
- [ ] **Step 3: Implement the finite parser.** Add grammar YAML schema version `1.0`; tokenize Unicode whitespace/case-folded text while preserving `raw_query`; classify cue-selected slots before intent precedence; reject unknown tokens, conflicting markers, optional-slot misuse, two distinct family values, and unsupported markers; accept only the exact `NOTE_LOOKUP`, `ALERT_RESOLUTION`, `COMPONENT_SEARCH`, `VERSION_FILTERED_SEARCH`, `PREREQUISITE_CLOSURE`, and `GENERAL_SEARCH` rules.
- [ ] **Step 4: Verify accepted/rejected behavior.** Run the focused tests (expected PASS), then `pytest tests/unit/test_sap_reasoning.py -q`; expected PASS with no old `RESOLVE_ALERT`/`PREREQUISITE_CHAIN` assumptions remaining.
- [ ] **Step 5: Commit and review.** `git add src/semantic_layer/reasoning/schema_linker.py tests/research/grounding_grammar.yaml tests/research/test_grounding_contract.py tests/unit/test_sap_reasoning.py && git commit -m "feat: add closed CIFRE grounding grammar"`. Review checks exact token sets, precedence, SP99 policy, and no regex fallback.

### Task 5: Correct planner, bounded prerequisite closure, and projection-safe SPARQL

**Files:**
- Modify: `src/semantic_layer/reasoning/query_planner.py:14-115`, `src/semantic_layer/reasoning/text_to_sparql.py:13-51`
- Test: `tests/unit/test_query_planner.py`, `tests/unit/test_sap_reasoning.py`, `tests/semantic/test_sap_kg.py`

**Interfaces:**
- Consumes: Task 3 namespace registry and Task 4 `GroundedEntities` intent/slots.
- Produces: `TraversalPattern(subject: str, predicate: str, object_val: str, optional: bool = False)`; `LogicalQueryPlan(target_var: str, intent: str, select_vars: list[str], patterns: list[TraversalPattern], filters: list[str], optional_patterns: list[TraversalPattern], required_variables: list[str], optional_variables: list[str], order_by: str | None, limit: int)`; `QueryPlanner.plan(entities: GroundedEntities) -> LogicalQueryPlan`; `TextToSPARQLEngine.compile(plan: LogicalQueryPlan) -> str`; and `TextToSPARQLEngine.validate_projections(plan) -> None` raising `ValueError`/`UNBOUND_REQUIRED_PROJECTION` before compilation.

- [ ] **Step 1: Write failing planner/compiler tests.** Add `test_prerequisite_cycle_and_depth_contract`; assert prerequisite plans select only `?note`, `?noteNumber`, `?title`, every selected variable has a required/optional pattern, the bounded union contains path lengths 1–16 and no unbounded `+`, combined alert+component+version anchors correctly, support-package filters are numeric, and optional variables are emitted only in `OPTIONAL` blocks.
- [ ] **Step 2: Verify failures.** Run `pytest tests/unit/test_query_planner.py tests/unit/test_sap_reasoning.py -q`; expected: current `?prereqTitle` projection and old predicates/prefixes fail.
- [ ] **Step 3: Implement minimal typed planning.** Emit neutral `cifsup`/`cifppms` predicates; use exact `PREREQUISITE_CLOSURE`; generate a deterministic union of 1..16 `hasPrerequisiteNote` hops with target exclusion and a depth marker; maintain sorted required/optional projection lists; reject any unbound required projection.
- [ ] **Step 4: Implement compiler validation and deterministic ordering.** Emit `PREFIX cifsup`, `PREFIX cifppms`, `PREFIX cifdata`, `PREFIX xsd`, and standard W3C prefixes; render required patterns, `OPTIONAL` patterns, filters, `ORDER BY`, and `LIMIT` deterministically; reject selected variables with no pattern.
- [ ] **Step 5: Verify closure and parity behavior.** Run focused planner/compiler tests (expected PASS), then `pytest tests/semantic/test_sap_kg.py tests/unit/test_query_planner.py -q`; expected PASS, including no target note, deduplication, cycle termination, and depth-17 `EMPTY_RESULT` contract.
- [ ] **Step 6: Commit and review.** `git add src/semantic_layer/reasoning/query_planner.py src/semantic_layer/reasoning/text_to_sparql.py tests/unit/test_query_planner.py tests/unit/test_sap_reasoning.py tests/semantic/test_sap_kg.py && git commit -m "fix: make CIFRE plans projection safe"`. Reviewer checks each projected variable is bound and no old namespace/predicate survives.

### Task 6: Add typed AQR statuses, bounded repair state machine, and provenance answers

**Files:**
- Modify: `src/semantic_layer/reasoning/reflective_agent.py:26-231`, `src/semantic_layer/agents/tools.py` and any CLI integration that serializes `ReasoningResult`
- Create: `tests/research/test_failure_state_machine.py`, `tests/research/test_answer_provenance.py`

**Interfaces:**
- Consumes: Task 2 `Status`/`ReasonCode`; Task 4 fail-closed grounding; Task 5 typed plans/compiler.
- Produces: `ReasoningResult` with `normalized_request`, `grounding`, `plan`, `sparql_initial`, `sparql_final`, `status: Status`, `reason_code: ReasonCode`, `attempts: int`, `repair: RepairLedger`, `relaxation: RelaxationDisclosure`, `answer_scope: Literal["strict", "relaxed_candidates", "none"]`, `relaxed_candidates`, `bindings`, `predicted_note_numbers`, `provenance`; `AQRReflectiveAgent.run(query_text: str, condition: str = "deterministic_bounded_repair", max_repairs: int = 3) -> ReasoningResult`; `RepairOperation` with the exact Spec §18.2 fields; and `sanitize_diagnostic(text: str, limit: int = 512) -> str`.

- [ ] **Step 1: Write failing state-machine tests.** Use a fake KG that returns bindings, empty rows, fixed syntax exceptions, and fixed execution exceptions. Assert initial index 0, max three repairs, attempts 0/1–4, exact status/reason pairs, append-only operation ledger, no-op detection, sanitized diagnostics, and no-reflection never entering repair.
- [ ] **Step 2: Pin the critical relaxation test.** In `test_relaxed_candidates_never_become_strict_success`, return no rows for strict SP/component constraints and rows after removing the support-package bound; assert `status is EMPTY_RESULT`, `reason_code is RELAX_SUPPORT_PACKAGE`, `answer_scope == "relaxed_candidates"`, strict `predicted_note_numbers == []`, and operation order remove-package then widen-component.
- [ ] **Step 3: Verify failures.** Run `pytest tests/research/test_failure_state_machine.py tests/research/test_answer_provenance.py -q`; expected: current agent returns string status, marks relaxation as recovery, has no closed reason code, and emits SAP-labelled citations.
- [ ] **Step 4: Implement the closed lifecycle.** Abstain before planning for unsupported grounding; map syntax/execution/empty events to the exact state table in Spec §26.5; record full attempted SPARQL text plus hashes; enforce `max_repairs == 3`; retain original constraints and strict status while exposing relaxed candidates separately.
- [ ] **Step 5: Implement binding-derived answers and provenance.** Build answer lines only from final strict bindings; use citation prefix `Synthetic fixture cifre-synthetic-support-ppms-v1; not official data.`; return no factual answer for unsupported/errors; sort bindings and nullable optional fields deterministically.
- [ ] **Step 6: Verify and commit.** Run focused tests (expected PASS), then `pytest tests/unit tests/integration -q`; commit with `git add src/semantic_layer/reasoning/reflective_agent.py src/semantic_layer/agents/tools.py tests/research/test_failure_state_machine.py tests/research/test_answer_provenance.py && git commit -m "feat: harden CIFRE AQR result lifecycle"`. Review checks state transitions, status/reason legality, and credential-safe diagnostics.

### Task 7: Normalize historical corpus, migration manifest, and v2 negatives

**Files:**
- Create: `scripts/migrate_benchmark_v1.py`, `tests/research/benchmark_dataset_legacy.yaml`, `tests/research/benchmark_dataset_v1.yaml`, `tests/research/benchmark_dataset_v2.yaml`, `tests/research/benchmark_migration_manifest_v1.yaml`, `tests/research/test_dataset_migration.py`
- Preserve unchanged: `tests/research/benchmark_dataset.yaml`

**Interfaces:**
- Consumes: Task 4 grammar/status reasons, Task 5 closure semantics, Task 6 result status model, and the exact legacy Q01-Q40 file.
- Produces: `migrate_benchmark(source: Path, v1: Path, v2: Path, manifest: Path) -> None`; normalized records with exactly `id, corpus_id, version, tier, category, question, expected_status, gold_note_numbers, reflection_reason, strict_constraints, gold_policy`; v1 IDs Q01–Q40; v2 IDs Q01–Q52; and a signed 40-entry migration manifest.

- [ ] **Step 1: Write failing migration tests.** Assert legacy archival is byte-identical, normalized v1 has 40 exact IDs/no `expected_notes`, v2 has the exact Q41–Q52 category/status/reason/question table, Q25/Q28/Q31 expand to `["3012445", "3098110"]`, Q33–Q40 become strict `EMPTY_RESULT`, and manifest records have all before/after/policy/derivation/sign-off fields.
- [ ] **Step 2: Verify failure.** Run `pytest tests/research/test_dataset_migration.py -q`; expected: missing script and normalized corpora/manifest.
- [ ] **Step 3: Implement deterministic migration.** Validate source Q01–Q40, copy the archival YAML, normalize exact fields/order, apply only Spec §26.1 changes, add v2 Q41–Q52 verbatim, write sorted unique seven-digit gold IDs, and compute deterministic graph/policy derivation hashes without time/random/network/model inputs.
- [ ] **Step 4: Validate and run.** Run `PYTHONPATH=src .venv/bin/python scripts/migrate_benchmark_v1.py tests/research/benchmark_dataset_legacy.yaml tests/research/benchmark_dataset_v1.yaml tests/research/benchmark_dataset_v2.yaml`; expected: deterministic completion and manifest output. Run focused migration tests (expected PASS).
- [ ] **Step 5: Commit and review.** `git add scripts/migrate_benchmark_v1.py tests/research/benchmark_dataset_legacy.yaml tests/research/benchmark_dataset_v1.yaml tests/research/benchmark_dataset_v2.yaml tests/research/benchmark_migration_manifest_v1.yaml tests/research/test_dataset_migration.py && git commit -m "feat: normalize CIFRE benchmark corpora"`. Review compares all before/after golds and verifies v2 negatives distinguish unknown token/entity, ambiguity, unsupported intent, and strict empty.

### Task 8: Rebuild benchmark runner, exact/status-gated metrics, and deterministic result artifact

**Files:**
- Modify: `src/semantic_layer/research/benchmark_runner.py:1-206`, `src/semantic_layer/research/__main__.py`
- Create/replace generated: `results/latest_benchmark.json`, `tests/research/test_benchmark_metrics.py`, `tests/research/test_result_artifact.py`

**Interfaces:**
- Consumes: Tasks 2, 5, and 6 contracts; Task 3 graph/provenance; Task 5 planner output.
- Produces: `BenchmarkRunner(knowledge_graph: SAPKnowledgeGraph, dataset_paths: Sequence[Path], result_path: Path = Path("results/latest_benchmark.json"))`; `run() -> dict[str, Any]` with exactly two conditions and v1/v2 `corpus_runs`; `score_query(expected_status: Status, observed_status: Status, gold: Sequence[str], predicted: Sequence[str]) -> QueryMetrics`; `aggregate_metrics(records: Sequence[QueryRecord]) -> ConditionAggregate`; `build_hash_manifest(root: Path) -> HashManifest`; and canonical `write_result_artifact(result: Mapping[str, Any], path: Path) -> None`.

- [ ] **Step 1: Write failing metric fixtures.** Add `test_result_hash_manifest_rejects_mutated_input`; assert the five Spec §18.1 hand-calculated rows, both-empty precision/recall/F1 = `1.000000`, one-empty/one-nonempty = `0.000000`, N/A answer metrics are JSON `null`, status counts include all five statuses, and relaxed candidates never enter strict scoring.
- [ ] **Step 2: Verify failure and remove fake comparisons.** Run `pytest tests/research/test_benchmark_metrics.py -q`; expected: current `ParadigmMetrics` lacks status gating and still exposes Vector RAG/hallucination. The new test must also assert `vector_rag`, `hallucination`, `VSR`, and superiority fields are absent.
- [ ] **Step 3: Implement two-condition runner.** Evaluate every corpus record under `deterministic_no_reflection_ablation` and `deterministic_bounded_repair`, derive per-query records matching Spec §17, preserve status/expected status and strict-vs-relaxed fields, and place every aggregate under `corpus_run.aggregate.by_condition[condition_id]`.
- [ ] **Step 4: Implement exact metrics and canonical artifact.** Use `Decimal` half-even six-place strings; calculate macro/micro, tier/category, operational, optional-binding, and status metrics; expand the exact Spec §26.6 manifest (excluding the artifact itself, `.git`, `.venv`, untracked files); include environment/lock/namespace/validation metadata; sort records and keys; forbid NaN/None/timestamps in hashed content.
- [ ] **Step 5: Verify schema/hash behavior.** Run `pytest tests/research/test_benchmark_metrics.py tests/research/test_result_artifact.py -q`; expected PASS. Run the runner once and then `python -c 'from semantic_layer.research.contracts import load_and_validate_result; load_and_validate_result("results/latest_benchmark.json")'`; expected: schema-valid artifact with exactly two corpus runs and 52 v2 records per condition.
- [ ] **Step 6: Commit and review.** `git add src/semantic_layer/research results/latest_benchmark.json tests/research/test_benchmark_metrics.py tests/research/test_result_artifact.py && git commit -m "feat: add deterministic CIFRE benchmark artifact"`. Review checks no fake paradigm, no pooled conditions, exact hash ordering, and per-query provenance/status completeness.

### Task 9: Add canonical validation/reproducibility target, parity, and CI

**Files:**
- Modify: `Makefile:7-38`, `.github/workflows/ci.yml:5-20`, `src/semantic_layer/validation.py`, `src/semantic_layer/semantic_validation.py`
- Create: `scripts/research_verify.py`, `tests/research/test_reproducibility.py`

**Interfaces:**
- Consumes: Tasks 2–8 registry, validation report, runner, corpora, graph fixtures, and lock.
- Produces: `run_research_verify(root: Path, python: str) -> VerificationReport`; graph parity function `assert_graph_isomorphic(generated: Graph, checked_in: Graph) -> None`; five matrix checks `SUPPORT_VALID`, `SUPPORT_INVALID`, `ERP_VALID`, `ERP_INVALID`, `COMBINED_VALID`; `PREREQUISITE_CYCLE_DEPTH` algorithm evidence; and Make target `research-verify` invoked exactly as `make PYTHON=.venv/bin/python research-verify`.

- [ ] **Step 1: Write failing reproducibility tests.** Monkeypatch a generated graph with one triple changed and assert `assert_graph_isomorphic` fails; mutate a namespaced fixture/hash and assert `run_research_verify` returns non-zero; assert the validation report contains exact paths/hashes/inference/results and cycle/depth outputs from Spec §22.
- [ ] **Step 2: Verify failures.** Run `pytest tests/research/test_reproducibility.py -q`; expected: missing helper/target and current validation API lacks scope, hash, parity, and algorithm evidence.
- [ ] **Step 3: Implement temporary generation and validation.** Generate into `TemporaryDirectory`, load generated/checked-in graphs, compare RDFLib graph isomorphism (not Turtle bytes), construct combined graph in the exact five-path order and shapes order, run pySHACL with `inference="rdfs", abort_on_first=False, advanced=False, js=False, meta_shacl=False`, and record expected nonconformance as passing negative control.
- [ ] **Step 4: Implement target and CI.** Make `research-verify` run generation/parity, all matrix checks, v1/v2 benchmark/result/schema validation, claim-contract tests, complete pytest, and Ruff. Install CI with the locked `--require-hashes --constraint` command and add job `research-verify`; if post-install execution exceeds 120 seconds, split into `research-verify-assets` and `research-verify-benchmark` with identical acceptance checks.
- [ ] **Step 5: Verify success and deliberate failure.** Run `make PYTHON=.venv/bin/python research-verify`; expected: zero exit, concise report, fresh result hashes. In a temporary copy mutate one fixture byte and rerun; expected: non-zero `HASH_MISMATCH`/parity failure without source replacement.
- [ ] **Step 6: Commit and review.** `git add Makefile .github/workflows/ci.yml src/semantic_layer/validation.py src/semantic_layer/semantic_validation.py scripts/research_verify.py tests/research/test_reproducibility.py && git commit -m "ci: add canonical CIFRE research verification"`. Review confirms lock installation, no silent fixture mutation, all matrix checks, and no shortened CI path.

### Task 10: Sanitize README, metadata, repository claims, and secondary positioning

**Files:**
- Modify: `README.md`, `pyproject.toml:5-15`, `docs/data-products.md`, `docs/governance.md`, `docs/federated-semantics.md`, all `mappings/**/*.yaml`, `data_products/**/*.yaml`, `examples/**/*`, generated query-plan/SQL docs, and tracked result consumers except `results/latest_benchmark.json` generation
- Test: `tests/unit/test_documentation_contract.py` (claim-only tests owned here)

**Interfaces:**
- Consumes: Task 8 artifact fields and Task 9 command/validation paths.
- Produces: first-screen README sections in required order, exact independent disclaimer, literal labels `Implemented locally`, `Synthetic/simulated`, `Proposed future work`, `Not implemented`, and package description `Independent synthetic semantic-layer and knowledge-graph research prototype`; all adapters labelled unexecuted simulations and federated semantic layer explicitly secondary.

- [ ] **Step 1: Add failing claim tests.** Add `test_publication_claim_surface_contract` asserting the disclaimer precedes the first research heading/benchmark command, README primary/secondary order, four status labels, exact package description terms/no affiliation/production claim, interview-brief/result/lock/provenance paths, and no SAP ownership/certification/vector/hallucination/solved-PhD claims across tracked publication files.
- [ ] **Step 2: Verify failure.** Run `pytest tests/unit/test_documentation_contract.py::test_publication_claim_surface_contract -q`; expected: current README/package/docs fail with opening affiliation, fake Vector RAG and unsupported ownership/capability language.
- [ ] **Step 3: Rewrite publication surface.** Put the exact Spec §4 disclaimer first; make synthetic KG/AQR, contracts, flow, reproducibility, benchmark method, limitations/future experiments, then federated ERP secondary. Label Databricks/Snowflake/Fabric as unexecuted simulations and replace ownership claims with `repository-maintained synthetic contract` or `illustrative mapping`.
- [ ] **Step 4: Verify wording and links.** Run the focused claim test (expected PASS), then the existing Markdown fence/link tests; expected: all links resolve and Mermaid remains GitHub-safe.
- [ ] **Step 5: Commit and review.** `git add README.md pyproject.toml docs/data-products.md docs/governance.md docs/federated-semantics.md mappings data_products examples tests/unit/test_documentation_contract.py && git commit -m "docs: sanitize CIFRE prototype claims"`. Review reads the first screen without source access and confirms current/proposed/not-implemented boundaries.

### Task 11: Rewrite proposal, add interview brief, and refresh verification report

**Files:**
- Modify: `docs/research/cifre_phd_proposal.md`, `docs/verification-report.md`
- Create: `docs/research/cifre-interview-brief.md`
- Test: `tests/unit/test_documentation_contract.py` (research handoff tests only)

**Interfaces:**
- Consumes: Task 8 exact post-change metrics/artifact, Task 9 exact command/validation matrix, Task 10 wording contract.
- Produces: proposal sections for motivation/questions, implemented baseline, protocol, hypotheses/future LLM/vector/hybrid experiments, privacy/provenance/human evaluation, risks/falsifiable outcomes/three-year directions, disclaimer/non-goals; interview brief with five source-verifiable statements, command, artifact, exact metrics, limitations, and no-affiliation statement; verification report with commit, hashes, commands, environment, and known limitations.

- [ ] **Step 1: Add failing handoff tests.** Add `test_publication_claim_contract_and_links`; assert proposal contains all required sections and independent boundary; brief contains the disclaimer, `cifre-synthetic-aqr-v1`, `results/latest_benchmark.json`, `make PYTHON=.venv/bin/python research-verify`, exact generated baseline metrics (read from artifact rather than copied constants), and five source links; report contains current commit/hash/command/lock/known-limitations fields.
- [ ] **Step 2: Verify failure.** Run `pytest tests/unit/test_documentation_contract.py -q`; expected: missing interview brief and stale proposal/report assertions.
- [ ] **Step 3: Rewrite documents from executable evidence.** State deterministic symbolic baseline as implemented, all learned retrieval/generation as proposed future work, synthetic corpus limitations, and federated layer as secondary; copy exact values and hashes from the verified artifact/command output only after Task 9 succeeds.
- [ ] **Step 4: Verify docs.** Run `make PYTHON=.venv/bin/python research-verify` and then `pytest tests/unit/test_documentation_contract.py -q`; expected: zero exit and links/commands point to existing artifacts.
- [ ] **Step 5: Commit and review.** `git add docs/research/cifre_phd_proposal.md docs/research/cifre-interview-brief.md docs/verification-report.md tests/unit/test_documentation_contract.py && git commit -m "docs: add CIFRE research handoff"`. Review independently traces each of five brief statements to source/test/artifact evidence.

### Task 12: Final branch audit and reproducibility gate

**Files:**
- Modify only files required to correct audit failures; otherwise no new implementation files.
- Test: `tests/unit/test_final_readiness.py` (extend with final claim/secret/manifest checks)

**Interfaces:**
- Consumes: all prior commits and the complete Spec §26.6 live manifest.
- Produces: a clean, reviewable branch with no forbidden claims/secrets/legacy IRIs/placeholders, valid Markdown/Mermaid/links, valid YAML/JSON/Turtle, matching result hashes, and passing full verification.

- [ ] **Step 1: Write failing final audit tests.** Add tests that scan tracked runtime/assets/tests/docs/examples/results/mappings/data products for forbidden legacy URI families and `help.sap.com` (excluding only the design spec), credentials/private-key patterns, the repository's placeholder-marker set, forbidden claims, missing required paths, stale `hash_manifest`, and result-ID/composite uniqueness.
- [ ] **Step 2: Run the audit and fix only scoped failures.** Run `rg -n -i 'help\.sap\.com|http://ontology\.sap\.com|http://data\.sap\.com|https://sap\.example/erp/' --glob '!docs/superpowers/specs/2026-09-19-cifre-research-prototype-hardening-design.md' .`; run `gitleaks detect --source . --no-banner --redact`; run the repository placeholder-marker scan; use `apply_patch` for corrections and preserve unrelated user changes.
- [ ] **Step 3: Validate all formats and links.** Run `python -m json.tool tests/research/result_schema.json`, YAML parse over tracked YAML, RDF parse for every tracked Turtle, `pytest tests/unit/test_documentation_contract.py tests/unit/test_final_readiness.py -q`, and Markdown/Mermaid/link checks; expected: PASS and no warnings promoted to claims.
- [ ] **Step 4: Run complete verification.** Run `make PYTHON=.venv/bin/python research-verify`, `pytest -q`, and `.venv/bin/python -m ruff check .`; expected: all commands exit 0, artifact hash manifest matches current bytes, v1/v2 and two conditions are present, and expected negative controls are reported as expected rather than failures.
- [ ] **Step 5: Final branch audit and handoff.** Run `git status --short`, `git diff --check`, `git log --oneline --decorate -20`, and inspect every task commit/file ownership against this plan. Do not push. A fresh reviewer repeats `make ... research-verify`, checks no external GitHub state changed, and signs the branch only after all acceptance criteria pass.

## Plan Self-Review

- **Spec coverage:** T1 covers baseline inventory; T2 lock/provenance/root schema; T3 namespace migration, SKOS/OWL split, datatypes, fixtures; T4 exact grammar/abstention; T5 closure/projection/planner/compiler; T6 statuses/repair/relaxation/provenance; T7 historical/v1/v2 migration manifest; T8 exact/status-gated metrics and root JSON; T9 parity/SHACL/reproducibility/CI; T10 repository claim sanitation and federated-secondary positioning; T11 proposal/brief/report; T12 scans and complete verification.
- **Placeholder scan:** Every implementation behavior in this plan names a path, interface, focused test, command, and expected outcome; the final audit explicitly scans placeholder markers and secrets.
- **Type consistency:** `NAMESPACE_REGISTRY`, `Status`, `ReasonCode`, `GroundedEntities`, `LogicalQueryPlan`, `ReasoningResult`, `BenchmarkRunner`, and `VerificationReport` are introduced before consumers; condition/status/reason names match the spec tables and result schema.
- **Shared-file sequencing:** `tests/unit/test_documentation_contract.py` is split by ownership and only touched by T10/T11; `Makefile`/CI only T9; `pyproject.toml` dependency declaration T2 then description T10; `results/latest_benchmark.json` is generated only by T8 and refreshed by T11/T12 verification; no parallel wave edits these files.
- **Feasibility:** Each task has a focused failure-first test and bounded commit/review gate. T3/T4 are the only parallel wave and have disjoint implementation/test files. Full `research-verify` is deferred until all contracts and assets exist.
