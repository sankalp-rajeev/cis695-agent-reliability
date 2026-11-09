# Fix 18b completion

The scope amendment was committed first as `803cab7`. Separate stderr capture and `stderr_b64` now apply only to SymPy. pytest and Django use the original merged pipe and single-stream read. The driver diff against `d4e5d41` is in `driver_capture_diff.patch`; real fake-runner checks verify identical merged capture bytes and no `stderr_b64` key.

SymPy split parents are excluded from the unproven identity-loss check. Existing rerun statuses are preserved, including when the parent has import proof. A silent rerun without import proof still halts. Five new unit checks cover these cases and both merged-stream runners.

Exhaustive G1: **166/166 READY**, zero projected halts, **zero test bodies**. The separate Fix 18b manifest pin is `d2c4277141abcc2bfdf20fb87ee82a92a10dd44b251879b74c0f30c5d8ccc3bb`; the Fix 18 pin remains unchanged. Lookup prefers Fix 18b, then Fix 18/17/16.

Runtime smoke uses `phase4_launch.run_task -> Calls.run -> ContainerTestExecutor.run`. Each paired task runs base then patched with the same executor. The helper exits immediately before policy scoring and confirmations; base-only tasks exit before the patched call. The base pass of paired 13480 also belongs to the five-base check.

| Task | Tree | G1 identities recorded exactly once | COLLECTION_ERROR | SKIPPED | TIMEOUT | NOT_REACHED | Health trip |
|---|---|---:|---:|---:|---:|---:|---|
| `sympy__sympy-13480` | base | 763/763 | 16 | 29 | 0 | 0 | No |
| `sympy__sympy-13480` | patched | 763/763 | 16 | 29 | 0 | 0 | No |
| `sympy__sympy-17318` | base | 21/21 | 0 | 0 | 0 | 0 | No |
| `sympy__sympy-19783` | base | 729/729 | 0 | 6 | 0 | 0 | No |
| `sympy__sympy-24562` | base | 662/662 | 0 | 1 | 1 | 463 | No |
| `sympy__sympy-14711` | base | 429/429 | 0 | 4 | 0 | 0 | No |
| `astropy__astropy-13977` | base | 2959/2959 | 0 | 175 | 0 | 0 | No |
| `astropy__astropy-13977` | patched | 2959/2959 | 0 | 175 | 0 | 0 | No |
| `django__django-10973` | base | 13/13 | 0 | 2 | 0 | 0 | No |
| `django__django-10973` | patched | 13/13 | 0 | 2 | 0 | 0 | No |

All ten tree passes have zero missing or duplicate G1 identities, zero unexplained non-run identities and zero health trips. All five SymPy base counts exactly match Fix 18. The pytest and Django passes have zero `stderr_b64` event keys.

Both 13480 trees record 763/763 identities exactly once and 16 COLLECTION_ERROR entries with the import signature:

`DeprecationWarning -> PyTestReporter._active_file during import of sympy/physics/quantum/tests/test_printing.py`

The final full unit suite has **1,367 successful checks** (1,362 plus five), with the **same six pre-existing failures and 17 errors**, verified by issue names. The unit summary is masked.

Raw runtime captures remain in the ignored run directory; `identity_smoke_capture_manifest.json` publishes hashes only. The initial helper startup error happened before any test pass; the corrected helper uses the launcher’s effective runner when selecting SymPy tasks. Executor sources still match every sealed G1 source pin.

H1/H1b/H2/H3, thresholds, B1/B2 and frozen selections are unchanged. No quarantined attempt-3 paths were modified; their contents were not opened for verification. No correctness labels, oracle data or benchmark test outcomes were inspected for analysis. No freeze tag, force-push or experiment launch.
The final secret scan found no credentials in full Git history, the working tree or the index. See `secret_scan.json` for the log hash.
