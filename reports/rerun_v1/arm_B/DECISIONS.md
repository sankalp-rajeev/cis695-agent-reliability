# Arm B decisions

## Before grading

- The audited run reported `COMPLETE` for all 92 tasks. Read-only tmux and Docker checks found no tmux server or running containers. The independent SHA-256 inventory matched all 9,252 entries in the runner seal and added the runner seal itself. The source folder remained read-only.
- The seal summary takes decision counts from the live verifier record of each completed task. The ledger job key is the absolute arm directory. Repair calls use the ledger stage `agent`. Amendment A1 moves the one filtered empty-patch task, `django__django-13569`, from the runner's no-patch count to provider-blocked. Spend sums the 6,911 call costs for this job by provider and in total. All calls were settled and no stage escrows were active.
- Amendment A2 governs grading. The worktree and the arm header identify pipeline commit `2a3bf7fa9070ded3dbdb2600831bf83e4247b4b8`. Both `uv.lock` and the worktree interpreter report SWE-bench 5.0.2.
- The oracle ordering guard parses the main study's base `VerificationRecord` with extra fields forbidden. The E2E verifier writes the same base fields and eight additional V1.4.1 fields. The grading-folder adapter will copy only the base fields into `verification_record.full.json`, preserving their values. It will verify the source record's sealed hash and copy `patch.diff` and `repair_record.json` byte for byte. The oracle and its ordering guard stay at the frozen commit.

## Grading handoff

- The operator requested a two-task smoke test and a resumable handoff. The smoke test used the first empty and first non-empty patch in the sealed completion order. The manifest matched before and after the test. The two oracle records remain in the grading directory and count toward the final 92.
- The dataset cache contains only SWE-bench Verified entries in this worktree's `runs/hf_home`. Dataset and Hub access are offline. The unchanged oracle controls harness networking.
- The driver checks for an active arm, harness, and Docker activity before starting each task. It checks periodically during active evaluation and archives an attempt if it detects contention. The current oracle invocation is allowed to clean up before pausing. A retry archives the first oracle record and harness logs so the unchanged oracle starts with a clean harness report path.
- For final labels, `resolved` is true only for the oracle's `resolved` outcome. The oracle outcome and harness error class preserve whether the harness produced a verdict. A missing report uses the logged timeout or patch-application failure when available, and otherwise uses `missing_harness_report`.

| Smoke test task | Oracle outcome | FAIL_TO_PASS | PASS_TO_PASS | Oracle wall time |
| --- | --- | ---: | ---: | ---: |
| `astropy__astropy-13977` | Empty patch | — | — | 0.001409 s |
| `astropy__astropy-14365` | Unresolved (U) | 0/1 | 8/8 | 64.110223 s |

Neither smoke task required a re-run.

## After grading

Finalized and verified 92 labels. See [the report](REPORT.md) for timing and re-runs.

### Post-unblinding tooling deviation, 18 November 2026

Grading paused at 90/92 on `pylint-dev__pylint-8898`. The driver expected a repair record, but the seal contained a byte-empty patch and `agent_absence.json` with reason `AGENT_EXCEPTION:JSONDecodeError`. Commit `8b864b4e178e88fadada356e86a2f845883e1369` allows the grading adapter to use the oracle's empty-patch rule only when the manifest lists the absence record and the patch has the SHA-256 of zero bytes. The adapter copied both sealed inputs byte for byte and recorded the repair record as `NOT_AVAILABLE` with the sealed reason. The harness was skipped. A missing repair record for any non-empty patch still stops grading.

The resumed run finished the two remaining tasks, both `empty_patch`. All 90 previously completed grading, oracle, and attempt receipts matched their pre-resumption SHA-256 digests. The frozen oracle, SWE-bench 5.0.2, and all previously recorded labels remained intact. Finalization and the independent seal, copy, and label verification passed for 92 tasks.

### Harness apply-failure investigation, after unblinding

The grading receipts record five events under `patch_apply_failed` across three tasks. The SHA-256 checks tied each harness intermediate patch to the sealed bytes, including both re-runs. All three patches used LF line endings and ended with a newline.

| Task | First attempt error text | Re-run result | Final outcome and class |
| --- | --- | --- | --- |
| `django__django-13023` | `Patch Apply Failed`. `patch: **** Only garbage was found in the patch input.` The harness exited 0 without a report. | Same error and no report, exit 0. | `infra_error` (X) |
| `django__django-14140` | Git logged `Applied patch django/db/models/query_utils.py cleanly.` Django then raised `TypeError: register_lookup() missing 1 required positional argument: 'lookup_class'`. The harness report set `patch_successfully_applied=false` and `infra_failure=false`. | No re-run. The oracle recorded a non-infrastructure outcome. | `patch_apply_failed` (X) |
| `django__django-16667` | `Patch Apply Failed`. `patch: **** Only garbage was found in the patch input.` The harness exited 0 without a report. | Same error and no report, exit 0. | `infra_error` (X) |

- **`django__django-13023`.** The patch begins with `---` and `+++` file headers and has a range-less hunk header, `@@ class DecimalField(Field):`. A local Git patch parse returned `error: unrecognized input`. Sealed V1 recorded FAIL and `unparseable`, with `patch_applies=true`.
- **`django__django-16667`.** The submission begins with `FINAL_STATUS: RESOLVED` and contains no file or hunk headers. The local Git patch parser returned `error: unrecognized input`. Sealed V1 recorded FAIL and `unparseable`, with `patch_applies=true`.
- **`django__django-14140`.** Sealed V1 recorded PASS and `patch_applies=true`, consistent with Git's observed success. The applied patch changed `register_lookup` from a class method to an instance method. The import traceback stopped the suite before it produced any test results. Both output markers were present. Reprocessing the retained log with the installed harness parser reproduced the exact report. The parser found neither a test result nor evidence the suite ran, and the infrastructure classifier returned no match, so the report retained its default `patch_successfully_applied=false`.

The frozen V1.4.1 adapter sets `patch_applies` when the `does_not_apply` violation is absent. For the two malformed submissions, the parser returned `unparseable` before an apply check. The boolean therefore coexists with V1 FAIL and gives no evidence of a successful application. The third event is a harness report classification after a successful application. These findings are descriptive and the three final X labels are preserved.
