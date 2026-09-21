# ADR-006: Use DuckDB for the runnable demo

## Context

A local reference should run without a paid account, network access, or
proprietary data while exercising real compilation and execution.

## Decision

Use DuckDB over deterministic local CSV views as the only fully implemented
execution adapter. Keep platform mappings and dialect snippets as clearly
labeled illustrative extension seams.

## Alternatives

Require a cloud account, mock execution entirely, or ship a heavyweight
database server.

## Consequences

The end-to-end path is reproducible and inexpensive for synthetic fixtures. It
is not evidence of cloud latency, cloud security, production scale, or a live
platform connection.

Cloud execution is **Not implemented**; broader platform evaluation is
**Proposed future work**.
