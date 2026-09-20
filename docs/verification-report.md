# Research handoff verification report

**Evidence date:** 2026-09-20 UTC
**Scope:** Task 12 documentation handoff
**Status:** evidence-shaped handoff; final Task 13 verification is pending

> This is an independent, unaffiliated candidate prototype using synthetic
> support and product-lifecycle fixtures. It is not an SAP product, SAP
> publication, SAP-endorsed benchmark, or report of access to SAP internal
> data. The repository demonstrates a deterministic symbolic baseline and
> proposes future LLM/retrieval experiments; it does not claim completed PhD
> research or production readiness.

This report replaces the previous broad verification narrative with fields
that can be filled from a fresh checkout. Historical commands and old
comparative numbers remain historical evidence in
[`cifre-hardening-baseline.md`](research/cifre-hardening-baseline.md); they are
not reused as current results.

## Implemented/proposed/not-implemented boundary

| Status | Boundary |
| --- | --- |
| Implemented locally | Synthetic RDF/Turtle fixtures; deterministic grounding, typed plans, SPARQL compilation, RDFLib execution, scoped SHACL reports, bounded repair, and binding-derived provenance. |
| Proposed future work | Learned grounding, constrained Text-to-SPARQL, vector retrieval alongside the graph, learned repair, scale, drift, and human evaluation. |
| Not implemented | LLM or embedding calls, vector index, proprietary data, external stores, production integration, and a completed final benchmark artifact. |

## Current artifact metric fields

The current runner and JSON Schema expose exactly these metric fields: status
counts (`status_counts`), status correctness (`status_accuracy`), strict
answer-set fields (`exact_set`, `precision`, `recall`, `f1`), and operational
fields (`syntax_success_rate`, `execution_success_rate`,
`recovery_attempt_rate`, `recovery_success_rate`, `strict_empty_rate`,
`unsupported_rejection_rate`, and `optional_binding_rate`). These are the only
current artifact metrics; Task 13 owns their final values.

## Future-only metric fields

The following fields are not emitted by the current artifact and remain
proposed future work: `relation_path_correctness`, `groundedness`,
`provenance_completeness`, `latency`, `token_count`, `cost`, `robustness`, and
`human_unsupported_answer_rate`. They require a separately implemented
experiment and evidence protocol.

## Evidence fields

The exact values below are intentionally not invented. Task 13 owns the final
claim, artifact, hash, and reproducibility gate.

| Field | Task 12 state |
| --- | --- |
| Git commit | **Pending Task 13:** record the exact final commit SHA after all owned changes are integrated. |
| Input SHA-256 hashes | **Pending Task 13:** record graph, shapes, corpora, code/config, and result-manifest digests from the final run. |
| Dependency lock | `constraints/py312.txt` is the declared lock input; **pending Task 13:** record its exact SHA-256 and resolved package versions. |
| Environment | **Pending Task 13:** record Python version, platform system/machine, pip version, and locked package versions from the final run. |
| Canonical artifact | `results/latest_benchmark.json` is **not yet created** in this Task 12 checkout; Task 13 alone creates and validates it. |
| Final command result | **Not yet run:** Task 13 must run `make PYTHON=.venv/bin/python research-verify` in the final checkout and record exit status and concise output. |
| Final metrics | **Pending Task 13:** read only from the schema-valid canonical artifact; no aggregate values are asserted here. |

## Commands

The single final command is:

```bash
make PYTHON=.venv/bin/python research-verify
```

The final target is expected to generate temporary synthetic graph data, check
generated/check-in graph isomorphism, validate declared SHACL scopes, validate
v1/v2 corpus metadata and hashes, run the two deterministic conditions, write
the canonical artifact, run tests, and run Ruff. It must fail on stale hashes,
namespace drift, unexpected validation, schema/claim violations, test failure,
or lint failure. This paragraph describes the required protocol; it is not a
claim that the final target has passed.

Task 12 documentation checks are narrower and do not create the canonical
artifact:

```bash
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/unit/test_documentation_contract.py::test_research_handoff_contract_and_links -q
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_documentation_contract.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_claim_scan.py -q
PYTHONPATH=src .venv/bin/ruff check tests/unit/test_documentation_contract.py
git diff --check
```

The Markdown contract covers relative link syntax, GitHub-style anchors,
balanced fences, and Mermaid safety. The claim scan and final full link check
remain subject to the complete Task 13 surface and final artifact.

### Observed Task 12 checks

These observations cover the documentation handoff only; they do not fill the
Task 13 fields above.

| Check | Observed result |
| --- | --- |
| Focused `test_research_handoff_contract_and_links` | `1 passed` |
| `tests/unit/test_documentation_contract.py` | `14 passed` |
| `tests/unit/test_claim_scan.py` | `70 passed` |
| AQR planner/repair/provenance/metric contracts | `30 passed` when run with read-only system package paths added for the missing `jsonschema` dependency; no environment files were changed. |
| Targeted Ruff (`tests/unit/test_documentation_contract.py`) | `All checks passed!` |
| `git diff --check` | Exit status 0; no whitespace errors. |
| Full repository pytest | No authoritative Task 12 count is recorded: the shared environment lacks the declared `jsonschema` dependency, and the read-only workaround exposed unrelated federated namespace/asset expectations. Task 13 must run the complete gate in the locked environment. |

The direct shared `.venv` invocation of source-level tests cannot import
`jsonschema` in this checkout. The final verification must use the declared
locked environment rather than treating the read-only workaround above as the
final environment evidence.

## Implemented baseline evidence

The current code supports the following locally inspectable path:

```text
synthetic ontology/data
  -> namespace/schema and graph-parity checks
  -> scoped SHACL validation
  -> finite grounding
  -> typed logical plan
  -> deterministic SPARQL
  -> RDFLib execution
  -> bounded repair/relaxation ledger
  -> strict status and binding-derived provenance
```

The source boundaries are:

* [`schema_linker.py`](../src/semantic_layer/reasoning/schema_linker.py):
  finite grammar and explicit unknown/ambiguous failure classes;
* [`query_planner.py`](../src/semantic_layer/reasoning/query_planner.py):
  typed patterns, component hierarchy path, and bounded prerequisite evidence;
* [`text_to_sparql.py`](../src/semantic_layer/reasoning/text_to_sparql.py):
  deterministic compilation and required-projection validation;
* [`reflective_agent.py`](../src/semantic_layer/reasoning/reflective_agent.py):
  closed statuses, three-attempt repair cap, and strict/relaxed separation;
* [`loader.py`](../src/semantic_layer/kg/loader.py): RDFLib loading and scoped
  SHACL `ValidationReport`.

The controlled corpora are `cifre-synthetic-aqr-v1` (40 records) and the v2
fixture with explicit negative and strict-empty records. The future artifact
must report each corpus and each condition separately; the previous proposal's
Vector-RAG, hallucination, and broad comparative tables are not evidence.

## Hash and artifact contract for Task 13

The final report must include the exact SHA-256 values for the checked-in
graph/shape inputs, generated/check-in parity inputs, corpus files, lock,
tracked code/config manifest, and canonical result. It must include the
artifact schema version, namespace registry, validation checks, per-corpus
dataset hash and query IDs, condition IDs, per-query records, environment, and
package lock metadata. A missing artifact, stale input hash, or unreviewed
metric field is a failed handoff rather than a zero or pass value.

## Known limitations

* The graph and corpora are synthetic, small, and repository-authored. No
  proprietary, customer, or external support data is represented.
* Grounding is a finite deterministic grammar; unsupported phrasing fails
  closed and is not evidence of general language understanding.
* The reasoner has hand-written, bounded repair and uses RDFLib locally. No
  LLM, embedding, vector retriever, external store, or neural baseline has
  been executed.
* Support/ERP validation scopes must be reported accurately; a support-only
  SHACL run is partial rather than whole-repository conformance.
* Scale to millions of documents, ontology evolution, model drift, privacy
  controls, and deployment have not been evaluated.
* Exact commit, final hashes, final metrics, canonical artifact, and final
  command result are **not yet available** and remain Task 13 work.
