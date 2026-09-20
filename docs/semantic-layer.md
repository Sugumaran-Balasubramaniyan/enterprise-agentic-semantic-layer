# Semantic asset contract

The semantic layer keeps business vocabulary in versioned YAML and relationship
meaning in OWL/RDFS. The YAML document carries a semantic version, neutral
namespace, and repository metadata; each typed concept includes a definition,
synonyms, classification, sensitivity, relationships or allowed values, and
examples. The loader retains these fields and enforces semantic-version syntax.

## Asset responsibilities

- `semantic/vocabulary/sap_erp.yaml` is the repository glossary and metadata contract.
- `semantic/taxonomy/sap_products.ttl` organizes labels with SKOS; its resources use `cifskos`.
- `semantic/ontology/sap_erp.ttl` defines synthetic OWL classes and property domains/ranges under `ciferp`.
- `semantic/ontology/sap_support.ttl` and `semantic/ontology/sap_ppms.ttl` define synthetic support and lifecycle terms under `cifsup` and `cifppms`.
- `semantic/shapes/sap_erp_shapes.ttl` validates ERP instances; postings require an ID, date, status, order, and non-negative amount.
- Metrics, rules, contracts, and illustrative mappings connect semantic meaning to the local DuckDB path.

Use the local validation command:

```bash
make PYTHON=.venv/bin/python validate-semantic
```

It loads the semantic assets and validates the valid and deliberately
incomplete sample graphs. A failing fixture is expected evidence of the shape
contract; it is not a production conformance claim.

## Contract boundaries

RDF graph assets answer what entities and relationships mean. Repository-
maintained synthetic contracts describe grain and local quality. Typed plans,
policy checks, and the DuckDB compiler answer how an approved local analytical
query runs. The deterministic core is intentionally bounded and can be
extended only with new governed patterns and tests.

No LLM, vector index, or external retrieval service is part of this contract.
Schema linking, Text-to-SPARQL, repair learning, and hybrid retrieval are
**Proposed future work** and must preserve validation, policy, compiler, and
provenance boundaries.

See [architecture](architecture.md), [governance](governance.md), and
[ADR-004](decisions/ADR-004-typed-query-plans.md).
