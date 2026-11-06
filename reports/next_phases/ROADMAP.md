# Roadmap: V2 execution reliability and runtime instrumentation

Trust but Verify — CIS 695 · drafted 6 Nov 2026

## Where we start

The full V2 vs. call-graph experiment showed that most lost V2 evidence comes from how tests are run and read, not from which tests are selected.

| Measure | Value |
|---|---|
| Tasks with a yes/no V2 verdict | 31 / 83 (37%) |
| V2 INCOMPLETE (would have passed, evidence gaps) | 39 |
| Raw runner captures available, hash-verified | 780 |
| Known regression tests (from 5 correct-labelled patches) | 6 — V2 selected 6/6, call graph 0/6 |
| Grader failures in pre-existing tests (4 incorrect patches) | 7 — V2's list has 7/7, call graph 0/7 |
| Incorrect patches failing only added/rewritten tests | ~10 / 14 — unreachable by any existing-test method |

Dr. Hassan asked us to try runtime instrumentation, so it is Phase 6. It is tested two ways: as a measuring tool and as a test selector.

## Ground rules (all phases)

- **Frozen and read-only:** harness `b030e50`, V2 `9654fc7`, corrected call graph `e1a3ed1`, the frozen protocol, the full-83 analysis manifest (`2728ba1e…`), the 83 candidate patches, labels, source archives, Docker images and V2/call-graph selection lists. Nothing is overwritten or re-sealed.
- **New work lives on a new branch**, with outputs under a new folder, e.g. `reports/next_phases/phaseN_*`.
- **No label leakage:** correctness labels and grader test lists may be used only for post-hoc diagnosis. They never set a selector, ordering, timeout or parser decision.
- **Write the plan before any run** for Phases 3, 4 and 6b: parameters, metrics and success/failure thresholds.
- **Absence is never a pass:** every unexecuted test is reported with a reason.
- **No package installs inside the images.** Anything extra is mounted read-only from outside.

## Git workflow

Repository: https://github.com/sankalp-rajeev/cis695-agent-reliability

**Existing branches (do not commit to these):**

| Branch | What it holds |
|---|---|
| `main` | Main project line |
| `experiment/v2-scg-paired-harness` | Frozen V2 vs. call-graph harness (`b030e50`) and V2 (`9654fc7`) |
| `experiment/callgraph-typeprop` | Type-propagation experiment and corrected call graph (`e1a3ed1`) |
| `fix/pkg-cache-mask` | Package-cache mask fix |

**New branches for this roadmap:**

| Branch | Phases | Branched from |
|---|---|---|
| `experiment/v2-execution-repair` | 1, 2, 3, 4, 5 | `experiment/v2-scg-paired-harness` |
| `experiment/runtime-instrumentation` | 6a, 6b | `experiment/v2-scg-paired-harness`, then merges in `experiment/v2-execution-repair` before 6b |

**Tags mark frozen points.** Tags are never moved or deleted, and branches are never force-pushed.

| Tag | When |
|---|---|
| `phase4-plan-frozen` | Phase 4 plan and executor committed, before the run |
| `phase4-run-sealed` | Phase 4 manifest and summaries committed, after the run |
| `phase6b-plan-frozen` | Phase 6b evaluation set and thresholds committed, before any 6b run |

**What gets committed:** scripts, tests, CSVs, reports, manifests and hashes. Raw run output stays local: `runs/`, `logs/`, `*.jsonl` and `*.patch` are already in `.gitignore` because they can carry oracle data. Record raw captures by SHA-256 in a committed manifest instead.

### Step 0 — set up (once)

First check that the full-83 analysis is pushed. Run this in your local clone:

```bash
cd ~/projects/cis695-agent-reliability
git fetch origin
git status                                   # must be clean
git checkout experiment/v2-scg-paired-harness
git log origin/experiment/v2-scg-paired-harness..HEAD --oneline   # unpushed commits?
ls reports/v2_scg_analysis/                  # full83_postcollection_* should be listed
```

If the full-83 report folder is not on GitHub yet, push it before starting:

```bash
git add reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/
git commit -m "Add full-83 V2 vs SCG post-collection analysis (manifest 2728ba1e)"
git push origin experiment/v2-scg-paired-harness
```

Then create the two working branches and push them:

```bash
git checkout -b experiment/v2-execution-repair experiment/v2-scg-paired-harness
git push -u origin experiment/v2-execution-repair

git checkout -b experiment/runtime-instrumentation experiment/v2-scg-paired-harness
git push -u origin experiment/runtime-instrumentation

git checkout experiment/v2-execution-repair
mkdir -p reports/next_phases
```

**If `git push` returns 403:** run `gh auth login`, then `gh auth setup-git`, and push again.

### Before every commit

```bash
git status                                    # review exactly what changed
git diff --stat experiment/v2-scg-paired-harness -- \
  reports/v2_scg_analysis reports/v2_scg_paired reports/v2_scg_integration
# ^ must print nothing: frozen experiment folders unchanged
git diff --cached --name-only | grep -E '\.jsonl$|\.patch$|^logs/|^runs/' && echo "STOP: oracle-risk file staged"
```

Stage paths explicitly (`git add <path>`), never `git add -A`.

## Overview

| Phase | What | New runs? | Est. effort | Depends on |
|---|---|---|---|---|
| 1 | Trace the 7 known failing tests through our raw results | No | ~1 day | — |
| 2 | Give every INCOMPLETE case a cause from the 780 captures | No | ~2 days | — |
| 3 | Repair V2 execution | Small checks only | ~4–6 days | 1, 2 |
| 4 | One controlled V2 rerun on all 83 tasks | Yes, ~3–8 h | ~1 day | 3 |
| 5 | Offline replay of selectors and time-budget ordering | No | ~2 days | 4 |
| 6a | Runtime trace of the 13 known tests | Yes, tiny | ~1–2 days | — (alongside 1) |
| 6b | Bounded coverage-based selection trial | Yes, ~15 tasks | ~3–4 days | 3, 4 |

Effort figures are estimates.

**Suggested order:** Week 1: Phases 1, 2 and 6a. Weeks 2–3: Phase 3, then the Phase 4 run. Week 4: Phases 5 and 6b, then write-up.

---

## Phase 1 — Trace the 7 known failing tests

**Question:** the grader fails 4 incorrect patches on 7 tests that already existed, and all 7 are in V2's list. Why didn't they fail in our runs?

**Inputs:** stored V2 raw captures and verdict records; the 7 test IDs (`reports/callgraph_selection/typeprop_experiment/regression_validation/`).

**Steps:**
1. For each test, find its outcome on the original and patched trees in the raw captures.
2. Classify each test into exactly one bucket:
   - **A — not reached:** timed out or never run (e.g. django-13297, where 6,890 of 8,155 tests timed out).
   - **B — result dropped:** it ran, but the outcome wasn't admitted (parametrized name, parser, ANSI codes).
   - **C — already failing:** it fails on the original code in our image (environment difference).
   - **D — passed:** it passed on the patched code in our environment.
3. Record the evidence (capture file, line, hash) for every classification.

**Output:** `phase1_known_failures.csv` plus a half-page summary.

**Done when:** all 7 tests are classified with evidence.

**Decision:** if any land in D, look for an environment difference from the grader before Phase 3.

**Commit and push** (branch `experiment/v2-execution-repair`):

```bash
git checkout experiment/v2-execution-repair
git add reports/next_phases/phase1_known_failures/
git commit -m "Phase 1: classify the 7 grader-failing pre-existing tests from stored V2 captures"
git push
```

---

## Phase 2 — Cause for every INCOMPLETE case

**Question:** why is each of the 39 INCOMPLETE tasks incomplete, and how many would a result-reading fix alone recover?

**Inputs:** the 780 raw captures, frozen selection lists and V2 verdict records.

**Steps:**
1. For each task, count the gaps per cause:
   - timeout / not run;
   - parametrized name mismatch;
   - collection or runner error;
   - output parsing (Astropy colour codes, Django two-line format);
   - pass → exception scored as an error;
   - base/patched ID-set difference;
   - SymPy runner mismatch.
2. Replay a fixed parser over the stored captures offline. Count how many tasks become COMPLETE with no new runs.
3. Repeat the counts for the 13 NOT_AVAILABLE tasks.

**Output:** `phase2_incomplete_causes.csv` (task × cause counts), a cause summary table, and the "parser-only recovery" number.

**Done when:** every INCOMPLETE task has at least one evidenced cause and no gap is unexplained.

**Decision:** the cause shares set the priority order for Phase 3 and a realistic Phase 4 target.

**Commit and push:**

```bash
git add reports/next_phases/phase2_incomplete_causes/ scripts/<phase2_analysis_script>.py
git commit -m "Phase 2: attribute every INCOMPLETE and NOT_AVAILABLE gap from 780 raw captures"
git push
```

---

## Phase 3 — Repair V2 execution

**Goal:** change how V2 runs and reads tests without changing which tests it selects.

**Changes, in priority order from Phase 2:**
1. **Orchestration:** one runner process per test module (or per pass) instead of per batch of 25. Record the per-pass time budget as a parameter, and report every test not reached.
2. **Native collection:** run `pytest --collect-only -q` on both trees and use it only to expand V2's IDs into concrete node IDs (parametrized cases). It never adds or removes a selected test family. Django uses its own label discovery.
3. **Parsers:** strip ANSI codes in scoring, handle Django's two-line verbose output, and score parametrized cases individually.
4. **Classification:** add a separate `REGRESSION_ERROR` outcome for base PASS → patched ERROR. Report FAIL both with and without it.
5. **SymPy:** a `bin/test` runner adapter, matching the SWE-bench harness.
6. **Reporting:** keep the strict PASS rule as primary, and report raw per-task coverage beside it.

**Checks:**
- Unit tests for each parser and adapter.
- Run the three largest tasks per runner type to measure cost only.
- Re-score the stored captures with the new parsers. Any original V2 FAIL that disappears without an explained cause is a bug.

**Output:** a new executor version, its unit tests and the written plan for Phase 4.

**Done when:** all checks pass and the Phase 4 plan is committed.

**Commit and push:** one commit per change, so each fix can be reviewed and reverted on its own.

```bash
git add src/reliability/verifier/container.py tests/<new_test_file>.py
git commit -m "Phase 3: run one process per test module instead of 25-ID batches"
git push
# repeat for: native collection, parsers, REGRESSION_ERROR, SymPy adapter, reporting

# then freeze the plan and executor before Phase 4
git add reports/next_phases/phase4_plan.md
git commit -m "Phase 4 plan: hypothesis, metrics, thresholds and stopping rule"
git tag -a phase4-plan-frozen -m "Executor and Phase 4 plan frozen before the controlled rerun"
git push
git push origin phase4-plan-frozen
```

---

## Phase 4 — One controlled V2 rerun

**Hypothesis:** with V2's selection frozen, the repaired executor raises tasks with a yes/no verdict from **31/83 to at least 50/83**.

**Falsified if:** fewer than **42/83**. Then execution was not the dominant loss, and selection or environment work gains standing.

**Setup:**
- V2 only, all 83 tasks, no subsetting.
- Same frozen selection lists, images, `--network none`, machine and strict PASS rule.
- Per-pass cap of 1,800 s, with every cap hit reported.

**Metrics per task and tree:** selected, collected, admitted, executed, NOT_RUN, TIMEOUT, ERROR, REGRESSION, REGRESSION_ERROR, collection time, execution time, completeness state and gap reasons.

**After metrics are frozen (post-hoc only):**
- FAIL precision with an exact 95% interval;
- FAIL on correct patches;
- reconfirmation of the 6 regression tests;
- outcome of the 7 grader-failing tests.

**Stopping rule:**
- One run.
- No executor change after labels are read. Any later fix is a new version, reported as exploratory.
- Stop and report partial accounting if the run exceeds 12 h.

**Output:** a sealed run folder with a manifest, raw captures and hashes, plus a short results note.

**Commit and push:**
- Run from the tagged commit, with a clean tree.
- Raw captures stay in the ignored `runs/` folder.
- Commit only the manifest (with SHA-256 per capture), summaries and the results note.

```bash
git status                                     # must be clean before the run
git describe --exact-match HEAD                # must print phase4-plan-frozen
# ... run Phase 4 ...
git add reports/next_phases/phase4_rerun/      # manifest, summary CSVs, results note
git commit -m "Phase 4: controlled V2 rerun on 83 tasks with repaired executor (sealed)"
git tag -a phase4-run-sealed -m "Phase 4 results sealed before reading labels"
git push
git push origin phase4-run-sealed
# post-hoc label analysis goes in a separate, later commit
```

---

## Phase 5 — Offline replay

**Goal:** use the Phase 4 run as a complete reference to evaluate selection and ordering without new runs.

**Steps:**
1. **Selector replay:** score V2 Tier 1, Tier 1 + 2, and the corrected call graph by which reference regressions and tests each would have kept.
2. **Time-budget ordering:** use a label-free rule, fixed before Phase 4: Tier 1 before Tier 2; within a tier, test modules whose names match a changed module first; then source order. Compare it with 20 seeded random orderings at 30, 60, 120 and 300 s per pass, using measured per-test durations.

**Metrics:** share of reference regressions found, share of tests executed, time to first regression, and tasks complete at each budget. Unexecuted tests are always reported.

**Useful if:** at 120 s the rule keeps ≥ 90% of reference regressions, and its median time to first regression beats the random orderings' 25th percentile. With few regressions, report case by case rather than as a rate.

**Commit and push:**

```bash
git add reports/next_phases/phase5_replay/ scripts/<replay_script>.py
git commit -m "Phase 5: offline selector replay and time-budget ordering against Phase 4 reference"
git push
```

---

## Phase 6 — Runtime instrumentation (Dr. Hassan's request)

Instrumentation is tested in two parts:

- **6a, a measuring tool:** does runtime tracing show what the static graph misses?
- **6b, a test selector:** can coverage-based selection match running V2's full list at lower total cost?

### 6a — Runtime trace of the 13 known tests

**Question:** at runtime, do the 6 regression tests and the 7 grader-failing tests actually execute the changed function, and through what call chain?

**Tooling:**
- Python's built-in `sys.settrace` (or the `trace` module), loaded through a small `sitecustomize.py` mounted read-only and added via `PYTHONPATH`.
- No coverage.py install and no image changes.
- Works on all the images' Python versions (3.5–3.11).
- Django tests are traced through `runtests.py` the same way.

**Steps:**
1. Run each of the 13 tests alone on the original tree with tracing on.
2. Record whether each changed function (by AST-qualified name and line range) is entered, the call stack at first entry, and the hop count from the test.
3. Repeat on the patched tree. This also records patch-only functions the static graph could never contain.
4. Run each test once more without tracing. Its outcome must match, which checks that tracing doesn't change behaviour.
5. Compare each runtime chain with the static graph: find the first edge the graph lacks, and its cause (fixture, inheritance, property, re-export, visitor dispatch, other).

**Output:** `phase6a_runtime_vs_static.csv` with test · changed function · reached at runtime? · hops · reached statically? · first missing edge · cause.

**Done when:** all 13 tests are traced, or each failure to trace is recorded with a reason.

**Use in the write-up:** a measured static-vs-runtime gap, replacing hand-traced explanations. This is post-hoc diagnosis only. The test list comes from known outcomes, so it must never feed selection.

**Commit and push** (branch `experiment/runtime-instrumentation`):

```bash
git checkout experiment/runtime-instrumentation
git add tools/runtime_trace/sitecustomize.py tools/runtime_trace/README.md \
        reports/next_phases/phase6a_runtime_trace/
git commit -m "Phase 6a: runtime trace of 13 known tests vs static call graph (post-hoc diagnostic)"
git push
```

### 6b — Bounded coverage-based selection trial

**Hypothesis:** file-level coverage selection keeps every reference regression while executing at least 50% fewer tests on the patched tree.

**Evaluation set (fixed before any run, no tuning):**
- the 5 tasks with known regression tests;
- the 4 incorrect-patch tasks with pre-existing grader failures;
- 6 further tasks drawn with a fixed seed, stratified by repository, from the pytest-runnable tasks;
- about 15 tasks in total.

**Procedure:**
1. **Cold start:** on the original tree, run V2's full candidate list with per-test tracing, building a test → executed functions/files map.
2. **Select:**
   - function-level: tests whose trace enters a changed function;
   - file-level: tests whose trace touches a changed file.
3. **Patched tree:** run each selection.
4. **Reference:** compare with the Phase 4 run, where all V2 candidates ran on both trees.

**Metrics:**
- regressions kept vs. reference (recall);
- known tests kept (out of 13);
- tests executed on the patched tree;
- **total cost including the cold-start traced run**, vs. running everything on both trees;
- tracing overhead;
- outcome disagreements between traced and untraced runs.

**Blind spots to report, not hide:** functions that exist only after the patch, non-Python dependencies, data files.

**Success:** file-level selection keeps 100% of reference regressions and all reachable known tests, with ≥ 50% fewer patched-tree executions.

**Failure:** any reference regression is missed at file level, or tracing changes any test outcome.

**Either way, report the honest efficiency figure:** without a reusable coverage history, the cold-start run is a full traced base pass. The saving is therefore limited to the patched pass, minus tracing overhead.

**Done when:** the full metric table is filled for all evaluation tasks.

**Decision:** adopt coverage-based selection for later work only if 6b succeeds *and* its total cost beats the Phase 4 executor running V2's full list.

**Commit and push:** bring in the repaired executor and the sealed Phase 4 reference first, then freeze the 6b plan before any run.

```bash
git checkout experiment/runtime-instrumentation
git merge --no-ff phase4-run-sealed -m "Merge sealed Phase 4 reference into runtime-instrumentation"
git add reports/next_phases/phase6b_plan.md     # evaluation set, seed, thresholds
git commit -m "Phase 6b plan: evaluation set, seed and success/failure thresholds"
git tag -a phase6b-plan-frozen -m "Phase 6b plan frozen before any coverage run"
git push
git push origin phase6b-plan-frozen
# ... run 6b ...
git add reports/next_phases/phase6b_coverage_trial/
git commit -m "Phase 6b: bounded coverage-based selection trial vs Phase 4 reference"
git push
```

## Final step — merge and open pull requests

When all phases are done, open one pull request per branch into `main` and leave the experiment branches and tags in place:

```bash
gh pr create --base main --head experiment/v2-execution-repair \
  --title "V2 execution repair, controlled rerun and offline replay (Phases 1-5)" \
  --body "See reports/next_phases/ for phase reports. Frozen points: tags phase4-plan-frozen, phase4-run-sealed."
gh pr create --base main --head experiment/runtime-instrumentation \
  --title "Runtime instrumentation: trace diagnostic and coverage-selection trial (Phase 6)" \
  --body "See reports/next_phases/phase6a_* and phase6b_*. Frozen point: tag phase6b-plan-frozen."
```

---

## Decision points

| After | If | Then |
|---|---|---|
| Phase 1 | Any of the 7 tests passed in our environment | Investigate the environment difference before Phase 3 |
| Phase 2 | Parser fixes alone recover most INCOMPLETE tasks | Shrink Phase 3 to parsing; start Phase 4 sooner |
| Phase 4 | ≥ 50 / 83 yes/no verdicts | Execution confirmed as the main loss; headline result |
| Phase 4 | < 42 / 83 | Execution not dominant; revisit selection and environment |
| Phase 5 / 6a | A known failing test is outside V2's list, or is reachable at runtime but not selected | Selector work justified as a separate study |
| Phase 6b | Success and cheaper than the full list | Coverage selection becomes a candidate for future work |

## What this will let us claim

- How much oracle-blind regression evidence is lost to execution and result-reading, as opposed to test choice.
- A measured gap between static call-graph reachability and runtime execution on real SWE-bench tests.
- Whether coverage-based selection pays off when no test history exists.
- How many incorrect patches existing tests can reach at all (about 4 of 14 here, with 10 needing new tests: the V4 signal).

## Open questions

- Whether the base images reproduce the grader's environment closely enough (Phase 1, bucket C).
- How many correct patches will newly FAIL once exceptions and parametrized cases are scored. Old tests can disagree with correct fixes, as in pytest-5809.
- Statistical power: with only 4–6 reachable incorrect patches, results are case evidence, not rates.
