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
cases. The preliminary measured result is the committed
[`results/latest_benchmark.json`](../../results/latest_benchmark.json); exact
environment, input hashes, and values are summarized below.

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

The command validates the committed artifact against a fresh temporary run; it
does not rewrite the artifact. A reviewed source or documentation change must
be finalized explicitly and then pass the same gate again.

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
| Not implemented | LLM or embedding calls, vector index, proprietary data, external store, production integration, and any claim beyond this preliminary synthetic artifact. |

## Metric handoff

### Measured preliminary run

This Task 13 finalization run was executed from source revision
`9b3da7c836be605d084138cb5ba99fdf438c918e` on Python `3.12.3`, Linux
`aarch64`, with pip `25.2` and lock SHA-256
`a8b8a5054ae3d55cfc51950b0276d9d7d00c725c7676cad1cdc741ef274f1534`.
The temporary run's artifact manifest contained 156 entries and had digest
`33fe84eac0ddccd67b85c44358b70bb4a3fbfaa373fac5b06d4c113c5a31ffaa`.
The outer artifact digest is intentionally not embedded in this document
because this document is one of the manifest-covered inputs; compute it with
`sha256sum results/latest_benchmark.json` after checkout.

| Corpus | Dataset SHA-256 | N | Condition | Status accuracy | Exact / P / R / F1 | Syntax | Execution | Strict empty | Unsupported rejection |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| v1 `cifre-synthetic-aqr-v1` | `6fe8532232c66b04c7cbe92f8479e809dd57c38890d59db4672d0c20a9c04f67` | 40 | no-reflection; bounded-repair | `0.200000` | `1.000000 / 1.000000 / 1.000000 / 1.000000` | `1.000000` | `0.200000` | `0.025000` | `null` |
| v2 `cifre-synthetic-aqr-v2` | `40c3cf58b29de5d99a34f5640b982e79c42a217d8e6f73d8b7534a3eddd60168` | 52 | no-reflection; bounded-repair | `0.384615` | `1.000000 / 1.000000 / 1.000000 / 1.000000` | `1.000000` | `0.230769` | `0.096154` | `1.000000` |

The two conditions produce the same aggregate values on these deterministic
fixtures; the artifact retains separate per-query records and condition IDs.
Status counts are v1 `SUCCESS=7, EMPTY_RESULT=1, UNSUPPORTED=32` and v2
`SUCCESS=7, EMPTY_RESULT=5, UNSUPPORTED=40` (all other statuses zero). The
combined graph and shape hashes are
`95db160d7c1efc576cdd4c76c488f0f8869929ab6f7b554b37be9e3baf445fa7` and
`5568aca9287fbeb9f0731bb25837ed481e2f650d72fda921ebfe3f70e9eb7127`.

### Current artifact metric fields

The current runner and JSON Schema expose exactly these metric fields: status
counts (`status_counts`), status correctness (`status_accuracy`), strict
answer-set fields (`exact_set`, `precision`, `recall`, `f1`), and operational
fields (`syntax_success_rate`, `execution_success_rate`,
`recovery_attempt_rate`, `recovery_success_rate`, `strict_empty_rate`,
`unsupported_rejection_rate`, and `optional_binding_rate`). The values above
come from the schema-valid artifact and remain preliminary synthetic evidence,
not a generalization or external comparison.

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
* The artifact is a repository-authored preliminary result; no external or
  production evaluation has been performed. Re-run the locked command after
  any manifest-covered byte changes.
