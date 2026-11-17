# E2E v1.4.1 status

COMPLETE: A1–A7 pass. A1 83/83; A2 all four policies 83/83 with zero health halts; A3 14 ACCEPT / 67 FLAG / 2 REJECT with no differences; A4 three native runners match sealed collection identities and outcomes; A4b registry interface passes; A5 all 48 new tests pass; A6 has zero new failed/error IDs; A7 independent audit passes.

Final registry SHA-256: 9e55c5a82501753f19f5f83cdcab69afe178a9800aaa848918867a5a8af1d5fb. All 83 task rows/operational TaskSpecs are unchanged by the build-provenance refresh. All 83 immutable images are present locally. All 75 frozen-manifest entries match; v1.4.0 files are untouched.

Latest routing branch fetched without tags and merged (already up to date at 983c3f4). Post-merge suite: 1553 passed, 7 skipped, 6 failed, 17 errors; failed/error IDs and statuses equal the pre-merge run and reference set. No reference failure now passes. The approved offline cache resolves all 30 prior sandbox errors.

Release: feature/e2e-v1.4.1; intended annotated local freeze tag e2e-v1.4.1-frozen at the final commit. No model calls, repair rerun, correctness grading, image pulls/builds, or pushes. The user publishes the branch/tag.

Report: reports/next_phases/e2e_v1_4_1/REPORT.md. Commands: RUNBOOK.md there. Decisions include the 31 hash-first argv sources, byte-only golden CSV exception, schema additions, dynamic selected-slot hygiene, persistent ledger/escrow, resume and stop rules. Known limitations and the source-scope note are disclosed in the report. Completed before the Wednesday 18 November 2026, 18:00 ET deadline.
