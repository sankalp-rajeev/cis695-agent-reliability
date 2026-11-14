Fix 16 implements the executor-failure principle in four implementation commits.
The plan amendment was committed and pushed as 67b3fc3 before code. H1, H1b, H2,
H3 thresholds, B1, B2, frozen selections, the original reference artifact and
uv.lock remain unchanged. [scope.json](scope.json) records the commits and checks.

G2 and the G1-collected check count identity failures, using **lost >= 10 AND
lost/reference >= 1%**. Test outcomes retain their identities. Reference
PASS/FAIL/ERROR becoming SKIPPED is separate environment drift under that same
threshold. G3 checks collection stages only. Execution/admission zero output
cannot create a health halt.

Observed process death produces raw CRASH, scored as ERROR. Completed outcomes
are preserved; remaining unstarted IDs become NOT_REACHED. This includes both
nonzero and zero `os._exit`, plus SIGSEGV. A module-execution identity failure
requires no test progress on both its first attempt and retry, including a silent
zero exit. It contributes infrastructure NOT_RUN to the thresholded loss count.
The fatal Python diagnostic is not parsed as a phantom pytest ERROR identity.

Confirmation scoring requires base PASS 3/3 and patched non-PASS 3/3. Repeated
patched ERROR/CRASH yields REGRESSION_ERROR; mixed PASS/non-PASS observations or
a timeout yield FLAKY. Missing confirmation identity/evidence remains unavailable
evidence. Confirmation health still runs inside each call before scoring.

Receipt consumers verify manifest-listed bytes before parsing. Unlisted plain
collection JSON cannot shadow a listed gzip receipt. Both declared and derived
reference removals must exactly equal the published 16 Pylint IDs on each tree;
no other removal is accepted. Exact PASS/FAIL/ERROR drift membership is derived
from hash-pinned original V2 files through a structural projection that never
decodes verdicts or labels. XFAIL/XPASS are excluded from that drift membership.
[Reference provenance](../fix16_reference/manifest.json) preserves all original
reference memberships and source hashes. Attempt-2 files were not accessed.

A fresh exhaustive G1 was required because eight existing pins changed:
phase4_launch.py, phase4_stage_preflight.py, container.py, g1_reference.py,
regression.py, result_parser.py, run_health.py and validated_run.py. The final
audit covers **83 tasks x 2 trees: 166 READY**, with zero projected halts,
identity losses, environment-drift slots, fallback slots or test-body executions.
Wall time was 3,344.23 seconds. All 39 source hashes and 672 receipt hashes verify
through the real launcher. The final manifest checksum, stored in committed
phase4_plan.md, is:
`27972b20156c9c972c618e3e547d692184ed948026aa79e700543780d7369bde`.
The 664 task receipts use lossless gzip with their original byte hashes retained.
[checks.json](checks.json) records the verification and exact 32-slot exclusion.
A 66-pair partial audit was preserved under runs before adding zero-exit coverage;
the final audit starts fresh and reuses none of those receipts.

All 44 Fix 16 cases pass, covering real subprocess deaths, raw capture/scoring,
AND thresholds, whole-tree ERROR, drift, two-attempt module failures, manifest
shadowing/tampering and removal mismatch blocking. The existing task-1 halt test
still uses actual native validation and the real health-record writer: ten
INVALID_ID losses stop task 2 before scoring. Existing tests were updated where
they encoded OR thresholds, admission loss, execution G3, single-ID halts,
ERROR-as-FLAKY, or retrying after observed test progress. INVALID_ID still counts
as identity loss; a single lost identity is below the new halt threshold.
Manifest fixtures now commit the real Fix 16 pin and listed receipt hashes.

The full unit suite was rerun after G1 and checksum sealing:
**1,339 passed, 6 failed, 6 skipped, 17 errors** in 42.90 seconds. Its failure/error
identity set exactly matches Fix 15 and the pre-G1 run. All 38 dataset tests pass.
The remaining test_v2_scg_paired results are 47 passed, two failed and 17 setup
errors. [unit_suite.json](unit_suite.json) lists every remaining identity and
reason; [unit_suite.log.gz](unit_suite.log.gz) preserves the complete log.

| Remaining issue | Failures | Setup errors | Reason |
| --- | ---: | ---: | --- |
| Django selection fixture | 1 | 0 | Pre-existing django__django-16899.patch fixture is missing. |
| Shadow isolation | 3 | 0 | Kernel 5.15 exposes Landlock ABI 1; the worker requires ABI 4 and abstains. Known limitation; isolation is enforced. |
| Historical V2 defaults | 1 | 0 | The test expects the former four-field 300/600 configuration. |
| Historical V2 freeze | 1 | 17 | Current verifier files differ from immutable historical source hashes. |

Attempt-2 outcomes, verdicts and labels were not read. No benchmark test bodies
were executed, no tag was created and no experiment was launched.
