# Rerun protocol v1 (pre-registered, frozen before any audited run)

Project: CIS 695 "Trust but Verify" (oracle-blind verification of LLM patches on SWE-bench Verified).
Frozen: 17 November 2026, before arm B launches. Committed on branch `protocol/rerun-v1` with the annotated tag `rerun-protocol-v1-frozen`. Any change after that tag is a protocol amendment: a new file and a new tag, reported as such.

## 1. Questions
- **Q-A (replication):** with fresh patches from the same repair model as the main study (DeepSeek), run end to end through the repaired pipeline, do the Phase 7 findings hold? Those findings are the decision mix, ACCEPT precision, and the verifier being no better than chance at keeping wrong patches out.
- **Q-B (weaker agent):** when the repair agent is often wrong (gpt-4.1-mini), does the verifier separate wrong patches from correct ones better than chance? Does the answer depend on the kind of wrong patch?
- **Q-AB (paired):** on the same tasks, how do decisions and their precision change with agent strength?

## 2. Frozen components (all hashes SHA-256)
| Component | Identity |
|---|---|
| Pipeline | annotated tag `e2e-v1.4.3-frozen`, commit `2a3bf7f`; decision policy `v1.4.1-full` (`configs/verifier/full_v1_4_1.yaml` `cd148b7c…`) |
| Generic health rule | `configs/verifier/run_health_generic_exceptions.json` `133b1718…` (Django GIS guard only) |
| Task specs | `configs/e2e/task_specs_83.json` `9e55c5a8…` (at the tag) plus `configs/e2e/task_specs_add9_e2e_v141.json` `bee27f25…` (branch `feature/task-prep` at `639cc29`) |
| Run order | `configs/e2e/cohorts/main92_run_order.txt` `9f0164f5…` (`639cc29`): the 83 comparable tasks in frozen order, then the 9 additions |
| Repair, arm A | `configs/model/primary.yaml` `39d072a6…` (DeepSeek, 100 steps) |
| Repair, arm B | `configs/model/primary_umgpt.yaml` `25ec42b8…` (gpt-4.1-mini on the UM toolkit, 100 steps, $0.60 per task) |
| V4 generator, both arms | `configs/model/generator.yaml` `c482616d…` (DeepSeek V4 Flash, 80 steps) |
| Ledger | one shared file `runs/provider_spend_ledger.json` in `~/projects/wt-e2e`, seeded from the UM probe |

## 3. Cohort
- **92 tasks:** the 83 Phase 4 tasks (the comparable set) plus 9 main-study tasks prepared by the task-prep job.
- **Excluded before any run, label-free:** the 7 `psf__requests` main-study tasks (the image holds an unmaskable newer copy of the package, so the answer is in the container) and `sphinx-doc__sphinx-10614` (its environment setup edits a tracked file, so the source-integrity check fails closed).
- **Pilots do not count:** pilot runs (`runs/e2e_v1_4_*_pilot_*`) are engineering evidence only. Pilot tasks are re-run from scratch in the arms.

## 4. Arms and order
1. **Arm B first:** repair with gpt-4.1-mini on the UM key, V4 on DeepSeek. Output `runs/e2e_v1_4_3_armB_um`.
2. **Arm A after funding:** repair and V4 on DeepSeek. Output `runs/e2e_v1_4_3_armA_deepseek`. It starts once the DeepSeek account is topped up, and may start earlier and stop at its cap.
- Both use `--mode audited --freeze-tag e2e-v1.4.3-frozen` with the same manifest, task specs, generator and ledger. Arms run one at a time, never in parallel.
- **Caps:** DeepSeek cap = funded balance minus $0.50, rounded down. It is $4.00 at freeze, and is raised only by resuming the same folder. UM: the ledger prices cached input at a 75% discount, but U-M's pricing page lists no cached-input price, so real UM charges may be up to about 2x the ledger. Arm B therefore starts with a $10.00 ledger cap for both account and job (the probe's $0.66 counts). After the first day, the U-M Toolkit billing dashboard is compared with the ledger, and the cap is reset on resume so that real charges stay within the key's budget. Each cap change is recorded in attempt.json and counts as an operational step, not a deviation.

## 5. Stopping and resuming
- No stopping based on results. Allowed stops: a budget stop, a systemic-infrastructure stop, a source-integrity abort, or an operator interrupt. Each is recorded in `completion.json`.
- Resume only with the same command and folder. Only the caps may change, and every attempt is logged in `attempt.json`. After an interrupted process, settle any open ledger reservation at its full reserved amount (conservative) before resuming.
- **Budget coverage:** if arm B's UM cap stops it before all 92, its cohort is the tasks it completed. Because of the run order these are the first k comparable tasks. Report k.
- **A pipeline defect found mid-arm:** stop; fix it as a new tagged version; then re-verify the arm's frozen patches in full with `--verify-only-from` into a new folder (patches are never regenerated). Keep the original folder as evidence. Report both.

## 6. Blinding
- No labels, oracle output or grader verdicts are looked at until an arm is sealed. Monitoring during a run uses label-free fields only: `completion.json`, the ledger, infrastructure and no-patch counts, and decision counts.
- **Seal:** the runner's `seal.json`, plus a report-only commit of the seal hash and `completion.json` on branch `results/rerun-v1`, under the annotated tag `rerun-armB-sealed` (and `rerun-armA-sealed`).
- **Grading after the seal:** the same oracle step as the main study, unchanged, using the pinned swebench 4.0.4 wheel. The label is the harness's resolved / not resolved.

## 7. Outcome classes
- **Patch tasks:** a non-empty frozen patch. These are the units for all precision metrics.
- **No-patch tasks** (empty patch; REJECT by V1) and **agent-infrastructure tasks** (`AGENT_INFRA`) are counted and reported separately. They are excluded from precision metrics. A sensitivity analysis includes no-patch tasks as wrong patches.
- **Wrong-patch types, from grader evidence only and independent of verifier signals:**
  - **R (regression-wrong):** at least one PASS_TO_PASS test fails;
  - **U (under-solved):** all PASS_TO_PASS pass and at least one FAIL_TO_PASS fails;
  - **X (other):** the patch does not apply in the harness, or the harness errors.

## 8. Analysis (per arm, then paired)
- **Primary accounting:** Policy S with INVALID_ID excluded (the live decision). Policy C and the INVALID_ID-as-missing variants are sensitivities, from each task's `v2_policies.json`.
- **Primary metrics:**
  1. decision counts (ACCEPT/FLAG/REJECT);
  2. ACCEPT precision, correct ÷ ACCEPT, with a Wilson 95% CI;
  3. the base rate (correct ÷ patch tasks) as the "no verifier" baseline;
  4. the share of wrong patches not ACCEPTed versus the share of all patch tasks not ACCEPTed. This is the Phase 7 chance comparison, with a two-proportion difference and its CI;
  5. the share of correct patches not ACCEPTed (the coverage cost).
- **By wrong-patch type (R/U/X):** the not-ACCEPTed rate for each type.
- **Signal attribution:** for each non-ACCEPT patch task, which signals were FAIL and which were absent, counted separately for correct and wrong patches.
- **Q-A:** compare arm A with the sealed Phase 7 primary (14/67/2; ACCEPT precision 11/14). Descriptive, with CIs; no hypothesis test is claimed.
- **Q-AB:** on tasks where both arms produced patches, cross-tabulate decision × correctness per arm.
- **Exploratory, labelled as such:** drop-one-signal ablations recomputed offline from the stored signals; per-repository breakdowns; cost per correct ACCEPT.

## 9. Contamination
Before any result is reported, run the extended leakage audit (branch `analysis/leakage-gaps`) on both arms' repair and V4 trajectories. Report CONFIRMED and awareness findings. A sensitivity analysis excludes CONFIRMED tasks.

## 10. Deviations
Every deviation from this protocol is listed in the results report with its reason and when it was decided, before or after unblinding.
