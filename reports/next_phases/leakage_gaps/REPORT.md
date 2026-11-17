# Leakage gaps audit

## Interpreted verdict

**2 non-requests tasks meet T4 (environment leak); 62 meet T3 as their highest tier (memory or solving indicator).**

T4 requires guarded answer content or a base-absent hidden test name in tool output before the model first produced it. T3 indicates model-first content and cannot distinguish memory from solving. Raw CONFIRMED flags below are an artifact inventory, not a contamination verdict. Setup history alone is harmless under the interpreted rules. The seven requests tasks are reported as Excluded and contribute to none of the task-tier totals.

The highest applicable tier wins: T0 has no tier evidence; T1 is harmless setup history; T2 is awareness or access attempts without qualifying answer content; T3 is model-first content; T4 is tool-first answer exposure.

| Role (93 non-requests tasks; maximum over runs) | T0 | T1 | T2 | T3 | T4 | Observed |
|---|---:|---:|---:|---:|---:|---:|
| Repair | 3 | 0 | 28 | 60 | 2 | 93 |
| V4 generator | 22 | 2 | 22 | 45 | 2 | 84 |

T0 means no tier evidence; missing trajectories are explicitly marked `observed=false` and do not establish a clean run. Per-run rows retain their own tier. Unique-task totals use the maximum across the stored runs.

**T4 tasks:** matplotlib__matplotlib-20676, matplotlib__matplotlib-21568.

**T3 tasks (highest tier across roles/runs):** astropy__astropy-13398, astropy__astropy-14365, astropy__astropy-14508, django__django-10973, django__django-11095, django__django-11299, django__django-12965, django__django-13023, django__django-13033, django__django-13158, django__django-13212, django__django-13569, django__django-13786, django__django-13807, django__django-13820, django__django-14140, django__django-14631, django__django-15037, django__django-15103, django__django-15278, django__django-15375, django__django-15499, django__django-15572, django__django-15930, django__django-16136, django__django-16612, django__django-16631, matplotlib__matplotlib-20488, matplotlib__matplotlib-22865, matplotlib__matplotlib-22871, matplotlib__matplotlib-23476, matplotlib__matplotlib-24026, matplotlib__matplotlib-24177, matplotlib__matplotlib-24637, matplotlib__matplotlib-25122, matplotlib__matplotlib-25287, matplotlib__matplotlib-25479, matplotlib__matplotlib-26291, mwaskom__seaborn-3069, pallets__flask-5014, pydata__xarray-4629, pydata__xarray-4695, pydata__xarray-4966, pylint-dev__pylint-4551, pylint-dev__pylint-4970, pylint-dev__pylint-6528, pylint-dev__pylint-7277, pytest-dev__pytest-10051, pytest-dev__pytest-5787, pytest-dev__pytest-5809, pytest-dev__pytest-7236, scikit-learn__scikit-learn-10908, scikit-learn__scikit-learn-12585, scikit-learn__scikit-learn-14141, scikit-learn__scikit-learn-14629, sphinx-doc__sphinx-10435, sphinx-doc__sphinx-10466, sphinx-doc__sphinx-7910, sympy__sympy-13480, sympy__sympy-17318, sympy__sympy-19783, sympy__sympy-24562.

**Comparable cohort:** 60 of 83 comparable tasks are T3 or T4. The comparable set is the historically pinned 83-task archive inventory; no correctness or grader labels were read.

Distinctiveness guard: 24 matched content probes and 3 raw-finding occurrences lose any ability to support T3/T4. A content probe must have at least 25 non-whitespace characters and fewer than three occurrences in the verified base archive. The guard does not apply to the separate base-absent hidden-name rule.

| Masked path | Reclassified raw read observations |
|---|---|
| /opt/miniconda3/pkgs | masked-read-empty-listing=1 |
| /root/.cache/pip | masked-read-archive-member-list=3, masked-read-content=15, masked-read-directory-metadata=1, masked-read-empty-listing=1, masked-read-file-metadata=1, masked-read-listed-files=18, masked-read-other-paths-only=1 |

The 40 raw masked-read findings are preserved. Nonempty stdout alone is not proof of cache content. A cache access supports T4 only when guarded answer content is tool-first. The full cache receipts and chronological evidence are in `tiers/artifacts/`; the focused history receipt is in `tiers/history_gold_checks.json`.

Reclassification of the 40 raw cache-read flags (including requests): empty-listing=1, metadata-only=2, nonempty-content-or-filenames=36, other-path-output-only=1. One observation addresses both masked paths, so the path table has 41 entries. Metadata-only and other-path output do not establish returned answer content.

1 raw content match exists only in JSON serialization, with no matching decoded source content. Its first raw appearance is recorded but it cannot support T3/T4.

### Focused Django history check

The `django__django-15499` history match is a model-produced working-tree diff, not a line retrieved from a source commit. Both probes occur zero times at base and pass the length guard; both were model-first. The source commit is therefore null: the diff compares the working tree against the Git index. The pinned base identity and command are identified below by hash only.

| Command SHA-256 | Pinned base commit | Probe SHA-256 | Base occurrences | Non-whitespace characters | First seen |
|---|---|---|---:|---:|---|
| 5affaf21fe0e1362449bc2c8224802cf81dcdff1d4336221e3023684970e18c6 | d90e34c61b27fba2527834806639eebbcfab9631 | ae8ffa1545b41b18a1cfb86d4751e6a08858372d26adaa30e8c6b943863b3b81 | 0 | 40 | model_output |
| 5affaf21fe0e1362449bc2c8224802cf81dcdff1d4336221e3023684970e18c6 | d90e34c61b27fba2527834806639eebbcfab9631 | ac00ec75e2d637d0e826ab86d821becf6836d2a1b5ea0ce64e157012f3bdd89c | 0 | 28 | model_output |

Reproduce the interpreted layer with `scripts/audit_leakage_tiers.py`; verify it with `scripts/verify_leakage_gaps.py`. The rerun entry point is `scripts/audit_rerun_arm.py --run <output folder>` and was exercised on synthetic data only. Interpretation validation is recorded separately in `tiers/unit_comparison.json` and `tiers/verification.json`.

All original per-artifact finding files and image receipts remain unchanged. The standard-library verifier independently recomputes every tier and total, checks the CSV and immutable input hashes, and rechecks chronological speaker/probe receipts against decoded trajectories.

<!-- interpreted-totals-json: {"T3_tasks": ["astropy__astropy-13398", "astropy__astropy-14365", "astropy__astropy-14508", "django__django-10973", "django__django-11095", "django__django-11299", "django__django-12965", "django__django-13023", "django__django-13033", "django__django-13158", "django__django-13212", "django__django-13569", "django__django-13786", "django__django-13807", "django__django-13820", "django__django-14140", "django__django-14631", "django__django-15037", "django__django-15103", "django__django-15278", "django__django-15375", "django__django-15499", "django__django-15572", "django__django-15930", "django__django-16136", "django__django-16612", "django__django-16631", "matplotlib__matplotlib-20488", "matplotlib__matplotlib-22865", "matplotlib__matplotlib-22871", "matplotlib__matplotlib-23476", "matplotlib__matplotlib-24026", "matplotlib__matplotlib-24177", "matplotlib__matplotlib-24637", "matplotlib__matplotlib-25122", "matplotlib__matplotlib-25287", "matplotlib__matplotlib-25479", "matplotlib__matplotlib-26291", "mwaskom__seaborn-3069", "pallets__flask-5014", "pydata__xarray-4629", "pydata__xarray-4695", "pydata__xarray-4966", "pylint-dev__pylint-4551", "pylint-dev__pylint-4970", "pylint-dev__pylint-6528", "pylint-dev__pylint-7277", "pytest-dev__pytest-10051", "pytest-dev__pytest-5787", "pytest-dev__pytest-5809", "pytest-dev__pytest-7236", "scikit-learn__scikit-learn-10908", "scikit-learn__scikit-learn-12585", "scikit-learn__scikit-learn-14141", "scikit-learn__scikit-learn-14629", "sphinx-doc__sphinx-10435", "sphinx-doc__sphinx-10466", "sphinx-doc__sphinx-7910", "sympy__sympy-13480", "sympy__sympy-17318", "sympy__sympy-19783", "sympy__sympy-24562"], "T4_tasks": ["matplotlib__matplotlib-20676", "matplotlib__matplotlib-21568"], "by_role": {"generator": {"counts": {"T0": 22, "T1": 2, "T2": 22, "T3": 45, "T4": 2}, "observed_tasks": 84, "tasks_by_tier": {"T0": ["astropy__astropy-13398", "astropy__astropy-7606", "django__django-12663", "django__django-13569", "django__django-14140", "django__django-16255", "django__django-16612", "django__django-16667", "matplotlib__matplotlib-22865", "matplotlib__matplotlib-24627", "matplotlib__matplotlib-25332", "pydata__xarray-4629", "pylint-dev__pylint-4551", "pylint-dev__pylint-8898", "pytest-dev__pytest-7432", "scikit-learn__scikit-learn-10908", "scikit-learn__scikit-learn-12585", "scikit-learn__scikit-learn-14894", "sphinx-doc__sphinx-10614", "sphinx-doc__sphinx-7748", "sympy__sympy-14711", "sympy__sympy-24562"], "T1": ["pylint-dev__pylint-7277", "pytest-dev__pytest-7521"], "T2": ["astropy__astropy-13977", "astropy__astropy-14508", "django__django-11820", "django__django-12209", "django__django-13158", "django__django-13297", "django__django-15375", "django__django-16082", "django__django-16315", "matplotlib__matplotlib-14623", "matplotlib__matplotlib-22719", "matplotlib__matplotlib-23299", "matplotlib__matplotlib-24970", "pydata__xarray-6599", "pydata__xarray-6744", "pylint-dev__pylint-4661", "pylint-dev__pylint-4970", "pylint-dev__pylint-6903", "pytest-dev__pytest-6202", "pytest-dev__pytest-7236", "sphinx-doc__sphinx-10323", "sphinx-doc__sphinx-7910"], "T3": ["astropy__astropy-14365", "django__django-10973", "django__django-11095", "django__django-11299", "django__django-12965", "django__django-13023", "django__django-13033", "django__django-13212", "django__django-13786", "django__django-13807", "django__django-13820", "django__django-14631", "django__django-15037", "django__django-15103", "django__django-15278", "django__django-15499", "django__django-15572", "django__django-15930", "django__django-16136", "django__django-16631", "matplotlib__matplotlib-20488", "matplotlib__matplotlib-22871", "matplotlib__matplotlib-23476", "matplotlib__matplotlib-24026", "matplotlib__matplotlib-24177", "matplotlib__matplotlib-24637", "matplotlib__matplotlib-25122", "matplotlib__matplotlib-25287", "matplotlib__matplotlib-25479", "matplotlib__matplotlib-26291", "mwaskom__seaborn-3069", "pallets__flask-5014", "pydata__xarray-4695", "pydata__xarray-4966", "pylint-dev__pylint-6528", "pytest-dev__pytest-10051", "pytest-dev__pytest-5787", "pytest-dev__pytest-5809", "scikit-learn__scikit-learn-14141", "scikit-learn__scikit-learn-14629", "sphinx-doc__sphinx-10435", "sphinx-doc__sphinx-10466", "sympy__sympy-13480", "sympy__sympy-17318", "sympy__sympy-19783"], "T4": ["matplotlib__matplotlib-20676", "matplotlib__matplotlib-21568"]}, "unobserved_tasks": ["astropy__astropy-13398", "django__django-12663", "matplotlib__matplotlib-22865", "matplotlib__matplotlib-24627", "matplotlib__matplotlib-25332", "pylint-dev__pylint-4551", "pylint-dev__pylint-8898", "sphinx-doc__sphinx-10614", "sphinx-doc__sphinx-7748"]}, "repair": {"counts": {"T0": 3, "T1": 0, "T2": 28, "T3": 60, "T4": 2}, "observed_tasks": 93, "tasks_by_tier": {"T0": ["django__django-16082", "django__django-16255", "pytest-dev__pytest-10051"], "T1": [], "T2": ["astropy__astropy-13977", "astropy__astropy-7606", "django__django-11820", "django__django-12209", "django__django-12663", "django__django-13297", "django__django-16315", "django__django-16667", "matplotlib__matplotlib-14623", "matplotlib__matplotlib-22719", "matplotlib__matplotlib-23299", "matplotlib__matplotlib-24627", "matplotlib__matplotlib-24970", "matplotlib__matplotlib-25332", "pydata__xarray-6599", "pydata__xarray-6744", "pylint-dev__pylint-4661", "pylint-dev__pylint-6903", "pylint-dev__pylint-8898", "pytest-dev__pytest-5809", "pytest-dev__pytest-6202", "pytest-dev__pytest-7432", "pytest-dev__pytest-7521", "scikit-learn__scikit-learn-14894", "sphinx-doc__sphinx-10323", "sphinx-doc__sphinx-10614", "sphinx-doc__sphinx-7748", "sympy__sympy-14711"], "T3": ["astropy__astropy-13398", "astropy__astropy-14365", "astropy__astropy-14508", "django__django-10973", "django__django-11095", "django__django-11299", "django__django-12965", "django__django-13023", "django__django-13033", "django__django-13158", "django__django-13212", "django__django-13569", "django__django-13786", "django__django-13807", "django__django-13820", "django__django-14140", "django__django-14631", "django__django-15037", "django__django-15103", "django__django-15278", "django__django-15375", "django__django-15499", "django__django-15572", "django__django-15930", "django__django-16136", "django__django-16612", "django__django-16631", "matplotlib__matplotlib-20488", "matplotlib__matplotlib-22865", "matplotlib__matplotlib-22871", "matplotlib__matplotlib-23476", "matplotlib__matplotlib-24026", "matplotlib__matplotlib-24177", "matplotlib__matplotlib-24637", "matplotlib__matplotlib-25122", "matplotlib__matplotlib-25287", "matplotlib__matplotlib-25479", "matplotlib__matplotlib-26291", "mwaskom__seaborn-3069", "pallets__flask-5014", "pydata__xarray-4629", "pydata__xarray-4695", "pydata__xarray-4966", "pylint-dev__pylint-4551", "pylint-dev__pylint-4970", "pylint-dev__pylint-6528", "pylint-dev__pylint-7277", "pytest-dev__pytest-5787", "pytest-dev__pytest-7236", "scikit-learn__scikit-learn-10908", "scikit-learn__scikit-learn-12585", "scikit-learn__scikit-learn-14141", "scikit-learn__scikit-learn-14629", "sphinx-doc__sphinx-10435", "sphinx-doc__sphinx-10466", "sphinx-doc__sphinx-7910", "sympy__sympy-13480", "sympy__sympy-17318", "sympy__sympy-19783", "sympy__sympy-24562"], "T4": ["matplotlib__matplotlib-20676", "matplotlib__matplotlib-21568"]}, "unobserved_tasks": []}}, "cache_findings_by_result": {"empty-listing": 1, "metadata-only": 2, "nonempty-content-or-filenames": 36, "other-path-output-only": 1}, "cohort": 100, "comparable_T3_or_T4_count": 60, "comparable_T3_or_T4_tasks": ["astropy__astropy-14365", "astropy__astropy-14508", "django__django-10973", "django__django-11095", "django__django-11299", "django__django-12965", "django__django-13023", "django__django-13033", "django__django-13158", "django__django-13212", "django__django-13569", "django__django-13786", "django__django-13807", "django__django-13820", "django__django-14140", "django__django-14631", "django__django-15037", "django__django-15103", "django__django-15278", "django__django-15375", "django__django-15499", "django__django-15572", "django__django-15930", "django__django-16136", "django__django-16612", "django__django-16631", "matplotlib__matplotlib-20488", "matplotlib__matplotlib-20676", "matplotlib__matplotlib-22871", "matplotlib__matplotlib-23476", "matplotlib__matplotlib-24026", "matplotlib__matplotlib-24177", "matplotlib__matplotlib-24637", "matplotlib__matplotlib-25122", "matplotlib__matplotlib-25287", "matplotlib__matplotlib-25479", "matplotlib__matplotlib-26291", "mwaskom__seaborn-3069", "pallets__flask-5014", "pydata__xarray-4629", "pydata__xarray-4695", "pydata__xarray-4966", "pylint-dev__pylint-4970", "pylint-dev__pylint-6528", "pylint-dev__pylint-7277", "pytest-dev__pytest-10051", "pytest-dev__pytest-5787", "pytest-dev__pytest-5809", "pytest-dev__pytest-7236", "scikit-learn__scikit-learn-10908", "scikit-learn__scikit-learn-12585", "scikit-learn__scikit-learn-14141", "scikit-learn__scikit-learn-14629", "sphinx-doc__sphinx-10435", "sphinx-doc__sphinx-10466", "sphinx-doc__sphinx-7910", "sympy__sympy-13480", "sympy__sympy-17318", "sympy__sympy-19783", "sympy__sympy-24562"], "comparable_count": 83, "comparable_tasks": ["astropy__astropy-13977", "astropy__astropy-14365", "astropy__astropy-14508", "astropy__astropy-7606", "django__django-10973", "django__django-11095", "django__django-11299", "django__django-11820", "django__django-12209", "django__django-12965", "django__django-13023", "django__django-13033", "django__django-13158", "django__django-13212", "django__django-13297", "django__django-13569", "django__django-13786", "django__django-13807", "django__django-13820", "django__django-14140", "django__django-14631", "django__django-15037", "django__django-15103", "django__django-15278", "django__django-15375", "django__django-15499", "django__django-15572", "django__django-15930", "django__django-16082", "django__django-16136", "django__django-16255", "django__django-16315", "django__django-16612", "django__django-16631", "django__django-16667", "matplotlib__matplotlib-14623", "matplotlib__matplotlib-20488", "matplotlib__matplotlib-20676", "matplotlib__matplotlib-22719", "matplotlib__matplotlib-22871", "matplotlib__matplotlib-23299", "matplotlib__matplotlib-23476", "matplotlib__matplotlib-24026", "matplotlib__matplotlib-24177", "matplotlib__matplotlib-24637", "matplotlib__matplotlib-24970", "matplotlib__matplotlib-25122", "matplotlib__matplotlib-25287", "matplotlib__matplotlib-25479", "matplotlib__matplotlib-26291", "mwaskom__seaborn-3069", "pallets__flask-5014", "pydata__xarray-4629", "pydata__xarray-4695", "pydata__xarray-4966", "pydata__xarray-6599", "pydata__xarray-6744", "pylint-dev__pylint-4661", "pylint-dev__pylint-4970", "pylint-dev__pylint-6528", "pylint-dev__pylint-6903", "pylint-dev__pylint-7277", "pytest-dev__pytest-10051", "pytest-dev__pytest-5787", "pytest-dev__pytest-5809", "pytest-dev__pytest-6202", "pytest-dev__pytest-7236", "pytest-dev__pytest-7432", "pytest-dev__pytest-7521", "scikit-learn__scikit-learn-10908", "scikit-learn__scikit-learn-12585", "scikit-learn__scikit-learn-14141", "scikit-learn__scikit-learn-14629", "scikit-learn__scikit-learn-14894", "sphinx-doc__sphinx-10323", "sphinx-doc__sphinx-10435", "sphinx-doc__sphinx-10466", "sphinx-doc__sphinx-7910", "sympy__sympy-13480", "sympy__sympy-14711", "sympy__sympy-17318", "sympy__sympy-19783", "sympy__sympy-24562"], "excluded_tasks": ["psf__requests-1142", "psf__requests-1724", "psf__requests-1766", "psf__requests-2317", "psf__requests-2931", "psf__requests-5414", "psf__requests-6028"], "guard_reasons": {"guard-short-content": 24}, "guard_removed_matches": 24, "guard_removed_raw_findings": 3, "included_tasks": 93, "masked_path_counts": {"/opt/miniconda3/pkgs": {"masked-read-empty-listing": 1}, "/root/.cache/pip": {"masked-read-archive-member-list": 3, "masked-read-content": 15, "masked-read-directory-metadata": 1, "masked-read-empty-listing": 1, "masked-read-file-metadata": 1, "masked-read-listed-files": 18, "masked-read-other-paths-only": 1}}, "observed_rows": 196, "raw_masked_read_findings": 40, "row_counts": {"generator": {"Excluded": 7, "T0": 26, "T1": 2, "T2": 23, "T3": 45, "T4": 2}, "repair": {"Excluded": 7, "T0": 5, "T2": 28, "T3": 63, "T4": 2}}, "rows": 210, "schema_version": 1, "serialization_only_raw_findings": 1} -->

## Raw-rule inventory (historical headline; findings unchanged)

<!-- raw-rule-inventory-begin -->
# Leakage gaps audit

**Verdict: confirmed evidence appears in stored agent-visible artifacts.**

This is an artifact audit, not proof that the model could not remember an answer. Image exposure and an agent actually receiving an answer are separate observations. The audit uses no correctness labels or grader results.

Stored trajectories: 196 directories (105 repair, 91 V4), 100 unique tasks, 1141 in-scope files. Confirmed findings: 458; affected tasks: 86. Benchmark-awareness findings: 1437 across 96 unique tasks.

Confirmed findings include 15 gold-patch content matches, 7 test-patch content matches, 40 successful masked-cache read findings, 281 history-output findings, and 115 absent-before-definition test-name findings. These are artifact occurrences and can overlap. Under the specified audit rules, the original DeepSeek study cannot be certified as isolated from answers. A post-base preparation commit alone establishes history access; the content-match findings are the more direct answer-exposure evidence.

Images: 100/100 present; 0 missing; 0 incomplete. 100 images contain commits after base; 0 images contain at least one exact gold post-image blob. 28 unmasked package copies have a version different from base; 0 copy versions remain unresolved.

<!-- totals-json: {"images": {"cohort": 100, "different_version_copies": 28, "different_version_tasks": ["psf__requests-1142", "psf__requests-1724", "psf__requests-1766", "psf__requests-2317", "psf__requests-2931", "psf__requests-5414", "psf__requests-6028"], "future_history_images": 100, "future_reachable_images": 100, "gold_blob_images": 0, "gold_blobs_probed": 120, "incomplete": [], "missing": [], "present": 100, "unresolved_copy_versions": 0}, "trajectory": {"awareness_tasks": 96, "confirmed_tasks": ["astropy__astropy-13398", "astropy__astropy-13977", "astropy__astropy-14508", "django__django-10973", "django__django-11095", "django__django-11820", "django__django-12209", "django__django-12663", "django__django-12965", "django__django-13033", "django__django-13158", "django__django-13212", "django__django-13297", "django__django-13569", "django__django-13820", "django__django-14140", "django__django-14631", "django__django-15037", "django__django-15278", "django__django-15499", "django__django-15572", "django__django-15930", "django__django-16136", "django__django-16315", "django__django-16612", "django__django-16631", "django__django-16667", "matplotlib__matplotlib-14623", "matplotlib__matplotlib-20488", "matplotlib__matplotlib-20676", "matplotlib__matplotlib-21568", "matplotlib__matplotlib-22719", "matplotlib__matplotlib-22865", "matplotlib__matplotlib-22871", "matplotlib__matplotlib-23299", "matplotlib__matplotlib-23476", "matplotlib__matplotlib-24026", "matplotlib__matplotlib-24177", "matplotlib__matplotlib-24627", "matplotlib__matplotlib-24637", "matplotlib__matplotlib-24970", "matplotlib__matplotlib-25122", "matplotlib__matplotlib-25287", "matplotlib__matplotlib-25332", "matplotlib__matplotlib-25479", "matplotlib__matplotlib-26291", "mwaskom__seaborn-3069", "pallets__flask-5014", "psf__requests-1142", "psf__requests-1724", "psf__requests-1766", "psf__requests-2317", "psf__requests-2931", "psf__requests-5414", "psf__requests-6028", "pydata__xarray-4629", "pydata__xarray-4695", "pydata__xarray-4966", "pydata__xarray-6599", "pydata__xarray-6744", "pylint-dev__pylint-4551", "pylint-dev__pylint-4661", "pylint-dev__pylint-4970", "pylint-dev__pylint-6528", "pylint-dev__pylint-6903", "pylint-dev__pylint-7277", "pylint-dev__pylint-8898", "pytest-dev__pytest-10051", "pytest-dev__pytest-5787", "pytest-dev__pytest-5809", "pytest-dev__pytest-7236", "pytest-dev__pytest-7521", "scikit-learn__scikit-learn-10908", "scikit-learn__scikit-learn-12585", "scikit-learn__scikit-learn-14141", "scikit-learn__scikit-learn-14629", "sphinx-doc__sphinx-10323", "sphinx-doc__sphinx-10435", "sphinx-doc__sphinx-10466", "sphinx-doc__sphinx-10614", "sphinx-doc__sphinx-7748", "sphinx-doc__sphinx-7910", "sympy__sympy-14711", "sympy__sympy-17318", "sympy__sympy-19783", "sympy__sympy-24562"], "downgrades": 0, "findings": 32567, "generator_directories": 91, "golden_violations": 0, "legacy_findings": 912, "repair_directories": 105, "rules": {"fetch-curl": 64, "fetch-pip-download": 90, "fetch-pip-install": 1, "history-git-cat-file": 18, "history-git-diff": 29, "history-git-fsck": 130, "history-git-log": 377, "history-git-reflog": 52, "history-git-rev-list": 60, "history-git-show": 268, "history-git-stash": 5, "history-gold-added-line": 1, "history-newer-commit": 280, "legacy": 692, "legacy-review-retained": 46, "test-name-absent-before-definition": 115, "test-name-agent-defined-before-output": 1, "test-name-present-at-base": 30338}, "scanned_files": 1141, "severity": {"benchmark-awareness": 1437, "confirmed": 458, "exposed-copy": 273, "review": 30399}, "task_directories": 196, "unique_tasks": 100}} -->

## Stored-run findings

Read in place: `main_50_a`, `main_50_b`, `main_2_rerun_mpl`, `main_3_rerun_infra`, including each root’s `_reproduction_cache`. Only the audit allowlist is opened; oracle/grader result files are excluded. Per-artifact severity, rule and hashed evidence are in `tasks/<run>/<role>/<iid>.json`.

| Severity | Findings |
|---|---:|
| benchmark-awareness | 1437 |
| confirmed | 458 |
| exposed-copy | 273 |
| review | 30399 |

| Rule | Findings |
|---|---:|
| fetch-curl | 64 |
| fetch-pip-download | 90 |
| fetch-pip-install | 1 |
| history-git-cat-file | 18 |
| history-git-diff | 29 |
| history-git-fsck | 130 |
| history-git-log | 377 |
| history-git-reflog | 52 |
| history-git-rev-list | 60 |
| history-git-show | 268 |
| history-git-stash | 5 |
| history-gold-added-line | 1 |
| history-newer-commit | 280 |
| legacy | 692 |
| legacy-review-retained | 46 |
| test-name-absent-before-definition | 115 |
| test-name-agent-defined-before-output | 1 |
| test-name-present-at-base | 30338 |

Counts are findings, not unique events: the same occurrence can be represented in a trajectory and final artifacts, and several source rules can match one command. A successful fetch/history output is added alongside its attempted-command finding. Legacy REVIEW findings remain when rule 3 adds stronger evidence.

Confirmed artifact evidence (no oracle content):

| Task | Run | Role | Kind | Rule | Artifact | Line |
|---|---|---|---|---|---|---:|
| matplotlib__matplotlib-20676 | main_2_rerun_mpl | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 36 |
| matplotlib__matplotlib-20676 | main_2_rerun_mpl | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 38 |
| matplotlib__matplotlib-20676 | main_2_rerun_mpl | repair | git-history-search | history-newer-commit | trajectory.jsonl | 169 |
| matplotlib__matplotlib-20676 | main_2_rerun_mpl | repair | git-history-search | history-newer-commit | trajectory.jsonl | 169 |
| matplotlib__matplotlib-21568 | main_2_rerun_mpl | repair | git-history-search | history-newer-commit | trajectory.jsonl | 18 |
| matplotlib__matplotlib-21568 | main_2_rerun_mpl | repair | git-history-search | history-newer-commit | trajectory.jsonl | 37 |
| matplotlib__matplotlib-21568 | main_2_rerun_mpl | repair | test-patch-content | legacy | trajectory.jsonl | 0 |
| sympy__sympy-17318 | main_3_rerun_infra | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 28 |
| sympy__sympy-17318 | main_3_rerun_infra | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 67 |
| sympy__sympy-17318 | main_3_rerun_infra | generator | fail-to-pass-name | test-name-absent-before-definition | generation_trajectory.jsonl | 0 |
| sympy__sympy-19783 | main_3_rerun_infra | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 20 |
| sympy__sympy-19783 | main_3_rerun_infra | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 58 |
| sympy__sympy-19783 | main_3_rerun_infra | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 74 |
| sympy__sympy-17318 | main_3_rerun_infra | repair | git-history-search | history-newer-commit | trajectory.jsonl | 40 |
| sympy__sympy-17318 | main_3_rerun_infra | repair | git-history-search | history-newer-commit | trajectory.jsonl | 40 |
| sympy__sympy-17318 | main_3_rerun_infra | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| sympy__sympy-19783 | main_3_rerun_infra | repair | git-history-search | history-newer-commit | trajectory.jsonl | 49 |
| sympy__sympy-19783 | main_3_rerun_infra | repair | git-history-search | history-newer-commit | trajectory.jsonl | 50 |
| sympy__sympy-24562 | main_3_rerun_infra | repair | git-history-search | history-newer-commit | trajectory.jsonl | 41 |
| django__django-12965 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 64 |
| django__django-12965 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 64 |
| django__django-13158 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 18 |
| django__django-13158 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 40 |
| django__django-13158 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 62 |
| django__django-13212 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 21 |
| django__django-13212 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 36 |
| django__django-13212 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 38 |
| django__django-15037 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 82 |
| django__django-15499 | main_50_a | generator | fail-to-pass-name | test-name-absent-before-definition | generation_trajectory.jsonl | 0 |
| django__django-15572 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 19 |
| django__django-15930 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 25 |
| matplotlib__matplotlib-14623 | main_50_a | generator | newer-copy-path | legacy | generation_trajectory.jsonl | 0 |
| matplotlib__matplotlib-14623 | main_50_a | generator | newer-copy-path | legacy | generation_trajectory.jsonl | 0 |
| matplotlib__matplotlib-14623 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 14 |
| matplotlib__matplotlib-20676 | main_50_a | generator | newer-copy-path | legacy | generation_trajectory.jsonl | 0 |
| matplotlib__matplotlib-20676 | main_50_a | generator | newer-copy-path | legacy | generation_trajectory.jsonl | 0 |
| matplotlib__matplotlib-20676 | main_50_a | generator | newer-copy-path | legacy | generation_trajectory.jsonl | 0 |
| matplotlib__matplotlib-20676 | main_50_a | generator | newer-copy-path | legacy | generation_trajectory.jsonl | 0 |
| matplotlib__matplotlib-20676 | main_50_a | generator | newer-copy-path | legacy | generation_trajectory.jsonl | 0 |
| matplotlib__matplotlib-20676 | main_50_a | generator | newer-copy-path | legacy | generation_trajectory.jsonl | 0 |
| matplotlib__matplotlib-20676 | main_50_a | generator | gold-patch-content | legacy | generation_trajectory.jsonl | 0 |
| matplotlib__matplotlib-20676 | main_50_a | generator | test-patch-content | legacy | generation_trajectory.jsonl | 0 |
| matplotlib__matplotlib-20676 | main_50_a | generator | fail-to-pass-name | test-name-absent-before-definition | generation_trajectory.jsonl | 0 |
| matplotlib__matplotlib-20676 | main_50_a | generator | fail-to-pass-name | test-name-absent-before-definition | generation_trajectory.jsonl | 0 |
| matplotlib__matplotlib-20676 | main_50_a | generator | test-patch-content | legacy | test_repro_2.py | 0 |
| matplotlib__matplotlib-20676 | main_50_a | generator | test-patch-content | legacy | test_repro_3.py | 0 |
| matplotlib__matplotlib-21568 | main_50_a | generator | newer-copy-path | legacy | generation_trajectory.jsonl | 0 |
| matplotlib__matplotlib-21568 | main_50_a | generator | newer-copy-path | legacy | generation_trajectory.jsonl | 0 |
| matplotlib__matplotlib-21568 | main_50_a | generator | newer-copy-path | legacy | generation_trajectory.jsonl | 0 |
| matplotlib__matplotlib-21568 | main_50_a | generator | newer-copy-path | legacy | generation_trajectory.jsonl | 0 |
| matplotlib__matplotlib-21568 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 14 |
| matplotlib__matplotlib-21568 | main_50_a | generator | gold-patch-content | legacy | generation_trajectory.jsonl | 0 |
| matplotlib__matplotlib-21568 | main_50_a | generator | test-patch-content | legacy | generation_trajectory.jsonl | 0 |
| matplotlib__matplotlib-22871 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 22 |
| matplotlib__matplotlib-25122 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 17 |
| matplotlib__matplotlib-25122 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 26 |
| matplotlib__matplotlib-25122 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 26 |
| matplotlib__matplotlib-25122 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 27 |
| matplotlib__matplotlib-25122 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 27 |
| pallets__flask-5014 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 28 |
| pallets__flask-5014 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 28 |
| pallets__flask-5014 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 28 |
| pallets__flask-5014 | main_50_a | generator | fail-to-pass-name | test-name-absent-before-definition | generation_trajectory.jsonl | 0 |
| psf__requests-1724 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 51 |
| psf__requests-2317 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 22 |
| psf__requests-6028 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 14 |
| psf__requests-6028 | main_50_a | generator | gold-patch-content | legacy | generation_trajectory.jsonl | 0 |
| pydata__xarray-6599 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 28 |
| pydata__xarray-6599 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 44 |
| pydata__xarray-6744 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 12 |
| pydata__xarray-6744 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 18 |
| pydata__xarray-6744 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 21 |
| pydata__xarray-6744 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 21 |
| pydata__xarray-6744 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 21 |
| pylint-dev__pylint-4970 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 26 |
| pylint-dev__pylint-6528 | main_50_a | generator | newer-copy-path | legacy | generation_trajectory.jsonl | 0 |
| pylint-dev__pylint-6528 | main_50_a | generator | newer-copy-path | legacy | generation_trajectory.jsonl | 0 |
| pylint-dev__pylint-6528 | main_50_a | generator | newer-copy-path | legacy | generation_trajectory.jsonl | 0 |
| pylint-dev__pylint-6528 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 20 |
| pylint-dev__pylint-6528 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 32 |
| pylint-dev__pylint-6528 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 92 |
| pylint-dev__pylint-6528 | main_50_a | generator | fail-to-pass-name | test-name-absent-before-definition | generation_trajectory.jsonl | 0 |
| pylint-dev__pylint-6528 | main_50_a | generator | fail-to-pass-name | test-name-absent-before-definition | generation_trajectory.jsonl | 0 |
| pylint-dev__pylint-6528 | main_50_a | generator | pass-to-pass-name | test-name-absent-before-definition | generation_trajectory.jsonl | 0 |
| pylint-dev__pylint-6528 | main_50_a | generator | pass-to-pass-name | test-name-absent-before-definition | generation_trajectory.jsonl | 0 |
| pylint-dev__pylint-6528 | main_50_a | generator | pass-to-pass-name | test-name-absent-before-definition | generation_trajectory.jsonl | 0 |
| pylint-dev__pylint-6528 | main_50_a | generator | pass-to-pass-name | test-name-absent-before-definition | generation_trajectory.jsonl | 0 |
| pylint-dev__pylint-7277 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 18 |
| pytest-dev__pytest-5809 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 12 |
| scikit-learn__scikit-learn-14141 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 28 |
| scikit-learn__scikit-learn-14629 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 62 |
| sphinx-doc__sphinx-7910 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 46 |
| sphinx-doc__sphinx-7910 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 50 |
| sphinx-doc__sphinx-7910 | main_50_a | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 50 |
| astropy__astropy-14508 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 30 |
| astropy__astropy-14508 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 32 |
| astropy__astropy-14508 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 32 |
| astropy__astropy-14508 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 70 |
| django__django-10973 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 34 |
| django__django-11095 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 14 |
| django__django-11095 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 16 |
| django__django-11095 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 29 |
| django__django-12663 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 42 |
| django__django-12663 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 111 |
| django__django-13158 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 34 |
| django__django-13158 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 48 |
| django__django-13158 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 58 |
| django__django-13158 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 58 |
| django__django-13158 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 106 |
| django__django-13158 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| django__django-13212 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 20 |
| django__django-13212 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 56 |
| django__django-13212 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 56 |
| django__django-15037 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 43 |
| django__django-15037 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 43 |
| django__django-15037 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 44 |
| django__django-15037 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| django__django-15278 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 17 |
| django__django-15499 | main_50_a | repair | git-history-search | history-gold-added-line | trajectory.jsonl | 31 |
| django__django-15930 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 18 |
| django__django-15930 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 24 |
| django__django-15930 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 41 |
| django__django-15930 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 41 |
| django__django-15930 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| django__django-16612 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 31 |
| django__django-16612 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| django__django-16667 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| matplotlib__matplotlib-14623 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 43 |
| matplotlib__matplotlib-14623 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 74 |
| matplotlib__matplotlib-20676 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | agent_output.txt | 0 |
| matplotlib__matplotlib-20676 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | agent_output.txt | 0 |
| matplotlib__matplotlib-20676 | main_50_a | repair | gold-patch-content | legacy | patch.diff | 0 |
| matplotlib__matplotlib-20676 | main_50_a | repair | gold-patch-content | legacy | repair_record.json | 0 |
| matplotlib__matplotlib-20676 | main_50_a | repair | test-patch-content | legacy | repair_record.json | 0 |
| matplotlib__matplotlib-20676 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | repair_record.json | 0 |
| matplotlib__matplotlib-20676 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | repair_record.json | 0 |
| matplotlib__matplotlib-20676 | main_50_a | repair | gold-patch-content | legacy | submission_raw.txt | 0 |
| matplotlib__matplotlib-20676 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | submission_raw.txt | 0 |
| matplotlib__matplotlib-20676 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | submission_raw.txt | 0 |
| matplotlib__matplotlib-20676 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| matplotlib__matplotlib-20676 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| matplotlib__matplotlib-20676 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| matplotlib__matplotlib-20676 | main_50_a | repair | gold-patch-content | legacy | trajectory.jsonl | 0 |
| matplotlib__matplotlib-20676 | main_50_a | repair | test-patch-content | legacy | trajectory.jsonl | 0 |
| matplotlib__matplotlib-20676 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-20676 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-21568 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 58 |
| matplotlib__matplotlib-22871 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 71 |
| matplotlib__matplotlib-22871 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 87 |
| matplotlib__matplotlib-24026 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| matplotlib__matplotlib-24026 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| matplotlib__matplotlib-24026 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 44 |
| matplotlib__matplotlib-24627 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 28 |
| matplotlib__matplotlib-25122 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25122 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25287 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 18 |
| matplotlib__matplotlib-25332 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25332 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| matplotlib__matplotlib-25332 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 38 |
| matplotlib__matplotlib-25332 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 43 |
| matplotlib__matplotlib-25332 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 111 |
| matplotlib__matplotlib-26291 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 26 |
| matplotlib__matplotlib-26291 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 44 |
| matplotlib__matplotlib-26291 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 138 |
| pallets__flask-5014 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 52 |
| pallets__flask-5014 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 52 |
| pallets__flask-5014 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 66 |
| pallets__flask-5014 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| psf__requests-1766 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| psf__requests-1766 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| psf__requests-1766 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 16 |
| psf__requests-1766 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 28 |
| psf__requests-1766 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 28 |
| psf__requests-1766 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| psf__requests-2317 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 24 |
| psf__requests-2317 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 63 |
| psf__requests-2317 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 67 |
| psf__requests-2317 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 67 |
| psf__requests-2317 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 68 |
| psf__requests-2317 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 76 |
| psf__requests-2317 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 86 |
| psf__requests-2317 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 90 |
| psf__requests-2317 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 90 |
| psf__requests-2317 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 98 |
| psf__requests-2317 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 99 |
| psf__requests-6028 | main_50_a | repair | gold-patch-content | legacy | patch.diff | 0 |
| psf__requests-6028 | main_50_a | repair | gold-patch-content | legacy | repair_record.json | 0 |
| psf__requests-6028 | main_50_a | repair | gold-patch-content | legacy | submission_raw.txt | 0 |
| psf__requests-6028 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 15 |
| psf__requests-6028 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 60 |
| psf__requests-6028 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 60 |
| psf__requests-6028 | main_50_a | repair | gold-patch-content | legacy | trajectory.jsonl | 0 |
| pydata__xarray-4629 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 37 |
| pydata__xarray-4629 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| pydata__xarray-4695 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 31 |
| pydata__xarray-6599 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 28 |
| pydata__xarray-6599 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 84 |
| pydata__xarray-6599 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 84 |
| pydata__xarray-6599 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 84 |
| pydata__xarray-6599 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 87 |
| pydata__xarray-6599 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 109 |
| pydata__xarray-6744 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 26 |
| pylint-dev__pylint-4551 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| pylint-dev__pylint-4551 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| pylint-dev__pylint-4551 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| pylint-dev__pylint-4551 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| pylint-dev__pylint-4551 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 19 |
| pylint-dev__pylint-4551 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 22 |
| pylint-dev__pylint-4551 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 152 |
| pylint-dev__pylint-4970 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| pylint-dev__pylint-4970 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| pylint-dev__pylint-4970 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 29 |
| pylint-dev__pylint-6528 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| pylint-dev__pylint-6528 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 50 |
| pylint-dev__pylint-6528 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 166 |
| pylint-dev__pylint-6528 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 167 |
| pylint-dev__pylint-6528 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| pylint-dev__pylint-6528 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| pylint-dev__pylint-6528 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| pylint-dev__pylint-6528 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| pylint-dev__pylint-6528 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| pylint-dev__pylint-6528 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| pylint-dev__pylint-6528 | main_50_a | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| pylint-dev__pylint-7277 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| pylint-dev__pylint-7277 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 31 |
| scikit-learn__scikit-learn-12585 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | repair_record.json | 0 |
| scikit-learn__scikit-learn-12585 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 26 |
| scikit-learn__scikit-learn-12585 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 36 |
| scikit-learn__scikit-learn-12585 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 38 |
| scikit-learn__scikit-learn-12585 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 40 |
| scikit-learn__scikit-learn-12585 | main_50_a | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| sphinx-doc__sphinx-10614 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| sphinx-doc__sphinx-10614 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| sphinx-doc__sphinx-10614 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 89 |
| sphinx-doc__sphinx-7748 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| sphinx-doc__sphinx-7748 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 21 |
| sphinx-doc__sphinx-7748 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 46 |
| sphinx-doc__sphinx-7748 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 46 |
| sphinx-doc__sphinx-7748 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 56 |
| sphinx-doc__sphinx-7748 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 58 |
| sphinx-doc__sphinx-7910 | main_50_a | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| sphinx-doc__sphinx-7910 | main_50_a | repair | git-history-search | history-newer-commit | trajectory.jsonl | 18 |
| astropy__astropy-13977 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 20 |
| django__django-11820 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 38 |
| django__django-12209 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 16 |
| django__django-12209 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 48 |
| django__django-12209 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 48 |
| django__django-13297 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 29 |
| django__django-13820 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 19 |
| django__django-13820 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 21 |
| django__django-13820 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 21 |
| django__django-14631 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 17 |
| django__django-16136 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 20 |
| django__django-16315 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 41 |
| django__django-16631 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 20 |
| django__django-16631 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 74 |
| matplotlib__matplotlib-20488 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 64 |
| matplotlib__matplotlib-22719 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 12 |
| matplotlib__matplotlib-22719 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 22 |
| matplotlib__matplotlib-22719 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 22 |
| matplotlib__matplotlib-23299 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 20 |
| matplotlib__matplotlib-23299 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 22 |
| matplotlib__matplotlib-23299 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 28 |
| matplotlib__matplotlib-23299 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 28 |
| matplotlib__matplotlib-23476 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 66 |
| matplotlib__matplotlib-24637 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 58 |
| matplotlib__matplotlib-24637 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 64 |
| matplotlib__matplotlib-24637 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 78 |
| matplotlib__matplotlib-24637 | main_50_b | generator | fail-to-pass-name | test-name-absent-before-definition | generation_trajectory.jsonl | 0 |
| matplotlib__matplotlib-24970 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 10 |
| matplotlib__matplotlib-25479 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 42 |
| matplotlib__matplotlib-25479 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 42 |
| matplotlib__matplotlib-25479 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 80 |
| mwaskom__seaborn-3069 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 28 |
| mwaskom__seaborn-3069 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 74 |
| psf__requests-1142 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 14 |
| psf__requests-1142 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 28 |
| psf__requests-1142 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 28 |
| psf__requests-1142 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 74 |
| psf__requests-5414 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 19 |
| pydata__xarray-4966 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 42 |
| pylint-dev__pylint-4661 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 11 |
| pylint-dev__pylint-4661 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 25 |
| pylint-dev__pylint-4661 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 25 |
| pytest-dev__pytest-10051 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 18 |
| pytest-dev__pytest-5787 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 28 |
| pytest-dev__pytest-5787 | main_50_b | generator | fail-to-pass-name | test-name-absent-before-definition | generation_trajectory.jsonl | 0 |
| pytest-dev__pytest-5787 | main_50_b | generator | fail-to-pass-name | test-name-absent-before-definition | generation_trajectory.jsonl | 0 |
| pytest-dev__pytest-7236 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 34 |
| pytest-dev__pytest-7521 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 15 |
| sphinx-doc__sphinx-10323 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 26 |
| sphinx-doc__sphinx-10466 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 22 |
| sphinx-doc__sphinx-10466 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 27 |
| sphinx-doc__sphinx-10466 | main_50_b | generator | git-history-search | history-newer-commit | generation_trajectory.jsonl | 55 |
| astropy__astropy-13398 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 46 |
| astropy__astropy-13398 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 46 |
| astropy__astropy-13398 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 48 |
| astropy__astropy-13977 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 59 |
| django__django-12209 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 118 |
| django__django-12209 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 118 |
| django__django-13033 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 36 |
| django__django-13033 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 64 |
| django__django-13033 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 64 |
| django__django-13297 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 39 |
| django__django-13297 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 59 |
| django__django-13297 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 81 |
| django__django-13569 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 32 |
| django__django-13569 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 36 |
| django__django-13569 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 64 |
| django__django-13820 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 19 |
| django__django-13820 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 19 |
| django__django-13820 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 42 |
| django__django-13820 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 42 |
| django__django-14140 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 26 |
| django__django-14140 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 30 |
| django__django-14140 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 32 |
| django__django-14140 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 136 |
| django__django-14140 | main_50_b | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| django__django-14631 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 28 |
| django__django-16136 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 26 |
| django__django-16136 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 52 |
| django__django-16315 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 56 |
| django__django-16315 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 149 |
| django__django-16631 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 39 |
| django__django-16631 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 103 |
| matplotlib__matplotlib-20488 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 93 |
| matplotlib__matplotlib-20488 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 119 |
| matplotlib__matplotlib-20488 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 173 |
| matplotlib__matplotlib-22719 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 38 |
| matplotlib__matplotlib-22865 | main_50_b | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-22865 | main_50_b | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-22865 | main_50_b | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-22865 | main_50_b | repair | pass-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-23299 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 30 |
| matplotlib__matplotlib-23299 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 39 |
| matplotlib__matplotlib-23299 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 39 |
| matplotlib__matplotlib-23299 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 57 |
| matplotlib__matplotlib-23476 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 45 |
| matplotlib__matplotlib-23476 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 51 |
| matplotlib__matplotlib-23476 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 93 |
| matplotlib__matplotlib-23476 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 93 |
| matplotlib__matplotlib-23476 | main_50_b | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-24177 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 50 |
| matplotlib__matplotlib-24637 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 68 |
| matplotlib__matplotlib-24637 | main_50_b | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| matplotlib__matplotlib-24970 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 18 |
| matplotlib__matplotlib-25479 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 26 |
| matplotlib__matplotlib-25479 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 28 |
| matplotlib__matplotlib-25479 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 30 |
| mwaskom__seaborn-3069 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 22 |
| mwaskom__seaborn-3069 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 38 |
| mwaskom__seaborn-3069 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 39 |
| mwaskom__seaborn-3069 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 39 |
| psf__requests-1142 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 23 |
| psf__requests-1142 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 44 |
| psf__requests-1142 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 44 |
| psf__requests-1142 | main_50_b | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| psf__requests-2931 | main_50_b | repair | gold-patch-content | legacy | patch.diff | 0 |
| psf__requests-2931 | main_50_b | repair | gold-patch-content | legacy | repair_record.json | 0 |
| psf__requests-2931 | main_50_b | repair | gold-patch-content | legacy | submission_raw.txt | 0 |
| psf__requests-2931 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 14 |
| psf__requests-2931 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 75 |
| psf__requests-2931 | main_50_b | repair | gold-patch-content | legacy | trajectory.jsonl | 0 |
| psf__requests-2931 | main_50_b | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |
| pylint-dev__pylint-4661 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 83 |
| pylint-dev__pylint-4661 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 131 |
| pylint-dev__pylint-6903 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 32 |
| pylint-dev__pylint-6903 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 32 |
| pylint-dev__pylint-6903 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 44 |
| pylint-dev__pylint-6903 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 44 |
| pylint-dev__pylint-8898 | main_50_b | repair | newer-copy-path | legacy | trajectory.jsonl | 0 |
| pylint-dev__pylint-8898 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 22 |
| pylint-dev__pylint-8898 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 54 |
| pylint-dev__pylint-8898 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 56 |
| pytest-dev__pytest-5787 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 45 |
| pytest-dev__pytest-7236 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 19 |
| pytest-dev__pytest-7236 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 70 |
| scikit-learn__scikit-learn-10908 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 30 |
| scikit-learn__scikit-learn-10908 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 88 |
| scikit-learn__scikit-learn-10908 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 88 |
| sphinx-doc__sphinx-10323 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 92 |
| sphinx-doc__sphinx-10435 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 22 |
| sphinx-doc__sphinx-10435 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 34 |
| sphinx-doc__sphinx-10435 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 77 |
| sphinx-doc__sphinx-10466 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 18 |
| sphinx-doc__sphinx-10466 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 44 |
| sphinx-doc__sphinx-10466 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 79 |
| sphinx-doc__sphinx-10466 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 165 |
| sympy__sympy-14711 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 16 |
| sympy__sympy-14711 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 58 |
| sympy__sympy-17318 | main_50_b | repair | git-history-search | history-newer-commit | trajectory.jsonl | 28 |
| sympy__sympy-17318 | main_50_b | repair | fail-to-pass-name | test-name-absent-before-definition | trajectory.jsonl | 0 |

## Golden comparison and rule 3

Immutable baseline: audit module from `7fefe1d`. Legacy findings: 912; golden violations: 0; explicit rule-3 downgrades: 0. Comparison uses a multiset of artifact, kind, line and severity. `downgrades.json` lists every downgrade; the independent verifier reopens the archive directly and checks its digest and symbol hashes.

The original Git/grep base-probe subtraction was independently rerun in all 100 images; its probe-hash sets exactly matched the extended audit inputs. This includes the original grep symlink and binary handling.

Base test symbols are checked in SHA-256-verified `SourceArchive` inputs. 83 archives carry historical pins; 10 existing archives receive audit inventory pins. The seven requests archives were missing from the supplied archive directory, so read-only `git archive` of each image’s pinned base commit supplied a local archive and a new digest. This provenance is recorded per task. A name at base is REVIEW. An absent name seen before any successful agent file-write defines it is CONFIRMED; a name introduced by such a write is REVIEW. Final artifacts are assessed after the trajectory’s writes.

## Image exposure

Every image was read through our own anonymous `docker run --rm --network none --read-only --pull never` containers, with a read-only probe mount. No existing container was inspected, stopped or changed; no image was pulled. Git probes use read-only commands, including `hash-object` without `-w`. All reachable refs and all objects are enumerated; newer timestamps and descendants of base both count. A setup commit after base alone does not establish that an answer is available. Exact gold post-image blob presence is tested independently.

| Task | Future reachable | Future objects | Changed file categories | Mode-only / content changes where source paths changed | Gold added-line matches in future diff | Gold blobs present / probed |
|---|---:|---:|---|---|---:|---:|
| astropy__astropy-13398 | 1 | 1 | build_metadata=1 | see categories | 0 | 0 / 4 |
| astropy__astropy-13977 | 1 | 1 | build_metadata=1 | see categories | 0 | 0 / 1 |
| astropy__astropy-14365 | 1 | 1 | build_metadata=4, other_files=777, other_source=648, test_source=425, version_source=1 | 1854 / 1 | 0 | 0 / 1 |
| astropy__astropy-14508 | 1 | 1 | build_metadata=1 | see categories | 0 | 0 / 1 |
| astropy__astropy-7606 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-10973 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-11095 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-11299 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-11820 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-12209 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-12663 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-12965 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-13023 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-13033 | 1 | 1 | build_metadata=4, other_files=3610, other_source=847, test_source=1789, version_source=1 | 6251 / 0 | 0 | 0 / 1 |
| django__django-13158 | 1 | 1 | build_metadata=4, other_files=3611, other_source=851, test_source=1790, version_source=1 | 6257 / 0 | 0 | 0 / 1 |
| django__django-13212 | 1 | 1 | identical tree | see categories | 0 | 0 / 2 |
| django__django-13297 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-13569 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-13786 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-13807 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-13820 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-14140 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-14631 | 1 | 1 | identical tree | see categories | 0 | 0 / 2 |
| django__django-15037 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-15103 | 1 | 1 | identical tree | see categories | 0 | 0 / 2 |
| django__django-15278 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-15375 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-15499 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-15572 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-15930 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-16082 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-16136 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-16255 | 1 | 1 | build_metadata=5, other_files=3889, other_source=867, test_source=1878, version_source=1 | 6640 / 0 | 0 | 0 / 1 |
| django__django-16315 | 1 | 1 | identical tree | see categories | 0 | 0 / 2 |
| django__django-16612 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| django__django-16631 | 1 | 1 | identical tree | see categories | 0 | 0 / 2 |
| django__django-16667 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| matplotlib__matplotlib-14623 | 1 | 1 | identical tree | see categories | 0 | 0 / 3 |
| matplotlib__matplotlib-20488 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| matplotlib__matplotlib-20676 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| matplotlib__matplotlib-21568 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| matplotlib__matplotlib-22719 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| matplotlib__matplotlib-22865 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| matplotlib__matplotlib-22871 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| matplotlib__matplotlib-23299 | 1 | 1 | build_metadata=3, other_files=3384, other_source=944, test_source=102 | 4433 / 0 | 0 | 0 / 1 |
| matplotlib__matplotlib-23476 | 1 | 1 | build_metadata=3, other_files=3402, other_source=944, test_source=102 | 4451 / 0 | 0 | 0 / 1 |
| matplotlib__matplotlib-24026 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| matplotlib__matplotlib-24177 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| matplotlib__matplotlib-24627 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| matplotlib__matplotlib-24637 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| matplotlib__matplotlib-24970 | 1 | 1 | build_metadata=4, other_files=3384, other_source=951, test_source=107 | 4446 / 0 | 0 | 0 / 1 |
| matplotlib__matplotlib-25122 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| matplotlib__matplotlib-25287 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| matplotlib__matplotlib-25332 | 1 | 1 | build_metadata=4, other_files=3331, other_source=943, test_source=107 | 4385 / 0 | 0 | 0 / 1 |
| matplotlib__matplotlib-25479 | 1 | 1 | identical tree | see categories | 0 | 0 / 2 |
| matplotlib__matplotlib-26291 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| mwaskom__seaborn-3069 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| pallets__flask-5014 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| psf__requests-1142 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| psf__requests-1724 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| psf__requests-1766 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| psf__requests-2317 | 1 | 1 | build_metadata=3, other_files=42, other_source=80 | 125 / 0 | 0 | 0 / 1 |
| psf__requests-2931 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| psf__requests-5414 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| psf__requests-6028 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| pydata__xarray-4629 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| pydata__xarray-4695 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| pydata__xarray-4966 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| pydata__xarray-6599 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| pydata__xarray-6744 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| pylint-dev__pylint-4551 | 1 | 1 | identical tree | see categories | 0 | 0 / 4 |
| pylint-dev__pylint-4661 | 1 | 1 | identical tree | see categories | 0 | 0 / 2 |
| pylint-dev__pylint-4970 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| pylint-dev__pylint-6528 | 1 | 1 | identical tree | see categories | 0 | 0 / 2 |
| pylint-dev__pylint-6903 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| pylint-dev__pylint-7277 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| pylint-dev__pylint-8898 | 1 | 1 | identical tree | see categories | 0 | 0 / 3 |
| pytest-dev__pytest-10051 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| pytest-dev__pytest-5787 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| pytest-dev__pytest-5809 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| pytest-dev__pytest-6202 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| pytest-dev__pytest-7236 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| pytest-dev__pytest-7432 | 1 | 1 | build_metadata=5, other_files=323, other_source=114, test_source=96, version_source=1 | 539 / 0 | 0 | 0 / 1 |
| pytest-dev__pytest-7521 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| scikit-learn__scikit-learn-10908 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| scikit-learn__scikit-learn-12585 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| scikit-learn__scikit-learn-14141 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| scikit-learn__scikit-learn-14629 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| scikit-learn__scikit-learn-14894 | 1 | 1 | build_metadata=20, other_files=415, other_source=567, test_source=215 | 1217 / 0 | 0 | 0 / 1 |
| sphinx-doc__sphinx-10323 | 1 | 1 | build_metadata=1 | see categories | 0 | 0 / 1 |
| sphinx-doc__sphinx-10435 | 1 | 1 | build_metadata=1 | see categories | 0 | 0 / 1 |
| sphinx-doc__sphinx-10466 | 1 | 1 | build_metadata=1 | see categories | 0 | 0 / 1 |
| sphinx-doc__sphinx-10614 | 1 | 1 | build_metadata=1 | see categories | 0 | 0 / 1 |
| sphinx-doc__sphinx-7748 | 1 | 1 | build_metadata=2 | 0 / 2 | 0 | 0 / 1 |
| sphinx-doc__sphinx-7910 | 1 | 1 | build_metadata=2 | 0 / 2 | 0 | 0 / 1 |
| sympy__sympy-13480 | 1 | 1 | build_metadata=1, other_files=304, other_source=630, test_source=502, version_source=1 | 1438 / 0 | 0 | 0 / 1 |
| sympy__sympy-14711 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |
| sympy__sympy-17318 | 1 | 1 | identical tree | see categories | 0 | 0 / 2 |
| sympy__sympy-19783 | 1 | 1 | identical tree | see categories | 0 | 0 / 2 |
| sympy__sympy-24562 | 1 | 1 | identical tree | see categories | 0 | 0 / 1 |

Each `images/<iid>.json` records future commit hashes, changed-file counts, changed-source-file counts, hashed changed paths, object counts and gold blob hash/presence pairs. No commit messages, source text or patch lines are published.

Future commits with source changes: 14. Eleven of these change only file permissions. The astropy task `astropy__astropy-14365` changes 1,854 file modes and one file’s content; the two sphinx tasks `sphinx-doc__sphinx-7748` and `sphinx-doc__sphinx-7910` each change two build-metadata files. None of the future commit diffs contains a distinctive gold-added line. The per-image tree deltas record all affected tasks without revealing content.

**Smallest proposed isolation fix (not implemented):** start the agent with a fresh single-commit repository materialized from the verified pinned base archive, with no copied `.git` directory. Keep the installed task environment and existing network/cache masks. This removes historical refs, reflogs and dangling objects together. Merely deleting refs leaves objects searchable. The user owns the decision to change agent startup.

### Package caches and unmasked copies

| Task | Conda cache files | Pip cache files | Repo archives | Unmasked copies | Different versions |
|---|---:|---:|---:|---:|---:|
| astropy__astropy-13398 | 19436 | 213 | 0 | 0 | 0 |
| astropy__astropy-13977 | 19436 | 213 | 0 | 0 | 0 |
| astropy__astropy-14365 | 19436 | 213 | 0 | 0 | 0 |
| astropy__astropy-14508 | 19436 | 213 | 0 | 0 | 0 |
| astropy__astropy-7606 | 17626 | 91 | 0 | 0 | 0 |
| django__django-10973 | 17775 | 77 | 0 | 0 | 0 |
| django__django-11095 | 17775 | 77 | 0 | 0 | 0 |
| django__django-11299 | 17775 | 77 | 0 | 0 | 0 |
| django__django-11820 | 17775 | 77 | 0 | 0 | 0 |
| django__django-12209 | 17775 | 77 | 0 | 0 | 0 |
| django__django-12663 | 17775 | 77 | 0 | 0 | 0 |
| django__django-12965 | 17775 | 89 | 0 | 0 | 0 |
| django__django-13023 | 17775 | 89 | 0 | 0 | 0 |
| django__django-13033 | 17775 | 89 | 0 | 0 | 0 |
| django__django-13158 | 17775 | 89 | 0 | 0 | 0 |
| django__django-13212 | 17775 | 89 | 0 | 0 | 0 |
| django__django-13297 | 17775 | 89 | 0 | 0 | 0 |
| django__django-13569 | 17775 | 89 | 0 | 0 | 0 |
| django__django-13786 | 17775 | 89 | 0 | 0 | 0 |
| django__django-13807 | 17775 | 89 | 0 | 0 | 0 |
| django__django-13820 | 17775 | 89 | 0 | 0 | 0 |
| django__django-14140 | 18852 | 315 | 0 | 0 | 0 |
| django__django-14631 | 18852 | 315 | 0 | 0 | 0 |
| django__django-15037 | 19506 | 361 | 0 | 0 | 0 |
| django__django-15103 | 19506 | 361 | 0 | 0 | 0 |
| django__django-15278 | 19506 | 361 | 0 | 0 | 0 |
| django__django-15375 | 19506 | 361 | 0 | 0 | 0 |
| django__django-15499 | 19506 | 361 | 0 | 0 | 0 |
| django__django-15572 | 19506 | 361 | 0 | 0 | 0 |
| django__django-15930 | 19506 | 361 | 0 | 0 | 0 |
| django__django-16082 | 19506 | 361 | 0 | 0 | 0 |
| django__django-16136 | 19506 | 361 | 0 | 0 | 0 |
| django__django-16255 | 19506 | 361 | 0 | 0 | 0 |
| django__django-16315 | 19506 | 361 | 0 | 0 | 0 |
| django__django-16612 | 19620 | 337 | 0 | 0 | 0 |
| django__django-16631 | 19620 | 337 | 0 | 0 | 0 |
| django__django-16667 | 19620 | 337 | 0 | 0 | 0 |
| matplotlib__matplotlib-14623 | 18773 | 225 | 0 | 0 | 0 |
| matplotlib__matplotlib-20488 | 18773 | 717 | 1 | 0 | 0 |
| matplotlib__matplotlib-20676 | 18773 | 717 | 1 | 0 | 0 |
| matplotlib__matplotlib-21568 | 18773 | 717 | 1 | 0 | 0 |
| matplotlib__matplotlib-22719 | 72706 | 107 | 0 | 0 | 0 |
| matplotlib__matplotlib-22865 | 74729 | 113 | 0 | 0 | 0 |
| matplotlib__matplotlib-22871 | 74729 | 111 | 0 | 0 | 0 |
| matplotlib__matplotlib-23299 | 74729 | 113 | 0 | 0 | 0 |
| matplotlib__matplotlib-23476 | 74729 | 113 | 0 | 0 | 0 |
| matplotlib__matplotlib-24026 | 75446 | 107 | 0 | 0 | 0 |
| matplotlib__matplotlib-24177 | 75446 | 135 | 0 | 0 | 0 |
| matplotlib__matplotlib-24627 | 75446 | 141 | 0 | 0 | 0 |
| matplotlib__matplotlib-24637 | 75446 | 147 | 0 | 0 | 0 |
| matplotlib__matplotlib-24970 | 75446 | 145 | 0 | 0 | 0 |
| matplotlib__matplotlib-25122 | 75446 | 145 | 0 | 0 | 0 |
| matplotlib__matplotlib-25287 | 75669 | 147 | 0 | 0 | 0 |
| matplotlib__matplotlib-25332 | 73721 | 141 | 0 | 0 | 0 |
| matplotlib__matplotlib-25479 | 75669 | 147 | 0 | 0 | 0 |
| matplotlib__matplotlib-26291 | 75669 | 147 | 0 | 0 | 0 |
| mwaskom__seaborn-3069 | 19506 | 273 | 0 | 0 | 0 |
| pallets__flask-5014 | 19698 | 381 | 0 | 0 | 0 |
| psf__requests-1142 | 20143 | 3 | 0 | 5 | 4 |
| psf__requests-1724 | 21972 | 4 | 0 | 5 | 4 |
| psf__requests-1766 | 20143 | 3 | 0 | 5 | 4 |
| psf__requests-2317 | 20143 | 3 | 0 | 5 | 4 |
| psf__requests-2931 | 20143 | 3 | 0 | 5 | 4 |
| psf__requests-5414 | 20143 | 27 | 0 | 5 | 4 |
| psf__requests-6028 | 20143 | 27 | 0 | 5 | 4 |
| pydata__xarray-4629 | 94352 | 89 | 0 | 0 | 0 |
| pydata__xarray-4695 | 94352 | 85 | 0 | 0 | 0 |
| pydata__xarray-4966 | 94352 | 113 | 0 | 0 | 0 |
| pydata__xarray-6599 | 88058 | 119 | 0 | 0 | 0 |
| pydata__xarray-6744 | 87027 | 113 | 0 | 0 | 0 |
| pylint-dev__pylint-4551 | 19504 | 363 | 0 | 0 | 0 |
| pylint-dev__pylint-4661 | 19504 | 357 | 0 | 0 | 0 |
| pylint-dev__pylint-4970 | 19504 | 357 | 0 | 0 | 0 |
| pylint-dev__pylint-6528 | 19504 | 381 | 0 | 0 | 0 |
| pylint-dev__pylint-6903 | 19504 | 411 | 0 | 0 | 0 |
| pylint-dev__pylint-7277 | 19504 | 423 | 0 | 0 | 0 |
| pylint-dev__pylint-8898 | 19436 | 331 | 0 | 0 | 0 |
| pytest-dev__pytest-10051 | 19504 | 77 | 0 | 0 | 0 |
| pytest-dev__pytest-5787 | 19504 | 85 | 0 | 0 | 0 |
| pytest-dev__pytest-5809 | 19504 | 103 | 0 | 0 | 0 |
| pytest-dev__pytest-6202 | 19504 | 85 | 0 | 0 | 0 |
| pytest-dev__pytest-7236 | 19504 | 79 | 0 | 0 | 0 |
| pytest-dev__pytest-7432 | 19504 | 85 | 0 | 0 | 0 |
| pytest-dev__pytest-7521 | 19504 | 85 | 0 | 0 | 0 |
| scikit-learn__scikit-learn-10908 | 38035 | 2 | 0 | 0 | 0 |
| scikit-learn__scikit-learn-12585 | 38035 | 2 | 0 | 0 | 0 |
| scikit-learn__scikit-learn-14141 | 38035 | 4 | 0 | 0 | 0 |
| scikit-learn__scikit-learn-14629 | 38035 | 4 | 0 | 0 | 0 |
| scikit-learn__scikit-learn-14894 | 38035 | 4 | 0 | 0 | 0 |
| sphinx-doc__sphinx-10323 | 19504 | 261 | 0 | 0 | 0 |
| sphinx-doc__sphinx-10435 | 19504 | 249 | 0 | 0 | 0 |
| sphinx-doc__sphinx-10466 | 19504 | 249 | 0 | 0 | 0 |
| sphinx-doc__sphinx-10614 | 19504 | 255 | 0 | 0 | 0 |
| sphinx-doc__sphinx-7748 | 19504 | 287 | 0 | 0 | 0 |
| sphinx-doc__sphinx-7910 | 19504 | 287 | 0 | 0 | 0 |
| sympy__sympy-13480 | 19916 | 9 | 0 | 0 | 0 |
| sympy__sympy-14711 | 19916 | 9 | 0 | 0 | 0 |
| sympy__sympy-17318 | 19916 | 9 | 0 | 0 | 0 |
| sympy__sympy-19783 | 19916 | 9 | 0 | 0 | 0 |
| sympy__sympy-24562 | 19916 | 9 | 0 | 0 | 0 |

| Masked repository package | Format | Version | Entries across images |
|---|---|---|---:|
| matplotlib | wheel | 3.7.5 | 3 |
| requests | conda-extracted | 2.31.0 | 7 |
| xarray | conda-extracted | 2025.4.0 | 5 |

Cache archive and extracted-package versions, paths or path hashes, and copy versions are recorded in each image JSON. These counts show what the two tmpfs masks hide before an agent starts. Copies resolving to `/testbed` are excluded from the unmasked-copy count. Base source versions are preferred; the fallback is an ancestor-tag description at the pinned base, explicitly identified in JSON. Version comparisons indicate differences, not an ordering of releases.

| Unmasked different-version copy task | Copy path | Base version | Copy version | Gold added-line matches |
|---|---|---|---|---:|
| psf__requests-1142 | `/opt/miniconda3/envs/testbed/lib/python3.9/site-packages/pip/_vendor/requests` | 1.1.0 | 2.32.3 | 0 |
| psf__requests-1142 | `/opt/miniconda3/lib/python3.11/site-packages/pip/_vendor/requests` | 1.1.0 | 2.31.0 | 0 |
| psf__requests-1142 | `/opt/miniconda3/lib/python3.11/site-packages/requests` | 1.1.0 | 2.31.0 | 0 |
| psf__requests-1142 | `/usr/lib/python3/dist-packages/pip/_vendor/requests` | 1.1.0 | 2.27.1 | 1 |
| psf__requests-1724 | `/opt/miniconda3/envs/testbed/lib/python2.7/site-packages/pip/_vendor/requests` | 2.0.1 | 2.22.0 | 0 |
| psf__requests-1724 | `/opt/miniconda3/lib/python3.11/site-packages/pip/_vendor/requests` | 2.0.1 | 2.31.0 | 0 |
| psf__requests-1724 | `/opt/miniconda3/lib/python3.11/site-packages/requests` | 2.0.1 | 2.31.0 | 0 |
| psf__requests-1724 | `/usr/lib/python3/dist-packages/pip/_vendor/requests` | 2.0.1 | 2.27.1 | 0 |
| psf__requests-1766 | `/opt/miniconda3/envs/testbed/lib/python3.9/site-packages/pip/_vendor/requests` | 2.0.1 | 2.32.3 | 0 |
| psf__requests-1766 | `/opt/miniconda3/lib/python3.11/site-packages/pip/_vendor/requests` | 2.0.1 | 2.31.0 | 0 |
| psf__requests-1766 | `/opt/miniconda3/lib/python3.11/site-packages/requests` | 2.0.1 | 2.31.0 | 0 |
| psf__requests-1766 | `/usr/lib/python3/dist-packages/pip/_vendor/requests` | 2.0.1 | 2.27.1 | 1 |
| psf__requests-2317 | `/opt/miniconda3/envs/testbed/lib/python3.9/site-packages/pip/_vendor/requests` | 2.4.3 | 2.32.3 | 0 |
| psf__requests-2317 | `/opt/miniconda3/lib/python3.11/site-packages/pip/_vendor/requests` | 2.4.3 | 2.31.0 | 0 |
| psf__requests-2317 | `/opt/miniconda3/lib/python3.11/site-packages/requests` | 2.4.3 | 2.31.0 | 0 |
| psf__requests-2317 | `/usr/lib/python3/dist-packages/pip/_vendor/requests` | 2.4.3 | 2.27.1 | 0 |
| psf__requests-2931 | `/opt/miniconda3/envs/testbed/lib/python3.9/site-packages/pip/_vendor/requests` | 2.9.0 | 2.32.3 | 2 |
| psf__requests-2931 | `/opt/miniconda3/lib/python3.11/site-packages/pip/_vendor/requests` | 2.9.0 | 2.31.0 | 2 |
| psf__requests-2931 | `/opt/miniconda3/lib/python3.11/site-packages/requests` | 2.9.0 | 2.31.0 | 2 |
| psf__requests-2931 | `/usr/lib/python3/dist-packages/pip/_vendor/requests` | 2.9.0 | 2.27.1 | 2 |
| psf__requests-5414 | `/opt/miniconda3/envs/testbed/lib/python3.9/site-packages/pip/_vendor/requests` | 2.26.0 | 2.32.3 | 0 |
| psf__requests-5414 | `/opt/miniconda3/lib/python3.11/site-packages/pip/_vendor/requests` | 2.26.0 | 2.31.0 | 0 |
| psf__requests-5414 | `/opt/miniconda3/lib/python3.11/site-packages/requests` | 2.26.0 | 2.31.0 | 0 |
| psf__requests-5414 | `/usr/lib/python3/dist-packages/pip/_vendor/requests` | 2.26.0 | 2.27.1 | 1 |
| psf__requests-6028 | `/opt/miniconda3/envs/testbed/lib/python3.9/site-packages/pip/_vendor/requests` | 2.27.0 | 2.32.3 | 2 |
| psf__requests-6028 | `/opt/miniconda3/lib/python3.11/site-packages/pip/_vendor/requests` | 2.27.0 | 2.31.0 | 2 |
| psf__requests-6028 | `/opt/miniconda3/lib/python3.11/site-packages/requests` | 2.27.0 | 2.31.0 | 2 |
| psf__requests-6028 | `/usr/lib/python3/dist-packages/pip/_vendor/requests` | 2.27.0 | 2.27.1 | 3 |

Requests exclusion check (counts only):

| Task | Vendored copies | Different-version vendored copies | Distinctive gold-line matches across copies |
|---|---:|---:|---:|
| psf__requests-1142 | 3 | 3 | 1 |
| psf__requests-1724 | 3 | 3 | 0 |
| psf__requests-1766 | 3 | 3 | 1 |
| psf__requests-2317 | 3 | 3 | 0 |
| psf__requests-2931 | 3 | 3 | 6 |
| psf__requests-5414 | 3 | 3 | 1 |
| psf__requests-6028 | 3 | 3 | 7 |

All seven requests images contain three different-version vendored copies. 5 contain at least one distinctive gold-added probe in a vendored copy. The exclusion therefore catches actual newer-source exposure. Probe matches do not establish that an entire fix was available or that the agent read the copy. No other cohort task has a different-version unmasked repository package.


## Validation and reproduction

All commands run from the worktree root with this worktree’s `.venv` and:

```sh
export HF_HOME=/home/sankalp/projects/wt-leakage/runs/hf_home
export HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1
env -u PYTHONPATH PYTHONPATH=src .venv/bin/python scripts/audit_image_leakage.py
env -u PYTHONPATH PYTHONPATH=src .venv/bin/python scripts/audit_leakage_gaps.py
env -u PYTHONPATH PYTHONPATH=src .venv/bin/python scripts/verify_leakage_gaps.py
env -u PYTHONPATH PYTHONPATH=src .venv/bin/python -m pytest -p no:cacheprovider -rfE
```

Docker access was escalated only for the listed image operations. The split `--prepare`/`--collect --inventory` mode supports Docker-only escalation. Private requests, dataset data, raw logs and exported archives remain under ignored `runs/`.

Offline dataset cache initially copied: 15,484,578 bytes (15 MB), only SWE-bench Verified Hub and datasets entries. Existing tests and reference files were unchanged.

Full unit-suite comparison by node ID: 0 new failures/errors; 0 reference failures now pass. The final suite reports 6 failed, 1542 passed, 7 skipped, 17 errors. All 71 new audit tests pass. The six failures and seventeen errors are exactly the reference IDs; there are no newly passing reference failures to explain. Full IDs and comparison are in `unit_comparison.json`; local output is `runs/leakage_gaps/pytest.out`. Synthetic tests cover every command family, ordered test definitions, verified archives, mocked Docker invocation and reachable/dangling commits in temporary repositories.

The independent verifier imports only the standard library. It recounts per-task JSON, checks report totals, preserves legacy findings as a multiset and rechecks each rule-3 downgrade directly against the archive. No agent-container isolation fix was implemented. No branch was pushed.
