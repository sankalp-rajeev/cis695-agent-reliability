# Phase 6b plan-freeze verification

Merge commit: `55d6756d531737e928d5ddef7f179562e7358502`, with parents `d77762ec75b418d62717d2fb3c76ab844aa6b830` and `4fbd4ba480e6e481434d68d05d950a324d50c58f`. The merge used `--no-ff`; there were no conflicts. All 18 Phase 6a files remain byte-identical to d77762e; Git blob hashes are recorded in `merge_validation.json`.

The same Fix 18 unit suite (`bash scripts/test.sh tests/unit --tb=no`, with temporary JUnit XML paths) was run on both branches. The non-passing checks were not fixed or suppressed. Counts and all failing/error check names were identical:

| Branch/revision | Passed | Failed | Errors | Skipped |
|---|---:|---:|---:|---:|
| V2 execution repair / `4fbd4ba` | 1348 | 6 | 47 | 6 |
| Merged runtime instrumentation / `55d6756` | 1348 | 6 | 47 | 6 |

The separate `python3 tests/unit/test_phase5_replay.py -v` invocation passed all 11 checks.

The set selector ran twice with the commands recorded in `merge_validation.json`. Both `eval_set.json` and `eval_set.sha256` were byte-identical. The set has seven fixed tasks, six seeded tasks and 12 fixed reference IDs. Whole-file SHA-256 of `eval_set.json`: `368c8650739746b53638c35682a876134c14e76d80def8511bcb76b3054f4920`.

| Seeded task | Repository | Eligible repository pool size |
|---|---|---:|
| `matplotlib__matplotlib-24637` | matplotlib/matplotlib | 12 |
| `pallets__flask-5014` | pallets/flask | 1 |
| `pydata__xarray-6744` | pydata/xarray | 4 |
| `pytest-dev__pytest-5787` | pytest-dev/pytest | 6 |
| `scikit-learn__scikit-learn-12585` | scikit-learn/scikit-learn | 3 |
| `sphinx-doc__sphinx-7910` | sphinx-doc/sphinx | 3 |

The selector used only hash-pinned, label-free Phase 5 costs/reference IDs and the frozen task metadata. The roadmap deviation in the plan records the audit conclusion supplied in the request; no correctness labels or oracle data were opened.

No tracer was written or run, no trace or benchmark was run, and no Docker or model call was made. Existing tags and sealed results were not modified. This step stops at the plan freeze.
