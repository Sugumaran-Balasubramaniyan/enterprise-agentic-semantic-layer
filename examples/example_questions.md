# Governed example questions

The deterministic agent accepts business questions, not SQL. It resolves only
registered terms, emits a typed logical plan, and fails closed for unsupported
intent, invalid scope, uncertified products, or denied access.

## Primary claims investigation

> Find French motor-insurance customers with at least three qualifying claims
> in the last 12 months and total incurred loss above EUR 20,000.

Run it locally with:

```bash
.venv/bin/python -m semantic_layer.demo
```

Use the `ClaimsAnalystFR` role. The deterministic result contains `FR_001` and
`FR_002`; cancelled and duplicate claims are excluded by the governed
`QualifyingClaim` rule.

## Other governed discovery patterns

- `How many French motor insurance customers have active policies this year?`
- `Show the claims ratio for French motor insurance customers in the current year.`

Only the primary claims plan is compiled and executed by the local DuckDB
adapter. Active-policy questions are discovery-only. `ClaimsRatio` is also
discovery-only and intentionally returns `PRODUCT_DENIED` during authorization:
no local simulated role can access its complete `ClaimsAnalytics` and
`PremiumAnalytics` product set. A production implementation needs a reviewed
aggregate-only workload role, a compiler, platform-native controls, and
execution/evidence tests. Cloud mappings remain declared extension artifacts
and are not executed by this repository.
