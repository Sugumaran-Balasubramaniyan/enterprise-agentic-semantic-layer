# ADR-002: Keep semantic assets in Git

## Context

Definitions, mappings, rules, and product contracts need peer review,
versioned history, reproducible CI, and rollback.

## Decision

Store canonical YAML, Turtle, product contracts, and mappings in Git. Load them
into the local registry at runtime; Git remains the source of truth.

## Alternatives

Use an opaque catalog-only UI or store definitions solely in application code.

## Consequences

Changes are diffable and testable, and local demos are reproducible. A
production catalog may mirror these assets, but must preserve ownership,
version, review, and rollback semantics.
