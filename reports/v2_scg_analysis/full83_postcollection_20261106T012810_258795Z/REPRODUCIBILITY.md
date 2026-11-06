# Post-collection analysis provenance

This directory contains new read-only scientific analysis of the completed run.
It is outside both the freeze and collected results. No original artifact was
overwritten, no graph/selector was rebuilt and no benchmark/Docker test was run.

Original inputs:

- Execution worktree: `/home/sankalp/projects/cis695-v2-scg-paired-review-b030e50`,
  clean and detached at `b030e508d849926b9a2260c70e1091adebfee993`.
- Freeze: `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/paired_frozen`.
- Results: `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results`.
- Correctness: pinned Git bytes of `docs/results_100.csv`, with final-study
  source-run provenance and exact candidate hashes checked against the verified
  patch manifest. `correctness_source_pinned.csv` preserves those authoritative
  bytes. Working-tree CRLF and four recorded rerun aliases were resolved without
  changing labels or candidates; see `analysis_incidents.json`.
- Witnesses: six named historical existing-suite witnesses from
  `reports/v2_discovery_cleanup/audit/known_witnesses_retained.json`.

Analysis order:

1. Verify completion marker, protocol/plan/results digests and 83/166 counts.
2. Run pinned `scripts/v2_scg_paired.py summarize` **without labels**; the new
   output exactly reproduced the existing `metrics.json`.
3. Prepare hash-bound post-hoc sidecars and run the same existing summary with
   `--labels` and `--witnesses`. No selectors or verdicts are recomputed.
4. `analyze_completed.py` verifies all paired/native records, frozen seals,
   selected lists, per-call capture hashes and recorded source checks; it derives
   diagnostics from recorded results, reusing the read-only monitor's explanation
   helpers. It reads no benchmark module as Python code.
5. `diagnostic_replays.py` replays saved output strings through the unchanged
   pytest parser. ANSI stripping is diagnostic input normalization only, with
   all native results preserved. It also records existing missing-pytest and
   shadow-isolation diagnostics, without executing either component.
6. `finalize_analysis.py` independently recomputes label counts, checks every
   regression's base/patched/confirmation/base status sequence, writes compact
   inventories and verifies protected files unchanged.

`analysis_commands.json` records exact argument arrays and environments, and
`unlabeled_summary.command.json` / `labeled_summary.command.json` include exit
codes and timings. The preparation helper already invokes the labelled summary;
its command is listed separately as provenance, not a second required invocation.
The analysis scripts create outputs exclusively. Reproduction requires a fresh
analysis directory with `analysis_configuration.json` pointing to these immutable
inputs and a successful unlabeled summary first; do not rerun output-producing
commands over this completed directory.

Key evidence:

- `integrity_verification.json`: record pairing, seals, 780 raw capture hashes,
  91 source checks and expected no-verdict abstentions.
- `labeled_summary.json`: unchanged harness metrics and historical-witness metrics.
- `analysis_metrics.json`: coverage, overlapping diagnostic reason counts,
  graph/availability strata and useful SCG evidence cases.
- `task_arm_inventory.csv`, `incorrect_patch_outcomes.csv`,
  `paired_dispositions.csv`: compact task-level comparisons.
- `regression_evidence.json`, `failure_diagnostic_excerpts.json`,
  `historical_witness_execution.json`: concrete positive/false-alarm evidence.
- `parser_and_environment_diagnostics.json`: parser replay, missing pytest in all
  five SymPy images, and the unavailable shadow classifier's seven UNCERTAIN
  predictions.
- `original_artifacts_before.json` / `final_preservation_check.json`: all 766
  frozen files and 1,290 result files unchanged during analysis.
- `external_analysis_inputs.json` and `historical_report_inputs.json`: code,
  helper and historical-report hashes used by this analysis.

Source hashes establish inspected file equivalence, not complete runtime import
provenance. A failed/incomplete runner capture can have valid file hashes.
Historical labels, witness retention and raw observations are kept as separate
evidence tiers; none is silently substituted for a native verdict.

`analysis_artifact_sha256.json` seals all new files except itself and its detached
checksum file. `SHA256SUMS` records that manifest's SHA-256. No original freeze or
result seal is replaced. Summary stdout/stderr and all source scripts are retained.
