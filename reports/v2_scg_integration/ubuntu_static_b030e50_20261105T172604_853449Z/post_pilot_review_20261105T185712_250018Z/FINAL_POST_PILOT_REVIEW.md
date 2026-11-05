# Final post-pilot diagnostic review

Recommendation: **GO for the unchanged frozen experiment as a comparison of the two frozen pipelines under their shared native execution/verdict policy.** No demonstrated environment or source-integrity blocker remains in the reviewed pilot scope. Report parameter-family admission losses, raw concrete-case coverage, native abstentions and graph strata explicitly. The results will measure the complete frozen pipelines, including this parser limitation; they cannot isolate selector quality independently of test-ID admission.

Execution remains unauthorized by this diagnostic review. Recommended next action: separately authorize creation and review of an explicit 83-task execution plan against this original freeze, then authorize its guarded execution using that new plan's exact SHA-256. The existing three-task plan authorizes only its three tasks. No full plan or benchmark execution was created or started during this review.

## Identity and integrity

- Harness: `b030e508d849926b9a2260c70e1091adebfee993`, clean detached worktree `/home/sankalp/projects/cis695-v2-scg-paired-review-b030e50`.
- Corrected SCG: `e1a3ed1c74fd304493c3fe3811de755af77e306c`, unchanged clean worktree.
- Original protocol SHA-256: `2eaf8341274099cf4210674e6418a4b1e44ea2d0babb09a1c2243f77258c5153`.
- Original pilot results SHA-256: `1c38559c76a0f62f37bd7f301c988ceb02c6f2ab186b0680670e750cba03a8da`.
- Original pilot plan SHA-256: `57c84e2ceb615ebe7df43a5a26cf140b300b5a838f706ce6f7f7a5d2b9a77f1d`.
- Frozen validation passed again for all 83 tasks, including host environment, exact image bindings and daemon checks; validation started zero containers. See `validate_final.*`.
- All 766 frozen-tree files and 102 pilot-tree files match the before-review snapshot; all 765 frozen sealed artifacts and 101 pilot sealed artifacts match their manifests. This includes the pilot's 40 raw captures. No protected file was added, removed or changed.
- All 83 archives were independently SHA-256 checked again against the freeze. The static inventory reconciles every arm's selected count and all 18,717 pytest selected-ID slots; the remaining slots use the separate Django adapter. Total frozen slots remain V2 57,682 and SCG 131. All 354 task/file diagnostic source references match archive bytes.

The original freeze is usable unchanged. No reseal, parser fix, selection replacement or verdict promotion is required or recommended within this experiment.

## Matplotlib root cause

Frozen V2 selection for `matplotlib__matplotlib-25287`:

1. `lib/matplotlib/tests/test_skew.py::test_set_line_coll_dash_image`
2. `lib/matplotlib/tests/test_skew.py::test_skew_rectangle`

Both source functions use `image_comparison`. Its helper `_pytest_image_comparison` applies `pytest.mark.parametrize('extension', extensions)`; the default formats are png/pdf/svg. The actual saved base and patched output each contains six suffixed cases: both families have `[png]` PASSED, `[pdf]` PASSED and `[svg]` SKIPPED. Thus each phase has four passes and two skips, six observed concrete cases, twelve observations across the pair.

At the frozen harness revision, `src/reliability/verifier/container.py:478` accepts a pytest outcome only when its entire emitted ID is an exact member of the requested-ID set. None of the six suffixed IDs equals either requested bare family ID. Replaying the unchanged parser over saved raw output admits zero statuses in each phase. The requested `TestResult` entries therefore remain `NOT_RUN`; `regression.classify` preserves those two outcomes, and `n_executed == 0` yields native `NOT_AVAILABLE`.

The separate lossless raw-ID accounting maps each concrete case to exactly one requested family. The unchanged `completeness_of` rule accepts a missing/NOT_RUN family when all its mapped cases passed or skipped, so completeness is `COMPLETE` with no gaps. This rule does not modify the legacy TestResults or the native outcome count. `integrity_verdict` only downgrades incomplete PASS; it never promotes NOT_AVAILABLE. **The preserved result is EXECUTED / COMPLETE / NOT_AVAILABLE, with two requested IDs, zero native admitted executed IDs and six raw cases per phase.** See `matplotlib_parser_replay.json` for every case, mapping and replayed outcome. No new test was executed to obtain this diagnosis.

This is an unchanged shared parser limitation, rather than a container crash, missing test, timeout or demonstrated source mismatch. It applies to both execution arms. Its effect can be asymmetric because their selected family mixes differ. Xarray's pilot already demonstrates that some families can remain NOT_RUN while other admitted IDs allow a native PASS.

## Static exposure across all 83 tasks

The scan read frozen selections and archive AST/source data only. It examined direct function/class/module pytest parametrization, visible requested/autouse parametrized fixtures and dependencies, and source-verified helper decorators such as Matplotlib's image comparison. All positive evidence records include source paths, line numbers and SHA-256 values. No import, pytest collection or benchmark execution established these counts.

| Scope | Tasks | Statically exposed selected-ID slots |
|---|---:|---:|
| V2 | 36 | 3,913 |
| SCG | 4 | 17 |
| Either arm, unique tasks | 36 | Counts above include overlapping IDs |

There are **35 other tasks with definite static declaration exposure besides Matplotlib-25287**, or **34 beyond the two pilot tasks Matplotlib and Xarray already showing runtime family interpretation**. Eleven additional nonempty pytest tasks cannot be ruled out by static analysis. Thus 47 tasks form the conservative structural exposure envelope: 46 besides Matplotlib, or 45 beyond those two pilot tasks. These are exposure counts, not predicted NOT_AVAILABLE or failure counts.

The other 36 cohort tasks consist of 31 Django-runner tasks and five pytest tasks with both frozen lists empty. They are outside this particular nonempty pytest family-admission issue. All 83 identities and both arms, including empty and unavailable selections, are retained in `parameter_exposure_tasks.csv` and `.json`. No frozen ID already includes a bracketed parameter suffix in either arm.

SCG static exposure occurs in `matplotlib__matplotlib-25122` (3 IDs), `pydata__xarray-4629` (4), `pylint-dev__pylint-6528` (2) and `scikit-learn__scikit-learn-12585` (8). Every selected ID has a static parameter declaration in Matplotlib-25287 V2, Matplotlib-25122 SCG and Pylint-6528 SCG. These are higher-risk lists for zero native admissions; their runtime consequences remain unknown beyond the completed pilot.

The eleven additional uncertain tasks are astropy-14365, pylint-4661, pytest-5809, scikit-learn-14141, sphinx-10323, sphinx-7910, and sympy-13480/14711/17318/19783/24562. Full instance IDs are in `parameter_exposure_summary.json`.

Static declaration exposure does not prove collection, emitted suffixes, exact-admission losses or a whole-arm abstention. Conditional decorators, fixture overrides, plugins and collection hooks can alter runtime behavior. The scan is a lower bound on positively supported declarations, with a separate broad structural envelope; it is not proof that the eleven uncertain tasks are unaffected. No runtime impact was inferred from correctness labels or historical witnesses.

## Import-only diagnostics

Exactly three diagnostic containers used the frozen host-local immutable image IDs, `--pull=never`, `/testbed`, network disabled and no source mounts, matching the paired runner's container arrangement. No image was pulled, rebuilt, retagged or substituted. The normal image Python was invoked through the runner's login-shell context. The diagnostic child reproduced the entry-point `sys.path[0]`: `/testbed/tests` for Django's script and `/testbed` for `python -m pytest`. Image environment, full sys.path, origins, realpaths, package locations, editable metadata and file hashes are in `import_probes/`.

| Task | Frozen image ID | Project Python modules matching archive paths/bytes | Common source files matching | Install mechanism |
|---|---|---:|---:|---|
| django__django-15103 | `sha256:10ca209ff265ccb996602e08fe0362a94b3f6b3f80a0f4fb34cabc22fe697ae8` | 4/4 | 6/6 | PEP 660 editable finder; direct URL `file:///testbed` |
| matplotlib__matplotlib-25287 | `sha256:0a721ca71f4cfd2858777c2a451a954e50fa78f2551661a4cbcd0a9d6aa71c73` | 4/4 | 2/2 | Editable `.pth` adds `/testbed/lib` |
| pydata__xarray-4629 | `sha256:6ef760ecc8a78780f669f3e24a32e11a5ad5adaec505fce12cc15d27648657d0` | 7/7 | 7/7 | `easy-install.pth` and `xarray.egg-link` point to `/testbed` |

All 15 sampled project Python modules resolved to their expected source paths and match archive SHA-256 values. Django resolves under `/testbed/django`, Matplotlib under `/testbed/lib/matplotlib`, Xarray under `/testbed/xarray`. Dependencies such as pytest/numpy/pandas/dask resolve from the image's conda site-packages as recorded. No sampled target-package site-packages shadowing or conflicting realpath was found. Duplicate Xarray path entries resolve to the same files. Duplicate Matplotlib distribution metadata describes an editable install rather than a second imported target package.

Django and Matplotlib editable distribution metadata contains older version strings than their runtime source-derived version strings. This is an ambiguity in package metadata, already present in the bound images; the inspected source paths and bytes independently match. Neither version strings nor editable metadata alone establish source fidelity. Matplotlib `_path` and `ft2font` extension realpaths and binary hashes were recorded, but a source archive cannot establish their build provenance.

Before/after content, size and mtime snapshots match for 6,563 Django, 5,604 Matplotlib and 460 Xarray benchmark-tree files (excluding `.git`). All three probes returned zero, applied no candidate patch, and invoked no test collection or execution. They suppressed bytecode writes with `sys.dont_write_bytecode=True`; diagnostic files were placed under container `/tmp`. Three diagnostic containers were subsequently removed, confirmed by a read-only Docker inventory.

These probes reproduce entry-point import resolution, not pytest plugin/conftest collection, Django test setup, patched-state imports or every transitive import. They cannot supply missing retrospective evidence. No probe was represented as an identical re-execution of an earlier pytest process.

## Evidence interpretation and remaining limitations

1. **Source-file equivalence:** archive-to-container hash matches establish equivalence for the inspected relevant source/test files, including the pilot's shared prechecks. They do not establish whole-image historical identity or compiled-extension provenance.
2. **Current Python import resolution:** separate base-image probes establish actual module origins and hashes within their captured diagnostic context. Editable installation behavior is explained and sampled package shadowing was not found.
3. **Earlier execution imports:** the saved Django banner explicitly names `/testbed/django`; Xarray warning paths provide partial in-process source evidence; Matplotlib's earlier output does not establish adequate library origins. No complete earlier sys.path/module-origin ledger exists for all three runs. The new probes do not retroactively fill that gap or prove every earlier test import.

Finding classification:

- Demonstrated environment/source-integrity blockers: **none in the reviewed scope**. All 83 bindings/archives validate; runtime import probes cover only the three pilot images. The other 80 tasks have no new import-only probe in this review, and retain the harness's mandatory per-arm source checks.
- Unchanged measurement limitation: exact-ID admission of parameter families, affecting the interpretation and coverage of native outcomes. Keep native NOT_AVAILABLE, raw observations, incomplete states and abstentions intact. Report raw-versus-admitted coverage and the asymmetry between arms; raw observations must not silently become native PASS or FAIL.
- Missing diagnostic evidence: complete historical import traces, full transitive/patched-state import provenance, compiled-extension build provenance and runtime impact of the static exposure flags. These remain explicitly unknown, rather than established mismatches.
- SCG's original empty/unavailable lists and partial graphs remain unchanged scientific scope limitations. A complete evidence record for a selected list does not establish complete dependency reachability or patch correctness.

A parser repair or a new requirement for case-complete native scoring would define a different experimental protocol and would require separate review and freezing. The present GO recommendation applies to the original native-policy protocol with its transparent limitations. No code, selector, classification rule, candidate patch, image binding, freeze, pilot plan, result or raw evidence was changed; no correctness sidecar was accessed.

## Diagnostic artifacts

All new evidence is confined to this `post_pilot_review_20261105T185712_250018Z` directory. `evidence_sha256.json` seals every diagnostic file except itself; `SHA256SUMS` records that manifest's digest. Main machine-readable evidence: `final_integrity_verification.json`, `parameter_exposure_summary.json`, `parameter_exposure_tasks.csv`, `parameter_exposure_ids.json`, `matplotlib_parser_replay.json`, `import_provenance_verified_summary.json`, `import_probes/`, `archive_and_static_evidence_recheck.json`, `validate_final.*` and `docker_cleanup_verification.json`.
