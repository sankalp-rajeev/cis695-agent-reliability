# Rerun protocol v1, amendment A3 (decided 18 November 2026, after arm B was sealed; see Blinding status)

**Purpose.** Section 8 names the metrics but leaves some computations open. This amendment fixes them so the analysis code can be frozen before the full labels exist. No question, cohort, frozen component, outcome class or primary metric changes.

**Blinding status, stated exactly.**
- Before this text was written, its author (Claude, the project's analyst) and Sankalp had seen two grading outcomes from the grading smoke test: `astropy__astropy-13977` (empty patch, harness skipped) and `astropy__astropy-14365` (not resolved, type U; FAIL_TO_PASS 0/1, PASS_TO_PASS 8/8).
- The text was written and handed to the executing agent before 09:36 MST on 18 November, before anyone on the analysis side had seen any aggregate grading output.
- After that, the executing agent in the first Stage 1 session ran `grading_status.sh` and saw a partial aggregate of oracle outcomes. That session stopped before committing anything. It recorded exactly what it saw in a disclosure file (SHA-256 `e8005aa5c76e3bd2133f8951752ae8779ad130242b451bd985ec8170f34f9594`), which is published with the arm B results.
- The author of this text has not seen that aggregate. No word of this amendment was changed after either exposure, apart from inserting that hash and this paragraph.
- The analysis code was written in a fresh agent session that had not seen it.
- Both smoke-test tasks stay in every analysis.

1. **Units.** A patch task is a completed task whose frozen patch is non-empty. Provider-blocked (A1), no-patch and agent-infrastructure tasks are counted and reported but are not patch tasks.
2. **Correct and wrong.** Correct means the A2 oracle reports resolved. A wrong patch is a patch task that is not resolved. Its type R, U or X comes from the grader evidence in labels.csv, as section 7 defines.
3. **Intervals.** Every single proportion gets a Wilson score 95% interval (z = 1.959964). Every difference of two proportions gets a Newcombe hybrid score interval (Newcombe 1998, method 10) built from those Wilson limits.
4. **Metric 4 (chance comparison), as written.** d = P(not ACCEPT | wrong) − P(not ACCEPT | all patch tasks), with a Newcombe interval. Wrong patches are a subset of all patch tasks, so the two proportions are not independent; the report says this interval is approximate.
   **Supplementary, added now.** d′ = P(not ACCEPT | wrong) − P(not ACCEPT | correct), with a Newcombe interval, plus a two-sided Fisher exact test on correctness × (ACCEPT, not ACCEPT). The results report says the verifier separates wrong patches from correct ones "better than chance" only if d′ > 0 and its interval excludes 0. Otherwise it says the data do not show it.
5. **Accountings.** For each task the four accountings (S and C, each with INVALID_ID excluded or as missing) are recomputed with the frozen `FullPolicyV141`. Only V2 is replaced, by that accounting's report in `v2_policies.json`, mapped exactly as the live pipeline maps it (PASS→PASS; FAIL and REGRESSION_ERROR→FAIL; INCOMPLETE and NOT_AVAILABLE→NOT_AVAILABLE). A task without `v2_policies.json` keeps its recorded V2 absence in every accounting. The recomputed S with INVALID_ID excluded must reproduce the live decision on every task; if it does not, the analysis stops.
6. **Sensitivities.** All are reported; none replaces the primary.
   (a) no-patch tasks counted as wrong patches (section 7);
   (b) provider-blocked tasks counted as no-patch, inside (a) (A1);
   (c) Policy C and INVALID_ID-as-missing accountings;
   (d) excluding tasks with any T4 (environment-leak) finding in the repair or V4 trajectory from `audit_rerun_arm.py`. These are section 9's CONFIRMED tasks;
   (e) additionally excluding tasks with any T3-name finding (a hidden test name mentioned before it is defined).
   T3-content findings are reported but not excluded, because they are consistent with solving. Phase 7's checks that drop the 3 cache-read tasks and the 38 `main_50_a` tasks apply to Phase 7's patches only; rerun arms get their own audit.
7. **Signal attribution.** For each non-ACCEPT patch task: V1–V4 each as PASS, FAIL or absent (with the recorded absence reason), plus the record's decision reasons. Tabulated separately for correct and wrong patches.
8. **Exploratory, labelled as such.** Drop-one-signal ablation: re-decide with one signal at a time forced to PASS, so that signal can no longer block. Per-repository tables. Cost per correct ACCEPT: the arm's total ledger spend over both providers ÷ correct ACCEPTs, plus the median per-task spend.
9. **Paired Q-AB** (once both arms are sealed and graded): on tasks where both arms have a patch, the decision × correctness table for each arm, and the count of tasks whose decision or correctness differs between arms. Descriptive only.
10. **Nothing else.** Any other metric, test or exclusion in a results report is a deviation, listed with its date and whether it was decided before or after unblinding.
