# The Jargon Buster: Glossary of Key Terms

> A comprehensive, plain-English reference guide translating enterprise, semantic web, and computer science terms into everyday language.

When reading technical codebases, specialized acronyms can feel like an impenetrable wall. Keep this glossary open in a tab to quickly decode any unfamiliar term.

---

## 1. Enterprise & Business Systems

### ERP (Enterprise Resource Planning)
- **Plain English**: A massive, integrated software suite that manages every aspect of running a global corporation—accounting, purchasing, inventory, manufacturing, human resources, and sales.
- **Everyday Analogy**: The central nervous system of a giant enterprise. If you buy a pair of running shoes online, the ERP system tells the distribution center to package them, tells the factory to manufacture a replacement pair, tells the accountant to log the revenue, and generates the shipping manifest.
- **In This Repo**: Represented by synthetic SAP-inspired tables such as `sales_orders.csv` and `acdoca_financials.csv`.

### ACDOCA (Universal Journal Entry)
- **Plain English**: In modern SAP financial software, ACDOCA is the central database table that records every single financial transaction across the entire global organization in one place.
- **Everyday Analogy**: A massive, tamper-evident master ledger book kept in a bank vault where every deposit, expense, and currency transfer is stamped on a single row.
- **In This Repo**: [`data/curated/acdoca_financials.csv`](../../data/curated/acdoca_financials.csv) and [`data_products/acdoca_financials.yaml`](../../data_products/acdoca_financials.yaml).

### Semantic Layer
- **Plain English**: An intelligent translation bridge that sits between complex, messy database tables and human business users or AI agents. It maps technical column names to unified business concepts.
- **Everyday Analogy**: The bilingual concierge desk at an international airport. Instead of requiring tourists to read airport engineering blueprints, the concierge translates "Where is my flight?" into "Gate B14, Boarding at 2:15 PM".
- **In This Repo**: The entire architecture defined in [`docs/semantic-layer.md`](../semantic-layer.md) and implemented in [`src/semantic_layer/`](../../src/semantic_layer/).

### Data Product
- **Plain English**: A curated, high-quality dataset that is treated like a commercial product: it has an explicit owner, clear documentation, automated quality checks, and an unambiguous usage contract.
- **Everyday Analogy**: A packaged, inspected, and certified organic apple at a grocery store with an ingredients and nutrition label, rather than raw apples dumped loose from an unverified orchard.
- **In This Repo**: Defined in YAML under [`data_products/`](../../data_products/).

### Data Lineage
- **Plain English**: The complete historical record of where a specific piece of data came from, what transformations were applied to it, and which reports or calculations use it.
- **Everyday Analogy**: A food traceability barcode on a steak that tells you the exact farm, pasture, packaging date, and distribution route.
- **In This Repo**: Managed by [`src/semantic_layer/lineage/service.py`](../../src/semantic_layer/lineage/service.py).

---

## 2. Knowledge Graphs & The Semantic Web

### Knowledge Graph (KG)
- **Plain English**: A database that stores information as an interconnected network of real-world things (entities) and the meaningful relationships connecting them, rather than as flat tables of rows and columns.
- **Everyday Analogy**: A detective's investigation corkboard with photos of suspects, locations, and vehicles pinned down and connected by labelled pieces of red yarn.
- **In This Repo**: Loaded by [`src/semantic_layer/kg/loader.py`](../../src/semantic_layer/kg/loader.py) from files like [`semantic/ontology/sap_support.ttl`](../../semantic/ontology/sap_support.ttl).

### RDF (Resource Description Framework)
- **Plain English**: The international World Wide Web Consortium (W3C) standard format for representing knowledge graphs. It breaks all human knowledge down into atomic statements called "triples".
- **Everyday Analogy**: Constructing complex stories entirely out of simple 3-word sentences: Subject, Verb, Object.
- **In This Repo**: Used across all `.ttl` files in the `semantic/` directory.

### Triple (Subject - Predicate - Object)
- **Plain English**: The fundamental unit of graph data. A subject is connected to an object via a relationship called a predicate.
- **Example**: `(:SAPNote123, :resolvesAlert, :TIME_OUT)`.
- **Everyday Analogy**: `(Alice, owns, Dog)`.

### Turtle (`.ttl`)
- **Plain English**: A clean, human-readable text format for writing RDF graph triples without the visual clutter of XML.
- **In This Repo**: All files ending in `.ttl` in the `semantic/` folder.

### URI / IRI (Internationalized Resource Identifier)
- **Plain English**: A global, web-safe unique address that names a concept or relationship so that computers around the world never confuse two different things that share the same human name.
- **Everyday Analogy**: A person's full passport number with country code, ensuring two people named "John Smith" are never mixed up.
- **In This Repo**: Prefixes like `cifsup:`, `ciferp:`, and `cifppms:` expand to unique namespace URIs.

### Ontology (OWL / RDFS)
- **Plain English**: A formal blueprint or set of rules that defines what categories of things can exist in a domain, what attributes they can have, and how they are allowed to relate to one another.
- **Everyday Analogy**: The zoning and architectural building codes of a city specifying that a "Residential House" may have "Bedrooms", but a "Highway" cannot have "Bedrooms".
- **In This Repo**: Declared in [`semantic/ontology/sap_support.ttl`](../../semantic/ontology/sap_support.ttl) and [`semantic/ontology/sap_erp.ttl`](../../semantic/ontology/sap_erp.ttl).

### Taxonomy (SKOS)
- **Plain English**: A hierarchical categorization tree that organizes concepts into broader and narrower categories, along with preferred and alternative synonyms.
- **Everyday Analogy**: Biological classification: Animal -> Mammal -> Carnivore -> Feline -> Lion.
- **In This Repo**: Declared in [`semantic/taxonomy/sap_products.ttl`](../../semantic/taxonomy/sap_products.ttl).

### SHACL (Shapes Constraint Language)
- **Plain English**: A schema validation language for graphs. It acts like an automated checklist or unit test that checks whether graph data obeys mandatory rules.
- **Everyday Analogy**: A building inspector with a checklist making sure every apartment unit has at least one window, a smoke detector, and an emergency exit before signing off.
- **In This Repo**: Declared in [`semantic/shapes/sap_support_shapes.ttl`](../../semantic/shapes/sap_support_shapes.ttl).

### SPARQL
- **Plain English**: The standard query language used to search, filter, and extract data from RDF knowledge graphs (the equivalent of SQL for graphs).
- **Everyday Analogy**: A magnifying glass form where you leave blanks on the detective board: "Find me every [Note] that [resolvesAlert] [TIME_OUT]".
- **In This Repo**: Generated by [`src/semantic_layer/reasoning/text_to_sparql.py`](../../src/semantic_layer/reasoning/text_to_sparql.py).

---

## 3. Computer Science & Artificial Intelligence

### Agentic AI & AQR (Autonomous Query Reasoning)
- **Plain English**: An intelligent software system that does not just generate text blindly, but instead autonomously plans a multi-step query, checks the results, reflects on errors, and safely repairs mistakes.
- **Everyday Analogy**: A diligent research assistant who plans their library search, goes to the stacks, verifies the book contents, checks cross-references, and corrects catalog typos.
- **In This Repo**: Implemented in [`src/semantic_layer/reasoning/reflective_agent.py`](../../src/semantic_layer/reasoning/reflective_agent.py).

### Deterministic vs. Probabilistic
- **Deterministic**: A system that will ALWAYS produce the exact same output for a given input every single time, with mathematical certainty (100% predictable, zero hallucination).
- **Probabilistic (Stochastic)**: A system that guesses the next word or token based on statistical probabilities (like ChatGPT), which might generate different or fabricated answers on different runs.
- **In This Repo**: The entire baseline in this repository is 100% deterministic!

### Fail-Closed Abstention
- **Plain English**: A security and safety policy where the system explicitly says "I do not have enough information to answer this" rather than guessing or making up a fake answer.
- **Everyday Analogy**: An honest doctor who says "We need to run a blood test before I prescribe this" instead of guessing an unverified medication.
- **In This Repo**: Handled by `ReasonCode` and `Status.UNSUPPORTED` in [`src/semantic_layer/reasoning/schema_linker.py`](../../src/semantic_layer/reasoning/schema_linker.py).

### FSM (Finite State Machine)
- **Plain English**: A computational model that can only be in one of a finite number of states at any given moment, transitioning between them based on explicit rules.
- **Everyday Analogy**: A turnstile at a subway station: it is either `Locked` or `Unlocked`. Inserting a coin transitions it from `Locked` to `Unlocked`. Pushing the bar transitions it back to `Locked`.
- **In This Repo**: The repair loop in [`src/semantic_layer/reasoning/reflective_agent.py`](../../src/semantic_layer/reasoning/reflective_agent.py).

### BFS (Breadth-First Search)
- **Plain English**: An algorithm for exploring a graph level-by-level, checking all immediate neighbors first before moving to neighbors-of-neighbors.
- **Everyday Analogy**: Ripples expanding outward from a pebble dropped into a calm pond.
- **In This Repo**: Used for bounded prerequisite traversal in [`src/semantic_layer/reasoning/query_planner.py`](../../src/semantic_layer/reasoning/query_planner.py).

### DFS (Depth-First Search)
- **Plain English**: An algorithm for exploring a graph by following a single branch as deeply as possible until hitting a dead end or cycle before backtracking.
- **Everyday Analogy**: Exploring a maze by always following the right-hand wall until you find an exit or return to the entrance.
- **In This Repo**: Used for cycle detection in [`src/semantic_layer/reasoning/query_planner.py`](../../src/semantic_layer/reasoning/query_planner.py).

### Cryptographic Hash (SHA-256)
- **Plain English**: A mathematical function that converts any piece of data (whether a single word or a 1,000-page book) into a unique 64-character digital fingerprint. If even one character changes, the fingerprint changes completely.
- **Everyday Analogy**: Tamper-evident security tape on an evidence bag: if the bag is opened or altered, the tape visibly breaks.
- **In This Repo**: Used for input manifests and audit trails in [`src/semantic_layer/research/benchmark_runner.py`](../../src/semantic_layer/research/benchmark_runner.py).

### OLAP (Online Analytical Processing)
- **Plain English**: A database designed specifically for fast calculations and aggregations across millions of rows (calculating total quarterly profits) rather than updating individual transactions.
- **Everyday Analogy**: A financial accountant scanning down only the "Total Price" column of 10,000 receipts in a few seconds.
- **In This Repo**: Handled by DuckDB via [`src/semantic_layer/compiler/duckdb.py`](../../src/semantic_layer/compiler/duckdb.py).
