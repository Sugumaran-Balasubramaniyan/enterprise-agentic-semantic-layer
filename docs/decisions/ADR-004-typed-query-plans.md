# ADR-004: Use typed, SQL-free query plans

## Context

Free-form generated SQL can bypass policy, use unapproved joins, and lose local
provenance. A deterministic prototype needs a small, inspectable interface.

## Decision

The workflow emits a validated Pydantic `SemanticQueryPlan` containing
canonical IDs, typed filters, relationships, metrics, time context, selected
synthetic contracts, simulated caller context, and target platform. Only the
local compiler emits SQL.

## Alternatives

Accept SQL from an LLM or pass an untyped dictionary directly to a database
driver.

## Consequences

Unsafe shapes fail validation and the compiler can enforce approved templates.
The plan schema must evolve with explicit semantic versioning and focused
tests. A future learned parser would remain a proposal at this boundary.

Learned parsing is **Proposed future work** and is **Not implemented** here.
