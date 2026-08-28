# GlobalSure insurance ontology

The canonical ontology lives in [`semantic/ontology/insurance.ttl`](../semantic/ontology/insurance.ttl). It is a small OWL/RDFS vocabulary for the concepts that must interoperate across the French, UK, and German local entities.

`MotorInsurance` is an `InsuranceProduct`. Policies point to products with `hasProduct`/`policyProduct`; claims point to policies with `relatesToPolicy`/`claimPolicy`. The ontology also defines the required domain and range for `ownsPolicy`, `submitsClaim`, `coversRisk`, `hasCoverage`, and `generatesPremium`, plus identifier, status, date, and loss properties used by the local validation graph.

`countryCode` is shared by customers and policies through the `CountryCodedEntity`
superclass, so its domain does not incorrectly require an instance to be both.

The ontology describes meaning and relationships; it does not replace analytical product contracts, authorization, or SQL compilation. The SKOS product taxonomy supplies preferred and alternative labels, while SHACL supplies instance-data constraints.

This is intentionally an ontology/runtime boundary: graph assets answer what
entities and relationships mean, while certified products and platform
compilers answer how an approved analytical query runs. See
[ADR-003](decisions/ADR-003-ontology-runtime-boundary.md).
