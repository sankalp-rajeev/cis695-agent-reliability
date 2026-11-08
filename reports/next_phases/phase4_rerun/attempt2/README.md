# Phase 4 attempt 2: capture seal and integrity stop

**Status: ABORTED_INTEGRITY — executor bug; aggregate analysis stopped.** The driver completed all 83 tasks, but only **five of the six required historical native FAIL tasks retain FAIL evidence**. Process completion is not acceptance of the controlled run.

## Preflight and raw capture seal

The worktree passed preflight on `experiment/v2-execution-repair`, clean at `phase4-plan-frozen-v2` / `f840ce93f52d0a09462bc69124c00f3545b50519`; live origin matched. No executor code, frozen selection, image, threshold, or baseline was changed.

[manifest.json](manifest.json) seals **all 1,642 files, 3,269,760,712 bytes** in ignored `runs/phase4_v2_attempt2_20261107T223159Z/`, including its existing capture manifest. All 1,641 hashes in that existing manifest agree with the new independent SHA-256 scan. Raw captures were not moved or modified. The manifest records freeze tag/commit, the launcher argv observed in the prior live health check, and start/end timestamps.

- Start: 2026-11-07 22:32:19.416675 UTC.
- End: 2026-11-08 02:56:27.981976 UTC.
- Driver wall time: **15,849.070585 seconds (4 h 24 min 9 s)**.
- Driver completion: COMPLETE, 83 task completions, no driver error. The analysis integrity gate below overrides acceptance of that run.

No attempt-1 captures/outcomes or correctness labels were read. Only the six required native FAIL tasks were examined before the gate stopped analysis.

## Required FAIL integrity gate

[Six-task CSV](native_FAIL_integrity.csv) records all four policy/accounting combinations and the original witness identities. The five retained tasks have stable 3/3 base PASS and 3/3 patched FAIL observations for their original witnesses.

| Required task | Policy C | Policy S | Original native FAIL evidence |
|---|---|---|---|
| django-12209 | FAIL | FAIL | Retained, stable |
| django-14140 | FAIL | FAIL | Retained, stable |
| django-14631 | NOT_AVAILABLE | NOT_AVAILABLE | **Lost: native collection blocked both trees** |
| matplotlib-25479 | FAIL | FAIL | Retained, stable |
| pytest-5809 | FAIL | FAIL | Retained, stable |
| sphinx-10435 | FAIL | FAIL | Retained, stable |

The verdicts in this table are identical with INVALID_ID excluded or treated as missing. This is the required integrity check, not the requested full 83-task verdict table.

## Diagnosed executor bug

Task: `django__django-14631`, Django 4.0, base commit `84400d2e9db7c51fee4e9bb04c028f665b8e7624`.

The frozen collector at [collection.py](../../../../src/reliability/verifier/collection.py:57) unconditionally accesses `runner.setup`:

```python
params = inspect.signature(runner.setup).parameters
runner.setup(**dict((k, v) for k, v in values.items() if k in params))
```

The captured native collection error on both trees is:

```text
File "/tmp/verifier_django_collect.py", line 18, in <module>
    params = inspect.signature(runner.setup).parameters
AttributeError: module 'runtests' has no attribute 'setup'
```

AST inspection of the frozen base archive proves `tests/runtests.py` has **no top-level setup function**. It exposes `setup_collect_tests` (line 200), `setup_run_tests` (line 286), and the corresponding teardown functions. No source was executed to diagnose this mismatch. The file's archive/image SHA-256 is `c637e819144aa5af27743ff372387eea7ffe8160e1ba13b379310d84f49dd0ac`; the fresh pristine source receipt is VERIFIED. The candidate patch touches only `django/forms/boundfield.py` and `django/forms/forms.py`, not the native runner.

The original witness remains in the frozen selection and is statically classified runnable:

```text
tests/forms_tests/tests/test_forms.py::FormsTestCase::test_datetime_clean_initial_callable_disabled
```

The earlier label-free [native FAIL ledger](../../phase3_fix2/native_FAIL_evidence.csv) records base PASS to patched FAIL for this exact identity. In attempt 2, both initial tree captures instead report COLLECTION_ERROR for it. Each tree has **4,462 COLLECTION_ERROR and six INVALID_ID slots**, **zero executed identities, zero execution events and zero raw test results**. Neither tree timed out: their captured pass durations are 30.595 and 30.079 seconds against the 1,800-second budget. No confirmation candidate was produced. Thus this loss is neither a changed selection, ordinary flaky failure, candidate patch modifying collection, nor a budget issue: the executor's version-specific setup assumption prevents execution.

[Structured receipts](integrity_stop.json) include the exact witness results/validation, all six integrity checks, original witness references, frozen AST function inventory, source identity and hashes of the sealed evidence paths.

## Stop and follow-up

The known cause is an executor defect; it does not satisfy the requirement that all six original FAIL witnesses remain evidenced. Under the pre-registered integrity-stop rule, this attempt is **aborted for analysis** and retained with its capture hash manifest. H1/H1b/H2/H3, the complete verdict table, sensitivity totals, confirmation totals, remaining-gap aggregates and runner-time aggregates were **not computed or published**. The thresholds and B1/B2 remain unchanged. No `phase4-run-sealed` tag is created; correctness labels remain unopened.

Proposed repair only: make Django native-collection initialization follow the checked-out runner's supported setup/teardown API, with offline adapter tests for this version, before a separately authorized new executor version/freeze tag and a fresh task-1 run. **No repair, retry, rerun or selective task execution was performed.** Neither old freeze tag was moved.
