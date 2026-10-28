# Baseline versus Full — post-hoc analysis only

The committed `docs/results_100.csv` supplies the authoritative merged population,
oracle labels, frozen V1–V4 signals and observed Full decisions. No agents,
verification, tests from benchmark repositories, oracle evaluations or ablations
are rerun. Policies, manifests, study labels and prior artifacts are untouched.

`reconstruction.py` calls the actual implemented policies on a signal-only
`Evidence` object. Oracle outcomes never reach that object. Baseline is
independently reconstructed. Full is the committed observation, checked against
code with explicit risk provenance; inferred risk absence is not independent
measurement. See report.md for the detailed missing-data qualification.

`statistics_core.py` implements metrics, Wilson intervals, paired patch bootstrap
(NumPy PCG64 seed 695, 10,000 resamples), exact stopped-ACCEPT enrichment and exact
McNemar on classification correctness. `compare.py` writes the derived tables;
`render_report.py` produces the report from them. No statistical test on raw
ACCEPT changes is presented as evidence of quality.

Run from the project root:

```bash
env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest reports/policy_comparison/test_comparison.py -q -p no:cacheprovider -o addopts=
env -u PYTHONPATH .venv/bin/python -B reports/policy_comparison/compare.py
```

Only the new test file is collected. Its fixtures are synthetic and include
hand-computed matrices, a reference Wilson interval and exact-test answers.
The report records conservative interpretations and the pytest-7432 sensitivity;
it never changes the authoritative headline. All files remain uncommitted.
