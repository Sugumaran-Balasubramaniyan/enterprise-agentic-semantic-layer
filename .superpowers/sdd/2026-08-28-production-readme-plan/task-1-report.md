# Task 1 report: API and verification contract

## Scope

Aligned the public README with the registered FastAPI transport and the latest
checked-in verification evidence. Added documentation-contract regression tests
so unsupported routes or stale evidence wording cannot silently return.

## Files changed

- `README.md`
  - Replaced unsupported detail routes with the exact implemented routes.
  - Documented request-body constraints, simulated caller context, fail-closed
    behavior, and `/validate` read-only behavior.
  - Added dated verification evidence and the source-of-truth report link.
- `tests/unit/test_documentation_contract.py`
  - Added route-table coverage against `create_app()`.
  - Added verification date/source/pass-count assertions.

The concurrent parent-task edit to the production README design spec was not
included in this task commit.

## TDD evidence

The new tests initially failed as intended:

- route test failed because README contained unsupported detail routes and did
  not list the implemented `GET /concepts/{concept_id}` route;
- evidence test failed because README lacked `2026-08-28 UTC`.

After the README changes:

```text
./.venv/bin/python -m pytest tests/unit/test_documentation_contract.py -q
10 passed in 2.04s

make PYTHON=./.venv/bin/python lint
All checks passed!

git diff --check
exit status 0
```

## Commit and push

Commit: `56b1d1ea7ff636d12bd89005e49504a664c21e12` (before report metadata amend).

Push target: `origin/feat/semantic-layer-implementation`.

## Concerns

- The request-body `role` remains explicitly documented as simulated context,
  not authentication; production identity must be supplied by the transport.
- Cloud adapters and cloud SQL remain documented as unexecuted extensions.
- The README’s earlier interview-oriented content is outside this focused API
  and evidence task and is being handled by the parent production-README work.
