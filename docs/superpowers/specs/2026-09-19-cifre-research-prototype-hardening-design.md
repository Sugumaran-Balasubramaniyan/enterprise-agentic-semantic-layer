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
labels match. Use the explicit reviewed mapping
`ciferp:canonicalConcept` when a class is linked to a taxonomy concept. The
mapping is not an implicit `rdf:type` assertion.

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
record `legacy_expected_notes`, `revised_expected_notes`, a reason, the graph
query/policy used to derive the new set, and reviewer sign-off in the dataset
metadata or migration manifest. Gold sets are justified by the current graph
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
| Benchmark | `src/semantic_layer/research/benchmark_runner.py`, `tests/research/benchmark_dataset.yaml`, new `results/latest_benchmark.json` | Real conditions only; exact-set and set metrics; hashes/per-query records |
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

Keep the 40-query v1 at `tests/research/benchmark_dataset.yaml` unchanged in
scope and create `tests/research/benchmark_dataset_v2.yaml` with the 12
negative records specified in Section 23. Add migration metadata to v1, remove
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
    sequence: [lookup_verb, filler*, note_number]
  - id: alert_resolution
    intent: ALERT_RESOLUTION
    sequence: [question_word, filler*, alert_code, filler*, component_code?, product_version?, support_package?, priority?]
  - id: component_search
    intent: COMPONENT_SEARCH
    sequence: [question_word, filler*, component_code, filler*, product_version?, support_package?, priority?]
  - id: version_filtered_search
    intent: VERSION_FILTERED_SEARCH
    sequence: [question_word, filler*, alert_code|component_code, filler*, product_version|support_package, filler*, priority?]
  - id: prerequisite_closure
    intent: PREREQUISITE_CLOSURE
    sequence: [question_word, filler*, prerequisite_marker, filler*, note_number]
  - id: general_note_lookup
    intent: GENERAL_SEARCH
    sequence: [note_number]
lookup_verb: [find, get, identify, retrieve, what, which]
question_word: [find, get, identify, what, which, list]
prerequisite_marker: [dependency, dependencies, prerequisite, prerequisites]
```

`filler*` consumes only the declared `filler_tokens`; `?` consumes zero or
one slot; `|` consumes exactly one alternative. The sequence is token-based,
not a permissive regular expression. The parser rejects a sequence that binds
an optional slot before its required anchor or binds two alternatives from the
same family.

The entity slots are exactly the linker vocabulary sets already declared in
`schema_linker.py`: `alert_code`, `component_code`, `product_version`,
`software_component`, `support_package`, `note_number`, and `priority`.
Entity values are case-insensitive for matching and are emitted in their
canonical spelling. A seven-digit note number is accepted only as a
`note_number`; an `SPnn` token is accepted only as a `support_package`; the
remaining entity forms must occur in the finite vocabulary. A distinct second
value in any entity family is an ambiguity and causes abstention. Repeating
the same canonical value is harmless.

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
`PREREQUISITE_CLOSURE`; an alert selects `ALERT_RESOLUTION`; a component
without an alert selects `COMPONENT_SEARCH`; a version/support-package
qualifier with an alert or component selects `VERSION_FILTERED_SEARCH`; a
single note number with lookup wording selects `NOTE_LOOKUP`; the only
remaining accepted case is `GENERAL_SEARCH` with exactly one note number.
Conflicting intent markers, no required slot, multiple distinct values,
unknown tokens, and a version/package qualifier without an alert or component
return `UNSUPPORTED` before planning. The linker never invents an entity from
an unrecognised spelling, parent, synonym, or external capability.

The grammar fixtures must include these exact cases:

| Input | Expected intent/status | Extracted entities |
| --- | --- | --- |
| `Retrieve the title and details for SAP Note 3012445.` | `NOTE_LOOKUP` / `SUCCESS` after execution | `note_number=[3012445]` |
| `Which SAP note resolves alert TIME_OUT in component MM-PUR-PO?` | `ALERT_RESOLUTION` / `SUCCESS` after execution | `alert_code=[TIME_OUT]`, `component_code=[MM-PUR-PO]` |
| `What are the prerequisite notes required for SAP Note 3109922?` | `PREREQUISITE_CLOSURE` / `SUCCESS` after execution | `note_number=[3109922]` |
| `Find notes valid for S/4HANA 2023.` | `UNSUPPORTED` / `UNSUPPORTED` | no anchored alert/component |
| `Find notes for TIME_OUT and DBSQL_NO_MORE_CONNECTION.` | `UNSUPPORTED` / `UNSUPPORTED` | two distinct `alert_code` values |
| `Find notes for UNKNOWN_ALERT.` | `UNSUPPORTED` / `UNSUPPORTED` | `UNKNOWN_TOKEN` |
| `Find notes for TIME_OUT in component BC-DB-HDB for an Oracle system.` | `UNSUPPORTED` / `UNSUPPORTED` | `UNKNOWN_TOKEN=oracle/system` |

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
  "query_id": "Q01",
  "condition": "deterministic_bounded_repair",
  "question": "Which SAP Notes directly resolve alert DBSQL_NO_MORE_CONNECTION?",
  "expected_status": "SUCCESS",
  "observed_status": "SUCCESS",
  "reason_code": "NONE",
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
  "plan": {"digest_sha256": "...", "required_variables": ["?note", "?title", "?noteNumber"]},
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
  "bindings": [
    {"noteNumber": "3345100", "title": "...", "alertCode": "DBSQL_NO_MORE_CONNECTION"}
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
    "graph_sha256": "...",
    "citation": "Synthetic fixture cifre-synthetic-support-ppms-v1; not official data."
  }
}
```

The JSON Schema checked in at
`tests/research/result_schema.json` is authoritative and must encode the
following details:

- The required top-level fields are `schema_version`, `query_id`,
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
- Required projected variables are `?note`, `?noteNumber`, and `?title` for
  note answers. Optional variables have an explicit `optional: true` entry in
  the plan and their missing bindings are JSON `null`.
- Binding rows sort by the tuple `(noteNumber, title, note IRI, remaining
  projected variable names)` after conversion to UTF-8 strings. Object keys
  sort lexicographically. This ordering is applied before hashing.
- Metric values are decimal strings with exactly six fractional digits,
  rounded half-even from `Decimal`; binary JSON floats are forbidden. Counts
  are non-negative JSON integers. Boolean fields are JSON booleans.
- Canonical JSON is UTF-8, RFC 8785-style key ordering, no insignificant
  whitespace, `\n` only where a file writer requires a final line ending, and
  no timestamp in the hashed content.

### 17.1 Exact hash manifest and environment

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
tests/research/benchmark_dataset.yaml
tests/research/benchmark_dataset_v2.yaml
tests/research/result_schema.json
constraints/py312.txt
Makefile
pyproject.toml
.github/workflows/ci.yml
src/semantic_layer/kg/*.py
src/semantic_layer/reasoning/*.py
src/semantic_layer/research/*.py
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
  cifmeta: https://example.org/cifre-kg/meta#
synthetic_label_policy:
  official_help_documentation: forbidden
  official_note: forbidden
  official_product: forbidden
```

The RDF graph contains a metadata resource under
`https://example.org/cifre-kg/meta#dataset-cifre-synthetic-support-ppms-v1`
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
| `cifmeta` | `SyntheticDataset`, `SyntheticCrosswalk` | `sourceKind`, `official`, `datasetId`, `generatedBy`, `graphPath`, `mapsToConcept`, `crosswalkVersion` |

Allowed instance bases are exact: support instances use
`https://example.org/cifre-kg/data/support/{note,alert,component,simcat,doc}/`;
PPMS instances use
`https://example.org/cifre-kg/data/ppms/{productline,product,version,component,compversion,sp,patch}/`;
ERP instances use
`https://example.org/cifre-kg/data/erp/{partner,order,doc,product,risk,coverage,status,loss}/`;
and metadata resources use
`https://example.org/cifre-kg/meta/`. The RDF namespace IRIs in Section 5.1
are the only class/property bases. No other HTTP(S) IRI is valid for a
synthetic domain resource except W3C vocabulary IRIs (`rdf`, `rdfs`, `owl`,
`xsd`, `sh`, and `skos`).

The explicit ERP-to-SKOS crosswalk is a separate resource with this schema:

```turtle
cifmeta:crosswalk-v1 a cifmeta:SyntheticCrosswalk ;
    cifmeta:crosswalkVersion "1.0"^^xsd:string ;
    cifmeta:mapsToConcept cifskos:ProductAutomotive .

ciferp:ProductAutomotive cifmeta:mapsToConcept cifskos:ProductAutomotive .
```

`cifmeta:mapsToConcept` has domain `ciferp:Product` and range
`skos:Concept`; it never asserts that the SKOS concept is an OWL class and
never replaces `rdf:type`.

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

## 23. Corpus versions and reflection metadata

The existing 40 questions remain unchanged as the controlled v1 corpus at
`tests/research/benchmark_dataset.yaml`, with header
`version: "1.0.0"`, `corpus_id: "cifre-synthetic-aqr-v1"`, and exactly five
tiers of eight questions. No negative questions are added to v1 and no v1
question is silently deleted. Revised gold expectations remain governed by
the migration fields in Section 8.1; v1 is the positive baseline used for the
headline preliminary metrics.

Create a separate v2 file at
`tests/research/benchmark_dataset_v2.yaml`, with header
`version: "2.0.0"`, `corpus_id: "cifre-synthetic-aqr-v2"`, and all 40 v1
records copied byte-for-byte plus 12 new negative records: two unknown-token,
two unknown-entity, two ambiguous/multiple-entity, two unsupported-intent,
two syntax, and two strict-empty cases. V2 does not alter v1 golds. The
reproducibility target runs both files, writes one `corpus_runs` entry per
version to `results/latest_benchmark.json`, and reports v1 and v2 separately.

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
or F1 scoring. The required `optional_binding_rate` field is a decimal-string
operational metric computed as bound optional cells divided by optional cells
encountered, with `"0.000000"` for a zero-cell plan. This resolves the prior conflict between
an optional pattern and an asserted mandatory answer field.

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
tests/research/benchmark_dataset.yaml
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
