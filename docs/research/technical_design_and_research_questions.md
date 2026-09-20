# Technical design and research questions

> This is an independent, unaffiliated candidate prototype using synthetic
> support and product-lifecycle fixtures. It is not an SAP product, SAP
> publication, SAP-endorsed benchmark, or report of access to SAP internal
> data. The repository demonstrates a deterministic symbolic baseline and
> proposes future LLM/retrieval experiments; it does not claim completed PhD
> research or production readiness.

This note is an interview-oriented explanation of the current repository. It
marks implemented behaviour separately from proposed research. The current
system has no LLM call, embedding model, vector index, vector retriever,
external graph store, proprietary data, or production integration.

## Current data flow

```text
synthetic Turtle/YAML fixtures
  -> neutral namespace and schema checks
  -> generated/check-in graph parity
  -> scoped SHACL validation
  -> SchemaLinker finite grammar
  -> GroundedEntities (or explicit abstention)
  -> QueryPlanner LogicalQueryPlan
  -> TextToSPARQLEngine projection-safe SPARQL
  -> SAPKnowledgeGraph RDFLib execution
  -> bounded repair or semantic relaxation
  -> typed status, strict bindings, and provenance
  -> v1/v2 per-query record and deterministic result artifact
```

The path is implemented in the [`schema linker`](../../src/semantic_layer/reasoning/schema_linker.py),
[`query planner`](../../src/semantic_layer/reasoning/query_planner.py),
[`SPARQL compiler`](../../src/semantic_layer/reasoning/text_to_sparql.py),
[`bounded reasoner`](../../src/semantic_layer/reasoning/reflective_agent.py),
and [`KG loader`](../../src/semantic_layer/kg/loader.py). The canonical result
file is a Task 13 output, so this document does not substitute prose for its
future hashes or metrics.

## Implemented and proposed boundaries

| Capability | Implemented locally | Proposed future work |
| --- | --- | --- |
| Data | Synthetic support/PPMS RDF/Turtle and versioned YAML questions | Approved, de-identified or synthetic text collections with data cards |
| Grounding | Fixed vocabulary, template matching, explicit unknown/ambiguous failure | Learned entity linking with confidence, candidate sets, and abstention |
| Planning | Typed `LogicalQueryPlan` with finite predicates and projections | Learned or hybrid plan proposal validated against the same schema |
| Query | Deterministic SPARQL 1.1 text from a plan | Constrained Text-to-SPARQL candidate generation |
| Execution | Local RDFLib graph queries | Controlled comparison of stores and retrieval indexes |
| Repair | At most three logged, allowlisted repairs/relaxations | Learned diagnostic policy with the same finite budget and ledger |
| Retrieval | Graph traversal only | A real vector-retrieval condition alongside graph constraints |
| Answers | Strict binding-derived fields and synthetic provenance | Human-reviewed explanatory text with evidence and provenance |

The `Not implemented` boundary covers LLM or embedding calls, a vector index,
proprietary or external data, an external graph service, production
integration, and human-evaluation results. Those omissions are not hidden
inside the proposed column.

## Typed interfaces

The current pipeline passes typed values between stages rather than passing an
unrestricted prompt or executable string through every stage.

| Interface | Current fields/contract | Boundary |
| --- | --- | --- |
| `GroundedEntities` | Raw and normalized request, finite entity slots, intent, confidence, and `ReasonCode` failure class | Implemented; confidence is currently deterministic rather than learned. |
| `LogicalQueryPlan` | Target variable, intent, selected variables, required/optional variables, triple/path patterns, filters, order, and limit | Implemented; the compiler rejects unbound required projections. |
| `TextToSPARQLEngine` | `validate_projections(plan)` followed by deterministic `compile(plan)` | Implemented; no arbitrary model text is executed. |
| `ReasoningResult` | Status, reason code, attempts, initial/final query, bindings, predicted notes, repair ledger, relaxation disclosure, answer scope, and provenance | Implemented; strict bindings and relaxed candidates are separate. |
| `ValidationReport` | Conformance, report text, shapes path, scope (`support`, `erp`, or `combined`), and inference | Implemented; scope must be reported accurately. |
| Benchmark record/artifact | Expected/observed status, gold/predicted note sets, exact-set and set metrics, hashes, environment, and per-query evidence | Schema and runner are implemented; canonical final artifact is Task 13-owned. |

## RDF vs property graph

### Implemented: RDF

The current graph is RDF: facts are subject-predicate-object triples with URI
terms and typed or language-tagged literals. The checked-in Turtle uses neutral
synthetic namespaces such as `cifsup:` and `cifppms:`. RDF is appropriate here
because the experiment needs explicit ontology terms, RDFLib execution, SPARQL,
OWL vocabulary, and SHACL constraints. `SAPKnowledgeGraph` stores the graph in
an RDFLib `Graph`; no external graph service is required.

### Not implemented: property-graph execution

A property graph would represent vertices and edges with implementation-defined
labels and properties, often queried through a different language. That model
can be useful for operational traversals, but this repository does not run a
property-graph database or claim a property-graph benchmark. A future store
comparison would need an explicit mapping policy, equivalent data, equivalent
path semantics, and separate latency/cost measurements. “Graph” in the current
implementation means an RDF graph unless stated otherwise.

## OWL, SHACL, and their different jobs

### OWL

The synthetic support and PPMS files use OWL classes and properties to describe
the vocabulary: for example, `cifsup:SAPNote`, `cifsup:ApplicationComponent`,
`cifppms:ProductVersion`, domains, ranges, and the
`cifsup:hasPrerequisiteNote` transitive-property declaration. OWL describes
meaning and possible entailments. The query planner does not rely on a hidden
global reasoner to invent answers; prerequisite reachability is bounded and
recorded explicitly.

### SHACL

SHACL supplies validation constraints over a data graph. The checked-in shapes
require fields such as an English label, a single note number, a governed
priority, component links, and product/component-version links. The loader's
`validate_shacl` method returns a `ValidationReport` with `conforms`, report
text, shape path, scope, and inference metadata. Valid fixtures and deliberately
invalid fixtures are separate controls.

### OWL vs SHACL

OWL is the vocabulary/semantic model; SHACL is a validation contract. An OWL
range can describe what an object should be, while a SHACL `minCount`, datatype,
language, or allowed-value constraint can reject a concrete malformed fixture.
Conformance to SHACL does not prove that every possible OWL entailment holds,
and an OWL declaration does not by itself supply the repository's desired
cardinality or human-readable error policy. The verification protocol labels a
support-only run as partial unless each declared graph and shape scope has
been run.

## SPARQL and property paths

### SPARQL

SPARQL is the query language executed over the RDF graph. It is not generated
from arbitrary text in the current system. A `LogicalQueryPlan` carries the
target variable, selected variables, triple/path patterns, filters, ordering,
and limit. `TextToSPARQLEngine.compile` renders deterministic prefixes and a
`SELECT DISTINCT` query after checking that every required projection is bound
by a mandatory pattern. RDFLib executes that text and returns normalized rows.

### Actual multi-hop implementation

There are two implemented forms:

1. **Component hierarchy.** A note-to-component pattern uses
   `cifsup:affectsComponent/cifsup:parentComponent*`, so a requested parent
   code can match a leaf or descendant component through zero or more parent
   edges. The compiler keeps this path in the generated SPARQL.
2. **Prerequisite closure.** The planner uses a deterministic union of paths
   with one through sixteen repeated
   `cifsup:hasPrerequisiteNote` edges. It excludes the target note and selects
   only variables with binding patterns. A separate breadth-first traversal
   reports unique reachable nodes, cycle edges, depth truncation, status, and
   `PREREQUISITE_DEPTH_EXCEEDED`. This is deliberately bounded rather than an
   unbounded transitive query.

The cycle fixture proves that a cycle does not repeat the target, and the
depth-17 fixture proves that the configured depth limit fails closed. These are
algorithm tests, not claims that arbitrary real graphs are complete.

## Bounded query repair

The [`AQRReflectiveAgent`](../../src/semantic_layer/reasoning/reflective_agent.py)
accepts exactly two conditions: `deterministic_no_reflection_ablation` and
`deterministic_bounded_repair`. The no-reflection condition executes once. The
bounded condition caps `max_repairs` at three and appends a `RepairOperation`
for every attempt, including the query and plan hashes, status transition,
reason code, changed constraints, binding count, bounded diagnostic, and
optional SPARQL text.

For a syntax or execution exception, the current allowlist can restore a
missing approved prefix when the diagnostic identifies one. An unknown prefix
or opaque error is not repaired by free-form rewriting. For an empty strict
result, the semantic sequence is:

1. remove the support-package bound;
2. widen a leaf component to its finite parent, if possible; and
3. stop when the budget or operation list is exhausted.

Relaxation is not strict success. The result keeps `EMPTY_RESULT` for the
original constraints, leaves strict `bindings` and predicted note numbers
empty, and places any returned rows in `relaxed_candidates` with
`answer_scope=relaxed_candidates`. This is the implemented contract, not a
learned self-correction result.

## Unknown entities and ambiguous entities

### Unknown entities

The linker checks alert, component, priority, product, software-component, and
support-package cues against finite vocabularies. An unknown alert after an
alert cue, an unknown component after a component cue, an unknown priority, or
a malformed support-package token sets a stable reason such as
`UNKNOWN_ENTITY`. Note identifiers use a seven-digit decimal syntax rule rather
than a finite vocabulary: a syntactically valid but absent note is accepted,
planned, and executed, then returns `EMPTY_RESULT`; a malformed or
non-seven-digit note value is rejected as `UNKNOWN_ENTITY`. Unknown filler or
grammar words can produce `UNKNOWN_TOKEN`. The reasoner returns `UNSUPPORTED`
with no plan, SPARQL, binding, or factual answer for a rejected request; it does
not invent an IRI, parent, note, or product version.

### Ambiguous entities

Multiple distinct recognized values in the same slot produce
`AMBIGUOUS_INPUT`. A conflict between a prerequisite request and other anchors,
or an unsupported order/template, can produce `AMBIGUOUS_INTENT` or
`UNSUPPORTED_INTENT`. These are policy decisions made before execution, not a
silent choice of the first entity. The v2 corpus contains explicit negative
cases so rejection is evaluated rather than hidden inside an empty result.

## Proposed LLM insertion points

No model is called today. A future experiment could insert a model at one
boundary at a time:

1. **Grounding:** propose candidate entity IDs and confidence values for a
   paraphrase; a typed linker decides accept, ask for clarification, or abstain.
2. **Plan proposal:** propose an intent and typed patterns; the planner/schema
   validator rejects unknown predicates, variables, or paths.
3. **Text-to-SPARQL draft:** propose a query only after a plan exists; the
   compiler and parser gate it before execution.
4. **Repair policy:** classify a bounded diagnostic and select one allowlisted
   operation; the ledger and strict status remain deterministic.
5. **Answer wording:** draft an explanation from approved bindings and source
   identifiers; it cannot add unsupported entities or facts.

Each insertion can be ablated independently against the two deterministic
conditions. A model's fluency is not a validity or provenance measure.

## Constraining LLM-generated SPARQL

If a future model emits SPARQL, the raw text must not be sent directly to a
store. The proposed gate is:

1. normalize the request and ground entities against a versioned namespace and
   predicate allowlist;
2. require a typed plan or a schema-valid candidate structure;
3. parse the query with a SPARQL parser and reject unknown prefixes,
   predicates, graph/service clauses, updates, unbound required projections,
   unsafe expressions, and unbounded resource use;
4. compile or canonicalize only approved patterns, filters, ordering, and
   limits;
5. execute read-only with time and row limits, then classify syntax,
   execution, empty, unsupported, and success statuses; and
6. retain the draft, final query, hashes, result bindings, source IDs, and
   repair/relaxation ledger for review.

The current compiler implements the projection-binding part of this gate. The
full model-facing protocol is proposed work.

## Text-to-SPARQL evaluation

### Execution vs exact-match accuracy

**Execution accuracy** asks whether a query parses and executes under the
declared store/runtime. It can be true even when a query returns the wrong
relation or extra notes. **Exact-set accuracy** asks whether the strict
predicted note-number set equals the gold set for the question and expected
status. The current artifact records syntax validity, execution success, status
accuracy, status counts, exact-set precision/recall/F1, recovery attempts and
successes, strict-empty rate, unsupported rejection, and optional-binding
rate. A relaxed candidate set never replaces the strict set for scoring.

String-level exact match of a SPARQL serialization is useful for deterministic
regression, but it is not a sufficient semantic measure: equivalent queries
can serialize differently, and an executable query can still be wrong.

### Current artifact metric fields

The current runner and JSON Schema expose exactly these metric fields: status
counts (`status_counts`), status correctness (`status_accuracy`), strict
answer-set fields (`exact_set`, `precision`, `recall`, `f1`), and operational
fields (`syntax_success_rate`, `execution_success_rate`,
`recovery_attempt_rate`, `recovery_success_rate`, `strict_empty_rate`,
`unsupported_rejection_rate`, and `optional_binding_rate`). This is the
complete current metric surface; the final values remain Task 13 evidence.

Future-only metric fields, not emitted by the current artifact, are
`relation_path_correctness`, `groundedness`, `provenance_completeness`,
`latency`, `token_count`, `cost`, `robustness`, and
`human_unsupported_answer_rate`. Relation/path, groundedness, provenance,
latency, token/cost, robustness, and human unsupported-answer measurements
require a separately implemented future experiment.

### Corpus and artifact

`cifre-synthetic-aqr-v1` contains 40 controlled synthetic records. The v2
fixture contains 52 records including negative unknown, ambiguous, and strict
empty cases. Each record has a stable ID, question, category, expected status,
gold note set, strict flag, and exact-set policy. The future artifact records
per-query grounding, plan, query, status, reason, attempts, bindings,
relaxations, provenance, input hashes, environment, and separate aggregate
metrics for each corpus and condition. Task 13 owns creation and final
verification of `results/latest_benchmark.json`.

## Retrieval alongside the KG

The repository currently has graph traversal only. A future Vector RAG
baseline is proposed for comparison: it can retrieve explanatory passages from
an independently versioned
text corpus, while the KG supplies typed entities, relations, version bounds,
and prerequisite paths. A hybrid system should join the two through stable
provenance IDs, not let a similar passage override a graph constraint. The
comparison must include graph-only, text-only, and hybrid conditions with the
same question splits, retrieval depth, indexing policy, latency budget, token
budget, and human evidence rubric. No vector-RAG score is reported here.

## Scale to millions of documents

The current graph and 40/52-record corpora are small controlled fixtures. They
do not support a claim about millions of documents. A scale study would define
synthetic or approved document-generation rules, graph density, update rate,
entity cardinality, index build time, memory, and query mix. It would measure
p50/p95 latency, throughput, timeout/error rate, memory, cost, and exact-set or
status degradation at pre-registered scale points. Partitioning, caching,
full-text indexes, vector indexes, and alternative RDF stores would be
experimental factors, not assumed improvements.

## Ontology evolution

Ontology evolution is a versioned-contract problem. A future change may add or
rename a class/predicate, alter a range or shape, deprecate a path, or change a
namespace mapping. The safe protocol is to version the ontology, shapes,
grammar, planner/compiler, corpus, and result schema together; run migration
and graph-parity checks; preserve old artifacts; and record whether a query was
migrated, rejected, or abstained. Drift detection should compare schema and
shape signatures and exercise representative queries. The current repository
has version markers and migration manifests, but no learned drift detector.

## Research contribution vs software engineering

The software-engineering contribution is a typed, reproducible baseline with
closed failure states, deterministic query construction, bounded repair, source
links, tests, and an artifact contract. It makes later comparison possible and
prevents unsupported claims from being presented as results.

The research contribution would be an experimentally supported answer to the
questions above: which learned or hybrid additions improve coverage or human
evidence quality at a fixed semantic-risk, latency, token, and privacy budget;
which fail; and how ontology and model drift change that conclusion. A feature
being implemented, a passing unit test, or a well-formed SPARQL query is not by
itself a research result.

## Research questions, hypotheses, and falsifiable measures

These questions are proposals, not findings:

| Question / hypothesis | Falsifiable measure |
| --- | --- |
| **RQ1 / H1:** learned grounding improves held-out coverage without increasing wrong-entity acceptance at a fixed validity budget | Entity precision/recall, calibration, unknown/ambiguous rejection, false acceptance |
| **RQ2 / H2:** constrained plan-first generation improves semantic and path validity over an unconstrained generator | Syntax/execution rate, predicate/schema validity, projection validity, relation/path exactness |
| **RQ3 / H3:** bounded execution feedback recovers failures without hidden semantic relaxation | Strict exact-set accuracy, recovery success, ledger completeness, budget use, strict/relaxed separation |
| **RQ4 / H4:** hybrid retrieval improves evidence-supported answer correctness under a fixed cost budget | Blinded human correctness, provenance completeness, unsupported-claim annotations, latency/tokens/cost |
| **RQ5:** versioned ontology and index policies preserve reliability at scale and under drift | p95 latency, memory, migration/drift detection, broken-plan rate, status and exact-set degradation |

## Source map

The following implementation files are the source of truth for current claims;
the links are repository-relative and do not imply any external affiliation.

| Claim | Source |
| --- | --- |
| finite grounding and explicit failure classes | [`schema_linker.py`](../../src/semantic_layer/reasoning/schema_linker.py) |
| typed plans, hierarchy paths, and bounded prerequisite evidence | [`query_planner.py`](../../src/semantic_layer/reasoning/query_planner.py) |
| projection-safe deterministic SPARQL | [`text_to_sparql.py`](../../src/semantic_layer/reasoning/text_to_sparql.py) |
| status lifecycle, repair ledger, and strict/relaxed separation | [`reflective_agent.py`](../../src/semantic_layer/reasoning/reflective_agent.py) |
| RDFLib loading and scoped SHACL report | [`loader.py`](../../src/semantic_layer/kg/loader.py) |
