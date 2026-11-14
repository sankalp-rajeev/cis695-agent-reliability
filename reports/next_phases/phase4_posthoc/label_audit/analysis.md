# Phase 4 label-integrity audit

This is post-hoc, after `phase4-run-sealed`. The original labels, sealed results, executor, and all tags stay unchanged. Audited grades below are separate measurements, never replacement labels. All 1,799 sealed run files were reverified before each audit/report execution.

## Binding and label basis across all 83 tasks

| Classification | Tasks |
|---|---:|
| SUPPORTED | 72 |
| SKIP_ONLY | 2 |
| BINDING_MISMATCH | 9 |
| NO_GRADER_RECORD | 0 |

Every archived record was located using the final CSV source-run binding, including the four `rerun` aliases. The inventory checks the frozen patch against the launch plan, correctness sidecar, and binding manifest. The original label comes from the pinned results CSV; it agrees with the archived oracle/report resolved status in all 83 cases. All applied-patch bytes are present verbatim in run_instance.log, and successful application is logged. Matching declared hashes in oracle_record.json do not repair mismatching actual applied bytes.

For nine tasks, the linked archived grading evidence describes a different **applied candidate** from the candidate named by the label metadata. The CSV label and linked report grade agree on correct/incorrect, but that agreement does not repair the frozen-candidate binding or establish how the provenance mismatch arose. This includes both correct and incorrect labels. No semantic patch equivalence is inferred from a byte mismatch.

| Task | Original CSV label / linked archived report grade | Frozen bytes | Applied bytes | Source run |
|---|---|---:|---:|---|
| astropy__astropy-13977 | incorrect / incorrect | 1096 | 4475 | main_50_b |
| astropy__astropy-7606 | correct / correct | 646 | 592 | main_50_b |
| django__django-11820 | correct / correct | 2195 | 1813 | main_50_b |
| django__django-13297 | incorrect / incorrect | 1770 | 4454 | main_50_b |
| matplotlib__matplotlib-25122 | correct / correct | 753 | 1336 | main_50_a |
| pydata__xarray-4695 | correct / correct | 567 | 576 | main_50_a |
| pydata__xarray-6599 | correct / correct | 471 | 1728 | main_50_a |
| pydata__xarray-6744 | correct / correct | 1698 | 1222 | main_50_a |
| pytest-dev__pytest-7432 | correct / correct | 1826 | 490 | main_50_a |

Full SHA-256 values for every mismatch:

- **astropy__astropy-13977**: frozen `8c9bef88b67b264fb5bcdf2ff232064826900e5cf694285c7bdaeba469614e34` (1096 bytes); archived applied `8d1b3c17724abd743b342a604a31f538d80a4aaab0bb70865c43bd65f0f6d128` (4475 bytes). Original label metadata (`incorrect`) claims the frozen hash; linked archived report `/home/sankalp/projects/cis695-agent-reliability/logs/run_evaluation/main_50_b__astropy__astropy-13977/deepseek_deepseek-v4-flash/astropy__astropy-13977/report.json` grades the applied hash as `incorrect`.
- **astropy__astropy-7606**: frozen `af932a2c4ac4e1e50b2c1a79751e8fdd1b3d99a002e315d079c4e6ae4130eeea` (646 bytes); archived applied `c5493fe1e50bf8859e2dcec8aa28cf941d35e6a4e640770ebba3476e2c5a189e` (592 bytes). Original label metadata (`correct`) claims the frozen hash; linked archived report `/home/sankalp/projects/cis695-agent-reliability/logs/run_evaluation/main_50_b__astropy__astropy-7606/deepseek_deepseek-v4-flash/astropy__astropy-7606/report.json` grades the applied hash as `correct`.
- **django__django-11820**: frozen `7c3a9c8a78aff5064d0a1880b61f5ded53b7d1cb58251c7f9f677a81765d51d8` (2195 bytes); archived applied `b72ab06a2a0f8252d399bd128ddd10838cbd1314d3fe027031c2e0feff5b46ed` (1813 bytes). Original label metadata (`correct`) claims the frozen hash; linked archived report `/home/sankalp/projects/cis695-agent-reliability/logs/run_evaluation/main_50_b__django__django-11820/deepseek_deepseek-v4-flash/django__django-11820/report.json` grades the applied hash as `correct`.
- **django__django-13297**: frozen `69181c9a98281a325159813f1b8a53aa13bf3dd5bb8bd375894c1d344a9cdc85` (1770 bytes); archived applied `25022237ebec1e6eb372fa015fabd303550f8ab77d773d81e0e3fc050397fc68` (4454 bytes). Original label metadata (`incorrect`) claims the frozen hash; linked archived report `/home/sankalp/projects/cis695-agent-reliability/logs/run_evaluation/main_50_b__django__django-13297/deepseek_deepseek-v4-flash/django__django-13297/report.json` grades the applied hash as `incorrect`.
- **matplotlib__matplotlib-25122**: frozen `d90258463035a063dbabb8e861cfcd2f9ddd84f94bff5bd81fd920e8cc34cf28` (753 bytes); archived applied `3761f5ef5beb6f0c852c030d29062c3e2e3bcd3548cc40447eab9a8fb90a3e67` (1336 bytes). Original label metadata (`correct`) claims the frozen hash; linked archived report `/home/sankalp/projects/cis695-agent-reliability/logs/run_evaluation/main_50_a__matplotlib__matplotlib-25122/deepseek_deepseek-v4-flash/matplotlib__matplotlib-25122/report.json` grades the applied hash as `correct`.
- **pydata__xarray-4695**: frozen `e3c08b25fd67e1749afb35cafa794688d3c5b6e6699bfcad15f3708c895a4403` (567 bytes); archived applied `2ca6510c074a7af20957c8604f91653f016d5a0b009607f9df995237bb586693` (576 bytes). Original label metadata (`correct`) claims the frozen hash; linked archived report `/home/sankalp/projects/cis695-agent-reliability/logs/run_evaluation/main_50_a__pydata__xarray-4695/deepseek_deepseek-v4-flash/pydata__xarray-4695/report.json` grades the applied hash as `correct`.
- **pydata__xarray-6599**: frozen `810aa2a801cb4c1c9be5c123ac651f5b9efa1c9e33128f9399684f6e551c23d1` (471 bytes); archived applied `268b4250433097481c3af806cf5b61bfeecd0b3e62469d3bf2b1e3860f14c1cd` (1728 bytes). Original label metadata (`correct`) claims the frozen hash; linked archived report `/home/sankalp/projects/cis695-agent-reliability/logs/run_evaluation/main_50_a__pydata__xarray-6599/deepseek_deepseek-v4-flash/pydata__xarray-6599/report.json` grades the applied hash as `correct`.
- **pydata__xarray-6744**: frozen `c81fd169410f0b73aaab09fbb63fa8bd5545d41e82b203e27e76500527411096` (1698 bytes); archived applied `d850ba23cffb478e4cdcf27ad05f9446df4b0ff86c2d709b870973b41bba394c` (1222 bytes). Original label metadata (`correct`) claims the frozen hash; linked archived report `/home/sankalp/projects/cis695-agent-reliability/logs/run_evaluation/main_50_a__pydata__xarray-6744/deepseek_deepseek-v4-flash/pydata__xarray-6744/report.json` grades the applied hash as `correct`.
- **pytest-dev__pytest-7432**: frozen `85c2adb175ee8f9d7aefa1586f26ec2848b1e8d4db3c1ea6dd3aead284efe448` (1826 bytes); archived applied `d8341276a9cb851c05850e18af79934229ab01d0531fe3df6bbc0f01f8f40b1c` (490 bytes). Original label metadata (`correct`) claims the frozen hash; linked archived report `/home/sankalp/projects/cis695-agent-reliability/logs/run_evaluation/main_50_a__pytest-dev__pytest-7432/deepseek_deepseek-v4-flash/pytest-dev__pytest-7432/report.json` grades the applied hash as `correct`.

SUPPORTED means binding matches and the report/log support the original grade: all expected references pass for a correct label; an unmet F2P (including absent F2P) or a genuine FAILED/ERROR supports an incorrect label. SKIP_ONLY means an incorrect grade has no unmet F2P or genuine P2P assertion/error, only skipped or absent P2P tests. BINDING_MISMATCH takes precedence over outcome basis. Missing report, raw log, oracle record or applied-patch evidence would be NO_GRADER_RECORD; none is missing.

Official parsing counts PASSED and XFAIL as passing. The five Pylint skip results are bound to native file/line summaries through the previously checked patched-source spans; the parser alone omits their IDs. SKIPPED and absent stay distinct in this audit. Tests outside the F2P/P2P references do not support a task label merely because they failed.

## Nonpassing references, task by task

The following table lists **every task**, including tasks with empty lists. The CSV and JSON preserve each test ID, native status, report success/failure bucket, and any source-bound skip proof. `none` means an empty list, not a missing record.

| Task | Original | Classification | F2P not passing | P2P FAILED/ERROR | P2P SKIPPED | P2P absent |
|---|---|---|---|---|---|---|
| astropy__astropy-13977 | incorrect | BINDING_MISMATCH | `astropy/units/tests/test_quantity_ufuncs.py::TestUfuncReturnsNotImplemented::TestBinaryUfuncs::test_full[empty-duck_quantity0-quantity0-add]` (FAILED)<br>`astropy/units/tests/test_quantity_ufuncs.py::TestUfuncReturnsNotImplemented::TestBinaryUfuncs::test_full[empty-duck_quantity0-quantity0-multiply]` (FAILED)<br>`astropy/units/tests/test_quantity_ufuncs.py::TestUfuncReturnsNotImplemented::TestBinaryUfuncs::test_full[empty-duck_quantity0-quantity1-add]` (FAILED)<br>`astropy/units/tests/test_quantity_ufuncs.py::TestUfuncReturnsNotImplemented::TestBinaryUfuncs::test_full[empty-duck_quantity0-quantity1-multiply]` (FAILED)<br>`astropy/units/tests/test_quantity_ufuncs.py::TestUfuncReturnsNotImplemented::TestBinaryUfuncs::test_full[empty-duck_quantity1-quantity0-add]` (FAILED)<br>`astropy/units/tests/test_quantity_ufuncs.py::TestUfuncReturnsNotImplemented::TestBinaryUfuncs::test_full[empty-duck_quantity1-quantity0-multiply]` (FAILED)<br>`astropy/units/tests/test_quantity_ufuncs.py::TestUfuncReturnsNotImplemented::TestBinaryUfuncs::test_full[empty-duck_quantity1-quantity1-add]` (FAILED)<br>`astropy/units/tests/test_quantity_ufuncs.py::TestUfuncReturnsNotImplemented::TestBinaryUfuncs::test_full[empty-duck_quantity1-quantity1-multiply]` (FAILED) | none | none | none |
| astropy__astropy-14365 | correct | SUPPORTED | none | none | none | none |
| astropy__astropy-14508 | correct | SUPPORTED | none | none | none | none |
| astropy__astropy-7606 | correct | BINDING_MISMATCH | none | none | none | none |
| django__django-10973 | correct | SUPPORTED | none | none | none | none |
| django__django-11095 | correct | SUPPORTED | none | none | none | none |
| django__django-11299 | correct | SUPPORTED | none | none | none | none |
| django__django-11820 | correct | BINDING_MISMATCH | none | none | none | none |
| django__django-12209 | correct | SUPPORTED | none | none | none | none |
| django__django-12965 | correct | SUPPORTED | none | none | none | none |
| django__django-13023 | correct | SUPPORTED | none | none | none | none |
| django__django-13033 | correct | SUPPORTED | none | none | none | none |
| django__django-13158 | correct | SUPPORTED | none | none | none | none |
| django__django-13212 | incorrect | SUPPORTED | `test_value_placeholder_with_decimal_field (forms_tests.tests.test_validators.ValidatorCustomMessageTests)` (ABSENT)<br>`test_value_placeholder_with_file_field (forms_tests.tests.test_validators.ValidatorCustomMessageTests)` (ABSENT) | none | none | none |
| django__django-13297 | incorrect | BINDING_MISMATCH | none | `test_template_params_warning (generic_views.test_base.DeprecationTests)` (FAILED) | none | none |
| django__django-13569 | correct | SUPPORTED | none | none | none | none |
| django__django-13786 | correct | SUPPORTED | none | none | none | none |
| django__django-13807 | correct | SUPPORTED | none | none | none | none |
| django__django-13820 | correct | SUPPORTED | none | none | none | none |
| django__django-14140 | correct | SUPPORTED | none | none | none | none |
| django__django-14631 | correct | SUPPORTED | none | none | none | none |
| django__django-15037 | correct | SUPPORTED | none | none | none | none |
| django__django-15103 | correct | SUPPORTED | none | none | none | none |
| django__django-15278 | correct | SUPPORTED | none | none | none | none |
| django__django-15375 | correct | SUPPORTED | none | none | none | none |
| django__django-15499 | correct | SUPPORTED | none | none | none | none |
| django__django-15572 | correct | SUPPORTED | none | none | none | none |
| django__django-15930 | correct | SUPPORTED | none | none | none | none |
| django__django-16082 | correct | SUPPORTED | none | none | none | none |
| django__django-16136 | correct | SUPPORTED | none | none | none | none |
| django__django-16255 | correct | SUPPORTED | none | none | none | none |
| django__django-16315 | correct | SUPPORTED | none | none | none | none |
| django__django-16612 | correct | SUPPORTED | none | none | none | none |
| django__django-16631 | incorrect | SUPPORTED | `test_get_user_fallback_secret (auth_tests.test_basic.TestGetUser.test_get_user_fallback_secret)` (FAILED) | none | none | none |
| django__django-16667 | incorrect | SUPPORTED | `test_value_from_datadict (forms_tests.widget_tests.test_selectdatewidget.SelectDateWidgetTest.test_value_from_datadict)` (ABSENT) | none | none | none |
| matplotlib__matplotlib-14623 | correct | SUPPORTED | none | none | none | none |
| matplotlib__matplotlib-20488 | correct | SUPPORTED | none | none | none | none |
| matplotlib__matplotlib-20676 | incorrect | SUPPORTED | `lib/matplotlib/tests/test_widgets.py::test_span_selector_bound[horizontal]` (FAILED)<br>`lib/matplotlib/tests/test_widgets.py::test_span_selector_bound[vertical]` (FAILED) | none | none | none |
| matplotlib__matplotlib-22719 | correct | SUPPORTED | none | none | none | none |
| matplotlib__matplotlib-22871 | correct | SUPPORTED | none | none | none | none |
| matplotlib__matplotlib-23299 | incorrect | SUPPORTED | `lib/matplotlib/tests/test_rcparams.py::test_no_backend_reset_rccontext` (FAILED) | none | none | none |
| matplotlib__matplotlib-23476 | incorrect | SUPPORTED | `lib/matplotlib/tests/test_figure.py::test_unpickle_with_device_pixel_ratio` (FAILED) | none | none | none |
| matplotlib__matplotlib-24026 | correct | SUPPORTED | none | none | none | none |
| matplotlib__matplotlib-24177 | correct | SUPPORTED | none | none | none | none |
| matplotlib__matplotlib-24637 | correct | SUPPORTED | none | none | none | none |
| matplotlib__matplotlib-24970 | correct | SUPPORTED | none | none | none | none |
| matplotlib__matplotlib-25122 | correct | BINDING_MISMATCH | none | none | none | none |
| matplotlib__matplotlib-25287 | correct | SUPPORTED | none | none | none | none |
| matplotlib__matplotlib-25479 | incorrect | SUPPORTED | `lib/matplotlib/tests/test_colors.py::test_colormap_equals` (FAILED)<br>`lib/matplotlib/tests/test_colors.py::test_set_cmap_mismatched_name` (FAILED) | `lib/matplotlib/tests/test_colors.py::test_register_cmap` (FAILED) | none | none |
| matplotlib__matplotlib-26291 | correct | SUPPORTED | none | none | none | none |
| mwaskom__seaborn-3069 | incorrect | SUPPORTED | `tests/_core/test_plot.py::TestScaling::test_nominal_y_axis_tweaks` (FAILED) | none | none | none |
| pallets__flask-5014 | correct | SUPPORTED | none | none | none | none |
| pydata__xarray-4629 | correct | SUPPORTED | none | none | none | none |
| pydata__xarray-4695 | correct | BINDING_MISMATCH | none | none | none | none |
| pydata__xarray-4966 | correct | SUPPORTED | none | none | none | none |
| pydata__xarray-6599 | correct | BINDING_MISMATCH | none | none | none | none |
| pydata__xarray-6744 | correct | BINDING_MISMATCH | none | none | none | none |
| pylint-dev__pylint-4661 | incorrect | SUPPORTED | `tests/lint/unittest_lint.py::test_pylint_home` (ABSENT) | none | none | none |
| pylint-dev__pylint-4970 | correct | SUPPORTED | none | none | none | none |
| pylint-dev__pylint-6528 | incorrect | SKIP_ONLY | none | none | `tests/lint/unittest_lint.py::test_custom_should_analyze_file` (SKIPPED)<br>`tests/lint/unittest_lint.py::test_multiprocessing[1]` (SKIPPED)<br>`tests/lint/unittest_lint.py::test_multiprocessing[2]` (SKIPPED)<br>`tests/test_self.py::TestRunTC::test_jobs_score` (SKIPPED) | none |
| pylint-dev__pylint-6903 | correct | SUPPORTED | none | none | none | none |
| pylint-dev__pylint-7277 | incorrect | SKIP_ONLY | none | none | `tests/test_self.py::TestRunTC::test_jobs_score` (SKIPPED) | none |
| pytest-dev__pytest-10051 | correct | SUPPORTED | none | none | none | none |
| pytest-dev__pytest-5787 | correct | SUPPORTED | none | none | none | none |
| pytest-dev__pytest-5809 | correct | SUPPORTED | none | none | none | none |
| pytest-dev__pytest-6202 | correct | SUPPORTED | none | none | none | none |
| pytest-dev__pytest-7236 | correct | SUPPORTED | none | none | none | none |
| pytest-dev__pytest-7432 | correct | BINDING_MISMATCH | none | none | none | none |
| pytest-dev__pytest-7521 | correct | SUPPORTED | none | none | none | none |
| scikit-learn__scikit-learn-10908 | correct | SUPPORTED | none | none | none | none |
| scikit-learn__scikit-learn-12585 | correct | SUPPORTED | none | none | none | none |
| scikit-learn__scikit-learn-14141 | correct | SUPPORTED | none | none | none | none |
| scikit-learn__scikit-learn-14629 | correct | SUPPORTED | none | none | none | none |
| scikit-learn__scikit-learn-14894 | correct | SUPPORTED | none | none | none | none |
| sphinx-doc__sphinx-10323 | correct | SUPPORTED | none | none | none | none |
| sphinx-doc__sphinx-10435 | correct | SUPPORTED | none | none | none | none |
| sphinx-doc__sphinx-10466 | correct | SUPPORTED | none | none | none | none |
| sphinx-doc__sphinx-7910 | correct | SUPPORTED | none | none | none | none |
| sympy__sympy-13480 | correct | SUPPORTED | none | none | none | none |
| sympy__sympy-14711 | correct | SUPPORTED | none | none | none | none |
| sympy__sympy-17318 | incorrect | SUPPORTED | `test_issue_12420` (FAILED) | none | none | none |
| sympy__sympy-19783 | correct | SUPPORTED | none | none | none | none |
| sympy__sympy-24562 | correct | SUPPORTED | none | none | none | none |

## Fresh full-task audited grades

Official SWE-bench **5.0.2** `make_test_spec` and `run_instance` were used, with the full dataset eval script, official test_patch, and every F2P/P2P reference. The installed harness modules match distribution RECORD. Fresh containers use the same immutable image identities as the sealed run, preventing mutable-tag drift; the default resource settings and entire test command are otherwise unchanged. The two SKIP_ONLY tasks also receive a fresh grade with only CPU shares set to 2048 before container start (equivalent to `--cpu-shares 2048`). No executor code is involved or edited.

Each invocation has a 1,800-second safety timeout. A timeout, application failure or missing usable report is recorded as no audited grade, not silently classified incorrect. Set B uses the **default-environment** audited grade. The extra CPU-2048 projection is a separate sensitivity. Raw logs stay under ignored `runs/phase4_label_audit/`; report JSON records their hashes, full reference counts, exact image IDs and resource settings.

| Task | Basis | Profile | F2P / P2P references | Audited grade | F2P not met | P2P not met |
|---|---|---|---|---|---:|---:|
| astropy__astropy-13977 | BINDING_MISMATCH | default | 20 / 322 | correct | 0 | 0 |
| astropy__astropy-7606 | BINDING_MISMATCH | default | 1 / 240 | correct | 0 | 0 |
| django__django-11820 | BINDING_MISMATCH | default | 2 / 61 | correct | 0 | 0 |
| django__django-13297 | BINDING_MISMATCH | default | 1 / 52 | correct | 0 | 0 |
| matplotlib__matplotlib-25122 | BINDING_MISMATCH | default | 12 / 2476 | correct | 0 | 0 |
| pydata__xarray-4695 | BINDING_MISMATCH | default | 1 / 875 | correct | 0 | 0 |
| pydata__xarray-6599 | BINDING_MISMATCH | default | 1 / 264 | incorrect | 1 | 1 |
| pydata__xarray-6744 | BINDING_MISMATCH | default | 3 / 1815 | correct | 0 | 0 |
| pylint-dev__pylint-6528 | SKIP_ONLY | default | 4 / 171 | incorrect | 0 | 4 |
| pylint-dev__pylint-6528 | SKIP_ONLY | cpu2048 | 4 / 171 | correct | 0 | 0 |
| pylint-dev__pylint-7277 | SKIP_ONLY | default | 1 / 122 | incorrect | 0 | 1 |
| pylint-dev__pylint-7277 | SKIP_ONLY | cpu2048 | 1 / 122 | correct | 0 | 0 |
| pytest-dev__pytest-7432 | BINDING_MISMATCH | default | 1 / 77 | correct | 0 | 0 |

FAILED/ERROR parser entries outside official reference lists (these can include expected nested pytester child results, not top-level task failures; they are not used to invent a different task grade):

- pydata__xarray-4695 / default: `xarray/tests/test_dataarray.py::TestDataArray::test_from_series_multiindex` (FAILED).
- pylint-dev__pylint-6528 / default: `tests/test_self.py::TestCallbackOptions::test_generate_toml_config` (FAILED), `tests/test_self.py::TestCallbackOptions::test_generate_toml_config_disable_symbolic_names` (FAILED).
- pylint-dev__pylint-6528 / cpu2048: `tests/test_self.py::TestCallbackOptions::test_generate_toml_config` (FAILED), `tests/test_self.py::TestCallbackOptions::test_generate_toml_config_disable_symbolic_names` (FAILED).
- pylint-dev__pylint-7277 / default: `tests/test_self.py::TestCallbackOptions::test_generate_toml_config` (FAILED), `tests/test_self.py::TestCallbackOptions::test_generate_toml_config_disable_symbolic_names` (FAILED).
- pylint-dev__pylint-7277 / cpu2048: `tests/test_self.py::TestCallbackOptions::test_generate_toml_config` (FAILED), `tests/test_self.py::TestCallbackOptions::test_generate_toml_config_disable_symbolic_names` (FAILED).
- pytest-dev__pytest-7432 / default: `test_xfail_run_anyway.py::test_func` (FAILED), `test_xfail_imperative_in_setup_function.py::test_this` (FAILED), `test_xfail_raises.py::test_raises` (FAILED), `test_reportchars.py::test_1` (FAILED), `test_simple.py::test_foo` (ERROR), `test_reportchars_all.py::test_5` (ERROR), `test_reportchars_all.py::test_1` (FAILED), `test_errors_in_xfail_skip_expressions.py::test_nameerror` (ERROR), `test_errors_in_xfail_skip_expressions.py::test_syntax` (ERROR), `test_module_level_skip_error.py` (ERROR), `test_invalid_skip_keyword_parameter.py` (ERROR), `test_summary_list_after_errors.py::test_fail` (FAILED).

## Label sets and changed assignments

A preserves the original labels. B preserves original labels for SUPPORTED tasks, uses the fresh default audited grade elsewhere, and excludes tasks with neither. These are analytical label-set mappings; the source labels are never written.

| Label set | Correct | Incorrect | Excluded |
|---|---:|---:|---:|
| A original | 69 | 14 | 0 |
| B audited default | 70 | 13 | 0 |
| B CPU-2048 sensitivity | 72 | 11 | 0 |

| Task whose assignment differs | A | B | Original classification |
|---|---|---|---|
| astropy__astropy-13977 | incorrect | correct | BINDING_MISMATCH |
| django__django-13297 | incorrect | correct | BINDING_MISMATCH |
| pydata__xarray-6599 | correct | incorrect | BINDING_MISMATCH |

## §3a — verdict × label, A and B side by side

Policy verdicts are read unchanged from the hash-pinned sealed result. INVALID_ID excluded is primary; INVALID_ID missing is sensitivity. Original-A matrices and every proportion/interval reproduce the previous post-hoc report exactly.

| Policy | Verdict | A correct | A incorrect | B correct | B incorrect |
|---|---|---:|---:|---:|---:|
| C_invalid_excluded | PASS | 43 | 9 | 42 | 10 |
| C_invalid_excluded | FAIL | 5 | 1 | 5 | 1 |
| C_invalid_excluded | REGRESSION_ERROR | 1 | 0 | 1 | 0 |
| C_invalid_excluded | INCOMPLETE | 15 | 4 | 17 | 2 |
| C_invalid_excluded | NOT_AVAILABLE | 5 | 0 | 5 | 0 |
| C_invalid_missing | PASS | 33 | 9 | 32 | 10 |
| C_invalid_missing | FAIL | 5 | 1 | 5 | 1 |
| C_invalid_missing | REGRESSION_ERROR | 1 | 0 | 1 | 0 |
| C_invalid_missing | INCOMPLETE | 25 | 4 | 27 | 2 |
| C_invalid_missing | NOT_AVAILABLE | 5 | 0 | 5 | 0 |
| S_invalid_excluded | PASS | 14 | 6 | 14 | 6 |
| S_invalid_excluded | FAIL | 5 | 1 | 5 | 1 |
| S_invalid_excluded | REGRESSION_ERROR | 1 | 0 | 1 | 0 |
| S_invalid_excluded | INCOMPLETE | 44 | 7 | 45 | 6 |
| S_invalid_excluded | NOT_AVAILABLE | 5 | 0 | 5 | 0 |
| S_invalid_missing | PASS | 13 | 6 | 13 | 6 |
| S_invalid_missing | FAIL | 5 | 1 | 5 | 1 |
| S_invalid_missing | REGRESSION_ERROR | 1 | 0 | 1 | 0 |
| S_invalid_missing | INCOMPLETE | 45 | 7 | 46 | 6 |
| S_invalid_missing | NOT_AVAILABLE | 5 | 0 | 5 | 0 |

## §3b — detection, false alarms and missed PASS

All intervals are exact two-sided **95% Clopper-Pearson** intervals. Primary positive = FAIL alone; secondary positive = FAIL or REGRESSION_ERROR. Conditional denominators include PASS+FAIL for primary and PASS+FAIL+REGRESSION_ERROR for secondary. INCOMPLETE and NOT_AVAILABLE stay in the all-labelled denominators but not the conditional denominators. Each set uses its own correct/incorrect totals; undefined 0-denominator rates are explicit. These intervals describe the observed proportions and do not turn audited harness grades into semantic ground truth.

| Policy | Positive rule | Proportion | A original [95% CI] | B audited default [95% CI] |
|---|---|---|---|---|
| C_invalid_excluded | primary_FAIL_only | Detection / all incorrect | 1/14 = 7.14% [0.18%, 33.87%] | 1/13 = 7.69% [0.19%, 36.03%] |
| C_invalid_excluded | primary_FAIL_only | Detection / verdicted incorrect | 1/10 = 10.00% [0.25%, 44.50%] | 1/11 = 9.09% [0.23%, 41.28%] |
| C_invalid_excluded | primary_FAIL_only | False alarms / all correct | 5/69 = 7.25% [2.39%, 16.11%] | 5/70 = 7.14% [2.36%, 15.89%] |
| C_invalid_excluded | primary_FAIL_only | False alarms / verdicted correct | 5/48 = 10.42% [3.47%, 22.66%] | 5/47 = 10.64% [3.55%, 23.10%] |
| C_invalid_excluded | primary_FAIL_only | Missed PASS / all incorrect | 9/14 = 64.29% [35.14%, 87.24%] | 10/13 = 76.92% [46.19%, 94.96%] |
| C_invalid_excluded | primary_FAIL_only | Missed PASS / verdicted incorrect | 9/10 = 90.00% [55.50%, 99.75%] | 10/11 = 90.91% [58.72%, 99.77%] |
| C_invalid_excluded | secondary_FAIL_plus_REGRESSION_ERROR | Detection / all incorrect | 1/14 = 7.14% [0.18%, 33.87%] | 1/13 = 7.69% [0.19%, 36.03%] |
| C_invalid_excluded | secondary_FAIL_plus_REGRESSION_ERROR | Detection / verdicted incorrect | 1/10 = 10.00% [0.25%, 44.50%] | 1/11 = 9.09% [0.23%, 41.28%] |
| C_invalid_excluded | secondary_FAIL_plus_REGRESSION_ERROR | False alarms / all correct | 6/69 = 8.70% [3.26%, 17.97%] | 6/70 = 8.57% [3.21%, 17.73%] |
| C_invalid_excluded | secondary_FAIL_plus_REGRESSION_ERROR | False alarms / verdicted correct | 6/49 = 12.24% [4.63%, 24.77%] | 6/48 = 12.50% [4.73%, 25.25%] |
| C_invalid_excluded | secondary_FAIL_plus_REGRESSION_ERROR | Missed PASS / all incorrect | 9/14 = 64.29% [35.14%, 87.24%] | 10/13 = 76.92% [46.19%, 94.96%] |
| C_invalid_excluded | secondary_FAIL_plus_REGRESSION_ERROR | Missed PASS / verdicted incorrect | 9/10 = 90.00% [55.50%, 99.75%] | 10/11 = 90.91% [58.72%, 99.77%] |
| C_invalid_missing | primary_FAIL_only | Detection / all incorrect | 1/14 = 7.14% [0.18%, 33.87%] | 1/13 = 7.69% [0.19%, 36.03%] |
| C_invalid_missing | primary_FAIL_only | Detection / verdicted incorrect | 1/10 = 10.00% [0.25%, 44.50%] | 1/11 = 9.09% [0.23%, 41.28%] |
| C_invalid_missing | primary_FAIL_only | False alarms / all correct | 5/69 = 7.25% [2.39%, 16.11%] | 5/70 = 7.14% [2.36%, 15.89%] |
| C_invalid_missing | primary_FAIL_only | False alarms / verdicted correct | 5/38 = 13.16% [4.41%, 28.09%] | 5/37 = 13.51% [4.54%, 28.77%] |
| C_invalid_missing | primary_FAIL_only | Missed PASS / all incorrect | 9/14 = 64.29% [35.14%, 87.24%] | 10/13 = 76.92% [46.19%, 94.96%] |
| C_invalid_missing | primary_FAIL_only | Missed PASS / verdicted incorrect | 9/10 = 90.00% [55.50%, 99.75%] | 10/11 = 90.91% [58.72%, 99.77%] |
| C_invalid_missing | secondary_FAIL_plus_REGRESSION_ERROR | Detection / all incorrect | 1/14 = 7.14% [0.18%, 33.87%] | 1/13 = 7.69% [0.19%, 36.03%] |
| C_invalid_missing | secondary_FAIL_plus_REGRESSION_ERROR | Detection / verdicted incorrect | 1/10 = 10.00% [0.25%, 44.50%] | 1/11 = 9.09% [0.23%, 41.28%] |
| C_invalid_missing | secondary_FAIL_plus_REGRESSION_ERROR | False alarms / all correct | 6/69 = 8.70% [3.26%, 17.97%] | 6/70 = 8.57% [3.21%, 17.73%] |
| C_invalid_missing | secondary_FAIL_plus_REGRESSION_ERROR | False alarms / verdicted correct | 6/39 = 15.38% [5.86%, 30.53%] | 6/38 = 15.79% [6.02%, 31.25%] |
| C_invalid_missing | secondary_FAIL_plus_REGRESSION_ERROR | Missed PASS / all incorrect | 9/14 = 64.29% [35.14%, 87.24%] | 10/13 = 76.92% [46.19%, 94.96%] |
| C_invalid_missing | secondary_FAIL_plus_REGRESSION_ERROR | Missed PASS / verdicted incorrect | 9/10 = 90.00% [55.50%, 99.75%] | 10/11 = 90.91% [58.72%, 99.77%] |
| S_invalid_excluded | primary_FAIL_only | Detection / all incorrect | 1/14 = 7.14% [0.18%, 33.87%] | 1/13 = 7.69% [0.19%, 36.03%] |
| S_invalid_excluded | primary_FAIL_only | Detection / verdicted incorrect | 1/7 = 14.29% [0.36%, 57.87%] | 1/7 = 14.29% [0.36%, 57.87%] |
| S_invalid_excluded | primary_FAIL_only | False alarms / all correct | 5/69 = 7.25% [2.39%, 16.11%] | 5/70 = 7.14% [2.36%, 15.89%] |
| S_invalid_excluded | primary_FAIL_only | False alarms / verdicted correct | 5/19 = 26.32% [9.15%, 51.20%] | 5/19 = 26.32% [9.15%, 51.20%] |
| S_invalid_excluded | primary_FAIL_only | Missed PASS / all incorrect | 6/14 = 42.86% [17.66%, 71.14%] | 6/13 = 46.15% [19.22%, 74.87%] |
| S_invalid_excluded | primary_FAIL_only | Missed PASS / verdicted incorrect | 6/7 = 85.71% [42.13%, 99.64%] | 6/7 = 85.71% [42.13%, 99.64%] |
| S_invalid_excluded | secondary_FAIL_plus_REGRESSION_ERROR | Detection / all incorrect | 1/14 = 7.14% [0.18%, 33.87%] | 1/13 = 7.69% [0.19%, 36.03%] |
| S_invalid_excluded | secondary_FAIL_plus_REGRESSION_ERROR | Detection / verdicted incorrect | 1/7 = 14.29% [0.36%, 57.87%] | 1/7 = 14.29% [0.36%, 57.87%] |
| S_invalid_excluded | secondary_FAIL_plus_REGRESSION_ERROR | False alarms / all correct | 6/69 = 8.70% [3.26%, 17.97%] | 6/70 = 8.57% [3.21%, 17.73%] |
| S_invalid_excluded | secondary_FAIL_plus_REGRESSION_ERROR | False alarms / verdicted correct | 6/20 = 30.00% [11.89%, 54.28%] | 6/20 = 30.00% [11.89%, 54.28%] |
| S_invalid_excluded | secondary_FAIL_plus_REGRESSION_ERROR | Missed PASS / all incorrect | 6/14 = 42.86% [17.66%, 71.14%] | 6/13 = 46.15% [19.22%, 74.87%] |
| S_invalid_excluded | secondary_FAIL_plus_REGRESSION_ERROR | Missed PASS / verdicted incorrect | 6/7 = 85.71% [42.13%, 99.64%] | 6/7 = 85.71% [42.13%, 99.64%] |
| S_invalid_missing | primary_FAIL_only | Detection / all incorrect | 1/14 = 7.14% [0.18%, 33.87%] | 1/13 = 7.69% [0.19%, 36.03%] |
| S_invalid_missing | primary_FAIL_only | Detection / verdicted incorrect | 1/7 = 14.29% [0.36%, 57.87%] | 1/7 = 14.29% [0.36%, 57.87%] |
| S_invalid_missing | primary_FAIL_only | False alarms / all correct | 5/69 = 7.25% [2.39%, 16.11%] | 5/70 = 7.14% [2.36%, 15.89%] |
| S_invalid_missing | primary_FAIL_only | False alarms / verdicted correct | 5/18 = 27.78% [9.69%, 53.48%] | 5/18 = 27.78% [9.69%, 53.48%] |
| S_invalid_missing | primary_FAIL_only | Missed PASS / all incorrect | 6/14 = 42.86% [17.66%, 71.14%] | 6/13 = 46.15% [19.22%, 74.87%] |
| S_invalid_missing | primary_FAIL_only | Missed PASS / verdicted incorrect | 6/7 = 85.71% [42.13%, 99.64%] | 6/7 = 85.71% [42.13%, 99.64%] |
| S_invalid_missing | secondary_FAIL_plus_REGRESSION_ERROR | Detection / all incorrect | 1/14 = 7.14% [0.18%, 33.87%] | 1/13 = 7.69% [0.19%, 36.03%] |
| S_invalid_missing | secondary_FAIL_plus_REGRESSION_ERROR | Detection / verdicted incorrect | 1/7 = 14.29% [0.36%, 57.87%] | 1/7 = 14.29% [0.36%, 57.87%] |
| S_invalid_missing | secondary_FAIL_plus_REGRESSION_ERROR | False alarms / all correct | 6/69 = 8.70% [3.26%, 17.97%] | 6/70 = 8.57% [3.21%, 17.73%] |
| S_invalid_missing | secondary_FAIL_plus_REGRESSION_ERROR | False alarms / verdicted correct | 6/19 = 31.58% [12.58%, 56.55%] | 6/19 = 31.58% [12.58%, 56.55%] |
| S_invalid_missing | secondary_FAIL_plus_REGRESSION_ERROR | Missed PASS / all incorrect | 6/14 = 42.86% [17.66%, 71.14%] | 6/13 = 46.15% [19.22%, 74.87%] |
| S_invalid_missing | secondary_FAIL_plus_REGRESSION_ERROR | Missed PASS / verdicted incorrect | 6/7 = 85.71% [42.13%, 99.64%] | 6/7 = 85.71% [42.13%, 99.64%] |

## CPU-2048 resource sensitivity (not primary B)

| Policy | Verdict | Correct | Incorrect |
|---|---|---:|---:|
| C_invalid_excluded | PASS | 44 | 8 |
| C_invalid_excluded | FAIL | 5 | 1 |
| C_invalid_excluded | REGRESSION_ERROR | 1 | 0 |
| C_invalid_excluded | INCOMPLETE | 17 | 2 |
| C_invalid_excluded | NOT_AVAILABLE | 5 | 0 |
| C_invalid_missing | PASS | 34 | 8 |
| C_invalid_missing | FAIL | 5 | 1 |
| C_invalid_missing | REGRESSION_ERROR | 1 | 0 |
| C_invalid_missing | INCOMPLETE | 27 | 2 |
| C_invalid_missing | NOT_AVAILABLE | 5 | 0 |
| S_invalid_excluded | PASS | 16 | 4 |
| S_invalid_excluded | FAIL | 5 | 1 |
| S_invalid_excluded | REGRESSION_ERROR | 1 | 0 |
| S_invalid_excluded | INCOMPLETE | 45 | 6 |
| S_invalid_excluded | NOT_AVAILABLE | 5 | 0 |
| S_invalid_missing | PASS | 15 | 4 |
| S_invalid_missing | FAIL | 5 | 1 |
| S_invalid_missing | REGRESSION_ERROR | 1 | 0 |
| S_invalid_missing | INCOMPLETE | 46 | 6 |
| S_invalid_missing | NOT_AVAILABLE | 5 | 0 |

The JSON and metrics.csv provide every CPU-sensitivity proportion with the same exact interval and denominator rules. These extra rows expose resource-dependent audited grades without choosing a more favorable primary grade.

## Provenance, reproduction and limits

- Source labels: `/home/sankalp/projects/cis695-v2-scg-ubuntu-publication/reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/correctness_sidecar.json`; SHA-256 `cd61a6e726a32e159db87a5040be5ea49c5c67e147faac424bf9a756d4e0c990`.
- Cached Verified dataset revision: `78f471bf655a3137b2e8a75af1501690ec009ec3`; Parquet SHA-256 `030cfd7f2a704c4c0226e7f104c725a3b41230b1d3517f9c915ad7ea5be3fa25`. Only explicit grading/source columns are loaded; gold solution patches are not needed.
- All 83 archived reports, oracle records, native logs, applied patch files and frozen candidates are hash-inventoried in analysis.json. The four rerun aliases are taken from the existing pinned binding records, not guessed from directory names.
- `env -u PYTHONPATH .venv/bin/python reports/next_phases/phase4_posthoc/label_audit/audit.py` regenerates reports without running tests. `--grade` is the explicit full-task execution mode; completed grades are hash-verified before reuse. `--inventory` only inventories archived evidence.
- The report is generated twice from the same raw grade artifacts and compared byte-for-byte. No rerun of grades is needed to check deterministic analysis.
- A mismatched applied patch invalidates the binding, regardless of whether the original and audited labels happen to agree. A SUPPORTED label can be supported by unmet F2P without an assertion traceback. A successful audited grade establishes the official harness result in the stated environment, not an independent proof of correctness.
- The sealed runtime measurements and all original-A figures remain immutable. Any interpretive effect of changed labels appears only in this separate report.
