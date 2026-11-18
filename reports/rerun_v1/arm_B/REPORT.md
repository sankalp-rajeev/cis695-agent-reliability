# Rerun v1 Arm B grading

The annotated tag `rerun-armB-sealed` binds 92 completed tasks to manifest SHA-256 `8b9db5d3fc614ea43e56d5a5bf4db3619b708b7e720e9d77a0a8712058f9e9ee`.
The source was re-hashed before and after grading and at finalization. See [the seal](seal/) for the pre-grading accounting.

The frozen `run_oracle` used SWE-bench 5.0.2 from the lockfile and a 1,800-second task timeout.
Non-empty patches used the oracle's existing harness network configuration. Verified dataset access was offline.

## Timing

The first recorded attempt started at 2026-11-18T15:54:55.784084+00:00.
The latest recorded attempt ended at 2026-11-18T18:29:07.359604+00:00.
The 94 oracle attempts took 2255.816 seconds in total, including 0.039 seconds on empty patches. These are summed attempt times.
Mean wall time including retries was 24.520 seconds per completed task.

## Harness errors and re-runs

2 infrastructure re-runs. 2 final infrastructure errors.
- `django__django-13023` had attempt classes `patch_apply_failed → patch_apply_failed` and finished `X:patch_apply_failed`.
- `django__django-14140` had attempt classes `patch_apply_failed` and finished `X:patch_apply_failed`.
- `django__django-16667` had attempt classes `patch_apply_failed → patch_apply_failed` and finished `X:patch_apply_failed`.

## Label counts

| Oracle outcome | Tasks |
| --- | ---: |
| empty_patch | 41 |
| resolved | 25 |
| unresolved | 23 |
| patch_apply_failed | 1 |
| infra_error | 2 |

| Wrong-patch type | Tasks |
| --- | ---: |
| R | 12 |
| U | 11 |
| X | 3 |
