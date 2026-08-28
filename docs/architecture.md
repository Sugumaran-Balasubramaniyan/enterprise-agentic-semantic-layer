# Architecture

GlobalSure Insurance Group's semantic layer is a small control plane between
business intent and platform execution. Git is the reviewable source of truth
for vocabulary, taxonomy, ontology, SHACL shapes, metric rules, products, and
local mappings. Python services load those assets into a typed registry; a
request is resolved, authorized, planned, compiled, executed, quality-checked,
and recorded with provenance.

```mermaid
flowchart TB
    U[User or application] --> A[Deterministic agent workflow]
    A --> R[Semantic registry]
    R --> V[Vocabulary and taxonomy]
    R --> O[Ontology and SHACL]
    R --> P[Certified product contracts]
    R --> M[Metrics rules and mappings]
    A --> G[Governance and quality]
    A --> Q[Typed semantic query plan]
    Q --> C[Platform compiler]
    C --> D[DuckDB local adapter]
    C -. extension artifact .-> X[Databricks / Snowflake / Fabric]
    D --> E[Rows and provenance envelope]
```

## Request flow

The public API accepts business language plus a caller context. It never
accepts a SQL string and the agent has no arbitrary-SQL tool. The planner
emits `SemanticQueryPlan`, a Pydantic contract containing canonical concepts,
relationships, filters, metric predicates, a time context, certified product
IDs, caller context, and a target platform.

```mermaid
flowchart LR
    Q[Business question] --> R[Resolve terms and synonyms]
    R --> S[Select relationships and certified products]
    S --> Z{Authorize role, country, purpose}
    Z -- deny --> N[Fail closed with reason code]
    Z -- allow --> P[Build typed logical plan]
    P --> K[Compile approved mapping and metric template]
    K --> X[Execute locally in DuckDB]
    X --> V[Validate quality and result integrity]
    V --> T[Persist signed provenance]
    T --> O[Answer with plan, SQL, rows and evidence]
```

## What each semantic asset does

Glossary YAML defines human meaning, ownership, synonyms, sensitivity, and
version. SKOS taxonomy organizes product labels. OWL/RDFS describes typed
classes and relationships, while SHACL validates instance graphs. A knowledge
graph contains compact example facts; it is not the analytical execution
store. Product contracts describe grain, SLA, classification, quality and
lineage. Mappings normalize local fields and values to the Group vocabulary.
Metrics and rules define governed calculations such as `QualifyingClaim` and
`ClaimsRatio`.

RAG can retrieve policy documents or explain a definition, but retrieval does
not make a join, metric, authorization decision, or physical field mapping
safe. The semantic layer supplies those executable contracts. An optional LLM
may improve language understanding or explanation; deterministic resolution,
validation, authorization, compilation, and provenance remain authoritative.

## Federation and ownership

Group owns canonical concepts, the ontology, interoperability rules, semantic
versioning, and CI. France, the UK, and Germany own local products, source
schemas, mappings, extensions, and regulatory policies. Each local product
must map into the canonical vocabulary before a Group metric can use it.

```mermaid
flowchart TB
    G[Group semantic contract 1.0.0]
    G --> FR[France / Databricks mapping]
    G --> UK[United Kingdom / Snowflake mapping]
    G --> DE[Germany / Fabric mapping]
    FR --> N[Canonical normalized values]
    UK --> N
    DE --> N
    N --> P[Certified products and governed metrics]
```

The mapping boundary is explicit and platform-independent. For example,
`MTR`, `CAR`, and `MotorInsurance` normalize to
`insurance:MotorInsurance`; an unknown value fails closed. Cloud identifiers
and SQL examples are documentation/interface artifacts only. The repository
does not claim a live Databricks, Snowflake, or Fabric execution.

## Mapping and execution boundary

```mermaid
flowchart LR
    LP[Local physical schema] -->|reviewed YAML mapping| CP[Canonical field and value]
    CP -->|typed plan| T[Trusted compiler template]
    T --> DB[DuckDB CSV views]
    T -. dialect example, unexecuted .-> DC[Cloud dialect SQL]
    DB --> A[Quality-bound answer]
    DC -. requires credentials and adapter .-> CE[Production execution plane]
```

DuckDB is the fully implemented adapter and runs against deterministic
synthetic CSVs. A production adapter would delegate authentication,
row-level security, network policy, and audit to the native platform; the
semantic compiler must not bypass those controls.

## Cross-cutting controls

Authorization combines role, country, purpose, and classification. Quality
checks cover IDs, non-negative loss, dates, statuses, countries, and mapped
products. Unsafe or degraded products block detail queries. Static lineage
connects source to product to metric; dynamic provenance records the question,
plan, mappings, physical files, versions, authorization, quality result,
timestamps, and digests for the particular answer.

See [agent architecture](agent-architecture.md),
[governance](governance.md), and [federated semantics](federated-semantics.md)
for operational details.
