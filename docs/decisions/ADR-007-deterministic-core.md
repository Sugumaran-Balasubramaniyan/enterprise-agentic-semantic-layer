# ADR-007: Keep the governed core deterministic

## Context

Language models can improve conversational UX but introduce variability and
must not be allowed to invent joins, metrics, or access decisions.

## Decision

Resolver, planner, authorization, compiler, quality checks, execution, and
provenance are deterministic and testable. An optional LLM may assist parsing
or explanation only after and before these validation boundaries.

## Alternatives

Make an LLM the primary planner, or expose an unconstrained agent tool.

## Consequences

Answers are reproducible and fail closed. Natural-language coverage is
intentionally bounded until new patterns receive governed tests.
