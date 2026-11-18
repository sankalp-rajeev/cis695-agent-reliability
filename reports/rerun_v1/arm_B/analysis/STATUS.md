# Arm B analysis status

## 18 November 2026, Stage 2

After Sankalp authorized the real-label run, both input files were taken from the verified grading commit `bf832e9d9dd686d6255c01ca656b3d401271cec4`. Their Git blobs were byte-identical at results head `9b07499dd3cf561c05e522bc3bcad0572d1c0805`. The columns, allowed outcomes, task IDs and patch hashes passed preflight. The grading verifier passed for all 92 cases. [Input provenance](input_provenance.json)

All 9,253 sealed input files passed their manifest check. The scripts matched the freeze tag. The analyzer ran once with real labels under `--stage 2`. The independent checker passed with zero mismatches across 13 CSVs, 5,107 rows, and `counts.json`. [Checker receipt](checker_receipt.json)

The report uses the checked results and includes the three documented deviations and the descriptive X notes. The copied session-1 disclosure matches the SHA-256 in A3. [Arm B report](REPORT.md)

The final manifest binds the contents of this directory. Stage 2 ends at the annotated `rerun-armB-analysis-sealed` tag.

## 18 November 2026, Stage 1 resumed after the audit coverage fix

Sankalp authorized a label-free fix to the audit's nested e2e V4 discovery. The fix at `073294a6853d390a032f7f66a3e8b7b357e8a27b` on `analysis/leakage-gaps` adds the explicit `tasks/<id>/verification/v4/cache/<id>/generation_trajectory.jsonl` layout, validates the inner task ID, and preserves duplicate detection across the three layouts. The 167 synthetic leakage unit tests passed.

Before and after the fresh offline audit, all 9,253 sealed files passed `sha256sum -c`. The manifest independently lists 91 repair and 51 V4 trajectories under `tasks/`. The audit's `source_trajectories` is 142, and the per-role source paths match the manifest. `pylint-dev__pylint-8898` has no repair trajectory. Its verified `agent_absence.json` records `AGENT_EXCEPTION:JSONDecodeError`.

| Audit | Role | Trajectories | T3-name tasks / findings | T3-content tasks / findings | T4 tasks / findings | Awareness tasks / findings |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Partial | Repair | 91 | 1 / 1 | 13 / 19 | 0 / 0 | 16 / 20 | |
| Partial | V4 | 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | |
| Full | Repair | 91 | 1 / 1 | 13 / 19 | 0 / 0 | 16 / 20 | |
| Full | V4 | 51 | 4 / 4 | 27 / 55 | 0 / 0 | 27 / 54 | |

Across both roles, the full audit found T3-name evidence on 4 tasks, T3-content evidence on 30 tasks, and T4 evidence on 0 tasks. Awareness findings affected 33 tasks. The partial audit and its receipt are preserved under `leakage_audit_partial_superseded`. The full audit has 328 files covered by [leakage_audit.sha256](leakage_audit.sha256), SHA-256 `ab576cff28861b03e311df7f0be2202495eb638307e6587153dcb51c346d4c90`.

The analysis scripts pass lint. The analysis and independent checker passed the Stage 1 label-free case, the seeded mixed synthetic case, the all-resolved and all-wrong patch cases, and the synthetic Arm B self-pair. Each checker run reported zero mismatches. Zero denominators produced `NOT_AVAILABLE`. The self-pair shared 51 patch tasks with zero decision or correctness differences. The label argument gate was tested for both scripts. The [synthetic checker receipt](../../../../tests/fixtures/rerun_arm_analysis/checker_receipt.json) records the script, fixture, seal, and audit hashes. Generated result tables are under the ignored `runs/synthetic_check/` directory.

The Stage 1 freeze commit contains the scripts, fixtures, checker receipt, full and superseded audit outputs, and this log. At the Stage 1 freeze, Stage 2 was pending operator authorization. No real labels or grading output were accessed.

## 18 November 2026, Stage 1 hard stop at the contamination audit

Protocol §9 requires coverage of repair and V4 trajectories. The audit ran successfully from `wt-leakage` at `8f3f25337ab977070dadc46640e553be7a0aba3a`, but its scope contains 91 observed repair rows and zero observed V4 rows. The audit's 182 role rows include 91 placeholders for unobserved V4 trajectories. `pylint-dev__pylint-8898` has no repair trajectory in the seal and no audit row.

The seal lists 51 V4 trajectories at `tasks/<id>/verification/v4/cache/<id>/generation_trajectory.jsonl`. At the recorded audit commit, `discover_arm` in `src/reliability/benchmark/rerun_leakage.py` checks the root-level `_reproduction_cache/<id>/` and `tasks/<id>/` generator layouts. Neither pattern reaches the nested V4 cache. This was verified from manifest path names and the audit's own coverage metadata. Both `sha256sum -c` passes succeeded and the seal membership matched all 9,253 regular files.

The partial audit has 277 files and its [checksum manifest](leakage_audit_partial_superseded.sha256) has SHA-256 `ae4c98f08b58b07546334dc59a8ae39e097b157caf390b8c5829d0486241e22a`. These counts cover the repair audit.

| Finding | Tasks | Findings |
| --- | ---: | ---: |
| T3-name | 1 | 1 |
| T3-content | 13 | 19 |
| T4 | 0 | 0 |
| Awareness | 16 | 20 |

### Completed checks

- The disclosure SHA-256 matched. The draft matched the exact prompt text after restoring the placeholder. A3 was committed and tagged as `rerun-protocol-v1-amendment-a3` at `eed59d29b10bcb87030b966779235450051218a6`.
- The `analysis/rerun-v1` worktree starts at `0b57889` and has its dedicated offline frozen environment.
- The label-free recomputation reproduced 92 of 92 live decisions (5 ACCEPT, 42 FLAG, 45 REJECT). All 41 empty patches were REJECTed, including one provider-blocked task, `django__django-13569`. The 51 patch tasks split 5 ACCEPT, 42 FLAG and 4 REJECT. There were 0 agent-infrastructure tasks and 40 V2 reports. Total ledger spend was $17.88918096 and matched the seal to the cent.
- The checker's standalone known-answer tests passed. At this point the full synthetic checker suite had not run and draft lint findings were still open.

- 18 November 2026, before unblinding. Git normalized line endings in both audit tier CSVs during the initial local commit. Added path-specific Git attributes to preserve the original tool output bytes and checked the stored audit blobs against their original receipts. The final local freeze tag includes this preservation change.
