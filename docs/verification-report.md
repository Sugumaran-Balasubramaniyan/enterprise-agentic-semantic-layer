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
| scoped credential-pattern scan | Exit status 0; eight source-code identifier matches were reviewed below. |

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
excluding lock files, returned eight matches:

- `src/semantic_layer/query_planner/service.py:62`, `:64`, `:65`, and `:66`
  are parser regular-expression constants (`_NUMBER_TOKEN`,
  `_COUNTRY_TOKEN`, `_PRODUCT_TOKEN`, and `_SUBJECT_TOKEN`).
- `src/semantic_layer/query_planner/service.py:130` is a local parser variable
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

## Final-review release blockers (2026-08-28 UTC)

The final-review blockers were closed in one focused change:

- The bounded planner grammar now rejects residual status filters, mixed intent
  clauses, multiple or unsupported country scopes, and customer-specific
  restrictions. The same rejection is exercised through the query-plan API and
  agent workflow, before final plan construction.
- `DataProduct.quality.status` is a validated `CERTIFIED`/`DEGRADED`/`UNSAFE`
  contract. Only `CERTIFIED` products can be selected, authorized, compiled, or
  executed; denial messages include the observed status.
- Golden deterministic evidence is required and typed. Governed primary and
  threshold variants execute the local agent path and verify quality,
  authorization, provenance, and metric evidence. Discovery-only cases remain
  a separate evaluation dimension.

Fresh verification after these changes:

| Command | Observed result |
| --- | --- |
| `.venv/bin/ruff check .` | `All checks passed!` |
| `.venv/bin/pytest -q` | `149 passed, 1 warning in 18.94s`; the warning is the existing third-party TestClient deprecation. |
| `.venv/bin/python -m semantic_layer.evaluation` | `Golden evaluation: 31/31 cases passed` with `discovery_only=10/10`; executable variants were run rather than metadata-only checked. |

## Important final-review findings (2026-08-28 UTC)

The final-review follow-up is implemented in one focused change:

- The local HTTP API and deterministic evaluation now label requester-supplied
  roles as simulated caller context, explicitly not authentication. Governance
  enforces role-specific maximum product classifications and denies unknown or
  over-classified products with `CLASSIFICATION_DENIED`.
- Primary provenance now records the complete plan/rule/metric semantic
  closure, including Customer, Policy, MotorInsurance, Claim,
  QualifyingClaim, IncurredLoss, ClaimCount, and TotalIncurredLoss. It also
  separates the physical sources actually queried from all sources validated
  by the quality gate.
- HOME remains an intentionally unregistered extension: normalization and
  quality validation reject it as governed, and the generated curated fixture
  contains only registered products so its quality gate remains PASS.
- Cloud SQL files and the cloud rendering helper are explicitly marked as
  unexecuted, incomplete, and not equivalent to the governed plan. The valid
  RDF fixture now includes Customer-to-Policy and Policy-to-Claim links plus
  country context.

Fresh verification for this follow-up:

| Command | Observed result |
| --- | --- |
| `make PYTHON=./.venv/bin/python lint` | `All checks passed!` |
| `make PYTHON=./.venv/bin/python validate-semantic` | Valid graph conforms; invalid graph fails as expected. |
| `make PYTHON=./.venv/bin/python check-yaml` | `YAML: 11 files parsed` |
| `make PYTHON=./.venv/bin/python check-mappings-quality` | `24 passed` |
| `make PYTHON=./.venv/bin/python check-compiler` | `4 passed` |
| `make PYTHON=./.venv/bin/python check-golden` | `13 passed` |
| `make PYTHON=./.venv/bin/python evaluate` | `Golden evaluation: 31/31 cases passed`; `discovery_only=10/10`. |
| `make PYTHON=./.venv/bin/python test` | `158 passed, 1 warning`; the warning is the existing third-party TestClient deprecation. |

## Final-readiness follow-up (2026-08-28 UTC)

The final-readiness follow-up adds bounded controls without changing the
documented product or execution claims:

- The planner accepts only complete, anchored forms of the three reviewed
  question grammars. Residual exclusions, named-customer clauses, and claim
  date predicates are rejected during discovery, so the agent and request API
  cannot execute them.
- Explicit golden answers use the same evidence-checked execution helper as
  governed variants. Authorization, PASS quality, compiled metric IDs, signed
  provenance, and result/plan/query/metric evidence are required; rows alone
  cannot satisfy the contract. Discovery-only denominators include every case
  declared with that mode, including failed cases.
- `countryCode` uses a `CountryCodedEntity` superclass shared by Customer and
  Policy, avoiding OWL intersection semantics for multiple domain
  declarations. A combined ontology, instance, and SHACL regression covers
  both country-coded entity types.
- The Makefile defaults to a managed `.venv` when present and `python3` on a
  fresh checkout, while preserving `PYTHON=` overrides. The example question
  runner no longer requires a bare `python` command.

Fresh full-matrix verification for this follow-up:

| Command | Observed result |
| --- | --- |
| `make test` | `175 passed, 1 warning`; the warning is the existing third-party TestClient deprecation. |
| `make lint` | `All checks passed!` |
| `make validate-semantic` | Valid graph conforms; invalid graph fails as expected. |
| `make check-yaml` | `YAML: 11 files parsed` |
| `make check-mappings-quality` | `24 passed` |
| `make check-golden` | `13 passed` |
| `make check-compiler` | `4 passed` |
| `make evaluate` | `Golden evaluation: 31/31 cases passed`; `discovery_only=10/10`. |
| `make demo` | Completed the governed DuckDB demonstration and returned FR_001/FR_002. |

## Final integrity evidence follow-up (2026-08-28 UTC)

The final integrity review is closed with focused regression coverage:

- Golden executable cases now receive and execute against the exact supplied
  `SemanticRegistry`; mutating the supplied `QualifyingClaim` rule therefore
  changes the evaluation outcome instead of being hidden by a disk reload.
- `authorization_outcome` is included in the signed execution payload and is
  checked against the authorization capability by the adapter and provenance
  store. A tampered outcome is rejected before durable provenance is written.
- Curated quality validation rejects blank or literal-null values for every
  required join identifier: customer, policy, claim, and premium identifiers
  wherever those joins apply.
- The governed example command uses `.venv/bin/python`, matching the managed
  project environment.

Fresh matrix after these changes:

| Command | Observed result |
| --- | --- |
| `make PYTHON=.venv/bin/python lint` | `All checks passed!` |
| `make PYTHON=.venv/bin/python test` | `195 passed, 1 warning`; the warning is the existing third-party TestClient deprecation. |
| `make PYTHON=.venv/bin/python validate-semantic` | Valid graph conforms; invalid graph fails as expected; exit status 0. |
| `make PYTHON=.venv/bin/python check-yaml` | `YAML: 11 files parsed` |
| `make PYTHON=.venv/bin/python check-mappings-quality` | `42 passed` |
| `make PYTHON=.venv/bin/python check-golden` | `13 passed` |
| `make PYTHON=.venv/bin/python check-compiler` | `4 passed` |
| `make PYTHON=.venv/bin/python evaluate` | `Golden evaluation: 31/31 cases passed`; `discovery_only=10/10`. |
| `make PYTHON=.venv/bin/python demo` | Completed the governed DuckDB demonstration and returned FR_001/FR_002. |
| `git diff --check` | Exit status 0 with no whitespace errors reported. |
| scoped credential-pattern scan | Exit status 0; eight benign source-code identifier matches, with no credential values. |

## GitHub publication integrity validation (2026-08-29 UTC)

This documentation follow-up rechecked the public handbook, its navigation,
and every Mermaid block in `README.md` and `docs/`. The documentation contract
now verifies balanced Markdown fences, a closing fence for each Mermaid block,
the absence of literal `\\n` labels and non-self-closing `<br>` labels, local
relative-link targets and anchors, and obsolete audience-specific wording.
The current 13 Mermaid blocks use GitHub-compatible syntax; the two
multi-line flowchart labels use explicit `<br/>` markup.

| Command | Observed result |
| --- | --- |
| `.venv/bin/python -m pytest tests/unit/test_documentation_contract.py -q` | `17 passed` |
| Markdown/Mermaid static scan | All tracked Markdown fences were balanced; all README/docs Mermaid blocks closed; no literal `\\n` or `<br>` labels were found. |
| local-link and stale-reference scan | Documentation-contract link and stale-reference checks passed; no prohibited legacy audience-specific references were found in published Markdown. |
| `make PYTHON=.venv/bin/python lint` | `All checks passed!` |
| `make PYTHON=.venv/bin/python validate-semantic` | Valid graph conformed and the invalid graph failed as expected. |
| `make PYTHON=.venv/bin/python check-yaml` | `YAML: 11 files parsed` |
| `make PYTHON=.venv/bin/python check-mappings-quality` | `42 passed` |
| `make PYTHON=.venv/bin/python check-golden` | `13 passed` |
| `make PYTHON=.venv/bin/python check-compiler` | `4 passed` |
| `make PYTHON=.venv/bin/python evaluate` | `Golden evaluation: 31/31 cases passed`; `discovery_only=10/10`. |
| `make PYTHON=.venv/bin/python demo` | Completed the governed DuckDB demonstration and returned `FR_001` and `FR_002`. |
| `make PYTHON=.venv/bin/python test` | `205 passed, 1 warning`; the warning is the existing third-party TestClient deprecation. |
| `git diff --check` | Exit status 0 with no whitespace errors. |

No local Mermaid CLI was installed: `npx --no-install @mermaid-js/mermaid-cli
--version` correctly declined to download a missing package. The static
contract and direct source scan therefore provide the rendering evidence for
this environment; GitHub remains the final renderer for Markdown previews.

## Documentation fence validator follow-up (2026-08-29 UTC)

This focused follow-up closes the Task 8 review finding against
`tests/unit/test_documentation_contract.py` by replacing the prior
regex-only fence checks with a stateful Markdown fence parser. The
documentation contract now accepts both backtick and tilde fences of length
three or greater, requires the closing fence to use the same character with a
length at least as long as the opener, and recognizes Mermaid blocks even
when they use four-or-more backticks. Two regression tests cover tilde-fenced
blocks and four-backtick Mermaid blocks. The stronger validator also exposed
one unmatched tracked fence sequence in
`.superpowers/sdd/2026-08-28-federated-semantic-layer/task-8-report.md`,
which was repaired without changing README or published docs content.

| Command | Observed result |
| --- | --- |
| `./.venv/bin/python -m pytest tests/unit/test_documentation_contract.py -q -k 'tilde or mismatched_or_short or four_backtick or mermaid_fences_are_balanced or mermaid_fences_close'` | `5 passed, 15 deselected in 0.61s` |
| `./.venv/bin/python -m pytest tests/unit/test_documentation_contract.py -q` | `20 passed in 2.20s` |
| `./.venv/bin/ruff check .` | `All checks passed!` |
| `./.venv/bin/pytest -q` | `208 passed, 1 warning in 19.81s`; the warning is the existing third-party Starlette/httpx deprecation. |
| `git diff --check` | Exit status 0 with no whitespace errors. |

## README verification-count re-review follow-up (2026-08-29 UTC)

This re-review closes the remaining documentation consistency gap after the
fence-validator change. `docs/verification-report.md` already recorded the
latest local suite result as `208 passed`, but `README.md` and its
documentation-contract assertion still referenced the prior `205 passed`
snapshot. The README verification summary and capability matrix now point to
the latest `208 passed` evidence while leaving older counts in this report as
date-labeled historical records only.

| Command | Observed result |
| --- | --- |
| `./.venv/bin/python -m pytest tests/unit/test_documentation_contract.py -q -k latest_evidence` | `1 passed, 19 deselected in 0.62s` |
| `./.venv/bin/python -m pytest tests/unit/test_documentation_contract.py -q` | `20 passed in 2.22s` |
| `./.venv/bin/ruff check .` | `All checks passed!` |
| `./.venv/bin/pytest -q` | `208 passed, 1 warning in 19.66s`; the warning is the existing third-party Starlette/httpx deprecation. |
| `git diff --check` | Exit status 0 with no whitespace errors. |
