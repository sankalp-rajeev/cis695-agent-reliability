# Phase 3 Fix 5 — SymPy native bin/test adapter and parser

Fix 4 was committed and pushed separately as `28f93e3`; the accounting guard was
precommitted in `ec918ba`. This commit adds the SymPy adapter without changing
B1/B2, thresholds, CPU settings or the production 300-second execution cap.

## Adapter and verified identity scope

SymPy is discovered from `bin/test` plus `sympy/__init__.py` before pytest config.
Live validation also repairs the frozen `pytest` runner metadata when those
source files prove this is a SymPy tree; the frozen selection lists are unchanged.
The actual runner is recorded separately in each task/tree receipt.

The adapter invokes native `bin/test -C --verbose --no-subprocess <module>`.
The cache setting is applied before the first SymPy import. The additional
no-subprocess flag preserves the exact selection guard within a single module
process instead of losing it to native hash-randomization re-exec. SymPy's
built-in `-k` matcher uses substrings, so the adapter filters native file
collection to the exact module and native matches to exact selected function
names. No test-source file or selected family is added or modified.

Collection delegates to native SymPyTests.test_file with matches returning false,
records the native functions, and never enters a test body. Both historical
utilities.runtests and newer testing.runtests module layouts are supported.
Unselected generator factories are not called. A selected generator without
verified concrete identities is COLLECTION_ERROR, never INVALID_ID or an invented
pass; there are no selected generators in this smoke's 781 selected functions.
Native import/collector failures stay missing under both policies.

The shared parser reads native file headers and verbose test tokens: ok, f/XFAIL,
X/XPASS, F, E, and skip/timeout tokens. It handles ANSI, multiline status output,
file boundaries and summaries without inventing test identities. Parsed baseline
caches from prior runner revisions are invalidated. The cache revision changed
after the smoke; the smoke calls ContainerTestExecutor directly and never reads
baseline caches. This sole post-smoke cache guard is recorded separately in
`cache_revision_addendum.json` and covered by a dedicated unit test.

## Final combined base-only smoke

Tasks were fixed by identity/runner type: Django-11820 and the first sorted frozen
SymPy task, SymPy-13480. No patched tree, correctness sidecar or label comparison.
Base source/config files, including SymPy's bin/test, were hash-verified before
collection and execution. All containers used network none and were removed.

| Task | Selected slots | Admitted C | Missing C | Admitted S | Missing S | INVALID_ID | Wall time |
|---|---:|---:|---:|---:|---:|---:|---:|
| Django-11820 | 3,167 | 3,123 | 28 | 3,060 | 91 | 16 | 109.73 s |
| SymPy-13480 | 781 | 638 | 125 | 635 | 128 | 18 | 335.32 s |

Missing counts above exclude the separately reported INVALID_ID slots. Treating
invalid slots as missing gives C/S missing counts 44/107 for Django and 143/146
for SymPy. INVALID_ID never contributes admitted outcomes or the H1 numerator.

Django: **82 initial module processes, zero individual retries**, one process per
executed module. Its collection errors remain missing; GIS modules each have an
isolated native-collection process and no test execution process.

SymPy: **14 initial module processes plus 16 individual retries = 30 execution
processes**. One quantum printing module failed to load under the native warning
policy; its 16 remaining valid IDs were retried individually and stayed
COLLECTION_ERROR. This is not converted to INVALID_ID or a regression.
Twelve other completed modules used one process each; the limits module was
still running at the cap, and the lambdify module was not reached. Per-module
counts and durations are in each task's `module_processes.csv`.

**SymPy hit the unchanged 300-second execution cap. It was not rerun.** Its
33.27-second validation phase plus setup and execution gives 335.32 seconds total.
The 125 C-missing slots comprise 16 collection errors, two observed test errors,
and 107 timed-out/unreached slots (represented by TIMEOUT until Fix 7 separates
NOT_REACHED). The 18 INVALID_ID slots were absent from successful native
collection in the disabled Sage test module. RUNNER_UNAVAILABLE is now zero:
this new native-adapter smoke is separate from the corrected historical pytest
smoke, whose 781 slots remain RUNNER_UNAVAILABLE in the immutable Fix 4 report.
No failed base assertion/error is called a patch regression, and no outcome was
compared with correctness labels.

`base_smoke_summary.csv` gives counts; `base_smokes/` contains per-module receipts,
base-only outcomes and raw byte evidence. `adapter_provenance.json` records the
native command and adapter payload hash.

## Stored paired sensitivity and H1

The accounting report replays the same immutable 83-task captures and frozen
static source ledger, not the fresh base smokes. It does not invent unrun patched
SymPy outcomes. Under both INVALID_ID accounting rules, C has 42 PASS/FAIL yes/no
verdicts and S has 21; including the separately reported REGRESSION_ERROR gives
43/22. **Differing tasks: C none, S none.** All six native FAILs retain evidence.

The stored-data H1 projection remains 23,761 / unchanged B1 37,614 (63.17%),
with zero INVALID_ID admissions. Its informational secondary denominator removes
498 invalid B1 slots: 23,761 / 37,116 (64.02%). This is not a Phase 4 run result
or a change to the primary denominator, 60% prediction, or 30% falsification
threshold. See `stored_accounting/` for every task and both denominator rules.

## Validation and stop point

Full pinned worktree suite: **1,103 passed, 6 failed, 6 skipped, 17 setup errors**;
all **18 new Fix 5 tests pass**. The exact failure/error test identities match the pre-existing environment
baseline. Reasons remain the
missing ignored patch fixture, unavailable Landlock, pre-Fix-2 config expectation
and historical source seals. No unrelated test or seal was weakened. Ruff passes
for changed files; the shared driver/parser and adapter are Python-3.6 compatible.

```bash
env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/test_sympy_adapter.py -q
env -u PYTHONPATH .venv/bin/python scripts/phase3_execution_smoke.py \
  --task sympy__sympy-13480 --output /tmp/sympy_base_fresh
```

The smoke command is supplied for reproducibility, not an instruction to retry
the recorded cap hit. Fixes 6–8 and the controlled Phase 4 run have not started.
Result commit: resolve `git log -1 --format=%h -- reports/next_phases/phase3_fix5/SUMMARY.md`.
