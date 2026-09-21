# ADR-005: Compile at the platform boundary

## Context

The same semantic intent may eventually target local DuckDB and other engines,
but dialects, security controls, and credentials are not interchangeable.

## Decision

Compile an approved typed plan through a platform-specific compiler and let the
native adapter execute under its own identity and security controls. The local
DuckDB adapter is the only implemented execution adapter in this repository.

## Alternatives

Generate one dialect-neutral SQL string, or let each platform independently
reinterpret semantic meaning.

## Consequences

The control plane stays portable and mappings remain explicit. Each future
adapter needs independent credentials, semantics, performance, and security
verification. Cloud examples in this repository are unexecuted simulations.

Cloud adapter implementation is **Proposed future work** and is **Not
implemented**.

The implemented adapter executes only the local synthetic fixtures.
