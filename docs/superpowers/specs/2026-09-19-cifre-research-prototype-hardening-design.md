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
  with overlapping local names and IRIs (for example `ProductAutomotive`).
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

The wording may be shortened for metadata, but it must preserve the same
meaning. “SAP” may describe the domain inspiration or names in synthetic
question text; it must not be used as an owner, publisher, certification
authority, or result sponsor.

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
| `cifdata` | `https://example.org/cifre-kg/data/` | Synthetic support/PPMS instance resources; append `support/`, `ppms/`, or another explicit dataset segment |
| `ciferp` | `https://example.org/cifre-kg/erp#` | Synthetic ERP OWL classes/properties currently represented by the `sap:` ERP namespace |
| `cifskos` | `https://example.org/cifre-kg/vocabulary#` | Synthetic SKOS concept schemes and concepts |

`example.org` is used as a reserved documentation namespace. These IRIs are
not SAP IRIs and must be labelled as synthetic in ontology metadata. The
instance pattern should be, for example,
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
labels match. Use explicit reviewed mappings (for example a documented
`ciferp:canonicalConcept` property or a mapping table) when a class is linked
to a taxonomy concept. The mapping is not an implicit `rdf:type` assertion.

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
- each relaxation operation and order (for example remove support-package
  bound, then widen a component);
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
  queries in a subsequent corpus version, or add them to v1 only with new IDs
  and an explicit version change.

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
- run environment versions sufficient to reproduce the result;
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
5. Run the deterministic no-reflection and bounded-repair benchmark, writing
   `results/latest_benchmark.json`.
6. Run claim-contract, research, semantic, and complete pytest checks.
7. Run Ruff and report a concise verification summary.

The command must use temporary generated files and must not silently replace
source fixtures. It should fail non-zero on namespace drift, graph parity
failure, unexpected SHACL outcome, stale result hash, benchmark schema error,
claim-contract violation, test failure, or lint failure.

CI should run this target in a dedicated research-verification job if its
measured runtime is reasonable for the existing suite; otherwise split the
same steps into cached semantic and benchmark jobs without removing any
acceptance check. No cloud account, external endpoint, API key, model
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
- update `pyproject.toml` description and project URLs/metadata, if present,
  to describe an independent local semantic-layer and KG research prototype;
- make `docs/verification-report.md` a fresh post-change report rather than a
  historical assertion, including exact commands, commit, hashes, and known
  limitations.

The repository must not mutate GitHub metadata, releases, topics, remote
descriptions, or other external state as part of this work.

## 11. Architecture, data flow, and likely file impact

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

Likely implementation impact is intentionally explicit:

| Area | Likely files | Required boundary |
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

Validate and version the retained 40-query corpus, add migration metadata and
negative cases, remove the fake Vector RAG path, rename the one-shot ablation,
implement exact-set/set metrics, and write the hashed per-query JSON artifact.

**Acceptance:** A fresh run produces schema-valid `results/latest_benchmark.json`
with no Vector RAG/hallucination fields, deterministic input hashes, per-query
records, and hand-checked metric edge cases. Changed golds have explicit
evidence and migration reasons.

### Task 6: Add the single verification target

Implement `research-verify`, connect it to proportionate CI, and make it
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
