# ADR-006: Use DuckDB for the runnable demo

## Context

An interview-ready reference must run without paid accounts, network access,
or production data while exercising real compilation and execution.

## Decision

Use DuckDB over deterministic local CSV views as the only fully implemented
execution adapter. Keep Databricks, Snowflake, and Fabric mappings and SQL
examples as clearly labeled extension seams.

## Alternatives

Require a cloud account, mock execution entirely, or ship a heavyweight
database server.

## Consequences

The end-to-end path is reproducible and inexpensive. It is not evidence of
cloud latency, cloud security, or production scale.
