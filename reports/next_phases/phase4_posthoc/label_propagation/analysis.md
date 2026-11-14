# Label provenance root cause and propagation

All computations below are post-hoc label sensitivities. The pre-registered labels, sealed results, executor, predictions, selectors, thresholds, and tags are unchanged. B is primary for interpretation; B-cpu is the requested resource sensitivity. No Docker, agent or benchmark execution is performed.

## Root cause

The nine frozen candidates are the final answers from the replacement agent attempts; each raw submission, trajectory exit message, extracted diff, repair record, and frozen SHA agrees. Every mismatched grader patch is instead the exact final answer of an earlier excluded halted attempt, retained in `_excluded_main_50_a_halted` or `_excluded_main_50_b_halted` (one later excluded attempt happens to submit identical bytes too). This is stale evaluation reuse, not a faulty claim/diff extraction or an intermediate agent patch.

The source run directories were archived and the halves restarted using the same experiment IDs. The external `logs/run_evaluation/<experiment>__<instance>/<model>/<instance>/report.json` namespace survived. The official harness checks whether that path exists and skips completed instances without comparing the prediction hash. All nine newer harness.log files explicitly say **already run, skipping / No instances to run**. The oracle wrapper verifies the new local frozen patch, writes new predictions, then reads the old report and stamps it with `record.patch.sha256`. Later, prepare_posthoc_evaluation.py joins the pinned CSV oracle status to independently checked export hashes; it never checks the actual patch behind the linked report. Thus the original sidecar has a genuine new frozen hash attached to an old attempt’s grade.

| Task | Earlier final answer: UTC start → finish | Replacement final answer: UTC start → finish | Earlier / replacement launch commits |
|---|---|---|---|
| astropy__astropy-13977 | 2026-10-09T17:43:40+00:00 → 2026-10-09T17:53:00+00:00 | 2026-10-09T20:50:20+00:00 → 2026-10-09T20:58:57+00:00 | `c44de11` / `17fdf59` |
| astropy__astropy-7606 | 2026-10-09T18:09:02+00:00 → 2026-10-09T18:09:53+00:00 | 2026-10-09T21:12:19+00:00 → 2026-10-09T21:13:07+00:00 | `c44de11` / `17fdf59` |
| django__django-11820 | 2026-10-09T18:23:54+00:00 → 2026-10-09T18:38:09+00:00 | 2026-10-09T21:27:11+00:00 → 2026-10-09T21:34:01+00:00 | `c44de11` / `17fdf59` |
| django__django-13297 | 2026-10-09T19:17:58+00:00 → 2026-10-09T19:23:23+00:00 | 2026-10-09T22:29:24+00:00 → 2026-10-09T22:38:44+00:00 | `c44de11` / `17fdf59` |
| matplotlib__matplotlib-25122 | 2026-10-08T21:41:18+00:00 → 2026-10-08T21:42:38+00:00 | 2026-10-09T03:40:49+00:00 → 2026-10-09T03:48:39+00:00 | `8add43e` / `b4aca76` |
| pydata__xarray-4695 | 2026-10-08T21:14:06+00:00 → 2026-10-08T21:15:24+00:00 | 2026-10-09T03:11:08+00:00 → 2026-10-09T03:12:58+00:00 | `8add43e` / `b4aca76` |
| pydata__xarray-6599 | 2026-10-08T21:27:04+00:00 → 2026-10-08T21:37:29+00:00 | 2026-10-09T03:23:15+00:00 → 2026-10-09T03:35:14+00:00 | `8add43e` / `b4aca76` |
| pydata__xarray-6744 | 2026-10-08T20:52:27+00:00 → 2026-10-08T20:55:54+00:00 | 2026-10-09T02:34:28+00:00 → 2026-10-09T02:41:23+00:00 | `8add43e` / `b4aca76` |
| pytest-dev__pytest-7432 | 2026-10-08T21:03:36+00:00 → 2026-10-08T21:04:25+00:00 | 2026-10-09T02:53:29+00:00 → 2026-10-09T02:56:14+00:00 | `8add43e` / `b4aca76` |

The complete root_cause.json records both trajectory SHA-256 IDs, exit-message row numbers, submission/frozen hashes and byte sizes, all excluded intermediate attempts, oracle timestamps, first grader-log timestamps, cache-hit lines, and historical source-code hashes/line anchors. Naive grader log timestamps are retained verbatim; agent/oracle timestamps explicitly record UTC. No file modification timestamp is used as the chronology.

Agent extraction: mini-SWE-agent 2.4.6 → `_split_submission` at `<<<END_CLAIM>>>`, removing only leading LF separators → `freeze_patch` writes exact bytes and a hash, refusing overwrite. The restart created a new task directory rather than overwriting the old read-only patch. The current final answer is authoritative for the frozen experiment; the earlier answer was real but belonged to the excluded attempt. The sidecar preparer was committed at `d9a22f9530763f6ab746a5717549ce0daaa20e29 2026-11-06T13:27:31-07:00`.

## Exposure in other batches

| Locally retained batch | Oracle/patch records scanned | Explicit cache hits | Hash mismatches | Cache hits with matching hashes | Missing binding evidence |
|---|---:|---:|---:|---:|---:|
| 3.1_smoke_gemini-3.1-flash-lite | 1 | 0 | 0 | 0 | 1 |
| _excluded_main_50_a_halted | 10 | 0 | 0 | 0 | 0 |
| _excluded_main_50_a_halted_2 | 10 | 10 | 5 | 5 | 0 |
| _excluded_main_50_b_halted | 8 | 0 | 0 | 0 | 0 |
| main_2_rerun_mpl | 1 | 0 | 0 | 0 | 0 |
| main_3_rerun_infra | 3 | 0 | 0 | 0 | 0 |
| main_50_a | 43 | 10 | 5 | 5 | 0 |
| main_50_b | 44 | 8 | 4 | 4 | 0 |

The same structural risk applies to any reuse of experiment/model/instance IDs, including explicit oracle reruns after a changed prediction. The second halted main_50_a attempt demonstrates reuse before the final run; matching hashes on a cache hit demonstrate that a stale grade can remain invisible to a mismatch-only audit. The separately named main_2_rerun_mpl and main_3_rerun_infra records have distinct namespaces and no local cache-hit evidence. The older smoke record is also inventoried; its applied-patch evidence is unavailable locally, so its binding cannot be certified. This is a census of retained local records, not a claim that deleted or unavailable pilot batches are safe. No excluded attempt is pooled into propagated performance metrics.

## Separate audited label artifact

`../label_audit/audited_labels.csv` contains all 83 frozen hashes, A/B/B-cpu labels, SUPPORTED-original versus regrade provenance, and original/default/CPU report and output hashes. It is a new artifact; correctness_sidecar.json and the pinned CSV remain unchanged and remain the pre-registered A set.

| Set | Correct | Incorrect |
|---|---:|---:|
| A | 69 | 14 |
| B | 70 | 13 |
| B-cpu | 72 | 11 |

A→B changes: Astropy-13977 and Django-13297 become correct; Xarray-6599 becomes incorrect. B→B-cpu changes: Pylint-6528 and Pylint-7277 become correct. These are analytical assignments from audited grades, never replacements for original labels. Labels outside the audited 83 (six nonempty requests and empty-patch rows) retain their original values in the 89/93/100-task sensitivity tables. Different-patch excluded/pilot records are never assigned audited labels just by instance ID.

## Consumer inventory

`consumers.csv` lists 13 report families and their code/report paths. `label_references.csv` lists 1256 source/prose keyword references with line numbers, distinguishing direct consumers from static restatements and oracle-blind guards. The inventory covers original V1–V4, combined policy, claims, earlier diagnostics and scoring audits, V2/SCG, Phase 2 skip cohorts, selector retention cohorts, Phase 4 policies, and presentation restatements.

| Consumer | Code | Reports | Propagated family / limit |
|---|---|---|---|
| Main study signals and claims | src/reliability/analysis/metrics.py<br>scripts/metrics.py<br>scripts/interim_report.py<br>scripts/run_pilot.py | docs/results_100.md<br>reports/pilot_summary.md<br>reports/smoke_3.1.md | main/*;claims/*;policy/*; Original headline, half and all-study populations; pilot/alternate-candidate rows are not relabelled by task ID. |
| Baseline versus Full assessment | reports/policy_comparison/compare.py<br>reports/policy_comparison/reconstruction.py<br>reports/policy_comparison/statistics_core.py<br>reports/policy_comparison/render_report.py | reports/policy_comparison/report.md<br>reports/policy_comparison/metrics.csv | policy/*;paired_policy/*; Frozen ACCEPT/FLAG/REJECT decisions; original hypothetical pytest-7432 sensitivity retained. |
| Failure diagnosis | reports/failure_analysis/extract_evidence.py<br>reports/failure_analysis/compact_overview.py<br>reports/failure_analysis/rerun_group4_regression.py<br>scripts/old_assertion_check.py<br>scripts/old_assertion_check_gold.py | reports/failure_analysis/failure_analysis.md<br>reports/failure_analysis/failure_analysis.csv | main/headline83/*;cohort/grader_witness_tasks4; Task label annotations and main-study counts propagate; independent superseded-assertion classes and raw historical test statuses do not. |
| V2 oracle post-hoc diagnosis | reports/v2_diagnostic/oracle_posthoc.py<br>reports/v2_diagnostic/diagnostic.py | reports/v2_diagnostic/report.md<br>reports/v2_diagnostic/sample_report.md<br>reports/v2_diagnostic/patches.csv<br>reports/v2_diagnostic/wrong_patch_tests.csv | main/headline83/V2;diagnostic/*; The fixed old failure inventory is not made into fresh grader evidence for mismatched candidates. |
| Earlier selector opportunity analysis | reports/next_steps/analyze.py | reports/next_steps/report.md<br>reports/next_steps/phase2_counts_by_repo.csv<br>reports/next_steps/phase3_metrics.csv | main/repo/*;selector_wrong_cohort/*; Selector identities and historical reference lists stay fixed; label-cohort weighting only. |
| V2 raw-scoring audit | reports/v2_scoring_audit/audit.py<br>reports/v2_scoring_audit/finish_blocked.py<br>reports/v2_scoring_audit/resume_20261026/analyze_resume.py<br>reports/v2_scoring_audit/resume_20261026/finish_resume.py | reports/v2_scoring_audit/report.md<br>reports/v2_scoring_audit/resume_20261026/report.md<br>reports/v2_scoring_audit/resume_20261026/metrics_before_after.csv | scoring_audit/*;main/headline83/V2;main/repo/*/V2; Original 8-target and exact three-/one-task observed cohorts retained; unavailable raw data never becomes a new verdict. |
| Frozen V2 versus SCG | scripts/v2_evaluation.py<br>scripts/v2_scg_paired.py<br>reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/analyze_completed.py<br>reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/finalize_analysis.py | reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/FINAL_SCIENTIFIC_REPORT.md<br>reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/PRESENTATION_SUMMARY.md | paired83/*; Recorded final V2/SCG outcomes, including no-verdict states, preserved. Label-free runtime/selection comparisons unchanged. |
| Sidecar binding | reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/prepare_posthoc_evaluation.py | reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/sidecar_provenance.json | cohort/*; This joined CSV labels and frozen export hashes without checking the archived applied-patch hash; original sidecar remains untouched. |
| Exploratory shadow classification | scripts/v2_stabilization_finish.py<br>scripts/v2_shadow_five.py<br>scripts/v2_shadow_five_v2.py | reports/v2_stabilization/classifier_v2/downstream_audit.json<br>reports/v2_stabilization/classifier_v2/live_summary.json | shadow/*; Five superseded-assertion class labels are independent labels, not patch-correctness labels. Their class agreement is unchanged; global wrong-patch denominator propagates. |
| Skip-dependent post-hoc labels | scripts/phase2_policy_projection.py | reports/next_phases/phase2_incomplete_causes/ACCEPTED_SKIP_LABELS_POST_HOC_ONLY.md<br>reports/next_phases/phase2_incomplete_causes/accepted_PASS_labels_POST_HOC_ONLY.json | cohort/skip_dependent13; Exactly the frozen 13-task cohort; no selection or skip policy changes. |
| Known old-test witnesses | scripts/phase1_known_failures.py<br>reports/next_phases/phase4_posthoc/grader_gap/analyze.py | reports/next_phases/phase1_known_failures/SUMMARY.md<br>reports/next_phases/phase4_posthoc/grader_gap/analysis.md | cohort/grader_witness_tasks4; Historical nominal ceiling is qualified by skips and mismatched patch binding; root cause does not edit old test outcomes. |
| Sealed post-hoc quantities | reports/next_phases/phase4_posthoc/analysis.py<br>reports/next_phases/phase4_posthoc/label_audit/audit.py | reports/next_phases/phase4_posthoc/analysis.md<br>reports/next_phases/phase4_posthoc/label_audit/analysis.md | phase4/*; All four policies and registered secondary REGRESSION_ERROR counting; pre-registered H1/H1b/H2/H3 label-free and unchanged. |
| Presentation restatements | static report notes | reports/next_phases/PRESENTATION_NOTES.md<br>reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/PRESENTATION_SUMMARY.md | main/*;policy/*;paired83/*;phase4/*;cohort/*; Only a new integrity slide note is added. Older reports remain historical originals; this report supplies the corrections. |

The H1/H1b/H2/H3 completeness hypotheses, runtimes, test counts, label-free selector criteria, native verdict counts, and independent superseded-assertion class agreement do not consume patch correctness labels and therefore do not move. Labels used as historical annotations move only in this separate analysis. Original reports remain archived originals.

## Headline numbers under A → B → B-cpu

Every binomial proportion has an exact two-sided 95% Clopper-Pearson interval. Selector-retention sums include only measured entries; blank historical counts remain unknown and are counted separately, never replaced by zero. `changed_numbers.csv` is the exhaustive flat table of every changed count, numerator, denominator, proportion, interval, derived score or paired statistical summary produced by these registered metric families; `metrics.csv` also retains unchanged values. Values include explicit undefined zero denominators.

| Context | Measure | A | B | B-cpu |
|---|---|---|---|---|
| claims/headline83 | RESOLVED_claim_precision | 69/83 = 83.13% [73.32%, 90.46%] | 70/83 = 84.34% [74.71%, 91.39%] | 72/83 = 86.75% [77.52%, 93.19%] |
| main/headline83/V1 | detection_all_incorrect | 0/14 = 0.00% [0.00%, 23.16%] | 0/13 = 0.00% [0.00%, 24.71%] | 0/11 = 0.00% [0.00%, 28.49%] |
| main/headline83/V2 | detection_all_incorrect | 1/14 = 7.14% [0.18%, 33.87%] | 1/13 = 7.69% [0.19%, 36.03%] | 1/11 = 9.09% [0.23%, 41.28%] |
| main/headline83/V3 | detection_all_incorrect | 3/14 = 21.43% [4.66%, 50.80%] | 3/13 = 23.08% [5.04%, 53.81%] | 3/11 = 27.27% [6.02%, 60.97%] |
| main/headline83/V4 | detection_all_incorrect | 0/14 = 0.00% [0.00%, 23.16%] | 0/13 = 0.00% [0.00%, 24.71%] | 0/11 = 0.00% [0.00%, 28.49%] |
| policy/headline83/full | ACCEPT_precision | 45/52 = 86.54% [74.21%, 94.41%] | 45/52 = 86.54% [74.21%, 94.41%] | 46/52 = 88.46% [76.56%, 95.65%] |
| policy/headline83/full | false_accepts | 7 | 7 | 6 |
| policy/headline83/baseline | ACCEPT_precision | 53/64 = 82.81% [71.32%, 91.10%] | 53/64 = 82.81% [71.32%, 91.10%] | 55/64 = 85.94% [74.98%, 93.36%] |
| policy/headline83/full | correct_acceptance_recall | 45/69 = 65.22% [52.79%, 76.29%] | 45/70 = 64.29% [51.93%, 75.39%] | 46/72 = 63.89% [51.71%, 74.88%] |
| policy/headline83/baseline | correct_acceptance_recall | 53/69 = 76.81% [65.09%, 86.13%] | 53/70 = 75.71% [63.99%, 85.17%] | 55/72 = 76.39% [64.91%, 85.60%] |
| paired83/v2 | detection_all_incorrect | 1/14 = 7.14% [0.18%, 33.87%] | 1/13 = 7.69% [0.19%, 36.03%] | 1/11 = 9.09% [0.23%, 41.28%] |
| paired83/scg | detection_all_incorrect | 0/14 = 0.00% [0.00%, 23.16%] | 0/13 = 0.00% [0.00%, 24.71%] | 0/11 = 0.00% [0.00%, 28.49%] |
| phase4/C_invalid_excluded | detection_all_incorrect | 1/14 = 7.14% [0.18%, 33.87%] | 1/13 = 7.69% [0.19%, 36.03%] | 1/11 = 9.09% [0.23%, 41.28%] |
| phase4/C_invalid_excluded | detection_verdicted_incorrect | 1/10 = 10.00% [0.25%, 44.50%] | 1/11 = 9.09% [0.23%, 41.28%] | 1/9 = 11.11% [0.28%, 48.25%] |
| phase4/C_invalid_excluded | false_alarm_all_correct | 5/69 = 7.25% [2.39%, 16.11%] | 5/70 = 7.14% [2.36%, 15.89%] | 5/72 = 6.94% [2.29%, 15.47%] |
| phase4/C_invalid_excluded | false_alarm_verdicted_correct | 5/48 = 10.42% [3.47%, 22.66%] | 5/47 = 10.64% [3.55%, 23.10%] | 5/49 = 10.20% [3.40%, 22.23%] |
| phase4/C_invalid_excluded | missed_all_incorrect | 9/14 = 64.29% [35.14%, 87.24%] | 10/13 = 76.92% [46.19%, 94.96%] | 8/11 = 72.73% [39.03%, 93.98%] |
| phase4/S_invalid_excluded | missed_all_incorrect | 6/14 = 42.86% [17.66%, 71.14%] | 6/13 = 46.15% [19.22%, 74.87%] | 4/11 = 36.36% [10.93%, 69.21%] |
| cohort/skip_dependent13 | incorrect_count | 4 | 5 | 3 |
| cohort/grader_witness_tasks4 | witness_ceiling_over_all_incorrect | 4/14 = 28.57% [8.39%, 58.10%] | 3/13 = 23.08% [5.04%, 53.81%] | 1/11 = 9.09% [0.23%, 41.28%] |

Total changed metric rows: **1783**. These rows include the originally reported repository, population and raw-scoring-subset sensitivities; duplicate prose citations map to the same computation rather than pretending to be new experiments.

## Interpretation and statistical limits

- B is the primary default-environment interpretation. B-cpu must remain visible because Pylint’s default environment can make otherwise passing old tests skip. No favorable environment is selected as primary after seeing the outcome. Signal correctness rates exclude empty patches, which are not correct/incorrect nonempty candidates; combined-policy including-empty sensitivities preserve the original unsafe-negative convention and retain separate empty columns.
- The original label binding defect is independent of whether a label changes after regrading: all nine mismatches remain provenance failures even when B agrees with A.
- Label propagation cannot repair old grader captures, testcase code, alternative candidate bytes or selector/reference provenance. Historical diagnostic and selector-retention tables keep their fixed identities and are explicitly label sensitivities, not new detection observations. The fixed four-task old-witness ceiling is not expanded with new witnesses found by regrades.
- For signals, FAIL predicts an incorrect patch; PASS is the other binary verdict; incomplete/unavailable outcomes abstain. Phase 4 additionally retains the registered FAIL+REGRESSION_ERROR secondary. For combined policies, ACCEPT predicts correct and FLAG/REJECT withhold. All definitions are unchanged.
- The exact CP intervals apply to binomial proportions. F1 and paired-bootstrap summaries are derived statistics, not binomial proportions, so CP is mathematically inapplicable to them. Existing paired-bootstrap seed 695, 10,000 resamples and row order are retained for policy-score differences; exact McNemar/hypergeometric tests retain their original formulas. Per-test identity proportions are descriptive and clustered within tasks; their CP intervals are not evidence of independent test sampling.
- This analysis does not establish semantic ground truth for harness-resolved patches. The audited labels are grades in the stated environment, and all original metrics remain reproducible under A.

## Reproduction

`env -u PYTHONPATH .venv/bin/python reports/next_phases/phase4_posthoc/label_propagation/propagate.py` reads stored evidence only and regenerates the new artifacts plus the added presentation note. The run manifest is verified before data reads. analysis.json records every evidence/code hash, frozen metric family, root trace and numeric value. Run twice and compare output bytes; no historical report generator is invoked and no existing report is overwritten.
