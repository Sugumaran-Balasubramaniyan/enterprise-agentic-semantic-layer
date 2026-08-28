# GlobalSure insurance ontology

The canonical ontology lives in [`semantic/ontology/insurance.ttl`](../semantic/ontology/insurance.ttl). It is a small OWL/RDFS vocabulary for the concepts that must interoperate across the French, UK, and German local entities.

`MotorInsurance` is an `InsuranceProduct`. A `Customer` owns a `Policy` and submits a `Claim`; a `Claim` relates to its `Policy`. A `Policy` has a product, covers a risk, has coverage, and generates premium. The ontology also defines domain and range declarations for those relationships, plus identifier, status, date, and loss properties used by the local validation graph. `policyProduct` and `claimPolicy` remain explicit subproperty aliases for compatibility; the canonical sample graph and SHACL constraints use `hasProduct` and `relatesToPolicy`.

`countryCode` is shared by customers and policies through the `CountryCodedEntity`
superclass, so its domain does not incorrectly require an instance to be both.

The ontology describes meaning and relationships; it does not replace analytical product contracts, authorization, or SQL compilation. The SKOS product taxonomy supplies preferred and alternative labels, while SHACL supplies instance-data constraints.

This is intentionally an ontology/runtime boundary: graph assets answer what
entities and relationships mean, while certified products and platform
compilers answer how an approved analytical query runs. See
[ADR-003](decisions/ADR-003-ontology-runtime-boundary.md).
