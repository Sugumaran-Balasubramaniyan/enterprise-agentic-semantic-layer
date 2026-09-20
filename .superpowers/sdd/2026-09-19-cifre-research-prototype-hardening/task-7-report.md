# Task 7 report: CIFRE benchmark migration

## Status

Complete. The historical corpus remains unchanged, its archive is byte-identical,
normalized v1/v2 corpora are generated, and the signed 40-record migration
manifest validates under the closed schema. Commit SHA is recorded below.

## Files

Created or generated only the Task 7 artifacts:

- `scripts/migrate_benchmark_v1.py`
- `tests/research/benchmark_dataset_legacy.yaml`
- `tests/research/benchmark_dataset_v1.yaml`
- `tests/research/benchmark_dataset_v2.yaml`
- `tests/research/benchmark_migration_manifest_v1.yaml`
- `tests/research/test_dataset_migration.py`
- this report

`tests/research/benchmark_dataset.yaml` was not modified.

## Legacy identity

`tests/research/benchmark_dataset.yaml` and
`tests/research/benchmark_dataset_legacy.yaml` both have SHA-256
`04bb3d5f7c0516c9eca400ea22026df7096281fa0df148b38cbfe81ce930307f` and
`cmp` reports byte identity.

Generated artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| `benchmark_dataset_v1.yaml` | `25d5636944e447efde665d63b04c1e1d4791f05ae196a24969f0378b056b1f65` |
| `benchmark_dataset_v2.yaml` | `40c3cf58b29de5d99a34f5640b982e79c42a217d8e6f73d8b7534a3eddd60168` |
| `benchmark_migration_manifest_v1.yaml` | `c163328baeea44ba1bb5c9a2081bb79435e77d6b37ea89d81e11567a9fc5f968` |

## TDD and verification

The initial focused run was red during collection because the migration module
did not yet exist (`ModuleNotFoundError: No module named 'scripts'`). After the
implementation, the focused run was green:

```text
PYTHONPATH=src /tmp/cifre-task7-venv/bin/pytest tests/research/test_dataset_migration.py -q
4 passed
```

The documented offline generation command was run, followed by a second run;
all three generated artifact hashes were unchanged (`sha256sum -c`: three
`OK` results). Dependency-complete research verification used an isolated
`/tmp/cifre-task7-venv` and did not mutate the shared `.venv`:

```text
PYTHONPATH=src /tmp/cifre-task7-venv/bin/pytest tests/research -q
64 passed
ruff check scripts/migrate_benchmark_v1.py tests/research/test_dataset_migration.py
All checks passed!
```

## Manifest decisions

The manifest contains the exact Q01-Q40 order and closed top-level, change,
record, derivation, and review fields. Historical `expected_notes` values are
retained only as `gold_before`; normalized records use sorted unique seven-digit
`gold_note_numbers`. Q25/Q28/Q31 apply prerequisite closure expansion, Q26/Q27/
Q29/Q30/Q32 record closure normalization, and Q33-Q40 become strict
`EMPTY_RESULT` with `STRICT_EMPTY_SEMANTIC_RELAXATION`. Q41-Q52 use the exact
v2 negative categories/reasons and tier 0. Closure derivations use the fixed
support graph SHA-256
`e36887b065ea722861f7a5d9b382bdebea349f37f7360245843b8375db40b017`; policy
derivations use the specified zero hash. The required
`repository-maintainer`/`signed_off: true` representation is schema fixture
metadata, not a claim of an external approval process.

## Self-review and concerns

Self-review confirmed the legacy file has no diff, normalized files contain no
`expected_notes`, all normalized records preserve canonical field order, the
manifest validator rejects unsigned records and missing derivation hashes, and
generation is offline/model-free/time-free/network-free. The pre-existing
shared `.venv` lacked packages needed by the full research suite; verification
therefore used the isolated dependency-complete environment named above. No
other concerns remain.

## Commit

`97700ba` (the commit is amended only to record this SHA in the report).
