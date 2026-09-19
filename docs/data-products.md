# Certified data products

SAP SE publishes four versioned contracts under `data_products/`. Each
contract names its owner, platform/location boundary, row grain, service level,
quality checks, classification, PII fields, lineage, exposed concepts, schema,
and certification state. The contracts are the selection boundary for agents;
an agent cannot choose an uncertified physical table by guessing a name.

| Product | Grain | Primary concepts | Quality state |
| --- | --- | --- | --- |
| `BusinessPartners` | one row per partner | BusinessPartner, CompanyCode | CERTIFIED |
| `SalesOrders` | one row per sales order | SalesOrder, ActiveSalesOrder, Product | CERTIFIED |
| `ACDOCAFinancials` | one row per journal entry item | FinancialPosting, QualifyingPosting, FinancialLoss | CERTIFIED |
| `BillingAnalytics` | one row per order and billing period | BillingDocument, SalesOrder | CERTIFIED |

The curated demo files in `data/curated/` implement these schemas locally.
`data/raw/` also contains deliberately invalid records (blank IDs, negative
amounts, future dates, and an unknown status) for quality-check verification.
The generated values are synthetic demonstration data and use EUR for a reproducible local run.

## Governed metrics

`semantic/metrics/metrics.yaml` defines `PostingCount`, `TotalDebitLossEur`,
`AveragePostingAmountEur`, `ActiveSalesOrderCount`, and `CostRevenueRatio`, including the
expression, unit, source product, and rule. `QualifyingPosting` in
`semantic/rules/financial_postings.yaml` excludes `REVERSED` and `DUPLICATE` journal entries while
keeping those records observable for audit and quality analysis.

`CostRevenueRatio` is a safe multi-product metric: ACDOCAFinancials loss and
BillingAnalytics billed revenue are each filtered and aggregated independently, then
joined on `partner_id`, `country`, and canonical `product` before division.
The caller's as-of date and reporting window apply independently to
`posting_date` and `billing_date`; the contract explicitly forbids joining raw
posting and billing rows, which would multiply measures for partners with more
than one posting or billing period. A zero revenue denominator produces a null
ratio rather than an unbounded value.

This repository validates that definition during discovery only. No local
simulated role is authorized for the complete product set, so authorization
returns `PRODUCT_DENIED`, and the DuckDB compiler does not implement the ratio.
Production enablement requires an aggregate-only workload policy and executable
compiler, platform-control, and evidence tests; the checked-in definition is not
an execution claim.

Generate the same dataset for any explicit as-of date with the project
environment active:

```bash
.venv/bin/python -c "from datetime import date; from pathlib import Path; from semantic_layer.data_generation import generate_demo_data; generate_demo_data(Path('data'), date(2026, 8, 28))"
```

The repository script uses the same fixed date: `.venv/bin/python data/generate_demo_data.py`.

## Certification boundary

An agent may select only contracts whose certification status is `CERTIFIED`.
Product grain prevents accidental join multiplication, while classification
and PII declarations feed authorization. Static upstream lineage in each YAML
contract is combined with dynamic query provenance after execution. These
contracts describe the local reference implementation; they are not claims
that a production catalog or cloud platform is connected.

See [governance](governance.md) and [ADR-008](decisions/ADR-008-certified-data-products.md).
