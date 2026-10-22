# Current V2 diagnostic

Read-only analysis of the committed 93-task headline study, restricted to its
83 non-empty patches. All oracle comparisons are **POST-HOC ANALYSIS ONLY** and
must never feed selection, decisions, experiments, policies, manifests, or configs.

Files:

- `diagnostic.py`: oracle-free projection/aggregation of stored V2 evidence;
  reuses the existing patch parser, symbol extractor, record schema, and outcome enum.
- `oracle_posthoc.py`: the separate offline driver, oracle/test-ID comparison,
  CSV generation, and report generation. It never calls selection or execution.
- `patches.csv`: one row per non-empty headline patch, with independent
  `*_status` (`recorded`, `inferred`, `missing`) and `*_source` columns.
- `report.md`: results, distributions, repository summaries, limitations, and
  the exact generation command.
- `oracle_test_matches.csv`: every compared official ID, its normalization,
  matched selected IDs, or exact reason it remains unmatched.
- `wrong_patch_tests.csv`: failed-F2P-only classification for every known wrong
  patch; P2P-only failures are marked not applicable.
- `inputs.json`: generation command, Python version, code/input SHA-256 hashes.
- `sample_*`: the three-task preview generated and shown before the full run.
- `test_diagnostic.py`: offline matching, aggregation, provenance, population,
  no-execution, and production-import-boundary checks.

From the repository root, reproduce both principal outputs:

```bash
env -u PYTHONPATH .venv/bin/python -B reports/v2_diagnostic/oracle_posthoc.py --dataset-arrow /home/rajee/.cache/huggingface/datasets/SWE-bench___swe-bench_verified/default/0.0.0/78f471bf655a3137b2e8a75af1501690ec009ec3/swe-bench_verified-test.arrow
```

For the original three-task preview, append `--sample`. The Arrow file is an
already-stored benchmark cache; it is read directly without network access or
Hugging Face cache-lock writes. On another machine pass the identical cached
file at its local path and compare its hash with `inputs.json`. Without
`--dataset-arrow`, only the gold lists already preserved in the failure-analysis
snapshot are used; unsupported fields stay missing. That mode is useful but does
not reproduce the additional five local-only tasks' post-hoc comparisons.

Run tests without creating pytest/bytecode caches outside this directory:

```bash
env -u PYTHONPATH .venv/bin/python -B -m pytest reports/v2_diagnostic/test_diagnostic.py -p no:cacheprovider
```

The final-study CSV remains authoritative. Detailed study snapshots exist for
only 19 rows; five additional local records have unverified final-run identity
and are explicitly exploratory. The other 59 rows retain missing detailed fields.
No other run is substituted. In particular, pytest-7432 remains committed
`resolved` while a separate note records local `patch_apply_failed` and the
contradictory applied-cleanly/segfault harness evidence.

Tier membership and per-test V2 outcomes were not serialized. They cannot be
recovered from counts or selected-ID ordering, so they remain blank. Exact-ID
overlap counts are lower bounds when docstring names or renamed counterparts
cannot be resolved; no fuzzy matching is used. Large selected-ID unions remain
in the hashed input artifacts instead of exceeding ordinary CSV field limits.
