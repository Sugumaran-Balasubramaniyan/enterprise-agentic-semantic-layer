# Research interview brief

## One-minute scope

This research prototype investigates knowledge-grounded Agentic AI with RDF,
OWL, SHACL, SPARQL, deterministic query planning and repair, provenance, and
controlled evaluation. The current research instrument is a deterministic symbolic baseline
over synthetic data; proposed future LLM, vector, and
agentic-model conditions are future work. The preliminary controlled benchmark
is small, with no proprietary data and no production-scale validation.

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

Run the reproducibility gate from the repository root:

```bash
make PYTHON=.venv/bin/python research-verify
```

The command validates deterministic content against a fresh temporary run and
reports the recorded and current runtime environments separately; it does not
rewrite the artifact. A reviewed source or documentation change must be
finalized explicitly and then pass the same gate again.

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

This Task 13 finalization run was executed from base source revision
`0744f635f68f12ff71af7618dd0f50f470424975` plus the final hardening changes in
the working tree, on Python `3.12.3`, Linux `aarch64`, with pip `25.2` and lock SHA-256
`a8b8a5054ae3d55cfc51950b0276d9d7d00c725c7676cad1cdc741ef274f1534`.
The pre-documentation temporary run contained 157 manifest entries and had digest
`142db4126ab35bd559c640258f284b64b0c691692a96aedb718793d6469d2fd8`.
That digest is historical evidence for the temporary run, not the canonical
post-documentation digest. Read the current canonical internal digest from
`results/latest_benchmark.json` (`hash_manifest.digest_sha256`) after checkout;
repeating it here would change a manifest-covered document and invalidate the
value. The outer artifact digest is intentionally not embedded in this
document because it is also manifest-covered; compute it with
`sha256sum results/latest_benchmark.json` after checkout.

| Corpus | Dataset SHA-256 | N | Condition | Status accuracy | Exact / P / R / F1 | Syntax | Execution | Strict empty | Unsupported rejection |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| v1 `cifre-synthetic-aqr-v1` | `6fe8532232c66b04c7cbe92f8479e809dd57c38890d59db4672d0c20a9c04f67` | 40 | no-reflection; bounded-repair | `1.000000` | `1.000000 / 1.000000 / 1.000000 / 1.000000` | `1.000000` | `1.000000` | `0.200000` | `null` |
| v2 `cifre-synthetic-aqr-v2` | `40c3cf58b29de5d99a34f5640b982e79c42a217d8e6f73d8b7534a3eddd60168` | 52 | no-reflection; bounded-repair | `1.000000` | `1.000000 / 1.000000 / 1.000000 / 1.000000` | `1.000000` | `0.846154` | `0.230769` | `1.000000` |

The two conditions produce the same aggregate values on these deterministic
fixtures; the artifact retains separate per-query records and condition IDs.
Status counts are v1 `SUCCESS=32, EMPTY_RESULT=8, UNSUPPORTED=0` and v2
`SUCCESS=32, EMPTY_RESULT=12, UNSUPPORTED=8` (all other statuses zero). The
combined graph and shape hashes are
`f419406cdc4367d3b9cfce17bb8aa5a405eb2b4987f37298b7820cb081fae6cb` and
`5568aca9287fbeb9f0731bb25837ed481e2f650d72fda921ebfe3f70e9eb7127`.
The support ontology input hash is
`5d8ee297caf5ee2842fdf76c568428138523a93a9239cef5db82a3a5234164a8`.

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
