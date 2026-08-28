# Governance, quality and security

## Ownership and change control

GlobalSure Group owns the canonical vocabulary, ontology, semantic CI,
interoperability rules, and semantic version. Local entities own source
schemas, local mappings, products, and regulatory restrictions. A pull request
that changes a definition, relationship, join, metric expression, or
normalization must include updated tests and a reviewer from the owning data
office.

Semantic versions follow the contract in the repository: patches correct
metadata; minors add compatible concepts or synonyms; majors change meaning,
joins, or metric semantics and update golden questions. Product certification
is separate from semantic versioning and includes owner, grain, SLA,
classification, quality checks, and lineage.

## Authorization

The demo roles are `ClaimsAnalystFR`, `ClaimsManagerGroup`, `FinanceAnalyst`,
and `AgentService`. Authorization evaluates role, country, purpose, and
classification. A French claims analyst is scoped to French claims; Finance
can use premium metrics without customer PII; an unknown role is denied.
Quality or authorization failures are fail-closed and return a reason code.

## Data quality

The curated path checks non-null identifiers, non-negative incurred loss,
non-future claim dates, governed statuses and countries, and certified product
mappings. `CANCELLED` and `DUPLICATE` claims remain observable for audit but
are excluded from `QualifyingClaim`. A product marked unsafe or degraded must
not be used for a detail answer. Quality status is included in both the API
response and provenance.

## Lineage and provenance

Static lineage describes source-to-product-to-metric transformations in the
product and mapping contracts. Dynamic provenance records a query ID, question
digest, canonical concepts, metric IDs, product and mapping IDs, physical
sources, semantic versions, caller and authorization outcome, quality outcome,
row count, timestamps, and integrity digests. The provenance API can retrieve
the record after execution.

## Security boundary

The demo contains synthetic data and no credentials. It rejects SQL-shaped
business questions at the request boundary and never interpolates model text
into a query template. A local signing key may be configured for restart-safe
demo signatures; production should use an external KMS or signing service.
Platform adapters must use native cloud identity, row-level security, network
controls, and audit logging. The local package's internal names are not a
production security boundary.

## Operations checklist

- Review vocabulary, ontology, rules, products, and mappings as code.
- Run YAML, SHACL, mapping, quality, compiler, golden, and full pytest checks.
- Inspect authorization and quality outcomes before trusting rows.
- Retain provenance alongside the answer and alert on degraded products.
- Test a new platform adapter against the same typed plans and golden cases.
- Never report cloud execution or benchmark performance without live evidence.
