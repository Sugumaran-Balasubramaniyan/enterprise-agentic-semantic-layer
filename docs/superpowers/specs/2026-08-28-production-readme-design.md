# Production README Handbook Design

## Classification

This is an architectural documentation task. The README is the repository's
primary operating contract for engineers, architects, security reviewers, and
operators; it must explain not only the demo path but also the boundaries and
controls required to evolve the reference implementation into production.

## Goal

Replace the superseded introductory README with a detailed, accurate,
production-oriented repository handbook while preserving the concise local
demo path and avoiding claims unsupported by the checked-in implementation.
The repository must not contain legacy guided-demo content; demonstrations
must be framed as normal operational examples and technical documentation.

## Design

The README will be organized as a navigable handbook with four user journeys:

1. **Understand:** problem statement, principles, architecture, semantic
   contract, federation model, and business use case.
2. **Run:** prerequisites, clean-install quickstart, data generation, API,
   CLI, request/response examples, expected outputs, configuration, and
   troubleshooting.
3. **Operate and secure:** local versus production contracts, deployment
   topology, identity, authorization, privacy, provenance retention, signing,
   observability, failure modes, incident actions, backups, and upgrades.
4. **Change and extend:** repository map, asset ownership, contribution and
   review workflow, semantic versioning, CI gates, release/deprecation policy,
   onboarding a country/domain, and production platform extensions.

Deep domain explanations remain in the existing `docs/` pages and are linked
from the README. The README will contain enough context to stand alone while
using those documents as authoritative detail rather than duplicating them.

## Accuracy rules

- Every API endpoint listed in the README must match the FastAPI OpenAPI
  surface. Unsupported detail/relationship routes will be removed unless
  implemented as part of this change.
- Every command must be executable from a clean checkout with the documented
  Python environment.
- Test and evaluation counts must include a verification date and identify
  the authoritative evidence file.
- Implemented, simulated, and production-target capabilities must be clearly
  separated.
- Demo request roles are explicitly simulated; production identity and policy
  enforcement must be described as gateway/platform responsibilities.
- No secrets, real customer data, or paid cloud credentials are required.

## Required sections

The final README must include:

- audience and repository status;
- table of contents and role-based start paths;
- business problem and semantic-layer principles;
- architecture diagrams and request lifecycle;
- vocabulary, taxonomy, ontology, SHACL, knowledge graph, metrics, products,
  mappings, quality, lineage, security, provenance, and federation;
- supported prerequisites/platform matrix and clean-install quickstart;
- deterministic data lifecycle, schemas/grains/join keys, and fixture policy;
- complete implemented API and CLI examples, including success and fail-closed
  responses;
- configuration matrix and signing-key behavior;
- deployment topology and development/staging/production separation;
- operational runbook, observability boundary, incident/failure matrix,
  backup/restore, retention, and upgrade compatibility;
- CI coverage and local-only verification boundaries;
- semantic asset contribution, ownership, review, release, deprecation, and
  migration policy;
- pilot implementation plan, 30/60/90-day milestones, scale-out stages, and
  measurable promotion/exit criteria;
- production extension patterns for Databricks, Snowflake, Fabric, MCP, LLM
  enhancement, KMS/HSM, and policy services;
- traceability matrix from requested capability to implementation, tests, and
  production analogue;
- a concise end-to-end demonstration path framed as a normal system walkthrough,
  with no legacy guided-demo language or scripted guide;
- GitHub publication integrity: balanced Markdown fences, GitHub-compatible
  Mermaid syntax, resolved links, and regression checks for stale references;
- license, synthetic-data policy, limitations, and support/escalation notes.

## Verification

Documentation changes will be verified with:

- documentation contract tests;
- link and command checks;
- API route comparison against generated OpenAPI;
- Ruff and full pytest suite;
- semantic validation, golden evaluation, and demo execution;
- `git diff --check` and secret-pattern review.

The README change is complete only when the worktree is clean and the updated
commit is pushed to the active GitHub branch.
