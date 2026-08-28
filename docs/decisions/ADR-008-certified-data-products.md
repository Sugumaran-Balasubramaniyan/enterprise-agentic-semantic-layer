# ADR-008: Select certified data products

## Context

Selecting physical tables by guessed names makes grain, quality, lineage, and
security implicit and easy to bypass.

## Decision

Agents select only versioned, certified product contracts. Contracts declare
grain, owner, SLA, classification, PII, quality checks, lineage, and exposed
concepts; unsafe products block detail execution.

## Alternatives

Let the agent search every table, or centralize all data in one uncontracted
warehouse relation.

## Consequences

Product selection is explainable and auditable, with a clear onboarding path
for local entities. Certification adds stewardship and release overhead.
