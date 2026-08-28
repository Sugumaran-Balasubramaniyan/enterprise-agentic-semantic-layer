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

## Round 1 review remediation evidence

RED, before strict loader and constraint validation:

```text
$ .venv/bin/python -m pytest tests/golden/test_evaluation.py tests/unit/test_resolver.py -q
8 failed, 10 passed
Failures: duplicate natural-language questions, omitted expectation fields,
and mutated rule/metric constraints were accepted.
```

GREEN after the review fixes:

```text
$ .venv/bin/python -m pytest tests/golden/test_evaluation.py tests/unit/test_resolver.py -q
..................                                                       [100%]
18 passed in 2.04s
```

The loader now requires concepts, relationships, products, metrics, and
authorization expectations, and rejects duplicate question text. Constraint
references resolve through the registry and must match discovered metrics and
their governed rules. A focused plural-resolution regression covers customers,
claims, policies, ActivePolicy, and QualifyingClaim.

Final remediation matrix:

```text
$ make PYTHON=.venv/bin/python lint
All checks passed!
$ make PYTHON=.venv/bin/python check-yaml
YAML: 11 files parsed
$ make PYTHON=.venv/bin/python check-mappings-quality
21 passed in 0.67s
$ make PYTHON=.venv/bin/python check-golden
11 passed in 1.62s
$ make PYTHON=.venv/bin/python check-compiler
3 passed in 0.47s
$ make PYTHON=.venv/bin/python test
131 passed, 1 warning in 9.10s
$ make PYTHON=.venv/bin/python evaluate
Golden evaluation: 31/31 cases passed (resolution=31/31, relationships=31/31, products=31/31, metrics=31/31, authorization=31/31, deterministic_answers=31/31)
```

## Commit history

The baseline Task 7 implementation was committed as
`e1e1631497b98a016ad93d7f783fbbbeab867c58` (`test: add golden semantic evaluation suite`).
This report is being updated for the first review-remediation round; the
remediation is committed as
`fix: harden golden evaluator integrity` (the commit SHA is reported by the
handoff separately so this evidence file does not contain a self-referential
hash).
