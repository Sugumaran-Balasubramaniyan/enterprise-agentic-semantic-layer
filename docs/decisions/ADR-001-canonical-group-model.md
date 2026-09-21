# ADR-001: Canonical semantic model

## Context

Questions over the synthetic support and relational fixtures need one stable
meaning for business partners, orders, postings, products, and graph terms.
Independent labels would make local mappings and tests incomparable.

## Decision

Maintain one repository-reviewed canonical vocabulary, relationship model,
allowed-value set, and semantic version. Local mappings normalize into those
terms before planning or metric evaluation. This is a repository design
decision, not a claim that an external group owns or publishes the model.

## Alternatives

Allow every local fixture to publish independent semantics, or maintain only a
central table schema without explicit semantic assets.

## Consequences

Cross-fixture questions remain comparable and reviewable. Local schemas retain
their own shape, while mappings and breaking changes are visible in Git and
covered by tests. Future external stewardship would require a separately
reviewed governance process.

External stewardship is **Proposed future work** and is **Not implemented**.
