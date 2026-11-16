Policy v1.4.0 is implemented and validated for the four decided changes, with no stored decision changes. All new tests pass and the full unit suite has no failures beyond the measured baseline.

## Result

| Check | Result |
|---|---:|
| Sealed V1 violation probes | 11/11 caught (was 10/11) |
| Sealed V1 controls | 3/3 pass |
| Added fixtures | 6 violation probes caught, 2 controls pass |
| New unit tests | 45/45 pass |
| v1.3 golden decision entries | 100/100 exact, including reasons/version |
| v1.4 stored-signal decision changes | 0/100 |
| Independent standard-library verification | PASS |

The new fixtures cover assertion removal, constant true, equality tautology,
replacement by `pass`, a skip decorator and a skip call. Unit tests also cover
`assert 1`, `assert not False`, xfail/skip variants, assertion loss masked by a new
test, unparsable and non-Python files, V3 evidence and gates, every limit subtype,
usage and sanitization, record-writing isolation, and all reporting sensitivities.
[Probe results](v1_probes.csv) retain the individual outcomes.

## Decision delta table

| Policy | ACCEPT | FLAG | REJECT | Changed tasks |
|---|---:|---:|---:|---:|
| Stored v1.3.0 | 54 | 34 | 12 | — |
| Recomputed v1.3.0 | 54 | 34 | 12 | 0 |
| v1.4.0, stored signals | 54 | 34 | 12 | 0 |

There are no changed tasks or causes to enumerate. [delta.csv](delta.csv) lists
all 100 comparisons; [golden.csv](golden.csv) records the exact golden matches.
No V2 accounting projection replaces a stored V2 outcome in these tables.

## Unit baseline by name

| Outcome | origin/main baseline | v1.4.0 |
|---|---:|---:|
| Passed | 1375 | 1420 |
| Failed | 6 | 6 |
| Setup errors | 47 | 47 |
| Skipped | 6 | 6 |

All 1,434 existing test names retain exactly the same status; all 45 additional
tests pass. [test_comparison.csv](test_comparison.csv) lists every name and status,
and [test_summary.json](test_summary.json) records zero new failures and zero
baseline status changes. Existing problems include read-only dataset-cache
locks, a missing Django fixture, sandbox-dependent shadow checks and pre-existing
V2 frozen-source/configuration mismatches. No frozen input was changed to make
those tests pass. An initial guard launcher added `/tmp` to sys.path and caused
one extra interpreter-contamination failure; the final guarded rerun loads the
guard without that path and has no extra failure.

## Selection and implementation

Use `env -u PYTHONPATH .venv/bin/python scripts/verify_patch_v1_4.py <task_dir>
--config full-v1.4`. This writes `verification_record.full-v1.4.json`; the new
configuration is `configs/verifier/full_v1_4.yaml`. Existing policy entry points,
source files and frozen configs are byte-identical to origin/main: the preservation
check verifies all 164 original source/config/test files. Only the
explicitly requested new section is appended to `docs/VERIFIER_POLICY.md`.

V1 uses complete base and patched ASTs. Incomplete analysis is attributed and
conservatively blocks ACCEPT. V3 retains separate streams and versions; only
syntax/import FAIL gates ACCEPT, preserving existing REJECT precedence. V4 uses
80 steps and zero retries with every other cap unchanged, recording telemetry in
the new-version cache and each signal record. The reporting helper defaults to
Policy S with INVALID_ID excluded, keeping the other three variants labeled as
sensitivities and leaving V2 execution untouched. Conservative interpretations
are recorded in [DECISIONS.md](DECISIONS.md).

## Reproduction and limits

Run from the repository root, using installed dependencies and local inputs:

```sh
env -u PYTHONPATH .venv/bin/python reports/policy_v1_4/probe_v1.py
env -u PYTHONPATH .venv/bin/python reports/policy_v1_4/recompute.py
python3 reports/policy_v1_4/verify.py
env -u PYTHONPATH .venv/bin/python reports/policy_v1_4/offline_tests.py --junitxml=/tmp/policy-v1.4-final.xml
python3 reports/policy_v1_4/compare_tests.py /tmp/policy-v1.4-final.xml
```

The unit command has a nonzero exit because of the unchanged baseline failures;
the comparison command verifies that no new failing name exists. The independent
checker imports no producer or policy modules and reconstructs decisions from
the original verification records. Input hashes are retained in
[policy_inputs.json](policy_inputs.json). V1 reuses the sealed `v1_fixtures` and
`v1_case_spec.json` unchanged, with the three-file extraction recipe from
`run_v1.py`; the local base archive comes from the audit's preparation record.

Validation made no model calls or non-Git network requests and did not open
label sources. The final suite ran under network and repository-label access
guards. The increased V4 cap was tested with synthetic generator outcomes,
not live generation; token counts absent from an outcome remain explicitly
unreported. Stored-signal recomputation establishes decision compatibility and
does not predict the effects of future regenerated V4 tests.

Freeze target: annotated tag `policy-v1.4.0-frozen` on the final report commit,
pushed with `feature/policy-v1.4`. Main and all pre-existing tags remain unchanged.
