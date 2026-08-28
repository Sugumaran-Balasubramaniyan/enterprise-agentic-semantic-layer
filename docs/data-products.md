# Certified data products

GlobalSure publishes four versioned contracts under `data_products/`. Each
contract names its owner, platform/location boundary, row grain, service level,
quality checks, classification, PII fields, lineage, exposed concepts, schema,
and certification state. The contracts are the selection boundary for agents;
an agent cannot choose an uncertified physical table by guessing a name.

| Product | Grain | Primary concepts | Quality state |
| --- | --- | --- | --- |
| `Customer360` | one row per customer | Customer, Country | CERTIFIED |
| `PolicyMaster` | one row per policy | Policy, ActivePolicy, InsuranceProduct | CERTIFIED |
| `ClaimsAnalytics` | one row per claim | Claim, QualifyingClaim, IncurredLoss | CERTIFIED |
| `PremiumAnalytics` | one row per policy and premium period | Premium, Policy | CERTIFIED |

The curated demo files in `data/curated/` implement these schemas locally.
`data/raw/` also contains deliberately invalid records (blank IDs, negative
amounts, future dates, and an unknown status) for later quality-check demos.
The generated values are fictional and use EUR for a reproducible local run;
they are not production or AXA data.

## Governed metrics

`semantic/metrics/metrics.yaml` defines `ClaimCount`, `TotalIncurredLoss`,
`AverageClaimAmount`, `ActivePolicyCount`, and `ClaimsRatio`, including the
expression, unit, source product, and rule. `QualifyingClaim` in
`semantic/rules/claims.yaml` excludes `CANCELLED` and `DUPLICATE` claims while
keeping those records observable for audit and quality analysis.

Generate the same dataset for any explicit as-of date with:

```bash
python -c "from datetime import date; from pathlib import Path; from semantic_layer.data_generation import generate_demo_data; generate_demo_data(Path('data'), date(2026, 8, 28))"
```

The repository script uses the same fixed date: `python data/generate_demo_data.py`.
