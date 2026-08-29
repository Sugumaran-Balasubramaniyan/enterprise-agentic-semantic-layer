# Task 8 report: GitHub publication integrity

## Status

Validated pending the commit and push recorded by the task handoff.

## Changes

- Strengthened the documentation contract so every tracked Markdown fence is
  balanced and every README/docs Mermaid fence closes independently.
- Kept GitHub Mermaid labels safe by rejecting literal `\\n` and non-self-closing
  `<br>` labels; the existing multi-line labels use `<br/>`.
- Preserved local relative-link and anchor validation and the regression guard
  for obsolete audience-specific references.
- Reconciled README's current verification date and full-suite count to
  `2026-08-29 UTC` and `205 passed`.
- Added fresh publication-integrity evidence to `docs/verification-report.md`.

## TDD evidence

The revised README-evidence assertion was run before the documentation update
and failed as intended because the handbook still said `195 passed` instead
of the post-change expected `205 passed`. After the documentation update, the
focused documentation contract passed with 17 tests.

## Verification

- Documentation contract: 17 passed.
- Lint, semantic validation, YAML, mapping/quality, golden, compiler,
  evaluation, and demo checks passed.
- Full suite: 205 passed with one existing FastAPI/Starlette `TestClient`
  deprecation warning.
- Markdown-link, Mermaid/fence, stale-reference scans, and `git diff --check`
  passed.

## Concern

No Mermaid CLI is installed locally. `npx --no-install` declined to fetch the
missing package, so this task used the in-repository static publication
contract and direct block inspection; GitHub preview remains the final render
environment.
