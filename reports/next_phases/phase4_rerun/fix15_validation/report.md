Fix 15 implements the five reference/confirmation/G1 rules and the three
additional timeout, interruption and exception requirements. The plan amendment
was committed and pushed as 9fb3cb0 before code. The eight implementation groups
have separate commits, recorded in [scope.json](scope.json). Thresholds, B1,
B2, frozen selections, the original reference artifact and uv.lock are unchanged.

The exhaustive G1 audit is READY: all 83 tasks × 2 trees completed, zero projected
halts, zero projected reference losses, zero fallback slots and zero test-body
executions. Wall time was 3,315.57 seconds. All 35 source hashes and 672 packaged
receipt hashes verify through the launcher's real `require_g1` function. The
manifest SHA-256, verified against phase4_plan.md in committed HEAD, is
`2db4cbc30a2bcaa83df4dd5ec59b6477910ef56f299a5aa74c6a70bcdee2f377`.
The 664 task receipts use lossless gzip; original bytes and their hashes remain
recoverable. [checks.json](checks.json) records the aggregate checks.

Exactly 16 unique Pylint-4970 IDs are excluded on each tree: 32 tree-ID slots.
The fresh containing-directory receipts prove the file is not collected; no
explicit-file import is attempted. The exclusions exactly match the published
[list](../fix15_reference/spurious_reference_ids.json), with no other removals.
Both Pylint projections have zero loss. The current audit's
[reference_hygiene.json](../fix15_g1/reference_hygiene.json) records every slot.

Sixteen trees have an empty original reference and a nonempty G1 native set,
covering 11,146 slots. There are 26 empty original references in total; the other
ten have no native runnable set (empty selection or module skip). The identity
guard applies to every tree. Across all trees G1 contains 112,626 native valid
slots and reports 264 module-skipped slots. INVALID_ID totals remain 572 before
and after Fix 15; the full table is
[invalid_id_comparison.csv](../fix15_g1/invalid_id_comparison.csv).

The worktree environment was rebuilt from the unchanged lockfile using a fresh
uv cache and copied package files. Dataset tests use an identical writable copy
of the existing local cache in offline mode. All 38 tests in test_loader,
test_no_leakage and test_sampler pass; the 30 previous dataset setup errors are
resolved. [Environment evidence](../fix15_environment/README.md) records the
command, versions, cache hashes and kernel probe.

The final full unit suite, run after G1 and checksum sealing, reports
**1,295 passed, 6 failed, 6 skipped, 17 errors** in 37.83 seconds. All 29 Fix 15
guard cases pass. test_v2_scg_paired runs: 47 pass, two fail and 17 encounter its
historical source-integrity barrier during fixture setup. Every remaining
failure/error identity was already present before Fix 15.
[unit_suite.json](unit_suite.json) lists each identity and reason;
[unit_suite.log.gz](unit_suite.log.gz) preserves the complete log.

| Remaining issue | Failures | Setup errors | Reason |
| --- | ---: | ---: | --- |
| Django selection fixture | 1 | 0 | Pre-existing django__django-16899.patch fixture is missing. |
| Shadow isolation | 3 | 0 | Kernel 5.15 exposes Landlock ABI 1; the worker requires ABI 4 and abstains. Known kernel limitation; isolation remains enforced. |
| Historical V2 defaults | 1 | 0 | Old test expects the former four-field 300/600 configuration. |
| Historical V2 freeze | 1 | 17 | Five current verifier files differ from the immutable historical source hashes. |

Existing test maintenance: test_fix8_confirmation now expects confirmation ERROR
to yield candidate FLAKY with global INCOMPLETE, while all six isolated calls
still run. test_fix2_outcomes explicitly disables reruns to test initial-capture
classification; confirmation behavior is covered separately. Empty-reference
skip cases follow the identity-only rule. G1 continuity uses a contained
BaseException; KeyboardInterrupt/SystemExit have separate persistence/rethrow
coverage. Exception fixtures register explicit trees and stages. G1 fixtures
supply their reference cohort. The focused environment/guard run passed 101 tests.

Attempt-2 outcomes, verdicts and labels were not read. No benchmark test bodies
were executed, no tag was created and no experiment was launched.
