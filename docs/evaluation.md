# Local evaluation and preliminary research

The checked-in golden suite in `tests/golden/questions.yaml` is a small,
reviewable semantic regression contract. It checks canonical resolution,
relationship paths, synthetic contract selection, metrics, simulated policy,
and deterministic answers where a case has an executable local path. Discovery-
only cases stop before execution by design.

Run the local regression command from the repository root:

```bash
make PYTHON=.venv/bin/python evaluate
```

`run_evaluation(registry)` returns per-case evidence and separate summaries for
resolution, relationships, products, metrics, authorization, deterministic
answers, and discovery-only cases. This is a local regression signal over
synthetic fixtures. It is not a production evaluation, a proprietary-data
study, or evidence of broad generalization.

The controlled v1/v2 KG/AQR benchmark methodology is described first in the
README. It records exact per-query outcomes, strict versus relaxed status,
repair attempts, and provenance. The canonical result artifact and final
metrics are owned by the final publication task, so this page intentionally
does not state final numbers or hashes.

The regression suite also covers metric/rule references, independent aggregate
semantics for the ratio definition, SHACL outcomes, namespace contracts, and
the bounded deterministic core. A green local test run is evidence about the
checked-in implementation only.

External-model comparisons and production-scale evaluation are **Not
implemented**. They remain **Proposed future work** with separate protocols.
