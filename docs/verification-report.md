# Final verification report

Evidence recorded on 2026-08-28 UTC from the local linked worktree on branch
`feat/semantic-layer-implementation`. All Python commands used the project
virtual environment through `make PYTHON=.venv/bin/python`.

## Commands and results

The required local matrix completed before this report was added:

| Command | Observed result |
| --- | --- |
| `make PYTHON=.venv/bin/python lint` | `ruff check .` reported `All checks passed!`. |
| `make PYTHON=.venv/bin/python test` | Pytest collected 138 tests; `138 passed, 1 warning in 9.16s`. The warning is FastAPI/Starlette's third-party `TestClient` deprecation notice. |
| `make PYTHON=.venv/bin/python validate-semantic` | Loaded 13 vocabulary concepts; the valid graph conformed and the deliberately invalid graph did not conform, as expected. |
| `make PYTHON=.venv/bin/python evaluate` | `Golden evaluation: 31/31 cases passed` with every reported dimension at `31/31`. |
| `make PYTHON=.venv/bin/python demo` | Completed the governed DuckDB claims demonstration described below. |
| `git diff --check` | Exit status 0 with no whitespace errors reported. |
| scoped credential-pattern scan | Exit status 0; four source-code identifier matches were reviewed below. |

Supplemental CI-aligned checks also completed: YAML parsing reported 11 files;
mapping/quality checks had 21 passing tests; golden tests had 11 passing tests;
compiler checks had 3 passing tests; and the documentation contract had 7
passing tests.

## Main end-to-end claims demonstration

The local demo accepted the primary French motor-insurance question, resolved
the governed concepts, selected `Customer360`, `PolicyMaster`, and
`ClaimsAnalytics`, built a typed DuckDB plan, and returned two rows after a
quality result of `PASS` with score 100:

| customer_id | country | claim_count | total_incurred_loss_eur |
| --- | --- | ---: | ---: |
| FR_001 | FR | 3 | 24000.0 |
| FR_002 | FR | 3 | 25000.0 |

The emitted plan used the `ClaimsAnalystFR` caller context, the
`DatabricksFranceMapping` semantic mapping, parameterized DuckDB SQL, and a
runtime provenance envelope. Runtime query IDs, timestamps, and digests were
not copied into this report because they vary per execution.

## Semantic validation and SHACL

`validate-semantic` loaded 13 vocabulary concepts. The valid RDF fixture
conformed. The invalid fixture produced the expected SHACL failures: a missing
claim date and a negative incurred loss. This confirms both the conforming
path and that the invalid test fixture is rejected.

## Golden evaluation

The fresh local semantic evaluation completed all 31 governed cases:
`resolution=31/31`, `relationships=31/31`, `products=31/31`,
`metrics=31/31`, `authorization=31/31`, and
`deterministic_answers=31/31`. This is a deterministic local regression
signal over the checked-in synthetic fixtures, not a benchmark or a claim
about production accuracy.

## Security and secret scan

The requested case-insensitive scan for credential-like assignment patterns,
excluding lock files, returned four matches:

- `src/semantic_layer/query_planner/service.py:99` is a local parser variable
  named `token`.
- `src/semantic_layer/models.py:17`, `:22`, and `:27` are regular-expression
  constants used to recognize SQL-shaped input.

These are code identifiers and input-validation patterns, not credential
values. The scan did not report an API key, password, or secret assignment.
No credential values are recorded in this report.

## Documentation review

The focused documentation contract test completed with 7 passing tests.
An additional read-only Markdown check found 22 local link targets, all
present; it found 10 Mermaid diagram fences and balanced fenced code blocks.
The documentation review therefore covered the checked documentation
contracts, local relative links, and diagram/fence structure. It did not make
network requests to validate external URLs.

## Known limitations

- DuckDB is the only executed adapter. Databricks, Snowflake, and Microsoft
  Fabric adapters and SQL examples are unexecuted simulations that still need
  platform-native credential, security, performance, and integration testing.
- Deterministic business-language parsing is intentionally bounded to governed
  vocabulary, synonym, and pattern coverage; unsupported phrasing must be
  expanded through reviewed assets and tests.
- The local data set is synthetic, deterministic, and not evidence of
  production data quality, scale, latency, accuracy, or security.
- The documentation check verified local paths and Markdown fence structure;
  it did not validate external-link availability.

## Publication handoff

Read-only GitHub checks found the existing `origin` remote at
`https://github.com/Sugumaran-Balasubramaniyan/enterprise-agentic-semantic-layer.git`.
The GitHub CLI authenticated successfully for the account
`Sugumaran-Balasubramaniyan` with HTTPS Git operations and repository/workflow
scopes. No remote, repository, or publication state was changed by this task.

An authorized maintainer can offer publication of this branch without creating
or overwriting a repository by first reviewing the branch and then running:

```bash
git push -u origin feat/semantic-layer-implementation
```
