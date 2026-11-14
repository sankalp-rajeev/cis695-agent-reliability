# Fix 11/12 scope: collection health only

Only attempt-2 native-collection receipts were read: no base.json, patched.json, result.json, test execution logs, verdicts, outcome aggregates or labels. Each candidate collection receipt SHA-256 matches the attempt-2 seal; collection-only metadata was inspected to identify the earliest initial receipt. When multiple receipts exist, the first receipt with the complete frozen selection is the initial collector. Empty selections have an explicit NOT_INVOKED_EMPTY_SELECTION row.

The per-task/tree [health CSV](attempt2_collector_health.csv) covers all 166 pairs. Tests collected means selected concrete runnable identities recorded by native validation, not all unselected items in a containing file. The old receipts do not retain a separate outer-driver exit code; that field is explicitly NOT_RECORDED rather than invented. Actual per-module exit-code distributions are reported separately from semantic per-ID failures: Django can catch initialization errors and return process status 0 while every ID reports COLLECTION_ERROR. [Failure signatures](attempt2_collector_failures.csv) list every affected task/tree and signature; [summary](summary.json) lists all affected tasks.

## Django archive entry points

All 31 archive hashes match frozen metadata. AST inspection only; no archive source imports or execution. Sixteen expose setup and fifteen expose setup_run_tests. Per-task signatures, source hashes and available teardown names are in [django_entry_points.csv](django_entry_points.csv).

| Django version | Tasks | Entry point |
|---|---:|---|
| 3.0 | 3 | setup |
| 3.1 | 2 | setup |
| 3.2 | 10 | setup |
| 4.0 | 1 | setup |
| 4.0 | 1 | setup_run_tests |
| 4.1 | 6 | setup_run_tests |
| 4.2 | 5 | setup_run_tests |
| 5.0 | 3 | setup_run_tests |

All **37 distinct effective (runner, repo, version) combinations** and their lowest-ID representatives are in [runner_repo_versions.csv](runner_repo_versions.csv). SymPy uses its native runner; frozen metadata calls it pytest, and the repaired executor already detects bin/test.

The only pre-listed stage exceptions are the GIS backend abort on frozen Django GIS modules and missing xmlschema in pytest-5787/testing/test_junitxml.py, on either tree. [run_health_exceptions.json](run_health_exceptions.json) enumerates exact task/module/stage scopes and required messages before code. Other collection/import/deselection errors are not silently added to the exception list.
