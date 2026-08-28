# Generated SQL examples

The DuckDB compiler is the only executable compiler in this repository. It
emits a fixed, parameterized template only after a typed plan, certified data
products, approved mappings, and authorization controls have been applied.

Databricks, Snowflake, and Microsoft Fabric representations are explicitly
incomplete SQL fragments, not equivalent generated plans. Their adapters fail
closed until their own credentials, configuration, mapping-derived compilation,
and platform-native security controls are deliberately supplied.

The local primary query uses the `QualifyingClaim` rule's governed included
statuses and its fixed demo as-of date of `2026-08-28`; cancelled and duplicate
claims are therefore never counted in the result.
