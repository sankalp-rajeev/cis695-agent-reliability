# Phase 3 Fix 4 — collection accounting guard and module fault isolation

The INVALID_ID accounting guard was committed and pushed before implementation
in `ec918ba`. B1 = 37,614, B2 = 21/83 and all thresholds remain unchanged.

INVALID_ID now requires static proof (absent source/object, non-test object,
no runnable owner) or an explicitly successful native receipt that omits the
identity. Nonzero collector exit (including pytest exit 5), missing receipts,
collector crashes, module/interpreter/import failures and timeouts remain missing
as COLLECTION_ERROR or RUNNER_UNAVAILABLE under C and S. Static parse/ancestry
errors are not proof of invalidity. Missing runner and collection errors have
separate test statuses and paired outcomes, neither counted as execution or
regression. Baseline caches are revised to avoid mixing the former accounting.

Native pytest validation passes only containing module paths to `--collect-only
-q`, followed by an intersection with selected identities. It never sends an
unverified `file::test` ID to pytest. A real subprocess unit test verifies the
command and proves an unselected collected function is not admitted or executed.

## Corrected historical collection-only smoke counts

This reclassification uses the immutable Fix 3 receipts and captured messages;
there was no new test execution or correctness join for this table.

| Task | VALID | INVALID_ID | COLLECTION_ERROR | RUNNER_UNAVAILABLE |
|---|---:|---:|---:|---:|
| Django-11820 | 3,125 | 16 | 26 | 0 |
| Astropy-13977 | 2,959 | 16 | 105 | 0 |
| SymPy-13480 | 0 | 0 | 0 | 781 |

SymPy's absent pytest runner is RUNNER_UNAVAILABLE, not INVALID_ID. Astropy's
nonzero no-collection exits are COLLECTION_ERROR, not successful absence.
`corrected_collection/corrected_counts.csv` and per-label JSON retain reasons.
The original Fix 3 reports remain immutable historical evidence.

## Execution isolation

The driver groups validated identities by module and starts one runner process
per module. A module load abort triggers individual reruns only for valid IDs
without an observed terminal outcome. Actual FAIL/ERROR case outcomes are kept;
already observed cases are not rerun. The parent load placeholders are superseded
when individual receipts replace them, while the full raw bytes remain available.
GIS guard modules stay isolated, are not retried, and remain missing evidence.
Per-module start/end receipts record parent/retry relationships and durations.
The per-pass execution cap remains 300 s; Fixes 6–8 have not started.

## Base-only Django smoke

Frozen task Django-11820: **82 execution processes across 82 executed modules,
one process per module, zero individual retries**, 104.04 s wall time including
36.46 s validation and 65.15 s completed runner-process time. All 2,574 archived
base Python/config files were verified. No patched run or correctness labels.

| Slot accounting | Admitted | Missing excluding INVALID_ID | INVALID_ID separately | Missing including INVALID_ID |
|---|---:|---:|---:|---:|
| C | 3,123 | 28 | 16 | 44 |
| S | 3,060 | 91 | 16 | 107 |

The 28 C-missing slots include 26 collection errors and two observed test errors.
Two GIS modules each have one isolated collection process and zero execution
processes; their guard errors stay missing. Full per-module counts are in
`django_base_smoke/module_processes.csv`; raw results are base outcomes only,
not patch-correctness findings. Failed base assertions are not labelled regressions.

## Stored paired-capture accounting sensitivity (83 tasks)

Only frozen selections, the frozen base/patched static ledger and immutable
stored captures were replayed; no benchmark execution or correctness sidecars.
An owner-expanded original slot is admitted only if all instances are observed.
Historical collection/infrastructure gaps remain missing; no native collection
success is invented by this replay. All six original native FAILs remain FAIL.

| Policy | INVALID_ID completeness | PASS | FAIL | REGRESSION_ERROR | PASS + FAIL yes/no | Including REGRESSION_ERROR |
|---|---|---:|---:|---:|---:|---:|
| C | excluded | 36 | 6 | 1 | 42 | 43 |
| C | missing | 36 | 6 | 1 | 42 | 43 |
| S | excluded | 15 | 6 | 1 | 21 | 22 |
| S | missing | 15 | 6 | 1 | 21 | 22 |

**Tasks whose verdict differs: C: none; S: none.** Every task is listed in
`stored_accounting/task_policy_sensitivity.csv`; `policy_counts.csv` retains
REGRESSION_ERROR separately so it cannot silently enlarge the historical
PASS/FAIL coverage definition.

H1 is an **offline projection, not the Phase 4 run result**: 23,761 admitted
original B1 slots / unchanged B1 37,614 = 63.17%. INVALID_ID contributes zero
admissions. The 498 INVALID_ID slots within B1 stay in the primary denominator.
The explicitly informational secondary denominator is 37,116, giving 64.02%.
No threshold or primary denominator was changed. Admission uses observed
PASS/FAIL/SKIPPED/XFAIL/XPASS cases, with every expanded instance required;
collection/runner errors, invalid IDs, missing/timeouts and ERROR remain outside
this conservative numerator. `H1_projection.json` records both denominators.

## Validation and reproduction

Full pinned local unit suite: **1,085 passed, 6 failed, 6 skipped, 17 setup errors**.
All 11 new Fix 4 tests pass. The exact pre-existing failure/error set is unchanged
(missing ignored patch fixture, unavailable Landlock, stale pre-Fix-2 config
expectation, and historical frozen-source seals); see `preexisting_unit_failures.csv`.
Ruff passes for changed files. No correctness labels were opened or joined.

```bash
env -u PYTHONPATH .venv/bin/python scripts/phase3_guard_replay.py --output /tmp/guard_fresh
env -u PYTHONPATH .venv/bin/python scripts/phase3_accounting_replay.py --output /tmp/accounting_fresh
env -u PYTHONPATH .venv/bin/python scripts/phase3_execution_smoke.py \
  --task django__django-11820 --output /tmp/django_module_fresh
```

Result commit: resolve `git log -1 --format=%h -- reports/next_phases/phase3_fix4/SUMMARY.md`.
Fix 5 is the next separately committed change; it is not included here.
