# Phase 2 additions: batch collateral, accepted skips and policy projections

**Stored data only. Correctness labels were not read by this stage.**

## Batch abort collateral

The 942 load/collection-abort batch occurrences across 32 tasks strand **3,138 collateral NOT_RUN tree-ID slots**, or **10.06% of 31,179 native NOT_RUN slots**.

The denominator is every native selected-ID NOT_RUN status in initial base/patched calls, including parser-admission gaps; it excludes TIMEOUT, ERROR, missing identities and confirmation calls. Each (task, tree, selected ID) is counted once. The 216 runner-start failures are outside this 942-batch scope. Collateral excludes the offending candidate set, so it is not a prediction of how many tests would pass if the loader were repaired.

| Offending-label class | Batch occurrences | Candidate-label occurrences | Collateral tree-ID slots |
|---|---:|---:|---:|
| property | 8 | 8 | 192 |
| non_test_function | 98 | 116 | 2334 |
| class_attribute | 0 | 0 | 0 |
| module_level_helper | 4 | 4 | 96 |
| missing_module | 130 | 130 | 0 |
| other | 702 | 2356 | 516 |

The classes are mutually exclusive batch-occurrence counts summing to 942. Multiple method-name candidates remain explicit in the case table. Non-test function means a method/helper incompatible with standalone unittest label loading; module-level helpers are separated by their selected source path. Ordinary pytest functions that were not collected remain other. A missing selected class/method is not called a missing module. Missing module covers 130 pytest-5787 batches with explicit ModuleNotFoundError for xmlschema. Other consists of 584 remaining pytest not-found batches, 92 GIS environment guards and 26 Matplotlib collection attribute errors; missing selected class/method attributes are not promoted to missing modules.

| Top task | Collateral tree-ID slots | Base | Patched |
|---|---:|---:|---:|
| django__django-13297 | 824 | 412 | 412 |
| django__django-14631 | 518 | 259 | 259 |
| django__django-15930 | 416 | 208 | 208 |
| django__django-16136 | 398 | 199 | 199 |
| django__django-11820 | 240 | 120 | 120 |

## Accepted skips among the 13 native PASS tasks

| Reason group | Concrete tests | Tasks | Case/tree slots | Ordinary skip tests | Expected-failure tests |
|---|---:|---:|---:|---:|---:|
| cores_CPU | 38 | 2 | 76 | 38 | 0 |
| missing_dependency | 1 | 1 | 2 | 1 | 0 |
| platform | 0 | 0 | 0 | 0 | 0 |
| Python_version | 0 | 0 | 0 | 0 | 0 |
| other | 244 | 12 | 488 | 236 | 8 |

A test here is a unique (task, concrete raw test ID), deduplicated across the two trees; selected-family counts also appear in the CSV. Task counts overlap across reason groups. Native SKIPPED normalization includes XFAIL; expected-failure tests are exposed separately under other. Reason quality and source/capture references remain in accepted_skips.csv.

**0/13 stay PASS** under the strict rule that every selected SKIPPED observation is missing evidence. **0/13 are CPU-only across all normalized SKIPPED outcomes**. **2/13 have only CPU-conditioned ordinary skips** (pylint-6528 and pylint-7277), but each also has XFAIL outcomes stored as SKIPPED, so changing CPU resources alone does not satisfy this strict rule.

## Net projections — not experimental results

| Policy projection | Projected PASS | Retained native FAIL | Projected yes/no | Change from native 31/83 |
|---|---:|---:|---:|---:|
| current_policy_plus_parser_replay | 36 | 6 | 42/83 | +11 |
| parser_replay_plus_strict_skips | 14 | 6 | 20/83 | -11 |

Current policy plus parser replay retains 25 PASS and 6 FAIL and adds 9 formerly INCOMPLETE plus 2 formerly NOT_AVAILABLE tasks: 31 + 9 + 2 = 42. Strict skip handling retains 12 native PASS, the same 6 confirmed FAIL and 2 newly complete tasks: 12 + 6 + 2 = 20. Equivalently, 42 minus 13 skip-dependent native PASS minus 9 skip-dependent replay gains = 20.

These are completeness-only projections, not rerun results or new native verdicts. Confirmed native FAIL remains decisive even with other missing evidence; strictness applies to PASS. No new regression, REGRESSION_ERROR, confirmation, runner repair or CPU-induced execution is inferred. XFAIL follows the existing native SKIPPED normalization. Actual executor implementation and validation may differ from this offline projection.

## Evidence and ordering

batch_offending_label_classes.csv preserves the capture path:line range, source references, labels, identification confidence and collateral identities for all 942 batches. policy_projection_tasks.csv and accepted_PASS_skip_policy.csv preserve the task-level sets behind every projection. policy_projection_manifest.json hashes the label-blind inputs and analyzer. A later post-hoc label join must record this document’s SHA-256 and must not change these sets or counts.
