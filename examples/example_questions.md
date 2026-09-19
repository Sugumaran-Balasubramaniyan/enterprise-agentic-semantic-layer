# Governed example questions

The deterministic agent accepts business questions, not SQL. It resolves only
registered terms, emits a typed logical plan, and fails closed for unsupported
intent, invalid scope, uncertified products, or denied access.

## Primary financial posting audit

> Find French automotive business partners with at least three qualifying financial postings
> in the last 12 months and total debit loss above EUR 20,000.

Run it locally with:

```bash
.venv/bin/python -m semantic_layer.demo
```

Use the `ClaimsAnalystFR` role. The deterministic result contains `FR_001` and
`FR_002`; reversed and duplicate postings are excluded by the governed
`QualifyingPosting` rule.

## Other governed discovery patterns

- `How many French automotive business partners have active sales orders this year?`
- `Show the cost-revenue ratio for French automotive business partners in the current year.`

Only the primary financial posting plan is compiled and executed by the local DuckDB
adapter. Active-sales-order questions are discovery-only. `CostRevenueRatio` is also
discovery-only and intentionally returns `PRODUCT_DENIED` during authorization:
no local simulated role can access its complete `ACDOCAFinancials` and
`BillingAnalytics` product set. A production implementation needs a reviewed
aggregate-only workload role, a compiler, platform-native controls, and
execution/evidence tests. Cloud mappings remain declared extension artifacts
and are not executed by this repository.
