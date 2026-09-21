# Repository-maintained synthetic data contracts

The files under `data_products/` are repository-maintained synthetic contracts.
They describe grain, quality checks, classification, PII fields, lineage,
exposed concepts, and an internal selection status for the local demonstration.
They are not published by an external organization and are not external
certifications.

| Product | Grain | Primary concepts | Local status |
| --- | --- | --- | --- |
| `BusinessPartners` | one row per partner | BusinessPartner, CompanyCode | `CERTIFIED` synthetic contract status |
| `SalesOrders` | one row per sales order | SalesOrder, ActiveSalesOrder, Product | `CERTIFIED` synthetic contract status |
| `ACDOCAFinancials` | one row per journal entry item | FinancialPosting, QualifyingPosting, FinancialLoss | `CERTIFIED` synthetic contract status |
| `BillingAnalytics` | one row per order and billing period | BillingDocument, SalesOrder | `CERTIFIED` synthetic contract status |

The `CERTIFIED` value is an internal contract gate used by local selection and
tests. It does not mean a platform, catalog, regulator, or external authority
has certified the data. The generated values are synthetic demonstration data
for a reproducible local run.

## Local fixtures and metrics

Curated files in `data/curated/` implement the local schemas. Files in
`data/raw/` contain deliberate invalid records such as blank IDs, negative
amounts, future dates, and unknown statuses for quality-check verification.

`semantic/metrics/metrics.yaml` defines `PostingCount`, `TotalDebitLossEur`,
`AveragePostingAmountEur`, `ActiveSalesOrderCount`, and `CostRevenueRatio`.
`semantic/rules/financial_postings.yaml` excludes reversed and duplicate
postings from the qualifying-posting rule while retaining those rows for local
quality analysis.

`CostRevenueRatio` is a discovery-only contract in this checkout. Its two
inputs are filtered and aggregated independently before joining on stable keys,
so raw posting and billing rows are not multiplied. The local simulated roles
do not authorize a complete ratio execution path; no production enablement or
cloud execution is implied.

Regenerate the deterministic local data with:

```bash
.venv/bin/python data/generate_demo_data.py
```

Or choose the fixed as-of date explicitly:

```bash
.venv/bin/python -c "from datetime import date; from pathlib import Path; from semantic_layer.data_generation import generate_demo_data; generate_demo_data(Path('data'), date(2026, 8, 28))"
```

## Selection boundary

The resolver and planner select only contracts whose local status is
`CERTIFIED`. Grain, quality, classification, and PII declarations feed the
local policy check. Static lineage is combined with dynamic provenance after a
local execution. An agent cannot choose a physical table by guessing a name.

This boundary is a local design decision and a future integration seam, not a
claim that an external catalog or cloud platform is connected. See
[governance](governance.md) and
[ADR-008](decisions/ADR-008-certified-data-products.md).

Cloud execution and external catalog integration are **Not implemented**;
future adapters would require their own evidence and controls.
