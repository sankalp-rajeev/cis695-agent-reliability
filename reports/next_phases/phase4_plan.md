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
- **Integrity stop:** the attempt is aborted and documented. Any fix must be label-free, becomes a new executor version with a new freeze tag, and the run restarts from task 1. An old freeze tag is never moved.
- **Attempt 1 quarantine:** the 35-task attempt is **aborted, not analyzed**. Its captures are retained with a hash manifest; none of its outcomes may inform any fix or analysis.
- **Proven SWE-bench pre_install edits (Fix 10):** the project stays pinned to `swebench==5.0.2`, which has no `pre_install` specifications. Use an isolated downloaded `swebench==4.0.4` wheel; record its SHA-256 and PyPI URL. Parse its constants source without importing SWE-bench into the verifier, reading only `MAP_REPO_VERSION_TO_SPECS[repo][version]["pre_install"]`; a missing required spec halts. Read only `instance_id`, `repo`, `base_commit` and `version` from the project's pinned SWE-bench Verified dataset snapshot and record its hash. In each affected pristine image, pinned by frozen image ID, read its own repository/environment build script if present (for example `/root/setup_repo.sh` or `/root/setup_env.sh`), extract its repository pre_install commands and require exact equality with the snapshot's ordered list; disagreement halts. If no such script exists, accept the snapshot alone and record "no image script". Accept an image/archive difference only if the archive file equals the base blob AND the image file equals that blob after applying those exact commands in order in an isolated temporary directory, never to the image. Any other difference halts; there are no blanket file exemptions. The separately proven export-subst rule remains in force.
- **Generated, untracked version modules:** hash before and after each runtime stage. Any change sets `GENERATED_INPUT_CHANGED` on that task's evidence and is reported; it does not halt the run.

### Attempt-2 quarantine and run-health guards (before Fix 11/12)

Attempt 2 is quarantined: its hashes and captures are kept, **"aborted at integrity gate, not analyzed"**. None of its test outcomes, verdicts or aggregate metrics may inform a fix or analysis. Executor-health-only collection receipts and frozen source metadata may be inspected; correctness labels remain unopened. This adds guards without changing H1/H1b/H2/H3, thresholds, B1 or B2.

- **G1 — exhaustive stage preflight:** every task × tree runs a fresh pristine-source check, patch application on the patched tree, native collection and runner start-up, with **zero test bodies**. G1 runs all **166 task/tree pairs without stopping at the first failure**, records every failure, and evaluates the launch gate **only at the end**. Fail-fast applies to the controlled run only. Launch only after all stages succeed or fail solely for the exact pre-listed exceptions below. Unexpected collector failure remains a preflight failure even if fallback candidates exist. Native collection is not called test admission.
- **G2 — admission monotonicity:** for each task/tree, every selected ID with an admitted outcome in the frozen original V2 run must have an admitted outcome now, unless proven INVALID_ID. Compute admission only, never PASS/FAIL. Halt if a task/tree loses **>= 10 such IDs OR >= 1% of them**. An empty reference set has no percentage loss. All members of an expanded slot must be admitted; expansion never adds a family. The reference is the original frozen run, not either quarantined attempt or the Fix 5 projection.
- **G3 — zero-output halt:** any stage with nonzero input and zero collected/admitted output halts unless its exact task/module/stage/cause matches the pre-listed exception list. Empty input and all-proven-invalid input have explicit statuses, not a silent empty result. Fallback candidates are reported separately from successfully collected identities.
- **G4 — live health:** after each task, write and flush a record to `health.jsonl` containing explicit collector/stage status, admitted share and G2/G3 checks. Evaluate and persist a halt immediately, before starting the next task. Health records contain admission only, never test outcome classes or verdicts.
- **G5 — deterministic order:** first cover every effective `(runner, repo, version)` combination once, choosing the lowest instance_id for each combination and sorting representatives by instance_id; append all remaining tasks in their original frozen order. Publish this order before launch. Native SymPy is its own runner combination.
- **G6 — containment:** a failed collector may fall back only to statically validated IDs from the same selection, under module isolation and marked `COLLECTOR_FALLBACK`; retain the primary collector error and count fallback identities separately. Do not fall back on static unknowns, proven invalid IDs, exhausted budgets or the pre-listed missing-evidence exceptions. Every stage reports an explicit status and input/output counts; no stage silently returns an empty result.
- **Pre-listed exceptions, fixed before code:** (1) **GIS_GUARD**: only frozen Django `tests/gis_tests/**` modules, with the exact diagnostic `A GIS database backend is required to run gis_tests`, at native collection/module execution; (2) **XMLSCHEMA_MISSING**: only `pytest-dev__pytest-5787`, `testing/test_junitxml.py`, with `No module named 'xmlschema'`, at native collection/module execution. Both trees are covered. Exact task/module scopes are enumerated in `phase4_rerun/fix11_12_scope/run_health_exceptions.json`. There are no blanket task, repository, nonzero-exit or import-failure exemptions. These exceptions remain missing evidence, never admitted; they do not relax G2.
- **Any health halt follows the integrity-stop rule:** abort and document; any fix is label-free, requires a new executor version and a new freeze tag, and restarts from task 1. Old tags are never moved.

### Module-level collection skips (before Fix 13)

- **Native evidence required:** if a module collects zero items AND the native collector records a module-level skip for that module with a reason (`pytest -rs` SKIPPED line, or the native Django/SymPy equivalent), every selected ID in that module becomes **SKIPPED**, reason `module_skip: <reason>`. A package-initialization skip must be tied by the native collector to the affected module. Static importorskip statements or missing packages alone never synthesize an outcome.
- This is a recorded outcome, handled by Policy C and Policy S exactly like ordinary SKIPPED and grouped by its recorded reason. It is neither INVALID_ID nor a new test family. **G3 does not fire for a recorded module skip.** Zero items with no recorded module skip remains COLLECTION_ERROR and triggers G3.
- **G2 module-skip compatibility:** a module-skipped ID counts as admitted only when its frozen original-run reference is SKIPPED or absent. If the original run admitted PASS/FAIL/ERROR for it, it counts as lost. Other present admitted evidence such as XFAIL/XPASS is not silently converted into a skip-compatible reference. The reference is derived from the frozen original run only; quarantined attempts and correctness labels remain excluded.
- G1 is exhaustive even after unlisted failures; the launch gate remains closed if any unlisted failure remains at the end. No exception list, hypothesis threshold, B1 or B2 changes with this amendment.

### Identity normalization and review fixes (before Fix 14)

This amendment supersedes conflicting G2 and module-skip wording above. H1,
H1b, H2, H3, all thresholds, B1 (37,614), and B2 remain unchanged. Attempt-2
outcomes, verdicts and correctness labels remain quarantined. Collection-only
diagnosis is in `phase4_rerun/fix14_diagnosis/`.

1. Normalize pytest node IDs by removing `::()::` instance segments and a
   trailing `::()` in collection and execution result mapping. Preserve the
   parameter payload, including non-ASCII text, and the frozen selected IDs.
2. Native collection is authoritative: send every selected ID, including
   statically rejected IDs, to native collection, alongside any same-family
   expansions. INVALID_ID requires agreement between static and native layers.
   An originally admitted reference ID now INVALID_ID is LOST in G2; the same
   applies to an expanded slot. Static rejection never exempts reference loss.
3. For a tree with empty original reference and non-empty selection, use the
   G1 natively collected set as its G2 reference, projected unanimously to the
   frozen selected slots. Retain concrete collection identities in the receipt.
4. Run G3 and G2 inside every confirmation call, before returning it to scoring.
   Compare G2 with the corresponding initial run's admitted subset for that
   confirmation selection, including expanded slots. Persist a halt immediately.
5. Exclude COLLECTOR_FALLBACK slots from G2's admitted set and admitted share,
   even if their execution emits terminal outcomes; report them separately.
6. Remove natively proven-absent IDs from G3 input_count only after both layers
   agree under rule 2. A module whose inputs are all proven absent reports
   ALL_PROVEN_INVALID and does not halt; retain original and excluded counts.
7. A reference ID admitted as PASS/FAIL/ERROR that is now SKIPPED for any reason
   counts as lost in G2. Preserve the existing stricter XFAIL/XPASS skip guard.
8. A native module skip covers every selected ID inside the module, including
   statically rejected IDs: each becomes MODULE_SKIPPED, never INVALID_ID.
9. SymPy module-level `disabled` true, as honored by that task's own runner,
   is a native module-level skip with reason `module_skip: disabled`.
10. INVALID_ID (`not_a_test_module`) requires native collection of the containing
    directory under the effective repository config to exclude the file. Do not
    attempt its explicit-file import. Config guesses alone are insufficient.
11. Add a genuine module-import exception only for the exact task, module,
    stage and diagnostic reproduced with SWE-bench's command form; it remains
    missing evidence. For matplotlib-23476, repository-root `pytest -rA
    --collect-only lib/matplotlib/tests/test_backend_bases.py` reproduces
    `AttributeError: module 'matplotlib.testing' has no attribute 'compare'`;
    collecting `lib/matplotlib/tests` succeeds. The exception is restricted to
    that explicit module at native_collection/module_execution, on both trees.
    Directory success grants no blanket task exemption or new admitted IDs.
12. G1 records per-pair filesystem/write failures and BaseException, continues
    through all 83 × 2 pairs, and evaluates the gate only after the complete audit.

Diagnosis: all 52 frozen pytest-run images were queried with `pip show pytest`.
Only astropy-7606 has pytest < 4.0 (3.3.1); five SymPy images have no pytest and
use native bin/test. Astropy raw item.nodeid includes `::()::`, absent from -q
stdout, affecting 536 base selected slots (1,078 raw collected instances).
SymPy-13480 sets disabled on missing Sage and on Python 3; its native
`SymPyTests.test_file` checks `gl.get("disabled", False)` before function
collection. Pylint-4970 uses python_files `*test_*.py`, testpaths `tests`, and
native `tests/functional` directory collection excludes
`consider_using_with_open.py`. No benchmark test bodies were read or executed.

### Reference hygiene, confirmation loss and G1-collected guard (before Fix 15)

This amendment supersedes conflicting Fix 14 guard wording. All H1/H1b/H2/H3
thresholds, B1 (37,614), B2, frozen selections and the original reference
provenance remain unchanged. Attempt-2 outcomes, verdicts and labels remain unread.

1. Remove a frozen-reference ID only with native containing-directory proof of
   `not_a_test_module` under rule 10. Its historical explicit-file import was
   spurious admission. Publish the exact exclusions and their directory receipts.
   The existing receipts identify 16 unique IDs in pylint-4970's
   `tests/functional/c/consider/consider_using_with.py`, on both trees (32 tree-ID
   slots). No other reference removal is permitted; ordinary INVALID_ID remains
   a loss, including expanded slots. Remove these same IDs from skip-blocking
   reference sets so they cannot be reintroduced by skip accounting.
2. G1 projects G2 for every task/tree from its native receipts against the cleaned
   frozen reference. An ID is potentially admitted only with native collection
   or a compatible native module skip; fallback is excluded. Any projected halt
   blocks the launch gate. All 166 pairs still run before gate evaluation.
3. Confirmation G2 counts identity loss only: COLLECTION_ERROR, INVALID_ID,
   NOT_RUN, RUNNER_UNAVAILABLE, missing/unmatched identities, and collector
   fallback. ERROR or TIMEOUT in any confirmation makes its candidate FLAKY,
   even if all patched confirmations consistently return ERROR; it never causes
   a health halt. Native collection/start-up failures remain identity failures.
   G3 must not reinterpret terminal ERROR/TIMEOUT execution/admission output as
   zero identity output. Preserve the missing/unstable evidence in the record.
4. Every tree also checks identity loss against its G1 natively collected valid
   set, unanimously projected to frozen slots and excluding fallback/module skips.
   Apply the unchanged >= 10 OR >= 1% loss thresholds. NOT_REACHED and TIMEOUT
   remain reported budget gaps, never identity loss; they are H1b's missing
   evidence. For the 16 empty-original-reference trees this identity-only G1 rule
   replaces Fix 14's full-admission-loss fallback. Non-empty original references
   retain their existing full-admission G2 rule and stronger-reference skip rule.
   Confirmation calls check the corresponding G1 subset as well as the initial
   run's admitted subset. Execution/admission G3 accounting reports budget-only
   gaps without creating a zero-output halt in these identity-only checks.
5. The launcher verifies the G1 manifest's SHA-256 from phase4_plan.md as stored
   in the committed freeze HEAD, before starting a container. An unset/mismatched
   anchor fails closed. The plan is excluded from the G1 source manifest to avoid
   a circular hash; the freeze commit binds the plan and manifest together.
6. Normalize pytest instance segments in timeout attribution (`_active_test`),
   preserving parameter payloads and the original selected identity.
7. G1 records KeyboardInterrupt/SystemExit per pair and re-raises them, including
   recording failures encountered while persisting the interruption. Other
   per-pair filesystem errors and BaseException remain contained and recorded.
8. Pre-registered exceptions match exact task, tree, module, stage and diagnostic.
   Apply native_collection and module_execution independently. A collection-stage
   allowance does not authorize an execution-stage allowance. Both remain missing
   evidence; neither relaxes G2 or the G1-collected identity guard.

The 16 excluded identities (the same list applies to base and patched) are:

- `tests/functional/c/consider/consider_using_with.py::test_codecs_open`
- `tests/functional/c/consider/consider_using_with.py::test_futures`
- `tests/functional/c/consider/consider_using_with.py::test_lock_acquisition`
- `tests/functional/c/consider/consider_using_with.py::test_lock_acquisition_in_context_manager1`
- `tests/functional/c/consider/consider_using_with.py::test_multiprocessing`
- `tests/functional/c/consider/consider_using_with.py::test_named_temporary_file`
- `tests/functional/c/consider/consider_using_with.py::test_popen`
- `tests/functional/c/consider/consider_using_with.py::test_pyzipfile`
- `tests/functional/c/consider/consider_using_with.py::test_spooled_temporary_file`
- `tests/functional/c/consider/consider_using_with.py::test_subscript_assignment`
- `tests/functional/c/consider/consider_using_with.py::test_suppress_in_exit_stack`
- `tests/functional/c/consider/consider_using_with.py::test_tarfile`
- `tests/functional/c/consider/consider_using_with.py::test_temporary_directory`
- `tests/functional/c/consider/consider_using_with.py::test_temporary_file`
- `tests/functional/c/consider/consider_using_with.py::test_urlopen`
- `tests/functional/c/consider/consider_using_with.py::test_zipfile`

Fix 15 G1 manifest SHA-256: 2db4cbc30a2bcaa83df4dd5ec59b6477910ef56f299a5aa74c6a70bcdee2f377

## 5. Post-hoc, only after `phase4-run-sealed`

These may use labels; the executor never changes in response:

- FAIL and REGRESSION_ERROR on incorrect and correct patches, with exact 95% intervals;
- outcomes of the 7 grader-failing pre-existing tests and the 6 known regression tests;
- the 4 incorrect patches among the 13 skip-dependent PASS tasks: their verdicts under C and S;
- the 2 pylint tasks: what the 38 CPU-conditioned tests did once they ran.

## 6. Cost and stopping rule

- **Concurrency:** serial (one container at a time), chosen so container contention cannot alter timing, timeouts or NOT_REACHED counts. Estimated 4.08-4.86 h plus confirmation runs; the 12 h stop rule applies.
- **Engineering estimate:** 5–7 working days for fixes 0–8.
- **Run estimate:** 3–8 h. Stop and report partial accounting at 12 h.
- **One run per frozen executor version.** An integrity-aborted attempt is quarantined under the rule above; a label-free repair requires a new version and freeze tag, followed by a fresh run from task 1. Other later executor changes are reported as exploratory.
