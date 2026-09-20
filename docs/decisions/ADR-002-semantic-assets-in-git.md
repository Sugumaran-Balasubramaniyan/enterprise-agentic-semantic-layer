# ADR-002: Keep semantic assets in Git

## Context

Definitions, mappings, rules, and synthetic contracts need peer review,
versioned history, reproducible checks, and a recoverable change trail.

## Decision

Store canonical YAML, Turtle, SHACL, contract, and mapping assets in Git. Load
them into the local registry at runtime; the checked-in files remain the source
of truth for this prototype.

## Alternatives

Use an opaque catalog-only interface or store semantic definitions solely in
application code.

## Consequences

Changes are diffable and testable, and local runs can be reproduced from a
checkout. A future catalog may mirror the assets, but it must preserve the
version, review, and rollback semantics; no such catalog connection is
implemented here.

A catalog mirror is **Proposed future work**; external catalog integration is
**Not implemented**.
