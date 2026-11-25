# build_labels.py: report.json shape fix (24 Nov 2026)

`build_labels.py` builds an analysis label file (`resolved`, `official_patch_sha256`, `evidence`) from the official `logs/<id>/report.json` and `patch.diff` files in the SWE-bench submissions bucket.

**Problem.** The first version read only the nested shape `{"<instance_id>": {"resolved": ...}}`, which Claude Sonnet 4's v1.0.0 reports use. Gemini 2.5 Flash's v1.0.0 reports (`20250726_mini-v1.0.0_gemini-2.5-flash`) put `resolved` at the top level. All 53 fetched Gemini reports were therefore skipped. chain_b2 step 1b wrote `with_label 0`, and the first `results_b1.md` showed Gemini with no labels.

**Fix.** The builder uses `data[iid]` when that key holds a dict, and otherwise the top-level object. It takes `resolved` only when it is a bool. The evidence string records the shape (`nested` or `flat`) and the report's sha256.

**Checks.**
- Claude Sonnet 4's labels rebuilt with the fixed builder are identical (60/60 `resolved` and patch sha256).
- Gemini: 53 of 60 ids are labelled. Each of the 53 official `patch.diff` sha256 values equals our sealed input bytes before newline normalization (0 mismatches).
- The other 7 ids have no official evaluation: django-11451, django-13401, xarray-3677, xarray-4687, scikit-learn-25973, sympy-14531, sympy-22456.
- Gemini's leaderboard entry has no `per_instance_details`, so it gives no cross-check (`leaderboard_missing 53`).

**Analysis.** `results_b1.md` and `results_b1.json` were produced by `scripts/analyze_v1_5.py` at tag `study-analysis-frozen` (sha256 `236fefbe5a356841e656e38a70c6938a52616b16a12e446712f2628fe9ffb49e`, unchanged), re-run for all three systems with these labels.
