# Fix 11/12: executor health, quarantine and guarded launch

**Stopped at G1; launch is blocked.** Fixes 11 and 12 are implemented and tested, but the exhaustive preflight cannot be approved: its first completed task/tree has an unlisted collector failure. No new freeze tag or controlled run was created. Attempt-2 outcomes, verdicts, aggregate results and correctness labels were not read.

## Preflight and scope

Initial branch preflight passed: clean `experiment/v2-execution-repair`, HEAD and live origin `6ae513b3ce6619e1ccfe1431921d35607dae7dc8`. Attempt 2 is quarantined as **"aborted at integrity gate, not analyzed"**; [quarantine marker](attempt2/quarantine.json) retains the existing manifest SHA-256 without modifying its raw captures.

The [scope report](fix11_12_scope/README.md) and [per-task/tree collector CSV](fix11_12_scope/attempt2_collector_health.csv) cover **166 original attempt-2 collection receipts/status rows**. Only `raw/*_validation_*/validation.json` files and frozen selections were opened; collection-only metadata across candidate receipts identifies the earliest initial receipt matching the full selection. No attempt-2 base.json, patched.json, result.json, execution output or prior result reports were read. Each available collection receipt was verified against the existing raw seal. Empty selections are explicitly NOT_INVOKED_EMPTY_SELECTION. Recorded exit codes are per-module; the old receipts did not retain a separate outer-driver exit code, reported as NOT_RECORDED rather than inferred.

All **31 tasks with any failed/partial collector** are listed in [summary.json](fix11_12_scope/summary.json); [error-signature rows](fix11_12_scope/attempt2_collector_failures.csv) provide task/tree/signature counts. The signatures include missing runtests.setup, the GIS backend abort, native exit 5 with no collected items, Matplotlib testing.compare AttributeError, missing test.txt, missing xmlschema and unavailable lightgbm during collection. These are collector-health observations, not task verdicts.

## Fix 11 — source-capability-aware Django setup

Commit `678831b`. The native helper chooses a callable `setup`, otherwise `setup_run_tests`, from the actual checked-out runner. It checks required parameters before invoking setup and returns an explicit COLLECTION_ERROR for unsupported APIs/arguments or bootstrap failure. It never calls a test method. The setup entry point is retained in collection receipts. No version string is used to assume an API: two commits with the same declared Django version can differ.

AST-only inspection and parameter validation resolve **all 31 frozen Django archives: 16 setup, 15 setup_run_tests**. The [per-task/version inventory](fix11_12_scope/django_entry_points.csv) records both setup/teardown availability, signatures and source/archive hashes; [offline implementation choices](fix11_12_scope/fix11_entry_choice.csv) confirm every choice. Seven new unit cases include both APIs, historical signatures, failure closure, historical Python 3.6 syntax and test bodies that would raise if called.

## Fix 12 — G2 through G6 and G1 launch barrier

Commit `c5d54d9`.

- G2 reference sets are built for **all 83 tasks**, from the frozen original V2 run only. [Counts per task](fix11_12_reference/counts.csv), [compressed identity sets](fix11_12_reference/reference_ids.json.gz) and [provenance](fix11_12_reference/manifest.json) retain identities/admission only. A structural JSON projection skips verdict, raw-output and other unwanted values without decoding them; statuses are immediately reduced to admission membership, never kept as outcome classes. The reference is not either quarantined attempt or the Fix 5 projection.
- Live health measures each initial task/tree independently, requires unanimous admission of expanded slots, exempts only proven INVALID_ID, and halts on >=10 lost reference IDs OR >=1% loss. An empty reference has no percentage loss. No verdict participates in this computation.
- Nonzero-input/zero-output stages halt unless their exact task/module/stage and diagnostic match the precommitted exception list. Collector output counts remain native counts; fallback candidates never inflate them.
- Health records are written, flushed and fsynced before another task can start. A halt is recorded before raising; source and runner-stage errors also produce explicit health status. Records contain admission and collector health, not test outcome classes/verdicts.
- The first **37 task representatives** cover every effective runner/repo/version combination, using the lowest instance_id per combination and sorting that prefix by ID; the remaining tasks retain frozen order. [Combination catalogue](fix11_12_scope/runner_repo_versions.csv) and the G1 plan record the exact order. SymPy is its native runner despite historical pytest metadata.
- Collector crashes can fall back only to IDs already statically validated from the same selected code, under the existing module isolation, marked COLLECTOR_FALLBACK. Static unknowns, proven invalids, time-budget exhaustion and listed missing-evidence exceptions do not get fallback. Native errors remain visible. Every runtime stage has explicit status/counts; startup uses help only with the native warning environment for SymPy.
- Execution requires a successful, source/receipt-sealed G1 result for all 166 pairs and the complete G2 reference. Both old freeze tags are rejected by the launcher. No automatic tag, resume, notification or controlled launch was added.

The only pre-listed exceptions are **GIS_GUARD** on the enumerated Django GIS modules and **XMLSCHEMA_MISSING** in pytest-5787/testing/test_junitxml.py, both trees. The [48 exact module scopes](fix11_12_scope/run_health_exceptions.json) were committed with the plan before implementation. No exception was added after G1 failed. They remain missing evidence and do not relax G2. Hypothesis thresholds, B1 and B2 are unchanged.

## G1 stop — zero test bodies

[G1 summary](fix11_12_g1/summary.json), [all planned task/tree statuses](fix11_12_g1/tasks.csv), and [receipt/source seal](fix11_12_g1/manifest.json).

The first completed pair, **astropy__astropy-13977 / base**, passed its pristine-source check and runner start-up, but **seven modules, 105 selected inputs** returned native pytest **exit 5 with zero selected identities collected**. Each has explicit COLLECTION_ERROR/G3 evidence. The captured diagnostics include `Internet access disabled`, `no tests collected`, and a numpy size RuntimeWarning; their presence is recorded without claiming which message caused collection to be empty. None matches either permitted exception. The 105 statically valid fallback slots are marked and retained separately, not counted as successful native collection.

Failed modules:

1. astropy/io/misc/asdf/tags/unit/tests/test_quantity.py (4 inputs)
2. astropy/io/misc/asdf/tags/coordinates/tests/test_earthlocation.py (4)
3. astropy/io/misc/asdf/tags/coordinates/tests/test_skycoord.py (12)
4. astropy/io/misc/asdf/tags/table/tests/test_table.py (14)
5. astropy/io/misc/tests/test_parquet.py (28)
6. astropy/visualization/wcsaxes/tests/test_formatter_locator.py (29)
7. astropy/visualization/wcsaxes/tests/test_wcsapi.py (14)

Per the user's stop rule, the audit was interrupted when this completed failure receipt was observed. The patched-tree collector had started; it was interrupted and its container removed. Status coverage is **one BLOCKED completed pair, one INTERRUPTED pair, 164 NOT_REACHED pairs**. The remaining pairs are **unverified**, not silently passed. All 83 tasks/both trees are listed, but the exhaustive preflight was not completed successfully. The stop log and partial pristine receipt are preserved. **Zero benchmark test bodies were executed.** No selective execution or retry followed the stop, no exception was widened, and no subsequent code fix was made.

## Unit verification and review stop

Final full suite: **1,216 passed, 6 failed, 6 skipped, 17 errors (18.95 s)**. The 23 failure/error identities exactly match the pre-existing environment baseline; no new failures. All **7 Fix 11 and 17 Fix 12 cases** pass, including collector-crash fallback, loss/zero-output halts, fsynced health before next task, deterministic coverage order, projection safety and zero-body G1 wiring. [Unit summary](fix11_12_scope/unit_summary.json); the old failure reasons remain the missing ignored patch fixture, Landlock availability, stale config expectation and historical source seals. Ruff and diff checks pass.

The plan/quarantine commit is `276f710`, before either implementation. Code remains at the tested Fix 12 version; the final report commit adds receipts/documentation only. Stop for review. **Do not approve phase4-plan-frozen-v3 or launch while G1 is blocked.** Any further repair must be label-free and follow the integrity-stop/new-version/new-tag/fresh-task-1 rule.
