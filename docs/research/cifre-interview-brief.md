# CIFRE research interview brief

## One-minute scope

This is an independent, unaffiliated candidate prototype using synthetic
support and product-lifecycle fixtures. There is no employment, sponsorship,
host, collaboration, or affiliation implied by the repository; there is no
affiliation with any external organization. It is not an
official product, benchmark, or report of proprietary-data access. The current
research instrument is a deterministic RDF/SHACL/SPARQL baseline; learned,
vector, and agentic model conditions are proposed future work.

No affiliation with an external organization is implied.

The primary corpus is `cifre-synthetic-aqr-v1` (40 controlled synthetic
questions). The checked-in v2 corpus adds explicit negative and strict-empty
cases. The final metrics are not printed in this brief: Task 13 must generate
and review `results/latest_benchmark.json` before any exact aggregate value is
reported.

## Current data flow

```text
synthetic fixtures -> namespace/schema checks -> graph parity -> scoped SHACL
  -> finite grounding -> typed logical plan -> deterministic SPARQL
  -> local RDFLib execution -> bounded repair -> typed result/provenance
```

Run the planned reproducibility gate from the repository root:

```bash
make PYTHON=.venv/bin/python research-verify
```

The command and canonical artifact are Task 13 handoff items. Until that task
completes, commit identity, hashes, and final metric values are pending.

## Five source-verifiable implementation statements

1. The [`schema linker`](../../src/semantic_layer/reasoning/schema_linker.py)
   uses a finite grammar and finite entity vocabularies. Unknown tokens,
   unknown entities, and ambiguous input are represented as stable failure
   reasons instead of invented identifiers.
2. The [`query planner`](../../src/semantic_layer/reasoning/query_planner.py)
   emits a typed logical plan, uses a component hierarchy property path, and
   bounds prerequisite traversal to a finite depth with cycle/depth evidence.
3. The [`SPARQL compiler`](../../src/semantic_layer/reasoning/text_to_sparql.py)
   rejects an unbound required projection before emitting deterministic
   `SELECT DISTINCT` text.
4. The [`bounded reasoner`](../../src/semantic_layer/reasoning/reflective_agent.py)
   records each attempt and permits at most three repairs. Support-package
   removal and component widening remain disclosed relaxed candidates rather
   than strict success.
5. The [`knowledge-graph loader`](../../src/semantic_layer/kg/loader.py)
   loads RDF/Turtle into RDFLib and returns a scoped `ValidationReport` for
   SHACL validation; support-only validation is not silently called complete.

## What is implemented, proposed, and absent

| Status | Boundary |
| --- | --- |
| Implemented locally | Synthetic RDF/Turtle fixtures; deterministic grammar, plans, SPARQL, RDFLib execution; typed statuses; bounded repair; binding-derived provenance. |
| Proposed future work | Learned schema/entity grounding, constrained Text-to-SPARQL, real vector retrieval alongside the KG, learned feedback policies, scale, drift, and human evaluation. |
| Not implemented | LLM or embedding calls, vector index, proprietary data, external store, production integration, and a completed final benchmark artifact. |

## Metric handoff

The final artifact is the source for exact baseline fields. Task 13 must fill
and verify, per corpus and condition: syntax-success rate, execution-success
rate, status accuracy, exact note-set accuracy, precision/recall/F1,
relation/path correctness, strict-empty rate, unsupported rejection,
repair/recovery attempts and successes, groundedness/provenance fields,
latency, token/cost fields where applicable, and robustness slices. No old
proposal number is reused; Task 13 must provide the evidence before any
unsupported-answer rate is discussed.

## Limitations to state in an interview

* The graph and questions are synthetic and small; no proprietary or customer
  data is represented.
* The linker covers a finite grammar and fails closed on unsupported phrasing;
  it is not a general language-understanding system.
* The current reasoner is deterministic and hand-written. Its three-attempt
  repair policy is a research baseline, not learned reflection.
* The current path has graph traversal only. A future text/vector comparison
  needs its own corpus, index, model/version, cost protocol, and human review.
* Scale to millions of documents, ontology evolution, model drift, privacy,
  and operational deployment have not been evaluated.
* Task 13 still owns the final artifact, exact commit/hash manifest, complete
  verification command result, and final claim scan.
