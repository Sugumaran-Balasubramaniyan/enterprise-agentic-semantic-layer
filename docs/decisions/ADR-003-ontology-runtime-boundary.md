# ADR-003: Keep ontology and analytical runtime distinct

## Context

RDF/OWL and SHACL express typed relationships and graph constraints, while
relational execution is a clearer fit for the synthetic analytical fixtures.
Turning every aggregation into graph traversal would obscure that boundary.

## Decision

Use ontology, taxonomy, and SHACL for meaning, relationships, and graph
validation. Use repository-maintained synthetic contracts and the local DuckDB
compiler for approved aggregation.

## Alternatives

Use a knowledge-graph-only runtime, or omit graph assets and rely on physical
table names alone.

## Consequences

The prototype retains explainable graph relationships while exercising a real
local analytical path. The graph and contract checks must stay aligned through
semantic tests. This decision does not claim production scale or external
platform compatibility.

Production-scale graph/runtime validation is **Proposed future work** and is
**Not implemented**.
