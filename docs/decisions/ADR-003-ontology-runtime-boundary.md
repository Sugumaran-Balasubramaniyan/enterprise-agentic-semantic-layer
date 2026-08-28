# ADR-003: Keep ontology and analytical runtime distinct

## Context

RDF/OWL and SHACL are useful for typed relationships and graph validation, but
turning every aggregation into graph traversal would complicate analytical
execution.

## Decision

Use ontology, taxonomy, and SHACL for meaning, relationships, and validation;
use certified analytical products and platform compilers for aggregation.

## Alternatives

Use a knowledge-graph-first runtime, or omit graph assets and rely on table
names alone.

## Consequences

The design retains explainable relationships without sacrificing SQL engine
strength. Two contracts must be kept aligned through semantic CI.
