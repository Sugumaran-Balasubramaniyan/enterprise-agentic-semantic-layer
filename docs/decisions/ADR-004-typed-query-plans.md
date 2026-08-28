# ADR-004: Use typed, SQL-free query plans

## Context

Free-form model SQL can bypass authorization, use unapproved joins, and lose
provenance.

## Decision

Agents emit a validated Pydantic `SemanticQueryPlan` containing canonical IDs,
typed filters, relationships, metrics, time context, products, caller, and
platform. Only the compiler emits SQL.

## Alternatives

Accept SQL from an LLM, or pass an untyped dictionary directly to a driver.

## Consequences

Unsafe shapes fail at validation and the compiler can enforce approved
templates. The plan schema must evolve with explicit semantic versioning.
