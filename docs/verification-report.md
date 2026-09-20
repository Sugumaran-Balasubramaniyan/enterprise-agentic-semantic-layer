# Research handoff verification report

**Evidence date:** 2026-09-20 UTC
**Scope:** final CIFRE synthetic research artifact and reproducibility gate
**Status:** final preliminary evidence recorded; canonical artifact finalized

> This is an independent, unaffiliated candidate prototype using synthetic
> support and product-lifecycle fixtures. It is not an SAP product, SAP
> publication, SAP-endorsed benchmark, or report of access to SAP internal
> data. The repository demonstrates a deterministic symbolic baseline and
> proposes future LLM/retrieval experiments; it does not claim completed PhD
> research or production readiness.

Historical commands and old comparative numbers remain historical evidence in
[`cifre-hardening-baseline.md`](research/cifre-hardening-baseline.md); they are
not reused as current results. The final report deliberately avoids the phrase “not yet available” as a status for the canonical artifact: it is present and validated.

## Implemented/proposed/not-implemented boundary

| Status | Boundary |
| --- | --- |
| Implemented locally | Synthetic RDF/Turtle fixtures; deterministic grounding, typed plans, SPARQL compilation, RDFLib execution, scoped SHACL reports, bounded repair, binding-derived provenance, and the committed preliminary artifact. |
| Proposed future work | Learned grounding, constrained Text-to-SPARQL, vector retrieval alongside the graph, learned repair, scale, drift, and human evaluation. |
| Not implemented | LLM or embedding calls, vector index, proprietary data, external stores, production integration, or claims beyond this preliminary synthetic artifact. |

## Current artifact metric fields

The current runner and JSON Schema expose exactly these metric fields: status
counts (`status_counts`), status correctness (`status_accuracy`), strict
answer-set fields (`exact_set`, `precision`, `recall`, `f1`), and operational
fields (`syntax_success_rate`, `execution_success_rate`,
`recovery_attempt_rate`, `recovery_success_rate`, `strict_empty_rate`,
`unsupported_rejection_rate`, and `optional_binding_rate`). Exact values are
reported below and in [`results/latest_benchmark.json`](../results/latest_benchmark.json).

## Future-only metric fields

The following fields are not emitted by the current artifact and remain
proposed future work: `relation_path_correctness`, `groundedness`,
`provenance_completeness`, `latency`, `token_count`, `cost`, `robustness`, and
`human_unsupported_answer_rate`. Each requires a separately implemented
experiment and evidence protocol.

## Evidence fields

This Task 13 finalization run used base source revision
`0744f635f68f12ff71af7618dd0f50f470424975` plus the final hardening changes in
the working tree, Python `3.12.3`, Linux `aarch64`, and pip `25.2`. The exact
locked package map is embedded in the artifact environment section.

| Field | Observed evidence |
| --- | --- |
| Base source revision for measured run | `0744f635f68f12ff71af7618dd0f50f470424975` plus final working-tree hardening changes |
| Artifact schema | `1.0.0`, canonical UTF-8 JSON, 184 per-query records, two corpora, two conditions |
| Pre-documentation temporary-run manifest | `157` entries; digest `142db4126ab35bd559c640258f284b64b0c691692a96aedb718793d6469d2fd8` (historical temporary evidence, not the canonical post-documentation digest) |
| Dependency lock | `constraints/py312.txt`; SHA-256 `a8b8a5054ae3d55cfc51950b0276d9d7d00c725c7676cad1cdc741ef274f1534` |
| Platform/environment | Python `3.12.3`; Linux `aarch64`; pip `25.2`; third-party versions are sorted in artifact `environment.packages` |
| Canonical artifact | [`results/latest_benchmark.json`](../results/latest_benchmark.json), schema-validated and manifest-validated |
| Outer artifact digest | Deliberately not embedded in this manifest-covered report; run `sha256sum results/latest_benchmark.json` |
| Final command | `make PYTHON=.venv/bin/python research-verify`; exit `0` in the locked verification environment; supported runtime differences are reported separately from deterministic content |
| Secret scan | Repository-native fail-closed tracked-file scanner; the optional `gitleaks` binary was unavailable and is not claimed as run |

### Measured preliminary metrics

| Corpus | Dataset SHA-256 | N | Condition(s) | Status accuracy | Exact / precision / recall / F1 | Syntax | Execution | Strict empty | Unsupported rejection |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| `cifre-synthetic-aqr-v1` | `6fe8532232c66b04c7cbe92f8479e809dd57c38890d59db4672d0c20a9c04f67` | 40 | no-reflection; bounded-repair | `1.000000` | `1.000000 / 1.000000 / 1.000000 / 1.000000` | `1.000000` | `1.000000` | `0.200000` | `null` |
| `cifre-synthetic-aqr-v2` | `40c3cf58b29de5d99a34f5640b982e79c42a217d8e6f73d8b7534a3eddd60168` | 52 | no-reflection; bounded-repair | `1.000000` | `1.000000 / 1.000000 / 1.000000 / 1.000000` | `1.000000` | `0.846154` | `0.230769` | `1.000000` |

The two conditions are retained separately in the artifact and produce the
same aggregate values on these deterministic fixtures. Status counts are v1
`SUCCESS=32, EMPTY_RESULT=8, UNSUPPORTED=0` and v2
`SUCCESS=32, EMPTY_RESULT=12, UNSUPPORTED=8`; all other statuses are zero.

The canonical validation inputs were measured with these byte hashes:

| Input | SHA-256 |
| --- | --- |
| `semantic/ontology/sap_support.ttl` | `5d8ee297caf5ee2842fdf76c568428138523a93a9239cef5db82a3a5234164a8` |
| `semantic/ontology/sap_ppms.ttl` | `90aa9beea27ec0a04851255b003432a679b673bc7c39c422cf966bcdee7c49d8` |
| `semantic/data/sap_support_graph.ttl` | `e36887b065ea722861f7a5d9b382bdebea349f37f7360245843b8375db40b017` |
| `semantic/ontology/sap_erp.ttl` | `9e3031e50268f6288b671f835a5059e042cd62ad0904a925754f55dfb9e1c971` |
| `semantic/ontology/sample-graph-valid.ttl` | `a71f3009c6b5961985ffac339f0725b994a385db899545a66a60168b409c09fe` |
| `semantic/shapes/sap_support_shapes.ttl` | `483850daf948b45f3984a0374fff59d8445d6f40e0c9ce8828a87b79c047ed76` |
| `semantic/shapes/sap_erp_shapes.ttl` | `e3d7dbb687800fd3a4d60b09a8551f4318553f148de43c61b009a9705090b647` |
| combined graph / shapes | `f419406cdc4367d3b9cfce17bb8aa5a405eb2b4987f37298b7820cb081fae6cb` / `5568aca9287fbeb9f0731bb25837ed481e2f650d72fda921ebfe3f70e9eb7127` |

## Commands

The final verification target is:

```bash
make PYTHON=.venv/bin/python research-verify
```

It generates a temporary benchmark, checks generated/check-in graph
isomorphism, validates all five SHACL rows and the prerequisite cycle/depth
row, checks v1/v2 metadata and hashes, validates the committed artifact against
the final manifest/schema/result IDs and repository scans, runs the complete
pytest suite, and runs locked Ruff. It fails on stale bytes, namespace drift,
unexpected validation, claim/secret/placeholder findings, schema drift, test
failure, or lint failure. It never rewrites the canonical artifact.

The one-time publication boundary is explicit and separate:

```bash
PYTHONPATH=src .venv/bin/python -c \
  'from pathlib import Path; from semantic_layer.validation import finalize_research_artifact; print(finalize_research_artifact(Path(".")))'
```

Run it only after every manifest-covered source and documentation byte is
final, then run `research-verify` and regenerate the artifact if any such byte
changes.

## Implemented baseline evidence

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

* [`schema_linker.py`](../src/semantic_layer/reasoning/schema_linker.py): finite grammar and explicit unknown/ambiguous failure classes;
* [`query_planner.py`](../src/semantic_layer/reasoning/query_planner.py): typed patterns, component hierarchy path, and bounded prerequisite evidence;
* [`text_to_sparql.py`](../src/semantic_layer/reasoning/text_to_sparql.py): deterministic compilation and required-projection validation;
* [`reflective_agent.py`](../src/semantic_layer/reasoning/reflective_agent.py): closed statuses, bounded repair, and strict/relaxed separation;
* [`loader.py`](../src/semantic_layer/kg/loader.py): RDFLib loading and scoped SHACL `ValidationReport`.

## Known limitations

* The graph and corpora are synthetic, small, and repository-authored. No
  proprietary, customer, or external support data is represented.
* Grounding is a finite deterministic grammar; unsupported phrasing fails
  closed and is not evidence of general language understanding.
* The reasoner has hand-written, bounded repair and uses RDFLib locally. No
  LLM, embedding, vector retriever, external store, or neural baseline has
  been executed.
* Support/ERP validation scopes are reported separately; support-only SHACL is
  partial rather than whole-repository conformance.
* Scale to millions of documents, ontology evolution, model drift, privacy
  controls, and deployment have not been evaluated.
* Findings are preliminary and require reproduction from the locked source and
  committed artifact before any broader research claim.
