# SAP S/4HANA Enterprise Semantic Layer Ontology

The canonical ontology lives in [`semantic/ontology/sap_erp.ttl`](../semantic/ontology/sap_erp.ttl). It is a governed OWL/RDFS vocabulary for the concepts that must interoperate across the French, UK, and German enterprise operating units.

`ProductAutomotive` and `ProductCommercial` are subclasses of `Product`. A `BusinessPartner` holds a `SalesOrder` and is associated with `FinancialPosting` records; a `FinancialPosting` references its `SalesOrder`. A `SalesOrder` has a product, references business partners, and generates billing documents. The ontology defines domain and range declarations for those relationships, plus identifier, status, date, and debit amount properties used by the local validation graph. `orderProduct` and `postingOrder` remain explicit subproperty aliases for compatibility; the canonical sample graph and SHACL constraints use `hasProduct` and `referencesSalesOrder`.

`countryCode` is shared by business partners and sales orders through the `CountryCodedEntity` superclass, so its domain does not incorrectly require an instance to be both.

The ontology describes meaning and relationships; it does not replace analytical product contracts, authorization, or SQL compilation. The SKOS product taxonomy supplies preferred and alternative labels, while SHACL supplies instance-data constraints.

This is intentionally an ontology/runtime boundary: graph assets answer what entities and relationships mean, while certified products and platform compilers answer how an approved analytical query runs. See [ADR-003](decisions/ADR-003-ontology-runtime-boundary.md).
