# Phase 3 Part D

`src/reliability/verifier/policy_v1_5.py` adds `EvidenceV15`, which extends `EvidenceV14` with `v4_design`, `v4_full_pass`, `v4_fail_confirmed`, `v4_failing_units` and `v4_pass_units`. It also adds `FullPolicyV15` (`full-v1.5`, `v1.5.0-full`), which applies rules R1-R8 in PROTOCOL §4 order. Each decision records a `rule_id` and a `review_label` in `DecisionRecordV15`. There are three switches, all off by default: `r2_v3_reject`, `r3_extended_reject` and `r6_accept_v2_not_available`. The policy reuses v1.4.1 directly. R6 is v1.4.1's ACCEPT plus a V4 full pass. With `r6_accept_v2_not_available` on, a V2 NOT_AVAILABLE is treated as PASS when that check runs. R4, R5, R7 and R8 keep v1.4.1's reasons. An R3 REJECT from the extended part has reasons that start with `extended:`.

The adapter `evidence_from_signals()` reads the V4 findings written in Part B:

- **Per-requirement design:** the units come from `verdict_counts`, and FAIL-confirmed is counted only when the setup has two passes.
- **Legacy design:** units are kept tests, counted from their patched verdicts, and FAIL-confirmed is always 0.

The policy can be selected in two places:

- `decision.get_policy("full-v1.5")` imports it lazily, so `decision.py` still imports no signal module.
- `policy_from_config()` reads `configs/verifier/v1_5.yaml`, which now sets `decision_policy: full-v1.5` and all three switches to `false`.

`full_v1_4_1.yaml` is unchanged. The runtime decision in `run_v1_4_1.py` is unchanged and still records v1.4.1. Study decisions are recomputed offline with the tool described next.

`scripts/decide_v1_5.py <sealed run> --switches r2=0|1,r3=0|1,r6=0|1 --output DIR` writes `decisions_v1_5_<switches>.csv` and `summary_v1_5_<switches>.json` without running anything again. It refuses a run in any of these cases:

- It has no `seal.json`, the seal is not COMPLETE, or its files differ from the seal inventory.
- The output folder is inside the run.
- Its path contains a name on the existing forbidden list (`e2e_input_preflight.FORBIDDEN_NAMES`), extended with the names in CLAUDE.md: `grading`, `per_instance_details`, `git_peek` and `decision_by_correctness`.

A run folder that contains "gold" is accepted only if its header records `reference_patches: true`. This matches the one exception PROTOCOL §4.7 allows, and it covers `runs/study_dev_gold`. The tool opens only the seal, `completion.json`, the header (for that gold check) and each task's verification record. Each of those files is checked against the forbidden names and its seal SHA-256 before it is opened.

As a check, the tool ran on the sealed Arm B run with all switches off and the run's stored V2 (accounting S). It reproduced 92 of 92 stored decisions, and the patch tasks came out ACCEPT/FLAG/REJECT = 5/42/4.

## Truth table

`tests/unit/test_policy_v1_5.py` enumerates **4,896 consistent cases**. The 288 combinations of integrity × V2 × patch_applies × prohibited × V3 × V1-incomplete × high-risk are crossed with 17 consistent V4 combinations (outcome, design, confirmed ∈ {0,1}, failing ∈ {0,1,2}, passing ∈ {0,1}). The table runs under all 8 switch settings. Each case must return exactly one decision and a `rule_id`, and that decision must be the one the rule prescribes. Combinations that cannot occur in a real record were skipped by this rule:

- V4 PASS has failing = 0, confirmed = 0 and passing ≥ 1, and `v4_full_pass` is true only for PASS.
- V4 FAIL has failing ≥ 1.
- V4 NOT_AVAILABLE has failing = 0, and under the legacy design it also has passing = 0, because one stable pass makes legacy V4 PASS.
- confirmed ≤ failing.
- The legacy design always has confirmed = 0.

With switches on, a decision may differ from v1.4.1 only in one of three ways: a FLAG becomes an R2 REJECT, a FLAG becomes an extended R3 REJECT, or a FLAG with V2 NOT_AVAILABLE becomes an R6 ACCEPT. The tests also cover each rule, plus these precedence cases:

- R1 is checked before R2, and R3 before R5.
- R3b fires for V2 FAIL with V4 NOT_AVAILABLE.
- R5 never REJECTs.
- R6 never fires with a V2 or V4 FAIL.
- With one-pass evidence, `v4_fail_confirmed` is 0 even if the record claims FAIL_CONFIRMED, so the result is R4, not R3.

`tests/unit/test_decide_v1_5.py` checks that the tool refuses label paths, an unsealed run, a run altered after its seal, and a gold-named run without the reference header.

## Gates

- **(a) Passed.** With switches off, the decision equals `FullPolicyV141` on **4,896 of 4,896** truth-table cases (`test_switches_off_equals_v1_4_1_on_every_case`; the cases were also counted directly: 4,896 equal out of 4,896).
- **(b) Passed.** `scripts/replay_paired_skip_arm_b.py primary-config` printed "Used 40 captured executions and 11 stored V2 absences", "PASS: full_v1_4_1.yaml matched 51/51 stored decisions" and "PASS: v1_5.yaml matched 51/51 label-free P_invalid_excluded V2 outcomes".
- **(c) Passed.** The new step `scripts/replay_paired_skip_arm_b.py policy-v1-5` ran `full-v1.5` on Arm B with V2 replayed under accounting P and the old (legacy) V4 evidence. The only label-free inputs were the stored records and captures and `reports/paired_skip/armB/decisions_label_free.csv`. With switches off, it matched `decision_P_invalid_excluded` on 51 of 51 tasks. With all switches on, **16** decisions differ (`part_d_armB_all_switches.csv`). There are 7 new REJECTs, all from R2 or the extended R3, and 9 new ACCEPTs, all from R6:

  | Task | P (v1.4.1) | All on | Rule |
  |---|---|---|---|
  | django__django-12965 | FLAG | REJECT | R3 extended: 3 failing V4 units |
  | django__django-13297 | FLAG | REJECT | R3 extended: 3 failing V4 units |
  | matplotlib__matplotlib-25122 | FLAG | REJECT | R3 extended: 2 failing V4 units |
  | matplotlib__matplotlib-26291 | FLAG | REJECT | R3 extended: 2 failing V4 units |
  | django__django-14140 | FLAG | REJECT | R2 (v3_absolute_failure) |
  | matplotlib__matplotlib-23476 | FLAG | REJECT | R2 (v3_absolute_failure) |
  | sphinx-doc__sphinx-10323 | FLAG | REJECT | R2 (v3_absolute_failure) |
  | astropy__astropy-13398 | FLAG | ACCEPT | R6 (V2 NOT_AVAILABLE) |
  | astropy__astropy-14508 | FLAG | ACCEPT | R6 (V2 NOT_AVAILABLE) |
  | django__django-11095 | FLAG | ACCEPT | R6 (V2 NOT_AVAILABLE) |
  | django__django-15499 | FLAG | ACCEPT | R6 (V2 NOT_AVAILABLE) |
  | django__django-16082 | FLAG | ACCEPT | R6 (V2 NOT_AVAILABLE) |
  | matplotlib__matplotlib-24627 | FLAG | ACCEPT | R6 (V2 NOT_AVAILABLE) |
  | pylint-dev__pylint-6903 | FLAG | ACCEPT | R6 (V2 NOT_AVAILABLE) |
  | pytest-dev__pytest-7236 | FLAG | ACCEPT | R6 (V2 NOT_AVAILABLE) |
  | sympy__sympy-13480 | FLAG | ACCEPT | R6 (V2 NOT_AVAILABLE) |

  Under the legacy design a unit is a kept test, so "2+ failing units" here means 2+ failing tests, not requirements. The log is `runs/study_v1_5/part_d_gate_c.log` (SHA-256 `120df62ee8d103170c26999ed87f24f6103fe8eb9133c78a0adbaad7f906fe5d`). The CSV SHA-256 is `167f9e4c06bbcec5405c7128a600ecd4b8550f5afd2c8e322e7e9b16578e4d03`.
- **(d) Passed.** The full offline `tests/unit` suite had 1,824 passed, 6 skipped, 6 failed and 17 setup errors, counted from the progress markers because the repo's `addopts = "-q"` combined with `-q` hides the summary line. That is Part C's 1,755 plus the 69 new tests. Every failure and error ID matched `unit_baseline_phase1.json`, with zero new issues. The log is `runs/study_v1_5/unit_part_d.log` (SHA-256 `db43f419155d63d47a2b6be0e92be74f88d66fc45dea07a28e02dd96c6755141`).

No Docker runs, model calls or label files were used.

## Note for Phase 7

The extended R3 conditions are applied as written: confirmed ≥ 1 or failing ≥ 2, not limited to V4 FAIL. In a real record, failing units without a V4 FAIL can occur in only one case: per-requirement V4 where some frozen bytes could not be placed (`FROZEN_BYTES_NOT_IN_PLACE`, which gives V4 NOT_AVAILABLE) while other tests still failed. The truth table treats this as inconsistent. If it shows up in the dev runs, the `decide_v1_5.py` CSV will show it as an R3 REJECT with V4 NOT_AVAILABLE.
