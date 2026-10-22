POST-HOC ANALYSIS ONLY. This file uses oracle fields (FAIL_TO_PASS, PASS_TO_PASS, gold patch, test_patch). It must never feed back into any run, policy, manifest, or config.

# CIS 695 post-hoc failure analysis

Dataset source: HuggingFace `SWE-bench/SWE-bench_Verified` via `reliability.benchmark.loader.load_instance`. Named file `local_swebench_verified.jsonl` was **NOT FOUND**.

Replacement runs: `matplotlib__matplotlib-20676` from `main_2_rerun_mpl`; `sympy__sympy-17318` from `main_3_rerun_infra`; everything else from `main_50_a` / `main_50_b`. No record in `docs/results_100.csv` disagrees with the study-run verification/oracle files used here. The original leak-open `matplotlib__matplotlib-20676` in `main_50_a` is a **different patch** and is reported separately; it is not the study row.

Full quoted issue/patch/test files: `reports/failure_analysis/quotes/<instance_id>.md`.

## Summary

| Group | n | A WRONG_BEHAVIOUR | B INCOMPLETE_FIX | C REGRESSION_UNSEEN | D UNDERSPECIFIED | E SHARED_MISREADING | F OTHER |
|---|---|---|---|---|---|---|---|
| 1 false ACCEPT | 7 | 1 | 2 | 1 | 3 | 0 | 0 |
| 2 false FLAG (wrong patch) | 6 | 1 | 3 | 1 | 1 | 0 | 0 |
| 3 false REJECT | 1 | 0 | 1 | 0 | 0 | 0 | 0 |

Group 4 (right patches, A–F do not apply): **4 SUPERSEDED_ASSERTION** (django-14140, django-14631, pytest-5809, sphinx-10435). **1 NOT_ALL_SUPERSEDED** (django-12209: `test_save_primary_with_default` is not in gold `test_patch`).

**Of the 7 false accepts, 4 are real agent errors (A/B/C/E) and 3 are grader strictness (D):**

- Real agent error: django-13212 (B), pylint-7277 (A), django-13297 (C), matplotlib-23476 (B).
- Grader strictness: django-16667 (D), matplotlib-23299 (D), pylint-4661 (D).

Group 4 V2 rerun (existing `run_regression` path, baseline copied under `reports/failure_analysis/_baseline_cache_copy`): 4 of 5 tasks are SUPERSEDED_ASSERTION (every V2-failing test is rewritten/removed in gold `test_patch`). django-12209 is not: its one failing test is not in the gold `test_patch`.

---

# Group 1 — wrong patches the verifier ACCEPTed

## django__django-13212 — **B INCOMPLETE_FIX** (high)

**Run:** `main_50_a`. **Decision:** ACCEPT. **Oracle:** unresolved.

**Issue (quoted):**

> Make validators include the provided value in ValidationError
> It is sometimes desirable to include the provide value in a custom error message. For example:
> “blah” is not a valid email.
> By making built-in validators provide value to ValidationError, one can override an error message and use a %(value)s placeholder.

**Oracle failing tests:**

- F2P fail: `test_value_placeholder_with_decimal_field (forms_tests.tests.test_validators.ValidatorCustomMessageTests)`, `test_value_placeholder_with_file_field (...)`
- F2P pass: char_field, integer_field, null_character
- P2P fail: none

**Gold test (decimal) quoted:**

```
class MyForm(forms.Form):
    field = forms.DecimalField(
        max_digits=2, decimal_places=1,
        error_messages={code: '%(value)s'},
    )
form = MyForm({'field': value})
self.assertEqual(form.errors, {'field': [value]})
```
with cases `'NaN'` / `'invalid'`, `'123'` / `'max_digits'`, etc.

**Gold extra hunk the agent does not have** (`django/forms/fields.py`):

```
-    def validate(self, value):
-        super().validate(value)
-        if value in self.empty_values:
-            return
-        if not value.is_finite():
-            raise ValidationError(self.error_messages['invalid'], code='invalid')
```

Agent and gold both add `params={'value': value}` on `DecimalValidator` and `FileExtensionValidator`. NaN is rejected by `DecimalField.validate()` **before** the validator, with no `value` in params. That is why the official DecimalField F2P fails.

**Signals:** integrity PASS; regression PASS (1137 executed, 0 regressions, n_selected=1383, convention=tests_tree); static PASS; V4 PASS 3/3.

**V2 selection:** `tests/validators/tests.py::...` plus a large tests_tree set. The failing F2P tests live in `tests/forms_tests/tests/test_validators.py` and were **not** selected. overlap.py P2P overlap=0/2 (django label vs node-id mismatch).

**V4 (quoted asserts):** `expect_message(regex_validator, "blah", "blah is not a number.")` and `params` contains the value for IPv4/DecimalValidator. They never construct a `DecimalField` or `FileField`. That is why V4 passed.

**V2 passed** because it never ran the gold forms_tests F2P cases (new tests in `test_patch`).

**Why V4 ≠ gold:** partly. Same `%(value)s` idea; gold also requires form-field error strings for DecimalField/FileField.

---

## django__django-16667 — **D UNDERSPECIFIED** (high)

**Run:** `main_50_a`. **Decision:** ACCEPT. **Oracle:** unresolved.

**Issue (quoted):** visiting `?my_date_year=1234567821345678` yields `OverflowError: signed integer is greater than maximum` from `datetime.date(int(y), int(m), int(d))`. The issue asks that validation not crash.

**Agent patch:**

```
-            except ValueError:
+            except (ValueError, OverflowError):
                 return "%s-%s-%s" % (y or 0, m or 0, d or 0)
```

**Gold patch:**

```
+            except OverflowError:
+                return "0-0-0"
```

**Oracle:** F2P fail `test_value_from_datadict` (expects overflow → `"0-0-0"`); F2P pass `test_form_field` (form invalid, `"Enter a valid date."`); P2P none fail.

**Gold widget assertion quoted:**

```
+            ((str(sys.maxsize + 1), "12", "1"), "0-0-0"),
```

The issue never states the widget must return the sentinel `"0-0-0"`. The agent's catch still makes `form.is_valid()` false (the other F2P passed). That is grader format strictness, not a missed crash.

**Signals:** integrity PASS; regression PASS (192 executed, n_selected=272) including `SelectDateWidgetTest::test_value_from_datadict` (pre-gold assertions); V4 PASS.

**V4 (quoted):** `assert is_valid_without_crash(form) is False` on year `1234567821345678`. No check of `"0-0-0"`.

**V2 ran** the same node id but the **old** test body (no overflow row), so it passed.

**v4 vs gold:** no.

---

## pylint-dev__pylint-7277 — **A WRONG_BEHAVIOUR** (medium)

**Run:** `main_50_a`. **Decision:** ACCEPT. **Oracle:** unresolved.

**Issue (quoted):** `sys.path.pop(0)` when running via `runpy`; “there should be a check to ensure that the first item is `""`, `"."` or `os.getcwd()` before removing.”

**Agent (quoted):**

```
+    cwd = os.getcwd()
+    if not sys.path or sys.path[0] not in ("", ".", cwd):
+        return
     sys.path.pop(0)
```

**Gold (quoted):**

```
-    sys.path.pop(0)
     cwd = os.getcwd()
+    if sys.path[0] in ("", ".", cwd):
+        sys.path.pop(0)
     env_pythonpath = os.environ.get("PYTHONPATH", "")
```

Gold still runs the PYTHONPATH `:` pops when the first entry is custom. Agent **returns** and skips them.

**Oracle:** F2P `test_modify_sys_path` **passed**. P2P fail: `tests/test_self.py::TestRunTC::test_jobs_score`.

**Signals:** integrity PASS; regression PASS (57 executed, 2 PRE_EXISTING_FAIL, 13 NOT_RUN); V4 PASS. n_selected=70 including **both** `test_modify_sys_path` and `test_jobs_score`. P2P overlap 53/122.

**V2 selected the failing P2P test.** Per-test outcomes are not stored; the 2 PRE_EXISTING_FAIL slots are the likely classification, so V2 did not treat it as a regression. Confidence medium because we cannot quote a stored outcome for `test_jobs_score`.

**V4 (quoted):** `assert sys.path[0] == "something"` after `modify_sys_path()` / runpy. Matches the issue and the gold `/do_not_remove` idea; does not check PYTHONPATH colon handling.

**Why V4 passed:** it only checks that a custom leading entry is kept. **Why V2 passed:** F2P-equivalent `test_modify_sys_path` passed on the patched tree; `test_jobs_score` was not counted as REGRESSION.

---

## django__django-13297 — **C REGRESSION_UNSEEN** (high)

**Run:** `main_50_b`. **Decision:** ACCEPT. **Oracle:** unresolved.

**Issue (quoted):** `TemplateView.get_context_data` kwargs are `SimpleLazyObject`, causing `Error binding parameter 0` in ORM lookups.

**Agent:** calls `get_context_data(**kwargs)` **unwrapped**, then wraps the **context** afterwards.

**Gold:** keep wrapping kwargs, but `lazy(access_value, type(value))()` instead of `@SimpleLazyObject`.

**Oracle:** F2P `test_template_params_filtering` **passed**; P2P fail `test_template_params_warning`.

**Gold F2P quoted:**

```
def get_context_data(self, *, artist_name, **kwargs):
    artist = Artist.objects.get(name=artist_name)
...
self.assertEqual(response.context_data['artist'], artist)
```

**Gold P2P (existing) `test_template_params_warning`** still expects the deprecation warning when URL kwargs are read from the context. Agent’s different wrap timing breaks that.

**Signals:** integrity PASS; regression PASS (1265 executed, **6890 TIMEOUT**, n_selected=8155); V4 PASS.

**V2 selected** `tests/generic_views/test_base.py::DeprecationTests::test_template_params_warning` (symbol match). overlap.py reports 0/52 P2P overlap because django labels vs node ids. With 6890 timeouts, that P2P test did not finish as a completed regression.

**V4 (quoted):** `get_object_or_404` / ORM lookup with a URL kwarg must not raise `InterfaceError`. That is the F2P idea, not the warning test.

**Why V4 passed:** crash-on-ORM is fixed. **Why V2 passed:** the warning P2P test did not complete as REGRESSION (timeout mass).

---

## matplotlib__matplotlib-23299 — **D UNDERSPECIFIED** (high)

**Run:** `main_50_b`. **Decision:** ACCEPT. **Oracle:** unresolved. static FAIL (informational; FullPolicy does not read it).

**Issue (quoted):** `get_backend()` “removes all figures from `Gcf` if the first figure in `Gcf.figs` was created in an `rc_context`.” Expected: “The figure should not be missing from `Gcf`.”

**Agent:** early-return in `pyplot.switch_backend` if the auto sentinel is already resolved, so figures are not closed.

**Gold:** `rc_context` does not restore `backend`:

```
+    orig = dict(rcParams.copy())
+    del orig['backend']
```

**Official F2P quoted (the entire new test):**

```
def test_no_backend_reset_rccontext():
    assert mpl.rcParams['backend'] != 'module://aardvark'
    with mpl.rc_context():
        mpl.rcParams['backend'] = 'module://aardvark'
    assert mpl.rcParams['backend'] == 'module://aardvark'
```

The issue never mentions `rcParams['backend']` persistence or `module://aardvark`.

**Oracle:** F2P fail that test; P2P none fail.

**V4 (quoted):** `assert fig.number in after_keys` / `plt.fignum_exists` / `plt.gcf() is fig` after `get_backend()`. That is the issue. Agent’s workaround satisfies it.

**V2:** n_selected=46 in `test_pyplot.py` / qt backends; **did not** select `test_rcparams.py::test_no_backend_reset_rccontext` (gold-added). P2P overlap 0/192.

**Why V4 passed:** it checks Gcf, not rcParam restore. **Why V2 passed:** it never ran the gold rc_context test.

**v4 vs gold:** no.

---

## matplotlib__matplotlib-23476 — **B INCOMPLETE_FIX** (high)

**Run:** `main_50_b`. **Decision:** ACCEPT. **Oracle:** unresolved.

**Issue (quoted):** after unpickle, dpi doubles every iteration on M1 Mac (`200, 400, 800, ...`). Expected printout: dpi stays `200.0`.

**Agent:** do not overwrite `figure._original_dpi` if already set; set `_original_dpi = None` in `Figure.__init__`.

**Gold:**

```
+        # discard any changes to the dpi due to pixel ratio changes
+        state["_dpi"] = state.get('_original_dpi', state['_dpi'])
```
in `Figure.__getstate__`.

**Official F2P quoted:**

```
fig = Figure(dpi=42)
fig.canvas._set_device_pixel_ratio(7)
assert fig.dpi == 42*7
fig2 = pickle.loads(pickle.dumps(fig))
assert fig2.dpi == 42
```

Agent never writes original dpi into the pickle, so unpickled dpi stays scaled. Right idea (do not apply the ratio twice), missing the serialization the F2P checks.

**V4 (quoted):** after unpickle **re-apply** `_set_device_pixel_ratio(2)` and `assert fig.dpi == expected_dpi` (200). That can pass without `__getstate__` if canvas init does not double-apply.

**V2:** n_selected=696 including `test_figure.py` but **not** `test_unpickle_with_device_pixel_ratio` (gold-added). P2P overlap 44/104.

**Why V4 passed:** it re-applies the ratio and checks “no doubling,” not `dpi==42` on the raw unpickled figure. **Why V2 passed:** it did not run the gold-added test.

**v4 vs gold:** no.

---

## pylint-dev__pylint-4661 — **D UNDERSPECIFIED** (high)

**Run:** `main_50_b`. **Decision:** ACCEPT. **Oracle:** unresolved.

**Issue (quoted):** “data storage has a designated spot. The `$HOME/.local/share/<PROGRAM_NAME>` folder” (XDG **data**). “Simply change the variables/constants for where these files are made.”

**Agent:** `PYLINT_HOME = os.environ.get("PYLINTHOME", user_data_dir("pylint", "pylint"))` via **platformdirs**.

**Gold:** `PYLINT_HOME = appdirs.user_cache_dir("pylint")` (**cache**, plus appdirs dependency).

**Official F2P quoted:**

```
-        expected = os.path.join(uhome, ".pylint.d")
+        expected = appdirs.user_cache_dir("pylint")
    assert config.PYLINT_HOME == expected
```

The issue asked for data dir; the grader checks cache dir. V4 asserts XDG data paths (`$XDG_DATA_HOME/pylint` or `$HOME/.local/share/pylint`) — same misreading as the issue text, opposite of gold.

**Oracle:** F2P fail `tests/lint/unittest_lint.py::test_pylint_home`; official P2P list is empty.

**V2:** n_selected=4, all `tests/test_config.py::test_can_read_*`. Did not run `test_pylint_home`.

**Why V4 passed:** it encodes the issue’s data-dir requirement. **Why V2 passed:** it ran config-file readers, not PYLINT_HOME.

This is **not** E: V4 matches the **issue**, not the gold test. Label D.

---

# Group 2 — wrong patches the verifier FLAGged

## matplotlib__matplotlib-20676 — **A WRONG_BEHAVIOUR** (high)

**SPECIAL: two different agent patches. Do not draw a causal conclusion from one run.**

### Study record (masked rerun) — `main_2_rerun_mpl`

**Decision:** FLAG (`reproduction is NOT_AVAILABLE`). **Oracle:** unresolved.

**Issue (quoted):** interactive `SpanSelector` “forces axes limits to include 0.” Expected: limits remain at `(10, 20) + margins`.

**Rerun agent:** replace `ax.axvline`/`axhline` with `Line2D` + `ax.add_artist` in `ToolLineHandles.__init__`. Still constructs handles from `self.extents` in `_setup_edge_handle`.

**Gold (quoted):**

```
+        if self.direction == 'horizontal':
+            positions = self.ax.get_xbound()
+        else:
+            positions = self.ax.get_ybound()
+        self._edge_handles = ToolLineHandles(self.ax, positions,
```

**Oracle F2P fail:** `test_span_selector_bound[horizontal]`, `test_span_selector_bound[vertical]`. Gold also asserts `tool._edge_handles.positions == list(bound)`.

**Signals:** integrity PASS; regression PASS (340 executed, n_selected=736 including `test_span_selector` but **not** gold-added `test_span_selector_bound`); static FAIL (informational); **V4 NOT_AVAILABLE** `generator wrote no test files (LimitsExceeded)`. n_frozen=0.

**Why FLAG:** no V4, not a V2 catch of the F2P. **Why V2 passed:** gold F2P was not in the old suite / not selected. **Why V4 “passed”:** it did not run.

### Original leak-open — `main_50_a` (not the study row)

csv_disagreements vs `results_100.csv` are expected: this is **not** the replacement run (`source_run` csv=`main_2_rerun_mpl`, this record=`main_50_a`).

**Decision:** ACCEPT. **Oracle:** **resolved.** F2P both span_selector_bound tests **passed**.

**Original agent patch is the gold `_setup_edge_handle` axis-bounds change**, not the Line2D rerun patch (885 vs 1183 bytes). V4 existed and passed (`assert xlim_after == xlim_before`).

These are two agent attempts, not one patch under two leakage conditions. No causal claim about leakage.

---

## pylint-dev__pylint-6528 — **C REGRESSION_UNSEEN** (medium)

**Run:** `main_50_a`. **Decision:** FLAG (V4 LimitsExceeded). **Oracle:** unresolved.

**Issue:** `--ignore` / `--ignore-patterns` / `--ignore-paths` ignored under `--recursive=y`.

**Agent vs gold:** both add `_is_ignored_file` and skip ignored roots in `_discover_files`. Agent uses `os.path.normpath` and `dirs[:] = []`; gold uses `skip_subtrees.append(root)` without normpath.

**Oracle:** **all 4 F2P passed.** P2P fail: `test_custom_should_analyze_file`, `test_multiprocessing[1]`, `test_multiprocessing[2]`, `test_jobs_score`.

**Signals:** regression PASS (191 executed, 2 PRE_EXISTING_FAIL); V4 NA; n_selected=218. V2 **selected** `test_custom_should_analyze_file` and `test_jobs_score`. FLAG is from missing V4, not from V2 FAIL.

**Why V4 “passed”:** no tests generated. **Why V2 passed:** F2P not in old suite / not selected as those parametrized names; selected P2P fails classified as PRE_EXISTING_FAIL rather than REGRESSION (outcomes not stored).

---

## astropy__astropy-13977 — **B INCOMPLETE_FIX** (high)

**Run:** `main_50_b`. **Decision:** FLAG (regression NOT_AVAILABLE + V4 NA). **Oracle:** unresolved.

**Issue (quoted):** `Quantity.__array_ufunc__` should return `NotImplemented` for incompatible duck types instead of `ValueError`, so `__radd__` can run.

**Agent:** if any input is not `Quantity`/`ndarray` but has `__array_ufunc__`, `return NotImplemented` immediately.

**Gold:** `try/except` around `converters_and_unit`, plus `out=` handling — only defer when conversion actually fails.

**Oracle:** 8 F2P fail, all `test_full[empty-...-add/multiply]`; 12 F2P pass (`None` and `less`). P2P none fail.

Blanket `NotImplemented` misses the `out=empty` add/multiply cases the official F2P checks.

**Signals:** regression NOT_AVAILABLE (3082 selected, 3082 TIMEOUT, 0 executed); V4 LimitsExceeded.

**Why V4/V2 “passed”:** neither completed. V2 did not execute the failing F2P names (`test_quantity_ufuncs.py` parametrized ids not in the selected `test_quantity.py` list as those node ids).

---

## django__django-16631 — **B INCOMPLETE_FIX** (high)

**Run:** `main_50_b`. **Decision:** FLAG (V4 NA). **Oracle:** unresolved. static FAIL informational.

**Issue (quoted):** `SECRET_KEY_FALLBACKS` is not used for sessions; `get_session_auth_hash` does not pass `secret=` to `salted_hmac`.

**Agent:** verify fallback hashes; if any match, `session_hash_verified = True`. **Does not** `cycle_key` or write the new hash.

**Gold (quoted):**

```
+                    if session_hash and any(... fallback ...):
+                        request.session.cycle_key()
+                        request.session[HASH_SESSION_KEY] = session_auth_hash
+                    else:
+                        request.session.flush()
```

**Official F2P quoted:**

```
self.assertNotEqual(request.session.session_key, prev_session_key)
```
after rotating SECRET_KEY with fallbacks. Agent leaves the session key unchanged.

**V2:** n_selected=478 auth backends tests; **not** `test_get_user_fallback_secret` (gold-added). P2P overlap 0/12 (django labels).

**Why FLAG:** V4 LimitsExceeded. **Why V2 passed:** did not run the new F2P.

---

## mwaskom__seaborn-3069 — **B INCOMPLETE_FIX** (high)

**Run:** `main_50_b`. **Decision:** FLAG (V4 NA). **Oracle:** unresolved.

**Issue:** Nominal scales should match categorical: ±0.5 limits, no grid, y inverted.

**Gold (quoted):**

```
+                    axis_obj.grid(False, which="both")
+                    if axis_key not in p._limits:
+                        nticks = len(axis_obj.get_major_ticks())
+                        lo, hi = -.5, nticks - .5
+                        if axis == "y":
+                            lo, hi = hi, lo
+                        set_lim(lo, hi, auto=None)
```

No `set_inverted`.

**Agent:** also `ax.yaxis.set_inverted(True)` and `locs = get_majorticklocs(); lo, hi = locs[0]-0.5, locs[-1]+0.5`.

**Oracle:** F2P pass `test_nominal_x_axis_tweaks`; fail `test_nominal_y_axis_tweaks`.

**Gold y test quoted:** `assert ax1.get_ylim() == (2.5, -.5)`. Extra invert + tick-loc limits break y, not x (`xlim == (-.5, 2.5)` passed).

**V2:** selected `TestScaling` tests but **not** the gold-added nominal tweaks. P2P overlap 65/94.

**Why FLAG:** V4 NA. **Why V2 passed:** gold F2P not selected.

**v4 vs gold:** no V4. Agent’s y invert matches the **issue** bullet 3; gold test expects inverted *limits* without `set_inverted`.

---

## sympy__sympy-17318 — **D UNDERSPECIFIED** (high)

**Run:** `main_3_rerun_infra` (replacement). **Decision:** FLAG (`regression is NOT_AVAILABLE`). **Oracle:** unresolved.

**Issue (quoted):** `sqrtdenest` raises `IndexError`. “If an expression cannot be denested it should be returned unchanged.” Issue’s own “New Result”:

> `sqrtdenest((3 - sqrt(2)*sqrt(4 + 3*I) + 3*I)/2)` → `3/2 - sqrt(2)*sqrt(4 + 3*I)/2 + 3*I/2`

**Agent:** in `split_surds`, `if not surds: return S.One, S.Zero, expr`.

**Gold:** in `_sqrt_match`, only call `split_surds` when `all(sq.is_Rational and sq.is_positive for sq in sqargs)`.

**Official F2P quoted:**

```
def test_issue_12420():
    assert _sqrt_match(4 + I) == []
    assert sqrtdenest((3 - sqrt(2)*sqrt(4 + 3*I) + 3*I)/2) == I
    assert sqrtdenest(e) == e
```

The official test requires denesting **to `I`**, which the issue text does not state (it shows the unchanged expression).

**Signals:** V2 NOT_AVAILABLE (`No module named pytest`; 21 selected, 0 executed). **V4 PASS** 3/3: no IndexError, return unchanged.

**Why FLAG:** V2 could not run pytest, even though V4 passed. **Why V4 passed:** it encodes the issue (“unchanged”), not `== I`. **v4 vs gold:** no.

---

# Group 3 — wrong patch the verifier REJECTed

## matplotlib__matplotlib-25479 — **B INCOMPLETE_FIX** (high)

**Run:** `main_50_b`. **Decision:** REJECT (`regression test failed`). **Oracle:** unresolved.

**Issue (quoted):** `register_cmap(name='my_cmap_name', cmap=my_cmap)` then lookup uses `cmap.name` (`some_cmap_name`) instead of the registered name.

**Agent:**

```
+        cmap = cmap.copy()
+        cmap.name = name
+        self._cmaps[name] = cmap
```

**Gold:** same name update **plus** `Colormap.__eq__` no longer compares `.name`.

**Gold F2P quoted:**

```
# Test different names are equal if the lookup table is the same
cm_copy.name = "Test"
-    assert cm_copy != cmap
+    assert cm_copy == cmap
```

and `test_set_cmap_mismatched_name`: `assert cmap_returned == cmap` and `assert cmap_returned.name == "wrong-cmap"`.

Without `__eq__` ignoring names, `cmap_returned == cmap` fails even if register rewrote `.name` on the stored copy (the original object still has the old name). Right idea, misses the equality change both F2P tests use.

**Oracle:** F2P fail `test_colormap_equals`, `test_set_cmap_mismatched_name`; P2P fail `test_register_cmap`.

**Signals:** regression FAIL (78 executed, **1 REGRESSION**); V4 NA LimitsExceeded. n_selected=88 including `test_colormap_equals` and `test_register_cmap`. `test_set_cmap_mismatched_name` is gold-added, not selected.

**Why REJECT:** V2 saw a real old-suite failure (`test_register_cmap` and/or old `test_colormap_equals`). **Why V4 “passed”:** not generated.

Note: gold **rewrites** `test_colormap_equals` (names-not-equal → names-equal). The old assertion is superseded; V2 may have flagged that rewrite. The patch is still incomplete vs gold `__eq__`.

---

# Group 4 — right patches (oracle resolved) that failed old tests

V2 did not store failing test ids. Verifier-only rerun (no agent, no V4, no oracle; existing `run_regression`; baseline copied out of `runs/`): `reports/failure_analysis/group4_failing_tests.json`. Gold classification: `scripts/old_assertion_check_gold.py` → `group4_gold_check.json`.

A task is a superseded-assertion case **only if every failing V2 test is SUPERSEDED**. **4 of 5 are.** django-12209 is not.

## django__django-12209

**Run:** `main_50_b`. FLAG (regression FAIL, V4 PASS). Oracle **resolved**.

**Dataset / harness F2P name is garbage** (must report): official FAIL_TO_PASS is `partial(func, *args, **keywords) - new function with partial application` — a `functools.partial` docstring, not a test id. Harness `f2p_success` is the same string; P2P list empty. `local_swebench_verified.jsonl` was not present to cross-check.

**Issue:** saving with explicit pk on a field that has `default` should UPDATE, not INSERT.

**Agent:** deletes the whole “Skip an UPDATE when adding an instance and primary key has a default” block.

**Gold:** only adds `not raw and` to that condition (loaddata/raw still inserts).

**Gold test_patch:** **only adds** `UUIDDefaultData` model and serializer case 793. Does not rewrite existing save tests.

**V2 rerun failing test:** `tests/basic/tests.py::ModelInstanceCreationTests::test_save_primary_with_default`  
**Membership:** NEITHER (dataset F2P/P2P do not name this test).  
**Gold `test_patch`:** **NOT_TOUCHED** (no hunk in `tests/basic/tests.py`; gold only adds serializer `UUIDDefaultData`).

This is **not** a superseded-assertion case. Agent deletes the force-insert-when-default-pk skip entirely; gold keeps it except `raw`. The old test still encodes the Django 3.0 “new instance with default pk → INSERT” behaviour, which the agent no longer has. Real behaviour difference vs gold, even though the oracle resolved the issue’s explicit-pk UPDATE case.

V2 rerun: 2929 executed, 1 REGRESSION, n_selected=3319, baseline from cache. V4 asserts UPDATE not duplicate INSERT — matches the issue, not this old test.

## django__django-14140

**Run:** `main_50_b`. FLAG. Oracle resolved. V2 **2 REGRESSIONS**.

**Issue:** `Q(Exists(...)).deconstruct()` TypeError; single-child Q used kwargs `{child[0]: child[1]}`.

**Agent and gold** both remove the single-child special case (`args = tuple(self.children)`).

**Gold test_patch rewrites existing tests:**

```
-        self.assertEqual(args, ())
-        self.assertEqual(kwargs, {'price__gt': F('discounted_price')})
+        self.assertEqual(args, (('price__gt', F('discounted_price')),))
+        self.assertEqual(kwargs, {})
```
and the same for `test_deconstruct_negated`. Also **adds** `test_deconstruct_boolean_expression`.

**V2 rerun failing tests (both SUPERSEDED, both official F2P after rewrite):**

- `tests/queries/test_q.py::QTests::test_deconstruct`
- `tests/queries/test_q.py::QTests::test_deconstruct_negated`

Quoted gold `test_patch`:

```
-        self.assertEqual(args, ())
-        self.assertEqual(kwargs, {'price__gt': F('discounted_price')})
+        self.assertEqual(args, (('price__gt', F('discounted_price')),))
+        self.assertEqual(kwargs, {})
```

and for negated:

```
-        self.assertEqual(kwargs, {
-            'price__gt': F('discounted_price'),
-            '_negated': True,
-        })
+        self.assertEqual(args, (('price__gt', F('discounted_price')),))
+        self.assertEqual(kwargs, {'_negated': True})
```

**Task = SUPERSEDED_ASSERTION.** V4 `assert args == (('x', 1),)` matches the new gold, not the old kwargs form. V2 rerun: 1797 executed, 2 REGRESSIONS.

## django__django-14631

**Run:** `main_50_b`. FLAG. Oracle resolved. V2 **1 REGRESSION**.

**Issue:** `_clean_fields` / `changed_data` should go through BoundField so `cleaned_data` matches `form[name].initial`.

**Gold test_patch rewrites** `test_datetime_clean_initial_callable_disabled`:

```
-    def test_datetime_clean_initial_callable_disabled(self):
-        now = datetime.datetime(2006, 10, 25, 14, 30, 45, 123456)
-        ...
-        self.assertEqual(form.cleaned_data, {'dt': now})
+    def test_datetime_clean_disabled_callable_initial_microseconds(self):
+        ...
+        self.assertEqual(form.cleaned_data, {
+            'dt': datetime.datetime(2006, 10, 25, 14, 30, 46),
+        })
+    def test_datetime_clean_disabled_callable_initial_bound_field(self):
+        ...
+        self.assertEqual(cleaned, bf.initial)
```

Official F2P names in the dataset are those **docstrings**, not node ids. The V2-failing node is the **old** function name.

**V2 rerun failing test:** `tests/forms_tests/tests/test_forms.py::FormsTestCase::test_datetime_clean_initial_callable_disabled`  
**Membership:** NEITHER (dataset F2P strings are the new docstrings).  
**SUPERSEDED** — gold removes the old function and assertions:

```
-    def test_datetime_clean_initial_callable_disabled(self):
-        now = datetime.datetime(2006, 10, 25, 14, 30, 45, 123456)
-            dt = DateTimeField(initial=lambda: now, disabled=True)
-        self.assertEqual(form.cleaned_data, {'dt': now})
+    def test_datetime_clean_disabled_callable_initial_bound_field(self):
+        self.assertEqual(cleaned, bf.initial)
```

**Task = SUPERSEDED_ASSERTION.** V4 asserts `cleaned_data == BoundField.initial`. V2 rerun: 2812 executed, 1 REGRESSION.

## pytest-dev__pytest-5809

**Run:** `main_50_a`. FLAG. Oracle resolved. V2 **1 REGRESSION** of 4 executed.

**Issue:** pastebin `lexer=python3` causes HTTP 400; use `lexer=text`.

**Agent and gold:** `"lexer": "text"`.

**Gold test_patch (existing test rewrite):**

```
-        lexer = "python3" if sys.version_info[0] >= 3 else "python"
+        lexer = "text"
         assert "lexer=%s" % lexer in data.decode()
```

**V2 rerun failing test:** `testing/test_pastebin.py::TestPaste::test_create_new_paste` (official F2P; SUPERSEDED).

Quoted:

```
-        lexer = "python3" if sys.version_info[0] >= 3 else "python"
+        lexer = "text"
         assert "lexer=%s" % lexer in data.decode()
```

**Task = SUPERSEDED_ASSERTION.** V2 selected that test plus TestPasteCapture; P2P overlap 3/3; 4 executed, 1 REGRESSION. V4 asserts `lexer=text`.

## sphinx-doc__sphinx-10435

**Run:** `main_50_b`. FLAG. Oracle resolved. V2 **1 REGRESSION**.

**Issue:** LaTeX inline code highlighting inserts whitespace; suggested `sphinxupquote{% ... %}`.

**Agent:** replace opener with `sphinxupquote{%` and `rstrip() + '%\n'`.

**Gold:** opener `%`, strip `\n\end{Verbatim}` (`[:-15]`), trailer `'%' + CR + '}}'`.

**Gold test_patch rewrite of existing `test_latex_code_role`:**

```
-    assert (r'Inline \sphinxcode{\sphinxupquote{' + '\n' +
-            common_content + '\n}} code block') in content
+    assert (r'Inline \sphinxcode{\sphinxupquote{%' + '\n' +
+            common_content + '%\n}} code block') in content
```

**V2 rerun failing test:** `tests/test_build_latex.py::test_latex_code_role` (official F2P; SUPERSEDED).

Quoted:

```
-    assert (r'Inline \sphinxcode{\sphinxupquote{' + '\n' +
-            common_content + '\n}} code block') in content
+    assert (r'Inline \sphinxcode{\sphinxupquote{%' + '\n' +
+            common_content + '%\n}} code block') in content
```

**Task = SUPERSEDED_ASSERTION.** V2 selected that file (P2P overlap 74/74); 86 executed, 1 REGRESSION. V4 checks no leading whitespace / trailing `%` (partly gold).

---

# Coverage notes

`reliability.analysis.overlap.names_match` compares node-id tails. Django official names are `test_foo (module.Class)` so **overlap.py reports 0** even when V2 selected the same test as a node id. This analysis also used symbol-level membership (reported in each section).

V2 findings store counts, not failing names — Group 4 rerun is required for those ids.

V4 sources live in `runs/<exp>/_reproduction_cache/<id>/tests/test_repro_*.py`, not in the verification record body.

# Missing / disagreements

- `local_swebench_verified.jsonl`: **NOT FOUND**. Gold fields from HF `load_instance`.
- Per-test V2 outcomes: **not stored** in `verification_record.full.json`. Group 4 rerun reproduced the stored regression *counts* (1, 2, 1, 1, 1) and supplied the missing names.
- `django__django-12209` FAIL_TO_PASS in both HF and the harness report is a `functools.partial` docstring, not a test name.
- No study-row disagreement with `docs/results_100.csv`. The extra `matplotlib__matplotlib-20676` `main_50_a` record disagrees with the csv **by design** (csv uses `main_2_rerun_mpl`).
