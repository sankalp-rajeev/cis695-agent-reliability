# Next steps: stored V2 diagnosis, false positives, and frozen static selectors

[confirmed] Analysis only. Outputs are confined to `reports/next_steps/`. No commits, network, agents, models, Docker, benchmark tests, test collection, or unit tests were run. The only executed programs were standard-library artifact analysis scripts; no repository runtime modules were imported and no graph was rebuilt or modified.

[inferred] Conservative readings: a selected identity does not establish execution; aggregate counts cannot name the affected test. A gold class change cannot diagnose a V2 run that never used gold. NOT_AVAILABLE is a recorded V2 label, not a missing outcome. 'Usable' in Phase 2 means PASS or FAIL, irrespective of incomplete execution. An import closure here follows reverse *syntactic* module imports, and graph distance means at most three reverse call edges. Static retention never establishes a V2 result.

[confirmed] Claim tags: confirmed facts come directly from stored evidence or source; inferred claims are arithmetic, static projections, or interpretations. Unknowns are stated as UNKNOWN and are not promoted into a cause or zero measurement.

## Phase 1 — three V2 PASS misses

[inferred] **All three primary causes are (f) UNKNOWN.** The exact-run V2 snapshots exist, but only selection unions and aggregate histograms survived. No stored per-test base/patched result pair establishes any proposed primary cause. Diagnosis uses only the V2 projection, base archives, code, and file-availability checks. It was written before this analysis program opened any post-hoc inputs; see `phase1_completed_before_posthoc.json`.

| Case | Primary cause | Recorded selected / executed and histogram | Evidence |
|---|---|---|---|
| pylint-dev__pylint-6528 | [inferred] (f) UNKNOWN | [confirmed] 218 / 191; `{"NOT_RUN": 27, "PASS": 189, "PRE_EXISTING_FAIL": 2}` | `reports/failure_analysis/extracted.json:16076`; selection `reports/failure_analysis/extracted.json:16133` |
| pylint-dev__pylint-7277 | [inferred] (f) UNKNOWN | [confirmed] 70 / 57; `{"NOT_RUN": 13, "PASS": 55, "PRE_EXISTING_FAIL": 2}` | `reports/failure_analysis/extracted.json:2848`; selection `reports/failure_analysis/extracted.json:3018` |
| django__django-13297 | [inferred] (f) UNKNOWN | [confirmed] 8155 / 1265; `{"PASS": 1265, "TIMEOUT": 6890}` | `reports/failure_analysis/extracted.json:3438`; selection `reports/failure_analysis/extracted.json:3617` |

[confirmed] `phase1_record_availability.csv` records the absent exact-run `verification_record.full.json`, `verification_record.baseline.json`, run baseline cache, and failure-analysis copied baseline cache for each of these three. Their aggregate records are preserved in `reports/failure_analysis/extracted.json`, not lost entirely.

[inferred] Exactly what is missing for each case: the raw base result IDs/statuses; raw patched result IDs/statuses; final per-test classifications; stdout/result logs for each pass; test-specific timeout/completion evidence; and a pin identifying the executor source revision used in that historical run. The current source can explain mechanisms, but cannot identify which mechanism affected a named test.

| Proposed cause | Evidence and conclusion |
|---|---|
| (a) timed out / never ran, scored as pass | [confirmed] django-13297 has 6,890 TIMEOUTs and 1,265 PASS outcomes; the Pylint cases have 27/13 NOT_RUN. `regression.py:213` preserves NOT_RUN/TIMEOUT and `regression.py:314` emits patch PASS when some outcomes executed and none regressed. [inferred] Partial aggregate PASS is evidenced; no individual timeout was scored PASS. Which test was incomplete is UNKNOWN. |
| (b) already failed at base | [confirmed] Each Pylint histogram has two PRE_EXISTING_FAIL outcomes; django-13297 has none. `regression.py:228` through `:237` implements base/patch comparison. [inferred] Cannot assign either Pylint count to a particular test; (b) is not established. |
| (c) ID mismatch | [confirmed] The current pytest parser requires exact selected IDs (`container.py:359`, especially `:365`); Django maps labels (`container.py:386`). [inferred] A parameter-family accounting defect is evidenced below, but per-run output is absent, so it is not proven as any whole-patch primary cause. |
| (d) gold-changed Django class | [confirmed] The V2 executor toggles candidate base/patched trees (`container.py:286`); the reducer looks up selected IDs (`regression.py:295`). [inferred] A post-hoc gold comparison cannot establish a runtime ID mismatch. No gold data was consulted for diagnosis. |
| (e) OTHER | [inferred] No alternative cause is established by the stored per-case evidence. |
| (f) UNKNOWN | [inferred] Primary for all three; the missing per-pass records above prevent a causal assignment. |

[confirmed] **A source-level ID-accounting defect, separate from the unknown causes:** the snapshot selects unparameterized families. In the base archive for pylint-6528, `testbed/tests/lint/unittest_lint.py:804` decorates `test_multiprocessing` with `@pytest.mark.parametrize("jobs", [1, 2])`; its definition is at line 805. The current `_parse_pytest` (`container.py:365`) discards an emitted `family[case]` ID when only `family` was selected. `container.py:315` then represents an unreported family as NOT_RUN. This conclusion requires no grader or gold data. The full oracle-free scan is in `phase1_parametrized_families.csv`.

[inferred] Minimal **proposed, unapplied, untested** parser fix: map concrete cases back to an explicitly requested family and reuse the existing worst-status fold. This fixes discarded family output, not the policy for partial execution, and does not establish a causal explanation for these misses. It is not a full case-level differential design: a red base family can still absorb a new red case under family aggregation. Exact historical parser identity is UNKNOWN.

```diff
--- a/src/reliability/verifier/container.py
+++ b/src/reliability/verifier/container.py
@@ -362,9 +362,16 @@ def _parse_pytest(output: str, tests: tuple[str, ...]) -> dict[str, TestStatus]:
     statuses: dict[str, TestStatus] = {}
     for line in output.splitlines():
         match = _PYTEST_LINE.match(line.strip())
-        if match is None or match.group("id") not in wanted:
+        if match is None:
             continue
-        test, status = match.group("id"), _PYTEST_OUTCOME[match.group("outcome")]
+        test = match.group("id")
+        if test not in wanted and "[" in test:
+            family = test.split("[", 1)[0]
+            if family in wanted:
+                test = family
+        if test not in wanted:
+            continue
+        status = _PYTEST_OUTCOME[match.group("outcome")]
         earlier = statuses.get(test)
         if earlier is None or _PYTEST_SEVERITY[status] >= _PYTEST_SEVERITY[earlier]:
             statuses[test] = status
```

## Phase 2 — V2 false-positive rate

[confirmed] All 83 nonempty headline patches have a V2 outcome in `docs/results_100.csv` (69 right, 14 wrong by post-hoc oracle label); none is missing. The 13 NOT_AVAILABLE outcomes remain in the table. Detailed records are unavailable for many tasks, but their headline outcomes are present, so the missing-outcome stop condition does not apply.

| Post-hoc patch label | PASS | FAIL | NOT_AVAILABLE | Total |
|---|---:|---:|---:|---:|
| [inferred] right | 53 | 5 | 11 | 69 |
| [inferred] wrong | 11 | 1 | 2 | 14 |

[inferred] **False-positive rate over all right patches: 5/69 = 7.25%.** **Over right patches with usable V2: 5/(53+5) = 5/58 = 8.62%.** Usable excludes 11 NOT_AVAILABLE right patches, not partially executed PASS patches. False positives are exactly right patches with V2 FAIL, not all final FLAG/REJECT decisions.

| Repository | Right PASS / FAIL / NA | Wrong PASS / FAIL / NA |
|---|---:|---:|
| [inferred] astropy/astropy | 1 / 0 / 2 | 0 / 0 / 1 |
| [inferred] django/django | 24 / 3 / 0 | 4 / 0 / 0 |
| [inferred] matplotlib/matplotlib | 8 / 0 / 3 | 3 / 1 / 0 |
| [inferred] mwaskom/seaborn | 0 / 0 / 0 | 1 / 0 / 0 |
| [inferred] pallets/flask | 1 / 0 / 0 | 0 / 0 / 0 |
| [inferred] pydata/xarray | 4 / 0 / 1 | 0 / 0 / 0 |
| [inferred] pylint-dev/pylint | 1 / 0 / 1 | 3 / 0 / 0 |
| [inferred] pytest-dev/pytest | 6 / 1 / 0 | 0 / 0 / 0 |
| [inferred] scikit-learn/scikit-learn | 5 / 0 / 0 | 0 / 0 / 0 |
| [inferred] sphinx-doc/sphinx | 3 / 1 / 0 | 0 / 0 / 0 |
| [inferred] sympy/sympy | 0 / 0 / 4 | 0 / 0 / 1 |

[inferred] False-positive IDs: `pytest-dev__pytest-5809`; `django__django-12209`; `django__django-14140`; `django__django-14631`; `sphinx-doc__sphinx-10435`.
[confirmed] Raw outcomes, repository denominators/rates, and individual false positives are in `phase2_outcomes.csv`, `phase2_counts_by_repo.csv`, and `phase2_false_positives.csv`. Oracle outcome is used only as a post-hoc label.

## Phase 3 — static side experiment; no execution

[confirmed] **Step A preceded Step B.** All 36 outputs for nine cases were written to `frozen_selections/` and hashed in its manifest at `2026-10-23T20:39:53.973130+00:00`. Manifest SHA-256: `b065a6cda65f9eb21457361bd62bbd01fcf6a55e02d782e464bf3d10c5f3758c`. The freeze program lexically skips all unapproved mixed-snapshot values, including labels, gold patches, official lists and grader fields; the CSV projection accesses whitelisted non-oracle columns. It uses hash-verified candidate patch exports, base archives and existing graphs. Frozen files are verified before and after the post-hoc stage and are never regenerated in response to retention results.

[confirmed] The conversation already contained historical oracle observations; no claim of human/model blinding is made. Step A's program is isolated from those data: its selectors have no oracle field input. The fixed supplemental four-opportunity cohort comes from the user's requested preceding analysis; its labels are not queried to construct or tune any selector.

[inferred] Cohort: six stored selections of at least 1,000 tests; zero no-result cases established as selection-related; and the requested four opportunities reported separately (one overlaps the six, giving nine unique cases). Unexplained NOT_AVAILABLE outcomes are not reclassified as selection failures just because a static selector can return tests.

| Stored no-result group | Cases | Included as selection-related |
|---|---:|---| 
| [inferred] selection-related | 0 | yes |
| [inferred] timeout | 1 | no |
| [inferred] runner | 1 | no |
| [inferred] collection | 0 | no |
| [inferred] unknown | 11 | no |

[confirmed] Timeout: `astropy__astropy-13977` (already in the large cohort, not promoted to selection-related). Runner: `sympy__sympy-17318` (pytest absent). [inferred] UNKNOWN: `astropy__astropy-14365`, `astropy__astropy-14508`, `matplotlib__matplotlib-14623`, `matplotlib__matplotlib-25287`, `matplotlib__matplotlib-24177`, `pydata__xarray-4966`, `pylint-dev__pylint-6903`, `sympy__sympy-13480`, `sympy__sympy-14711`, `sympy__sympy-19783`, `sympy__sympy-24562`. See `no_result_groups.csv` for each record and evidence.

[inferred] **Frozen selector definitions:**

- **I1:** base test modules directly importing a candidate-changed production module.
- **I2:** the reverse syntactic import closure through one or two module hops. All statically declared imports, including conditional/local imports, count. `from pkg import name` links exact `pkg` and an exact `pkg.name` submodule when present; `from pkg import *` links only `pkg`. Relative imports use the actual package. Source roots `src/` and `lib/` are stripped; Django has its known `tests/` import-root alias. No dynamic imports, fuzzy tails, automatic parent-package expansion or re-export inference.
- **G3-R / G3-A:** existing amended graph, reverse call distance 1–3, using the same uniquely resolved candidate-changed symbol seeds. G3-R permits resolved edges; G3-A also permits existing ambiguous edges. Ambiguous seeds stay excluded in both, so the comparison changes edge status only. No class expansion, lexical fallback, ranking, budgets, or graph repair. Tests must exist in the base AST inventory.

[confirmed] Graph paths/hashes and candidate/archive hashes are in `step_a_inputs.json`; cohort and graph status in `case_cohort.csv`. [inferred] Both Pylint supplemental graphs are partial with missing portions (original graph reports resource-limited edge resolution); django-14631 is also partial. No graph output is treated as complete where its artifact says partial. Import AST parse failures are recorded separately in `base_inventory.json`. These static inventories are not proof of runtime collectability, inherited/dynamically generated test completeness, or coverage.

[inferred] Cells below are **test-family count / module count**; **THOUSANDS** marks at least 1,000 static tests. `L` = six large cases; `S` = supplemental opportunity-only cases. Counts are derived from the frozen sets.

| Case | Cohort | I1 | I2 | G3-R | G3-A |
|---|---|---:|---:|---:|---:|
| astropy__astropy-13977 | L | 373 / 7 | 5384 / 203 **THOUSANDS** | 324 / 54 | 327 / 55 |
| django__django-12209 | L | 1 / 1 | 4709 / 191 **THOUSANDS** | 0 / 0 | 0 / 0 |
| django__django-13212 | L | 451 / 8 | 2606 / 66 **THOUSANDS** | 0 / 0 | 17 / 4 |
| django__django-13297 | L | 82 / 3 | 269 / 7 | 1 / 1 | 1 / 1 |
| django__django-14140 | L | 0 / 0 | 5533 / 205 **THOUSANDS** | 0 / 0 | 262 / 32 |
| django__django-14631 | L | 203 / 2 | 2239 / 91 **THOUSANDS** | 0 / 0 | 0 / 0 |
| matplotlib__matplotlib-25479 | S | 279 / 5 | 2471 / 81 **THOUSANDS** | 0 / 0 | 0 / 0 |
| pylint-dev__pylint-6528 | S | 96 / 7 | 239 / 24 | 31 / 11 | 31 / 11 |
| pylint-dev__pylint-7277 | S | 169 / 16 | 269 / 37 | 1 / 1 | 1 / 1 |

[inferred] Runtime: exact subset runtimes are UNKNOWN. The available per-test caches for three large cases contain only zero duration placeholders (`duration_availability.csv`); no measured per-test timing can support a subset estimate. `selector_sizes.csv` and `phase3_metrics.csv` include an explicitly low-confidence proportional estimate `stored V2 duration × new set size / stored selected size` for seven uncensored cases. It includes setup/cache and assumes equal costs; it is a size-scaled proxy, not measured runtime or a promised speedup. Astropy-13977 and django-13297 are timeout censored and receive no estimate. An empty set's arithmetic zero is not a measured startup time.

| Case | I1 proportional seconds | I2 proportional seconds | G3-R proportional seconds | G3-A proportional seconds |
|---|---:|---:|---:|---:|
| [inferred] astropy__astropy-13977 | UNKNOWN (censored) | UNKNOWN (censored) | UNKNOWN (censored) | UNKNOWN (censored) |
| [inferred] django__django-12209 | 0.1 | 350.1 | 0.0 | 0.0 |
| [inferred] django__django-13212 | 26.8 | 154.7 | 0.0 | 1.0 |
| [inferred] django__django-13297 | UNKNOWN (censored) | UNKNOWN (censored) | UNKNOWN (censored) | UNKNOWN (censored) |
| [inferred] django__django-14140 | 0.0 | 271.5 | 0.0 | 12.9 |
| [inferred] django__django-14631 | 12.5 | 137.7 | 0.0 | 0.0 |
| [inferred] matplotlib__matplotlib-25479 | 55.6 | 492.7 | 0.0 | 0.0 |
| [inferred] pylint-dev__pylint-6528 | 62.4 | 155.3 | 20.1 | 20.1 |
| [inferred] pylint-dev__pylint-7277 | 101.3 | 161.2 | 0.6 | 0.6 |

[confirmed] **Step B only:** official failures and official F2P lists were opened after the manifest existed. No gold patch or gold test source is read by either new script. The earlier ceiling CSV supplies post-hoc base-relation labels, never selector inputs. [inferred] Exact Django unittest/node normalization and explicit parameter-family matching are used; docstring-only and renamed identities without a stored mapping stay UNKNOWN. The official F2P list is reported as a changed-behavior probe, not as a runtime changed-code coverage oracle.

| Six large cases | Compared probes | I1 retained | I2 retained | G3-R retained | G3-A retained |
|---|---|---:|---:|---:|---:|
| astropy__astropy-13977 | official failures | 0/8 | 0/8 | 0/8 | 0/8 |
| django__django-12209 | official F2P | 0/1; 1 UNKNOWN | 0/1; 1 UNKNOWN | 0/1; 1 UNKNOWN | 0/1; 1 UNKNOWN |
| django__django-13212 | official failures | 0/2 | 0/2 | 0/2 | 0/2 |
| django__django-13297 | official failures | 0/1 | 1/1 | 0/1 | 0/1 |
| django__django-14140 | official F2P | 0/4 | 3/4 | 0/4 | 3/4 |
| django__django-14631 | official F2P | 0/2; 2 UNKNOWN | 0/2; 2 UNKNOWN | 0/2; 2 UNKNOWN | 0/2; 2 UNKNOWN |

[inferred] **Four previously labeled existing-suite opportunities, separate from the six-case experiment:** cells count retained failing P2P identities/families. These are descriptive post-hoc opportunities with incomplete execution evidence, **not a pass/fail floor or selector acceptance criterion**. Pylint-6528's four official cases include two parameter cases served by one selected family.

| Opportunity | Baseline V2 | I1 | I2 | G3-R | G3-A |
|---|---|---:|---:|---:|---:|
| [inferred] django__django-13297 | [confirmed] PASS | 0/1 | 1/1 | 0/1 | 0/1 |
| [inferred] matplotlib__matplotlib-25479 | [confirmed] FAIL | 1/1 | 1/1 | 0/1 | 0/1 |
| [inferred] pylint-dev__pylint-6528 | [confirmed] PASS | 1/4 | 4/4 | 2/4 | 2/4 |
| [inferred] pylint-dev__pylint-7277 | [confirmed] PASS | 1/1 | 1/1 | 0/1 | 0/1 |

[inferred] Retaining a rewritten F2P name does not supply its gold body; new tests cannot be present in a base-only selection. Django-13297's unchanged P2P method has the previously recorded gold-changed class context; that is a post-hoc interpretation caveat, not Phase-1 causal evidence. For all four opportunities the stored per-test V2 execution status remains UNKNOWN. Raw identities, methods, unresolved IDs and base-relation labels are in `phase3_posthoc_test_matches.csv`; aggregate retention is in `phase3_metrics.csv` and `phase3_opportunities.csv`.

[confirmed] Stopped after Phase 3. No coverage pilot, graph engineering, testmon work, production edits, selector deployment, or test execution was started.

## Reproduction and audit files

[confirmed] Executed artifact-analysis commands (neither is a test command):

```bash
python3 -B reports/next_steps/freeze.py
python3 -B reports/next_steps/analyze.py
```

[confirmed] `freeze.py` refuses to overwrite an existing manifest. `step_b_gate.json` records the manifest hash and verification; `completion.json` records frozen-file verification after analysis. `analysis_inputs.json` records the later input hashes. Do not feed any post-hoc labels, comparisons, or proposed diff back into a run, selector or policy.
