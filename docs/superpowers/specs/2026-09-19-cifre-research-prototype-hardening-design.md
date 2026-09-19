# CIFRE Research Prototype Hardening Design

**Date:** 2026-09-19  
**Status:** Approved architectural direction; implementation plan follows after review  
**Audience:** Researchers, interviewers, reviewers, and engineers evaluating or extending this independent prototype  
**Scope:** The synthetic Support/PPMS knowledge-graph and Autonomous Query Reasoning (AQR) research pillar, plus the repository claims and verification artifacts that describe it

## 1. Intent and success criterion

This repository is an independent, unaffiliated candidate prototype inspired by
the research themes in SAP Labs France CIFRE Requisition 452538. It must make
two things easy to see:

1. A researcher can reproduce and inspect a deterministic symbolic baseline for
   synthetic enterprise-support questions.
2. A credible future research programme can introduce learned language
   understanding, retrieval, and agentic reflection as controlled experiments.

The repository must not imply an SAP employment, partnership, endorsement,
access to SAP internal systems, completed doctoral research, or solved PhD
problem. A successful revision lets an interview reviewer distinguish, without
reading implementation internals, what is implemented locally, what is
synthetic or simulated, what is proposed future work, and what has not been
evaluated.

The primary success criterion is an evidence-first research handoff: a fresh
checkout can regenerate or load the same graph, validate its semantic
contracts, run the benchmark, inspect per-query outcomes and input hashes,
and run the tests from one documented command. A claim in README, proposal,
benchmark output, package metadata, or verification report must be traceable to
an executable check or be labelled as a proposal.

## 2. Evidence discovered in the current repository

The following is the baseline to preserve and then correct. It is a repository
observation, not a claim about SAP systems or external research.

### 2.1 Current AQR execution path

The current support/PPMS AQR implementation is deterministic:

```text
fixed-vocabulary text matching
  -> GroundedEntities
  -> typed LogicalQueryPlan
  -> deterministic SPARQL compilation
  -> RDFLib graph execution
  -> bounded heuristic repair/relaxation
  -> answer synthesized only from returned bindings
```

The relevant implementation is in `schema_linker.py`, `query_planner.py`,
`text_to_sparql.py`, `kg/loader.py`, and `reflective_agent.py`. The linker has
finite component, alert, product-version, software-component, support-package,
note-number, and priority vocabularies. The planner emits typed triple
patterns, the compiler emits deterministic SPARQL, and the loader executes
locally with RDFLib. The current repair loop is bounded and heuristic: it can
remove a support-package bound or widen a component to a parent after an empty
result, and it has a simple prefix repair path for execution exceptions.

There is no LLM call, embedding model, vector index, vector retriever, or
neural baseline in the current code. The proposal and README currently use
neurosymbolic/LLM language that describes an intended research direction more
strongly than the implementation supports. The hardening work must preserve
the deterministic baseline while making the proposed learned components an
explicit future interface.

### 2.2 Current benchmark and documentation evidence

The repository contains a 40-query synthetic corpus at
`tests/research/benchmark_dataset.yaml`, partitioned into five eight-query
tiers. The current `BenchmarkRunner` reports three paradigms, but its Vector
RAG branch is a hard-coded conditional on query text and tier; it does not
retrieve chunks or run a vector system. It therefore cannot be reported as a
Vector RAG result and must be removed from the measured comparison.

The current one-shot branch runs the same deterministic linker, planner, and
compiler with reflection disabled. It should be named a deterministic
no-reflection ablation, not a text-generation baseline. The current AQR check
uses subset correctness, so an answer with extra notes can be counted as
correct. The report also exposes VSR, hallucination, and broad comparative
claims that are not supported by independently implemented systems or a
defined hallucination annotation protocol.

The benchmark corpus itself has data-integrity defects that the redesign must
surface and resolve, including expected-answer policy that does not always
match strict query semantics, reflection labels that assume a successful
relaxation, and a need for negative/unsupported cases. Existing entries are
retained as a versioned synthetic starting corpus; they are not silently
rewritten into evidence for a new result.

### 2.3 Current semantic and verification evidence

The latest recorded local verification in `docs/verification-report.md` reports
218 pytest tests passing (with two third-party deprecation warnings), Ruff
passing, semantic validation passing, and the 40-query research command
completing. These are the current recorded checks to use as a before/after
baseline; historical verification is not a substitute for rerunning the
post-change command.

The current assets mix claimed SAP-oriented IRIs (`http://ontology.sap.com/*`,
`http://data.sap.com/*`) with explicitly synthetic ERP assets
(`https://sap.example/erp/`). The first group can be read as official
namespace ownership even though the repository has no such authority. The
support and PPMS models also have these semantic issues:

- Language-tagged titles are emitted as `rdf:langString`, while the support
  ontology declares `sap:title` with range `xsd:string`; the shape works around
  this with an `sh:or` instead of making the contract coherent.
- The ERP vocabulary uses SKOS concepts and the ERP ontology uses OWL classes
  with overlapping local names and IRIs, including `ProductAutomotive`.
  A taxonomy concept is not automatically an instance/class in the ontology.
- Prerequisite traversal is modelled as an OWL transitive property, but the
  planner currently asks only for one direct `hasPrerequisiteNote` edge and
  returns a select variable (`?prereqTitle`) that has no binding pattern.
- SHACL validation is partial: the support shapes validate the loaded support
  graph, while the repository also contains ERP shapes and graph fixtures with
  separate validation paths. A successful partial validation must not be
  described as complete graph conformance.
- The generated support graph and checked-in Turtle artifact need an explicit
  graph-isomorphism parity check; textual serialization equality is not a
  semantic guarantee.

## 3. Decision: evidence-first hardening

The chosen approach is **evidence-first hardening**. It makes the local
symbolic system precise and reproducible, removes unsupported comparisons and
claims, and creates narrow interfaces for future learned experiments.

Two alternatives are rejected:

* **Docs-only correction:** Updating prose while leaving fake Vector RAG
  numbers, ambiguous namespaces, weak result semantics, and unreproducible
  artifacts would preserve the evidence problem.
* **Superficial LLM/vector dependencies:** Adding an SDK, embedding package,
  or nominal adapter without a controlled dataset, run protocol, cost and
  failure accounting, and a real executed baseline would create a dependency
  theatre rather than research evidence. No external model or vector service
  is added in this revision.

The hardening implementation is allowed to change interfaces and test
fixtures where required for truthful semantics. It is not allowed to claim
that a future LLM experiment has already happened.

## 4. Independent disclaimer and current-versus-proposed contract

The README, proposal, package metadata, benchmark metadata, and research
verification report must use a consistent disclaimer near the first research
claim:

> This is an independent, unaffiliated candidate prototype using synthetic
> support and product-lifecycle fixtures. It is not an SAP product, SAP
> publication, SAP-endorsed benchmark, or report of access to SAP internal
> data. The repository demonstrates a deterministic symbolic baseline and
> proposes future LLM/retrieval experiments; it does not claim completed PhD
> research or production readiness.

Metadata uses the first sentence of this disclaimer plus
`independent_repository: true` and `official: false`; those fields preserve
the same meaning. “SAP” may describe the domain inspiration or names in
synthetic question text; it must not be used as an owner, publisher,
certification authority, or result sponsor.

The research contract is:

| Capability | Current, evidenced locally | Proposed future programme |
| --- | --- | --- |
| Graph | Checked-in synthetic RDF/Turtle support and PPMS fixtures | Controlled ingestion and provenance studies on approved datasets |
| Grounding | Fixed vocabulary and deterministic pattern matching | Evaluated learned entity linking with an explicit abstention policy |
| Planning | Typed deterministic logical plans | Neural or hybrid planning compared against the deterministic baseline |
| Query | Deterministic SPARQL 1.1 compilation and RDFLib execution | Additional stores, optimizers, or constrained learned query synthesis |
| Reflection | Bounded hand-written repair/constraint-relaxation heuristics | Learned diagnostic policies under a fixed budget and safety gate |
| Retrieval | Graph traversal only; no vector retriever | Real vector/graph retrieval baseline with independently implemented protocol |
| Answer | Derived from graph bindings and provenance identifiers | Natural-language generation constrained by binding evidence and evaluated for unsupported claims |
| Evaluation | Preliminary synthetic benchmark and regression metrics | Held-out, multi-source, human-reviewed research evaluation |

No current implementation may be described as an LLM, vector, production, or
official SAP integration. A future experiment must add its own method,
version, configuration, seed, dependency lock, run artifact, and failure
analysis before being compared.

## 5. Namespace and asset migration

### 5.1 Exact neutral namespace contract

All synthetic support and PPMS ontology, instance, shape, generator, loader,
planner, compiler, and test references must migrate to these exact IRIs:

| Prefix | IRI | Use |
| --- | --- | --- |
| `cifsup` | `https://example.org/cifre-kg/support#` | Synthetic support classes, properties, and predicates |
| `cifppms` | `https://example.org/cifre-kg/ppms#` | Synthetic PPMS classes, properties, and predicates |
| `cifdata` | `https://example.org/cifre-kg/data/` | Synthetic instance resources under exactly `support/`, `ppms/`, or `erp/` |
| `ciferp` | `https://example.org/cifre-kg/erp#` | Synthetic ERP OWL classes/properties currently represented by the `sap:` ERP namespace |
| `cifskos` | `https://example.org/cifre-kg/vocabulary#` | Synthetic SKOS concept schemes and concepts |
| `cifmeta` | `https://example.org/cifre-kg/meta#` | Synthetic-source, provenance, crosswalk, and result metadata predicates |
| `cifmetaid` | `https://example.org/cifre-kg/id/meta/` | Synthetic metadata instance resources |

`example.org` is used as a reserved documentation namespace. These IRIs are
not SAP IRIs and must be labelled as synthetic in ontology metadata. The
instance pattern is exactly
`https://example.org/cifre-kg/data/support/note/3109922` and
`https://example.org/cifre-kg/data/ppms/version/S4HANA_2023`; it must not
retain `data.sap.com` path names.

The prefixes are intentionally distinct: `cifsup:SAPNote` and
`cifppms:ProductVersion` are different domain terms, while `ciferp:Product`
and `cifskos:Product` are different semantic artefacts. Prefix labels may use
the domain shorthand `SAPNote` for synthetic question compatibility, but
metadata must state that these are fictional fixtures.

### 5.2 Migration rules and compatibility decision

Update every reference consistently, including:

- `semantic/ontology/sap_support.ttl`, `semantic/ontology/sap_ppms.ttl`,
  `semantic/data/sap_support_graph.ttl`, their generators, and support tests;
- `src/semantic_layer/kg/loader.py` and
  `src/semantic_layer/kg/sap_dataset_generator.py` namespace constants and
  generated resource IRIs;
- `src/semantic_layer/reasoning/text_to_sparql.py`, planner predicates,
  schema-linker contracts, and all SPARQL assertions;
- ERP ontology, vocabulary, taxonomy, shapes, data fixtures, data-product
  references, tests, and documentation where the same IRI family is used;
- serialized benchmark and result artifacts, if they include resource IRIs.

Compatibility aliases are explicitly excluded. Do not retain old prefixes,
`owl:sameAs`, `rdfs:seeAlso`, dual IRI emission, a compatibility parser, or
dual namespace bindings. Aliases would make old official-looking IRIs
appear supported, allow stale artifacts to pass unnoticed, and make benchmark
provenance ambiguous. Migration is a deliberate clean break: regenerate the
checked-in synthetic graph, update all consumers in the same implementation
task, and let old snapshots fail until migrated. Rollback is a Git revert of
the migration commit, not runtime aliasing.

## 6. Minimal semantic corrections

These corrections are required before interpreting benchmark numbers.

### 6.1 Language-tag range consistency

Choose language-tagged English literals for human-readable synthetic text.
Declare title, symptom, root-cause, resolution, component description,
category name, and human labels consistently as `rdf:langString` where they
are part of a domain contract. Shapes must use `sh:datatype rdf:langString`
and `sh:languageIn ("en")` for those fields. Machine identifiers, codes,
priorities, and status values remain `xsd:string`; counts and package bounds
retain numeric datatypes. Do not use an `sh:or` to conceal an ontology/data
contract mismatch. If a field is intentionally language-neutral, document it
and use `xsd:string` consistently instead.

### 6.2 Separate SKOS concepts from OWL classes

Keep the federated semantic layer's ERP ontology under `ciferp:` and its
product taxonomy under `cifskos:`. `cifskos:ProductAutomotive` is a
`skos:Concept`; `ciferp:ProductAutomotive` is an OWL class only if the ERP
ontology needs that class. They must not share an IRI merely because the
labels match. When a class is linked to a taxonomy concept, use the explicit
reviewed `cifmeta:CrosswalkEntry` mapping resource under the `cifmetaid:`
instance namespace, as defined in Section 21. The mapping is not an implicit
`rdf:type` assertion.

Tests must assert both that SKOS scheme structure is valid and that a SKOS
concept is not accidentally used as an OWL class/type. This preserves the
distinction between classification/navigation and instance semantics.

### 6.3 Prerequisite closure

Represent each asserted prerequisite as one direct
`cifsup:hasPrerequisiteNote` edge and do not depend on RDFLib RDFS inference
to compute closure. Compile a prerequisite request with an explicit SPARQL
property path:

```sparql
?targetNote cifsup:hasPrerequisiteNote+
            ?note .
```

Join `?note` to its note number and title, select only variables with a
pattern, and deduplicate deterministically. The `+` path returns direct and
transitive prerequisites without returning the target itself; a query asking
for direct prerequisites may use the single edge and must say so in its
intent. Add a cycle fixture and a bounded query result policy so a malformed
synthetic graph cannot cause an unbounded traversal.

### 6.4 Remove unbound projections

The prerequisite plan must not select `?prereqTitle` unless it emits a
binding pattern for that variable. Prefer selecting `?note`, `?noteNumber`,
and `?title` with the same names used by answer synthesis. Add a compiler
contract test that every projected variable is bound by a required or
optional pattern and that no row depends on RDFLib's treatment of unbound
variables.

### 6.5 Make partial SHACL validation explicit

The loader should report validation scope and result, not only a boolean. A
support-only validation of `sap_support_graph.ttl` after migration is a
`partial` validation of the support shapes; an ERP graph validated against ERP
shapes is a separate scope. The full verification command must invoke each
declared scope and report:

- graph path and SHA-256;
- shape path and SHA-256;
- `scope` (`support`, `erp`, or `combined`);
- `conforms`;
- whether inference was enabled;
- the expected result for valid and deliberately invalid fixtures.

Documentation must use “partial SHACL validation” unless every declared graph
and shape set has been run. Invalid fixtures are expected negative controls,
not failed builds, when their result is the documented non-conformance.

### 6.6 Generated/check-in graph isomorphism

Build the support graph in memory or a temporary output path, load both it and
the checked-in Turtle into RDFLib, and compare them with graph isomorphism
(including blank-node handling), not raw serialization. Fail the parity check
on missing or additional triples. Record both artifact hashes for audit, but
use isomorphism as the semantic acceptance test. The same policy applies to
any generated ERP fixture with a checked-in artifact.

## 7. AQR failure and result model

The implementation must expose a typed result contract with a closed status
set:

| Status | Meaning | Answer/result policy |
| --- | --- | --- |
| `SUCCESS` | The original grounded request compiled, executed, and returned bindings under its stated constraints | Return only binding-derived fields and provenance; mark `constraint_relaxed=false` |
| `UNSUPPORTED` | Unknown entity, unsupported grammar, ambiguous intent, or policy-denied capability | Return no guessed query or answer; include a stable reason code |
| `SYNTAX_ERROR` | SPARQL compilation/parsing failed after the bounded repair budget | Return no factual answer; preserve diagnostics and attempted queries |
| `EXECUTION_ERROR` | Graph/store execution failed for a valid or repaired query | Return no factual answer; preserve error class without leaking credentials or internals |
| `EMPTY_RESULT` | The original valid query executed and returned no bindings | Return an explicit no-match result for the original constraints; distinguish from unsupported |

Unknown and unsupported input must fail closed before inventing a URI,
capability, parent component, note, or product version. Ambiguous input (for
example two equally valid intents or an unrecognised spelling that is not in
the controlled vocabulary) maps to `UNSUPPORTED` with
`reason_code=AMBIGUOUS_INPUT` or `UNKNOWN_ENTITY`. The agent must not silently
choose a capability to make a benchmark answer look successful.

Each result records the original normalized request, grounded entities,
logical plan, final SPARQL, status, reason code, execution attempt count,
reflection history, bindings, citations, and `constraint_relaxed` metadata.
Error text is bounded and sanitized; a query string or RDF value must not be
treated as executable SQL or arbitrary code.

### 7.1 Constraint relaxation disclosure

Relaxation is a research action, not exact satisfaction of the original
request. A result must preserve:

- the original constraint set;
- each relaxation operation and order (remove the support-package bound, then
  widen a component);
- the relaxed query and its bindings;
- whether strict execution was empty;
- `answer_scope=relaxed` when a relaxed answer is shown.

If strict execution is empty and a relaxed query finds records, the final
status remains `EMPTY_RESULT` for the original request, with a separate
`relaxed_candidates` field. It must not become `SUCCESS`, and benchmark exact
set accuracy must score the strict result as empty/incorrect against the
original gold set. A UI or CLI may display relaxed candidates only after
clearly labelling them as candidates outside the requested constraints.

The repair budget remains finite and configurable (default three attempts).
Every attempted query is recorded; a repair that changes semantics without a
declared operation is a contract failure.

## 8. Controlled preliminary synthetic benchmark

The benchmark is renamed and reframed as a **controlled preliminary synthetic
benchmark**. It measures this repository's deterministic prototype over a
checked-in synthetic graph. It is not an SAP benchmark, a production-support
evaluation, or evidence that a method generalizes to real data.

### 8.1 Corpus retention and relabelling

Retain all 40 current questions as the initial corpus under the exact versioned
name `cifre-synthetic-aqr-v1`. Preserve stable IDs and the original text in
the first migration. Change metadata and labels as follows:

- remove the Vector RAG paradigm and every fabricated Vector RAG number;
- rename the one-shot condition to `deterministic_no_reflection_ablation`;
- name the reflective condition `deterministic_bounded_repair`;
- treat `requires_reflection` as an analysis hint, not a gold claim that a
  repair must succeed;
- add negative, unknown, ambiguous, unsupported, syntax, and strict-empty
  queries only in the separate v2 corpus defined in Section 23; v1 remains
  the original 40-query controlled corpus.

Do not delete the legacy expected answer. For every changed gold expectation,
record the before and after sets, a `migration_reason`, the graph query/policy
used to derive the new set, and reviewer sign-off in the checked-in migration
manifest defined in Section 27. Gold sets are justified by the current graph
and declared semantics: exact note identity, direct versus transitive
prerequisite scope, hierarchy policy, version policy, and strict versus
relaxed constraints. A changed gold value is not a regression failure when
the semantic policy and evidence explain the change; the migration report
must show the before/after diff.

### 8.2 Dataset integrity metadata

The dataset header must include a schema version, corpus name/version, graph
fixture identifier and SHA-256, namespace map, generator/runner version,
query count, tier/category counts, gold policy, and a statement that all
records are synthetic. A loader must reject duplicate IDs, incorrect declared
counts, missing required fields, unknown status/category values, malformed
gold note IDs, and a `requires_reflection` claim without a valid reason.

Each query record includes at least:

```yaml
id: Q01
question: "..."
category: single_hop_alert
gold_note_numbers: ["3345100"]
expected_status: SUCCESS
strict_constraints: true
gold_policy: exact_set
```

Negative records use an empty gold set only when the expected status and reason
are explicit; unsupported is not silently equivalent to a valid empty query.

### 8.3 Metrics and artifact contract

For each condition and for each query, record:

- predicted note-number set and gold note-number set;
- exact-set correctness (`predicted == gold`);
- set precision, recall, and F1;
- status and expected status;
- syntax validity and execution success;
- strict non-empty success;
- reflection/repair attempted, recovered, and budget used;
- whether a relaxation occurred and whether output is strict or relaxed;
- bounded diagnostics and provenance identifiers.

Aggregate metrics must include macro and micro precision/recall/F1, exact-set
accuracy, syntax-success rate, execution-success rate, strict empty-result
rate, unsupported rejection rate, and recovery-attempt/recovery-success rates.
Define both-empty precision/recall/F1 as 1.0, and one-empty/one-nonempty as
0.0, in the metric contract. Report metrics by tier/category and overall.

Do not report VSR, hallucination percentage, or comparative superiority in
the redesigned result. “Binding-derived” is a property of the answer path,
not a measured zero-hallucination guarantee. Any future unsupported-claim
annotation study needs a separate human-reviewed protocol and dataset.

The runner writes deterministic JSON to `results/latest_benchmark.json` with:

- schema and runner versions;
- dataset, ontology, graph, and code/config SHA-256 hashes;
- namespace map and graph/shape validation summary;
- condition definitions;
- aggregate metrics;
- the complete ordered `per_query` result list;
- run environment fields `python_version`, `platform_system`,
  `platform_machine`, `pip_version`, and the sorted locked package versions;
- no mutable wall-clock field in the content hash (a display-only run time may
  be kept outside the deterministic artifact).

The checked-in artifact is regenerated by the verification command and must
be reviewed whenever corpus, graph, planner, compiler, status model, or metric
logic changes. A result with mismatched input hashes is stale and must fail
the claim-contract test.

## 9. Reproducibility command and CI boundary

Provide one obvious local command:

```bash
make PYTHON=.venv/bin/python research-verify
```

The target performs, in order:

1. Generate the synthetic support/PPMS graph into a temporary directory and
   load it alongside the checked-in graph.
2. Assert generated/check-in graph isomorphism and report hashes.
3. Validate each declared SHACL scope, including expected valid and invalid
   fixtures, with partial/full scope labels.
4. Validate benchmark metadata and input hashes.
5. Run the v1 and v2 deterministic no-reflection and bounded-repair benchmarks,
   writing their `corpus_runs` entries to `results/latest_benchmark.json`.
6. Run claim-contract, research, semantic, and complete pytest checks.
7. Run Ruff and report a concise verification summary.

The command must use temporary generated files and must not silently replace
source fixtures. It should fail non-zero on namespace drift, graph parity
failure, unexpected SHACL outcome, stale result hash, benchmark schema error,
claim-contract violation, test failure, or lint failure.

CI runs this target in a dedicated `research-verify` job. If the measured
post-install execution exceeds 120 seconds, split the same steps into the
named `research-verify-assets` and `research-verify-benchmark` jobs without
removing any acceptance check. No cloud account, external endpoint, API key, model
download, or vector service is required in CI.

## 10. Documentation and claim sanitation

### 10.1 README information architecture

Reorder the README so the synthetic KG/AQR research prototype is the primary
story and the federated semantic layer is a secondary reference implementation:

1. independent disclaimer, scope, and implementation status;
2. synthetic KG, semantic contracts, AQR data flow, and reproducibility command;
3. preliminary benchmark methodology and artifact link;
4. deterministic limitations and proposed LLM/retrieval research programme;
5. federated ERP semantic layer as a separate secondary pillar;
6. local setup, testing, governance, and non-goals.

Remove the current opening affiliation, “ours,” solved-problem, 0%
hallucination, and Vector RAG comparison claims. Replace each with an
evidence-linked statement or a proposed experiment. Keep “SAP” in synthetic
fixture descriptions only where the disclaimer makes the boundary clear.

### 10.2 Proposal and interview-defensible document

Rewrite `docs/research/cifre_phd_proposal.md` around an honest proposal
structure:

- research motivation and questions;
- what this repository currently implements;
- deterministic baseline architecture and limitations;
- controlled synthetic evaluation protocol;
- hypotheses and future LLM/vector/hybrid experiments;
- data, privacy, provenance, and human-evaluation requirements;
- risks, falsifiable outcomes, and three-year research directions;
- explicit independent-candidate disclaimer and non-goals.

Add `docs/research/cifre-interview-brief.md` as the required interview-
defensible document. It is a short fact sheet containing the current data flow,
one reproducibility command, exact baseline metrics after the redesign,
limitations, and five defensible statements an interviewer can verify from
source. It must state that no employment or affiliation is implied.

### 10.3 Repository-wide wording

Search all Markdown, YAML, Python docstrings, package metadata, and generated
reports for unsupported ownership and capability language. In particular:

- replace “SAP SE publishes,” “SAP central enterprise architecture owns,”
  “certified SAP data product,” and similar ownership language with
  “repository-maintained synthetic contract” or “illustrative mapping”;
- label Databricks, Snowflake, and Fabric adapters as unexecuted simulations;
- distinguish synthetic SAP-shaped names from official SAP assets;
- remove production, cloud, partnership, benchmark-superiority, and
  hallucination guarantees unless backed by current evidence;
- update the `pyproject.toml` description to
  `Independent synthetic semantic-layer and knowledge-graph research prototype`;
- make `docs/verification-report.md` a fresh post-change report rather than a
  historical assertion, including exact commands, commit, hashes, and known
  limitations.

The repository must not mutate GitHub metadata, releases, topics, remote
descriptions, or other external state as part of this work.

## 11. Architecture, data flow, and exact file impact

The hardened data flow is:

```text
synthetic ontology/data fixtures
  -> namespace and schema validation
  -> graph generation + isomorphism parity
  -> scoped SHACL validation
  -> fixed-vocabulary grounding (abstain on unknown/ambiguous)
  -> typed logical plan (all projected vars bound)
  -> deterministic SPARQL (explicit property paths)
  -> RDFLib execution
  -> bounded repair with operation ledger
  -> strict status + binding-derived answer
  -> per-query benchmark record + hashed JSON artifact
```

The implementation impact is fixed and explicit:

| Area | Exact files/globs | Required boundary |
| --- | --- | --- |
| Namespace constants and graph loading | `src/semantic_layer/kg/loader.py`, `src/semantic_layer/kg/sap_dataset_generator.py` | One neutral namespace registry; no legacy aliases |
| Synthetic semantic assets | `semantic/ontology/`, `semantic/shapes/`, `semantic/data/`, `semantic/vocabulary/`, `semantic/taxonomy/` | Distinct support, PPMS, ERP OWL, and SKOS IRIs; coherent datatypes |
| AQR contracts | `src/semantic_layer/reasoning/schema_linker.py`, `query_planner.py`, `text_to_sparql.py`, `reflective_agent.py` | Abstention, bound projections, closure path, typed status and repair ledger |
| Benchmark | `src/semantic_layer/research/benchmark_runner.py`, `tests/research/benchmark_dataset_legacy.yaml`, `tests/research/benchmark_dataset_v1.yaml`, `tests/research/benchmark_dataset_v2.yaml`, `results/latest_benchmark.json` | Real conditions only; exact-set and set metrics; hashes/per-query records |
| Reproducibility | `Makefile`, generator/validation helpers, tests | One `research-verify` target with parity, SHACL, benchmark, tests, lint |
| Claims and handoff | `README.md`, `docs/research/cifre_phd_proposal.md`, new `docs/research/cifre-interview-brief.md`, `docs/data-products.md`, `docs/governance.md`, `docs/verification-report.md`, `pyproject.toml` | Independent disclaimer, current/proposed labels, no ownership/affiliation claims |
| Tests | `tests/research/`, `tests/semantic/`, `tests/unit/`, documentation claim tests | TDD, semantic regression, artifact integrity, status and claim contracts |

The federated ERP path remains functional but secondary. Its deterministic
typed plans, authorization gates, and local DuckDB demonstration are not
silently merged into the AQR benchmark or presented as support-graph evidence.

## 12. Testing strategy

Implementation follows TDD: each behavior begins with a failing focused test,
then the smallest implementation, then the focused and full verification
commands. Tests must cover the following contracts.

### 12.1 Semantic and asset tests

- Every synthetic RDF file uses only the approved neutral namespaces for its
  domain and declares synthetic provenance.
- Support/PPMS ontology ranges agree with generated literal datatypes and
  language tags.
- SKOS concepts validate as concepts and cannot be mistaken for ERP OWL
  classes; explicit crosswalks are tested separately.
- Direct and transitive prerequisite cases return the declared closure, do not
  return the target note, deduplicate results, and terminate on a bounded cycle
  fixture.
- Every projected SPARQL variable has a binding pattern.
- Valid and invalid graph fixtures produce the expected scoped SHACL results.
- Generated and checked-in graphs are isomorphic; a changed triple fails.

### 12.2 AQR behavior tests

- Known supported questions return `SUCCESS` with strict binding-derived
  answers.
- Unknown alerts, unknown components, unsupported grammar, and ambiguous
  questions return `UNSUPPORTED` without invented capabilities.
- Syntax and execution failures return their distinct statuses after the
  bounded budget and preserve sanitized diagnostics.
- Strict zero bindings return `EMPTY_RESULT`; relaxed candidates remain
  disclosed and are never marked exact success.
- Relaxation history records every semantic operation and remains bounded.
- Answer text contains only values present in the final strict binding set,
  unless it is explicitly labelled a relaxed candidate.

### 12.3 Benchmark and claim-contract tests

- Dataset IDs, declared counts, categories, expected statuses, hashes, and
  gold note IDs are validated.
- The runner has exactly two measured conditions: deterministic no-reflection
  ablation and deterministic bounded repair. No Vector RAG result field,
  hallucination percentage, or unsupported comparative claim is accepted.
- Exact-set, precision, recall, F1, syntax, execution, and recovery metrics
  match hand-computed fixtures, including empty-set edge cases.
- Every result has a per-query record, input hashes, status, and strict versus
  relaxed marker; stale hashes fail.
- Markdown and package metadata claim tests reject affiliation, ownership,
  production, solved-PhD, zero-hallucination, and fake-vector claims.
- Documentation links and the interview brief point to executable commands
  and checked-in artifacts.

## 13. Execution sequence and acceptance criteria

The implementation is split into reviewable, independently verifiable tasks.
Each task should be a separate commit or clearly reviewable commit boundary.

### Task 1: Freeze current evidence and claim inventory

Capture current `git` commit, test/lint/semantic commands, benchmark output,
namespace occurrences, and claim locations in a migration note or test
fixture. Do not edit implementation until the baseline inventory is
reviewable.

**Acceptance:** The inventory identifies the AQR path, all three current
benchmark branches, the 40 query IDs, every old namespace family, and every
unsupported affiliation/ownership/LLM/vector claim targeted for removal.

### Task 2: Migrate synthetic namespaces and generated assets

Add the namespace registry, migrate support/PPMS/data IRIs, separate ERP OWL
and SKOS IRIs, regenerate checked-in fixtures, and update tests and SPARQL
prefixes in one clean-break change.

**Acceptance:** No old official-looking ontology/data IRI remains in the
synthetic support/PPMS path; all assets parse; no alias triples or dual
bindings exist; namespace and graph-isomorphism tests pass.

### Task 3: Correct semantic contracts

Fix language-tag ranges and shapes, prerequisite closure and projection,
partial SHACL result reporting, and generated/check-in parity. Add valid,
invalid, closure, cycle, datatype, and SKOS/OWL separation fixtures first.

**Acceptance:** Focused semantic tests pass; all shape scopes are explicitly
reported; direct/transitive prerequisite expectations are documented; no
unbound projection is compiled.

### Task 4: Harden AQR statuses and repair semantics

Introduce the closed result-status/reason-code model, fail-closed grounding,
bounded repair ledger, strict-versus-relaxed result fields, and binding-derived
answer contract. Update integration tests and CLI output.

**Acceptance:** Each status has a deterministic fixture; unknown/ambiguous
input never generates a guessed capability; relaxed results remain
`EMPTY_RESULT` for strict scoring; diagnostics are bounded and sanitized.

### Task 5: Rebuild the preliminary benchmark

Preserve `tests/research/benchmark_dataset.yaml` as historical input, generate
normalized v1 at `tests/research/benchmark_dataset_v1.yaml`, and create
`tests/research/benchmark_dataset_v2.yaml` with the 12 negative records
specified in Section 26.1. Add migration metadata to v1, remove
the fake Vector RAG path, rename the one-shot ablation, implement exact-set/set
metrics, and write the hashed v1/v2 per-query JSON artifact.

**Acceptance:** A fresh run produces schema-valid `results/latest_benchmark.json`
with one corpus run for v1 and one for v2, no Vector RAG/hallucination fields,
deterministic input hashes, per-query records, and hand-checked metric edge
cases. V1 golds remain stable; any revised gold has explicit evidence and
migration reasons.

### Task 6: Add the single verification target (locked v1/v2 verification)

Implement `research-verify`, install from `constraints/py312.txt`, add the
`research-verify` CI job, and make the target
exercise generation/load, parity, scoped SHACL, benchmark, results, tests, and
lint without external services.

**Acceptance:** The command succeeds on a clean checkout, fails on a deliberate
fixture/hash/namespace mutation, and produces a concise report whose claims
match the artifact.

### Task 7: Sanitize documentation and handoff

Restructure the README, rewrite the proposal status, add the interview brief,
sanitize ownership and platform language across the repository, update package
metadata, and record a fresh verification report.

**Acceptance:** Claim-contract tests pass; a reader can identify current versus
proposed work and the independent boundary from the first screen; all linked
commands and artifacts exist; no external GitHub metadata changes occur.

## 14. Risks, migration, and rollback

| Risk | Mitigation |
| --- | --- |
| Namespace migration breaks stale consumers | Make the clean break explicit, regenerate all checked-in assets, run repository-wide URI tests, and provide migration notes; no runtime aliases |
| Gold sets change after semantic corrections | Preserve legacy values and reasons, derive revised sets from a declared graph/policy, and review per-query diffs |
| Relaxation inflates apparent accuracy | Keep strict and relaxed bindings separate; score only strict exact satisfaction and report recovery separately |
| RDFLib/pySHACL versions differ | Pin/record supported versions, test explicit datatypes and graph isomorphism, and report environment hashes |
| Synthetic labels are mistaken for official data | Use neutral namespaces, synthetic metadata, prominent disclaimers, and claim-contract tests |
| Documentation drifts from code | Make hashes, result schema, command text, and current/proposed vocabulary executable test contracts |
| Benchmark runtime burdens CI | Measure locally, cache only safe dependency/setup work, and split jobs without weakening the same acceptance checks |
| Future learned work is added prematurely | Keep the current interface model-free; require a separate method, dependency, seed, dataset split, and evidence artifact before adding a condition |

Rollback is a Git operation at task boundaries. A failed namespace migration is
rolled back by reverting the migration commit and its dependent asset commit;
there is no compatibility alias or mixed-namespace runtime mode. A benchmark
method regression is rolled back by restoring the prior runner/dataset/result
commit while retaining the design document and the recorded reason for the
reversion. No generated or external production data is deleted, and no cloud
or GitHub state is changed.

## 15. Non-goals

This design does not authorize or require:

- an external LLM, model download, prompt service, or vector database;
- a real Vector RAG baseline or any fabricated comparative score;
- SAP proprietary, confidential, customer, production, or internal data;
- a claim of SAP affiliation, endorsement, partnership, or employment;
- cloud, production, hosted API, or deployment integration;
- a solved doctoral research problem or zero-hallucination guarantee;
- GitHub metadata, release, remote, issue, or repository-setting mutation;
- broad generalization claims from the 40-query synthetic corpus;
- replacement of the deterministic baseline with a learned system.

## 16. Normative grounding grammar and abstention contract

The deterministic linker is a finite grammar, not an open-ended natural
language capability. The grammar is checked in at
`tests/research/grounding_grammar.yaml`, with schema version `1.0`. A parser
normalizes Unicode whitespace, case-folds entity tokens, preserves the
original question, and accepts only the templates and filler tokens declared
in that file. Punctuation at template boundaries is ignored. A token that is
not an entity slot or a declared filler token is an `UNKNOWN_TOKEN`; it is not
silently discarded.

The grammar permits the exact filler vocabulary below and no other free text:

```yaml
filler_tokens:
  - addressing
  - addresses
  - alert
  - any
  - an
  - and
  - application
  - are
  - at
  - before
  - component
  - database
  - dependencies
  - dependency
  - details
  - does
  - dump
  - errors
  - error
  - affecting
  - for
  - find
  - fixing
  - has
  - have
  - in
  - identify
  - information
  - list
  - management
  - memory
  - note
  - notes
  - of
  - on
  - package
  - prerequisite
  - prerequisites
  - required
  - resolve
  - resolves
  - resolving
  - retrieve
  - runtime
  - sap
  - support
  - the
  - title
  - what
  - which
```

The grammar source also contains these exact token sequences:

```yaml
templates:
  - id: note_lookup
    intent: NOTE_LOOKUP
    sequence: [lookup_verb, "filler*", note_number]
  - id: alert_resolution
    intent: ALERT_RESOLUTION
    sequence: [question_word, "filler*", alert_code, "filler*", "component_code?", "product_version?", "support_package?", "priority?"]
  - id: component_search
    intent: COMPONENT_SEARCH
    sequence: [question_word, "filler*", component_code, "filler*", "product_version?", "support_package?", "priority?"]
  - id: version_filtered_search
    intent: VERSION_FILTERED_SEARCH
    sequences:
      - [question_word, "filler*", "alert_code|component_code", "filler*", "component_code?", "filler*", "product_version|support_package", "filler*", "priority?"]
      - [question_word, "filler*", "alert_code", "filler*", "product_version|support_package", "filler*", "component_code?", "filler*", "priority?"]
      - [question_word, "filler*", "product_version|support_package", "filler*", "alert_code|component_code", "filler*", "component_code?", "filler*", "priority?"]
  - id: prerequisite_closure
    intent: PREREQUISITE_CLOSURE
    sequence: [question_word, "filler*", prerequisite_marker, "filler*", note_number]
  - id: general_note_lookup
    intent: GENERAL_SEARCH
    sequence: [note_number]
lookup_verb: [find, get, identify, retrieve, what, which]
question_word: [find, get, identify, what, which, list]
prerequisite_marker: [dependency, dependencies, prerequisite, prerequisites]
unsupported_intent_marker: [explain, recommend, summarize]
```

`filler*` consumes only the declared `filler_tokens`; `?` consumes zero or
one slot; `|` consumes exactly one alternative. Each sequence is token-based,
not a permissive regular expression. The parser rejects a sequence that binds
an optional slot before its required anchor or binds two alternatives from the
same family. In `VERSION_FILTERED_SEARCH`, an alert anchor may be followed by
one component qualifier and one version/package qualifier; a component anchor
does not consume a second component slot. Therefore alert+component+version is
accepted with the alert as anchor and component as qualifier. The second
alternative accepts alert+version+component and the third accepts
version+alert+component, so the combined anchors may appear in either order
around the version qualifier. A component anchor never consumes a second
component slot.

The entity slots are exactly the linker vocabulary sets already declared in
`schema_linker.py`: `alert_code`, `component_code`, `product_version`,
`software_component`, `support_package`, `note_number`, and `priority`.
Entity values are case-insensitive for matching and are emitted in their
canonical spelling. A seven-digit note number is accepted only as a
`note_number`. Support packages have an explicit syntax policy: after an
`SP` cue or in a support-package slot, an uppercase-canonical token consisting
of `SP` followed by one or two decimal digits is a syntactically valid
`support_package` constraint even when that package is absent from the finite
graph/entity lexicon. `SP99` is therefore a valid numeric constraint that can
execute to `EMPTY_RESULT`; a named or malformed package token absent from the
lexicon is `UNKNOWN_ENTITY`. The remaining entity forms must occur in the
finite vocabulary. A distinct second value in any entity family is an
ambiguity and causes abstention. Repeating the same canonical value is
harmless.

The supported intents and their required slots are fixed:

| Intent | Required slots | Optional slots | Semantics |
| --- | --- | --- | --- |
| `NOTE_LOOKUP` | exactly one `note_number` | none | Direct lookup of one synthetic note |
| `ALERT_RESOLUTION` | exactly one `alert_code` | one `component_code`, one `product_version`, one `support_package`, one `priority` | Notes linked to an alert, with optional exact qualifiers |
| `COMPONENT_SEARCH` | exactly one `component_code` | one `product_version`, one `support_package`, one `priority` | Notes linked to a component and optional exact qualifiers |
| `VERSION_FILTERED_SEARCH` | exactly one `product_version` or one `support_package`, plus exactly one `component_code` or `alert_code` | one of the remaining version/priority slots | Anchored version-constrained search |
| `PREREQUISITE_CLOSURE` | exactly one `note_number` | none | Transitive prerequisite closure for one note |
| `GENERAL_SEARCH` | exactly one `note_number` | none | Alias for `NOTE_LOOKUP` only; it never emits an unconstrained note search |

Intent selection is deterministic and ordered: prerequisite words select
`PREREQUISITE_CLOSURE`; a version/support-package qualifier with one alert or
component selects `VERSION_FILTERED_SEARCH`; an alert without a version or
support-package selects `ALERT_RESOLUTION`; a component without those
qualifiers selects `COMPONENT_SEARCH`; a single note number with lookup
wording selects `NOTE_LOOKUP`; the only remaining accepted case is
`GENERAL_SEARCH` with exactly one note number.
Conflicting intent markers, no required slot, multiple distinct values,
unknown tokens, and a version/package qualifier without an alert or component
return `UNSUPPORTED` before planning. The linker never invents an entity from
an unrecognised spelling, parent, synonym, or external capability.

The grammar fixtures must include these exact cases:

| Input | Expected intent/status | Extracted entities |
| --- | --- | --- |
| `Retrieve the title and details for SAP Note 3012445.` | `NOTE_LOOKUP` / `SUCCESS` after execution | `note_number=[3012445]` |
| `Which SAP note resolves alert TIME_OUT in component MM-PUR-PO?` | `ALERT_RESOLUTION` / `SUCCESS` after execution | `alert_code=[TIME_OUT]`, `component_code=[MM-PUR-PO]` |
| `Find notes for alert TIME_OUT in component MM-PUR-PO on S/4HANA 2023.` | `VERSION_FILTERED_SEARCH` / `SUCCESS` after execution | `alert_code=[TIME_OUT]`, `component_code=[MM-PUR-PO]`, `product_version=[S4HANA_2023]` |
| `Find notes resolving alert TIME_OUT on S/4HANA 2022 in component SD-SLS.` | `VERSION_FILTERED_SEARCH` / `EMPTY_RESULT` after execution | `alert_code=[TIME_OUT]`, `product_version=[S4HANA_2022]`, `component_code=[SD-SLS]` |
| `What are the prerequisite notes required for SAP Note 3109922?` | `PREREQUISITE_CLOSURE` / `SUCCESS` after execution | `note_number=[3109922]` |
| `Find notes valid for S/4HANA 2023.` | `UNSUPPORTED` / `UNSUPPORTED` | no anchored alert/component |
| `Find notes for alert TIME_OUT and alert DBSQL_NO_MORE_CONNECTION.` | `UNSUPPORTED` / `UNSUPPORTED` | two distinct `alert_code` values |
| `Find notes for alert UNKNOWN_ALERT.` | `UNSUPPORTED` / `UNSUPPORTED` | `UNKNOWN_ENTITY` |
| `Find notes for alert TIME_OUT in component BC-DB-HDB for an Oracle system.` | `UNSUPPORTED` / `UNSUPPORTED` | `UNKNOWN_TOKEN=oracle/system` |

The fixture expected status is the status after execution for supported
templates and `UNSUPPORTED` for rejected templates. A grammar test must prove
that no rejected fixture reaches planner or compiler code.

## 17. Normative deterministic result JSON contract

Every benchmark condition writes one JSON object per query conforming to the
following contract. The aggregate artifact at
`results/latest_benchmark.json` contains `schema_version: "1.0.0"`, a
`corpus_runs` array, and these query objects in `per_query`. `null` is the
only representation of a missing nullable value; omitted fields are schema
violations. `NaN`, positive infinity, negative infinity, and the strings
`"None"` and `"NaN"` are forbidden.

```json
{
  "schema_version": "1.0.0",
  "corpus_id": "cifre-synthetic-aqr-v1",
  "query_id": "Q01",
  "condition": "deterministic_bounded_repair",
  "question": "Which SAP Notes directly resolve alert DBSQL_NO_MORE_CONNECTION?",
  "normalized_request": "which sap notes directly resolve alert dbsql_no_more_connection",
  "expected_status": "SUCCESS",
  "observed_status": "SUCCESS",
  "reason_code": "NONE",
  "original_constraints": {
    "alert_code": ["DBSQL_NO_MORE_CONNECTION"],
    "component_code": [],
    "product_version": [],
    "software_component": [],
    "support_package": [],
    "note_number": [],
    "priority": [],
    "predicates": ["cifsup:resolvesAlert", "cifsup:alertCode"]
  },
  "grounding": {
    "intent": "ALERT_RESOLUTION",
    "entities": {
      "alert_code": ["DBSQL_NO_MORE_CONNECTION"],
      "component_code": [],
      "product_version": [],
      "software_component": [],
      "support_package": [],
      "note_number": [],
      "priority": []
    }
  },
  "plan": {"digest_sha256": "0000000000000000000000000000000000000000000000000000000000000000", "required_variables": ["?note", "?title", "?noteNumber"]},
  "sparql": {"initial": "...", "final": "..."},
  "attempts": 1,
  "repair": {
    "max_repairs": 3,
    "recovered": false,
    "recovery_attempt": 0,
    "recovery_success": false,
    "relaxation_attempted": false,
    "operations": []
  },
  "relaxation": {
    "attempted": false,
    "strict_status": "SUCCESS",
    "operations": []
  },
  "answer_scope": "strict",
  "relaxed_candidates": [],
  "bindings": [
    {"note": "https://example.org/cifre-kg/data/support/note/3345100", "noteNumber": "3345100", "title": "...", "alertCode": "DBSQL_NO_MORE_CONNECTION"}
  ],
  "predicted_note_numbers": ["3345100"],
  "gold_note_numbers": ["3345100"],
  "metrics": {
    "applicable": true,
    "exact_set": true,
    "precision": "1.000000",
    "recall": "1.000000",
    "f1": "1.000000"
  },
  "provenance": {
    "dataset_id": "cifre-synthetic-support-ppms-v1",
    "source_kind": "synthetic_fixture",
    "official": false,
    "graph_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
    "citation": "Synthetic fixture cifre-synthetic-support-ppms-v1; not official data."
  }
}
```

The JSON Schema checked in at
`tests/research/result_schema.json` is authoritative and must encode the
following details:

- The required top-level fields are `schema_version`, `corpus_id`, `query_id`,
  `condition`, `question`, `expected_status`, `observed_status`,
  `reason_code`, `grounding`, `plan`, `sparql`, `attempts`, `repair`,
  `bindings`, `predicted_note_numbers`, `gold_note_numbers`, `metrics`, and
  `provenance`.
- `grounding`, `plan`, and `sparql` are nullable objects; `metrics` is always
  an object; `metrics.exact_set`, `metrics.precision`, `metrics.recall`, and
  `metrics.f1` are nullable and become JSON `null` when `applicable` is false.
  `provenance` is never nullable, including for an unsupported query.
- `condition` is one of `deterministic_no_reflection_ablation` or
  `deterministic_bounded_repair`.
- `expected_status`, `observed_status`, and every operation `status_before`
  and `status_after` are one of `SUCCESS`, `UNSUPPORTED`, `SYNTAX_ERROR`,
  `EXECUTION_ERROR`, or `EMPTY_RESULT`.
- `reason_code` is the enum in Section 18; it is `NONE` only for a strict
  `SUCCESS` or `EMPTY_RESULT` without an error/abstention reason.
- `grounding.intent`, `grounding.entities`, `plan`, and `sparql` are nullable
  only when the status is `UNSUPPORTED`; unsupported records have
  `grounding: null`, `plan: null`, and `sparql: null`.
- `bindings` is always an array. A supported empty result has `[]`; an
  unsupported result also has `[]`. Binding objects contain all required
  projected fields and contain optional projected fields with JSON `null`.
- `predicted_note_numbers` and `gold_note_numbers` are unique arrays of
  seven-digit strings sorted by Unicode code point. No set is represented as
  an object or comma-separated string.
- `corpus_id` is required on every per-query record. Query IDs are unique only
  within a corpus; the authoritative identity is the unique tuple
  `(corpus_id, condition, query_id)`, serialized in `result_ids` as
  `<corpus_id>:<condition>:<query_id>`. The schema enforces unique `query_ids`
  and `result_ids` arrays, and a semantic result-contract check enforces
  uniqueness of that composite tuple and exact result-ID references.
- Required projected variables are `?note`, `?noteNumber`, and `?title` for
  note answers. Optional variables have an explicit `optional: true` entry in
  the plan and their missing bindings are JSON `null`.
- Binding rows sort by the tuple `(noteNumber, title, note IRI, remaining
  projected variable names)` after conversion to UTF-8 strings. Object keys
  sort lexicographically. This ordering is applied before hashing.
- Aggregate metric-object values are decimal strings with exactly six
  fractional digits,
  rounded half-even from `Decimal`; binary JSON floats are forbidden. Counts
  are non-negative JSON integers. Boolean fields are JSON booleans.
- Canonical JSON is UTF-8, RFC 8785-style key ordering, no insignificant
  whitespace, `\n` only where a file writer requires a final line ending, and
  no timestamp in the hashed content.

### 17.1 Exact hash manifest and environment

The complete manifest is the sorted glob expansion in Section 26.6; the
short list below is retained only to show the primary research assets and is
not an alternative manifest.

`results/latest_benchmark.json` contains `manifest_version: "1.0"` and an
ordered `hash_manifest` with this exact path order. Each entry stores the
repository-relative path, byte SHA-256, and byte length:

```text
semantic/ontology/sap_support.ttl
semantic/ontology/sap_ppms.ttl
semantic/ontology/sap_erp.ttl
semantic/shapes/sap_support_shapes.ttl
semantic/shapes/sap_erp_shapes.ttl
semantic/taxonomy/sap_products.ttl
semantic/vocabulary/sap_erp.yaml
semantic/data/sap_support_graph.ttl
semantic/provenance/synthetic_source.yaml
tests/research/grounding_grammar.yaml
tests/research/benchmark_dataset_legacy.yaml
tests/research/benchmark_dataset_v1.yaml
tests/research/benchmark_dataset_v2.yaml
tests/research/benchmark_migration_manifest_v1.yaml
tests/research/result_schema.json
constraints/py312.txt
Makefile
pyproject.toml
.github/workflows/ci.yml
src/semantic_layer/kg/*.py
src/semantic_layer/reasoning/*.py
src/semantic_layer/research/*.py
data/**/*.py
```

Glob entries expand using POSIX path separators and bytewise lexical order;
the expanded paths are inserted in that order and duplicates are removed.
No other files are included, and `results/latest_benchmark.json` is never
included in its own manifest. The manifest digest is SHA-256 of each
`path\\0sha256\\0byte_length\\n` record concatenated in the listed order.

The artifact also records `environment` with exact `python_version`,
`platform_system`, `platform_machine`, `pip_version`, and the sorted package
versions read from `constraints/py312.txt`. It records the lock-file digest,
not an unconstrained live `pip freeze`. A run with a different Python major,
minor, platform, or package version is a distinct environment and cannot reuse
the recorded benchmark claim.

## 18. Correctness gating, repair lifecycle, and reason codes

### 18.1 Status-gated metrics

Each query has a declared `expected_status`. `status_correct` is true only
when `observed_status == expected_status`. Answer metrics (`exact_set`,
precision, recall, and F1) are applicable only when both conditions hold:

1. `expected_status == SUCCESS`; and
2. `status_correct == true`.

For every other case, `metrics.applicable` is false and answer metrics are
JSON `null`; the row remains in status and operational metric denominators.
In particular, an observed `EMPTY_RESULT` with an empty predicted set cannot
score as a correct answer when the expected status is `SUCCESS`, and an
observed `SUCCESS` with an empty set cannot score when the expected status is
`UNSUPPORTED` or `EMPTY_RESULT`. Aggregate answer metrics report
`applicable_count` and `not_applicable_count` and exclude nulls from both
macro and micro calculations. N/A is never converted to zero.

The following hand-calculated fixtures are mandatory metric tests, with note
numbers represented as sorted strings:

| Expected status/gold | Observed status/predicted | Status correct | Applicable | Exact | Precision | Recall | F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `SUCCESS` / `["1","2"]` | `SUCCESS` / `["1","3"]` | true | true | false | `0.500000` | `0.500000` | `0.500000` |
| `SUCCESS` / `["1"]` | `EMPTY_RESULT` / `[]` | false | false | null | null | null | null |
| `EMPTY_RESULT` / `[]` | `EMPTY_RESULT` / `[]` | true | false | null | null | null | null |
| `UNSUPPORTED` / `[]` | `SUCCESS` / `[]` | false | false | null | null | null | null |
| `SUCCESS` / `["1","2"]` | `SUCCESS` / `["1","2"]` | true | true | true | `1.000000` | `1.000000` | `1.000000` |

Status metrics remain separately reportable: status accuracy, syntax repair
success, execution success, unsupported rejection, strict empty rate, and
recovery counts. A relaxed candidate is never used as a predicted set for
strict answer metrics.

### 18.2 Lifecycle counts and reason enum

`max_repairs` is exactly `3`. Attempt index `0` is the initial grounding,
planning, compilation, and execution attempt. Repair indices `1`, `2`, and
`3` are the only permitted repair attempts, so `attempts` is an integer in
`[0,4]`; unsupported input has `attempts: 0`. A syntax or execution repair
replaces the current plan/query only after recording the failed attempt. If a
repaired query executes with strict bindings, the final status is `SUCCESS`
and `repair.recovery_success` is true. If all three repairs fail, the final
status is `SYNTAX_ERROR` or `EXECUTION_ERROR` according to the last failure,
and `recovery_success` is false.

An empty strict execution records `EMPTY_RESULT`. A semantic relaxation may
be attempted at repair index 1, 2, or 3 and may produce `relaxed_candidates`,
but final status remains `EMPTY_RESULT` for the original constraints and
`recovery_success` remains false. `recovered` is true only when a syntax or
execution repair yields strict `SUCCESS`; `recovery_attempt` is the 1-based
repair index of the first successful syntax/execution repair, or `0` when no
such repair occurred; `recovery_success` is the corresponding boolean.

The closed `reason_code` enum is:

```text
NONE
UNKNOWN_TOKEN
UNKNOWN_ENTITY
AMBIGUOUS_INTENT
MULTIPLE_DISTINCT_ENTITIES
UNSUPPORTED_INTENT
MISSING_REQUIRED_ENTITY
UNBOUND_REQUIRED_PROJECTION
SPARQL_SYNTAX
SPARQL_EXECUTION
EMPTY_STRICT_RESULT
RELAX_SUPPORT_PACKAGE
WIDEN_COMPONENT
REPAIR_BUDGET_EXHAUSTED
PROVENANCE_MISSING
HASH_MISMATCH
INVALID_DATASET
```

Each `repair.operations[]` ledger entry is required to contain
`attempt_index`, `operation_kind` (`initial`, `syntax_repair`,
`execution_repair`, `semantic_relaxation`, or `abstention`), `reason_code`,
`status_before`, `status_after`, `query_sha256`, `plan_sha256` (nullable for
abstention), `sparql_sha256` (nullable for abstention),
`changed_constraints` (sorted array), `binding_count`, `error_class` (nullable
for success), and `diagnostic` (bounded to 512 UTF-8 characters). The full
query and plan are stored only in the top-level fields and are null for
unsupported inputs. A ledger entry is append-only; no repair may overwrite a
previous query or diagnostic.

## 19. Locked dependencies and installation

The current baseline requires a committed constraints artifact at
`constraints/py312.txt`. It pins every direct and transitive package needed by
the runtime and development commands, including Python 3.12-compatible
versions of DuckDB, FastAPI, Pydantic, PyYAML, RDFLib, pySHACL, Uvicorn,
pytest, HTTPX, and Ruff. The file is generated from the reviewed environment,
contains hashes for installable distributions, and is updated in the same
commit as a dependency change. Its SHA-256 is included in
`results/latest_benchmark.json` and `docs/verification-report.md`.

The exact installation command from a clean checkout is:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip==25.2
.venv/bin/python -m pip install --require-hashes --constraint constraints/py312.txt -e '.[dev]'
```

The lock-generation command is fixed to `pip-tools==7.4.1` and is not required
for ordinary installation:

```bash
.venv/bin/python -m pip install pip-tools==7.4.1
.venv/bin/pip-compile --extra=dev --generate-hashes --output-file=constraints/py312.txt pyproject.toml
```

An installation that cannot satisfy the lock fails before verification; the
verification target never silently resolves unpinned latest versions.

## 20. Machine-readable synthetic provenance

Commit `semantic/provenance/synthetic_source.yaml` with schema version `1.0`.
It must contain exactly these top-level fields:

```yaml
schema_version: "1.0"
dataset_id: cifre-synthetic-support-ppms-v1
source_kind: synthetic_fixture
authority: independent_repository
official: false
source_license: repository-authored synthetic data
generator: src/semantic_layer/kg/sap_dataset_generator.py:build_sap_support_graph
graph_path: semantic/data/sap_support_graph.ttl
namespace_registry:
  cifsup: https://example.org/cifre-kg/support#
  cifppms: https://example.org/cifre-kg/ppms#
  cifdata: https://example.org/cifre-kg/data/
  ciferp: https://example.org/cifre-kg/erp#
  cifskos: https://example.org/cifre-kg/vocabulary#
  cifmeta: https://example.org/cifre-kg/meta#
  cifmetaid: https://example.org/cifre-kg/id/meta/
synthetic_label_policy:
  official_help_documentation: forbidden
  official_note: forbidden
  official_product: forbidden
```

The RDF graph contains a metadata resource under
`https://example.org/cifre-kg/id/meta/dataset-cifre-synthetic-support-ppms-v1`
with `cifmeta:sourceKind "synthetic_fixture"`,
`cifmeta:official false`, `cifmeta:datasetId`, `cifmeta:generatedBy`, and
`cifmeta:graphPath`. Runtime result provenance must copy `dataset_id`,
`source_kind`, `official`, and `graph_sha256`; every answer citation must
begin with `Synthetic fixture <dataset_id>; not official data.`

All documentation labels and resource titles use “Synthetic Help
Documentation”, “Synthetic Support Note”, and “Synthetic Product Version”.
The label “Official Help Documentation” is forbidden. Generator and checked-in
data must remove every `help.sap.com` URI and replace it with a neutral
`https://example.org/cifre-kg/docs/<identifier>` URI. A repository scan rejects
`help.sap.com`, regardless of whether it occurs in code, data, tests, or
documentation.

## 21. Complete namespace, crosswalk, and legacy-URI contract

The namespace registry is closed. The allowed class and property names are:

| Namespace | Allowed classes | Allowed object/data properties |
| --- | --- | --- |
| `cifsup` | `SAPNote`, `SystemAlert`, `ApplicationComponent`, `SimCatCategory`, `HelpDocumentation` | `affectsComponent`, `parentComponent`, `resolvesAlert`, `validForComponentVersion`, `validForProductVersion`, `hasPrerequisiteNote`, `hasSideEffectNote`, `classifiedUnderSimCat`, `referencedDocumentation`, `noteNumber`, `title`, `symptom`, `rootCause`, `resolution`, `priority`, `alertCode`, `severity`, `systemId`, `componentCode`, `componentDescription`, `categoryName`, `docUri`, `minSupportPackage`, `maxSupportPackage` |
| `cifppms` | `ProductLine`, `Product`, `ProductVersion`, `SoftwareComponent`, `SoftwareComponentVersion`, `SupportPackage`, `PatchLevel` | `belongsToProductLine`, `hasProductVersion`, `includesComponent`, `isVersionOfComponent`, `hasSupportPackage`, `hasPatchLevel`, `dependsOnComponent`, `productLineCode`, `productCode`, `versionCode`, `componentName`, `componentVersionString`, `stackLevel`, `spName`, `patchNumber`, `releaseYear` |
| `ciferp` | `BusinessPartner`, `SalesOrder`, `FinancialPosting`, `Product`, `ProductAutomotive`, `ProductCommercial`, `Risk`, `Coverage`, `BillingDocument`, `PostingStatus`, `CompanyCode`, `CountryCodedEntity`, `ActiveSalesOrder`, `QualifyingPosting`, `FinancialLoss` | `hasSalesOrder`, `hasFinancialPosting`, `referencesSalesOrder`, `hasProduct`, `coversRisk`, `hasCoverage`, `generatesBilling`, `postingOrder`, `orderProduct`, `countryCode`, `partnerId`, `salesOrderId`, `journalEntryId`, `postingDate`, `postingStatus`, `orderStatus`, `amountInCompanyCurrency`, `hasPostingStatus`, `hasFinancialLoss`, `statusValue`, `amountValue` |
| `cifskos` | `ProductScheme`, `Product`, `ProductAutomotive`, `ProductCommercial` as SKOS resources only | `skos:hasTopConcept`, `skos:topConceptOf`, `skos:narrower`, `skos:broader`, `skos:inScheme`, `skos:prefLabel`, `skos:altLabel` |
| `cifmeta` | `SyntheticDataset`, `CrosswalkEntry` | `sourceKind`, `official`, `datasetId`, `generatedBy`, `graphPath`, `sourceResource`, `targetConcept`, `crosswalkVersion` |

Allowed instance bases are exact: support instances use
`https://example.org/cifre-kg/data/support/{note,alert,component,simcat,doc}/`;
PPMS instances use
`https://example.org/cifre-kg/data/ppms/{productline,product,version,component,compversion,sp,patch}/`;
ERP instances use
`https://example.org/cifre-kg/data/erp/{partner,order,doc,product,risk,coverage,status,loss}/`;
and metadata resources use
`https://example.org/cifre-kg/id/meta/`. The RDF namespace IRIs in Section 5.1
are the only class/property bases. No other HTTP(S) IRI is valid for a
synthetic domain resource except W3C vocabulary IRIs (`rdf`, `rdfs`, `owl`,
`xsd`, `sh`, and `skos`).

The explicit ERP-to-SKOS crosswalk is a separate resource with this schema:

```turtle
cifmetaid:crosswalk-entry-product-automotive a cifmeta:CrosswalkEntry ;
    cifmeta:sourceResource ciferp:ProductAutomotive ;
    cifmeta:targetConcept cifskos:ProductAutomotive ;
    cifmeta:crosswalkVersion "1.0"^^xsd:string .
```

`cifmeta:sourceResource` and `cifmeta:targetConcept` have domain
`cifmeta:CrosswalkEntry`; their ranges are `ciferp:Product` and
`skos:Concept`, respectively. This metadata entry never asserts that the SKOS
concept is an OWL class and never replaces `rdf:type`.

The implementation and claim-contract tests scan all tracked runtime,
semantic-asset, test, README, proposal, metadata, and result files and reject
the legacy URI families `https://sap.example/erp/`,
`http://ontology.sap.com/`, and `http://data.sap.com/`, as well as their
prefix abbreviations when bound to those IRIs. The migration design file is
the sole documented exception because it names the forbidden families in this
contract; the scanner excludes only this file and reports its exclusion.

## 22. Exact SHACL and validation matrix

After namespace migration, these repository-relative graph and shape paths
are fixed. Each check runs RDFLib/pySHACL with `inference: "rdfs"`,
`abort_on_first: false`, `advanced: false`, `js: false`, and
`meta_shacl: false` unless the matrix explicitly says otherwise.

| Check ID | Data graph | Shapes graph | Inference | Expected conforms | Purpose |
| --- | --- | --- | --- | ---: | --- |
| `SUPPORT_VALID` | `semantic/data/sap_support_graph.ttl` | `semantic/shapes/sap_support_shapes.ttl` | `rdfs` | true | Generated support/PPMS fixture |
| `SUPPORT_INVALID` | `semantic/data/support-graph-invalid.ttl` | `semantic/shapes/sap_support_shapes.ttl` | `rdfs` | false | Missing note/component or invalid datatype negative control |
| `ERP_VALID` | `semantic/ontology/sample-graph-valid.ttl` | `semantic/shapes/sap_erp_shapes.ttl` | `rdfs` | true | Valid synthetic ERP fixture |
| `ERP_INVALID` | `semantic/ontology/sample-graph-invalid.ttl` | `semantic/shapes/sap_erp_shapes.ttl` | `rdfs` | false | Missing required fields and negative amount |
| `COMBINED_VALID` | union of `semantic/data/sap_support_graph.ttl` and `semantic/ontology/sample-graph-valid.ttl` | union of both shape graphs | `rdfs` | true | Cross-domain load with separate namespaces |
| `PREREQUISITE_CYCLE_DEPTH` | `semantic/data/support-prerequisite-cycle.ttl` and `semantic/data/support-prerequisite-depth17.ttl` | not applicable | algorithm | algorithm check | Cycle/depth traversal contract |

`SUPPORT_INVALID` is a new committed fixture and must carry the same
`cifmeta:sourceKind "synthetic_fixture"` metadata as the valid fixture.
`COMBINED_VALID` must not cause a support shape to target an ERP resource or
an ERP shape to target a support resource; the separate neutral namespaces
make that isolation testable. There is no combined invalid fixture: the two
negative checks above are the required negative evidence.

The validation report records check ID, exact graph/shapes paths, byte hashes,
inference string, `conforms`, violation count, and synthetic dataset ID. A
valid graph with a missing provenance triple fails the provenance contract
before SHACL; a deliberately invalid graph with the expected nonconformance
passes the negative-control test.

`COMBINED_VALID` is the canonical combined graph construction. The support,
ERP, and combined rows are projections of that same ordered graph load; no
second graph loader or alternate union is permitted.

`PREREQUISITE_CYCLE_DEPTH` is a named graph-algorithm check in the same
validation report, not an unrecorded benchmark side test. It first performs
cycle detection with a visited-node set, then evaluates the depth bound. For
the three-node cycle `A -> B -> C -> A`, the exact output is
`cycle_detected=true`, `cycle_edges=[[A,B],[B,C],[C,A]]`,
`reachable_unique=[B,C]`, `target_excluded=true`, and `status=SUCCESS`. For
the acyclic depth-17 fixture `N0 -> N1 -> ... -> N17`, the exact output is
`cycle_detected=false`, `reachable_unique=[N1,...,N16]`,
`depth_limit=16`, `truncated=true`, and `status=EMPTY_RESULT` with reason
`PREREQUISITE_DEPTH_EXCEEDED`; `N17` is not returned. Unique nodes are
computed before depth evaluation, so cycles cannot consume depth indefinitely.
These outputs are required in the validation report and reproducibility artifact.

## 23. Corpus versions and reflection metadata

The exact corpus migration is defined in Section 26.1. The currently committed
40-record file is historical input; normalized v1 is
`tests/research/benchmark_dataset_v1.yaml` and normalized v2 is
`tests/research/benchmark_dataset_v2.yaml`. V1 remains the 40-query positive
baseline, and v2 evaluates all 52 normalized records. The migration script,
not byte-for-byte copying, supplies the required normalized fields and exact
v1/v2 IDs, categories, statuses, and gold sets. Both versions produce one
`corpus_runs` entry in `results/latest_benchmark.json`.

Every record includes `reflection_reason`, whose enum is exactly:

```text
NONE
SYNTAX_REPAIR_REQUIRED
EXECUTION_REPAIR_REQUIRED
STRICT_EMPTY_SEMANTIC_RELAXATION
NO_REPAIR_EXPECTED
```

`reflection_reason` is `NONE` for v1 non-reflective cases, explicitly records
the reason for each v1 tier-5 query, and is `NO_REPAIR_EXPECTED` when a query
is supported but its expected path has no repair. It never means that a repair
must succeed. V2 negative records use `NONE`; they abstain before repair.
Task 5 in Section 13 must create v2 before benchmark result generation, and
Task 6 must validate and run both versions.

## 24. Optional projections and documentation contracts

The plan schema contains `required_variables` and `optional_variables` as
separate sorted arrays. A required variable must have a mandatory triple
pattern; the compiler rejects a missing pattern with
`UNBOUND_REQUIRED_PROJECTION`. An optional variable must occur only in an
`OPTIONAL` pattern and is encoded as JSON `null` when unbound. Optional
variables never enter `predicted_note_numbers`, exact-set, precision, recall,
or F1 scoring. The required `optional_binding_rate` field is a six-decimal
operational metric computed as bound optional cells divided by optional cells
encountered, with JSON `null` for a zero-cell plan because its denominator is
zero. This resolves the prior conflict between an optional pattern and an
asserted mandatory answer field.

Add executable documentation tests to
`tests/unit/test_documentation_contract.py` with these exact assertions:

1. The first research heading and the first benchmark command in `README.md`
   are preceded by the independent disclaimer text from Section 4.
2. The README first-screen research table labels AQR/KG as primary and links
   to the federated semantic layer under a secondary heading after the AQR
   reproducibility command.
3. The first screen contains the literal labels `Implemented locally`,
   `Synthetic/simulated`, `Proposed future work`, and `Not implemented`.
4. `pyproject.toml` description contains `independent`, `synthetic`, and
   `research prototype`, and contains no affiliation or production claim.
5. `docs/research/cifre-interview-brief.md` contains the disclaimer,
   `cifre-synthetic-aqr-v1`, `results/latest_benchmark.json`, and
   `make PYTHON=.venv/bin/python research-verify`.
6. `docs/data-products.md`, `docs/governance.md`, and every mapping YAML use
   `repository-maintained synthetic contract` or `illustrative mapping`, not
   SAP ownership, publication, certification, or platform-connection claims.

The tests also assert that the benchmark artifact, lock artifact, provenance
manifest, and validation matrix paths exist after implementation. These are
acceptance tests, not prose review suggestions.

## 25. Exact affected paths, target, CI, and sequencing amendment

The complete implementation path set is:

```text
constraints/py312.txt
semantic/provenance/synthetic_source.yaml
semantic/ontology/sap_support.ttl
semantic/ontology/sap_ppms.ttl
semantic/ontology/sap_erp.ttl
semantic/ontology/sample-graph-valid.ttl
semantic/ontology/sample-graph-invalid.ttl
semantic/shapes/sap_support_shapes.ttl
semantic/shapes/sap_erp_shapes.ttl
semantic/taxonomy/sap_products.ttl
semantic/vocabulary/sap_erp.yaml
semantic/data/sap_support_graph.ttl
semantic/data/support-graph-invalid.ttl
src/semantic_layer/kg/loader.py
src/semantic_layer/kg/sap_dataset_generator.py
src/semantic_layer/reasoning/schema_linker.py
src/semantic_layer/reasoning/query_planner.py
src/semantic_layer/reasoning/text_to_sparql.py
src/semantic_layer/reasoning/reflective_agent.py
src/semantic_layer/research/benchmark_runner.py
tests/research/grounding_grammar.yaml
tests/research/result_schema.json
tests/research/benchmark_dataset_legacy.yaml
tests/research/benchmark_dataset_v1.yaml
tests/research/benchmark_dataset_v2.yaml
tests/semantic/test_sap_kg.py
tests/semantic/test_shacl.py
tests/unit/test_sap_reasoning.py
tests/unit/test_documentation_contract.py
Makefile
README.md
docs/research/cifre_phd_proposal.md
docs/research/cifre-interview-brief.md
docs/data-products.md
docs/governance.md
docs/verification-report.md
pyproject.toml
.github/workflows/ci.yml
results/latest_benchmark.json
```

The exact reproducibility target is `research-verify`; its CI job is also
named `research-verify` in `.github/workflows/ci.yml`. CI executes
`make PYTHON=.venv/bin/python research-verify` after installing
`constraints/py312.txt`. The job has a 120-second execution-time budget after
dependency installation; exceeding it fails the job and requires a measured
split into `research-verify-assets` and `research-verify-benchmark` jobs that
run the same checks. The target must always run graph generation/load,
isomorphism parity, the five validation-matrix checks, v1 and v2 benchmark
runs, JSON Schema validation, result recording, the full pytest suite, and
Ruff. No check may be removed to meet the time budget.

Task sequencing is therefore fixed: Task 1 records baseline evidence; Task 2
migrates every namespace and adds the provenance file; Task 3 adds the exact
validation matrix, datatype/closure fixes, crosswalk, and graph parity; Task 4
adds the grammar, JSON result schema, status-gated metrics, and repair ledger;
Task 5 creates v2 and the hashed v1/v2 artifact; Task 6 adds the locked
installation and `research-verify` CI target; Task 7 updates README, proposal,
interview brief, metadata, mappings, and verification report. A task is
accepted only when its listed files, tests, and exact contract fields are
present and the preceding task's verification remains green.

This section is normative and supersedes earlier shorthand that refers to one
benchmark file, one benchmark run, or an unspecified dependency installation:
the implementation uses both named corpus versions, the locked constraints
file, and the v1/v2 `corpus_runs` structure in `results/latest_benchmark.json`.

## 26. Final reproducibility corrections

This section resolves the remaining migration choices and supersedes any
earlier wording that conflicts with it.

### 26.1 Historical input, normalized corpora, and exact migration

The currently committed `tests/research/benchmark_dataset.yaml` remains
unchanged as historical input. The migration first creates the identical
archival copy `tests/research/benchmark_dataset_legacy.yaml`. The checked-in normalized
corpora are:

- `tests/research/benchmark_dataset_v1.yaml`: exactly 40 records, IDs `Q01`
  through `Q40`, `corpus_id: cifre-synthetic-aqr-v1`, `version: "1.0.0"`;
- `tests/research/benchmark_dataset_v2.yaml`: exactly 52 records, IDs `Q01`
  through `Q52`, `corpus_id: cifre-synthetic-aqr-v2`, `version: "2.0.0"`.

The historical file is an input only and is never evaluated. The migration is
the committed deterministic script `scripts/migrate_benchmark_v1.py`, invoked
as:

```bash
PYTHONPATH=src .venv/bin/python scripts/migrate_benchmark_v1.py \
  tests/research/benchmark_dataset_legacy.yaml \
  tests/research/benchmark_dataset_v1.yaml \
  tests/research/benchmark_dataset_v2.yaml
```

The script has no wall-clock, random, network, or model input. It validates
that the legacy file has exactly `Q01` through `Q40`, copies `question`,
`tier`, and `category`, converts `expected_notes` to the sole normalized field
`gold_note_numbers`, and writes all fields required by Section 26.2. The
normalized files never contain `expected_notes`; that name is accepted only
in the historical input. `Q01` through `Q24` preserve their historical gold
sets and expected status `SUCCESS`. For prerequisite closure, `Q25`, `Q28`,
and `Q31` have gold `["3012445", "3098110"]`; `Q26` and `Q30` have
`["3012445"]`; `Q27`, `Q29`, and `Q32` have `["3185002"]`. `Q33` through
`Q40` have expected status `EMPTY_RESULT` and empty strict gold sets; their
historical answers appear only in the migration manifest; their
`reflection_reason` is `STRICT_EMPTY_SEMANTIC_RELAXATION`.

V2 adds these exact records; it does not copy YAML bytes from v1 because the
normalized schema adds required fields:

| ID | Category | Expected status | Reason | Question |
| --- | --- | --- | --- | --- |
| Q41 | `negative_unknown_token` | `UNSUPPORTED` | `UNKNOWN_TOKEN` | `Find notes for an unlicensed oracle system.` |
| Q42 | `negative_unknown_token` | `UNSUPPORTED` | `UNKNOWN_TOKEN` | `Which notes resolve an unexplained outage?` |
| Q43 | `negative_unknown_entity` | `UNSUPPORTED` | `UNKNOWN_ENTITY` | `Find notes for alert UNKNOWN_ALERT.` |
| Q44 | `negative_unknown_entity` | `UNSUPPORTED` | `UNKNOWN_ENTITY` | `Find notes for component ZZ-UNKNOWN.` |
| Q45 | `negative_ambiguity` | `UNSUPPORTED` | `AMBIGUOUS_INPUT` | `Find notes for alert TIME_OUT and alert DBSQL_NO_MORE_CONNECTION.` |
| Q46 | `negative_ambiguity` | `UNSUPPORTED` | `AMBIGUOUS_INPUT` | `Find notes for component FI and component MM.` |
| Q47 | `negative_unsupported_intent` | `UNSUPPORTED` | `UNSUPPORTED_INTENT` | `Summarize the support landscape in a paragraph.` |
| Q48 | `negative_unsupported_intent` | `UNSUPPORTED` | `UNSUPPORTED_INTENT` | `Recommend a patch for this system.` |
| Q49 | `negative_strict_empty` | `EMPTY_RESULT` | `EMPTY_STRICT_RESULT` | `Find notes for alert TIME_OUT in component MM-PUR-PO at SP99.` |
| Q50 | `negative_strict_empty` | `EMPTY_RESULT` | `EMPTY_STRICT_RESULT` | `Find notes for alert DBSQL_NO_MORE_CONNECTION in component BC-DB-HDB at SP99.` |
| Q51 | `negative_strict_empty` | `EMPTY_RESULT` | `EMPTY_STRICT_RESULT` | `Find notes resolving alert TIME_OUT on S/4HANA 2022 in component SD-SLS.` |
| Q52 | `negative_strict_empty` | `EMPTY_RESULT` | `EMPTY_STRICT_RESULT` | `Find notes for alert CALL_FUNCTION_NOT_FOUND in component SD-SLS.` |

Q43 and Q44 are unknown entities, not unknown tokens, because the explicit
`alert` and `component` cues select their finite lexicons and the values are
absent. Q41 and Q42 are unknown tokens because their words are outside the
grammar filler set and are not preceded by an entity cue. Q49-Q52 are valid
grammar requests whose strict graph constraints return no bindings. Syntax and
execution failures are not corpus records: they are deterministic mocked
executor tests at `tests/research/test_failure_state_machine.py`, which supply
fixed parser/store exceptions and fixed input hashes.

The four strict-empty records are derivable from the grammar contract: Q49 and
Q50 classify `SP99` as a syntactically valid support-package constraint, then
execute strict queries with no matching graph rows; Q51 uses the
version-before-component alternative and likewise returns no strict bindings;
Q52 is a valid alert/component request whose strict graph constraints return
no bindings. None of these records is an unknown-entity abstention.

### 26.2 Normalized record schema

Every v1 and v2 record has exactly these fields, in this canonical key order:

```yaml
id: Q01
corpus_id: cifre-synthetic-aqr-v1
version: "1.0.0"
tier: 1
category: single_hop_alert
question: "..."
expected_status: SUCCESS
gold_note_numbers: ["3345100"]
reflection_reason: NONE
strict_constraints: true
gold_policy: exact_set
```

The legacy before-values live only in the migration manifest defined in
Section 27. `gold_note_numbers` is always a sorted unique string array;
unsupported and empty records use `[]`. `tier` is an integer 1-5 for Q01-Q40
and `0` for Q41-Q52. `strict_constraints` is always true in v2. No normalized
record has an omitted field or the legacy `expected_notes` field.

### 26.3 Grounding precedence and token classification

Intent precedence is exactly:

1. `PREREQUISITE_CLOSURE` when a prerequisite marker and one note number are
   present; any alert, component, or version token makes the request
   `UNSUPPORTED` rather than changing this intent.
2. `VERSION_FILTERED_SEARCH` when exactly one alert or component anchor and
   exactly one product-version or support-package qualifier are present. With
   both alert and component, the alert is the anchor and the component is an
   additional qualifier.
3. `ALERT_RESOLUTION` when exactly one alert is present without a version or
   support-package qualifier; a single component is an optional qualifier.
4. `COMPONENT_SEARCH` when exactly one component is present without an alert
   or version/package qualifier.
5. `NOTE_LOOKUP` when exactly one note number is present with a lookup verb.
6. `GENERAL_SEARCH` only when exactly one note number is present and none of
   the preceding markers apply; it compiles identically to `NOTE_LOOKUP`.

Two distinct values in any entity family produce `AMBIGUOUS_INPUT`. An
`unsupported_intent_marker` produces `UNSUPPORTED_INTENT` before token
classification. Classification is lexicon- and cue-based, never regex-based:
after the explicit cue `alert`, `component`, `S/4HANA`, or `note`, the next
token is looked up in that exact finite lexicon; a missing lookup is
`UNKNOWN_ENTITY`. The separate support-package syntax policy admits numeric
`SP` tokens as described above, while a nonnumeric or named package still
requires the finite lexicon. A token outside `filler_tokens` and outside a
cued entity slot is `UNKNOWN_TOKEN`. Thus `ORACLE` and `SYSTEM` are unknown
tokens unless they are part of a complete known identifier in a lexicon. This
classification happens before intent precedence and is recorded in
`grounding.failure_class`.

The filler vocabulary includes `and` and `an`; the grammar therefore accepts
the v2 wording `alert TIME_OUT and alert DBSQL_NO_MORE_CONNECTION` long enough
to classify it as `AMBIGUOUS_INPUT`, while `an unlicensed Oracle system` is rejected as
`UNKNOWN_TOKEN`.

`FI` and `MM` are both entries in the committed component lexicon. Q46 is
therefore an ambiguity between two known component values, not an unknown
entity or token; the parser must preserve both values in its diagnostic before
abstaining.

### 26.4 Complete result artifact schema

The top-level object in `results/latest_benchmark.json` has exactly these
required fields:

```json
{
  "schema_version": "1.0.0",
  "artifact_id": "cifre-aqr-benchmark-results",
  "generated_by": "semantic_layer.research.benchmark_runner",
  "canonicalization": {"encoding": "UTF-8", "key_order": "lexicographic", "metric_precision": 6},
  "hash_manifest": {"manifest_version": "1.0", "entries": [], "digest_sha256": "0000000000000000000000000000000000000000000000000000000000000000"},
  "environment": {"python_version": "3.12.0", "platform_system": "Linux", "platform_machine": "x86_64", "pip_version": "25.2", "lock_sha256": "0000000000000000000000000000000000000000000000000000000000000000", "packages": {}},
  "namespace_registry": {
    "cifsup": "https://example.org/cifre-kg/support#",
    "cifppms": "https://example.org/cifre-kg/ppms#",
    "cifdata": "https://example.org/cifre-kg/data/",
    "ciferp": "https://example.org/cifre-kg/erp#",
    "cifskos": "https://example.org/cifre-kg/vocabulary#",
    "cifmeta": "https://example.org/cifre-kg/meta#",
    "cifmetaid": "https://example.org/cifre-kg/id/meta/",
    "legacy_uris_rejected": ["http://data.sap.com/", "http://ontology.sap.com/", "https://sap.example/erp/"]
  },
  "validation": {"checks": [], "combined_graph": {"data_paths": [], "shape_paths": [], "construction_order": [], "combined_graph_sha256": "0000000000000000000000000000000000000000000000000000000000000000", "combined_shapes_sha256": "0000000000000000000000000000000000000000000000000000000000000000", "inference": "rdfs", "conforms": true}},
  "corpus_runs": [],
  "per_query": []
}
```

`corpus_runs` is an array of objects with exactly these required fields and
types: `corpus_id`, `version`, `path`, and `dataset_sha256` are strings;
`query_count` is a non-negative integer; `query_ids` and `result_ids` are
sorted, unique string arrays; `conditions` is the fixed two-element string
array `["deterministic_no_reflection_ablation", "deterministic_bounded_repair"]`;
and `aggregate` is the object specified below. `result_ids` references
`per_query` objects by the exact string
`<corpus_id>:<condition>:<query_id>`. `per_query` is the complete array of
records, sorted by `(corpus_id, condition, query_id)`. The generated benchmark
artifact must contain exactly two `corpus_runs` entries, one for v1 and one
for v2; the empty arrays in the compact root example are structural notation
only and are replaced before verification.

Each per-query record additionally requires `normalized_request` (string),
`original_constraints` (object containing sorted entity arrays and the exact
constraint predicates), `relaxation` (object), `answer_scope` (enum
`strict`, `relaxed_candidates`, or `none`), and `relaxed_candidates` (array).
`relaxation.attempted` is boolean, `relaxation.operations` is the ordered
ledger, `relaxation.strict_status` is the status before relaxation, and
`relaxed_candidates` contains rows with the same binding schema as
`bindings`. `answer_scope` is `none` for unsupported/error records, `strict`
for strict success or strict empty, and `relaxed_candidates` only when strict
empty candidates are displayed. `original_constraints` is never replaced by
the relaxed constraints.

`attempts` counts executed attempts, not indexes: unsupported records have
`0`, an initial execution has `1`, and an initial plus three repairs has `4`.
Ledger `attempt_index` is zero-based (`0` initial, `1..3` repairs), so
`attempts = 0` or `1 + max(attempt_index)` for records with execution
attempts. `bindings` includes the required `note` IRI, `noteNumber`, and
`title` fields; optional fields are explicit JSON `null`.

`namespace_registry` is required and has exactly these string-valued namespace
keys:
`cifsup`, `cifppms`, `cifdata`, `ciferp`, `cifskos`, `cifmeta`, and
`cifmetaid`. Its values are the exact IRIs in Sections 5.1 and 20. The object
also contains `legacy_uris_rejected`, a sorted array of the three forbidden
URI families.

`validation` is required with `checks` (an array of objects containing string
`check_id`, ordered string-array `data_paths`, ordered string-array
`shape_paths`, `inference`, `expected_conforms`, `observed_conforms`, aligned
string-array `data_sha256`, aligned string-array `shape_sha256`, string
`provenance_dataset_id`, and `result`). `inference` is `rdfs` for SHACL rows
and `algorithm` for `PREREQUISITE_CYCLE_DEPTH`; that algorithm row has an empty
`shape_paths` and `shape_sha256` array. `combined_graph` is an object containing ordered
`data_paths`, ordered `shape_paths`, `construction_order`,
`combined_graph_sha256`, `combined_shapes_sha256`, `inference`, and
`conforms`). `result` is the enum `PASS`, `EXPECTED_NONCONFORMANT`, or
`FAIL`; expected nonconformance is a passing negative control.

`expected_conforms` and `observed_conforms` are booleans for SHACL rows and
JSON `null` for `PREREQUISITE_CYCLE_DEPTH`. The algorithm row has an empty
`shape_paths` array and additionally requires `algorithm_cases`, an array of
exactly two objects with `fixture`, `cycle_detected`, `cycle_edges`,
`reachable_unique`, `target_excluded`, `depth_limit`, `truncated`, `status`,
and nullable `reason` fields. The cycle case has fixture
`support-prerequisite-cycle.ttl`, `cycle_detected: true`, edges
`[["A", "B"], ["B", "C"], ["C", "A"]]`, `reachable_unique: ["B", "C"]`,
`target_excluded: true`, `depth_limit: 16`, `truncated: false`, `status:
"SUCCESS"`, and `reason: null`. The depth case has fixture
`support-prerequisite-depth17.ttl`, `cycle_detected: false`,
`cycle_edges: []`, `reachable_unique: ["N1", "N2", "N3", "N4", "N5",
"N6", "N7", "N8", "N9", "N10", "N11", "N12", "N13", "N14", "N15",
"N16"]`, `target_excluded: true`, `depth_limit: 16`, `truncated: true`,
`status: "EMPTY_RESULT"`, and
`reason: "PREREQUISITE_DEPTH_EXCEEDED"`.

Every `aggregate` has exactly these required keys and types:

```json
{
  "query_count": 52,
  "status_counts": {"SUCCESS": 32, "UNSUPPORTED": 8, "SYNTAX_ERROR": 0, "EXECUTION_ERROR": 0, "EMPTY_RESULT": 12},
  "status_accuracy": {"value": "1.000000", "numerator": 52, "denominator": 52},
  "answer_metrics": {
    "applicable_count": 32,
    "not_applicable_count": 20,
    "exact_set": {"value": "0.937500", "numerator": 30, "denominator": 32},
    "precision": {"value": "0.968750", "numerator": "31.000000", "denominator": "32.000000"},
    "recall": {"value": "0.937500", "numerator": "30.000000", "denominator": "32.000000"},
    "f1": {"value": "0.950000", "numerator": "30.400000", "denominator": "32.000000"},
    "micro": {
      "exact_set": {"value": "0.937500", "numerator": 30, "denominator": 32},
      "precision": {"value": "0.968750", "numerator": "31.000000", "denominator": "32.000000"},
      "recall": {"value": "0.937500", "numerator": "30.000000", "denominator": "32.000000"},
      "f1": {"value": "0.950000", "numerator": "30.400000", "denominator": "32.000000"}
    },
    "macro": {
      "exact_set": {"value": "0.937500", "numerator": "30.000000", "denominator": "32.000000"},
      "precision": {"value": "0.968750", "numerator": "31.000000", "denominator": "32.000000"},
      "recall": {"value": "0.937500", "numerator": "30.000000", "denominator": "32.000000"},
      "f1": {"value": "0.950000", "numerator": "30.400000", "denominator": "32.000000"}
    },
    "by_tier": {},
    "by_category": {}
  },
  "operational_metrics": {
    "syntax_success_rate": {"value": "1.000000", "numerator": 52, "denominator": 52},
    "execution_success_rate": {"value": "0.846154", "numerator": 44, "denominator": 52},
    "recovery_attempt_rate": {"value": "0.153846", "numerator": 8, "denominator": 52},
    "recovery_success_rate": {"value": "0.500000", "numerator": 4, "denominator": 8},
    "strict_empty_rate": {"value": "0.230769", "numerator": 12, "denominator": 52},
    "unsupported_rejection_rate": {"value": "1.000000", "numerator": 8, "denominator": 8},
    "optional_binding_rate": {"value": null, "numerator": 0, "denominator": 0}
  }
}
```

The numeric values above are schema examples, not claimed results; the runner
must compute them. Every metric object has integer or six-decimal-string
`numerator`, `denominator`, and nullable six-decimal-string `value`; `value`
is JSON `null` exactly when its denominator is zero. `status_counts` has all
five status enum keys, including zero values. The sole authoritative schema is
`tests/research/result_schema.json`; all examples and implementations must
validate against it.

`answer_metrics.micro` and `answer_metrics.macro` each contain exact-set,
precision, recall, and F1 metrics. Every value in `answer_metrics.by_tier` and
`answer_metrics.by_category` is an `aggregate_slice` with the same four direct
metrics, both micro/macro groups, all five status counts, applicable and
non-applicable denominators, query count, and `optional_binding_rate`.
`operational_metrics.optional_binding_rate` is the same six-decimal metric at
the overall scope. These are the only metric names; Section 8.3's macro/micro,
tier/category, status, and optional-binding requirements map to these schema
fields exactly.

`tests/research/result_schema.json` is the machine-authoritative root schema;
it is not a per-query-only schema. Its complete root contract is the following
schema (the implementation may factor the `$defs` into separate files only
when they are referenced by this exact `$id`):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.org/cifre-kg/schema/research-result-root-1.0.0.json",
  "title": "CIFRE benchmark result root",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "artifact_id", "generated_by", "canonicalization", "hash_manifest", "environment", "namespace_registry", "validation", "corpus_runs", "per_query"],
  "properties": {
    "schema_version": {"const": "1.0.0"},
    "artifact_id": {"type": "string"},
    "generated_by": {"type": "string"},
    "canonicalization": {
      "type": "object",
      "additionalProperties": false,
      "required": ["encoding", "key_order", "metric_precision"],
      "properties": {
        "encoding": {"const": "UTF-8"},
        "key_order": {"const": "lexicographic"},
        "metric_precision": {"const": 6}
      }
    },
    "hash_manifest": {
      "type": "object",
      "additionalProperties": false,
      "required": ["manifest_version", "entries", "digest_sha256"],
      "properties": {
        "manifest_version": {"const": "1.0"},
        "entries": {"type": "array", "items": {"type": "object"}},
        "digest_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}
      }
    },
    "environment": {
      "type": "object",
      "additionalProperties": false,
      "required": ["python_version", "platform_system", "platform_machine", "pip_version", "lock_sha256", "packages"],
      "properties": {
        "python_version": {"type": "string"},
        "platform_system": {"type": "string"},
        "platform_machine": {"type": "string"},
        "pip_version": {"type": "string"},
        "lock_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "packages": {"type": "object", "additionalProperties": {"type": "string"}}
      }
    },
    "namespace_registry": {
      "type": "object",
      "additionalProperties": false,
      "required": ["cifsup", "cifppms", "cifdata", "ciferp", "cifskos", "cifmeta", "cifmetaid", "legacy_uris_rejected"],
      "properties": {
        "cifsup": {"const": "https://example.org/cifre-kg/support#"},
        "cifppms": {"const": "https://example.org/cifre-kg/ppms#"},
        "cifdata": {"const": "https://example.org/cifre-kg/data/"},
        "ciferp": {"const": "https://example.org/cifre-kg/erp#"},
        "cifskos": {"const": "https://example.org/cifre-kg/vocabulary#"},
        "cifmeta": {"const": "https://example.org/cifre-kg/meta#"},
        "cifmetaid": {"const": "https://example.org/cifre-kg/id/meta/"},
        "legacy_uris_rejected": {"type": "array", "const": ["http://data.sap.com/", "http://ontology.sap.com/", "https://sap.example/erp/"]}
      }
    },
    "validation": {"$ref": "#/$defs/validation"},
    "corpus_runs": {"type": "array", "items": {"$ref": "#/$defs/corpus_run"}},
    "per_query": {"type": "array", "items": {"$ref": "#/$defs/per_query"}, "uniqueItems": true}
  },
  "$defs": {
    "status": {"enum": ["SUCCESS", "UNSUPPORTED", "SYNTAX_ERROR", "EXECUTION_ERROR", "EMPTY_RESULT"]},
    "metric": {
      "type": "object",
      "additionalProperties": false,
      "required": ["value", "numerator", "denominator"],
      "properties": {
        "value": {"oneOf": [{"type": "null"}, {"type": "string", "pattern": "^(0\\.[0-9]{6}|1\\.000000)$"}]},
        "numerator": {"oneOf": [{"type": "integer", "minimum": 0}, {"type": "string", "pattern": "^[0-9]+\\.[0-9]{6}$"}]},
        "denominator": {"oneOf": [{"type": "integer", "minimum": 0}, {"type": "string", "pattern": "^[0-9]+\\.[0-9]{6}$"}]}
      }
    },
    "status_counts": {
      "type": "object",
      "additionalProperties": false,
      "required": ["SUCCESS", "UNSUPPORTED", "SYNTAX_ERROR", "EXECUTION_ERROR", "EMPTY_RESULT"],
      "properties": {
        "SUCCESS": {"type": "integer", "minimum": 0},
        "UNSUPPORTED": {"type": "integer", "minimum": 0},
        "SYNTAX_ERROR": {"type": "integer", "minimum": 0},
        "EXECUTION_ERROR": {"type": "integer", "minimum": 0},
        "EMPTY_RESULT": {"type": "integer", "minimum": 0}
      }
    },
    "metric_group": {
      "type": "object",
      "additionalProperties": false,
      "required": ["exact_set", "precision", "recall", "f1"],
      "properties": {
        "exact_set": {"$ref": "#/$defs/metric"},
        "precision": {"$ref": "#/$defs/metric"},
        "recall": {"$ref": "#/$defs/metric"},
        "f1": {"$ref": "#/$defs/metric"}
      }
    },
    "aggregate_slice": {
      "type": "object",
      "additionalProperties": false,
      "required": ["query_count", "status_counts", "applicable_count", "not_applicable_count", "exact_set", "precision", "recall", "f1", "micro", "macro", "optional_binding_rate"],
      "properties": {
        "query_count": {"type": "integer", "minimum": 0},
        "status_counts": {"$ref": "#/$defs/status_counts"},
        "applicable_count": {"type": "integer", "minimum": 0},
        "not_applicable_count": {"type": "integer", "minimum": 0},
        "exact_set": {"$ref": "#/$defs/metric"},
        "precision": {"$ref": "#/$defs/metric"},
        "recall": {"$ref": "#/$defs/metric"},
        "f1": {"$ref": "#/$defs/metric"},
        "micro": {"$ref": "#/$defs/metric_group"},
        "macro": {"$ref": "#/$defs/metric_group"},
        "optional_binding_rate": {"$ref": "#/$defs/metric"}
      }
    },
    "aggregate": {
      "type": "object",
      "additionalProperties": false,
      "required": ["query_count", "status_counts", "status_accuracy", "answer_metrics", "operational_metrics"],
      "properties": {
        "query_count": {"type": "integer", "minimum": 0},
        "status_counts": {"$ref": "#/$defs/status_counts"},
        "status_accuracy": {"$ref": "#/$defs/metric"},
        "answer_metrics": {
          "type": "object",
          "additionalProperties": false,
          "required": ["applicable_count", "not_applicable_count", "exact_set", "precision", "recall", "f1", "micro", "macro", "by_tier", "by_category"],
          "properties": {
            "applicable_count": {"type": "integer", "minimum": 0},
            "not_applicable_count": {"type": "integer", "minimum": 0},
            "exact_set": {"$ref": "#/$defs/metric"},
            "precision": {"$ref": "#/$defs/metric"},
            "recall": {"$ref": "#/$defs/metric"},
            "f1": {"$ref": "#/$defs/metric"},
            "micro": {"$ref": "#/$defs/metric_group"},
            "macro": {"$ref": "#/$defs/metric_group"},
            "by_tier": {"type": "object", "additionalProperties": {"$ref": "#/$defs/aggregate_slice"}},
            "by_category": {"type": "object", "additionalProperties": {"$ref": "#/$defs/aggregate_slice"}}
          }
        },
        "operational_metrics": {
          "type": "object",
          "additionalProperties": false,
          "required": ["syntax_success_rate", "execution_success_rate", "recovery_attempt_rate", "recovery_success_rate", "strict_empty_rate", "unsupported_rejection_rate", "optional_binding_rate"],
          "properties": {
            "syntax_success_rate": {"$ref": "#/$defs/metric"},
            "execution_success_rate": {"$ref": "#/$defs/metric"},
            "recovery_attempt_rate": {"$ref": "#/$defs/metric"},
            "recovery_success_rate": {"$ref": "#/$defs/metric"},
            "strict_empty_rate": {"$ref": "#/$defs/metric"},
            "unsupported_rejection_rate": {"$ref": "#/$defs/metric"},
            "optional_binding_rate": {"$ref": "#/$defs/metric"}
          }
        }
      }
    },
    "corpus_run": {
      "type": "object",
      "additionalProperties": false,
      "required": ["corpus_id", "version", "path", "dataset_sha256", "query_count", "query_ids", "conditions", "aggregate", "result_ids"],
      "properties": {
        "corpus_id": {"type": "string"},
        "version": {"type": "string"},
        "path": {"type": "string"},
        "dataset_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "query_count": {"type": "integer", "minimum": 0},
        "query_ids": {"type": "array", "uniqueItems": true, "items": {"type": "string"}},
        "conditions": {"const": ["deterministic_no_reflection_ablation", "deterministic_bounded_repair"]},
        "aggregate": {"$ref": "#/$defs/aggregate"},
        "result_ids": {"type": "array", "uniqueItems": true, "items": {"type": "string"}}
      }
    },
    "binding": {
      "type": "object",
      "required": ["note", "noteNumber", "title"],
      "properties": {
        "note": {"type": "string"},
        "noteNumber": {"type": "string"},
        "title": {"type": ["string", "null"]}
      }
    },
    "per_query_metrics": {
      "type": "object",
      "additionalProperties": false,
      "required": ["applicable", "exact_set", "precision", "recall", "f1"],
      "properties": {
        "applicable": {"type": "boolean"},
        "exact_set": {"type": ["boolean", "null"]},
        "precision": {"type": ["string", "null"], "pattern": "^(0\\.[0-9]{6}|1\\.000000)$"},
        "recall": {"type": ["string", "null"], "pattern": "^(0\\.[0-9]{6}|1\\.000000)$"},
        "f1": {"type": ["string", "null"], "pattern": "^(0\\.[0-9]{6}|1\\.000000)$"}
      }
    },
    "provenance": {
      "type": "object",
      "additionalProperties": false,
      "required": ["dataset_id", "source_kind", "official", "graph_sha256", "citation"],
      "properties": {
        "dataset_id": {"type": "string"},
        "source_kind": {"const": "synthetic_fixture"},
        "official": {"const": false},
        "graph_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "citation": {"type": "string"}
      }
    },
    "per_query": {
      "type": "object",
      "additionalProperties": false,
      "required": ["schema_version", "corpus_id", "query_id", "condition", "question", "normalized_request", "expected_status", "observed_status", "reason_code", "original_constraints", "grounding", "plan", "sparql", "attempts", "repair", "relaxation", "answer_scope", "relaxed_candidates", "bindings", "predicted_note_numbers", "gold_note_numbers", "metrics", "provenance"],
      "properties": {
        "schema_version": {"const": "1.0.0"},
        "corpus_id": {"type": "string"},
        "query_id": {"type": "string"},
        "condition": {"enum": ["deterministic_no_reflection_ablation", "deterministic_bounded_repair"]},
        "question": {"type": "string"},
        "normalized_request": {"type": "string"},
        "expected_status": {"$ref": "#/$defs/status"},
        "observed_status": {"$ref": "#/$defs/status"},
        "reason_code": {"type": "string"},
        "original_constraints": {"type": "object"},
        "grounding": {"oneOf": [{"type": "null"}, {"type": "object"}]},
        "plan": {"oneOf": [{"type": "null"}, {"type": "object"}]},
        "sparql": {"oneOf": [{"type": "null"}, {"type": "object"}]},
        "attempts": {"type": "integer", "minimum": 0, "maximum": 4},
        "repair": {"type": "object"},
        "relaxation": {"type": "object"},
        "answer_scope": {"enum": ["strict", "relaxed_candidates", "none"]},
        "relaxed_candidates": {"type": "array", "items": {"$ref": "#/$defs/binding"}},
        "bindings": {"type": "array", "items": {"$ref": "#/$defs/binding"}},
        "predicted_note_numbers": {"type": "array", "uniqueItems": true, "items": {"type": "string", "pattern": "^[0-9]{7}$"}},
        "gold_note_numbers": {"type": "array", "uniqueItems": true, "items": {"type": "string", "pattern": "^[0-9]{7}$"}},
        "metrics": {"$ref": "#/$defs/per_query_metrics"},
        "provenance": {"$ref": "#/$defs/provenance"}
      }
    },
    "validation": {
      "type": "object",
      "additionalProperties": false,
      "required": ["checks", "combined_graph"],
      "properties": {
        "checks": {"type": "array", "items": {"type": "object"}},
        "combined_graph": {"type": "object"}
      }
    }
  }
}
```

### 26.5 Complete status/reason pairs and repair state machine

The query status/reason relation is closed:

| Status | Allowed final reasons |
| --- | --- |
| `SUCCESS` | `NONE` only |
| `UNSUPPORTED` | `UNKNOWN_TOKEN`, `UNKNOWN_ENTITY`, `AMBIGUOUS_INPUT`, `AMBIGUOUS_INTENT`, `MULTIPLE_DISTINCT_ENTITIES`, `UNSUPPORTED_INTENT`, `MISSING_REQUIRED_ENTITY` |
| `SYNTAX_ERROR` | `UNBOUND_REQUIRED_PROJECTION`, `SPARQL_SYNTAX`, `NO_OP_REPAIR`, `REPAIR_BUDGET_EXHAUSTED` |
| `EXECUTION_ERROR` | `SPARQL_EXECUTION`, `PROVENANCE_MISSING`, `NO_OP_REPAIR`, `REPAIR_BUDGET_EXHAUSTED` |
| `EMPTY_RESULT` | `EMPTY_STRICT_RESULT`, `RELAX_SUPPORT_PACKAGE`, `WIDEN_COMPONENT`, `PREREQUISITE_DEPTH_EXCEEDED` |

`INVALID_DATASET` and `HASH_MISMATCH` are artifact-level `artifact_errors`
and are forbidden as per-query reasons. Add `AMBIGUOUS_INPUT`, `NO_OP_REPAIR`,
and `PREREQUISITE_DEPTH_EXCEEDED` to the reason enum.

The closed state machine is:

| State | Event | Next state | Final status/reason |
| --- | --- | --- | --- |
| `INITIAL` | grammar abstention | `FINAL` | `UNSUPPORTED` / grammar reason |
| `INITIAL` with no-reflection condition | success | `FINAL` | `SUCCESS` / `NONE` |
| `INITIAL` with no-reflection condition | syntax/execution/empty | `FINAL` | corresponding error or `EMPTY_RESULT` |
| `INITIAL` bounded | syntax | `SYNTAX_REPAIR` | not final while budget remains |
| `INITIAL` bounded | execution | `EXECUTION_REPAIR` | not final while budget remains |
| `INITIAL` bounded | empty with relaxable predicate | `SEMANTIC_RELAXATION` | not final while budget remains |
| `INITIAL` bounded | empty without relaxable predicate | `FINAL` | `EMPTY_RESULT` / `EMPTY_STRICT_RESULT` |
| `SYNTAX_REPAIR` or `EXECUTION_REPAIR` | repaired strict success | `FINAL` | `SUCCESS` / `NONE`, `recovered=true` |
| `SYNTAX_REPAIR` or `EXECUTION_REPAIR` | same query/plan (no-op) | `FINAL` | error / `NO_OP_REPAIR` |
| `SYNTAX_REPAIR` or `EXECUTION_REPAIR` | another failure with budget | same repair state | not final |
| `SEMANTIC_RELAXATION` | candidates found | `FINAL` | `EMPTY_RESULT` / relaxation reason, `answer_scope=relaxed_candidates` |
| `SEMANTIC_RELAXATION` | no candidates | `FINAL` | `EMPTY_RESULT` / relaxation reason |
| any repair state | repair index 3 fails | `FINAL` | last error / `REPAIR_BUDGET_EXHAUSTED` |
| `SEMANTIC_RELAXATION` after a syntax/execution repair | any result | `FINAL` | `EMPTY_RESULT` / relaxation reason; `recovery_success=false` |

`max_repairs=3` is fixed for both conditions, but the no-reflection condition
never enters a repair state. Every attempted execution ledger entry stores
the complete `sparql_text` string, not merely a digest; the same text appears
in the corresponding top-level `sparql.initial` or `sparql.final` field. Thus
every attempted query is retrievable from the checked-in result artifact.

### 26.6 Hash manifest and validation construction

The hash manifest expands this exact ordered glob list, using repository-root
relative POSIX paths and bytewise lexical order within each glob, then sorts
the complete expanded path list once and removes duplicates:

```text
.github/workflows/ci.yml
Makefile
pyproject.toml
constraints/py312.txt
scripts/**/*.py
semantic/**/*.ttl
semantic/**/*.yaml
semantic/**/*.json
src/semantic_layer/**/*.py
data/**/*.py
tests/**/*.py
tests/**/*.yaml
tests/**/*.json
examples/**/*
README.md
docs/**/*.md
docs/**/*.json
docs/**/*.sql
mappings/**/*.yaml
data_products/**/*.yaml
results/**/*.json
results/**/*.sql
```

This includes both valid/invalid graph fixtures, `src/semantic_layer/semantic_validation.py`,
`src/semantic_layer/validation.py`, all current AQR consumers, generator and
loader code, integration/unit/semantic/vocabulary/documentation tests, and
the migration/failure scripts. Exclude `.git/`, `.venv/`,
`results/latest_benchmark.json`, and untracked files. Other tracked result
JSON/SQL consumers are included. The sorted manifest is the complete
research-reproduce input;
each path has its byte SHA-256 and length, and the digest uses the
`path\\0sha256\\0byte_length\\n` records specified in Section 17.1.

The canonical combined graph is constructed in this exact order into a fresh
RDFLib `Graph`: ontology support, ontology PPMS, checked-in support data,
ontology ERP, valid ERP sample. The exact paths are
`semantic/ontology/sap_support.ttl`, `semantic/ontology/sap_ppms.ttl`,
`semantic/data/sap_support_graph.ttl`, `semantic/ontology/sap_erp.ttl`, and
`semantic/ontology/sample-graph-valid.ttl`. Shapes are unioned in the order
`semantic/shapes/sap_support_shapes.ttl`, then
`semantic/shapes/sap_erp_shapes.ttl`. The combined graph and shapes are each
serialized to temporary canonical N-Triples for hashes, then validated as one
RDFLib graph with `inference: "rdfs"`. The graph-isomorphism check compares
the generated support graph with its checked-in artifact before the combined
load.

The committed prerequisite-cycle fixture is
`semantic/data/support-prerequisite-cycle.ttl`. The planner's exact traversal
policy is `MAX_PREREQUISITE_DEPTH=16`: it compiles a union of the valid SPARQL
property paths of lengths 1 through 16 over
`cifsup:hasPrerequisiteNote`, deduplicates note IRIs, excludes the target note,
and returns `EMPTY_RESULT` / `PREREQUISITE_DEPTH_EXCEEDED` when a reachable
edge would require hop 17. The cycle fixture is three notes A→B→C→A and
must return B and C for A without looping or returning A.

This bounded union supersedes the unbounded `cifsup:hasPrerequisiteNote+`
shorthand in Section 6.3; `+` describes the intended closure relation, while
the generated union is the executable bounded query.

### 26.7 Complete live affected-file set

The live implementation set is the exact union of the paths below; the prior
shorter table is superseded:

```text
.github/workflows/ci.yml
Makefile
pyproject.toml
constraints/py312.txt
scripts/**/*.py
semantic/**/*.ttl
semantic/**/*.yaml
semantic/**/*.json
semantic/provenance/synthetic_source.yaml
src/semantic_layer/**/*.py
data/**/*.py
tests/conftest.py
tests/integration/**/*.py
tests/unit/**/*.py
tests/semantic/**/*.py
tests/research/**/*.py
tests/research/**/*.yaml
tests/research/**/*.json
tests/research/benchmark_migration_manifest_v1.yaml
tests/golden/**/*.py
tests/golden/**/*.yaml
examples/**/*
mappings/**/*.yaml
data_products/**/*.yaml
README.md
docs/**/*.md
docs/**/*.json
docs/**/*.sql
results/**/*.json
results/**/*.sql
results/latest_benchmark.json
```

The set explicitly includes `src/semantic_layer/semantic_validation.py`,
`src/semantic_layer/validation.py`, `src/semantic_layer/kg/`,
`src/semantic_layer/reasoning/`, `src/semantic_layer/research/`, all current
integration/unit/semantic/vocabulary/documentation tests, and every current
consumer discovered by the repository globs. The implementation must update
all references in this set or the namespace/claim contract fails.

Claim scans also traverse every tracked `examples/**` file, `README.md`,
`docs/**/*.md`, `docs/**/*.json`, `docs/**/*.sql`, `mappings/**/*.yaml`,
`data_products/**/*.yaml`, `results/**/*.json`, and `results/**/*.sql`.
Generated query-plan JSON and SQL documentation is therefore included whether
it is stored under `docs/`, `examples/`, or a checked-in result directory; no
generated semantic identifier consumer is outside the scan. The only excluded
result path is the self-generated `results/latest_benchmark.json` artifact
while its own hash manifest is being computed.

### 26.8 Crosswalk RDF correction

The only permitted crosswalk form is a mapping-entry model with a coherent RDF
domain:

```turtle
cifmetaid:crosswalk-entry-product-automotive a cifmeta:CrosswalkEntry ;
    cifmeta:sourceResource ciferp:ProductAutomotive ;
    cifmeta:targetConcept cifskos:ProductAutomotive ;
    cifmeta:crosswalkVersion "1.0"^^xsd:string .
```

`cifmeta:sourceResource` has domain `cifmeta:CrosswalkEntry` and range
`ciferp:Product`; `cifmeta:targetConcept` has domain
`cifmeta:CrosswalkEntry` and range `skos:Concept`.
`cifmeta:CrosswalkEntry`, `sourceResource`, and `targetConcept` are added to
the closed metadata vocabulary. No `ciferp` resource is used as the subject
of a predicate whose declared domain is `cifmeta:CrosswalkEntry`, and no SKOS
concept is assigned an OWL class type.

## 27. Checked-in legacy-gold migration manifest

The exact migration manifest is
`tests/research/benchmark_migration_manifest_v1.yaml`. It is generated and
validated by `scripts/migrate_benchmark_v1.py` and is an input to
`results/latest_benchmark.json`. Its schema is:

```yaml
schema_version: "1.0"
source_path: tests/research/benchmark_dataset.yaml
archival_path: tests/research/benchmark_dataset_legacy.yaml
normalized_path: tests/research/benchmark_dataset_v1.yaml
record_ids: [Q01, Q02, Q03, Q04, Q05, Q06, Q07, Q08, Q09, Q10,
  Q11, Q12, Q13, Q14, Q15, Q16, Q17, Q18, Q19, Q20,
  Q21, Q22, Q23, Q24, Q25, Q26, Q27, Q28, Q29, Q30,
  Q31, Q32, Q33, Q34, Q35, Q36, Q37, Q38, Q39, Q40]
changes:
  - change_id: normalized_schema_v1
    record_ids: [Q01, Q02, Q03, Q04, Q05, Q06, Q07, Q08, Q09, Q10,
      Q11, Q12, Q13, Q14, Q15, Q16, Q17, Q18, Q19, Q20,
      Q21, Q22, Q23, Q24, Q25, Q26, Q27, Q28, Q29, Q30,
      Q31, Q32, Q33, Q34, Q35, Q36, Q37, Q38, Q39, Q40]
    before: {field: expected_notes, type: legacy_yaml}
    after: {field: gold_note_numbers, type: sorted_unique_string_array}
    migration_reason: SCHEMA_NORMALIZATION
    policy_citation: Section 26.2
    derivation_query:
      kind: policy
      text: "Convert legacy expected_notes to sorted gold_note_numbers."
      graph_sha256: "0000000000000000000000000000000000000000000000000000000000000000"
      result: {gold_before: [], gold_after: []}
      result_sha256: "0000000000000000000000000000000000000000000000000000000000000000"
records: []
review:
  reviewer_id: repository-maintainer
  signoff_required: true
  signed_off: true
```

`records` is required to contain exactly 40 entries in Q01-Q40 order. Each
entry has `id`, `category_before`, `category_after`, `gold_before`,
`gold_after`, `status_before`, `status_after`, `schema_before`,
`schema_after`, `migration_reason`, `policy_citation`, `derivation_query`,
`reviewer_id`, and `signed_off`. `derivation_query` has `kind` (`canonical_sparql`
or `policy`), the canonical query or policy `text`, `graph_sha256`, the
deterministic `result`, and `result_sha256`; the result is the exact evidence
used to derive `gold_after` (or to prove schema-only normalization).
The script rejects a missing entry, duplicate ID, changed category without a
`migration_reason`, a missing derivation field, or any unsigned record. The
`migration_reason` enum is exactly `SCHEMA_NORMALIZATION`,
`PREREQUISITE_CLOSURE_EXPANSION`, `PREREQUISITE_CLOSURE_NORMALIZATION`, or
`STRICT_CONSTRAINT_STATUS_CORRECTION`. Every entry uses
`migration_reason: SCHEMA_NORMALIZATION` for the field rename and the following exact
additional reasons where semantics change:

| IDs | `gold_before` | `gold_after` | `status_before` | `status_after` | `migration_reason` | Policy citation |
| --- | --- | --- | --- | --- | --- | --- |
| Q01-Q24 | historical `expected_notes` converted to sorted strings | same note set | `SUCCESS` | `SUCCESS` | `SCHEMA_NORMALIZATION` | Sections 26.1-26.2 |
| Q25, Q28, Q31 | `[3098110]` | `[3012445, 3098110]` | `SUCCESS` | `SUCCESS` | `PREREQUISITE_CLOSURE_EXPANSION` | Sections 6.3 and 26.1 |
| Q26, Q30 | `[3012445]` | `[3012445]` | `SUCCESS` | `SUCCESS` | `PREREQUISITE_CLOSURE_NORMALIZATION` | Sections 6.3 and 26.1 |
| Q27, Q29, Q32 | `[3185002]` | `[3185002]` | `SUCCESS` | `SUCCESS` | `PREREQUISITE_CLOSURE_NORMALIZATION` | Sections 6.3 and 26.1 |
| Q33-Q40 | historical `expected_notes` | `[]` | `SUCCESS` | `EMPTY_RESULT` | `STRICT_CONSTRAINT_STATUS_CORRECTION` | Sections 7.1, 18.1, and 26.1 |

For Q01-Q24, `gold_before` is the exact array read from the archived YAML;
the table's “same note set” means only type/order normalization. For Q33-Q40
the before array is preserved in the manifest, never copied into normalized
records or strict result scoring. `schema_before` and `schema_after` are
objects containing the complete field-name sets and their types, so the
manifest explains the schema change on every record, including unchanged
gold/status records. The `policy_citation` must name one of the exact section
references above. The reviewer fields are required evidence, not prose.
