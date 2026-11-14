# Phase 6b status

Start: 2026-11-14T07:28:16Z. Wall-clock deadline: 2026-11-14T17:28:16Z.
Branch: experiment/runtime-instrumentation.
Stage: 1, child/scope completeness repair and gates in progress.
Last completed step: preflight, existing-capture child table, observation-only
metadata instrumentation, and synthetic regression gates (28 passed before and
after observation instrumentation). Report-only smoke finished: existing parallel gate halted at 100% incomplete.
Old-rule diagnostic fractions: Matplotlib 1/4, Django-13033 4/4, parallel
Django-12965 16/16. Outcomes match in each smoke; 3 parallel workers ran tests.
These are diagnostics only. Raw captures, summary and manifest are preserved.
Starting HEAD: 8ee6c5230b70308acaf182a1e6e2a5b13cece415.
Draft checkpoint HEAD: da0d971.
Current checkpoint HEAD: this commit (resolve with git log -1 -- this file).
Existing protected tags: phase4-run-sealed, phase5-plan-frozen,
phase5-plan-amendment-a1, phase6b-plan-frozen. No tags created or changed.

Preflight: supplied draft files preserved; 276 GiB available; Docker 26.1.3
reachable with host access; default python 2.7.18, system python3 3.8.10, project
.venv Python 3.11.17; uv 0.12.23; git 2.25.1. Remote branch matched starting HEAD
and SSH access works. `gh` has no auth command; draft-PR availability unresolved.
No applicable AGENTS.md found. No label files opened. No model calls.

Amendment A1 approved by the user and committed/pushed alone as 6d558e8.
Original frozen plan remains a byte-identical prefix (SHA-256
71311b86285ab42f0402e1542e64be049ab78c11750de68fb1a0925e38ce9043).
Child-rule implementation and explicit scope records complete; 35 synthetic
gates passed, including new branches, exec replacement, posix_spawn, scope
isolation and the 5% cutoff on every smoke. Repair iterations used: 1 / 5.
All three repaired smoke gates pending.
Evaluation not started. All 13 tasks pending in eval_set.json order.
Stages 2, 3, 4 and 5 pending. No scientific verdict or headline metrics verified.
Merge candidate not ready. Next: all three repaired smokes, harness execution
checkpoint/resume checks, then harness freeze. The A1 blocker is resolved.

Protected tag object IDs verified unchanged:

- phase4-run-sealed: ba55b83560fa6c4cc1f2fe220c09387a648473b0
- phase5-plan-frozen: d4af4b870dd6f24b3fac61233b04c0c12b39f24a
- phase5-plan-amendment-a1: 97969395d0992959e6c0096fc6967babf0b17fdd
- phase6b-plan-frozen: 2388a0aeceacae1b395f40c38caae3f52262c89f
