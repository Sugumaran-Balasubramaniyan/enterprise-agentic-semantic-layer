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
   and its [grounding contract tests](../../tests/research/test_grounding_contract.py) use a
   finite grammar and finite vocabularies for alerts, components, and
   priorities. Declared note fixtures preserve canonical seven-digit
   identifiers, while unknown and ambiguous inputs return stable failure
   reasons instead of invented identifiers.
2. The [`query planner`](../../src/semantic_layer/reasoning/query_planner.py)
   and its [planner tests](../../tests/unit/test_aqr_query_planner.py) emit a
   typed logical plan, use a component hierarchy property path, and bound
   prerequisite traversal to a finite depth with cycle/depth evidence.
3. The [`SPARQL compiler`](../../src/semantic_layer/reasoning/text_to_sparql.py)
   and its [projection tests](../../tests/unit/test_aqr_query_planner.py)
   reject an unbound required projection before emitting deterministic
   `SELECT DISTINCT` text.
4. The [`bounded reasoner`](../../src/semantic_layer/reasoning/reflective_agent.py)
   and its [failure-state-machine tests](../../tests/research/test_failure_state_machine.py)
   record each attempt and permit at most three repairs. Support-package
   removal and component widening remain disclosed relaxed candidates rather
   than strict success.
5. The [`knowledge-graph loader`](../../src/semantic_layer/kg/loader.py)
   and its [loader and graph tests](../../tests/semantic/test_sap_kg.py) load RDF/Turtle
   into RDFLib and return a scoped `ValidationReport`; support-only validation
   is not silently called complete.

## What is implemented, proposed, and absent

| Status | Boundary |
| --- | --- |
| Implemented locally | Synthetic RDF/Turtle fixtures; deterministic grammar, plans, SPARQL, RDFLib execution; typed statuses; bounded repair; binding-derived provenance. |
| Proposed future work | Learned schema/entity grounding, constrained Text-to-SPARQL, real vector retrieval alongside the KG, learned feedback policies, scale, drift, and human evaluation. |
| Not implemented | LLM or embedding calls, vector index, proprietary data, external store, production integration, and a completed final benchmark artifact. |

## Metric handoff

### Current artifact metric fields

The current runner and JSON Schema expose exactly these metric fields: status
counts (`status_counts`), status correctness (`status_accuracy`), strict
answer-set fields (`exact_set`, `precision`, `recall`, `f1`), and operational
fields (`syntax_success_rate`, `execution_success_rate`,
`recovery_attempt_rate`, `recovery_success_rate`, `strict_empty_rate`,
`unsupported_rejection_rate`, and `optional_binding_rate`). The final values
must come from the schema-valid Task 13 artifact.

### Future-only metric fields

The following fields are not emitted by the current artifact and remain
proposed future work: `relation_path_correctness`, `groundedness`,
`provenance_completeness`, `latency`, `token_count`, `cost`, `robustness`, and
`human_unsupported_answer_rate`. No old proposal number is reused; each future
measurement needs its own implementation and evidence protocol.

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
