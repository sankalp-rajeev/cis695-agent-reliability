The candidate integrates the experiment branch’s accumulated verifier/SCG work and Phases 1–6b into a branch ready for review. Phase 6b is sealed and independently verified: INCONCLUSIVE, 12/12 references kept, 3.33% median per-task reduction, zero stable traced/untraced disagreements, and 1464.838s total execution cost versus 741.721s baseline. Do not adopt this selector on that evidence.

Main would gain the earlier diagnostic/cost work, repaired Phase 4 execution and provenance, sealed Phase 5 replay and tier analysis, exploratory Phase 6a runtime evidence, and the scoped child-aware Phase 6b tracer, reproducible harness, reports and independent verifier. This integrates the experiment branch’s full accumulated history. At the pre-notes snapshot `9b4a607`, the candidate was 145 commits ahead and zero behind `origin/main` (`8add43ed85da775491f4ecf457401d5d319324ad`), with 6,859 changed files, predominantly accumulated reports. Main is an ancestor and has not been checked out, committed to, merged, reset or pushed by this run.

The history includes commits referenced by the unchanged tags `phase4-run-sealed`, `phase5-plan-frozen`, `phase5-plan-amendment-a1` and `phase6b-plan-frozen`. New annotated tags are `phase6b-harness-frozen` (code commit `92a1e8e04d4cc788322eca3152739504dced2319`) and `phase6b-run-sealed` (result commit `df00cc6849a503cc31ace3768b7eff13aefd12af`). A1 was approved and appended before all evaluation captures. The frozen scripts/src/tracer code remains unchanged.

Full unit-suite comparison:

| Run | Passed | Skipped | Errors | Failures |
|---|---:|---:|---:|---:|
| Supplied known baseline | — | — | 47 | 6 |
| Starting commit, isolated worktree | 1347 | 6 | 47 | 7 |
| Candidate | 1375 | 6 | 47 | 6 |

Candidate errors are exactly 30 read-only Hugging Face cache-lock errors plus 17 existing drift errors. Every candidate error/failure is present in the starting-commit run by name. New errors or failures beyond the supplied baseline: **none**. The starting-commit run’s seventh failure is `tests/unit/test_env.py::test_assert_clean_interpreter_passes_under_the_test_runner`: using the shared editable venv from a different worktree places that worktree’s paths outside the imported environment guard’s trusted project root. The candidate passes it. Both raw runs include every unit test; no outcome was removed or rewritten, and no unrelated tests were fixed.

The six existing candidate failures are:

- `tests/unit/test_selection_ground_truth.py::test_django_16899_selects_admin_checks`
- `tests/unit/test_superseded_shadow.py::test_kernel_blocks_actual_file_access_in_classifier_process`
- `tests/unit/test_superseded_shadow_v2.py::test_v2_worker_still_cannot_open_oracle_files`
- `tests/unit/test_superseded_shadow_v2.py::test_only_one_extra_base_reuses_patch_confirmation_and_preserves_signal`
- `tests/unit/test_v2_scg_paired.py::test_frozen_configuration_defaults_are_unchanged`
- `tests/unit/test_v2_scg_paired.py::test_archived_v2_inputs_are_portable_without_changing_frozen_policy`

Raw logs/JUnit and hashes are in `runs/phase6b_merge_checks_20261114/`; `reports/next_phases/phase6b_run/unit_comparison.json` records every issue name and the comparison. All 27 Phase 6b unit cases pass within the full candidate suite; Stage 1 also passed the 38 combined tracer/Phase 5 synthetic checks and all three Docker smokes. Scientific verification independently checked all 5,678 numeric values and 7,579 raw-file hashes. The seal manifest has 7,601 run/result entries.

`experiment/callgraph-typeprop` is **not merged** into this candidate: its verified remote tip `e1a3ed1c74fd304493c3fe3811de755af77e306c` is not an ancestor. This is reported without merging it.

The candidate is pushed as `merge-candidate/phase6b-into-main`; main remains unchanged. No PR was opened: `/usr/bin/gh` is gitsome rather than the GitHub CLI and has no `auth status` command, so the required already-authenticated GitHub CLI condition could not be established. No credentials were installed or changed. The candidate is ready for review with the documented pre-existing test baseline and the INCONCLUSIVE scientific result.
