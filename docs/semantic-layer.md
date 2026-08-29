# Semantic asset contract

GlobalSure keeps the canonical business vocabulary in versioned YAML and the relationship vocabulary in OWL/RDFS. The YAML document itself carries a required semantic version, namespace, and owner; `load_vocabulary` retains those fields alongside the list of typed concepts and enforces semantic-version syntax at both levels. Every vocabulary record includes an identifier, definition, owner, semantic version, synonyms, classification, sensitivity, relationships or allowed values, and examples. This makes a concept reviewable by people and loadable by typed Python services.

The three semantic layers have distinct responsibilities:

- `semantic/vocabulary/insurance.yaml` is the governed glossary and metadata contract.
- `semantic/taxonomy/insurance-products.ttl` organizes product labels with SKOS. Local motor values such as `MTR`, `CAR`, and `MotorInsurance` map to `MotorInsurance`; `HOME` and `HomeInsurance` map to the governed `HomeInsurance` concept.
- `semantic/ontology/insurance.ttl` defines OWL classes and property domain/range constraints.
- `semantic/shapes/insurance-shapes.ttl` validates insurance instances. Claims require an ID, date, status, policy, and non-negative incurred loss; policies require an ID, product, and status.

Use `make PYTHON=.venv/bin/python validate-semantic` to load all 14 canonical
concepts and validate both sample graphs. The valid graph conforms; the
deliberately incomplete graph fails with an expected SHACL report and does not
make the command fail.

## Contract boundaries

The semantic layer combines glossary meaning, taxonomy labels, ontology
relationships, graph instances, product contracts, mappings, metrics, rules,
authorization, and execution controls. RAG may retrieve supporting text, but
it cannot substitute for these machine-readable contracts. The deterministic
core is intentionally bounded and can be extended only with new governed
patterns and tests.

See [architecture](architecture.md), [governance](governance.md), and
[ADR-004](decisions/ADR-004-typed-query-plans.md).
