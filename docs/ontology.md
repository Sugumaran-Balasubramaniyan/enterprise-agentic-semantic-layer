# Synthetic ERP semantic ontology

The local ERP ontology is stored in
[`semantic/ontology/sap_erp.ttl`](../semantic/ontology/sap_erp.ttl). Its
resources use the neutral `ciferp` namespace and represent synthetic fixtures.
The filename is retained for repository compatibility; its identifiers are not
external organization namespaces.

`ciferp:ProductAutomotive` and `ciferp:ProductCommercial` are subclasses of
`ciferp:Product`. A `ciferp:BusinessPartner` holds a
`ciferp:SalesOrder` and is associated with `ciferp:FinancialPosting` records.
A posting references its order; an order has a product, a business partner,
and billing documents. Domain, range, identifier, status, date, and amount
properties are used by the local validation graph.

The product taxonomy keeps SKOS concepts under `cifskos`. A reviewed
`cifmeta:CrosswalkEntry` relates a synthetic OWL product resource to a SKOS
concept; a class is not silently treated as a concept or vice versa.
`cifmeta` metadata marks fixtures as synthetic and non-official.

`ciferp:countryCode` is shared through the `CountryCodedEntity` superclass, so
its domain does not incorrectly require an instance to be two unrelated types.
SHACL supplies instance constraints, while the ontology describes meaning and
relationships. Neither replaces local product contracts, policy checks, or SQL
compilation.

This is the intentional ontology/runtime boundary: graph assets answer what
entities and relationships mean, while local contracts and compilers answer how
an approved analytical query runs. See [ADR-003](decisions/ADR-003-ontology-runtime-boundary.md).

External ontology ownership and production-scale validation are **Not
implemented**; broader ingestion and evaluation are **Proposed future work**.
