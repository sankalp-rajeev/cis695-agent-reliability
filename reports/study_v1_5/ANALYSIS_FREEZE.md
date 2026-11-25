# Analysis freeze (tag `study-analysis-frozen`)

The study's analysis is fixed here, before any test-set label is fetched or opened (amendment B6). It was written on branch `study/analysis`, from `study/v1.5-200` at `60f5ac1`, so that the running Phase 12 chain (`chain_p12`, Gemini 2.5 Flash) was not disturbed. The only labels used during development were arm B's dev labels, which are allowed, and made-up labels for a synthetic test.

## Files (sha256)

| file | sha256 |
|---|---|
| `scripts/analyze_v1_5.py` | `236fefbe5a356841e656e38a70c6938a52616b16a12e446712f2628fe9ffb49e` |
| `tests/unit/test_analyze_v1_5.py` | `45e5e11b4c4198b00ffc8a99db80e909d1cbb235a04fac8727303959f9d325ea` |
| `scripts/decide_v1_5.py` (imported, unchanged) | `aca6638114519889a031d9bf4aad8bd4d8023cf9b4c319cc065f6cd8a856f5cc` |
| `src/reliability/verifier/policy_v1_5.py` (unchanged) | `ab7f24dc50ebc67872979392f28581dc89c0a8f58e78a4587b6108026c9a3cb4` |

**Seed:** 20261126. **Bootstrap:** 10,000 resamples.

## Inputs

- **Runs.** Each system's sealed Phase 12 run. Decisions are recomputed from each sealed record exactly as `decide_v1_5.py` does: v1.5 evidence with A6, using the patch's added files. The switches are read from `configs/verifier/v1_5.yaml` at the annotated tag **`v1.5-frozen-2`** (r2, r6 and r6b on; r3 off), via `decide_v1_5.frozen_switches`.
- **Labels.** Official SWE-bench per-instance resolved status, stored as `{"system", "labels": {id: {"resolved", "official_patch_sha256"}}}`.
  - Where an official `patch.diff` exists, its sha256 must equal our sealed input bytes before our newline normalization. That is the input manifest's `source_sha256` for the Claude and Gemini official inputs, and `patch_sha256` otherwise (amendment B6).
  - A mismatched label is not used. It is listed and counted.
- **Gold.** The Phase 11 run `runs/study_test_gold_b1` (H3, and V4 against gold).
- **Recall.** The Phase 11 A3 audit summary, for the no-recall sensitivity.

## Scope

- **Headline.** Batch 1 (`configs/study_v1_5/test_batch1_final_ids.json`), minus:
  - the task ids in `configs/study_v1_5/headline_exclusions.json`, which include `astropy__astropy-7671` (B11);
  - the (system, id) pairs in `runs/study_v1_5/headline_exclusions_pending.json` (B13, pending), or any pair-level entries merged into `headline_exclusions.json` later.
- **Empty patches** are out of the verifier metrics and counted under RQ1.
- **Ids without a label** drop out of the labelled metrics and are counted.
- **Sensitivities.** (1) All batch tasks, with no exclusions. (2) The headline minus tasks with generator recall in the Phase 11 audit.
- **Pooling.** Pooled numbers use the minimum set (B1): gpt-4.1-mini, Claude Sonnet 4 and Gemini 2.5 Flash. o4-mini is never pooled (B6). Per-system tables cover every system given.

## Metrics (per system and pooled; non-empty labelled patches)

| metric | definition |
|---|---|
| base rate | correct ÷ n (Wilson 95%) |
| ACCEPT precision | correct ACCEPTs ÷ ACCEPTs (Wilson) |
| lift | precision ÷ base rate |
| accept-weighted base rate (B4) | Σ over systems of (system ACCEPTs ÷ all ACCEPTs) × system base rate; lift = precision ÷ this |
| coverage | correct ACCEPTed ÷ correct (Wilson) |
| false-accept rate | wrong ACCEPTed ÷ wrong (Wilson) |
| wrong rejected | wrong REJECTed ÷ wrong (Wilson) |
| correct rejected | correct REJECTed ÷ correct (Wilson) |
| FLAG rate | FLAGs ÷ n (Wilson) |
| held-back difference | not-ACCEPTed rate, wrong minus correct (Newcombe method 10); two-sided Fisher exact on held back × correct |

## Hypotheses

- **H1.** Pooled ACCEPT precision > pooled base rate. The task-clustered bootstrap resamples whole tasks with replacement. H1 is supported if the 2.5th percentile of (precision − base rate) is above 0. Resamples with no ACCEPT, no correct or no wrong patch are skipped and counted.
- **H2.** Wrong patches are held back more often than correct patches. Same bootstrap. Supported if the 2.5th percentile of the held-back difference is above 0.
- **H3 (B5).** Gold REJECTs ÷ non-empty gold patches under v1.5 frozen, as a point estimate with its Wilson 95% upper bound. Reported for all 60 and for the headline scope. Not a pass/fail test.

## Comparison tables (same signals)

- **v1.4.1.** `FullPolicyV141` on the v1.4.1 evidence of the same records.
- **V1+V2-only baseline (B4).**
  - REJECT if the patch doesn't apply, integrity fails, there is prohibited manipulation, or V2 FAILs.
  - ACCEPT if integrity is PASS, V2 is PASS and there is no high-severity risk flag.
  - FLAG otherwise.
  - V3 and V4 are ignored (`FullPolicy(require_reproduction=False)` with V3 and V4 NOT_AVAILABLE).
- **Within-task comparison (B4).** Tasks where systems in the pooled set disagree on correctness: the ACCEPT rate on correct and on wrong patches, and correct/wrong patch pairs in the same task counted as concordant (correct ACCEPTed, wrong not), discordant or tied.
- **V4 on correct public patches vs gold (B4).** The V4 full-pass rate of correct pooled-set patches, against the gold V4 full-pass rate on the same tasks, with a 2×2 table.

## Pre-registered secondary analyses S1–S3

These were decided before any test-set label was fetched or opened. Reason: **inherited v1.4.1 rules fired on public-agent patterns absent from the dev set.** On Phase 12's label-free records, the public patches trip V1 findings that arm B's and gold's patches never did: config edits, harness edits, binary blobs and conflict markers. Each is evaluated with the v1.5 frozen switches on modified evidence:

- **S1.** `high_severity_risk` does not block R6. Risk flags are informational.
- **S2.** The V1 findings `unexpected_config_edit`, `harness_file_edit`, `conflict_markers` and `binary_blob` do not fail V1. `does_not_apply` and `unparseable`, and every other violation, still do. If only these four were present, integrity becomes PASS, and prohibited manipulation is recomputed from the violations that remain.
- **S3.** S1 and S2 together.

The report also lists every task where `conflict_markers` fired only on lines starting `=======`. V1 records the first marker line per file. Only its first seven characters are compared, and no line text is printed.

## Tests

- **Unit tests** (`tests/unit/test_analyze_v1_5.py`, 29 pass): Wilson, Newcombe and Fisher against published values; metric counts, rates, lift and the accept-weighted base rate; bootstrap determinism; S1, S2, S3, v1.4.1 and the V1+V2 baseline; the `=======` detector; scope exclusions; label hash mismatches.
- **End to end on arm B dev data** (labels allowed): runs `study_dev_armb` (11 kept), `_2` (40) and `_3` (django-13158), with dev gold `study_dev_gold` + `_f`. The report is in [analysis_test/ARMB_DEV_TEST.md](analysis_test/ARMB_DEV_TEST.md).
  - It reproduces ADOPTION.md's adopted-set row: ACCEPT 20 correct / 4 wrong, precision 83.3%, coverage 80.0%. It has REJECT 0/7 instead of 0/8, because B12 moved django-13158 from REJECT to FLAG when it was re-verified in `_3`.
  - v1.4.1 on the same signals equals ADOPTION.md's switches-off row (13/3, 81.2%).
  - Dev gold H3 is 0/51 (Wilson upper 7.0%).
  - The label hash check passed 51/51.
- **Synthetic** (made-up random labels on the sealed Phase 12 runs; not a result): it exercised pooling, the within-task comparison, the headline task and pair exclusions, a missing label and a hash mismatch, and it is not kept. Headline scope 57 tasks, with 55 and 54 patches after drops; all-tasks 58 and 58; H3 1 of 57 (sympy-14248, as in Phase 11).
