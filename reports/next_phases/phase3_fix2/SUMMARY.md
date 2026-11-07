# Phase 3 Fix 2 — outcome separation (stored captures only)

XFAIL and XPASS remain distinct in the native parser, selected-family results,
concrete-case results, serialization and paired outcome summaries. Ordinary
SKIPPED is admitted under Policy C and blocks PASS under Policy S. XFAIL→XFAIL
is evidence under both. Existing compatible transition handling is retained.
Parsed baseline caches from Fix 1 are invalidated so normalized outcomes cannot
mix with the new model. Unittest unexpected success can explain its nonzero
exit without becoming an ordinary FAIL; pytest XPASS alone cannot explain exit 1.

Base PASSED→patched ERROR is REGRESSION_ERROR, with a separate task signal and
list of test identities. Assertion FAIL has priority if both types occur in a
task; the summary still retains both. Neither signal is demoted by missing
evidence. The downstream decision adapter maps both to negative evidence while
preserving the distinct signal and counts in the verification record.

## Results against Fix 1

All 83 frozen selections and 676 stored capture files were checked against
recorded hashes. No benchmark source execution, Docker, new confirmation runs,
or native-record changes were used. The comparison uses Fix 1 source at
`f53d67a`, with Policy S blocking its normalized SKIPPED (including old XFAIL).

| Policy / stage | PASS | FAIL | REGRESSION_ERROR | INCOMPLETE | NOT_AVAILABLE |
|---|---:|---:|---:|---:|---:|
| C before | 36 | 6 | 0 | 31 | 10 |
| C after | 36 | 6 | 1 | 30 | 10 |
| S before | 14 | 6 | 0 | 53 | 10 |
| S after | 15 | 6 | 1 | 51 | 10 |

**Policy C changes 1 task verdict; Policy S changes 2.** Django-10973 changes
INCOMPLETE→REGRESSION_ERROR under both policies. Its five PostgreSQL dbshell
cases are PASSED on base and ERROR on patch. Seaborn-3069 additionally changes
INCOMPLETE→PASS under S because its remaining non-PASS outcomes are XFAIL.
`regression_error_evidence.csv` gives the five concrete identities and capture
lines. These are observed transitions; stable 3× confirmation remains Fix 8.

**All six native FAILs remain FAIL under C and S**, with concrete base-PASS /
patched-FAIL evidence in `native_FAIL_evidence.csv`: Django-12209, Django-14140,
Django-14631, Matplotlib-25479, Pytest-5809 and Sphinx-10435.

`task_rescore.csv` records every before/after verdict; `policy_chart.csv` is the
small policy chart; `XFAIL_XPASS_evidence.csv` retains special-outcome witnesses.
`before_fix1/` preserves the independently scored old model, and manifests hash
its source snapshot and inputs. B1, B2 and all plan thresholds are unchanged.
The owner-expansion rule and offline owner report were committed and pushed
first in `ff53e21`. Fix 3 has not started.

## Validation

172 focused unit tests pass, covering parsing, paired scoring, serialization,
cache invalidation, both skip policies, parameter-family gaps, error precedence,
downstream records and the existing verifier/integrity/evaluation behavior.
Ruff passes for every changed source file and the new Fix 2 script/tests.

The full unit suite was attempted but is not green in this worktree: the parent
editable install adds `/home/sankalp/projects/cis695-agent-reliability/src` to
sys.path and trips `test_env`'s guard; after deselecting that test,
`test_launch_tmux` fails because this worktree has no `.venv/bin/python`.
Dataset-backed setup also failed in the broader run, which was interrupted.
These worktree/environment limits were left outside Fix 2's scope.

## Reproduction

Use Python 3.11+ with the existing project dependencies. Output directories
must not already exist. From this worktree:

```bash
mkdir -p /tmp/fix2_old_source
git archive f53d67a src | tar -x -C /tmp/fix2_old_source
PYTHONPATH=/tmp/fix2_old_source/src /path/to/venv/bin/python \
  scripts/phase3_fix2_rescore.py --legacy --output /tmp/fix2_before
PYTHONPATH=src /path/to/venv/bin/python scripts/phase3_fix2_rescore.py \
  --before /tmp/fix2_before/task_rescore.csv --output /tmp/fix2_after
PYTHONPATH=src /path/to/venv/bin/python -m pytest -q -o addopts='' \
  tests/unit/test_fix2_outcomes.py tests/unit/test_regression.py \
  tests/unit/test_native_capture_replay.py tests/unit/test_container.py \
  tests/unit/test_evidence.py tests/unit/test_verifier_run.py \
  tests/unit/test_v2_integrity.py tests/unit/test_v2_evaluation.py
```

Result commit: this Fix 2 commit, resolved with
`git log -1 --format=%h -- reports/next_phases/phase3_fix2/SUMMARY.md`.
