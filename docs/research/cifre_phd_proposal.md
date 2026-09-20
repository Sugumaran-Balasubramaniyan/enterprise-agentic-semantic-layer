# Knowledge-Grounded Autonomous Query Reasoning for Enterprise Agentic AI

**Working title:** proposed and not approved.
**Document status:** independent research-proposal outline; this is not an
approved doctoral project, employment application, sponsorship statement, or
report of completed research.

> This is an independent, unaffiliated candidate prototype using synthetic
> support and product-lifecycle fixtures. It is not an SAP product, SAP
> publication, SAP-endorsed benchmark, or report of access to SAP internal
> data. The repository demonstrates a deterministic symbolic baseline and
> proposes future LLM/retrieval experiments; it does not claim completed PhD
> research or production readiness.

## Scope and status boundary

This proposal uses enterprise support and product-lifecycle terminology because
those terms make the research problem concrete. The checked-in graph, questions,
and labels are repository-authored synthetic fixtures. No proprietary data,
outside service, or private knowledge source is used for the current path. The
proposal is intentionally written so that a reviewer can
separate what is implemented locally from what would be evaluated later.

| Boundary | Current statement |
| --- | --- |
| Implemented locally | Synthetic RDF/Turtle support and PPMS fixtures; scoped SHACL validation; fixed-vocabulary grounding; typed logical plans; deterministic SPARQL compilation; local RDFLib execution; bounded, logged repair; binding-derived answers and provenance fields. |
| Synthetic/simulated | `cifre-synthetic-aqr-v1` and its v2 extension; SAP-shaped names used as fictional identifiers; future retrieval and model comparisons described in this proposal. |
| Proposed future work | Learned schema/entity grounding, constrained Text-to-SPARQL, execution-guided policies, hybrid text retrieval plus graph traversal, scale experiments, drift studies, and human evaluation. |
| Not implemented | LLM calls, embeddings, vector indexes/retrievers, external stores, production deployments, access to proprietary support data, or a neural benchmark result. |

## Context and motivation

Enterprise support questions often combine several kinds of constraint: an
alert code, a component hierarchy, a product version, a support-package
bound, and a chain of prerequisite notes. A useful answer must preserve those
constraints and identify the source rows from which it was derived. A text
retriever can be helpful for explanatory prose, but a retrieval result alone
does not define a typed relation, a transitive path, or the policy for an empty
strict query.

The local prototype makes this problem inspectable with a small semantic graph.
Its support and product-lifecycle ontologies use neutral `cifsup`, `cifppms`,
and related `cif*` namespaces. It is a research instrument rather than a claim
about any external organization or dataset. The motivation for a future
agentic system is therefore methodological: study how language understanding,
retrieval, and feedback can be added without losing semantic validity,
abstention, reproducibility, or provenance.

## Research gap

The current baseline answers only a controlled grammar. That limitation is
useful: it provides a deterministic reference against which learned components
can be measured. The open research gap is a controlled comparison of:

1. learned grounding and entity linking that can abstain on unknown or
   ambiguous mentions;
2. Text-to-SPARQL generation constrained by an ontology, a typed plan, and a
   safe execution policy;
3. execution-guided repair that records semantic changes instead of silently
   changing the question; and
4. hybrid retrieval in which unstructured evidence complements, rather than
   replaces, graph constraints.

The gap is not filled by calling a model or adding a vector index without a
held-out protocol. Each future condition must have a versioned dataset,
configuration, model/dependency identifiers, random seeds where applicable,
cost accounting, and per-query failure evidence.

## Central research question

**How can an autonomous query reasoner combine learned language grounding,
constrained formal query synthesis, and execution feedback with a knowledge
graph so that broader enterprise questions are answered with measurable
semantic validity, exact relation/path behaviour, calibrated abstention, and
auditable provenance?**

The question is deliberately narrower than “build an autonomous support
assistant.” It asks which additions improve a controlled measure, under which
constraints, and at what latency and cost.

## Research questions and hypotheses

The following are hypotheses, not results. No hypothesis has been accepted or
confirmed by the current repository.

### RQ1 / H1 — learned grounding and abstention

**RQ1.** Can learned schema/entity grounding expand coverage over paraphrased
questions while preserving the baseline's fail-closed handling of unknown and
ambiguous entities?

**H1.** A learned linker with an explicit confidence threshold and abstention
policy will improve held-out entity recall at a fixed semantic-validity and
false-acceptance budget relative to the finite grammar.

Falsifiable measures are entity precision/recall, unknown-entity rejection,
ambiguous-entity rejection, calibration error, and the rate at which an
accepted entity maps to the wrong class or identifier.

### RQ2 / H2 — constrained Text-to-SPARQL

**RQ2.** Does generating a typed logical plan first, then constraining query
construction to an allowlisted schema, improve Text-to-SPARQL validity over an
unconstrained generator?

**H2.** Constrained generation will increase executable and semantically valid
queries, especially for relation and path constraints, at the same question
set and model budget as an unconstrained future baseline.

Falsifiable measures are syntax-success rate, execution-success rate,
ontology/predicate validity, projection-binding validity, relation/path exact
match, exact note-set accuracy, and abstention precision. A syntactically valid
query with the wrong relation is not a success.

### RQ3 / H3 — execution-guided repair

**RQ3.** When a valid request is empty or a draft query fails, which bounded
execution feedback policies recover useful answers without disguising a
relaxed answer as a strict answer?

**H3.** An execution-guided policy with a finite budget and an operation ledger
will improve recovery on pre-registered repair cases while preserving strict
status and reducing unrecorded semantic drift relative to one-shot execution.

Falsifiable measures are strict exact-set accuracy, recovery-attempt and
recovery-success rates, repair-budget use, changed-constraint correctness,
strict-versus-relaxed answer separation, diagnostic leakage, and the fraction
of repairs that introduce a relation/path error.

### RQ4 / H4 — hybrid retrieval and grounded answers

**RQ4.** Can graph constraints and provenance-preserving text retrieval work
together for questions whose answer needs explanatory passages as well as
entity and relation constraints?

**H4.** A hybrid graph-plus-text condition will improve human-rated answer
correctness and evidence completeness over graph-only or text-only conditions
on text-rich questions, subject to a pre-registered latency and token budget.

The falsifiable measures are answer correctness, groundedness and provenance
completeness, relation/path correctness, unsupported-claim annotations from a
human protocol, latency, token count, and cost. This hypothesis cannot be
tested by the current repository because no text retriever or model is
implemented.

### RQ5 — scale and robustness

How do grounding, planning, graph execution, and retrieval behave as document
and entity counts grow toward millions of documents, and which index or
partition choices preserve the same result contract? Measures include p50/p95
latency, memory, throughput, query timeout rate, exact-set degradation, and
cost per question across controlled scale points. The current fixture is not a
million-document evaluation.

### RQ6 — ontology evolution and human trust

How should an agent detect ontology evolution, map versioned schemas, and
explain changes to a reviewer without silently changing query meaning? Measures
include migration success, drift-detection precision/recall, broken-plan rate,
provenance continuity, reviewer agreement, abstention quality, and time to
repair a changed contract.

## Current deterministic baseline

The implemented pipeline is intentionally deterministic:

```text
synthetic ontology/data fixtures
  -> namespace and schema checks
  -> graph generation and checked-in graph parity
  -> scoped SHACL validation
  -> finite vocabulary grounding (abstain on unsupported input)
  -> typed LogicalQueryPlan
  -> projection-safe deterministic SPARQL
  -> RDFLib graph execution
  -> bounded repair/relaxation with an operation ledger
  -> strict status and binding-derived answer
  -> per-query metrics and hashed artifact
```

`SchemaLinker` recognizes finite lists of component codes, alert codes,
product versions, software components, support packages, note numbers, and
priorities. It emits a `GroundedEntities` value or a failure reason; it does
not call an LLM or invent an IRI. `QueryPlanner` maps accepted slots to typed
triple patterns. Component hierarchy uses the path
`cifsup:affectsComponent/cifsup:parentComponent*`. Prerequisite planning uses
a finite union of one through sixteen repeated
`cifsup:hasPrerequisiteNote` edges, while a separate traversal routine records
cycle and depth evidence. This bounded form is the actual implementation and
is not a claim of unrestricted graph closure.

`TextToSPARQLEngine` validates that every required projection is bound by a
mandatory pattern before rendering prefixes, `SELECT DISTINCT`, patterns,
filters, ordering, and a limit. `SAPKnowledgeGraph` executes the resulting
SPARQL locally with RDFLib. The loader's validation result includes a declared
scope, such as support or ERP; a support-only run is partial validation, not a
claim of whole-repository conformance.

The typed lifecycle has five closed statuses: `SUCCESS`, `UNSUPPORTED`,
`SYNTAX_ERROR`, `EXECUTION_ERROR`, and `EMPTY_RESULT`. Unknown entities,
unknown tokens, ambiguous input, and unsupported intent abstain before query
execution. Answers are synthesized from returned bindings and provenance
fields; an error or abstention has no factual answer.

The bounded condition permits at most three repair transitions. An allowlisted
missing-prefix repair is available for syntax or execution diagnostics. For an
empty strict query, the semantic relaxation order is removal of the
support-package bound and then widening a component to its parent. If a
relaxed query finds candidates, the original status remains `EMPTY_RESULT`,
the original constraints remain in the result, and the candidates are labelled
outside the requested constraints. This makes repair observable rather than a
hidden success claim.

## Controlled v1/v2 protocol

The corpus is named `cifre-synthetic-aqr-v1`, with stable query IDs and 40
synthetic records retained as the first controlled version. The separate
`cifre-synthetic-aqr-v2` corpus contains the v1 records plus explicit negative
cases for unknown tokens, unknown entities, ambiguous input/intent, and strict
empty results (52 records in the checked-in fixture). The records carry an
expected status, exact gold note set, category, strict-constraint flag, and
gold policy. The migration manifest records derivation evidence for changed
gold sets; a legacy expectation is not silently treated as a new result.

The two measured conditions are:

* `deterministic_no_reflection_ablation`: one deterministic grounding,
  planning, compilation, and execution pass;
* `deterministic_bounded_repair`: the same path with the bounded repair and
  relaxation ledger enabled.

Each condition is scored separately for each corpus. A result record includes
the question, grounding, plan, initial/final SPARQL, status, reason code,
attempts, repair operations, strict bindings, separately labelled relaxed
candidates, provenance, and hashes. Strict predictions are never replaced by
relaxed candidates. Both-empty exact-set precision/recall/F1 is defined by the
metric contract; one-empty/one-nonempty is not a success.

The final canonical JSON at `results/latest_benchmark.json` is owned by Task
13. Until that task runs the final verification command, this proposal does not
report aggregate metric values, final input hashes, or a completed benchmark
result.

## Methodology

The future programme is staged so that each learned capability can be compared
with the deterministic baseline.

### Phase 1 — formal KG and baseline

Freeze the synthetic graph and ontology versions, run graph-isomorphism parity,
run each declared SHACL scope with valid and invalid controls, and reproduce
the v1/v2 deterministic conditions. Publish the schema, exact-set policy,
status policy, hashes, environment, and per-query evidence together. This
phase is the baseline, not a completed learned evaluation.

### Phase 2 — learned schema/entity grounding and constrained Text-to-SPARQL

Introduce a versioned linker interface with confidence, candidate sets, and an
abstention decision. Evaluate lexical, learned, and hybrid grounding on
paraphrases and deliberately unknown/ambiguous inputs. A model may propose a
typed plan or query draft, but an allowlisted parser, ontology/schema check,
projection check, and read-only execution gate must approve it before use.

### Phase 3 — execution-guided repair

Compare no repair, the current deterministic bounded policy, and learned
diagnostic policies under the same maximum-attempt budget. Pre-register which
constraints may be relaxed, preserve an append-only operation ledger, and score
the strict request separately from any relaxed candidates. Include syntax,
execution, empty-result, cycle, depth, and unsupported cases.

### Phase 4 — hybrid RAG+KG retrieval

Add a reproducible text collection and a real vector-retrieval baseline only
after its corpus, embedding/index versions, retrieval depth, and cost are
defined. Compare graph-only, text-only, and hybrid retrieval. Graph edges and
typed constraints remain authoritative for entity/relation/path answers;
retrieved text can supply explanations only when its provenance is retained.

### Phase 5 — scale, robustness, and ontology drift

Vary document/entity volume, graph topology, query paraphrase, missing data,
and store/index implementations. Then introduce versioned ontology changes,
deprecations, renamed predicates, and changed shapes. Measure whether the
system detects drift and abstains or migrates explicitly rather than silently
changing the answer space.

## Baselines and metrics

The comparison table describes planned conditions. Only the first two are
implemented locally; the remaining rows are future baselines with no current
scores.

| Condition | Status | Controlled question |
| --- | --- | --- |
| Deterministic no-reflection | Implemented locally | What does finite grounding and one-pass typed SPARQL do? |
| Deterministic bounded repair | Implemented locally | What does the logged three-attempt repair policy do? |
| Vector retrieval alongside the KG | Proposed future baseline | Does text retrieval add useful passages without weakening graph constraints? |
| Unconstrained LLM Text-to-SPARQL | Proposed future baseline | What fails when a model drafts queries without the typed/schema gate? |
| Ontology-grounded LLM | Proposed future baseline | Does schema-aware prompting or constrained decoding improve semantic validity? |
| Agentic execution feedback | Proposed future baseline | Does a learned feedback policy recover more valid strict cases under the same budget? |

Every future run must report, at minimum:

* **Execution accuracy and syntax:** executable-query rate, syntax validity,
  execution success, and final status accuracy;
* **Semantic and answer correctness:** ontology validity, exact-set answer
  correctness, precision/recall/F1, relation/path correctness, and strict
  empty-result handling;
* **Repair:** attempted, recovered, budget used, operation validity, and
  strict-versus-relaxed separation;
* **Groundedness and provenance:** evidence coverage, provenance completeness,
  human-reviewed unsupported-answer rate, and citation agreement;
* **Efficiency:** p50/p95 latency, token count, model calls, memory, and cost;
* **Robustness:** unknown/ambiguous rejection, paraphrase performance,
  missing-data behaviour, graph noise, ontology drift, and scale curves.

String equality of SPARQL is not the sole evaluation. Equivalent query forms
should be judged by parsed structure, execution, projected bindings, and the
declared relation/path policy. The eventual artifact is the source for exact
baseline metric values; no values are copied from the historical proposal.

## Data, privacy, provenance, and human evaluation

The current data boundary is synthetic and repository-authored. It contains no
proprietary documents, credentials, customer records, or external retrieval
service. A future study would require documented data access approval, a
privacy review, minimisation and retention rules, access controls, redaction,
dataset and model cards, and a clear distinction between public, licensed,
and confidential material. If proprietary constraints prevent release, the
experiment must publish a reproducible synthetic or de-identified protocol
without implying access that was not granted.

Every future example must carry source identifiers and versioned graph/text
provenance. Train/validation/test splits must be separated before indexing to
prevent graph, question, template, or note leakage. Human evaluation should
use blinded, pre-registered rubrics for answer correctness, evidence support,
relation/path correctness, abstention appropriateness, and explanation
usefulness, with inter-rater agreement and adjudication recorded.

## Expected contributions

If the programme is supported by the experiments, its contributions would be:

1. a reproducible typed baseline and corpus protocol for constrained enterprise
   query reasoning over synthetic RDF;
2. an evaluation framework that separates syntax, execution, semantic
   validity, exact answer sets, repair, provenance, and efficiency;
3. controlled methods for inserting learned grounding, constrained query
   synthesis, and execution feedback without hiding semantic relaxation; and
4. evidence about when hybrid retrieval, scale techniques, or ontology-drift
   handling help or hurt under explicit budgets.

These are proposed contributions, not claims that the current repository has
already made a scientific discovery.

## Risks

* **Data access and privacy:** real support data may be unavailable or too
  sensitive; the study must stay synthetic or use approved de-identification.
* **Leakage:** duplicated templates, graph facts, or retrieval indexes can
  inflate scores; splits and provenance must be audited before each run.
* **Nondeterminism:** model, retrieval, and store versions can change output;
  record seeds, configurations, prompts, and per-query traces.
* **Ontology maintenance:** evolving classes, predicates, shapes, and mappings
  can invalidate old plans; version and migrate them explicitly.
* **Proprietary constraints:** a method may be technically promising but not
  publishable; publication boundaries must be set before collecting data.
* **Scale:** millions of documents may expose latency, memory, indexing, and
  cost limits that are absent from the small fixture.
* **Model drift:** a model or embedding update can alter grounding, repair, or
  answer style; drift detection and regression gates are required.

## Falsifiable outcomes

The project should report negative results as first-class outcomes. Examples:

* Reject H1 if learned grounding does not improve held-out coverage at the
  fixed validity and false-acceptance budget, or if abstention calibration is
  worse than the finite grammar.
* Reject H2 if constrained generation does not improve semantic or path
  validity after accounting for syntax and execution failures.
* Reject H3 if recovery gains disappear when strict exact-set scoring and
  repair costs are included, or if the policy changes constraints without a
  complete ledger.
* Reject H4 if hybrid retrieval does not improve blinded evidence-supported
  answers at the pre-registered latency/token/cost budget.

No threshold is selected after seeing the results. A result that fails to meet
the criterion is useful evidence about the boundary of the method.

## Three-year roadmap

### Year 1 — formal baseline and grounded language interface

Freeze ontology, graph, corpus versions, provenance, and the v1/v2 protocol.
Reproduce deterministic conditions, then evaluate learned schema/entity
grounding with abstention and a constrained plan interface on held-out
synthetic paraphrases. Deliverables are a reviewed protocol, data cards,
reproducibility artifacts, and an initial error taxonomy.

### Year 2 — constrained synthesis, repair, and hybrid retrieval

Evaluate ontology-grounded and unconstrained future generators, execute only
typed/allowlisted queries, and compare deterministic versus learned feedback
under a fixed repair budget. Add a versioned text collection and graph-plus-
text retrieval experiment with human evidence review. Deliverables are
ablation reports, cost/latency accounting, and a falsifiable assessment of
H1-H4.

### Year 3 — scale, drift, robustness, and consolidation

Run scale curves toward millions of documents where permitted, test alternative
stores and index policies, and evaluate ontology evolution and model drift.
Complete human evaluation, privacy/provenance audit, replication package, and
thesis-quality negative-result analysis. Any deployment or external study would
require separate authorization and is outside this repository's current scope.

## Non-goals

This document does not claim an external affiliation, host, sponsor,
collaboration, official dataset, access to private systems, or an operational
service. It does not claim doctoral completion, universal reasoning
capability, or a measured model/retrieval result. It does not turn synthetic note numbers or SAP-shaped labels into
official knowledge. It does not treat a relaxed candidate as an answer to the
original strict request, and it does not replace a final artifact, hash
manifest, or verification command with prose.

## Repository evidence

The implementation boundary can be inspected in the
[`schema linker`](../../src/semantic_layer/reasoning/schema_linker.py),
[`query planner`](../../src/semantic_layer/reasoning/query_planner.py),
[`SPARQL compiler`](../../src/semantic_layer/reasoning/text_to_sparql.py),
[`bounded reasoner`](../../src/semantic_layer/reasoning/reflective_agent.py),
and [`knowledge-graph loader`](../../src/semantic_layer/kg/loader.py). The
technical interview note and the short interview brief provide a more compact
map of those contracts. Task 13 owns the final canonical benchmark artifact
and the final claim/format/reproducibility gate.
