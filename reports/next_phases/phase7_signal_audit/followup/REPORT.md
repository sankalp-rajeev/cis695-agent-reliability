# Sealed signal audit: report-only follow-up

Independent standard-library check: PASS, zero mismatches; 11 CSV tables reconstructed from 302 raw inputs. All 82 pre-existing sealed artifacts remain unchanged. No verifier implementation, policy, configuration, frozen input, or existing tag was changed. Analysis and check helpers are report artifacts confined to this follow-up directory.

## 1. Primary accounting correction

The sealed audit headline used **S_invalid_missing**, giving **13 ACCEPT / 68 FLAG / 2 REJECT**, instead of Phase 4’s pre-registered primary **Policy S with INVALID_ID excluded**. The pre-registered primary is **S_invalid_excluded: 14 ACCEPT / 67 FLAG / 2 REJECT**.

The designation and excluded-ID rule are present in both `reports/next_phases/phase4_plan.md` and its `phase4-plan-frozen` version. [Exact tagged excerpt and digest](preregistration_evidence.json). The original report and seal are preserved, not rewritten.

| Accounting | ACCEPT | FLAG | REJECT | Role |
|---|---:|---:|---:|---|
| original | 52 | 30 | 1 | original decisions |
| C_invalid_excluded | 41 | 40 | 2 | sensitivity |
| C_invalid_missing | 32 | 49 | 2 | sensitivity |
| S_invalid_excluded | 14 | 67 | 2 | pre-registered primary |
| S_invalid_missing | 13 | 68 | 2 | sealed audit headline |

## 2. Post-hoc label comparisons

**Post-hoc, never used for any decision or accounting choice.** All 15 combinations use the same 83 frozen candidates and the original, audited-default, and CPU-2048 label sets. Precision is correct ACCEPTs / ACCEPTs; coverage is ACCEPTs / 83. Parentheses are Wilson 95% intervals; all labels are binary and scored.

| Accounting | Labels | Correct / ACCEPTs | Precision, 95% CI | Coverage, 95% CI | False-accept list |
|---|---|---:|---|---|---|
| original | original | 45/52 | 86.54% (74.73–93.32%) | 62.65% (51.90–72.28%) | FA1 (7) |
| original | audited_default | 45/52 | 86.54% (74.73–93.32%) | 62.65% (51.90–72.28%) | FA2 (7) |
| original | CPU_2048 | 46/52 | 88.46% (77.03–94.60%) | 62.65% (51.90–72.28%) | FA3 (6) |
| C_invalid_excluded | original | 36/41 | 87.80% (74.46–94.68%) | 49.40% (38.91–59.94%) | FA4 (5) |
| C_invalid_excluded | audited_default | 35/41 | 85.37% (71.56–93.12%) | 49.40% (38.91–59.94%) | FA5 (6) |
| C_invalid_excluded | CPU_2048 | 36/41 | 87.80% (74.46–94.68%) | 49.40% (38.91–59.94%) | FA6 (5) |
| C_invalid_missing | original | 27/32 | 84.38% (68.25–93.14%) | 38.55% (28.81–49.31%) | FA4 (5) |
| C_invalid_missing | audited_default | 26/32 | 81.25% (64.69–91.11%) | 38.55% (28.81–49.31%) | FA5 (6) |
| C_invalid_missing | CPU_2048 | 27/32 | 84.38% (68.25–93.14%) | 38.55% (28.81–49.31%) | FA6 (5) |
| S_invalid_excluded | original | 11/14 | 78.57% (52.41–92.43%) | 16.87% (10.32–26.34%) | FA7 (3) |
| S_invalid_excluded | audited_default | 11/14 | 78.57% (52.41–92.43%) | 16.87% (10.32–26.34%) | FA7 (3) |
| S_invalid_excluded | CPU_2048 | 12/14 | 85.71% (60.06–95.99%) | 16.87% (10.32–26.34%) | FA8 (2) |
| S_invalid_missing | original | 10/13 | 76.92% (49.74–91.82%) | 15.66% (9.39–24.98%) | FA7 (3) |
| S_invalid_missing | audited_default | 10/13 | 76.92% (49.74–91.82%) | 15.66% (9.39–24.98%) | FA7 (3) |
| S_invalid_missing | CPU_2048 | 11/13 | 84.62% (57.77–95.67%) | 15.66% (9.39–24.98%) | FA8 (2) |

Each list below contains full task IDs. Repeated list IDs mean exactly the same set of false accepts.

- **FA1**: `django__django-13212`; `django__django-13297`; `django__django-16667`; `matplotlib__matplotlib-23299`; `matplotlib__matplotlib-23476`; `pylint-dev__pylint-4661`; `pylint-dev__pylint-7277`.
- **FA2**: `django__django-13212`; `django__django-16667`; `matplotlib__matplotlib-23299`; `matplotlib__matplotlib-23476`; `pydata__xarray-6599`; `pylint-dev__pylint-4661`; `pylint-dev__pylint-7277`.
- **FA3**: `django__django-13212`; `django__django-16667`; `matplotlib__matplotlib-23299`; `matplotlib__matplotlib-23476`; `pydata__xarray-6599`; `pylint-dev__pylint-4661`.
- **FA4**: `django__django-16667`; `matplotlib__matplotlib-23299`; `pylint-dev__pylint-4661`; `pylint-dev__pylint-7277`; `sympy__sympy-17318`.
- **FA5**: `django__django-16667`; `matplotlib__matplotlib-23299`; `pydata__xarray-6599`; `pylint-dev__pylint-4661`; `pylint-dev__pylint-7277`; `sympy__sympy-17318`.
- **FA6**: `django__django-16667`; `matplotlib__matplotlib-23299`; `pydata__xarray-6599`; `pylint-dev__pylint-4661`; `sympy__sympy-17318`.
- **FA7**: `pylint-dev__pylint-4661`; `pylint-dev__pylint-7277`; `sympy__sympy-17318`.
- **FA8**: `pylint-dev__pylint-4661`; `sympy__sympy-17318`.

Machine-readable [all 15 rows with full lists](posthoc_accept_metrics.csv) and [each false accept with classifications](posthoc_false_accepts.csv). An absent grader-gap entry remains NOT_AVAILABLE. Labels are inherited from the existing audit, not regraded here.

All 83 stored agent claims are RESOLVED; agent-claim precision on those same 83 is:

| Label set | Correct / positive claims | Precision, Wilson 95% CI |
|---|---:|---|
| original | 69/83 | 83.13% (73.66–89.68%) |
| audited_default | 70/83 | 84.34% (75.02–90.61%) |
| CPU_2048 | 72/83 | 86.75% (77.81–92.44%) |

## 3. V1: existing-test edits in real candidates

**Zero of the 83 frozen patches modify an existing test file.** All other 17 selected main-study patches are available and likewise have zero existing-test edits: **0/100 overall**, with zero removed or loosened assertions in existing test files. **The V1 assertion-weakening gap changes no existing decision in these candidates.**

Every candidate digest was checked against its selected verification record. Both old and new Git paths were inspected; modifications, deletions and renames count as existing-file edits, while additions alone do not. The producer used unchanged V1 path conventions and the independent checker parsed Git headers separately. [100-patch inventory](v1_patch_inventory.csv); [every changed file](v1_changed_files.csv). No semantic assertion review was needed because no existing test was touched; this does not claim that V1 would catch future assertion weakening or indirect source-code manipulation.

## 4. V3: the two accepted FAIL cases

**Neither named record has an import-check failure: both record import PASS.** Their aggregate V3 FAILs identify different checks, and the records retain no detailed error output or base-import result.

| Task | Recorded import | Import failure reason | Actual recorded new failure | Same import on base? | Genuine or environmental? |
|---|---|---|---|---|---|
| matplotlib__matplotlib-23299 | PASS | N/A: no import failure | lint | NOT_RECORDED | UNKNOWN for lint; detailed failure output absent |
| pallets__flask-5014 | PASS | N/A: no import failure | build | NOT_RECORDED | UNKNOWN for build; detailed failure output absent |

Thus there is no failed import to classify as genuine or environmental. Whether the base commit fails the same import is UNKNOWN from the records, not a new PASS or FAIL. The current V3 configuration treats import as an absolute patched-tree check, but that is not substituted for missing recorded baseline evidence. The FAIL/ACCEPT combinations remain factual; these records alone do not establish a genuine runtime defect or an environmental failure. [Recorded details and provenance](v3_record_review.csv). No imports or builds were rerun.

## 5. V4: resource limits in the 14 no-output cases

**All 14 record 40 steps against a 40-step cap, and all record cost below the $1 cap. The explicitly recorded fired-limit subtype is UNKNOWN in every case:** the saved termination is only `LimitsExceeded`.

The inspected current agent guard raises LimitsExceeded when the step or cost cap is reached; wall time uses a separate TimeExceeded status. Together with n_steps=40 and cost below $1, this supports a **step-limit inference under that guard**, kept separate from the missing historical subtype. It does not recover unrecorded elapsed time, token use, or prove the historical installed guard’s identity.

Configured values, also present in these records: **40 steps; $1 generator cost; 1,200 s generator wall time; 8,192 output tokens per response; 60 s per command; 120 s per reproduction run; at most 3 test files of 65,536 bytes each; 0 retries; 2 base screens and 2 patched repeats.** There is no recorded total-token budget or token usage. Current configuration values agree with the stored budget fields.

| Task | Recorded steps / cap | Recorded cost / $1 | Termination | Explicit subtype |
|---|---:|---:|---|---|
| astropy__astropy-13977 | 40/40 | $0.031890 | LimitsExceeded | UNKNOWN |
| django__django-13158 | 40/40 | $0.034828 | LimitsExceeded | UNKNOWN |
| django__django-15037 | 40/40 | $0.029908 | LimitsExceeded | UNKNOWN |
| django__django-16631 | 40/40 | $0.035749 | LimitsExceeded | UNKNOWN |
| matplotlib__matplotlib-20676 | 40/40 | $0.028308 | LimitsExceeded | UNKNOWN |
| matplotlib__matplotlib-22871 | 40/40 | $0.034782 | LimitsExceeded | UNKNOWN |
| matplotlib__matplotlib-24637 | 40/40 | $0.029987 | LimitsExceeded | UNKNOWN |
| matplotlib__matplotlib-25479 | 40/40 | $0.028513 | LimitsExceeded | UNKNOWN |
| mwaskom__seaborn-3069 | 40/40 | $0.031993 | LimitsExceeded | UNKNOWN |
| pydata__xarray-4966 | 40/40 | $0.036448 | LimitsExceeded | UNKNOWN |
| pylint-dev__pylint-4970 | 40/40 | $0.027800 | LimitsExceeded | UNKNOWN |
| pylint-dev__pylint-6528 | 40/40 | $0.036141 | LimitsExceeded | UNKNOWN |
| sphinx-doc__sphinx-10323 | 40/40 | $0.028760 | LimitsExceeded | UNKNOWN |
| sympy__sympy-19783 | 40/40 | $0.066554 | LimitsExceeded | UNKNOWN |

Elapsed generator time and actual token use are UNKNOWN for all 14. The 8,192-token value is a per-response output cap, not evidence of a fired token limit. [Per-case limits and evidence](v4_limits.csv); [configuration values](configured_limits.csv). No generator, model or task test was run.

## Verification and seal

The independent [verify.py](verify.py) imports no producer or parent-audit analysis module. It reconstructs the decision rule, all 15 post-hoc rows and false-accept lists, claim precision, candidate-file counts, V3 review and V4 resource evidence directly from raw inputs, then compares all 11 CSVs and counts.json. It also checks the frozen plan excerpt and all 82 original sealed artifact hashes. [PASS receipt](independent_verification.json); [execution metadata](verification_execution.json); [input hashes](input_hashes.csv).

The first check launch was rejected by Docker for a duplicated frozen-plan mount before Python started. Its output is preserved in initial_launch.stdout.txt and initial_launch_execution.json; only the duplicate launcher mount was removed. The independent comparison itself passed on its first executed run, with no comparison changes.

Existing tags are preserved unchanged. The new annotated `signal-audit-followup-sealed` tag binds this follow-up report, tables, verification receipt and SHA-256 manifest.
