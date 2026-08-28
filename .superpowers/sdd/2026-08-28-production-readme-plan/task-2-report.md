# Task 2 report: local setup and data lifecycle guidance

## Status

Completed. The README now documents the local developer contract and the
synthetic data lifecycle in production-oriented terms.

## Changes

- Added a Python, operating-system, Git, cloud, LLM, Docker, and platform
  support matrix.
- Added clean checkout and virtual-environment installation instructions.
- Added configuration guidance for application, provenance, and integrity-test
  environment variables, including signing-key safety and `.env` handling.
- Documented the Git-backed registry as the source of truth and the disposable
  SQLite cache behavior.
- Documented raw versus curated fixture policy, quality failures, regeneration,
  explicit as-of behavior, and deterministic seed policy.
- Added local dataset schemas, grain, required keys, join keys, fields, and the
  claims-ratio fan-out safeguard.
- Documented dependency minimum-version behavior and the absence of a committed
  lockfile as a reproducibility caveat.
- Added focused documentation contract assertions.

## Verification

- `pytest tests/unit/test_documentation_contract.py -q`: 12 passed.
- `ruff check .`: passed.
- `git diff --check`: passed.
- `make PYTHON=.venv/bin/python validate-semantic`: valid graph conforms and
  invalid fixture fails as expected.
- `make PYTHON=.venv/bin/python demo`: completed with deterministic `FR_001`
  and `FR_002` results.

## Concerns and follow-up

- The generator currently uses explicit deterministic records rather than a
  random-number generator; the README records the seed policy for future
  randomized expansion.
- Dependency versions are minimum bounds rather than a lockfile. A production
  deployment should generate and review a platform-specific lockfile.
- The documentation still contains historical interview-demo material elsewhere
  in the README; a later documentation pass should remove or relocate that
  material as requested by the project owner.
