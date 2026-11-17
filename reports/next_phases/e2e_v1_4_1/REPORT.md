# E2E v1.4.1

**Verdict: IN PROGRESS. The approved input exceptions are resolved; no acceptance freeze has been created.**

| Check | Result | Evidence |
|---|---|---|
| A1 | PASS, 83/83 | Package ArchiveTree and unchanged select_tests reproduce identical IDs and order; A1.json. |
| A2 | Initial PASS, 83/83; final replay pending | All four policies match per-test outcomes and signals, with zero health halts; all 1,799 sealed files verified (3,488,110,239 bytes). A2.json and seal_check.json. |
| A3 | PASS, 83 tasks | 14 ACCEPT / 67 FLAG / 2 REJECT; identical to Phase 7 primary S_invalid_excluded; zero unattributed differences. A3.json and decisions_83.csv. |
| A4 | Initial PASS; final checkpoint rerun running | Django, native SymPy bin/test, and pytest all match sealed G1 identities and all four policy outcomes; --skip-v4 used. |
| A4b | PASS | Prepared cohort/origin gives identical operational TaskSpec/BaseSourceSpec; wrong hash, duplicate ID, and missing field refused; A4b.json. |
| A5 | PASS, focused mocked checks | Attributed V2 absences continue through V3/V4; systemic/integrity/budget stops and frozen-patch resume are covered. New tests total 44/44 pass; final suite pending. |
| A6 | PROVISIONAL PASS | Approved offline cache resolves all 30 sandbox errors; no failed/error ID beyond the reference. New tests: 44/44 pass. Final suite and merge rerun pending. |
| A7 | Initial PASS; final checkpoint rerun pending | Standard-library-only checker rehashes registry/frozen sources, compares A1 recorded arrays and raw A2 outcomes, and checks live receipts and policies. |

The shared schema is documented in docs/TASK_SPEC_SCHEMA.md. The generated registry SHA-256 is 9e55c5a82501753f19f5f83cdcab69afe178a9800aaa848918867a5a8af1d5fb. Its two optional artifact-path fields rebuild PreInstallSpec without renaming or removing shared fields. The registry contains no patch, selection, outcome, or correctness data.

All 31 approved Django sources were hash-verified before argv-only whitelist projection; the exact file/hash list is in DECISIONS.md. All 75 freeze-manifest hashes match, including the expressly approved byte-only golden CSV check. approved_input_access.json and approved_input_preflight.out retain the evidence. No frozen verifier file was modified.

The worktree-local offline dataset cache contains only the Verified dataset and matching Hub entry: 15,423,138 copied file/symlink bytes (hf_cache_copy.json). The required full suite uses:

```bash
env -u PYTHONPATH HF_HOME=/home/sankalp/projects/wt-e2e/runs/hf_home HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1 PYTHONPATH=src .venv/bin/python -m pytest -p no:cacheprovider -rfE
```

Its current comparison has zero new failed/error IDs and no reference failure newly passing (unit_comparison.offline_cache.json). No tests or reference files were changed. Final results will replace this progress report after implementation and the latest routing-branch merge.

Decisions, each with a one-line reason, are in DECISIONS.md. New-instance registries depend on the separate task-prep job. The patched-tree drift guard is intentionally weaker because only the base receives intersected Fix 16 drift identities. A4 has not yet run; --skip-v4 evidence cannot yet be claimed. No repair rerun or model call has been made. The user will push the branch; this agent makes local commits only.
