# Golden semantic evaluation

The checked-in suite in `tests/golden/questions.yaml` is a small, reviewable
contract test set for the semantic control plane. It contains 31 governed
questions, including ten secondary examples covering active-policy and
claims-ratio discovery across the French, UK, and German vocabulary. Every case
declares expected canonical concepts, relationship paths, certified products,
metrics, authorization outcome, and either an executable deterministic answer
or an explicit discovery-only constraint.

`run_evaluation(registry)` loads the cases and evaluates each dimension against
the supplied `SemanticRegistry`. The resulting `EvaluationReport` includes
per-case evidence and independent `resolution`, `relationships`, `products`,
`metrics`, `authorization`, `deterministic_answers`, and `discovery_only`
summaries. This is a local semantic regression signal, not a benchmark: no
external traffic, production data, or fabricated accuracy claim is involved.
The primary local DuckDB answer and governed primary/threshold variants execute
the agent path with quality, authorization, provenance, and metric evidence;
discovery-only cases intentionally stop after semantic discovery and are counted
separately.

Run the evaluation from the repository root:

```bash
make PYTHON=.venv/bin/python evaluate
```

Example output from the current synthetic fixture set:

```text
Golden evaluation: 31/31 cases passed (resolution=31/31, relationships=31/31, products=31/31, metrics=31/31, authorization=31/31, deterministic_answers=31/31, discovery_only=10/10)
```

The semantic regression tests separately protect metric/rule references,
ClaimsRatio's independent aggregate contract, and the `ActivePolicy` semantic
version, definition, included status, and exclusions. CI runs YAML parsing,
SHACL validation, mapping/data-quality tests, compiler tests, this golden
suite, and the complete pytest suite.
