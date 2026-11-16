# Signal audit status

Updated: 2026-11-16T19:57:16.598917+00:00. Branch: analysis/signal-audit.

COMPLETE: Stages 1-6. The corrected full independent verification passed with zero mismatches, comparing 25 CSV tables and eight JSON artifacts and independently rerunning all 14 V1 cases. Exact raw diagnostic text matched.

- The first verification failed because its own script passed a list where the analysis passed a tuple. The user authorized correction; cf58a54 contains the isolated one-line runtime fix and 770a717 the related expected JSON-array constructor fix found during the pre-rerun review. Comparison functions are unchanged.
- All 65 Stage 1-5 artifacts, including every CSV and result file, retain their pre-fix committed SHA-256 hashes. No analysis producer was rerun. The initial failed receipt and mismatch evidence remain unchanged; the successful receipt has a distinct filename.
- V1: 10/11 rejection probes caught; 3/3 controls passed; 13/14 total expectations met. Assertion loosening is missed.
- V3: zero decision effects in frozen83 and all_tasks; two stored V3 FAIL / ACCEPT cases.
- V4 frozen83: PASS 68, FAIL 1, NOT_AVAILABLE 14, all fourteen explicitly generator no-output. All other absence classes zero in that cohort. Raw generator stdout remains NOT_AVAILABLE.
- Conservative S_invalid_missing V2-only recompute: ACCEPT/FLAG/REJECT 52/30/1 -> 13/68/2; all four accounting sensitivities retained.
- Original false accepts surviving audit: 6/7 default, 5/7 CPU-2048. Aggregate original-decision false accepts are 7 default and 6 CPU-2048; recomputed false accepts are 3 and 2 respectively. Stage 5 was post-hoc and never used for a decision.
- REPORT.md and artifact_manifest.sha256 are the completion deliverables. Final annotated seal target: signal-audit-sealed at the completion commit, pushed after that commit.
- Label-free tag remains signal-audit-labelfree at d2cc07ab1036bf5a36225fcf8acf2698b5b6e8c4, pushed before label access. No protected verifier, policy, config, or frozen artifact was changed. No model calls, non-Docker task execution, or network beyond project Git operations occurred.

Attempt 1 was aborted after label exposure; this attempt used a fresh session and a file whitelist. No prior aborted attempt contents were read.
