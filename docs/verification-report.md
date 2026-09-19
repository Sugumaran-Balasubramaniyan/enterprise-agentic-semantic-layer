# Final verification report

Evidence recorded on 2026-08-29 UTC from the local repository on branch
`main`. All Python commands used the project virtual environment through
`make PYTHON=.venv/bin/python`.

## Commands and results

The required verification matrix completed across both pillars:

| Command | Observed result |
| --- | --- |
| `make PYTHON=.venv/bin/python lint` | `ruff check .` reported `All checks passed!`. |
| `make PYTHON=.venv/bin/python test` | Pytest collected 218 tests; `218 passed, 2 warnings in 22.13s`. The warnings are third-party FastAPI/Starlette deprecation notices. |
| `make PYTHON=.venv/bin/python validate-semantic` | Loaded 14 vocabulary concepts; the valid RDF graph conformed and the deliberately invalid graph did not conform, as expected. |
| `make PYTHON=.venv/bin/python kg-validate` | W3C SHACL graph validation of the SAP Support Knowledge Graph (`sap_support_graph.ttl`) passed (4/4 tests). |
| `make PYTHON=.venv/bin/python research-benchmark` | Executed 40 golden multi-hop enterprise benchmark queries against `SAP-KGBench`: 100.0% Execution Accuracy (40/40), 0.0% Hallucination. |
| `make PYTHON=.venv/bin/python evaluate` | `Golden evaluation: 31/31 cases passed` with every reported dimension at `31/31` and `discovery_only=10/10`. |
| `make PYTHON=.venv/bin/python demo` | Completed the governed DuckDB SAP S/4HANA ERP financial postings demonstration described below. |
| `git diff --check` | Exit status 0 with no whitespace errors reported. |
| Scoped credential-pattern scan | Exit status 0; no secret values or credential assignments detected. |

Supplemental CI-aligned checks also completed: YAML parsing reported 12 files;
mapping/quality checks had 42 passing tests; golden tests had 13 passing tests;
compiler checks had 4 passing tests; and the documentation contract had 20
passing tests.

## Main end-to-end SAP S/4HANA ERP demonstration

The local demo accepted the primary French automotive ERP question:
> "Find French automotive business partners with at least three qualifying financial postings in the last 12 months and total debit loss above EUR 20,000."

It resolved the governed concepts, selected `BusinessPartners`, `SalesOrders`, and
`ACDOCAFinancials`, built a typed DuckDB plan, and returned two rows after a
quality result of `PASS` with score 100:

| partner_id | country | posting_count | total_debit_loss_eur |
| --- | --- | ---: | ---: |
| FR_001 | FR | 3 | 24000.0 |
| FR_002 | FR | 3 | 25000.0 |

The emitted plan used the `FinancialControllerFR` caller context, the
`DatabricksFranceMapping` semantic mapping, parameterized DuckDB SQL, and a
runtime provenance envelope. Runtime query IDs, timestamps, and digests vary
per execution.

## SAP Support Knowledge Graph and AQR reasoning

The flagship research pillar was validated through:
1. **Ontological Conformance:** Loading SAP PPMS (`sap_ppms.ttl`) and SAP Support
   (`sap_support.ttl`) ontologies alongside 491 triples in `sap_support_graph.ttl`.
2. **SHACL Validation:** Closed-world shape constraints in `sap_support_shapes.ttl`
   confirmed that malformed notes and alerts are rejected.
3. **Autonomous Query Reasoning (`AQR-Reflect`):** Validated property path expansion,
   schema linking, and query relaxation across 40 complex enterprise queries.

## Golden evaluation

The fresh local semantic evaluation completed all 31 governed cases:
`resolution=31/31`, `relationships=31/31`, `products=31/31`,
`metrics=31/31`, `authorization=31/31`, and
`deterministic_answers=31/31` with `discovery_only=10/10`. This is a deterministic local regression
signal over the checked-in synthetic fixtures.

## Security and secret scan

A case-insensitive scan for credential-like assignment patterns,
excluding lock files, returned only input-validation regex constants and parser tokens:
- `src/semantic_layer/query_planner/service.py`: regular-expression constants (`_NUMBER_TOKEN`,
  `_COUNTRY_TOKEN`, `_PRODUCT_TOKEN`, `_SUBJECT_TOKEN`, `_POSTINGS_TOKEN`, `_LOSS_TOKEN`).
- `src/semantic_layer/models.py`: regular-expression constants used to recognize SQL-shaped input.

No API keys, passwords, or secret credentials were found.

## Documentation review

The documentation contract test suite passed with 20/20 tests:
- All Markdown fences are balanced.
- All Mermaid diagram blocks close properly and contain GitHub-safe labels.
- All relative Markdown links resolve to real files on disk.
- No obsolete audience-specific or legacy terminology remains in published documentation.

## Known limitations

- DuckDB is the only executed relational adapter. Databricks, Snowflake, and Microsoft
  Fabric adapters and SQL examples are unexecuted simulations that require
  platform-native credentials and cloud infrastructure.
- Deterministic business-language parsing is intentionally bounded to governed
  vocabulary, synonym, and pattern coverage; unsupported phrasing fails closed.
- The local dataset is synthetic and deterministic.
