# Task 7 report: golden semantic evaluation and CI checks

## Delivered

- Added `tests/golden/questions.yaml` with 31 governed questions, including
  ten explicitly identified secondary active-policy and claims-ratio examples
  across FR/GB/DE vocabulary and role scopes.
- Added `load_golden_cases`, `run_evaluation`, `EvaluationReport`, per-case
  evidence, and dimension summaries under `src/semantic_layer/evaluation`.
- Added the primary deterministic answer assertion and metric/rule plus
  `ActivePolicy` semantic-version regression tests.
- Added `docs/evaluation.md` documenting scope, measured output, and the
  discovery-only boundary for secondary patterns.
- Added Make targets for YAML parsing, semantic validation, mapping/data
  quality, golden tests, and compiler tests; CI now runs each target plus the
  full suite.
- Extended deterministic resolver matching with exact plural inflections so
  ordinary governed language such as “customers”, “claims”, and “policies” is
  grounded without fuzzy matching.

## TDD evidence

RED, before the evaluation package existed:

```text
$ .venv/bin/python -m pytest tests/golden/test_evaluation.py tests/semantic/test_metric_rules.py tests/semantic/test_active_policy_regression.py -q
ModuleNotFoundError: No module named 'semantic_layer.evaluation'
```

GREEN, after implementation:

```text
$ .venv/bin/python -m pytest tests/golden/test_evaluation.py tests/semantic/test_metric_rules.py tests/semantic/test_active_policy_regression.py -q
.......                                                                  [100%]
7 passed in 1.58s
```

## Required semantic verification

```text
$ make PYTHON=.venv/bin/python validate-semantic
Vocabulary: 13 concepts loaded
sample-graph-valid.ttl: CONFORMS (conforms)
sample-graph-invalid.ttl: DOES NOT CONFORM (fails as expected)
Validation Report
Conforms: False
Results (2):
... claim-FR-BAD missing claimDate ...
... claim-FR-BAD incurredLoss is not >= 0 ...

$ make PYTHON=.venv/bin/python evaluate
Golden evaluation: 31/31 cases passed (resolution=31/31, relationships=31/31, products=31/31, metrics=31/31, authorization=31/31, deterministic_answers=31/31)

$ .venv/bin/python -m pytest tests/golden tests/semantic -q
..........................................                               [100%]
42 passed in 2.13s
```

The SHACL violation output is the deliberate invalid fixture; the validation
CLI exits successfully only because the valid/invalid pair has the expected
conformance outcomes.

## Full verification

```text
$ .venv/bin/ruff check .
All checks passed!

$ .venv/bin/python -m pytest -q
........................................................................ [ 59%]
..................................................                       [100%]
122 passed, 1 warning in 8.77s

$ git diff --check
(no output; exit 0)
```

The one warning is the installed FastAPI/Starlette TestClient deprecation
notice for the current httpx compatibility layer. It does not fail tests.

## Commit

Pending commit: `test: add golden semantic evaluation suite`.
