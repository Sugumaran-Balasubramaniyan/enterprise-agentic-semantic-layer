# ADR-001: Canonical Group model

## Context

France, the UK, and Germany use different labels and physical schemas, while
Group reporting needs one meaning for Customer, Policy, Claim, and products.

## Decision

Group owns canonical concepts, relationships, allowed values, and semantic
versioning. Local mappings normalize into those concepts before planning or
metric evaluation.

## Alternatives

Allow each country to publish independent semantics, or maintain a central
warehouse schema without explicit semantic assets.

## Consequences

Cross-country questions become comparable and reviewable. Local teams retain
schema autonomy, but must maintain mappings and coordinate breaking changes.
