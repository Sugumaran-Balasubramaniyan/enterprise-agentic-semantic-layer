# Governance, quality, and security boundary

This is a local synthetic prototype. Governance language on this page describes
review practices and future deployment requirements, not an external owner or
certification authority.

## Review and change control

Changes to a vocabulary, namespace, relationship, graph shape, metric, rule,
contract, or mapping should include a focused test, a status label, and a
traceable rationale. Semantic versions distinguish metadata corrections,
compatible additions, and meaning-changing updates. Golden cases and SHACL
fixtures should change with the contract they exercise.

The files in `data_products/` are repository-maintained synthetic contracts.
Their `CERTIFIED` field is an internal selection status. It does not assert
publication, approval, or certification outside this repository.

## Authorization and quality

The local API's role, country, and purpose fields are simulated caller context,
not authentication. The local policy evaluates those fields together with
product classification, PII declarations, and the requested metric. Unknown or
over-classified contexts are denied by the implemented policy. Quality checks
cover identifiers, non-negative amounts, dates, statuses, countries, and
illustrative mappings. Reversed and duplicate rows remain observable for local
analysis but are excluded from the qualifying-posting rule.

## Lineage and provenance

Static lineage describes source-to-contract-to-metric transformations. Dynamic
local provenance records a query ID, question digest, canonical concepts,
metric IDs, contract and mapping IDs, semantic versions, simulated caller
context, policy outcome, quality outcome, row count, timestamps, and integrity
digests. Provenance is evidence for a local run; it is not a claim of durable
production retention.

## Security and privacy boundary

The demo contains synthetic data and no credentials. It rejects SQL-shaped
questions and never interpolates model text into a query template. A local
signing key can demonstrate restart-safe evidence, but an actual deployment
would need an external key service, identity provider, row/column controls,
network policy, audit logging, privacy review, and incident procedures.

Security, privacy, authentication, and governance controls are incomplete in
this prototype. No cloud execution or production performance should be
reported without a separate environment and evidence.

## Local checklist

- Review vocabulary, ontology, rules, contracts, and mappings as code.
- Run YAML, SHACL, mapping, quality, compiler, golden, and focused tests.
- Inspect policy and quality outcomes before relying on local rows.
- Retain local provenance alongside a result during an experiment.
- Treat platform mappings as illustrative until an adapter is independently tested.

External certification and production governance are **Not implemented**;
deployment controls are **Proposed future work**.
