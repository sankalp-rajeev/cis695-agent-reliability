# Protocol amendment, 21 Nov 2026

This amends [PROTOCOL.md](PROTOCOL.md) (tag `study-v1.5-prereg`) and [PLAN.md](PLAN.md). It takes effect at tag `study-v4-frozen`.

**When it was written.** After the first V4 pilot ([PILOT.md](pilot/PILOT.md)), the G3 diagnosis ([G3_DIAGNOSIS.md](pilot/G3_DIAGNOSIS.md)) and the one-pass re-pilot ([PILOT2.md](pilot/PILOT2.md)). All three used only the 10 dev gold patches. No labels or answer keys were opened. No arm B patch, test-set task or public-system patch has been verified with the new V4.

Each item gives the old rule, the new rule and the reason.

## A1. One V4 pass with the Phase 4b prompts

- **Old.** PROTOCOL change 4: two passes if the confirmed balance is at least $7, otherwise one. The balance was $9.03, so the mode was two passes. Per-requirement verdicts included FAIL-confirmed: kept tests from both passes fail. R3's extended part was any FAIL-confirmed requirement, or 2+ failing requirements, or a V4 failure with a V3 failure. RQ3 included a one-pass vs two-pass ablation (pass-1 tests only). PLAN Phase 4 gate: cost per task at most $0.06, otherwise stop.
- **New.**
  - V4 runs one pass with the Phase 4b prompts (`configs/agent/v4_requirements.yaml`, `configs/agent/v4_tests_per_requirement.yaml` at commit `fa1b016`, `v4_passes: 1`).
  - FAIL-confirmed can no longer occur, so it is removed from the rules. Every failing requirement is FAIL-single.
  - Extended R3 = V4 FAIL **and** (2+ failing requirements **or** a V3 failure). The V4 + V2 FAIL part is unchanged from v1.4.1. R4 is unchanged: one failing requirement, nothing else failing → FLAG "likely wrong".
  - The one-pass vs two-pass ablation is dropped from RQ3 and Phase 16.
  - G1 (cost per task) is a budget gate. It checks that the planned runs fit the balance and the run caps. It is not evidence about whether V4 is valid. Because V4 is frozen, a later cost problem is handled with the caps and the balance, never with a V4 change.
- **Reason.** The re-pilot, on the same 10 gold patches, cut gold patches with any V4 FAIL from 3 to 2 and raised V4 full passes from 6 to 8, at $0.033 per task against $0.067 for two passes. The two passes were not independent, so a "confirmed" failure would not have been two independent pieces of evidence.
- **Code.** With `v4_passes: 1`, the frozen code always gives a FAIL-confirmed count of 0. The extended R3 code therefore already gives the new rule, and no V4 or policy code changes for A1.

## A2. Generator fingerprint pinned now, recorded per response

- **Old.** `configs/model/generator.yaml` pinned `system_fingerprint: aeb56401ca74e127821c4f9126dcb669` (checked 30 Sep). Runs did not check it. The first pilot was served `bc19ba97cbe016479903222bb1578db6`. This was logged as a deviation, and the config was left unchanged.
- **New.**
  - `scripts/verify_model.py --update` was run on 21 Nov. The pin is now `bc19ba97cbe016479903222bb1578db6` (see [V4_FREEZE.md](V4_FREEZE.md)).
  - Each run logs the fingerprint of every response. The generator trajectories already store `extra.response.system_fingerprint` on each response: 858 of 858 responses in the re-pilot, all `bc19ba97cbe016479903222bb1578db6`. No code change was needed.
  - If the fingerprint changes before or during Phase 11, this is logged as a deviation in STATUS.md, with the run and the first affected response. It is not a stop.
- **Reason.** V4 is generated once per task set: by the dev gold run (Phase 6) and the test gold run (Phase 11). Every system on a task then reuses those frozen tests. A fingerprint change therefore cannot make systems differ from each other. It can only separate the dev tests from the test-set tests, and the logs make that visible.

## A3. Leakage stop rule

- **Old.** PLAN §9: stop on any leakage audit failure on a generator trajectory, including any gold-patch line found in a generator message. PILOT.md's G3 used the audit exit code.
- **New.**
  - **Stop** if a gold line first appears outside the model's own messages (system or user message, or tool output that the model did not produce by writing the line itself), or if the audit has any other CONFIRMED finding.
  - Gold lines the model wrote itself, and gold lines in kept tests, are recorded per task. They are not failures.
  - Phase 15 adds a sensitivity analysis on the tasks without model-written gold-line recall.
  - The first pilot keeps its failed G3. This rule applies from Phase 6 onward.
- **Reason.** The G3 diagnosis found that all 122 first-pilot findings (20 distinct lines, 7 tasks) were model-written. Each first appeared in the generator's own reasoning, and none came from the environment. A model that recalls or rederives a fix from the issue has not been given the answer. Any line that enters from outside the model's own messages is still a leak and still stops the run. Recall is reported, and the sensitivity analysis shows whether it affects the results.

## A4. Adoption rules

The code for (ii), (iii) and (v) is written and unit-tested before Phase 7. None of it is V4 code. Both V4 versions used in (vi), the new per-requirement V4 and the legacy V4 prompt, are frozen at `study-v4-frozen` ([V4_FREEZE.md](V4_FREEZE.md)).

| # | Old | New | Reason |
|---|---|---|---|
| (i) | A REJECT switch (R2, or R3 beyond v1.4.1) is adopted if it REJECTs at most 1 of the 51 dev gold patches and newly REJECTs at least 2 of arm B's 26 wrong patches. | Same, and it may also REJECT at most 1 of arm B's 25 correct patches. | Gold patches measure only the cost on reference fixes. Arm B's correct patches are the realistic cost on agent-written fixes, and the old rule did not bound that cost. |
| (ii) | V2 FAIL and V4 not a full PASS with no V4 failure → R3b REJECT, including V4 NOT_AVAILABLE. | V2 FAIL with V4 NOT_AVAILABLE, at least 1 requirement PASS and none failing → R5 FLAG "signals disagree", not R3b. | With per-requirement V4, a passing requirement is positive evidence against V2, as in R5. Rejecting on V2 alone would discard that evidence. |
| (iii) | R6's V2-NOT_AVAILABLE branch applies to any V2 NOT_AVAILABLE. | The branch applies only when V2 had nothing to check. A V2 that could not run for another reason does not qualify. | A V2 that could not run says nothing about the patch. Only "no test to run" is a real absence of a regression signal. |
| (iv) | The R6 branch is adopted if arm B ACCEPT precision under v1.5 is at least 80% and v1.5 accepts at least as many correct patches as v1.4.1-P. | The 80% bar is replaced: the branch is adopted if at least 70% of the arm B patches it newly ACCEPTs are correct. The second condition is unchanged. | The old bar mixed the branch's own ACCEPTs with those R6 already makes, so it did not measure the branch. The new bar judges only the patches the branch adds. The threshold is set now, before any Phase 7 data. |
| (v) | `decide_v1_5.py` has switches for R2, R3 and R6 only. The V2 fallback could not be switched off offline. | `decide_v1_5.py` gets a no-fallback V2 switch, which recomputes V2 without fallback-selected tests. | The fallback-keep rule (PROTOCOL §5) and the fallback ablation need V2 without the fallback, computed from stored signals. |
| (vi) | Phase 7 re-verifies arm B with the new V4 only. Old vs new V4 is a Phase 16 ablation. | Phase 7 also compares the new V4 with arm B's stored old V4, with switches off and V2 under accounting P. The old V4 is used only if it gives more correct ACCEPTs at equal or better ACCEPT precision. Otherwise the new V4 stands. | The new V4 has only been checked on 10 gold patches. This guards against freezing a V4 that does worse on agent patches than the one it replaces, and the rule is fixed before Phase 7. |

## A5. Restarts and the Phase 7 deadline

- **Old.** PLAN §9 stops a run on infrastructure errors on more than 5% of tasks. There was no restart rule and no deadline for Phase 7.
- **New.**
  - Each run may be restarted once, from scratch, and only for failures that are infrastructure-only. The restart is logged in STATUS.md.
  - If Phase 7 is not sealed by **Mon 23 Nov 12:00**, v1.5 is frozen with all switches off.
- **Reason.** Restarting from scratch keeps each sealed run a single uninterrupted attempt. Allowing only one restart, and only for infrastructure failures, keeps restarts from being used to pick results. The deadline keeps Phase 11 on schedule (PLAN §10: Phase 11 starts Monday overnight). Switches off is v1.4.1 behaviour, which was fixed before any of this data.

## Not in this amendment

The analysis items (audit M1-M6) will come in a second amendment before Phase 11.
