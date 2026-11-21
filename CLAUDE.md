# Study v1.5 — rules for every session

- Branch `study/v1.5-200`, worktree `~/projects/wt-study`. Plan: `reports/study_v1_5/PLAN.md`.
  Frozen protocol (tag `study-v1.5-prereg`): `reports/study_v1_5/PROTOCOL.md`.
  Tracker: `reports/study_v1_5/STATUS.md`.
- Follow the prompt's design exactly. Do not redesign; if something is ambiguous, stop and ask.
- Never open labels or answer keys before the run they concern is sealed: grading outputs,
  `runs/grading_*`, a submission's `logs/` or `results/`, `per_instance_details.json`,
  `git_peek_suspicious_commits.md`, any `*posthoc*`, `*label*` or `decision_by_correctness*`
  file, and the dataset fields `test_patch`, `FAIL_TO_PASS`, `PASS_TO_PASS`, `hints_text`.
- Never print patch contents into logs or replies.
- After tag `v1.5-frozen`: no changes to `src/` or `configs/`. Stop and report instead.
- "Stop" means stop and report. Do not fix and continue.
- Python: the worktree `.venv` with `env -u PYTHONPATH PYTHONPATH=src` and the HF offline
  variables in `reports/next_phases/task_prep/README.md`.
- Unit gate: no new failures or errors beyond `reports/study_v1_5/unit_baseline_phase1.json`.
- Every phase ends by updating `STATUS.md` and committing it with that phase's commit.
- Keep ponytail off for study work.
## Plugins
- Superpowers: the prompt is the approved design and plan. Skip brainstorming and
  writing-plans; do not ask design questions the prompt already answers. TDD and
  verification-before-completion are welcome. Never create branches or worktrees, merge,
  rebase or open PRs; work only on study/v1.5-200 in ~/projects/wt-study.
- claude-mem: injected memory is background only. If it conflicts with STATUS.md,
  PROTOCOL.md, PLAN.md or the current prompt, those win.

## Agent skills

### Issue tracker

Issues and specs live as local markdown files under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one root `GLOSSARY.md` plus `docs/adr/`, both created lazily. See `docs/agents/domain.md`.

- Tooling and agent-config commits (CLAUDE.md, docs/agents/, .gitignore) are allowed outside
  phases; keep them separate from study commits and never include reports/ or runs/ in them.