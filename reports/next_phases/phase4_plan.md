# Phase 3 fix order and Phase 4 plan (draft v1)

Trust but Verify · branch `experiment/v2-execution-repair` · drafted 6 Nov 2026 after Phase 2 (`107a286`)

**Status: DRAFT.** Before any Phase 3 code is written, fill in the two computed baselines in §3 and commit this file. Thresholds may not change after that commit. Implementation details may change until the `phase4-plan-frozen` tag.

## 1. What Phase 2 changed

Phase 2 counted the lost evidence (selected tree-ID slots; cause groups overlap). The ranking is not what we assumed:

| Cause | Tasks | Selected tree slots | Fixed by |
|---|---:|---:|---|
| Output or ID parsing | 32 | 17,157 | Fix 1 |
| Parametrized family mismatch | 36 | 6,619 | Fixes 1, 3 |
| SymPy runner mismatch | 5 | 5,244 | Fix 5 |
| Timeout / not reached | 2 | 4,899 | Fix 7 |
| Collection / runner error | 34 | 3,683 | Fix 0, then decide |
| Batch-abort collateral (within the above) | 32 | 3,138 | Fixes 3, 4 |
| GIS environment-guard abort | 14 | 2,262 | Fix 4 (isolate only) |

- **Timeouts are not the main loss.** They hit 2 tasks. Most lost evidence comes from reading results and from invalid IDs.
- **Batch aborts:** 942 load aborts. There were 714 not-found batches (including 130 with explicit xmlschema import errors), 98 non-test-function batches, 8 property batches and 4 helper batches, plus 92 GIS-guard and 26 genuine module-collection attribute-error batches. They strand 3,138 slots (10% of NOT_RUN).
- **Skips:** 13 of the 25 current PASS verdicts accepted selected skips, and none survives a strict skip rule. 38 skipped tests in 2 pylint tasks are CPU-conditioned: the default container reports 1 CPU, and `--cpu-shares 2048` gives 2. XFAIL is currently normalised to SKIPPED.
- **Projections (stored data, not results):** yes/no verdicts are 42/83 with parser replay under the current policy, and 20/83 with parser replay plus strict skips.

## 2. Phase 3 fix order

Each fix is one commit with unit tests. No fix changes which test families V2 selects.

0. **Diagnose collection/runner errors (offline, before coding).** List the top 10 error signatures behind the 3,683 slots, with task counts. Decide per signature: fixable in the executor, environmental, or genuine test-module error. Record the decision in this file.
1. **Move the Phase 2 parser replay into native scoring:** ANSI stripping, Django two-line status, unique ID mapping and concrete parameter accounting. Re-score the stored captures; the result must reproduce the 9/39 and 2/13 replay numbers exactly.
2. **Outcome model:**
   - XFAIL and XPASS become distinct outcomes, never SKIPPED. Base XFAIL → patched XFAIL counts as evidence.
   - A base PASS → patched ERROR transition becomes `REGRESSION_ERROR`, reported separately from FAIL.
3. **ID validation before running:**
   - Resolve every selected ID on each tree. pytest uses `--collect-only -q`; Django uses a dry `loadTestsFromName` per label.
   - Non-test objects (property, plain function, helper, class attribute) and not-found labels become `INVALID_ID`, with the reason. They are reported, never executed and never counted as NOT_RUN.
   - Parametrized families expand to concrete node IDs. Validation removes only invalid IDs; it never adds a family.
   - INVALID_ID accounting guard: `INVALID_ID` is used only when (a) the static layer proves the label is not in source, is a non-test object, or has no runnable owner; or (b) a native collector completed successfully and did not produce the label. Collector crash, missing runner, interpreter/import failure of the module, or nonzero collector exit becomes `COLLECTION_ERROR` or `RUNNER_UNAVAILABLE`, counted as missing evidence under both policies.
   - Runnable owner depends on the task's runner. unittest-loader runners (Django runtests.py): the owner must be a unittest.TestCase subclass. pytest: a unittest.TestCase subclass, or a class pytest collects under the repo's effective config (name matches python_classes from setup.cfg / tox.ini / pytest.ini / pyproject.toml, default Test*; no __init__; __test__ not False). SymPy bin/test: as its native collector reports. A selected method whose owner is not runnable under that runner is expanded to the same method on subclasses that are runnable under the same runner and inherit it unchanged (not overridden); this adds runnable identities for the same test code, not new families. The original slot counts as admitted only if all expanded instances are admitted; expansion counts are reported separately. A label with no runnable owner becomes INVALID_ID (no_runnable_owner). Native collection is authoritative; static predictions that disagree with it are reported.
4. **Batch fault isolation:**
   - Run one runner process per test module, not per 25 IDs.
   - If a module aborts at load, rerun its remaining valid IDs individually, so one bad label cannot strand others.
   - GIS environment-guarded modules run in their own process and stay missing evidence (no policy change).
5. **SymPy runner adapter:** `bin/test -C --verbose`, matching the SWE-bench harness, with its own parser and unit tests.
6. **Container CPU:** add `--cpu-shares 2048` to every container, in both trees and all repositories. Do not use `--cpus`, which caps CPU time and would add timeouts.
   - *Disclosure:* found while diagnosing grader-failing tests (Phase 1). It is justified on label-free grounds: the container misreports its CPU count.
7. **Time budget:** a per-pass cap of 1,800 s, recorded as a parameter. Every test not reached is reported as `NOT_REACHED` with elapsed time.
8. **Confirmation of new failures (label-free):** every new FAIL or `REGRESSION_ERROR` is rerun alone, 3× on each tree. It counts only if stable (base PASS 3/3, patched non-PASS 3/3). Unstable cases are reported as `FLAKY`.


### Fix 0 findings — completed from stored evidence before Phase 3 code

The 3,683 initial selected tree-ID slots occur in 29 slot-bearing tasks; the
34-task cause total above also includes tasks with native gap records or raw
ERROR observations and no selected slot in this group. These are slots affected
by a signature, including co-batched requests, not exception-occurrence counts.
The top ten cover 3,634/3,683 slots; the remaining 49 are in the complete CSV.
Callable names in missing-argument errors, pointer addresses and loader-only
missing class/module attributes are normalized. Task counts overlap.

| Signature | Tasks | Slots | Decision | Example capture path:line |
|---|---:|---:|---|---|
| `TypeError: <callable>() missing 1 required positional argument: 'self'` | 9 | 2200 | executor-fixable | `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results/tasks/django__django-11820/v2/raw/base_6ac678a26dec4c0699006882fe4520bb/runner.raw:16` |
| `pytest usage error: selected ID not found (without a more specific captured exception)` | 14 | 546 | executor-fixable | `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results/tasks/astropy__astropy-13977/v2/raw/base_9f05706c0b454f819fb0ff2242038534/runner.raw:835` |
| `TypeError: <callable>() missing 1 required positional argument: 'notify_mock'` | 3 | 250 | executor-fixable | `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results/tasks/django__django-15572/v2/raw/base_bd5b50cd323c440db1d4a2f9c1d995cd/runner.raw:59` |
| `TypeError: don't know how to make test from: <property object at <address>>` | 4 | 200 | executor-fixable | `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results/tasks/django__django-11820/v2/raw/base_6ac678a26dec4c0699006882fe4520bb/runner.raw:1829` |
| `ModuleNotFoundError: No module named 'xmlschema'` | 1 | 130 | environmental | `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results/tasks/pytest-dev__pytest-5787/v2/raw/base_aa42e82c97734a5a9d57986bf9f9276b/runner.raw:551` |
| `TypeError: <callable>() missing 1 required positional argument: 'request'` | 2 | 100 | executor-fixable | `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results/tasks/django__django-13297/v2/raw/base_b801df1e75a04136a31773e481cc700e/runner.raw:23464` |
| `AttributeError: selected class has no such attribute` | 9 | 98 | executor-fixable | `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results/tasks/django__django-11820/v2/raw/base_6ac678a26dec4c0699006882fe4520bb/runner.raw:2997` |
| `AttributeError: selected module has no such attribute` | 7 | 50 | executor-fixable | `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results/tasks/django__django-11820/v2/raw/base_6ac678a26dec4c0699006882fe4520bb/runner.raw:3009` |
| `FileNotFoundError: [Errno 2] No such file or directory: 'test.txt'` | 1 | 34 | environmental | `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results/tasks/pylint-dev__pylint-4970/v2/raw/base_cf11872ced644a7b96c558645983540c/runner.raw:962` |
| `AttributeError: module 'matplotlib.testing' has no attribute 'compare'` | 1 | 26 | genuine test-module error | `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results/tasks/matplotlib__matplotlib-23476/v2/raw/base_35f2e57399e84766b47d807dd2ccfdf6/runner.raw:152` |

**Decisions:** executor-fixable means Fixes 3/4 can validate, isolate and account
for the request; it does not promise that every invalid ID can become an
executed test or that the selector may add a replacement. Generic pytest
not-found is not enough to assert a particular dependency or native test ID.
The xmlschema import error is environmental. The test.txt error is an import
precondition in Pylint's functional lint-input file, verified in stored base
source; do not create a file to make collection pass. The Matplotlib compare
attribute failure is a real module-import exception in testing/_markers.py;
preserve it as a test-module error, without claiming a patched-only regression.

The complete slot-to-signature ledger, all signatures and all per-signature
rationales are in `reports/next_phases/phase4_baselines/fix0_slots.csv` and
`fix0_all_signatures.csv`; `fix0_top10.csv` is the small chart CSV. Run
`scripts/phase4_fix0_signatures.py --report reports/next_phases/phase2_incomplete_causes
--output <fresh-output-directory>` to reproduce them. `fix0_manifest.json`
records script/input SHA-256 values. No Docker, test execution or archived
source execution was used.

**Phase 3 checks:**

- Unit tests for every fix.
- Re-score the stored captures; all 6 original native FAILs must keep their evidence.
- Cost-only runs on the largest task per runner type (Django, pytest, SymPy). Their outcomes are not inspected for labels.

## 3. Baselines to compute before coding (stored data only)

| Baseline | Definition | Value |
|---|---|---|
| B1: addressable gap slots | Initial selected tree-ID gap slots (39,876), minus slots whose only causes are GIS environment guard, empty selection or base/patched ID-set difference | **37,614 slots** |
| B2: strict projection with XFAIL separated | Parser replay + strict skip rule, with XFAIL kept as its own outcome | **21/83 projected yes/no = 15 PASS + 6 retained native FAIL** (was 20/83 with XFAIL normalised) |


**Computed baseline accounting:** B1 = 39,876 − 2,262 GIS-guard-only slots =
**37,614**. Empty selections have zero selected tree-ID slots, and the
base/patched raw-ID-set-difference counter is a typed observation, not a
selected slot; each contributes zero exclusions. Every original selected slot
is counted once, keyed by task/tree/selected ID. No task-level or raw-event
count is subtracted from a slot denominator.

B2 is a **stored-data projection**, not a run result. The replay keeps XFAIL
and XPASS as separate outcomes (194 XFAIL and 12 XPASS initial mapped tree-case
observations), blocks ordinary SKIPPED evidence for PASS, and retains all six
native FAILs. Seaborn-3069 adds the one projected PASS relative to 20/83: its
remaining non-PASS evidence is XFAIL on both trees, not an ordinary skip.
`B2_tasks.csv`, `B2_tree_outcomes.csv` and `B2_XFAIL_XPASS_evidence.csv` preserve
the task membership, separate outcomes and exact path:line witnesses.

**Script and inputs:** `scripts/phase4_plan_baselines.py` reads the Phase 2
selected-gap table, parser replay and call-guard tables, uses the unchanged
Phase 2 parser (`scripts/phase2_capture_analysis.py`), verifies the frozen
83 selection lists and native V2 records, and re-reads 156 initial runner
captures. `reports/next_phases/phase4_baselines/baseline_manifest.json` hashes
every input; `baseline_summary.json` and `B1_B2.csv` contain the computed values.

```bash
python scripts/phase4_plan_baselines.py \
  --report reports/next_phases/phase2_incomplete_causes \
  --frozen /home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/paired_frozen \
  --results /home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results \
  --parser scripts/phase2_capture_analysis.py \
  --output /tmp/phase4_baselines_fresh
```

## 4. Phase 4 hypotheses

V2 only, all 83 tasks, frozen selection lists, same images and `--network none`, plus `--cpu-shares 2048`, running the executor at tag `phase4-plan-frozen`. The policies below are fixed now.

**Verdict policies reported:**

- **Policy C (skip-compatible):** the rule in force when the roadmap was written; SKIPPED counts toward completeness.
- **Policy S (skip-strict, primary for claims about PASS):** SKIPPED and NOT_REACHED selected tests are missing evidence. XFAIL is evidence. `INVALID_ID` is excluded from the denominator and reported.
- FAIL is never demoted under either policy.
- Report Policy C and Policy S yes/no counts both with `INVALID_ID` excluded from completeness (the policy above) and with `INVALID_ID` treated as missing evidence. List every task whose verdict differs between these two accounting rules. `COLLECTION_ERROR` and `RUNNER_UNAVAILABLE` remain missing evidence in all four reports.

**H1 — execution recovers evidence (primary):**

- *Prediction:* the repaired executor turns at least **60% of B1** into admitted outcomes.
- *Falsified if:* under **30% of B1**.
- *Why it matters:* this measures execution directly, independent of verdict policy.
- `INVALID_ID` slots are not admitted outcomes and do not count toward either the 60% prediction or the 30% falsification threshold of the unchanged B1 denominator. Also report an informational H1 with `INVALID_ID` removed from B1, clearly labelled **secondary**; it does not replace the primary H1 or change its thresholds.
- H1 is already met in the Fix 5 stored-data projection: **23,761/37,614 = 63.17%**, largely from parsing. This offline result is not evidence of additional live execution recovery.

**H1b — additional live recovery (added after the Fix 5 offline projection, before Phase 4):**

- The fixed denominator is the B1 slots not admitted in that stored-data projection: **37,614 − 23,761 = 13,853**.
- *Prediction:* the live Phase 4 run admits at least **50% (6,927 slots)** of this fixed residual set.
- *Falsified if:* below **25% (3,463 slots)** of this residual set.
- `INVALID_ID` never counts as admitted. Report H1b separately from H1; the existing H1 thresholds and B1/B2 remain unchanged.

**H2 — verdict coverage (pre-registered in the roadmap; unchanged):**

- A yes/no verdict means **PASS or FAIL (primary)**. Report a clearly labelled **secondary** count that also includes `REGRESSION_ERROR`; it does not replace the primary count.
- *Prediction:* under Policy C, at least **50/83** tasks get a yes/no verdict.
- *Falsified if:* under **42/83**. That equals the parser-only projection, so falsification means execution repair adds nothing beyond parsing.

**H3 — strict coverage (descriptive, no pass/fail):**

- Report Policy S yes/no verdicts against B2.
- Report remaining skips by reason group, with a separate line for CPU-conditioned tests.

**Integrity rules:**

- Any original native FAIL that disappears without an explained cause halts the analysis as an executor bug.
- A cap hit is reported, never silently retried.

## 5. Post-hoc, only after `phase4-run-sealed`

These may use labels; the executor never changes in response:

- FAIL and REGRESSION_ERROR on incorrect and correct patches, with exact 95% intervals;
- outcomes of the 7 grader-failing pre-existing tests and the 6 known regression tests;
- the 4 incorrect patches among the 13 skip-dependent PASS tasks: their verdicts under C and S;
- the 2 pylint tasks: what the 38 CPU-conditioned tests did once they ran.

## 6. Cost and stopping rule

- **Engineering estimate:** 5–7 working days for fixes 0–8.
- **Run estimate:** 3–8 h. Stop and report partial accounting at 12 h.
- **One run only.** Any later executor change is a new version, reported as exploratory.
