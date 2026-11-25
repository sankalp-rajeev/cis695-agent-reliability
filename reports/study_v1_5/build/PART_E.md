# Phase 3 Part E: code for amendment A3 and A4 (ii), (iii), (v)

This is the code for [AMENDMENT_2026-11-21.md](../AMENDMENT_2026-11-21.md) items A3, A4 (ii), A4 (iii) and A4 (v). Nothing was run apart from unit tests, read-only audits of the two sealed pilots and the offline replays. There were no model calls and no labels were opened.

Nothing listed in [V4_FREEZE.md](../V4_FREEZE.md) changed: `git diff study-v4-frozen` is empty for `configs/` and the four `reproduction*.py` files. The only changed files are `src/reliability/benchmark/leakage.py`, `scripts/audit_leakage.py`, `src/reliability/verifier/policy_v1_5.py`, `scripts/decide_v1_5.py`, three test files and `reports/study_v1_5/`. Every change started with a failing test.

## 1. A3: reference-run leakage audit

`leakage._reference_findings` now applies the pilot 2 first-appearance method to every reference (gold-patch) run.

- **Unit.** The unit of judgement is one conversation and one distinct gold line. The first message in that conversation containing the line decides the result.
- **Model-written text.** This is an assistant message's `content`, `reasoning_content` and tool-call `arguments`. Nothing else counts, including the `extra` copy of the provider response.
- **GENERATOR_RECALL.** The first appearance is in model-written text. This has the new severity `recorded`, which does not fail.
- **Pass prompts.** These are the messages before a conversation's first assistant turn. A line there counts as model-written only if it is in that V4 folder's `requirements.json` and was GENERATOR_RECALL in the same folder's requirements conversation.
- **GOLD_LINE_LEAK.** The first appearance is anywhere else: a tool output, a later user message, a system or user prompt, or only in an assistant's `extra`. This is `confirmed` and fails.
- **GOLD_LINE_IN_FROZEN_TEST.** Every kept test in `frozen.json` is read from `tests/` and must match its recorded sha256. A mismatch or missing file makes the task `reference-audit-incomplete`, which fails closed. A gold line in a kept test is `recorded`. Dropped tests are not scanned.
- **Newer copies.** `scan_newer_copies` now runs on every reference generator trajectory, with the same severities as agent audits.
- **Summary.** `scripts/audit_leakage.py --reference-summary OUT.json` writes one row per task, containing hashes only: `recall_lines`, `recall_messages`, `frozen_test_lines`, `leak_lines` and `candidate_lines`. `recall_messages` lists every (conversation, message index) that contains a line classified as recall in that conversation. The script also prints one count line per task.
- **Exit code.** As before, the audit exits 1 only on `confirmed` findings, which include an incomplete audit.

The old kind `GOLD_LINE_IN_GENERATOR` is no longer produced. The existing test that expected it for a tool-output hit now expects `GOLD_LINE_LEAK`.

### Gate: read-only audit of both sealed pilots

Both seals were checked before and after the audit: `runs/study_v4_pilot` MATCH over 685 files (`ff2fe8d5…`), and `runs/study_v4_pilot2` MATCH over 610 files (`ea17e98b…`).

| | Pilot 1 (`study_v4_pilot`) | Pilot 2 (`study_v4_pilot2`) | Expected |
|---|---|---|---|
| Exit code | 0 | 0 | 0 |
| GOLD_LINE_LEAK lines | 0 | 0 | 0 |
| Recall lines (distinct task × line) | 20, in 7 tasks | 17, in 6 tasks | 20 in 7 tasks; 17 |
| GENERATOR_RECALL findings (per conversation × line) | 50 | 30 | |
| Recall messages | 42 | 21 | |
| Frozen-test lines | 0 | 0 | 0 |
| Newer-copy findings | 5 listing, 2 ambiguous (exposed-copy, not failing) | 1 listing | no confirmed |
| Benchmark-awareness findings | 3 (unchanged) | 0 | |

Pilot 2 cross-checks:
- The 30 GENERATOR_RECALL rows equal the 30 rows of `pilot/pilot2/g3_classification.json` exactly, matched by task, conversation, first message index and sha256. Its 17 distinct lines match too.
- In both pilots, the recall messages are exactly the messages the old audit flagged: 42 messages and 122 findings in pilot 1, 21 messages and 55 findings in pilot 2.

Logs: `runs/study_v1_5/part_e_audit_pilot{1,2}.log`. Summaries: [part_e_audit_pilot1_summary.json](part_e_audit_pilot1_summary.json) and [part_e_audit_pilot2_summary.json](part_e_audit_pilot2_summary.json).

The first pilot's G3 result stays failed, as amendment A3 says. This audit shows only that the new rule classifies both pilots as expected.

## 2. A4 (ii): partial V4 pass against V2 FAIL (default rule)

`FullPolicyV15` has a new rule just before R3b. It fires on V2 FAIL with per-requirement V4 NOT_AVAILABLE, at least 1 requirement PASS and 0 failing. The result is **R5 FLAG "signals disagree"**, with reasons `regression test failed` and `reproduction NOT_AVAILABLE with N requirement(s) PASS and none failing`. The rule is not a switch.

Legacy V4, no passing requirement, or any failing requirement still reach R3b. R1 and an active R2 still come first.

### Truth table

The table gained a V2-absence dimension. An absent V2 is either `nothing_to_check` or `error`, the latter standing for every other absence. The table now has **11,520** consistent cases: 384 × 30, up from 288 × 30 = 8,640.

With switches off, v1.5 differs from v1.4.1 in **16 cases**, all in the A4 (ii) class:
- The class has 96 cases: 3 integrity outcomes × 2^5 flags.
- 16 of them change: integrity PASS or NOT_AVAILABLE, patch applies, no manipulation (2 × 2^3).
- All 16 go from v1.4.1's R3b REJECT to R5 FLAG `signals_disagree`.
- The other 80 cases in the class stay R1 REJECT.
- No case outside the class changes.

`test_switches_off_equals_v1_4_1_except_the_a4_ii_class` asserts exactly this, and the per-switch test allows only that change in addition to each switch's own rule.

## 3. A4 (iii): R6's V2-NOT_AVAILABLE branch only for nothing-to-check

`EvidenceV15` gains `v2_absence`, the V2 record's `SignalAbsence` value, or `None` when V2 reported. `evidence_from_signals` fills it in.

The `r6_accept_v2_not_available` switch now turns V2 NOT_AVAILABLE into an ACCEPT only when `v2_absence == "nothing_to_check"`. Every other absence stays FLAG (R8), including `error`, `timeout`, `incomplete`, `disabled`, `not_configured`, `not_implemented` and a missing value. The truth table checks that every switch-driven R6 change has V2 NOT_AVAILABLE with nothing to check.

The arm B replay (`scripts/replay_paired_skip_arm_b.py`, unchanged) builds v1.5 evidence from the stored record and swaps in the replayed P-accounting V2 outcome. `v2_absence` therefore comes from the stored record. On all 51 arm B records, whenever the replayed P outcome is NOT_AVAILABLE, the stored absence equals the replayed signal's absence: 6 `error`, 5 `nothing_to_check`, 6 `incomplete`. The replay therefore applies (iii) correctly without a change.

## 4. A4 (v): `decide_v1_5.py --no-v2-fallback`

This option recomputes V2 as if the fallback were off, from each task's sealed `verification/selection.json`. The file must also match the record's `selection_sha256`.

With the study config (`enable_tier0: false`, `max_tier: 2`), the fallback runs only when Tiers 1 and 2 select nothing. A fallback selection therefore holds only fallback tests. Without the fallback, V2 is NOT_AVAILABLE with nothing to check, which is what the run itself records for an empty selection.

The tool refuses rather than guessing in these cases:
- The selection does not show which tests the fallback chose (no `fallback_used`, `fallback_tests` or `tests`).
- V2 has a result but no selection is stored.
- The selection mixes fallback and other tests.
- `fallback_used` and `fallback_tests` disagree.

A task with no selection and V2 already NOT_AVAILABLE is kept as it is. Output files get the suffix `_v2-nofallback`, and the summary records `v2_fallback` and `v2_fallback_removed_tasks`. The CSV gains `v2_absence` and `v2_fallback_removed` columns.

The stored records can tell which tests the fallback selected, so nothing stopped this step. On pilot 2, where no task used the fallback, the decisions with and without the option are equal to the committed pilot 2 decisions.

## 5. Gates

- **Unit gate:** 1,869 passed, 6 skipped, 6 failed, 17 errors (`runs/study_v1_5/unit_part_e.log`). The failing and erroring IDs equal Phase 5's, which equal `unit_baseline_phase1.json`. The 33 extra passes are the new tests.
- **Truth table:** as in section 2: 11,520 cases, and exactly 16 differ from v1.4.1 with switches off, all in the A4 (ii) class.
- **v1.4.1 replay:** "PASS: full_v1_4_1.yaml matched 51/51 stored decisions" and "PASS: v1_5.yaml matched 51/51 label-free P_invalid_excluded V2 outcomes" (40 captured executions, 11 stored V2 absences).
- **v1.5 replay on arm B** (old V4 evidence, switches off): "PASS: full-v1.5 switches off matched 51/51 decision_P_invalid_excluded". The A4 (ii) case cannot occur here, because arm B's V4 is legacy.
- **All switches on:** **11** decisions now differ from `decision_P_invalid_excluded`, down from 16 in Part D. Every new REJECT comes from R2 or the extended R3 (`part_d_armB_all_switches.csv`, rewritten by the replay).

| instance_id | P decision | all on | rule |
|---|---|---|---|
| astropy__astropy-13398 | FLAG | ACCEPT | R6, V2 nothing to check |
| astropy__astropy-14508 | FLAG | ACCEPT | R6, V2 nothing to check |
| django__django-12965 | FLAG | REJECT | R3, extended: 3 failing V4 units |
| django__django-13297 | FLAG | REJECT | R3, extended: 3 failing V4 units |
| django__django-14140 | FLAG | REJECT | R2 |
| matplotlib__matplotlib-23476 | FLAG | REJECT | R2 |
| matplotlib__matplotlib-24627 | FLAG | ACCEPT | R6, V2 nothing to check |
| matplotlib__matplotlib-25122 | FLAG | REJECT | R3, extended: 2 failing V4 units |
| matplotlib__matplotlib-26291 | FLAG | REJECT | R3, extended: 2 failing V4 units |
| pylint-dev__pylint-6903 | FLAG | ACCEPT | R6, V2 nothing to check |
| sphinx-doc__sphinx-10323 | FLAG | REJECT | R2 |

The 7 new REJECTs are unchanged from Part D. Five Part D R6 ACCEPTs are gone, all because of A4 (iii):
- `django__django-11095`, `django__django-15499`, `django__django-16082` and `sympy__sympy-13480`: V2 `incomplete`.
- `pytest-dev__pytest-7236`: V2 `error`.

The 4 R6 ACCEPTs that remain all have V2 nothing-to-check. This is label-free: no correctness of any patch was looked at.

## Nothing stopped

Every gate gave the expected result.

## Follow-up: A4 (iii) revised (21 Nov)

Amendment section "A4 (iii) revised, 21 Nov": the R6 switch now also accepts V2 absence `incomplete`, but only when no test timed out or crashed on the patched tree. `EvidenceV15` gains `v2_patched_timeout_or_crash`, which comes from the stored patched run and patched confirmations, and is True when no patched run is stored. `decide_v1_5.py` writes it as a CSV column.

The truth table now has **17,280** cases (576 × 30, with 6 V2 cases). With switches off it still differs from v1.4.1 in exactly the 16 A4 (ii) cases.

Unit gate: 1,879 passed, 6 skipped, 6 failed, 17 errors, with IDs equal to the baseline. The v1.4.1 replay matched 51/51 decisions and 51/51 V2 outcomes, and v1.5 with switches off matched 51/51.

All switches on, arm B: **14** decisions differ from `decision_P_invalid_excluded`.
- The 7 REJECTs are unchanged.
- 7 ACCEPTs come from R6: 4 with V2 nothing-to-check (astropy-13398, astropy-14508, matplotlib-24627, pylint-6903) and 3 with V2 incomplete and no patched timeout or crash (django-15499, django-16082, sympy-13480).
- Two of Part D's R6 ACCEPTs stay out: `django__django-11095` (V2 incomplete, but its stored patched run has crash statuses) and `pytest-dev__pytest-7236` (V2 error).
