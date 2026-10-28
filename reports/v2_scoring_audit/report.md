# V2 scoring audit — amended protocol and Phase 1

[confirmed] The five requested committed right/FAIL candidate IDs were identified solely for cohort scope. No grader, gold patch or official test list has been opened for this audit. All candidate patches and original selections are copied/hash-frozen under this directory; no production code or prior report was changed.

[confirmed] Your five fixes and two notes are frozen in `protocol.json` before Docker/test execution. Phase 2 is one full selected-suite pass per side; Phase 3 adds at least three individual reruns per side for every raw base/patched difference (either direction) and every base FAIL. Any within-tree PASS/FAIL mixture is FLAKY. Four observations per side including the initial run are required for STABLE.

[confirmed] Usable V2 is defined before execution: **V2 ran at least one selected test on both trees and every selected test has a recorded base and patched outcome.** Raw coverage, not parser-specific success, fixes the same paired denominator for old and corrected metrics. Missing outcomes are not fabricated passes.

[confirmed] Full-pass timeout: 300 s per tree; 600 s per initial pair. Individual confirmation timeout: 300 s per tree/attempt. Read-only Docker preflight timeout: 20 s. No historical per-task override was found in the inspected snapshots; 300/600 s matches `src/reliability/verifier/regression.py:122`.

[unknown] Historical image IDs/digests are absent from the inspected V2 snapshots/cache/schema. Tags are recorded but do not establish environment-hash equality. Preflight will record current image IDs/digests and explicitly preserve UNKNOWN if comparison is impossible; environment drift will not be called flakiness.

## Existing evidence

| Patch | Selected | Stored V2 | Base cache | Existing primary diagnosis |
|---|---:|---|---|---|
| pytest-dev__pytest-5809 | 7 | FAIL | present | [unknown] UNKNOWN |
| django__django-12209 | 3319 | FAIL | present | [unknown] UNKNOWN |
| django__django-14140 | 2334 | FAIL | present | [unknown] UNKNOWN |
| django__django-14631 | 4469 | FAIL | present | [unknown] UNKNOWN |
| sphinx-doc__sphinx-10435 | 90 | FAIL | present | [unknown] UNKNOWN |
| pylint-dev__pylint-6528 | 218 | PASS | missing | [unknown] UNKNOWN |
| pylint-dev__pylint-7277 | 70 | PASS | missing | [unknown] UNKNOWN |
| django__django-13297 | 8155 | PASS | missing | [unknown] UNKNOWN |

[confirmed] Five existing Group-4 V2 rerun records name regression IDs, and five base caches preserve parsed baseline statuses. They contain no paired pre-parser runner logs and cannot establish the required stability repetitions. All eight same-study snapshots have selected-ID unions and aggregate histograms. `phase1_existing_evidence.csv` records exact snapshot line evidence, duplicate counts, cached failed-base IDs and named prior regressions.

[confirmed] Source review: pytest parser exact ID admission `container.py:365` drops parameterized case output if the selected ID is its family. Django fallback `container.py:399` includes an unqualified suffix match and last-write assignment at `:405`; collisions/duplicate output need raw-log checking. Selection emits families at `selection.py:407`; Django conversion is at `:441`. Missing/timeout results remain NOT_RUN/TIMEOUT at `regression.py:213`; base failure is excluded at `:237`; the current flake rerun is one-sided at `:303`. Patch PASS with partial execution is possible at `:314`–`:328`. Per-test final classifications are not serialized by `run.py:376`.

[inferred] These establish source-level mechanisms, not that any specific historical FAIL or PASS was caused by them. No individual primary cause is forced. All filenames in the previous paragraph are under `src/reliability/verifier/`.

[confirmed] Corrected re-scoring will cover only the raw-evidence-supported subset, whose size/IDs will be reported explicitly, with original metrics on the identical subset. The eight deliberately selected targets will never be presented as all-83 corrected results. Only raw formats actually observed in audit reruns may supply parser test fixtures.

[inferred] PRE_EXISTING_FAILURE covers a real patched failure absorbed by a confirmed failing base. TRUE_REGRESSION on a post-hoc right patch is a V2 design limit, not automatically a bug. Interpretation 6 will state corrected FAIL wrong/total counts against **14/83**, and separately state the subset's own wrong-patch rate; no label-based scoring tuning.

[unknown] Phases 2–6 await environment preflight. No benchmark or parser-unit tests have run.

## Final execution status

[confirmed] **Execution is blocked: no local Docker engine endpoint is available.** The distro Docker wrapper says WSL integration is unavailable. The Windows CLI initially hit a sandbox socket restriction; the same read-only query was then authorized outside the sandbox and reached Windows, where both local named pipes were absent. This is an engine availability failure, not a sandbox approval rejection and not a test result.

| Read-only preflight | Recorded result |
|---|---|
| distro `docker version` | [confirmed] Exit 1; Docker unavailable in this WSL distro |
| Windows CLI, sandboxed | [confirmed] Exit 1; WSL vsock permission error |
| Windows CLI, outside sandbox, `dockerDesktopLinuxEngine` | [confirmed] Exit 1; local pipe not found; `Server: null` |
| Windows CLI, outside sandbox, legacy `docker_engine` | [confirmed] Exit 1; local pipe not found; `Server: null` |

[confirmed] Every command was printed and recorded in `commands.jsonl` before execution, with a 20-second timeout. Stdout/stderr bytes and exit/status/duration are unchanged under `preflight/`. No network endpoint was used by the two Windows queries: both explicitly addressed local named pipes. No service was started and no image was pulled, built, installed or substituted.

## Phase status

| Phase | Result |
|---|---|
| 1: existing evidence and frozen amended protocol | [confirmed] Complete for the available records; per-patch cause remains UNKNOWN |
| 2: initial raw base/patch collection | [unknown] Blocked before any container launch; 0 observations |
| 3: bidirectional/base-FAIL confirmation | [unknown] 0 initial runs and 0 additional reruns on either tree; no STABLE/FLAKY labels |
| 4: same-raw-log old/fixed comparison | [unknown] No qualifying raw log pair; not performed |
| 5: actual-format parser tests and raw-only re-scoring | [unknown] Source-only risk screen completed; no observed raw formats, tests or valid re-scores |
| 6: paired corrected metrics | [unknown] Raw-evidence subset size 0; rates undefined, not zero |

[confirmed] `raw_test_outcomes.csv` inventories **18,662 requested selected IDs**, but its `record_kind` explicitly says UNEXECUTED_REQUEST_INVENTORY. Raw ID, tree outcomes, runner exits, timeout results, test duration and test stdout/stderr references are blank. The engine failure is not written as a test FAIL/TIMEOUT/NOT_AVAILABLE. `regression_reruns.csv` records the unmet three-additional-reruns requirement and zero completed attempts, not synthetic observations.

[unknown] Image-hash equality cannot be established: the historical digest was not found in the inspected V2 metadata and the stopped engine prevents current image inspection. Runner/Python versions and base commit could not be checked in the image. `environment_sanity.csv` records all eight planned tags, candidate hashes, timeouts and UNKNOWN environment checks. No execution has been mistaken for flakiness or study-environment equivalence.

## Source-only parser assessment and scope limit

[confirmed] The current source contains the exact-admission parameter-family defect at `src/reliability/verifier/container.py:365`, independently of oracle correctness labels. The proposed local diff is unchanged from the preceding source review and remains unapplied. [unknown] Without new raw runner formats and repeat outcomes, this audit cannot validate or replace that proposal as an empirically justified final fix, nor show that it caused any target's verdict.

[inferred] Family aggregation in the carried-forward proposal is incomplete for full case-level differential scoring: a family failing on both trees can conceal a new failing case. The Django parser's ambiguous suffix matching and last-write handling also require observed-format evidence. These limitations are stated rather than covered with outcome-directed synthetic fixtures. `tests.txt` therefore reports NOT RUN.

[confirmed] The stored-evidence risk screen covers all **83** nonempty headline rows, without reading oracle/grader/gold fields. Selected-ID unions are available for **19 confirmed study snapshots** and **5 local-only, final-identity-unverified records**; the other **59** lack detailed stored selections. Local-only evidence is not substituted for confirmed final-study evidence.

[inferred] Static base-archive inspection flags **21** available-selection records as plausibly affected (explicit parameter families or Django parser exposure); **62** remain UNKNOWN, including missing-selection records. This is a risk screen, not proof of a changed V2 result. Exact IDs, parameter/decorator file-line evidence, duplicate/normalization counts, and missing evidence are in `affected_stored_records.csv`.

[confirmed] **Valid raw-evidence re-scoring subset: 0 patches, IDs `[]`. Original metrics on that same subset also contain 0 patches.** The older normalized baseline caches and named-regression summaries do not satisfy the requirement for paired pre-parser logs. `metrics_before_after.csv` contains paired empty-subset rows and undefined rate fields; zero numerators/denominators there describe an empty cohort, not an observed zero-error result. No corrected all-83 result is claimed.

[confirmed] For orientation only, the oracle-free committed V2 outcome tally is PASS=64, FAIL=6, NOT_AVAILABLE=13. These original labels do not establish the newly defined raw-complete usable denominator. The previous report's PASS-or-FAIL denominator is not reused as usable under this audit's stricter definition.

[confirmed] `additional_reruns_needed.csv` lists the exact **75 patches outside the authorized eight**, the raw evidence needed and whether their original selection must first be recovered. None was rerun. The authorized eight are separately listed in `target_scope.json` and remain blocked. No additional run is authorized by this report.

[confirmed] The raw-collection gate stayed closed. Other than the narrow, explicitly requested committed right/FAIL cohort lookup, this audit did not read new oracle outcomes, grader records, gold patches or official failing-test lists. No post-hoc label was used to select a confirmation test, diagnose a failure, design a parser fix or tune scoring.

## Direct answers

| Question | Answer |
|---|---|
| 1. Real parser/scoring bug? | [confirmed] Source-level parameterized-ID admission defect. [unknown] Empirical effect on these runs and final case-level fix are not established. Partial aggregate PASS alone is not evidence an individual timeout was scored PASS. |
| 2. Did it cause any of the five right-patch FAILs? | [unknown] No qualifying raw rerun/repeat evidence. Existing parsed regression IDs do not establish parser causation. |
| 3. Did it cause any of the three PASS misses? | [unknown] No qualifying paired raw per-test evidence; do not assign cached/aggregate failures to a named test. |
| 4. How many apparent regressions were real? | [unknown] Six previously named parsed V2 transitions across five patches; zero newly validated. 'Zero validated' does not mean zero real. |
| 5. How many were flaky? | [unknown] No initial/repeat audit outcomes, so neither STABLE nor FLAKY can be assigned. |
| 6. Does corrected FAIL carry signal beyond the base rate? | [unknown] Corrected FAIL precision is 0/0 (undefined) on the zero-patch evidence subset, compared explicitly with the requested base rate 14/83 = 16.8675%. No corrected precision lift can be calculated; a targeted-eight statistic would not answer the population question. |
| 7. Hard gate or advisory? | [inferred] Remain unresolved pending raw evidence and environment identity. No gate or policy was changed, and no recommendation was tuned using correctness labels. |

[inferred] After raw collection becomes possible, interpretation must keep stable TRUE_REGRESSION on a post-hoc right patch separate from implementation bugs: a correct behavioral change can legitimately break an old test, which is a V2 design limit. Stable failed-base absorption is PRE_EXISTING_FAILURE. Neither observation authorizes changing the rule using gold outcomes.

## Reproduction and stop boundary

[confirmed] Commands executed in this audit: `python3 -B reports/v2_scoring_audit/audit.py prepare`; `python3 -B reports/v2_scoring_audit/audit.py preflight`; the separately printed/recorded Windows named-pipe queries; and `python3 -B reports/v2_scoring_audit/finish_blocked.py`. These performed artifact analysis or Docker version checks only. No benchmark or parser-unit test command ran.

[confirmed] All required output filenames exist. Original code, policies, frozen study artifacts and existing reports are unchanged. The new frozen candidate/selection inputs and protocol are hashed; preflight evidence remains separate from test observations. Stopped at the unavailable-engine boundary. No selector work, coverage experiment, graph engineering, testmon, Ollama, model, agent or ablation was started.
