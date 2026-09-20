# ADR-008: Select reviewed synthetic data contracts

## Context

Selecting physical tables by guessed names makes grain, quality, lineage, and
privacy assumptions implicit and easy to bypass.

## Decision

The local workflow selects only versioned repository-maintained synthetic
contracts whose internal status is `CERTIFIED`. Contracts declare grain,
classification, PII fields, quality checks, lineage, and exposed concepts;
unsafe contracts block detail execution.

`CERTIFIED` is a synthetic contract status for this repository's local tests.
It is not external certification, publication, endorsement, or evidence that a
catalog or platform is connected.

## Alternatives

Let the workflow search every table, or centralize all data in one uncontracted
warehouse relation.

## Consequences

Local product selection is explainable and auditable, with a clear onboarding
path for additional synthetic fixtures. Maintaining the contracts adds review
overhead. Future external certification would be a separate process and is not
implemented here.

External certification is **Not implemented**; any future certification
workflow is **Proposed future work**.
