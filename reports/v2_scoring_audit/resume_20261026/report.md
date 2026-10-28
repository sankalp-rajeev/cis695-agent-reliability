# Frozen V2 scoring audit — resumed execution

[confirmed] The saved `../protocol.json` and frozen inputs were verified by SHA-256 and used unchanged. Previous audit files and production code are preserved. New files are confined to this resume directory. No selector/call-graph work, network, image pull/build, dependency installation, model, agent or commit occurred.

[confirmed] **Three of eight authorized pairs ran; five are blocked by missing local frozen images.** Docker is reachable. Missing images: django-12209, django-13297, django-14140, django-14631 and sphinx-10435. They were not replaced or downloaded and their missing rerun results were not relabeled NOT_AVAILABLE. The original eight labels remain {'FAIL': 5, 'PASS': 3}.

| Phase | Result |
|---|---|
| 2 | [confirmed] Six full-selection passes, one base and one patched per available patch; raw bytes and batch events persisted before parsing |
| 3 | [confirmed] Five concrete candidates; 30 additional individual attempts, three per tree/test; every candidate has four observations per tree |
| 4 | [confirmed] Old and unchanged proposed parser applied offline to identical Phase-2 logs with identical confirmation evidence |
| 5 | [confirmed] Four actual-format parser tests pass; three new paired-raw replays; zero valid historical raw re-scores |
| 6 | [confirmed] Matched three-patch metrics and matched one-patch usable metrics; no corrected all-83 estimate |

## Paired observations

| Patch | Raw-covered selected IDs, base/patch | Old parsed IDs, base/patch | Proposed parsed IDs, base/patch | Committed / old replay / proposed replay | Usable |
|---|---|---|---|---|---|
| pylint-dev__pylint-6528 | 217/218; 217/218 | 191; 191 | 217; 217 | PASS / PASS / PASS | False |
| pylint-dev__pylint-7277 | 70/70; 70/70 | 57; 57 | 70; 70 | PASS / PASS / PASS | True |
| pytest-dev__pytest-5809 | 4/7; 4/7 | 4; 4 | 4; 4 | FAIL / FAIL / FAIL | False |

[confirmed] The proposal empirically fixes admission of 26 parameter families for pylint-6528 and 13 for pylint-7277, on each tree. It changes zero patch verdicts. The copied proposal is not applied to production. Its family-level aggregation can still conceal different failing concrete cases when a family fails on both trees [inferred limitation, not demonstrated here]. No Django raw format was observed, so Django parser tests and suffix/multiline-ID hypotheses remain unresolved.

## Stability and diagnosis

| Patch/test | Base initial + repeats | Patched initial + repeats | Classification |
|---|---|---|---|
| pylint-dev__pylint-6528 / `tests/test_self.py::TestCallbackOptions::test_generate_toml_config` | failed + ["failed", "failed", "failed"] | failed + ["failed", "failed", "failed"] | [confirmed] STABLE; PRE_EXISTING_FAILURE |
| pylint-dev__pylint-6528 / `tests/test_self.py::TestCallbackOptions::test_generate_toml_config_disable_symbolic_names` | failed + ["failed", "failed", "failed"] | failed + ["failed", "failed", "failed"] | [confirmed] STABLE; PRE_EXISTING_FAILURE |
| pylint-dev__pylint-7277 / `tests/test_self.py::TestCallbackOptions::test_generate_toml_config` | failed + ["failed", "failed", "failed"] | failed + ["failed", "failed", "failed"] | [confirmed] STABLE; PRE_EXISTING_FAILURE |
| pylint-dev__pylint-7277 / `tests/test_self.py::TestCallbackOptions::test_generate_toml_config_disable_symbolic_names` | failed + ["failed", "failed", "failed"] | failed + ["failed", "failed", "failed"] | [confirmed] STABLE; PRE_EXISTING_FAILURE |
| pytest-dev__pytest-5809 / `testing/test_pastebin.py::TestPaste::test_create_new_paste` | passed + ["passed", "passed", "passed"] | failed + ["failed", "failed", "failed"] | [confirmed] STABLE; TRUE_REGRESSION |

[confirmed] There is one stable real regression: pytest `TestPaste.test_create_new_paste`. The old test at `testing/test_pastebin.py:131` expects a Python lexer; the candidate sends `lexer=text`. Base passes 4/4 observations and patched fails 4/4. Its headline post-hoc label is right, so this is a V2 existing-test design limit in this environment, not a parser bug. [inferred] It is consistent with the historical false positive, but absent historical raw logs and image digests prevent proving historical causation.

[confirmed] In each pylint case, `TestCallbackOptions.test_generate_toml_config` and `test_generate_toml_config_disable_symbolic_names` fail on both trees 4/4 times; observed logs report TOMLKitError from adding a table to a dotted key. The base-failure rule excludes these four observed failures. No initially differing case was omitted from confirmation selection. Zero candidates are flaky; no timeout occurred.

[unresolved] These observed pre-existing failures do not establish why the headline wrong pylint patches passed the historical verifier. No official/gold failing-test list was used to diagnose them. Django-13297 remains UNKNOWN because its image is missing. Do not equate evidence of baseline absorption with proof that it absorbed the official failing test.

## Denominators, missing outcomes and metrics

[confirmed] Usable V2 means: **V2 ran at least one selected test on both trees and every selected test has a recorded base and patched outcome.** The parser-independent raw coverage flag was fixed before comparison. Missing IDs and process-level timeouts do not manufacture per-test outcomes. Completed responsible batches and concrete emitted outcomes are required for selected families. ERROR/SKIP are recorded outcomes; at least one concrete PASS/FAIL/SKIP must have run per tree. Only pylint-7277 qualifies.

[confirmed] Missing on both trees:
- `pylint-dev__pylint-6528`: `tests/test_self.py::TestRunTC::test_environ_pythonpath`
- `pytest-dev__pytest-5809`: `testing/test_pastebin.py::TestPasteCapture::test_pass`
- `pytest-dev__pytest-5809`: `testing/test_pastebin.py::TestPasteCapture::test_fail`
- `pytest-dev__pytest-5809`: `testing/test_pastebin.py::TestPasteCapture::test_skip`

[confirmed] Pytest reports its three missing IDs as not found; pylint-6528 reports a not-found selection too. No missing ID is assigned a raw PASS. Partial aggregate PASS is nevertheless allowed by the unchanged production scoring rule, as demonstrated by pylint-6528. This establishes incomplete-evidence PASS, not an individual missing test being classified PASS.

| Population/version | Patches (right/wrong) | PASS / FAIL / NOT_AVAILABLE | FAIL precision, wrong/FAIL | FPR, FAIL-right/all-right | FPR on usable right |
|---|---|---|---|---|---|
| paired_new_raw_subset / committed_original_same_new_raw_subset | 3 (1/2) | 2 / 1 / 0 | 0/1 | 1/1 | 0/0 |
| paired_new_raw_subset / old_parser_replay_same_raw | 3 (1/2) | 2 / 1 / 0 | 0/1 | 1/1 | 0/0 |
| paired_new_raw_subset / proposed_parser_replay_same_raw | 3 (1/2) | 2 / 1 / 0 | 0/1 | 1/1 | 0/0 |
| same_subset_raw_complete_usable_only / committed_original_same_new_raw_subset | 1 (0/1) | 1 / 0 / 0 | 0/0 | 0/0 | 0/0 |
| same_subset_raw_complete_usable_only / old_parser_replay_same_raw | 1 (0/1) | 1 / 0 / 0 | 0/0 | 0/0 | 0/0 |
| same_subset_raw_complete_usable_only / proposed_parser_replay_same_raw | 1 (0/1) | 1 / 0 / 0 | 0/0 | 0/0 | 0/0 |

[confirmed] All three versions on the matched new-raw subset yield PASS=2, FAIL=1, NOT_AVAILABLE=0. Proposed FAIL precision is **0/1 = 0%**, versus the requested global wrong-patch base rate **14/83 = 16.8675%** and this targeted subset's own wrong-patch rate **2/3 = 66.6667%**. False-positive rate over the subset's right patches is **1/1 = 100%**. On the single usable patch, FAIL precision is **0/0 undefined**, usable-right FPR is **0/0 undefined**, and wrong detection is **0/1**. These deliberately selected, incomplete observations cannot estimate global precision lift or a corrected global false-positive rate.

[confirmed] Historical valid raw re-scoring subset: **0 patches, []**. New paired-raw replay subset: **3**, explicitly listed in `raw_evidence_subset.json`; original committed metrics are shown on those identical three IDs beside both replays. The existing 83-row screen provides parsed/aggregate records, not qualifying paired historical raw logs. All 75 non-target patches remain unexecuted. Do not replace historical study outcomes with new-environment replays.

## Environment and practical limits

[confirmed] All observed images run Python 3.9.20; pylint runner is pytest 7.4.4 and pytest-5809 raw headers identify pytest 4.6.6.dev9+g8aba863a6. Current image IDs/RepoDigests, observed commits, patch hashes, frozen selections, batch exits and durations are recorded in `environment_sanity.csv` and raw preflight files. Full-pass and individual timeouts are 300 s; initial pair budget 600 s. All observed initial pairs complete well within budget.

[unresolved] Historical image digest, historical runner version and independently recorded historical base commit are absent from frozen inputs. Current HEAD was recorded and frozen candidate applicability checked, but historical identity is not proved. STABLE describes four repeated observations per side in the current image, not demonstrated equivalence to the original study environment.

[inferred] This evidence does not support strengthening V2 into a correctness gate: one stable old-test regression occurs on a right patch, two wrong patches still receive PASS, and only one replay meets the predeclared raw-completeness requirement. This is an interpretation of the fixed protocol, not a policy or selector change.

[confirmed] Preservation checks passed for all prior audit files, production sources, frozen inputs and newly captured raw logs. Commands are in `commands.jsonl`, raw logs/events in `phase2/` and `phase3/`, and offline parser checks in `parser_tests.stderr`. Execution stopped after the authorized audit; five missing images remain the only execution blocker.
