# Phase 3 Part F: fixes from the Phase 6 dev gold review (amendments A6–A8)

The three fixes come from the read-only review of the sealed Phase 6 run (`runs/study_dev_gold`). Their rules are amendment items A6–A8 in [AMENDMENT_2026-11-21.md](../AMENDMENT_2026-11-21.md). Nothing listed in [V4_FREEZE.md](../V4_FREEZE.md) changed: `git diff study-v4-frozen` is empty for `configs/` and the four `reproduction*.py` files. r6b needs no config change, because a switch missing from `v1_5.yaml` reads as off. Every change started with a failing test. No labels were opened, and no test-set data exists.

Code commit: `c15825831aee8c866440ac45dffb2419e5331084`. The step 4 re-verification ran at tag `study-dev-gold-f-launch`, which points at that commit.

## 1. V3 pre-existing failures (A6)

`static_v1_4.paired_v3(checks, added_paths)` decides each syntax or import check:
- **FAIL:** the check failed on the patched tree, and base either passes, fails with a different final exception type, or fails in a different file.
- **PRE_EXISTING:** base fails with the same exception type in the same file.
- **BASE_UNKNOWN:** an import failure in a module the patch adds or renames to. A syntax error in such a module is always FAIL.
- **FAIL_BASE_UNKNOWN:** the check failed and no base result is stored, so the failure is kept.

Only FAIL and FAIL_BASE_UNKNOWN count as a V3 failure. PRE_EXISTING and BASE_UNKNOWN are V3 not available for that check. If a failure can't be attributed to a file, it is pre-existing only when no check target is patch-added. A stored summary FAIL with no check record to pair stays a failure.

Where it applies:
- **Live V3:** now also runs the syntax check on base when it fails on the patched tree. It records `v3_paired` and `patch_added_paths` beside the unchanged `v3_absolute_failure` and summary.
- **v1.5 evidence:** `policy_v1_5.evidence_from_signals` recomputes the flag from the stored base and patched checks. `decide_v1_5.py` passes in the added files from each task's sealed `patch.diff`, and writes `v3_pre_existing` and `v3_base_unknown` columns. A patch the parser rejects counts as adding no files; V1 already marks such a patch unparseable, so R1 rejects it. Live runs and `decide_v1_5.py` therefore use the same function on the same stored results.
- **v1.4.1:** its V3 evidence and live decisions are unchanged, so the v1.4.1 replay still matches.

## 2. V2 paired collection errors (A7)

In `run_v1_4_1._run_v2`, if both trees fail run-health (G1) only because of per-module native collection errors, and the module → exception type map is the same on both trees, then:
- those modules' tests are removed from the selection (and from the fallback tests);
- G1 runs again on the reduced selection, in `g1_after_paired_exclusion/`, logged in `health.jsonl` with scope `G1_after_paired_exclusion`;
- V2 runs on the rest, and its findings record `paired_collection_exclusions` (module, exception type, excluded tests, trees).

The exception type comes from pytest's `E   Type:` lines, or from a `Type: message` line after a Python traceback. A runner that prints and exits without a traceback has no type and still blocks. A collection error on only one tree, different types, any other kind of blocking stage, a failed generic-rule pair, or no module left all keep today's behaviour: V2 NOT_AVAILABLE with absence error.

One existing test changed its expected result. `test_g1_paired_rule_controls_real_v2` has two cases where the GIS module aborts with `SystemExit` on both trees: a non-matching message on Django, and the GIS message on a non-Django repo. Before A7 these blocked, because only the GIS guard rule could unblock a module. Under A7 they are excluded and recorded, and the test now asserts that.

## 3. Switch r6b (A8)

New switch `r6b_accept_one_uncovered`, default off, with rule R6b (ACCEPT) between R6 and R7. R6b fires only when all of these hold:
- The ACCEPT conditions of v1.4.1 hold with V4 treated as a pass: V1 PASS with analysis complete, no V3 failure, no high-severity risk flag.
- V2 is PASS.
- The V4 is per-requirement and NOT_AVAILABLE, with exactly one requirement UNCOVERED, at least one PASS, none failing and none NO_RESULT.

I added the at-least-one-PASS condition: with no covered requirement there is no V4 evidence at all.

`EvidenceV15` gains `v4_uncovered_units` and `v4_no_result_units`. `decide_v1_5.py --switches` accepts an optional `r6b=0|1`. Output names add `_r6b-1` only when r6b is on, so existing file names are unchanged. Adoption in Phase 7 uses the same bar as R6's branch: at least 70% of the arm B patches it newly ACCEPTs must be correct. Arm B's V4 is legacy, so R6b cannot fire on arm B's stored old-V4 signals. Its Phase 7 effect will come from the re-verification with the new V4.

## 4. Re-verification of gold pytest-7236 and pytest-7521

`runs/study_dev_gold_f`:
- **Command:** `--mode audited --freeze-tag study-dev-gold-f-launch --reference-patches --reuse-v4-from runs/study_dev_gold`, with cap $2.373869516, the ledger total at launch.
- **Result:** status COMPLETE, seal MATCH over 105 files (sha256 `466d587160eac5f3a91357c932a88b07211295c2404a1718a3323f17ba7501f8`). The header shows git_dirty false.
- **V4 reuse:** 0 generator calls, 0 ledger calls, $0.00.
- **Folder:** made read-only after sealing.

| task | Phase 6 V2 | part F V2 | modules excluded (both trees, same type) | infrastructure flag |
|---|---|---|---|---|
| pytest-dev__pytest-7236 | NOT_AVAILABLE (error, RUN_HEALTH_G1) | NOT_AVAILABLE (incomplete) | `testing/example_scripts/issue_519.py` (UsageError, 2 tests), `testing/python/metafunc.py` (ModuleNotFoundError, 98), `testing/test_junitxml.py` (ModuleNotFoundError, 66) | yes → no |
| pytest-dev__pytest-7521 | NOT_AVAILABLE (error, RUN_HEALTH_G1) | NOT_AVAILABLE (incomplete) | `testing/python/metafunc.py` (ModuleNotFoundError, 98), `testing/test_junitxml.py` (ModuleNotFoundError, 66) | yes → no |

V2 now runs on both tasks and finds no failure in the tests that finished. It is incomplete only because of evidence gaps (skips and similar), with no patched-side timeout or crash. Both V4s stay full passes. In the live record both are still FLAG under v1.4.1, and they become ACCEPT (R6) only through the r6 switch.

## 5. Decisions under the three settings (label-free)

These come from `scripts/decide_v1_5.py`, with the A6 evidence, on the Phase 6 run with the two tasks taken from `runs/study_dev_gold_f`. Arm B uses its stored old-V4 signals, with V2 replayed under accounting P from the captured executions, as in parts D and E, plus the added files from its sealed patches. Fix 2 can't change arm B here: those are stored signals, and a V2 that G1 blocked has no captured run to replay. Machine-readable: [part_f_decisions.json](part_f_decisions.json).

### Gold (51 dev gold patches; pytest-7236 and pytest-7521 from runs/study_dev_gold_f)

| setting | ACCEPT | FLAG | REJECT | rules |
|---|---:|---:|---:|---|
| switches off | 25 | 26 | 0 | R4 5, R5 6, R6 25, R7 6, R8 9 |
| all on (r2, r3, r6, r6b) | 37 | 11 | 3 | R3 3, R4 2, R5 6, R6 33, R6b 4, R7 2, R8 1 |
| r2, r6, r6b on (r3 off) | 37 | 14 | 0 | R4 5, R5 6, R6 33, R6b 4, R7 2, R8 1 |

### Arm B (51 patches, old-V4 signals, V2 replayed under accounting P)

| setting | ACCEPT | FLAG | REJECT | rules |
|---|---:|---:|---:|---|
| switches off | 20 | 27 | 4 | R1 2, R3 2, R4 8, R5 7, R6 20, R7 1, R8 11 |
| all on (r2, r3, r6, r6b) | 27 | 13 | 11 | R1 2, R2 2, R3 7, R4 3, R5 7, R6 27, R7 1, R8 2 |
| r2, r6, r6b on (r3 off) | 27 | 18 | 6 | R1 2, R2 2, R3 2, R4 8, R5 7, R6 27, R7 1, R8 2 |

### Decisions changed by fix 1 (A6) or fix 2 (A7)

Fix 1 rows compare the same evidence with and without the A6 V3 rule. Fix 2 rows compare the Phase 6 record with the part F re-verification (both with A6).

| instance_id | set | setting | before | after | why |
|---|---|---|---|---|---|
| django__django-16631 | gold, fix 1 | switches off | FLAG/R8 | FLAG/R7 | V3 pre-existing: import; base-unknown: – |
| django__django-16631 | gold, fix 1 | all on (r2, r3, r6, r6b) | REJECT/R2 | FLAG/R7 | V3 pre-existing: import; base-unknown: – |
| django__django-16631 | gold, fix 1 | r2, r6, r6b on (r3 off) | REJECT/R2 | FLAG/R7 | V3 pre-existing: import; base-unknown: – |
| matplotlib__matplotlib-23476 | arm B, fix 1 | all on (r2, r3, r6, r6b) | REJECT/R2 | REJECT/R3 | V3 pre-existing: import; base-unknown: – |
| matplotlib__matplotlib-23476 | arm B, fix 1 | r2, r6, r6b on (r3 off) | REJECT/R2 | FLAG/R4 | V3 pre-existing: import; base-unknown: – |
| pytest-dev__pytest-7236 | gold, fix 2 | all on (r2, r3, r6, r6b) | FLAG/R8 | ACCEPT/R6 | V2 NOT_AVAILABLE (error) -> NOT_AVAILABLE (incomplete); excluded: testing/example_scripts/issue_519.py (_pytest.config.exceptions.UsageError, 2 tests); testing/python/metafunc.py (ModuleNotFoundError, 98 tests); testing/test_junitxml.py (ModuleNotFoundError, 66 tests) |
| pytest-dev__pytest-7236 | gold, fix 2 | r2, r6, r6b on (r3 off) | FLAG/R8 | ACCEPT/R6 | V2 NOT_AVAILABLE (error) -> NOT_AVAILABLE (incomplete); excluded: testing/example_scripts/issue_519.py (_pytest.config.exceptions.UsageError, 2 tests); testing/python/metafunc.py (ModuleNotFoundError, 98 tests); testing/test_junitxml.py (ModuleNotFoundError, 66 tests) |
| pytest-dev__pytest-7521 | gold, fix 2 | all on (r2, r3, r6, r6b) | FLAG/R8 | ACCEPT/R6 | V2 NOT_AVAILABLE (error) -> NOT_AVAILABLE (incomplete); excluded: testing/python/metafunc.py (ModuleNotFoundError, 98 tests); testing/test_junitxml.py (ModuleNotFoundError, 66 tests) |
| pytest-dev__pytest-7521 | gold, fix 2 | r2, r6, r6b on (r3 off) | FLAG/R8 | ACCEPT/R6 | V2 NOT_AVAILABLE (error) -> NOT_AVAILABLE (incomplete); excluded: testing/python/metafunc.py (ModuleNotFoundError, 98 tests); testing/test_junitxml.py (ModuleNotFoundError, 66 tests) |

### Per-task gold decisions

| instance_id | V2 | V3 failure | switches off | all on (r2, r3, r6, r6b) | r2, r6, r6b on (r3 off) |
|---|---|---|---|---|---|
| astropy__astropy-13398 | NOT_AVAILABLE | no | FLAG/R4 | REJECT/R3 | FLAG/R4 |
| astropy__astropy-14365 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| astropy__astropy-14508 | NOT_AVAILABLE | no | FLAG/R7 | FLAG/R7 | FLAG/R7 |
| astropy__astropy-7606 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| django__django-11095 | NOT_AVAILABLE | no | FLAG/R8 | FLAG/R8 | FLAG/R8 |
| django__django-12965 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| django__django-13023 | NOT_AVAILABLE | no | FLAG/R8 | ACCEPT/R6 | ACCEPT/R6 |
| django__django-13158 | NOT_AVAILABLE | no | FLAG/R8 | ACCEPT/R6 | ACCEPT/R6 |
| django__django-13212 | NOT_AVAILABLE | no | FLAG/R4 | FLAG/R4 | FLAG/R4 |
| django__django-13297 | PASS | no | FLAG/R4 | REJECT/R3 | FLAG/R4 |
| django__django-13786 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| django__django-13807 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| django__django-13820 | PASS | no | FLAG/R7 | ACCEPT/R6b | ACCEPT/R6b |
| django__django-14140 | FAIL | no | FLAG/R5 | FLAG/R5 | FLAG/R5 |
| django__django-15103 | PASS | no | FLAG/R7 | ACCEPT/R6b | ACCEPT/R6b |
| django__django-15278 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| django__django-15499 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| django__django-15572 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| django__django-16082 | NOT_AVAILABLE | no | FLAG/R8 | ACCEPT/R6 | ACCEPT/R6 |
| django__django-16255 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| django__django-16612 | NOT_AVAILABLE | no | FLAG/R8 | ACCEPT/R6 | ACCEPT/R6 |
| django__django-16631 | PASS | no (pre-existing: import) | FLAG/R7 | FLAG/R7 | FLAG/R7 |
| django__django-16667 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| matplotlib__matplotlib-20488 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| matplotlib__matplotlib-22871 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| matplotlib__matplotlib-23476 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| matplotlib__matplotlib-24026 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| matplotlib__matplotlib-24627 | NOT_AVAILABLE | no | FLAG/R4 | FLAG/R4 | FLAG/R4 |
| matplotlib__matplotlib-24637 | FAIL | no | FLAG/R5 | FLAG/R5 | FLAG/R5 |
| matplotlib__matplotlib-24970 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| matplotlib__matplotlib-25122 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| matplotlib__matplotlib-25287 | PASS | no | FLAG/R7 | ACCEPT/R6b | ACCEPT/R6b |
| matplotlib__matplotlib-25332 | FAIL | no | FLAG/R5 | FLAG/R5 | FLAG/R5 |
| matplotlib__matplotlib-25479 | FAIL | no | FLAG/R5 | FLAG/R5 | FLAG/R5 |
| matplotlib__matplotlib-26291 | FAIL | no | FLAG/R5 | FLAG/R5 | FLAG/R5 |
| pydata__xarray-6744 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| pylint-dev__pylint-6903 | NOT_AVAILABLE | no | FLAG/R8 | ACCEPT/R6 | ACCEPT/R6 |
| pylint-dev__pylint-7277 | PASS | no | FLAG/R7 | ACCEPT/R6b | ACCEPT/R6b |
| pytest-dev__pytest-5809 | FAIL | no | FLAG/R5 | FLAG/R5 | FLAG/R5 |
| pytest-dev__pytest-6202 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| pytest-dev__pytest-7236 | NOT_AVAILABLE | no | FLAG/R8 | ACCEPT/R6 | ACCEPT/R6 |
| pytest-dev__pytest-7432 | PASS | no | FLAG/R4 | REJECT/R3 | FLAG/R4 |
| pytest-dev__pytest-7521 | NOT_AVAILABLE | no | FLAG/R8 | ACCEPT/R6 | ACCEPT/R6 |
| scikit-learn__scikit-learn-10908 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| scikit-learn__scikit-learn-12585 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| scikit-learn__scikit-learn-14141 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| sphinx-doc__sphinx-10323 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| sphinx-doc__sphinx-10466 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| sphinx-doc__sphinx-7910 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |
| sympy__sympy-13480 | NOT_AVAILABLE | no | FLAG/R8 | ACCEPT/R6 | ACCEPT/R6 |
| sympy__sympy-19783 | PASS | no | ACCEPT/R6 | ACCEPT/R6 | ACCEPT/R6 |

Notes on these tables:
- **Switches off:** gold has 0 REJECT. django-16631 moves from R8 to R7 because its V3 import failure is pre-existing. Arm B with switches off still equals `decision_P_invalid_excluded` on 51/51 tasks.
- **Gold all-on REJECTs:** all 3 come from extended R3 (astropy-13398, django-13297, pytest-7432). There is no R2 gold REJECT any more.
- **r6b:** it ACCEPTs 4 gold patches (django-13820, django-15103, matplotlib-25287, pylint-7277). The fifth gold patch with one uncovered requirement, astropy-14508, has V2 nothing-to-check, so it doesn't qualify.
- **Fix 1 on arm B:** it changes only matplotlib-23476, whose import failure is pre-existing. With all switches on it is still REJECT, through extended R3 instead of R2. With r3 off it becomes FLAG (R4) instead of an R2 REJECT. Arm B's other R2 REJECTs (django-14140, sphinx-10323) have a base that passes, so they are real V3 failures.

## 6. Gates

- **Unit gate:** 1,947 passed, 6 skipped, 6 failed, 17 errors (`runs/study_v1_5/unit_part_f_final.log`), after the last code change. The failing and erroring IDs equal `unit_baseline_phase1.json`. The code commit's own run had 1,946 passed; the one extra pass is the test for unparseable patches.
- **Truth table:** the main table is unchanged (17,280 cases). With switches off, v1.5 differs from v1.4.1 in exactly the 16 A4 (ii) cases. r6b is tested on a separate per-requirement table of 20,736 cases with the uncovered and NO_RESULT counts, under all 8 settings of the other three switches:
  - With r6b off, decisions don't depend on those counts, and turning r6b on changes nothing in the main table.
  - With r6b on, decisions change only to R6b ACCEPT, from R7 FLAG, and only for cases that meet every R6b condition.
- **v1.4.1 replay:** "PASS: full_v1_4_1.yaml matched 51/51 stored decisions" and "PASS: v1_5.yaml matched 51/51 label-free P_invalid_excluded V2 outcomes". The v1.5 switches-off step still matched 51/51 `decision_P_invalid_excluded`. Its three-switch all-on diff is still 14 tasks; only matplotlib-23476's rule changes, from R2 to R3 (`part_d_armB_all_switches.csv`).
