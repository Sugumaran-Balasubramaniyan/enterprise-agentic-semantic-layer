# ADR-007: Keep the governed core deterministic

## Context

Language models could improve conversational UX but introduce variability and
must not invent joins, metrics, graph edges, or access decisions in this
prototype.

## Decision

Resolver, planner, policy, compiler, quality checks, execution, and provenance
are deterministic and testable. The current implementation has no LLM call.
Future parsing or explanation assistance may be evaluated only behind these
validation boundaries.

## Alternatives

Make an LLM the primary planner or expose an unconstrained agent tool.

## Consequences

Local answers are reproducible and fail closed where the implemented policy
requires it. Natural-language coverage is intentionally bounded until new
patterns receive governed tests. Learned components remain **Proposed future
work**.

The deterministic implementation is evaluated only on the local synthetic
fixtures; broader evaluation is **Proposed future work**.
