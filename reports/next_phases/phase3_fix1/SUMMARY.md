# Phase 3 Fix 1: native parser and concrete scoring

Stored-capture re-scoring only. No Docker, benchmark tests, package installation
or candidate-patch application. The fixed plan was committed and pushed as
`c4d17c8` before these native source changes.

## Native changes

`result_parser.py` moves the Phase 2 parser into the verifier: ANSI stripping,
Django multiline/bare statuses and docstrings, summary rejection, unique ID
mapping, fixture/loader identity and parameter-case accounting. Both live
`ContainerTestExecutor` and the offline replay call `run_from_capture`.

Selected-family aggregates are admission summaries; regression comparison,
baseline failure accounting and confirmations use individual concrete cases.
A failure in one base parameter cannot hide a different parameter's regression,
and different base/patched parameter IDs remain missing rather than paired.
Baseline caches carry a parser revision so legacy parsed baselines cannot mix
with Fix 1 patched outcomes. No frozen cache was changed.

## Stored-data verification

| Check | Native Fix 1 result |
|---|---:|
| Previously INCOMPLETE tasks recovered | **9/39** |
| Previously NOT_AVAILABLE tasks gaining binary evidence | **2/13** |
| Original native FAIL tasks retained | **6/6** |
| Calls matching Phase 2 parsed identities, statuses, flavors and kinds | **169/169** |
| V2 capture files hash-verified | **676** |

The recovered task sets exactly match Phase 2, not just their cardinalities.
The 676 files are V2's four captured files for each of 169 calls; SCG's 104 files
are outside this re-scoring. All initial-pair completeness decisions match the
Phase 2 reference. Six native FAILs retain concrete base-PASS/patched-FAIL
evidence in `native_FAIL_evidence.csv`, with source path:line references.
Existing recorded confirmations are reused only when their observed identities
cover the requested suspects; their original requested scope remains intact.
No new confirmation was needed or synthesized.

Offline native signal counts are **36 PASS, 6 FAIL, 31 INCOMPLETE and
10 NOT_AVAILABLE** (42/83 binary). Astropy-13977 moves from NOT_AVAILABLE to
INCOMPLETE because the fixed parser recovers partial evidence; it does not
become PASS. These are re-scored stored observations, not controlled-run results
or replacements for frozen native verdict files.

## Checks and scope

The focused parser, container, regression, completeness, downstream and record
checks report **160 passed, 1 skipped**. The skipped check requires an optional
stored verification-record fixture absent from this worktree; it is not a
benchmark skip or part of the recovery counts. Ruff passes for every new or
changed native Fix 1 source and its replay script/tests.

The launcher, capture driver, selection and committed plan are unchanged.
Historical skip-compatible classification is retained: runtime XFAIL/XPASS
separation, strict skips and REGRESSION_ERROR remain Fix 2; ID validation,
isolation, SymPy, CPU flags, time budgets and new confirmation policy remain
Fixes 3–8. Phase 3 cost-only checks have not run.

## Reproduction

Use `PYTHONPATH=src` with the project Python environment:

```bash
python scripts/phase3_fix1_rescore.py \
  --repo /home/sankalp/projects/cis695-v2-scg-ubuntu-publication \
  --phase2 reports/next_phases/phase2_incomplete_causes \
  --frozen /home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/paired_frozen \
  --results /home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results \
  --reference-parser scripts/phase2_capture_analysis.py \
  --output /tmp/phase3_fix1_fresh
```

`manifest.json` hashes each input and the native source used. `task_rescore.csv`
and `call_rescore.csv` inventory all tasks and calls; `recovery_chart.csv` has
three data rows for presentation.
