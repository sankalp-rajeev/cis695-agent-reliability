# Frozen V2 evaluation for review

- Validated code revision: `ea7d762f4b3e1320612f67893b5e7d7a46e5a68e`.
- Protocol SHA-256: `f3c8ef5c802d26985bbe0f70f5bf9f7ac846c73ef496b50e48af606bfead463f`.
- Status: **PREPARED_FOR_REVIEW_NOT_AUTHORIZED**. No full 83-task run has been launched.
- All 83 tasks have candidate bytes, selected-test manifests, base archive/source hashes and image availability records.
- 39 local images are present; 44 expected image tags are unavailable. A complete 83-task execution requires restoring those environments and preparing a new reviewed manifest.
- Source/configuration hashes include the unchanged regression/decision logic and frozen shadow-classifier configuration. The classifier remains shadow-only.
- Selection: `{"convention_sample_size": 200, "convention_seed": 695, "enable_tier0": false, "exclude_agent_authored_tests": true, "max_tier": 2}`.
- Execution: `{"baseline_cache_dir": null, "per_instance_timeout_s": 600, "per_pass_timeout_s": 300, "rerun_flaky": true}`.
- Fresh paired passes, no baseline cache, sequential containers, network disabled, no pulls/substitution, production resource defaults unchanged.
- The existing baseline-unreliable guard and confirmation behavior remain intact; no new total-time enforcement is introduced.

Run `env -u PYTHONPATH .venv/bin/python scripts/v2_evaluation.py validate --frozen reports/v2_discovery_cleanup/frozen_83` to review hashes without execution. See `README.md` for the guarded eventual run and post-collection metrics commands, and `runner_preparation_note.md` for the preparation CLI correction.

## Unavailable environments

- `astropy__astropy-13977`
- `astropy__astropy-7606`
- `django__django-11299`
- `django__django-11820`
- `django__django-12209`
- `django__django-13023`
- `django__django-13033`
- `django__django-13297`
- `django__django-13569`
- `django__django-13786`
- `django__django-13820`
- `django__django-14140`
- `django__django-14631`
- `django__django-15375`
- `django__django-16082`
- `django__django-16136`
- `django__django-16255`
- `django__django-16315`
- `django__django-16631`
- `matplotlib__matplotlib-20488`
- `matplotlib__matplotlib-22719`
- `matplotlib__matplotlib-23299`
- `matplotlib__matplotlib-23476`
- `matplotlib__matplotlib-24177`
- `matplotlib__matplotlib-24637`
- `matplotlib__matplotlib-24970`
- `matplotlib__matplotlib-25479`
- `mwaskom__seaborn-3069`
- `pydata__xarray-4966`
- `pylint-dev__pylint-4661`
- `pylint-dev__pylint-6903`
- `pytest-dev__pytest-10051`
- `pytest-dev__pytest-5787`
- `pytest-dev__pytest-7236`
- `pytest-dev__pytest-7521`
- `scikit-learn__scikit-learn-10908`
- `sphinx-doc__sphinx-10323`
- `sphinx-doc__sphinx-10435`
- `sphinx-doc__sphinx-10466`
- `sympy__sympy-13480`
- `sympy__sympy-14711`
- `sympy__sympy-17318`
- `sympy__sympy-19783`
- `sympy__sympy-24562`
