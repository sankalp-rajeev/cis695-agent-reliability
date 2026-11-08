Fix 14 implements the twelve pre-code rules in phase4_plan.md. B1, B2,
thresholds, and frozen selections are unchanged. The plan amendment was pushed
as 89c59d1 before implementation. The eight code groups have separate commits.

G1 covers all 83 tasks × 2 trees, with zero test bodies. Its gate is
READY; source and receipt hashes verify.
INVALID_ID totals: 1620 before → 572 after. The complete per-task/tree table
is [invalid_id_comparison.csv](../fix14_g1/invalid_id_comparison.csv). The baseline
collector source matches e1cadb4, and all 671 saved baseline receipt hashes verify.
Astropy-7606 (pytest 3.3.1) falls from 537 to 1 INVALID_ID on each tree:
536 corrected identity slots per tree. All other pytest installations are
at least 4.0; the five native SymPy images have no pytest installed. All 52
frozen pytest-run images have pip-show receipts in
[pytest_versions.csv](../fix14_diagnosis/pytest_versions.csv).

SymPy-13480 records all 18 selected Sage IDs per tree as MODULE_SKIPPED,
reason module_skip: disabled, observed inside the task's own runner. Pylint-4970
uses a native containing-directory receipt before declaring the lint input
not_a_test_module; it is never explicitly imported. Successful directory
collection retains its native collector context. A selected file is collected independently only when positive selected-item discovery
permits isolation from unrelated directory errors; discovery diagnostics remain
in the receipt, without new exceptions. Matplotlib-23476's precise
module import exception remains missing evidence, scoped to the pre-registered
module, stages, and diagnostic; explicit-file collection reproduces it while
directory collection succeeds.

The code sends static rejects to native collection; native success overrides
static rejection. Static/native disagreement remains missing evidence, and a
successful native absence does not become collector fallback. G3 excludes
agreed-absent instances, including an extra non-runnable parent probe for a
cross-module expansion. Concrete expansion members still require unanimous
admission in G2. Explicit pytest fixture declarations are static helpers only
when native collection also confirms absence.

All 159 focused regression checks pass. The full unit suite: 6 failed, 1236 passed, 6 skipped, 47 errors in 101.75s (0:01:41). Its failure/error identities exactly
match the before-change run (6 failed, 1205 passed, 6 skipped, 47 errors in 97.09s (0:01:37)). [unit_suite.json](unit_suite.json)
records both lists and log hashes. Existing NumPy import errors remain part of
that baseline. The focused regression suite covers real collection drivers,
pytest-3-style IDs, Unicode parameters, native-over-static admission, empty
references, confirmation crash/loss/zero output, partial fallback, ordinary skip
loss, module skips, SymPy disabled, native directory config, per-pair write and
BaseException failures, and an actual task-1 health halt stopping task 2 through
the launcher without a fake health-record writer.

All 664 task receipts are stored as lossless gzip files. The packaged G1 gate
and frozen-reference readers verify successfully; the empty-reference loader
uses G1 data for 16 trees and 11,146 reference slots. These counts describe
native collection. [checks.json](checks.json) records the verification.

The old INVALID_ID exemption test
`tests/unit/test_fix12_run_health.py::test_only_proven_invalid_can_exempt_a_reference_identity`
was replaced by `test_proven_invalid_reference_is_still_lost`. Also updated:
`test_only_successful_native_absence_or_static_proof_can_be_invalid` →
`test_only_agreed_static_and_native_absence_can_be_invalid`, and
`test_no_runnable_owner_reason_survives_native_rejection` →
`test_no_runnable_owner_still_needs_native_absence_proof`. Module-skip fixtures
now supply their G1 empty set, and the empty native-module test distinguishes
successful collection from a static/native disagreement.

Attempt-2 outcomes, verdicts, correctness labels, and benchmark test bodies
were not inspected. No tag was created and no experiment was launched.
