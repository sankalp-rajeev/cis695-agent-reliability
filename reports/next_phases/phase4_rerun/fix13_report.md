# Fix 13: native module collection skips and exhaustive G1

The worktree preflight passed on `experiment/v2-execution-repair`: clean HEAD and live origin `434a17a2c39d3e5fc9ba4432656361e871eb2688`. No attempt-2 outcome/verdict files or correctness labels were read.

## Static and pristine-package diagnosis

[Per-module diagnosis](fix13_diagnosis/README.md), [seven-module CSV](fix13_diagnosis/modules.csv), and [pip/import receipts](fix13_diagnosis/package_checks.json).

All three required packages are absent in the immutable pristine Astropy-13977 image: pip show and direct import each exit 1 for **asdf, pyarrow, matplotlib**. Four modules have a top-level pytest.importorskip("asdf"); test_parquet.py has pytest.importorskip("pyarrow"). The two WCSAxes files are skipped by the parent astropy/visualization/wcsaxes/__init__.py's pytest.importorskip("matplotlib") before their module imports. The CSV provides exact source locations/statements and hashes. These checks used only frozen archive source and package imports, with no collection or benchmark test bodies.

## Committed rule and implementation

Plan amendment **3e6f46b** precedes implementation **a0e37d8**. Hypothesis thresholds, B1 and B2 are unchanged.

Native pytest collection uses **--collect-only -q -rs**, a collection-report plugin and selected-ID intersection. A module-level skip requires zero actual collected items, a native skip tied to the requested module (including a parent package), a nonempty reason, and no collection error. ANSI is stripped from reasons. Exit 5 alone or a missing package/static importorskip alone is not skip evidence. Native collect reports and -rs SKIPPED lines establish the skip; captured validation retains the module scope, normalized reason, native exit code and explicit native-skip marker.

Django recognizes an explicit unittest.SkipTest while loading a module, and SymPy recognizes its native Skipped exception through the native collection reporter. Neither converts an ordinary ImportError into a skip.

Recorded module skips map logical selected instances to **SKIPPED**, message **module_skip: <reason>**, without executing them or adding a family. A partial owner expansion still requires every expanded member to be admitted; module-skip instances retain their native reason and raw/selected mapping. Policy C and Policy S use the existing ordinary-SKIPPED rules unchanged. A native module skip exempts that collection stage from G3; genuine empty collection with no recorded skip remains COLLECTION_ERROR and zero-output halt.

The new [schema-2 G2 reference](fix13_reference/manifest.json) is rebuilt from the frozen original V2 run only, with [per-task counts](fix13_reference/counts.csv). It retains identity sets, not verdicts or outcome classes: original admission, original skipped identities, and identities whose stronger evidence cannot be replaced by a module skip. A module-skipped ID is compatible only with original SKIPPED or absent execution evidence. PASS/FAIL/ERROR (and other present admitted non-skip evidence) is not allowed to become skip-compatible; ERROR identities also count as lost under that rule. The launcher rejects old references lacking these identity categories. G2's >=10 OR >=1% thresholds are unchanged.

G1 runs **all 166 task/tree pairs without stopping at a failure**, retains per-module diagnostics/proposed categories, and evaluates its launch gate only after the final pair. Controlled-run fail-fast remains in place. The launcher requires the explicit exhaustive/end-evaluated seal. No new exception was added to the precommitted GIS/xmlschema list.

## Unit verification

Full pinned suite: **1,235 passed, 6 failed, 6 skipped, 17 errors (22.62 s)**, with exactly the pre-existing failure/error identities and no new failures. All **19 Fix 13 cases** pass. Tests cover native importorskip, allow_module_level, package initialization, ANSI reasons, empty/no-reason rejection, Policy C/S, G2 original-reference compatibility including ERROR, native Django/SymPy equivalents, partial expansion, historical Python 3.6, and exhaustive continuation after an earlier failure. [Unit receipt](fix13_diagnosis/unit_summary.json). The unrelated pre-existing fixture/Landlock/config/historical-seal failures are unchanged. Ruff and diff checks pass.

## Exhaustive G1

The audit uses fresh pinned containers for each tree, serially, with --network none, --cpu-shares 2048, --pull=never and a 1,800-second stage-pass budget. It performs pristine source checking, patched-tree patch application, native collection and runner help/startup only. **No benchmark test bodies, controlled run, new tag, attempt-2 outcome analysis or label access is authorized or performed.**

**166/166 pairs completed: 158 READY, 8 BLOCKED; launch denied.** The gate was evaluated only after the final pair. Wall time was **3,284.48 s (54.74 min)**. Pristine checking, patch application where applicable, and runner startup completed for all pairs. All 31 Django tasks completed both trees. G2 is explicitly **NOT_EVALUATED_NO_TEST_EXECUTION** here; its compatibility rule is unit-tested and its original-run reference covers all 83 tasks.

[All task/tree statuses](fix13_g1/tasks.csv), [machine failure catalogue](fix13_g1/failures.csv), [reviewed failure catalogue with diagnostics and proposed categories](fix13_g1/failures_reviewed.csv), [summary](fix13_g1/summary.json). The reviewed catalogue lists **every one of the 104 module/tree failures**, including the 96 pre-listed exceptions. It supplements empty zero-output diagnostics with native collection receipt evidence; the machine catalogue is preserved unchanged.

The following eight failures are outside the pre-listed exceptions. Each row applies independently to **base and patched**; input counts are per tree. All are native-collection stage failures or G3 halts, with zero selected output and no recorded module-skip reason.

| Task | Module | Inputs per tree | Diagnostic | Proposed category |
|---|---|---:|---|---|
| astropy__astropy-7606 | astropy/time/tests/test_comparisons.py | 3 | Collector reports completion, and its stdout lists the three exact selected IDs, but the validation receipt marks them native_not_found/INVALID_ID. G3 halts. | native_identity_receipt_mismatch; these IDs are **not established invalid** by this contradictory evidence |
| sympy__sympy-13480 | sympy/external/tests/test_sage.py | 18 | Completed collector returns no selected identities or native skip reason. Base source sets disabled=True for absent Sage and for Python 3; the native collector excludes disabled modules. G3 halts. | source_disabled_without_native_skip_record |
| matplotlib__matplotlib-23476 | lib/matplotlib/tests/test_backend_bases.py | 13 | Import of matplotlib.testing._markers at line 35 raises AttributeError: module 'matplotlib.testing' has no attribute 'compare'. All 13 selected slots enter explicit collector fallback. | module_import_attribute_error |
| pylint-dev__pylint-4970 | tests/functional/c/consider/consider_using_with_open.py | 17 | Module import at line 12 opens test.txt and raises FileNotFoundError. All 17 selected slots enter explicit collector fallback. | module_import_missing_local_file |

The Sage/static collector source excerpts and hashes are in [g1_static_followup.json](fix13_diagnosis/g1_static_followup.json). The Astropy methods are ordinary functions, not yield-test generators. No repair, synthesized skip, file creation or exception-list addition was made for these failures after the audit. Candidate follow-up work needs review: reconcile the Astropy native identity receipt; retain or explicitly report SymPy's native disabled-module reason; inspect Matplotlib's required import initialization; and determine whether the Pylint path is a runnable test module or a lint input fixture before changing its handling.

The **96 pre-listed module/tree failures** comprise **94 GIS_GUARD** and **2 XMLSCHEMA_MISSING** entries, across 15 tasks. Their exact modules, selected inputs, messages and allowed-exception matches appear in both catalogues. They remain missing evidence; permitted does not mean collected successfully. No other cause was exempted.

Native module skips were recorded for **20 module/tree pairs, covering 228 selected slots** in this collection-only audit:

- Astropy-13977: all seven diagnosed modules on each tree, **105 slots per tree** (asdf 34, pyarrow 28, matplotlib 43), no collector fallback and no G3 halt.
- Xarray-6744: test_cupy.py, 3 slots per tree, native missing-cupy reason.
- Scikit-learn-14629 and -14894: test_compare_lightgbm.py, 3 slots per task/tree, native missing-lightgbm reason.

[All native skip scopes/reasons/counts](fix13_g1/module_skips.csv); [seven-module confirmation on both trees](fix13_diagnosis/native_skip_confirmation.csv). These are collection dispositions, not executed outcomes or an admission-monotonicity result. The unit tests verify their eventual ordinary-SKIPPED and G2 treatment.

## Receipts and stop

G1 ran from implementation commit **a0e37d8**, with source and reference hashes in [manifest.json](fix13_g1/manifest.json). All **664 per-tree JSON receipts** are losslessly gzip-compressed for Git (241,887,688 original bytes to 15,162,942 bytes); [compression.json](fix13_g1/compression.json) retains every original receipt hash. The original uncompressed audit and original manifest remain under ignored `runs/phase4_fix13_g1_raw/`. The sealed manifest covers compressed receipts and the complete reviewed catalogues. Original native diagnostics are recoverable byte-for-byte.

**Stop for review: G1 is blocked. No new tag or controlled run was created.** No attempt-2 outcome/verdict or correctness-label data was read. Thresholds, B1/B2 and the pre-listed exceptions are unchanged.
