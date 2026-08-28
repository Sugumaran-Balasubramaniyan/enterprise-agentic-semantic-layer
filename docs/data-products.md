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

`ClaimsRatio` is a safe multi-product metric: ClaimsAnalytics loss and
PremiumAnalytics premium are each filtered and aggregated independently, then
joined on `customer_id`, `country`, and canonical `product` before division.
The caller's as-of date and reporting window apply independently to
`claim_date` and `premium_date`; the contract explicitly forbids joining raw
claim and premium rows, which would multiply measures for customers with more
than one claim or premium period. A zero premium denominator produces a null
ratio rather than an unbounded value.

Generate the same dataset for any explicit as-of date with:

```bash
python -c "from datetime import date; from pathlib import Path; from semantic_layer.data_generation import generate_demo_data; generate_demo_data(Path('data'), date(2026, 8, 28))"
```

The repository script uses the same fixed date: `python data/generate_demo_data.py`.

## Certification boundary

An agent may select only contracts whose certification status is `CERTIFIED`.
Product grain prevents accidental join multiplication, while classification
and PII declarations feed authorization. Static upstream lineage in each YAML
contract is combined with dynamic query provenance after execution. These
contracts describe the local reference implementation; they are not claims
that a production catalog or cloud platform is connected.

See [governance](governance.md) and [ADR-008](decisions/ADR-008-certified-data-products.md).
