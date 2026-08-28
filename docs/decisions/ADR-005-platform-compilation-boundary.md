# ADR-005: Compile at the platform boundary

## Context

The same semantic intent must target DuckDB locally and cloud engines without
pretending their dialects, security, or credentials are interchangeable.

## Decision

Compile an approved typed plan through a platform-specific compiler and let the
native adapter execute under native identity and security controls.

## Alternatives

Generate one dialect-neutral SQL string, or let each platform own semantic
interpretation independently.

## Consequences

The control plane stays portable and mappings are explicit. Each adapter needs
independent credential, performance, and security verification; cloud examples
in this repository are unexecuted artifacts.
