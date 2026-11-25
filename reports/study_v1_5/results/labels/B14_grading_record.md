## B14 (pending, not committed). gpt-4.1-mini batch 1 labels from our grader

**When.** After tag `study-analysis-frozen` and after every batch 1 seal (gpt-4.1-mini, Claude Sonnet 4, Gemini 2.5 Flash).

**Why.** gpt-4.1-mini (`20250720_mini-v0.0.0`) published no per-instance results: its `logs/` prefix in the submissions bucket is empty, the experiments repository folder has only `metadata.yaml`, `logo.svg` and `git_peek_suspicious_commits.md` (upstream unchanged), and its leaderboard entry has the aggregate only (no `per_instance_details`).

**New rule.** gpt-4.1-mini's labels come from our swebench 5.0.2 grader, called as arm B was graded (`reliability.oracle.runner`'s harness call: `swebench.harness.run_evaluation`, SWE-bench Verified test split, one instance, `--max_workers 1`, `--timeout 1800`), on the exact sealed input bytes of the Phase 12 run (sha256 checked before each call). They are validated by agreement with the official labels on the B6 sample of 30 (system, id) pairs graded with the same grader on the same sealed bytes. The agreement rate is reported, not a gate.

**Agreement.** 30 sample pairs graded; 10 have both an official and our label; 10 agree (100.0%). Per system: {'claude-sonnet-4': {'agree': 10}, 'gemini-2.5-flash': {'no_official_label': 7}, 'gpt-4.1-mini': {'no_official_label': 13}}. The sample's gpt-4.1-mini pairs have no official label (none was published), so they are not comparable. Disagreements: none.

**gpt-4.1-mini labels.** 60 graded: resolved 11, unresolved 47, no label 2 (outcomes {'infra_error': 2, 'patch_apply_failed': 20, 'resolved': 11, 'unresolved': 27}).

Files: `runs/study_v1_5/labels/gpt-4.1-mini_ours/`, `runs/study_v1_5/labels/agreement_ours/` (per pair: predictions, harness log, report, result).
