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
- `make PYTHON=.venv/bin/python research-verify` is the final post-publication gate: after all code, docs, claim, proposal, and report files are final, it generates the canonical artifact, checks graph isomorphism, runs all five SHACL matrix rows plus the prerequisite algorithm row, runs both corpora/conditions, validates JSON/claims, runs pytest/Ruff, and fails non-zero on drift or stale hashes. Earlier tasks may run only focused asset checks or write temporary artifacts outside `results/`.
- Implementers use `apply_patch`, preserve unrelated work, commit only their task files, and do not push or mutate GitHub metadata/remotes/releases/topics.

## Review Focus

- Unknown, ambiguous, unsupported, and uncued tokens must abstain before planning with no invented URI or query; pinned by Task 4 `test_grounding_rejects_unknown_ambiguous_and_unsupported_inputs_before_planning`.
- A strict empty result with a successful relaxed candidate must remain `EMPTY_RESULT` and disclose the ordered relaxation ledger; pinned by Task 6 `test_relaxed_candidates_never_become_strict_success`.
- A transitive prerequisite cycle and depth-17 chain must terminate deterministically, exclude the target, and emit the exact cycle/depth evidence; pinned by Task 5 `test_prerequisite_cycle_and_depth_contract`.
- A stale or mutated input must invalidate the result artifact through the full manifest rather than silently reuse checked-in numbers; pinned by Task 8 `test_result_hash_manifest_rejects_mutated_input`.
- Public claims and links must expose the independent synthetic boundary and executable verification path, while retaining the federated layer as secondary; pinned by Task 11 `test_publication_claim_contract_and_links`.

## Dependency Graph and Safe Luna Waves

Tasks own the files listed below exclusively. A reviewer runs only the task’s focused failing/pass command until the publication files are final; the full `research-verify`, full claim scan, canonical result generation, and full pytest gate are reserved for T13. No two agents edit a shared file in the same wave. T3 owns namespace edits in `data_products/*.yaml`; T10 owns the later wording pass in those same four files and is therefore serialized after T3. T2 owns dependency declarations before T11 owns the package description. T8 may write only a temporary result outside `results/`; T13 is the sole owner of checked-in `results/latest_benchmark.json`.

```text
T1 baseline
  -> T2 lock + contracts/schema
       -> T3 namespaces/assets/fixtures  -┐
       -> T4 grammar/grounding ----------─┼-> T5 AQR planner/SPARQL contract
                                         └-> T6 repair/result consumers
T5 + T6 -> T7 corpus/migration manifest -> T8 benchmark + temporary artifact
T3 + T8 -> T9 asset validation/repro helper (local only, no CI)
T9 -> T10 code/examples/mappings/data-product claim pass
T10 -> T11 README/public docs/package/secondary positioning
T11 -> T12 proposal/interview brief/verification report
T12 -> T13 final scans + canonical result + full research-verify/pytest/lint
```

Safe waves are: Wave 0 `{T1}`; Wave 1 `{T2}`; Wave 2 `{T3, T4}`; Wave 3 `{T5}`; Wave 4 `{T6}`; Wave 5 `{T7}`; Wave 6 `{T8}`; Wave 7 `{T9}`; Wave 8 `{T10}`; Wave 9 `{T11}`; Wave 10 `{T12}`; Wave 11 `{T13}`. T3 and T4 are the only parallel wave and have disjoint implementation/test files. All publication and verification waves are serialized so the final hash manifest is generated only after every claim-bearing file is settled.

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
- Produces: `NAMESPACE_REGISTRY: Mapping[str, str]`; `Status` enum with exactly `SUCCESS`, `UNSUPPORTED`, `SYNTAX_ERROR`, `EXECUTION_ERROR`, `EMPTY_RESULT`; `ReasonCode` enum with exactly `NONE`, `UNKNOWN_TOKEN`, `UNKNOWN_ENTITY`, `AMBIGUOUS_INPUT`, `AMBIGUOUS_INTENT`, `MULTIPLE_DISTINCT_ENTITIES`, `UNSUPPORTED_INTENT`, `MISSING_REQUIRED_ENTITY`, `UNBOUND_REQUIRED_PROJECTION`, `SPARQL_SYNTAX`, `SPARQL_EXECUTION`, `EMPTY_STRICT_RESULT`, `RELAX_SUPPORT_PACKAGE`, `WIDEN_COMPONENT`, `REPAIR_BUDGET_EXHAUSTED`, `PROVENANCE_MISSING`, `HASH_MISMATCH`, `INVALID_DATASET`, `NO_OP_REPAIR`, and `PREREQUISITE_DEPTH_EXCEEDED`; `CONDITIONS = ("deterministic_no_reflection_ablation", "deterministic_bounded_repair")`; `canonical_json(value: object) -> bytes`; `sha256_bytes(data: bytes) -> str`; `load_and_validate_result(path: Path) -> dict[str, Any]`; and the authoritative root JSON Schema `$id` `https://example.org/cifre-kg/schema/research-result-root-1.0.0.json`. Artifact-level `HASH_MISMATCH` and `INVALID_DATASET` are never emitted as per-query reasons.

- [ ] **Step 1: Write failing contract tests.** In `tests/research/test_contracts.py`, assert the registry equals the exact seven IRI mapping, every status/reason enum value is closed, `canonical_json({"b": 1, "a": 2}) == b'{"a":2,"b":1}'`, provenance has exactly the Spec §20 top-level keys and `official is False`, and a root result with `schema_version != "1.0.0"` is rejected by `load_and_validate_result`.
- [ ] **Step 2: Verify the failures.** Run `pytest tests/research/test_contracts.py -q`; expected: import failure for `semantic_layer.research.contracts`, missing lock/provenance/schema paths, and missing schema validation.
- [ ] **Step 3: Add the schema validator and generate the lock.** Add the reviewed `jsonschema` version to the development dependencies, then in a clean Python 3.12 environment install `pip==25.2`, install `pip-tools==7.4.1`, run `.venv/bin/pip-compile --extra=dev --generate-hashes --output-file=constraints/py312.txt pyproject.toml`, and verify every direct/transitive distribution is pinned with hashes. The plan executor must not upgrade unrelated dependencies.
- [ ] **Step 4: Implement contracts and schema.** Add exact enums, namespace constants, canonical JSON serialization (UTF-8, sorted keys, no insignificant whitespace), SHA-256 helpers, provenance loader, and the complete Spec §26.4 root schema with `additionalProperties: false`, nullable fields, condition/status enums, composite result-ID requirements, metric precision, validation matrix, corpus runs, and per-query definitions.
- [ ] **Step 5: Add provenance and verify.** Write `semantic/provenance/synthetic_source.yaml` with exactly the Spec §20 fields, including `official: false`, `source_kind: synthetic_fixture`, exact generator/graph paths, namespace registry, and forbidden official-label policy. Run `pytest tests/research/test_contracts.py -q` (expected PASS), then `python -m json.tool tests/research/result_schema.json` (expected valid JSON).
- [ ] **Step 6: Commit and review.** `git add constraints/py312.txt semantic/provenance/synthetic_source.yaml src/semantic_layer/research/contracts.py tests/research/result_schema.json tests/research/test_contracts.py && git commit -m "build: lock CIFRE research contracts"`. Review verifies no unpinned dependency, root schema completeness, and exact contract names before T3/T4.

### Task 3: Migrate neutral namespaces and synthetic semantic assets

**Files:**
- Modify exactly: `src/semantic_layer/kg/loader.py:20-120`, `src/semantic_layer/kg/sap_dataset_generator.py:18-end`, `semantic/data/sap_support_graph.ttl`, `semantic/metrics/metrics.yaml`, `semantic/ontology/sample-graph-invalid.ttl`, `semantic/ontology/sample-graph-valid.ttl`, `semantic/ontology/sap_erp.ttl`, `semantic/ontology/sap_ppms.ttl`, `semantic/ontology/sap_support.ttl`, `semantic/rules/financial_postings.yaml`, `semantic/shapes/sap_erp_shapes.ttl`, `semantic/shapes/sap_support_shapes.ttl`, `semantic/taxonomy/sap_products.ttl`, `semantic/vocabulary/sap_erp.yaml`, `data/generate_demo_data.py`, `data_products/acdoca_financials.yaml`, `data_products/billing_analytics.yaml`, `data_products/business_partners.yaml`, `data_products/sales_orders.yaml`, `tests/semantic/test_active_policy_regression.py`, `tests/semantic/test_mappings.py`, `tests/semantic/test_metric_rules.py`, `tests/semantic/test_sap_kg.py`, `tests/semantic/test_shacl.py`, `tests/semantic/test_vocabulary.py`.
- Create: `semantic/data/support-graph-invalid.ttl`, `semantic/data/support-prerequisite-cycle.ttl`, `semantic/data/support-prerequisite-depth17.ttl`
- Create tests: `tests/semantic/test_namespace_contract.py`, `tests/semantic/test_asset_datatypes.py`
- Coordination: namespace literals in README, examples, public-doc, and research files are updated by their exact T10–T12 owner before that owner’s wording pass; T3 owns only semantic/code assets and the four data-product namespace edits. This is the intentional namespace-first/claim-second sequencing.

**Interfaces:**
- Consumes: `NAMESPACE_REGISTRY` from Task 2 and `SAPKnowledgeGraph`/`build_sap_support_graph` current APIs.
- Produces: `NamespaceRegistry`-backed constants `CIFSUP`, `CIFPPMS`, `CIFDATA`, `CIFERP`, `CIFSKOS`, `CIFMETA`, `CIFMETAID`; `build_sap_support_graph(ontology_paths: list[str | Path] | None = None) -> Graph` emitting only neutral IRIs; `SAPKnowledgeGraph.validate_shacl(shapes_path: str | Path, *, scope: str = "support") -> ValidationReport`; and synthetic metadata/crosswalk triples with disjoint OWL/SKOS resources.

- [ ] **Step 1: Add failing namespace/data tests.** Assert every tracked synthetic RDF/YAML resource IRI is under an approved base, and only these three control documents may contain forbidden legacy URI families: `docs/superpowers/specs/2026-09-19-cifre-research-prototype-hardening-design.md`, `docs/superpowers/plans/2026-09-19-cifre-research-prototype-hardening.md`, and `docs/research/cifre-hardening-baseline.md`; every other scanned file must be clean. Also assert graph metadata has `cifmeta:sourceKind "synthetic_fixture"` and `cifmeta:official false`, human labels are English `rdf:langString`, and `cifskos:ProductAutomotive` is a `skos:Concept` but not an OWL class/type.
- [ ] **Step 2: Verify failure before migration.** Run `pytest tests/semantic/test_namespace_contract.py tests/semantic/test_asset_datatypes.py -q`; expected: failures for old namespace bindings/IRIs, absent provenance, old `sh:or` datatype workaround, and SKOS/OWL collisions.
- [ ] **Step 3a: Migrate the runtime namespace producers first.** Modify only `src/semantic_layer/kg/loader.py`, `src/semantic_layer/kg/sap_dataset_generator.py`, and `data/generate_demo_data.py`; replace `PPMS`/`SAP` constants with the Task 2 registry, map instance bases to `data/support`, `data/ppms`, and `data/erp`, and remove `help.sap.com` without aliases or dual emission. Run `pytest tests/semantic/test_sap_kg.py tests/semantic/test_vocabulary.py -q`; expected: the focused tests pass with neutral constants and no old runtime prefixes.
- [ ] **Step 3b: Migrate ontology, vocabulary, rules, and shape assets.** Modify exactly `semantic/ontology/sample-graph-invalid.ttl`, `semantic/ontology/sample-graph-valid.ttl`, `semantic/ontology/sap_erp.ttl`, `semantic/ontology/sap_ppms.ttl`, `semantic/ontology/sap_support.ttl`, `semantic/rules/financial_postings.yaml`, `semantic/shapes/sap_erp_shapes.ttl`, `semantic/shapes/sap_support_shapes.ttl`, `semantic/taxonomy/sap_products.ttl`, and `semantic/vocabulary/sap_erp.yaml`; split ERP OWL resources under `ciferp:` from SKOS concepts under `cifskos:`, add `cifmetaid:crosswalk-entry-product-automotive` with the exact `CrosswalkEntry` shape, and update only direct IRI/prefix references. Run `pytest tests/semantic/test_namespace_contract.py tests/semantic/test_shacl.py -q`; expected: namespace and shape assertions pass before data-product edits.
- [ ] **Step 3c: Migrate generated data, metrics, products, and their consumers.** Modify exactly `semantic/data/sap_support_graph.ttl`, `semantic/metrics/metrics.yaml`, `data_products/acdoca_financials.yaml`, `data_products/billing_analytics.yaml`, `data_products/business_partners.yaml`, `data_products/sales_orders.yaml`, `tests/semantic/test_active_policy_regression.py`, `tests/semantic/test_mappings.py`, and `tests/semantic/test_metric_rules.py`; update neutral identifiers and direct SPARQL/test references while preserving product wording for T10’s later claim pass. Run `pytest tests/semantic/test_active_policy_regression.py tests/semantic/test_mappings.py tests/semantic/test_metric_rules.py -q`; expected: all namespace consumers pass, with no legacy aliases.
- [ ] **Step 4: Correct semantic datatypes and fixtures.** Change human-readable ranges/shapes to `rdf:langString` with `sh:languageIn ("en")`, keep machine fields `xsd:string`/numeric, add the invalid support graph with provenance, and add exact A→B→C→A and N0→…→N17 fixtures. Run `pytest tests/semantic/test_asset_datatypes.py tests/semantic/test_shacl.py -q`; expected: PASS.
- [ ] **Step 5: Regenerate and run the asset regression.** Generate the checked-in support graph with `PYTHONPATH=src .venv/bin/python -m semantic_layer.kg.sap_dataset_generator`, parse each named RDF/YAML asset, then run `pytest tests/semantic -q`; expected: no namespace/asset regressions.
- [ ] **Step 6: Commit and review.** `git add src/semantic_layer/kg/loader.py src/semantic_layer/kg/sap_dataset_generator.py semantic/data/sap_support_graph.ttl semantic/metrics/metrics.yaml semantic/ontology/sample-graph-invalid.ttl semantic/ontology/sample-graph-valid.ttl semantic/ontology/sap_erp.ttl semantic/ontology/sap_ppms.ttl semantic/ontology/sap_support.ttl semantic/rules/financial_postings.yaml semantic/shapes/sap_erp_shapes.ttl semantic/shapes/sap_support_shapes.ttl semantic/taxonomy/sap_products.ttl semantic/vocabulary/sap_erp.yaml data/generate_demo_data.py data_products/acdoca_financials.yaml data_products/billing_analytics.yaml data_products/business_partners.yaml data_products/sales_orders.yaml tests/semantic/test_active_policy_regression.py tests/semantic/test_mappings.py tests/semantic/test_metric_rules.py tests/semantic/test_sap_kg.py tests/semantic/test_shacl.py tests/semantic/test_vocabulary.py semantic/data/support-graph-invalid.ttl semantic/data/support-prerequisite-cycle.ttl semantic/data/support-prerequisite-depth17.ttl tests/semantic/test_namespace_contract.py tests/semantic/test_asset_datatypes.py && git commit -m "refactor: migrate CIFRE synthetic namespaces"`. Review scans for aliases, official-looking IRIs, missing provenance, and shared files before accepting T3; T10 owns only the later wording pass in the four data-product YAMLs.

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
- Create: `tests/unit/test_aqr_query_planner.py`
- Modify consumers: `tests/unit/test_query_planner.py`, `tests/semantic/test_sap_kg.py`; `tests/unit/test_sap_reasoning.py` keeps only grounding/compiler smoke coverage from T4/T5 and does not own planner-contract assertions.

**Interfaces:**
- Consumes: Task 3 namespace registry and Task 4 `GroundedEntities` intent/slots.
- Produces: `TraversalPattern(subject: str, predicate: str, object_val: str, optional: bool = False)`; `LogicalQueryPlan(target_var: str, intent: str, select_vars: list[str], patterns: list[TraversalPattern], filters: list[str], optional_patterns: list[TraversalPattern], required_variables: list[str], optional_variables: list[str], order_by: str | None, limit: int)`; `QueryPlanner.plan(entities: GroundedEntities) -> LogicalQueryPlan`; `TextToSPARQLEngine.compile(plan: LogicalQueryPlan) -> str`; and `TextToSPARQLEngine.validate_projections(plan) -> None` raising `ValueError`/`UNBOUND_REQUIRED_PROJECTION` before compilation.

- [ ] **Step 1: Write failing planner tests in the dedicated path.** Add `test_prerequisite_cycle_and_depth_contract`, `test_all_projected_variables_have_patterns`, and `test_combined_anchor_and_optional_projection_contract` to `tests/unit/test_aqr_query_planner.py`; assert prerequisite plans select only `?note`, `?noteNumber`, `?title`, every selected variable has a required/optional pattern, the bounded union contains path lengths 1–16 and no unbounded `+`, combined alert+component+version anchors correctly, support-package filters are numeric, and optional variables are emitted only in `OPTIONAL` blocks.
- [ ] **Step 2: Verify failures.** Run `pytest tests/unit/test_aqr_query_planner.py -q`; expected: current `?prereqTitle` projection and old predicates/prefixes fail. Run `pytest tests/unit/test_query_planner.py tests/unit/test_sap_reasoning.py -q`; expected: legacy consumer failures identify only compatibility assertions to update after the dedicated contract passes.
- [ ] **Step 3: Implement minimal typed planning.** Emit neutral `cifsup`/`cifppms` predicates; use exact `PREREQUISITE_CLOSURE`; generate a deterministic union of 1..16 `hasPrerequisiteNote` hops with target exclusion and a depth marker; maintain sorted required/optional projection lists; reject any unbound required projection.
- [ ] **Step 4: Implement compiler validation and deterministic ordering.** Emit `PREFIX cifsup`, `PREFIX cifppms`, `PREFIX cifdata`, `PREFIX xsd`, and standard W3C prefixes; render required patterns, `OPTIONAL` patterns, filters, `ORDER BY`, and `LIMIT` deterministically; reject selected variables with no pattern.
- [ ] **Step 5: Verify closure and parity behavior.** Run `pytest tests/unit/test_aqr_query_planner.py -q` (expected PASS), then `pytest tests/semantic/test_sap_kg.py tests/unit/test_query_planner.py tests/unit/test_sap_reasoning.py -q`; expected PASS, including no target note, deduplication, cycle termination, and depth-17 `EMPTY_RESULT` contract.
- [ ] **Step 6: Commit and review.** `git add src/semantic_layer/reasoning/query_planner.py src/semantic_layer/reasoning/text_to_sparql.py tests/unit/test_aqr_query_planner.py tests/unit/test_query_planner.py tests/unit/test_sap_reasoning.py tests/semantic/test_sap_kg.py && git commit -m "fix: make CIFRE plans projection safe"`. Reviewer checks each projected variable is bound and no old namespace/predicate survives.

### Task 6: Add typed AQR statuses, bounded repair state machine, and provenance answers

**Files:**
- Modify: `src/semantic_layer/reasoning/reflective_agent.py:26-231`, `src/semantic_layer/agents/tools.py` and any CLI integration that serializes `ReasoningResult`
- Modify consumers: `src/semantic_layer/demo_sap.py`, `tests/integration/test_sap_agent.py`
- Create: `tests/research/test_failure_state_machine.py`, `tests/research/test_answer_provenance.py`

**Interfaces:**
- Consumes: Task 2 `Status`/`ReasonCode`; Task 4 fail-closed grounding; Task 5 typed plans/compiler.
- Produces: `ReasoningResult` with `normalized_request`, `grounding`, `plan`, `sparql_initial`, `sparql_final`, `status: Status`, `reason_code: ReasonCode`, `attempts: int`, `repair: RepairLedger`, `relaxation: RelaxationDisclosure`, `answer_scope: Literal["strict", "relaxed_candidates", "none"]`, `relaxed_candidates`, `bindings`, `predicted_note_numbers`, `provenance`; `AQRReflectiveAgent.run(query_text: str, condition: str = "deterministic_bounded_repair", max_repairs: int = 3) -> ReasoningResult`; `RepairOperation` with the exact Spec §18.2 fields; and `sanitize_diagnostic(text: str, limit: int = 512) -> str`. Consumers in `src/semantic_layer/demo_sap.py` and `tests/integration/test_sap_agent.py` must read `result.status`, `result.reason_code`, `result.bindings`, and `result.provenance` instead of `execution_status`, `results`, or SAP-labelled citations.

- [ ] **Step 1: Write failing state-machine tests.** Use a fake KG that returns bindings, empty rows, fixed syntax exceptions, and fixed execution exceptions. Assert initial index 0, max three repairs, attempts 0/1–4, exact status/reason pairs, append-only operation ledger, no-op detection, sanitized diagnostics, and no-reflection never entering repair.
- [ ] **Step 2: Pin the critical relaxation test.** In `test_relaxed_candidates_never_become_strict_success`, return no rows for strict SP/component constraints and rows after removing the support-package bound; assert `status is EMPTY_RESULT`, `reason_code is RELAX_SUPPORT_PACKAGE`, `answer_scope == "relaxed_candidates"`, strict `predicted_note_numbers == []`, and operation order remove-package then widen-component.
- [ ] **Step 3: Verify failures.** Run `pytest tests/research/test_failure_state_machine.py tests/research/test_answer_provenance.py -q`; expected: current agent returns string status, marks relaxation as recovery, has no closed reason code, and emits SAP-labelled citations.
- [ ] **Step 4: Implement the closed lifecycle.** Abstain before planning for unsupported grounding; map syntax/execution/empty events to the exact state table in Spec §26.5; record full attempted SPARQL text plus hashes; enforce `max_repairs == 3`; retain original constraints and strict status while exposing relaxed candidates separately.
- [ ] **Step 5: Implement binding-derived answers and provenance.** Build answer lines only from final strict bindings; use citation prefix `Synthetic fixture cifre-synthetic-support-ppms-v1; not official data.`; return no factual answer for unsupported/errors; sort bindings and nullable optional fields deterministically.
- [ ] **Step 6: Update and verify consumers.** Change `src/semantic_layer/demo_sap.py` and `tests/integration/test_sap_agent.py` to use the typed result fields and explicit strict/relaxed labels; run `pytest tests/research/test_failure_state_machine.py tests/research/test_answer_provenance.py tests/integration/test_sap_agent.py -q` (expected PASS), then `pytest tests/unit/test_sap_reasoning.py -q` (expected PASS).
- [ ] **Step 7: Commit and review.** `git add src/semantic_layer/reasoning/reflective_agent.py src/semantic_layer/agents/tools.py src/semantic_layer/demo_sap.py tests/research/test_failure_state_machine.py tests/research/test_answer_provenance.py tests/integration/test_sap_agent.py && git commit -m "feat: harden CIFRE AQR result lifecycle"`. Review checks state transitions, status/reason legality, and credential-safe diagnostics.

### Task 7: Normalize historical corpus, migration manifest, and v2 negatives

**Files:**
- Create: `scripts/migrate_benchmark_v1.py`, `tests/research/benchmark_dataset_legacy.yaml`, `tests/research/benchmark_dataset_v1.yaml`, `tests/research/benchmark_dataset_v2.yaml`, `tests/research/benchmark_migration_manifest_v1.yaml`, `tests/research/test_dataset_migration.py`
- Preserve unchanged: `tests/research/benchmark_dataset.yaml`

**Interfaces:**
- Consumes: Task 4 grammar/status reasons, Task 5 closure semantics, Task 6 result status model, and the exact legacy Q01-Q40 file.
- Produces: `migrate_benchmark(source: Path, v1: Path, v2: Path, manifest: Path) -> None`; `validate_migration_manifest(manifest: Mapping[str, Any]) -> None`; normalized records with exactly `id, corpus_id, version, tier, category, question, expected_status, gold_note_numbers, reflection_reason, strict_constraints, gold_policy`; v1 IDs Q01–Q40; v2 IDs Q01–Q52; and a signed 40-entry migration manifest. The manifest top level is exactly `schema_version`, `source_path`, `archival_path`, `normalized_path`, `record_ids`, `changes`, `records`, `review`; each `records[]` entry is exactly `id`, `category_before`, `category_after`, `gold_before`, `gold_after`, `status_before`, `status_after`, `schema_before`, `schema_after`, `migration_reason`, `policy_citation`, `derivation_query`, `reviewer_id`, `signed_off`; `derivation_query` is exactly `kind`, `text`, `graph_sha256`, `result`, `result_sha256`; and `review` is exactly `reviewer_id`, `signoff_required`, `signed_off`. `migration_reason` is one of `SCHEMA_NORMALIZATION`, `PREREQUISITE_CLOSURE_EXPANSION`, `PREREQUISITE_CLOSURE_NORMALIZATION`, or `STRICT_CONSTRAINT_STATUS_CORRECTION`.

- [ ] **Step 1: Write failing migration tests.** Add `test_migration_manifest_has_exact_fields_and_reasons` and `test_cross_record_manifest_ids_and_signoff_are_valid`; assert legacy archival is byte-identical, normalized v1 has 40 exact IDs/no `expected_notes`, v2 has the exact Q41–Q52 category/status/reason/question table, Q25/Q28/Q31 expand to `["3012445", "3098110"]`, Q33–Q40 become strict `EMPTY_RESULT`, and every manifest top-level/record/derivation/review field and the four-value `migration_reason` enum is present.
- [ ] **Step 2: Verify failure.** Run `pytest tests/research/test_dataset_migration.py -q`; expected: missing script and normalized corpora/manifest, followed by a direct `validate_migration_manifest` import failure.
- [ ] **Step 3: Implement deterministic migration.** Validate source Q01–Q40, copy the archival YAML, normalize exact fields/order, apply only Spec §26.1 changes, add v2 Q41–Q52 verbatim, write sorted unique seven-digit gold IDs, and compute deterministic graph/policy derivation hashes without time/random/network/model inputs.
- [ ] **Step 4: Validate and run.** Run `PYTHONPATH=src .venv/bin/python scripts/migrate_benchmark_v1.py tests/research/benchmark_dataset_legacy.yaml tests/research/benchmark_dataset_v1.yaml tests/research/benchmark_dataset_v2.yaml`; expected: deterministic completion and manifest output. Run `pytest tests/research/test_dataset_migration.py -q` (expected PASS), including rejection of a missing field, duplicate record ID, unsigned record, invalid reason enum, and missing derivation hash.
- [ ] **Step 5: Commit and review.** `git add scripts/migrate_benchmark_v1.py tests/research/benchmark_dataset_legacy.yaml tests/research/benchmark_dataset_v1.yaml tests/research/benchmark_dataset_v2.yaml tests/research/benchmark_migration_manifest_v1.yaml tests/research/test_dataset_migration.py && git commit -m "feat: normalize CIFRE benchmark corpora"`. Review compares all before/after golds and verifies v2 negatives distinguish unknown token/entity, ambiguity, unsupported intent, and strict empty.

### Task 8: Rebuild benchmark runner, exact/status-gated metrics, and temporary result contract

**Files:**
- Modify: `src/semantic_layer/research/benchmark_runner.py:1-206`, `src/semantic_layer/research/__main__.py`
- Create: `tests/research/test_benchmark_metrics.py`, `tests/research/test_result_artifact.py`
- Temporary only: `tmp/cifre-benchmark-result.json` (untracked and deleted after the focused run); T13 is the sole owner of checked-in `results/latest_benchmark.json`.

**Interfaces:**
- Consumes: Tasks 2, 5, and 6 contracts; Task 3 graph/provenance; Task 5 planner output.
- Produces: `BenchmarkRunner(knowledge_graph: SAPKnowledgeGraph, dataset_paths: Sequence[Path], result_path: Path)` (the focused runner requires a caller-supplied temporary path); `run() -> dict[str, Any]` with exactly two conditions and v1/v2 `corpus_runs`; `score_query(expected_status: Status, observed_status: Status, gold: Sequence[str], predicted: Sequence[str]) -> QueryMetrics`; `aggregate_metrics(records: Sequence[QueryRecord]) -> ConditionAggregate`; `build_hash_manifest(root: Path) -> HashManifest`; `validate_result_id_references(result: Mapping[str, Any]) -> None`; and `write_result_artifact(result: Mapping[str, Any], path: Path) -> None`. T13 alone calls the writer with `results/latest_benchmark.json` after publication files are final.

- [ ] **Step 1: Write failing metric fixtures.** Add `test_result_hash_manifest_rejects_mutated_input`, `test_result_ids_are_unique_and_reference_composite_keys`, and `test_status_gated_metric_hand_fixtures`; assert the five Spec §18.1 hand-calculated rows, both-empty precision/recall/F1 = `1.000000`, one-empty/one-nonempty = `0.000000`, N/A answer metrics are JSON `null`, status counts include all five statuses, relaxed candidates never enter strict scoring, and `validate_result_id_references` rejects duplicate `(corpus_id, condition, query_id)` tuples or a `result_ids` entry not exactly referencing `<corpus_id>:<condition>:<query_id>`.
- [ ] **Step 2: Verify failure and remove fake comparisons.** Run `pytest tests/research/test_benchmark_metrics.py -q`; expected: current `ParadigmMetrics` lacks status gating and still exposes Vector RAG/hallucination. The new test must also assert `vector_rag`, `hallucination`, `VSR`, and superiority fields are absent.
- [ ] **Step 3: Implement and pass metric scoring.** Implement `score_query`, `aggregate_metrics`, `validate_result_id_references`, and `build_hash_manifest`; use `Decimal` half-even six-place strings, status gating, empty-set edge rules, exact composite IDs, and the exact Spec §26.6 path expansion. Run `pytest tests/research/test_benchmark_metrics.py -q`; expected: PASS.
- [ ] **Step 4: Implement and pass the two-condition runner.** Evaluate every corpus record under `deterministic_no_reflection_ablation` and `deterministic_bounded_repair`, derive per-query records matching Spec §17, preserve strict-vs-relaxed fields, and place every aggregate under `corpus_run.aggregate.by_condition[condition_id]`; include environment/lock/namespace/validation metadata and forbid NaN/None/timestamps in hashed content. Run `pytest tests/research/test_result_artifact.py -q`; expected: PASS against an in-memory result.
- [ ] **Step 5: Verify temporary artifact only.** Run this self-cleaning block, then confirm the temporary path is gone before reporting the focused result:

  ```bash
  cifre_tmp_dir="$(mktemp -d)"
  trap 'rm -rf -- "$cifre_tmp_dir"' EXIT
  PYTHONPATH=src .venv/bin/python -m semantic_layer.research \
    --output "$cifre_tmp_dir/cifre-benchmark-result.json"
  pytest tests/research/test_benchmark_metrics.py \
    tests/research/test_result_artifact.py -q
  rm -rf -- "$cifre_tmp_dir"
  trap - EXIT
  ```

  Expect PASS with a schema-valid temporary object containing exactly two corpus runs and 52 v2 records per condition. Do not create or stage `results/latest_benchmark.json` in this task.
- [ ] **Step 6: Commit and review.** `git add src/semantic_layer/research/benchmark_runner.py src/semantic_layer/research/__main__.py tests/research/test_benchmark_metrics.py tests/research/test_result_artifact.py && git commit -m "feat: add deterministic CIFRE benchmark metrics"`. Review checks no fake paradigm, no pooled conditions, exact composite result-ID validation, and no checked-in canonical result before publication is final.

### Task 9: Add asset validation and reproducibility helpers

**Files:**
- Modify: `src/semantic_layer/validation.py`, `src/semantic_layer/semantic_validation.py`
- Create: `scripts/research_verify.py`, `tests/research/test_reproducibility.py`

**Interfaces:**
- Consumes: Tasks 2–8 registry, validation report, runner, corpora, graph fixtures, and lock.
- Produces: `run_research_verify(root: Path, python: str, *, mode: Literal["assets", "final"]) -> VerificationReport` with `run_asset_verification(root: Path, python: str) -> VerificationReport` as the focused wrapper; graph parity function `assert_graph_isomorphic(generated: Graph, checked_in: Graph) -> None`; five SHACL matrix checks `SUPPORT_VALID`, `SUPPORT_INVALID`, `ERP_VALID`, `ERP_INVALID`, `COMBINED_VALID`; and `PREREQUISITE_CYCLE_DEPTH` algorithm evidence. T9 supplies the reusable final-mode function but does not modify `Makefile`, `.github/workflows/ci.yml`, claim gates, or the canonical artifact; T13 owns that wiring and gate.

- [ ] **Step 1: Write failing reproducibility tests.** Monkeypatch a generated graph with one triple changed and assert `assert_graph_isomorphic` fails; mutate a namespaced fixture/hash and assert `run_research_verify` returns non-zero; assert the validation report contains exact paths/hashes/inference/results and cycle/depth outputs from Spec §22.
- [ ] **Step 2: Verify failures.** Run `pytest tests/research/test_reproducibility.py -q`; expected: missing helper/target and current validation API lacks scope, hash, parity, and algorithm evidence.
- [ ] **Step 3: Implement temporary generation and validation.** Generate into `TemporaryDirectory`, load generated/checked-in graphs, compare RDFLib graph isomorphism (not Turtle bytes), construct combined graph in the exact five-path order and shapes order, run pySHACL with `inference="rdfs", abort_on_first=False, advanced=False, js=False, meta_shacl=False`, and record expected nonconformance as passing negative control.
- [ ] **Step 4: Implement asset-only mode.** Add `--assets-only` to `scripts/research_verify.py`; make asset mode run generation/parity, all matrix checks, and validation reports without benchmark output, claim tests, full pytest, Ruff, Makefile changes, or CI changes. Leave final target/CI ownership entirely to T13.
- [ ] **Step 5: Verify only asset success and deliberate failure.** Run `PYTHONPATH=src .venv/bin/python scripts/research_verify.py --assets-only`; expected: zero exit and validation evidence, with no `results/latest_benchmark.json`. In a temporary copy mutate one fixture byte and rerun; expected: non-zero parity/hash failure without source replacement. Do not run the final Make target or CI wiring yet.
- [ ] **Step 6: Commit and review.** `git add src/semantic_layer/validation.py src/semantic_layer/semantic_validation.py scripts/research_verify.py tests/research/test_reproducibility.py && git commit -m "feat: add CIFRE asset verification boundary"`. Review confirms no Makefile/CI mutation, no silent fixture mutation, all asset checks, and that the final gate remains deferred to T13.

### Task 10: Sanitize non-publication code, examples, mappings, and data-product claims

**Files:**
- Modify exactly: `src/semantic_layer/__init__.py`, `src/semantic_layer/adapters/__init__.py`, `src/semantic_layer/adapters/cloud.py`, `src/semantic_layer/adapters/duckdb.py`, `src/semantic_layer/agents/__init__.py`, `src/semantic_layer/agents/workflow.py`, `src/semantic_layer/api/__init__.py`, `src/semantic_layer/api/app.py`, `src/semantic_layer/compiler/__init__.py`, `src/semantic_layer/compiler/base.py`, `src/semantic_layer/compiler/cloud_examples.py`, `src/semantic_layer/compiler/duckdb.py`, `src/semantic_layer/control.py`, `src/semantic_layer/data_generation.py`, `src/semantic_layer/demo.py`, `src/semantic_layer/demo_sap.py`, `src/semantic_layer/governance/__init__.py`, `src/semantic_layer/governance/policy.py`, `src/semantic_layer/kg/__init__.py`, `src/semantic_layer/lineage/__init__.py`, `src/semantic_layer/lineage/service.py`, `src/semantic_layer/models.py`, `src/semantic_layer/provenance/__init__.py`, `src/semantic_layer/provenance/store.py`, `src/semantic_layer/quality/__init__.py`, `src/semantic_layer/quality/checks.py`, `src/semantic_layer/query_planner/__init__.py`, `src/semantic_layer/query_planner/service.py`, `src/semantic_layer/registry/__init__.py`, `src/semantic_layer/registry/service.py`, `src/semantic_layer/research/__init__.py`, `src/semantic_layer/resolver/__init__.py`, `src/semantic_layer/resolver/service.py`, `examples/README.md`, `examples/example_questions.md`, `examples/generated_query_plans/primary_erp_plan.json`, `examples/generated_sql/README.md`, `examples/generated_sql/databricks.sql`, `examples/generated_sql/microsoft-fabric.sql`, `examples/generated_sql/snowflake.sql`, `mappings/databricks/france.yaml`, `mappings/fabric/germany.yaml`, `mappings/snowflake/united_kingdom.yaml`, `data_products/acdoca_financials.yaml`, `data_products/billing_analytics.yaml`, `data_products/business_partners.yaml`, `data_products/sales_orders.yaml`.
- Coordination: T3 owns the first namespace migration in the four `data_products/*.yaml` files; T10 edits those same files only after T3, for ownership/certification wording. T4/T5/T6/T8 own their AQR Python files; T10 scans them and records any wording defect for the owning task instead of editing concurrently.
- Test: `tests/unit/test_claim_scan.py`

**Interfaces:**
- Consumes: Task 3 neutral identifiers, Task 8 condition names, and Task 9 asset-validation output.
- Produces: `scan_claim_surfaces(paths: Sequence[Path]) -> list[str]` that rejects SAP ownership/publication/certification, production/cloud/partnership, fake Vector RAG, hallucination guarantee, and solved-PhD language; all adapters/examples/mappings/data products explicitly say `repository-maintained synthetic contract`, `illustrative mapping`, or `unexecuted simulation` where applicable. The legacy-URI control allowlist is exactly `docs/superpowers/specs/2026-09-19-cifre-research-prototype-hardening-design.md`, `docs/superpowers/plans/2026-09-19-cifre-research-prototype-hardening.md`, and `docs/research/cifre-hardening-baseline.md`; every other scanned file must be clean. This task does not edit README or Markdown docs; T11 owns those exact files.

- [ ] **Step 1: Write the failing scan test.** Add `test_code_examples_mappings_and_data_products_have_supported_claims`; pass the exact file list above to `scan_claim_surfaces` and assert it reports current ownership/platform/certification claims while excluding only the three named control documents and preserving neutral namespace identifiers. Add a fixture assertion that any forbidden legacy URI in a non-control file is reported.
- [ ] **Step 2: Verify failure.** Run `pytest tests/unit/test_claim_scan.py -q`; expected: failures identify unsupported text in adapters, demos, generated SQL/plan examples, mappings, and data-product YAML.
- [ ] **Step 3a: Sanitize adapter, agent, API, and compiler source claims.** Modify exactly `src/semantic_layer/__init__.py`, `src/semantic_layer/adapters/__init__.py`, `src/semantic_layer/adapters/cloud.py`, `src/semantic_layer/adapters/duckdb.py`, `src/semantic_layer/agents/__init__.py`, `src/semantic_layer/agents/workflow.py`, `src/semantic_layer/api/__init__.py`, `src/semantic_layer/api/app.py`, `src/semantic_layer/compiler/__init__.py`, `src/semantic_layer/compiler/base.py`, `src/semantic_layer/compiler/cloud_examples.py`, and `src/semantic_layer/compiler/duckdb.py`; describe DuckDB/FastAPI/cloud adapters as local or simulated, remove ownership/production/certification promises, and preserve callable behavior. Run `PYTHONPATH=src .venv/bin/python -m compileall -q src/semantic_layer/__init__.py src/semantic_layer/adapters src/semantic_layer/agents src/semantic_layer/api src/semantic_layer/compiler`; expected: syntax passes with no API implementation change.
- [ ] **Step 3b: Sanitize the remaining non-AQR source claims.** Modify exactly `src/semantic_layer/control.py`, `src/semantic_layer/data_generation.py`, `src/semantic_layer/demo.py`, `src/semantic_layer/governance/__init__.py`, `src/semantic_layer/governance/policy.py`, `src/semantic_layer/lineage/__init__.py`, `src/semantic_layer/lineage/service.py`, `src/semantic_layer/models.py`, `src/semantic_layer/provenance/__init__.py`, `src/semantic_layer/provenance/store.py`, `src/semantic_layer/quality/__init__.py`, `src/semantic_layer/quality/checks.py`, `src/semantic_layer/registry/__init__.py`, `src/semantic_layer/registry/service.py`, `src/semantic_layer/resolver/__init__.py`, and `src/semantic_layer/resolver/service.py`; replace unsupported production/partnership/certification wording with the exact synthetic/local phrases while keeping data and policy semantics unchanged. Run `PYTHONPATH=src .venv/bin/python -m compileall -q src/semantic_layer/control.py src/semantic_layer/data_generation.py src/semantic_layer/demo.py src/semantic_layer/governance src/semantic_layer/lineage src/semantic_layer/models.py src/semantic_layer/provenance src/semantic_layer/quality src/semantic_layer/registry src/semantic_layer/resolver` and `pytest tests/unit/test_quality.py -q`; expected: syntax and quality behavior pass.
- [ ] **Step 3c: Scan AQR-owned source without editing another task’s files.** Run `scan_claim_surfaces` over `src/semantic_layer/demo_sap.py`, `src/semantic_layer/kg/__init__.py`, `src/semantic_layer/query_planner/__init__.py`, `src/semantic_layer/query_planner/service.py`, and `src/semantic_layer/research/__init__.py`; if a wording defect is found, record it for T3/T5/T6/T8 and leave that file unchanged. This preserves the T3/T5/T6/T8 ownership boundaries before the examples pass.
- [ ] **Step 4a: Sanitize generated examples.** Modify exactly `examples/README.md`, `examples/example_questions.md`, `examples/generated_query_plans/primary_erp_plan.json`, `examples/generated_sql/README.md`, `examples/generated_sql/databricks.sql`, `examples/generated_sql/microsoft-fabric.sql`, and `examples/generated_sql/snowflake.sql`; label all platform outputs as unexecuted simulations, replace unsupported ownership/certification language, and update only remaining legacy namespace literals. Run `python -m json.tool examples/generated_query_plans/primary_erp_plan.json`; expected: valid JSON and no example claim failure.
- [ ] **Step 4b: Sanitize mapping claims.** Modify exactly `mappings/databricks/france.yaml`, `mappings/fabric/germany.yaml`, and `mappings/snowflake/united_kingdom.yaml`; retain mapping keys and values, add `illustrative mapping` wording, and do not imply a platform connection or certification. Parse each file with the project YAML loader; expected: valid YAML with unchanged mapping structure.
- [ ] **Step 4c: Sanitize data-product claims after T3’s namespace pass.** Modify exactly `data_products/acdoca_financials.yaml`, `data_products/billing_analytics.yaml`, `data_products/business_partners.yaml`, and `data_products/sales_orders.yaml`; preserve neutral IRIs and describe each as a `repository-maintained synthetic contract`, removing ownership/publication/certification language. Run `pytest tests/unit/test_claim_scan.py -q`; expected: the complete T10 claim test passes before T11 publication files are touched.
- [ ] **Step 5: Verify scoped claims.** Run `pytest tests/unit/test_claim_scan.py -q` (expected PASS), then `pytest tests/unit/test_quality.py tests/semantic/test_mappings.py -q`; expected PASS. Do not run the full claim scan or full pytest gate yet.
- [ ] **Step 6: Commit and review.** `git add src/semantic_layer/__init__.py src/semantic_layer/adapters/__init__.py src/semantic_layer/adapters/cloud.py src/semantic_layer/adapters/duckdb.py src/semantic_layer/agents/__init__.py src/semantic_layer/agents/workflow.py src/semantic_layer/api/__init__.py src/semantic_layer/api/app.py src/semantic_layer/compiler/__init__.py src/semantic_layer/compiler/base.py src/semantic_layer/compiler/cloud_examples.py src/semantic_layer/compiler/duckdb.py src/semantic_layer/control.py src/semantic_layer/data_generation.py src/semantic_layer/demo.py src/semantic_layer/demo_sap.py src/semantic_layer/governance/__init__.py src/semantic_layer/governance/policy.py src/semantic_layer/kg/__init__.py src/semantic_layer/lineage/__init__.py src/semantic_layer/lineage/service.py src/semantic_layer/models.py src/semantic_layer/provenance/__init__.py src/semantic_layer/provenance/store.py src/semantic_layer/quality/__init__.py src/semantic_layer/quality/checks.py src/semantic_layer/query_planner/__init__.py src/semantic_layer/query_planner/service.py src/semantic_layer/registry/__init__.py src/semantic_layer/registry/service.py src/semantic_layer/research/__init__.py src/semantic_layer/resolver/__init__.py src/semantic_layer/resolver/service.py examples/README.md examples/example_questions.md examples/generated_query_plans/primary_erp_plan.json examples/generated_sql/README.md examples/generated_sql/databricks.sql examples/generated_sql/microsoft-fabric.sql examples/generated_sql/snowflake.sql mappings/databricks/france.yaml mappings/fabric/germany.yaml mappings/snowflake/united_kingdom.yaml data_products/acdoca_financials.yaml data_products/billing_analytics.yaml data_products/business_partners.yaml data_products/sales_orders.yaml tests/unit/test_claim_scan.py && git commit -m "docs: sanitize code and example claims"`. Reviewer checks every non-publication surface is covered and no T3/T4/T5/T6/T8 file was edited concurrently.

### Task 11: Sanitize README and public documentation with federated-secondary positioning

**Files:**
- Modify exactly: `README.md`, `pyproject.toml:5-15`, `docs/agent-architecture.md`, `docs/architecture.md`, `docs/data-products.md`, `docs/decisions/ADR-001-canonical-group-model.md`, `docs/decisions/ADR-002-semantic-assets-in-git.md`, `docs/decisions/ADR-003-ontology-runtime-boundary.md`, `docs/decisions/ADR-004-typed-query-plans.md`, `docs/decisions/ADR-005-platform-compilation-boundary.md`, `docs/decisions/ADR-006-duckdb-local-demo.md`, `docs/decisions/ADR-007-deterministic-core.md`, `docs/decisions/ADR-008-certified-data-products.md`, `docs/evaluation.md`, `docs/federated-semantics.md`, `docs/governance.md`, `docs/implementation-plan.md`, `docs/ontology.md`, `docs/semantic-layer.md`.
- Test: `tests/unit/test_documentation_contract.py` (publication-surface tests owned here)

**Interfaces:**
- Consumes: Task 9 asset-validation output and Task 10 `scan_claim_surfaces`; no final benchmark numbers or checked-in result artifact exist yet.
- Produces: a first-screen README with the exact disclaimer, labels `Implemented locally`, `Synthetic/simulated`, `Proposed future work`, and `Not implemented`; package description `Independent synthetic semantic-layer and knowledge-graph research prototype`; all listed docs using current/proposed boundaries; and a federated ERP section after the AQR reproducibility section explicitly marked secondary. T11 validates only artifact-independent wording/fence contracts; T13 resolves links to the canonical artifact after it exists. This task does not edit the research proposal, interview brief, baseline, or verification report; T12 owns those exact files.

- [ ] **Step 1: Write the failing publication test.** Add `test_publication_claim_contract_and_links`; assert the disclaimer precedes the first research heading and benchmark command, README primary/secondary order, four status labels, exact package description terms/no affiliation or production claim, and that required Markdown link text is present without resolving any link. Permit the README’s `results/latest_benchmark.json` link text before T13 creates the artifact; T13 owns all eventual link-resolution assertions.
- [ ] **Step 2: Verify failure.** Run `pytest tests/unit/test_documentation_contract.py::test_publication_claim_contract_and_links -q`; expected: current README/package/docs fail with opening affiliation, fake Vector RAG, ownership, certification, and unsupported production language.
- [ ] **Step 3a: Rewrite the README and primary architecture pages.** Modify exactly `README.md`, `docs/agent-architecture.md`, `docs/architecture.md`, `docs/data-products.md`, and `docs/evaluation.md`; put the exact Spec §4 disclaimer before the first research heading/benchmark command, present synthetic KG/AQR as the primary implemented path, label future work and non-implemented integrations, and remove ownership, certification, production, superiority, and hallucination guarantees. Run only the artifact-independent Markdown fence check on these five files; expected: fences are valid and the disclaimer is first. Defer all link resolution, including the artifact link, to T13 after canonical generation.
- [ ] **Step 3b: Rewrite ADR claims without changing decisions.** Modify exactly `docs/decisions/ADR-001-canonical-group-model.md`, `docs/decisions/ADR-002-semantic-assets-in-git.md`, `docs/decisions/ADR-003-ontology-runtime-boundary.md`, `docs/decisions/ADR-004-typed-query-plans.md`, `docs/decisions/ADR-005-platform-compilation-boundary.md`, `docs/decisions/ADR-006-duckdb-local-demo.md`, `docs/decisions/ADR-007-deterministic-core.md`, and `docs/decisions/ADR-008-certified-data-products.md`; retain each decision and consequence, but recast unsupported ownership/certification/production language as evidence-linked current behavior or proposed work. Run only the artifact-independent Markdown fence check on the ADR group; expected: fences are valid and no unsupported status claim remains. Defer all link resolution to T13.
- [ ] **Step 3c: Rewrite secondary positioning and implementation docs.** Modify exactly `docs/federated-semantics.md`, `docs/governance.md`, `docs/implementation-plan.md`, `docs/ontology.md`, and `docs/semantic-layer.md`; update neutral namespace literals, place federated ERP after the AQR reproducibility material as explicitly secondary, and mark cloud/platform connections as unexecuted simulations or future work. Run only the artifact-independent Markdown fence check on this group; expected: fences are valid, with link resolution deferred to T13.
- [ ] **Step 4: Update package metadata and artifact-independent wording.** Set the exact pyproject description; label cloud/platform adapters in docs as unexecuted simulations; preserve ADR intent while correcting ownership and implementation-status language. Run the named artifact-independent publication test only (expected PASS); defer the full documentation/link suite and artifact-link resolution to T13.
- [ ] **Step 5: Commit and review.** `git add README.md pyproject.toml docs/agent-architecture.md docs/architecture.md docs/data-products.md docs/decisions/ADR-001-canonical-group-model.md docs/decisions/ADR-002-semantic-assets-in-git.md docs/decisions/ADR-003-ontology-runtime-boundary.md docs/decisions/ADR-004-typed-query-plans.md docs/decisions/ADR-005-platform-compilation-boundary.md docs/decisions/ADR-006-duckdb-local-demo.md docs/decisions/ADR-007-deterministic-core.md docs/decisions/ADR-008-certified-data-products.md docs/evaluation.md docs/federated-semantics.md docs/governance.md docs/implementation-plan.md docs/ontology.md docs/semantic-layer.md tests/unit/test_documentation_contract.py && git commit -m "docs: position CIFRE prototype claims"`. Review reads the first screen without source access and confirms current/proposed/not-implemented boundaries.

### Task 12: Rewrite proposal, interview brief, and verification report

**Files:**
- Modify exactly: `docs/research/cifre_phd_proposal.md`, `docs/verification-report.md`, `docs/research/cifre-hardening-baseline.md` only to append final handoff pointers without changing its historical evidence.
- Create: `docs/research/cifre-interview-brief.md`, `docs/research/technical_design_and_research_questions.md`
- Test: `tests/unit/test_documentation_contract.py` (research-handoff tests owned here)

**Interfaces:**
- Consumes: Task 11 public wording and Task 9 command/validation paths; the final artifact is still generated only by T13.
- Produces: proposal sections for motivation/questions, implemented baseline, deterministic architecture/limitations, controlled protocol, future LLM/vector/hybrid hypotheses, privacy/provenance/human evaluation, risks/falsifiable outcomes, three-year research directions, explicit independent-candidate disclaimer, and non-goals; `docs/research/technical_design_and_research_questions.md` with the exact current data flow, typed interfaces, five research questions, hypotheses, falsifiable measures, and current/proposed boundaries; interview brief with five source-verifiable statements, a reproducibility command, metric fields explicitly sourced from the T13 artifact, limitations, and no-affiliation statement; and verification report fields for commit, hashes, commands, lock, environment, and known limitations.

- [ ] **Step 1: Write the failing handoff tests.** Add `test_research_handoff_contract_and_links`; assert the proposal contains all required research sections and independent disclaimer, the brief contains `cifre-synthetic-aqr-v1`, `results/latest_benchmark.json`, `make PYTHON=.venv/bin/python research-verify`, five source-link strings, and no-affiliation wording, and the verification report contains explicit commit/hash/command/lock/environment/limitation fields. Check link syntax/text only; do not resolve the not-yet-created artifact. Leave exact metric values for T13 to fill from the final artifact.
- [ ] **Step 2: Write the handoff documents.** Update remaining namespace literals in the exact research files, rewrite `docs/research/cifre_phd_proposal.md`, create `docs/research/technical_design_and_research_questions.md` and `docs/research/cifre-interview-brief.md`, and refresh `docs/verification-report.md` with evidence fields but no invented metric values; retain `docs/research/cifre-hardening-baseline.md` as historical evidence and add only a pointer to the final report.
- [ ] **Step 3: Verify the handoff scope.** Run `pytest tests/unit/test_documentation_contract.py::test_research_handoff_contract_and_links -q`; expected: PASS for section/disclaimer/link-text shape without filesystem link resolution, while exact metric fields remain explicitly pending T13.
- [ ] **Step 4: Commit and review.** `git add docs/research/cifre_phd_proposal.md docs/research/technical_design_and_research_questions.md docs/research/cifre-interview-brief.md docs/verification-report.md docs/research/cifre-hardening-baseline.md tests/unit/test_documentation_contract.py && git commit -m "docs: add CIFRE research handoff"`. Review independently traces each brief statement and each research question to source/tests and confirms no claim of final metrics is made before T13.

### Task 13: Final claim/secret/format audit, canonical result, and full verification gate

**Files:**
- Create/replace only: `results/latest_benchmark.json`
- Modify after T12: `docs/research/cifre-interview-brief.md`, `docs/verification-report.md`, `Makefile:7-38`, `.github/workflows/ci.yml:5-20`, `tests/unit/test_final_readiness.py`
- Test: `tests/unit/test_final_readiness.py`

**Interfaces:**
- Consumes: all prior task commits, the complete Spec §26.6 manifest, final public docs, proposal, interview brief, verification report, lock, migration manifest, and Task 9’s reusable final-mode verifier. The claim scan is the union of the exact T3, T10, T11, and T12 file lists plus `README.md`, and excludes only these three control documents that quote forbidden strings normatively: `docs/superpowers/specs/2026-09-19-cifre-research-prototype-hardening-design.md`, `docs/superpowers/plans/2026-09-19-cifre-research-prototype-hardening.md`, and `docs/research/cifre-hardening-baseline.md`.
- Produces: `finalize_research_artifact(root: Path) -> Path`, which calls `write_result_artifact` only after the final manifest is built; final exact metrics/hashes in the interview brief and verification report sourced from a temporary run; a clean branch with no forbidden claims/secrets/legacy IRIs/placeholder markers, valid Markdown/Mermaid/links/YAML/JSON/Turtle, and a result artifact whose `hash_manifest` matches every final input byte.

- [ ] **Step 1: Write failing final-gate tests.** Add `test_final_hash_manifest_covers_complete_spec_26_6_scope` and `test_final_claim_and_secret_scan_is_clean`. The manifest test must expand exactly this ordered Spec §26.6 list, sort the complete paths bytewise, remove duplicates, keep only tracked files, and exclude `.git/`, `.venv/`, `results/latest_benchmark.json`, and the artifact itself:

  ```python
  spec_26_6_globs = [
      ".github/workflows/ci.yml", "Makefile", "pyproject.toml", "constraints/py312.txt",
      "scripts/**/*.py", "semantic/**/*.ttl", "semantic/**/*.yaml", "semantic/**/*.json",
      "src/semantic_layer/**/*.py", "data/**/*.py", "tests/**/*.py", "tests/**/*.yaml",
      "tests/**/*.json", "examples/**/*", "README.md", "docs/**/*.md", "docs/**/*.json",
      "docs/**/*.sql", "mappings/**/*.yaml", "data_products/**/*.yaml", "results/**/*.json",
      "results/**/*.sql",
  ]
  tracked_paths = set(subprocess.check_output(
      ["git", "ls-files", "-z"], cwd=root
  ).decode().split("\0"))
  expected_paths = sorted({
      relative
      for pattern in spec_26_6_globs
      for path in root.glob(pattern)
      if path.is_file()
      for relative in (path.relative_to(root).as_posix(),)
      if relative in tracked_paths
      and relative != "results/latest_benchmark.json"
      and ".git/" not in f"{relative}/" and ".venv/" not in f"{relative}/"
  })
  assert artifact["hash_manifest"]["paths"] == expected_paths
  for relative in (".github/workflows/ci.yml", "constraints/py312.txt",
                   "scripts/research_verify.py", "tests/unit/test_final_readiness.py",
                   "src/semantic_layer/research/benchmark_runner.py",
                   "docs/verification-report.md",
                   "mappings/databricks/france.yaml"):
      mutated = copy_repo_and_change_one_byte(root, relative)
      assert build_hash_manifest(mutated) != artifact["hash_manifest"]
  ```

  The claim/secret test must assert that the three control documents are the only legacy-URI exceptions and that unsupported claims, credential patterns, and placeholder markers fail closed.
- [ ] **Step 2: Run only explicitly named artifact-independent pre-artifact checks.** Run only `pytest tests/unit/test_documentation_contract.py::test_publication_claim_contract_and_links tests/unit/test_documentation_contract.py::test_research_handoff_contract_and_links -q`; these tests must check wording, ordering, required source links, and required artifact-link text without resolving `results/latest_benchmark.json`. Then run the claim/secret/format checks and this legacy-URI scan with exactly the three control exclusions:

  ```bash
  rg -n -i 'help\.sap\.com|http://ontology\.sap\.com|http://data\.sap\.com|https://sap\.example/erp/' . \
    --glob '!docs/superpowers/specs/2026-09-19-cifre-research-prototype-hardening-design.md' \
    --glob '!docs/superpowers/plans/2026-09-19-cifre-research-prototype-hardening.md' \
    --glob '!docs/research/cifre-hardening-baseline.md'
  ```

  Also run `gitleaks detect --source . --no-banner --redact`, the repository placeholder-marker scan, and JSON/YAML/Turtle parsers; expected: zero matches/errors elsewhere. Do not run the full `tests/unit/test_documentation_contract.py` suite, any Markdown/Mermaid/link-resolution suite, final readiness tests, or result-artifact tests, and do not create `results/latest_benchmark.json`.
- [ ] **Step 3: Add final Makefile/CI wiring and verify only static target configuration.** Add the `research-verify` target and CI invocation, then run only the static Makefile/YAML assertions from `tests/unit/test_final_readiness.py` (for example, `pytest tests/unit/test_final_readiness.py -q -k 'make_target or ci_workflow'`). Do not run the final readiness or artifact tests before the canonical artifact exists.
- [ ] **Step 4: Generate, use, and remove temporary final metrics in one shell.** Keep the following as one shell block; the documentation copy/use and cleanup must happen before the block exits:

  ```bash
  cifre_tmp_dir="$(mktemp -d)"
  trap 'rm -rf -- "$cifre_tmp_dir"' EXIT
  PYTHONPATH=src .venv/bin/python -m semantic_layer.research \
    --output "$cifre_tmp_dir/final-cifre-metrics.json"
  jq -e '.corpus_runs and (.corpus_runs | length == 2)' \
    "$cifre_tmp_dir/final-cifre-metrics.json" >/dev/null
  # In this same shell, copy the exact aggregate metrics, corpus/graph/lock
  # hashes, command, and known limitations from the JSON above into both
  # docs/research/cifre-interview-brief.md and docs/verification-report.md.
  # Record the pre-commit source revision used for this run, never a guessed
  # future commit, then run only the two named artifact-independent contracts.
  pytest tests/unit/test_documentation_contract.py::test_publication_claim_contract_and_links \
    tests/unit/test_documentation_contract.py::test_research_handoff_contract_and_links -q
  git diff --check
  rm -rf -- "$cifre_tmp_dir"
  test ! -e "$cifre_tmp_dir"
  trap - EXIT
  ```

  Expect schema-valid v1/v2/two-condition data used only as documentation evidence; do not write `results/latest_benchmark.json` in this block. No later step or shell references `cifre_tmp_dir`.
- [ ] **Step 5: Generate the canonical artifact, then run the complete publication/link gate.** Run `PYTHONPATH=src .venv/bin/python -m semantic_layer.research --output results/latest_benchmark.json`; then run `pytest tests/unit/test_final_readiness.py tests/research/test_result_artifact.py -q`, the full `pytest tests/unit/test_documentation_contract.py -q` suite, and the complete Markdown/Mermaid/link-resolution checks, including resolution of every `results/latest_benchmark.json` link. Expected: canonical UTF-8 result, exact two corpus runs/two conditions, complete per-query records, complete Spec §26.6 hash manifest, and no broken publication or artifact links.
- [ ] **Step 6: Run the final readiness and full verification gate.** Run `make PYTHON=.venv/bin/python research-verify`, `pytest -q`, and `.venv/bin/python -m ruff check .`; expected: all exit 0, final code/docs hashes, expected negative controls, full claim scan, and report/artifact agreement. This is the first successful post-publication gate.
- [ ] **Step 7: Commit the canonical artifact and final docs, then audit.** `git add results/latest_benchmark.json docs/research/cifre-interview-brief.md docs/verification-report.md Makefile .github/workflows/ci.yml tests/unit/test_final_readiness.py && git commit -m "chore: record final CIFRE benchmark artifact"`.
- [ ] **Step 8: Run the final read-only audit.** Rerun `make PYTHON=.venv/bin/python research-verify`, `git status --short`, `git diff --check`, and `git log --oneline --decorate -20`; confirm no temporary directory remains, no untracked artifact is omitted, and no external GitHub state changed. A fresh reviewer signs the branch; do not push.

## Plan Self-Review

- **Spec coverage:** T1 baseline inventory; T2 lock/provenance/root schema; T3 namespace migration, SKOS/OWL split, datatypes, fixtures; T4 exact grammar/abstention; T5 dedicated AQR planner/closure/projection contract; T6 statuses/repair/relaxation/provenance plus `demo_sap.py` and integration consumer; T7 historical/v1/v2 migration manifest and exact fields/enums; T8 exact/status-gated metrics, composite result-ID validator, and temporary artifact only; T9 parity/SHACL/asset helpers; T10 complete non-publication code/examples/mappings/data-product claim surface; T11 exact README/docs/ADR/package and federated-secondary positioning; T12 proposal/interview/report; T13 final CI wiring, scans, canonical result generation, full research-verify/claim/pytest/lint gate.
- **Placeholder scan:** Every implementation behavior in this plan names a path, interface, focused test, command, and expected outcome; the final audit explicitly scans placeholder markers and secrets.
- **Type consistency:** `NAMESPACE_REGISTRY`, `Status`, `ReasonCode`, `GroundedEntities`, `LogicalQueryPlan`, `ReasoningResult`, `BenchmarkRunner`, and `VerificationReport` are introduced before consumers; condition/status/reason names match the spec tables and result schema.
- **Shared-file sequencing:** `tests/unit/test_documentation_contract.py` is split between T11 publication tests and T12 handoff tests; `tests/unit/test_claim_scan.py` is T10; `tests/unit/test_aqr_query_planner.py` is T5; asset validation helpers are T9, while `Makefile`/CI final wiring is T13; `pyproject.toml` dependency declaration is T2 and description T11; `data_products/*.yaml` namespace edits are T3 then claim edits T10; `results/latest_benchmark.json` is temporary in T8 and generated/committed only by T13 after T12; no parallel wave edits these files.
- **Ownership mapping:** T3 owns every listed synthetic TTL/YAML and generator/loader consumer; T4 owns grammar/linker; T5 owns planner/compiler and the dedicated planner test; T6 owns repair plus `demo_sap.py` typed consumers; T7 owns migration script/corpora/manifest; T8 owns runner/metrics/schema consumers but no canonical result; T9 owns local asset validation only; T10 owns claim edits for the non-AQR source/example/mapping/data-product list and performs scan-only checks on T3/T5/T6/T8-owned AQR files; T11 owns the exact README/public-doc/ADR/package list; T12 owns proposal/technical-design/interview/report; T13 owns final Makefile/CI wiring, final scans, and canonical result. No task uses a broad staging command.
- **Decomposition:** T3 separates runtime producers, ontology/shape assets, and generated-data consumers with focused tests; T10 separates source groups, scan-only AQR ownership checks, examples, mappings, and data products; T11 separates primary README/docs, ADRs, and secondary-positioning docs; T11 runs only artifact-independent wording/fence checks, while T13 runs the full documentation/link/artifact-link gate after Step 5; T13 keeps temporary generation, documentation use, cleanup, and trap removal in one shell block before canonical generation.
- **Feasibility:** Each task has bite-sized failing-test/minimal-pass/verification/commit steps and an independent review gate. T3/T4 are the only parallel wave and have disjoint implementation/test files. Full `research-verify`, full claim scan, canonical artifact hash, and full pytest are explicitly deferred to T13 after all docs and claims are final.
