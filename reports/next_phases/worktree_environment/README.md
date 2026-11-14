# Local worktree environment

Synced this worktree's ignored `.venv` with `uv sync --frozen --python
/home/sankalp/projects/cis695-agent-reliability/.venv/bin/python`, using the
shared uv cache. Both environments use CPython 3.11.17. `reliability.__file__`
is this worktree's `src/reliability/__init__.py`; the interpreter guard passes.
The lockfile and project configuration are unchanged. Re-run via
`env -u PYTHONPATH .venv/bin/python -m pytest tests/unit`.

Before Fix 3: **1,023 passed, 6 failed, 6 skipped, 17 setup errors** (18.04 s).
The run used the existing shared dataset cache with HF network disabled.
Every failure/setup error is listed in `baseline_failures.csv`.

- One selection ground-truth test needs an absent ignored `.patch` fixture.
  It is not reconstructed from benchmark correctness data.
- Three shadow-classifier tests need Landlock ABI >=4, unavailable here.
  The classifier correctly abstains; tests expect probe results/predictions.
- One config-snapshot test expects the pre-Fix-2 RegressionConfig fields and
  does not include `skip_compatible=True`.
- One failure and 17 setup errors reject frozen V2 source/evidence drift:
  historical protocol hashes no longer match repaired scorer source.

These failures are present at the preflight commit before Fix 3 changes.
Historical seals and unrelated code/tests were not altered to make them pass.
No correctness labels were opened or used to resolve them. No configuration
change was needed; this separate commit records the environment and full-suite
baseline so later failures can be compared against it.
