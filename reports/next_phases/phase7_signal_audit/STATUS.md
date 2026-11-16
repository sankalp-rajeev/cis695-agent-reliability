# Signal audit status

Updated: 2026-11-16T19:36:56.004386+00:00. Branch: analysis/signal-audit.

HARD STOP in Stage 6: independent verification mismatch in v1_raw_observations.json. The independent runner passed a list where the original runner passed a tuple, producing different out-of-scope diagnostic text. No correction or verification rerun followed the failure.

- Stages 1-4 completed, committed, pushed, and tagged signal-audit-labelfree at d2cc07ab1036bf5a36225fcf8acf2698b5b6e8c4 before any correctness-label source was opened.
- Stage 5 post-hoc analysis completed and pushed in 1bc80f8; never used for a decision.
- Stage 6 compared four CSVs successfully, including v1_adversarial.csv, then failed the detailed raw V1 evidence comparison. V3/V4/recompute/post-hoc independent comparisons: NOT_RUN because of the hard stop. Scientific aggregate conclusions remain provisional.
- No final report or final SHA-256 seal is claimed; signal-audit-sealed was not created. The label-free tag is preserved unchanged.
- Protected verifier, policy, config, and frozen artifacts have no changes. Fifty-five immutable label-free output files match their tagged contents.
- BLOCKED.md states the one decision needed; independent_verification.json and stage6_mismatch_evidence.json preserve the failure. Checkpoint, commit and push these files, verify a clean tree, and stop.

Attempt 1 was aborted after label exposure; this attempt used a fresh session and a file whitelist. No prior attempt file contents were read. No model calls, task execution outside Docker, or non-Git network operations occurred.
