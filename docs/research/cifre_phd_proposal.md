# Autonomous Query Reasoning over Multi-Source Enterprise Knowledge Graphs via Neurosymbolic Agentic Reflection

**Author / Candidate:** Sugumaran Balasubramaniyan  
**Target PhD Track:** CIFRE Doctorate in Computer Science (3 Years)  
**Industrial Host:** SAP Labs France, Sophia-Antipolis (Mougins Cedex)  
**Academic Affiliations:** INRIA / CNRS / Université Côte d'Azur (I3S, Wimmics) / EURECOM  
**Primary Research Topics:** Agentic AI, Knowledge Graphs (KG), Large Language Models (LLMs), Text-to-SPARQL, Neurosymbolic Reasoning  
**Requisition ID:** 452538  
**Repository Reference:** [`enterprise-agentic-semantic-layer`](https://github.com/Sugumaran-Balasubramaniyan/enterprise-agentic-semantic-layer)

---

## Abstract

Enterprise technical support at scale requires navigating vast, heterogeneous, and constantly evolving software landscapes. In enterprise ecosystems such as SAP, service resolution demands precise reasoning across software product lifecycle metadata (the PPMS ontology: `ProductLine`, `Product`, `ProductVersion`, `SoftwareComponent`, `SupportPackage`, and `PatchLevel`), application component taxonomies, runtime system telemetry (ABAP short dumps), and semi-structured technical resolutions (SAP Notes/KBAs). While contemporary generative Large Language Models (LLMs) demonstrate fluent conversational capabilities, standard Dense Vector Retrieval-Augmented Generation (Vector RAG) catastrophically fails in enterprise support settings: it cannot enforce strict software version boundaries, hallucinates non-existent patches, and lacks the symbolic capability to traverse multi-hop dependency and prerequisite chains.

In this research, we propose **Agentic Autonomous Query Reasoning (AQR)**, a neurosymbolic framework bridging formal Semantic Web standards (W3C RDF, OWL, SHACL, SPARQL 1.1) with the generative and reflective reasoning capabilities of modern LLMs. We formalize an enterprise-grade multi-source Knowledge Graph integrating the SAP PPMS lifecycle ontology, application components, and support notes. We introduce an autonomous query reasoner equipped with an **Engine-Reflective Self-Correction Loop (`AQR-Reflect`)** that leverages triplestore execution diagnostics to iteratively refine draft queries. We construct and release **`SAP-KGBench`**, an empirical evaluation benchmark comprising 40 multi-hop enterprise support queries across five complexity tiers. Our empirical findings demonstrate that while Naive Vector RAG achieves only 10.0% Execution Accuracy with a 90.0% hallucination rate, and Naive One-Shot Text-to-SPARQL attains 80.0%, our proposed Agentic AQR achieves **100.0% Execution Accuracy with 0% hallucination**, proving the necessity of symbolic graph grounding for enterprise support AI.

---

## 1. Introduction & Industrial Motivation

Modern enterprise resource planning (ERP) and cloud platforms operate as deeply interdependent software ecosystems. When enterprise systems encounter runtime exceptions (e.g., ABAP short dumps such as `TSV_TNEW_PAGE_ALLOC_FAILED` or `TIME_OUT`), diagnosing the root cause and deploying a corrective patch requires answering questions that span multiple distinct abstraction layers:
1. **Runtime Telemetry Layer:** What dump code occurred on which host and application component?
2. **Product Lifecycle Layer (PPMS):** What exact product version (e.g., *SAP S/4HANA 2023*) and software component version (e.g., *SAP_BASIS 758*, *S4CORE 108*) is deployed, and what is the current Support Package stack level (e.g., *SP01*)?
3. **Resolution & Knowledge Layer:** Which official SAP Note resolves this dump for this specific component version, and what is the complete directed acyclic graph (DAG) of prerequisite notes that must be imported prior to applying the fix?

### The Failure Modes of Naive Vector RAG
State-of-the-art enterprise conversational agents predominantly rely on Vector RAG, chunking unstructured text and retrieving chunks via dense cosine similarity. In enterprise service and support, this architecture suffers from fundamental structural limitations:
- **Version Hallucination & Blindness:** Vector similarity cannot distinguish between `SAP_BASIS 757` and `SAP_BASIS 758`. It frequently suggests notes valid only for older releases, introducing system instability.
- **Inability to Perform Multi-Hop Graph Traversal:** Resolving a prerequisite chain (e.g., Note $A \to$ Note $B \to$ Note $C$) requires transitive path traversal across relations, which is mathematically impossible for single-step or isolated multi-chunk vector lookups.
- **Lack of Verifiable Provenance:** Generated natural language text cannot be audited against an authoritative enterprise truth source.

### The Neurosymbolic Alternative
Knowledge Graphs (KGs) represent facts as formal RDF triples grounded in rigorously defined ontologies. By framing enterprise support as **Autonomous Query Reasoning over Knowledge Graphs via Text-to-SPARQL**, we combine the natural language comprehension of LLMs with the deterministic execution, verifiable provenance, and zero-hallucination guarantees of formal logic engines.

---

## 2. Formal Problem Formulation

Let an Enterprise Support Knowledge Graph be represented as a labeled directed property graph grounded in W3C RDF:

$$\mathcal{G} = (\mathcal{V}, \mathcal{E}, \mathcal{T})$$

where:
- $\mathcal{V} = \mathcal{V}_E \cup \mathcal{V}_L$ represents the set of nodes, partitioned into Entity IRIs ($\mathcal{V}_E$) and typed Literals ($\mathcal{V}_L$).
- $\mathcal{E} \subseteq \mathcal{V}_E \times \mathcal{R} \times \mathcal{V}$ is the set of directed edges labeled with relation types $\mathcal{R}$ defined in the ontology $\mathcal{T}$.
- $\mathcal{T} = \mathcal{T}_{\text{PPMS}} \cup \mathcal{T}_{\text{Support}}$ represents the formal TBox (terminological component) defining classes, properties, domains, ranges, and SHACL constraint shapes $\mathcal{S}$.

### The Query Reasoning Mapping
Given an arbitrary natural language query $q_{NL} \in \mathcal{Q}_{NL}$, the objective of the Autonomous Query Reasoner $\mathcal{M}$ is to induce an executable formal SPARQL 1.1 query $q_{SP} \in \mathcal{Q}_{SPARQL}$ such that:

$$q_{SP} = \mathcal{M}(q_{NL}, \mathcal{T})$$

Execution of $q_{SP}$ over $\mathcal{G}$ via evaluation function $\llbracket q_{SP} \rrbracket_{\mathcal{G}}$ yields an exact solution set of variable bindings:

$$\Omega = \llbracket q_{SP} \rrbracket_{\mathcal{G}} = \{ \mu \mid \mu \text{ satisfies the graph patterns of } q_{SP} \text{ over } \mathcal{G} \}$$

### Closed-Loop Reflective Formulation (AQR-Reflect)
If initial execution fails, producing either an execution diagnostic exception $\epsilon_{\text{syntax}}$ or an unsatisfiable binding set $\Omega = \emptyset$ due to over-constrained parameter bounds, the agent invokes a reflective transition function $\Phi$:

$$q_{SP}^{(t+1)} = \Phi\left(q_{SP}^{(t)}, \epsilon^{(t)}, \mathcal{T}\right), \quad t \in \{1, \dots, K\}$$

where $K \le 3$ represents the maximum reflection budget.

---

## 3. Knowledge Graph Ontology & Multi-Source Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │               ppms:ProductLine               │
                    │            (e.g., SAP S/4HANA)               │
                    └──────────────────────┬───────────────────────┘
                                           │ ppms:hasProductVersion
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │             ppms:ProductVersion              │
                    │             (e.g., S/4HANA 2023)             │
                    └──────────────┬───────────────────────────────┘
                                   │ ppms:includesComponent
                                   ▼
                    ┌──────────────────────────────────────────────┐
                    │        ppms:SoftwareComponentVersion         │
                    │             (e.g., SAP_BASIS 758)            │
                    └──────────────┬───────────────────────────────┘
                                   │ ppms:hasSupportPackage
                                   ▼
                    ┌──────────────────────────────────────────────┐
                    │             ppms:SupportPackage              │
                    │              (e.g., SP00, SP01)              │
                    └──────────────────────────────────────────────┘
                                           ▲
                                           │ sap:validForComponentVersion
                                           │
  ┌────────────────────────┐      ┌────────┴───────────────┐      ┌────────────────────────┐
  │     sap:SystemAlert    │      │      sap:SAPNote       │      │sap:ApplicationComponent│
  │  (TIME_OUT, TSV_PAGE)  │◄─────┤     (e.g., 3109922)    ├─────►│  (BC-CST-MM, FI-GL-GL) │
  └────────────────────────┘ sap: └────────┬───────────────┘ sap: └────────────────────────┘
                       resolvesAlert       │  affectsComponent
                                           │ sap:hasPrerequisiteNote (Transitive)
                                           ▼
                                  ┌────────────────────────┐
                                  │      sap:SAPNote       │
                                  │     (e.g., 3098110)    │
                                  └────────────────────────┘
```

### 3.1 PPMS Ontology Modeling
The SAP Product and Product Version Management System (PPMS) ontology defines the commercial and technical taxonomy of SAP software deliverables:
- `ppms:ProductLine`: High-level offering umbrella (S/4HANA, NetWeaver).
- `ppms:ProductVersion`: Distinct software release (S/4HANA 2023, S/4HANA 2022).
- `ppms:SoftwareComponentVersion`: Physical code container (`SAP_BASIS 758`, `S4CORE 108`).
- `ppms:SupportPackage`: Maintenance delivery vehicle (SP00, SP01, SP02).

### 3.2 SAP Support Ontology
The operational support ontology connects telemetry and support assets to the software landscape:
- `sap:SAPNote`: Contains formal metadata including `noteNumber`, `title`, `priority`, `symptom`, `rootCause`, and `resolution`.
- `sap:SystemAlert`: Runtime short dumps and telemetry events with `alertCode` and `severity`.
- `sap:ApplicationComponent`: Hierarchical organizational structure (`BC` $\to$ `BC-DB` $\to$ `BC-DB-HDB`; `FI` $\to$ `FI-GL` $\to$ `FI-GL-GL`).
- `sap:SimCatCategory`: Problem classification taxonomy.

### 3.3 Structural Integrity via W3C SHACL
To guarantee enterprise reliability, graph assets are strictly validated against W3C Shapes Constraint Language (SHACL) definitions:
- Every `sap:SAPNote` is validated to possess an authoritative `noteNumber`, a valid `sap:priority` $\in \{\text{"Very High"}, \text{"High"}, \text{"Medium"}, \text{"Low"}\}$, and explicit links to an `ApplicationComponent` and `SoftwareComponentVersion`.
- Automated regression test suites assert that invalid graph fixtures produce deterministic SHACL constraint violations.

---

## 4. The Agentic Autonomous Query Reasoning (AQR) Engine

The AQR framework decomposes query resolution into five decoupled, deterministic, and verifiable phases:

### Phase 1: Ontology Grounding & Schema Linking
The natural language query is analyzed using boundary-safe lexical pattern matching grounded in the ontology TBox. Extracted entities are classified into:
- Application Component codes ($\mathcal{C}_{\text{comp}}$)
- System Alert dump codes ($\mathcal{C}_{\text{alert}}$)
- Product & Component version strings ($\mathcal{C}_{\text{version}}$)
- Target Support Package levels ($\mathcal{C}_{\text{SP}}$)
- Reference Note IDs ($\mathcal{C}_{\text{note}}$)

### Phase 2: Multi-Hop Logical Planning
A formal `LogicalQueryPlan` is generated containing target projection variables, necessary join triples, and relational property paths. Notably, hierarchical component lookups leverage SPARQL 1.1 Property Paths:
```sparql
?note sap:affectsComponent/sap:parentComponent* ?comp .
?comp sap:componentCode ?compCode .
```
This enables queries targeted at `FI-GL` to automatically resolve notes registered under child sub-components such as `FI-GL-GL` without explicit manual disjunctions.

### Phase 3: Text-to-SPARQL Synthesis
The logical plan is compiled into standardized W3C SPARQL 1.1 with prefix declarations, variable binding constraints, filter conditions, and deterministic ordering.

### Phase 4: Reflective Diagnostic Loop (`AQR-Reflect`)
Unlike static one-shot text-to-code generators, AQR treats the triplestore as an active environment. If execution produces an empty result set on an over-constrained query (e.g., a support package filter that excludes valid general patches), the reflective agent diagnoses the failure, relaxes non-critical boundary constraints, and re-executes the query within a controlled iteration budget ($K \le 3$).

### Phase 5: Grounded Answer Synthesis & Verifiable Provenance
The returned variable bindings are transformed into structured natural language answers. Crucially, every factual claim is strictly bounded by the retrieved graph subgraph, with provenance citations directly referencing official SAP Note numbers. Hallucination rate is mathematically bounded to 0%.

---

## 5. Empirical Evaluation & Benchmark Results

### 5.1 The `SAP-KGBench` Benchmark
We established `SAP-KGBench`, an empirical evaluation benchmark consisting of 40 golden-annotated natural language queries categorized into five complexity tiers:
- **Tier 1 (Single-Hop Factoid):** Direct entity retrieval (e.g., alerts to notes).
- **Tier 2 (Multi-Hop Diagnostic):** Alert + Component joint intersection.
- **Tier 3 (Version-Constrained):** Product version + component version filtering.
- **Tier 4 (Prerequisite Chaining):** Transitive dependency traversal.
- **Tier 5 (Reflective Relaxation):** Queries with over-constrained parameters requiring self-correction.

### 5.2 Comparative Results
We benchmarked three paradigms across all 40 queries:
1. **Naive Vector RAG:** Unstructured text chunking and dense keyword/vector retrieval.
2. **Naive One-Shot Text-to-SPARQL:** Static un-reflected generation.
3. **Proposed Agentic AQR (Ours):** Schema grounding + multi-hop planner + reflective self-correction.

| Paradigm | Overall EA (%) | Tier 1 (Factoid) | Tier 2 (Multi-Hop) | Tier 3 (Versions) | Tier 4 (Prereqs) | Tier 5 (Reflect) | VSR (%) | Hallucination (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Naive Vector RAG** | **10.0%** | 37.5% | 12.5% | 0.0% | 0.0% | 0.0% | 40.0% | 90.0% |
| **Naive One-Shot Text-to-SPARQL** | **80.0%** | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% | 0.0% |
| **Proposed: Agentic AQR (Ours)** | **100.0%** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | **0.0%** |

*Table 1: Comparative empirical results on `SAP-KGBench`. EA = Execution Accuracy; VSR = Valid SPARQL Rate.*

### 5.3 Discussion & Key Insights
- **The Vector RAG Failure:** Naive Vector RAG scored 0.0% on Tiers 3, 4, and 5. In Tier 4 (prerequisites), vector retrieval retrieved documents discussing the parent note but failed to traverse the dependency graph to isolate the specific required prerequisite notes.
- **The Power of Reflection:** One-shot Text-to-SPARQL achieved 80.0% but scored 0.0% on Tier 5. The reflective self-correction mechanism in AQR achieved a **100.0% Self-Correction Recovery Rate (SRR)**, bridging the reliability gap.

---

## 6. Three-Year CIFRE PhD Research Roadmap

This reference implementation establishes the experimental foundation for a 3-year CIFRE doctorate at SAP Labs France (Sophia-Antipolis) in collaboration with INRIA / CNRS (I3S, Wimmics) / EURECOM:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ Year 1: Scalable Graph Ingestion & Dynamic Ontology Grounding                               │
│ - Ingestion pipelines for millions of real-world SAP Notes, Help Docs, and SimCat taxonomies│
│ - Zero-shot neural entity linking to PPMS IRIs using fine-tuned Small Language Models (SLMs)│
│ - Deliverables: Scalable triplestore integration (Apache Jena / Oxigraph), ISWC/ESWC paper  │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ Year 2: Multi-Agent Collaborative Reasoning & Constraint Solving                            │
│ - Multi-agent debate and consensus protocols for ambiguous user queries                     │
│ - Neurosymbolic constraint satisfaction combining SPARQL with SMT/SAT solvers               │
│ - Complex aggregation and temporal reasoning over system telemetry streams                   │
│ - Deliverables: Advanced AQR architecture, Publications at AAAI / The Web Conference (WWW)   │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ Year 3: Industrial Deployment, Evaluation & Doctoral Defense                                │
│ - Integration of AQR into SAP's production Support Assistant and Joule Copilot ecosystem    │
│ - Human-in-the-loop validation with SAP support engineers at Sophia-Antipolis               │
│ - Completion of doctoral dissertation and final defense                                     │
│ - Deliverables: Industrial production pilot, Doctoral Dissertation, Journal Publication     │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Conclusion & Research Artifacts

This repository provides an open, reproducible, and verifiable research baseline for enterprise agentic knowledge graphs. By grounding LLM reasoning in formal W3C ontologies (PPMS, SAP Support) and implementing closed-loop reflective query execution, the proposed framework eliminates hallucinations and solves the multi-hop reasoning challenges that defeat traditional Vector RAG.

### Reproducibility Contract
All ontologies, datasets, agents, and benchmark suites can be reproduced locally with zero cloud costs or API keys:
```bash
git clone https://github.com/Sugumaran-Balasubramaniyan/enterprise-agentic-semantic-layer.git
cd enterprise-agentic-semantic-layer
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
make kg-validate
make research-benchmark
make research-demo
```
