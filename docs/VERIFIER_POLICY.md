# Regression Test Selection Policy

**Component:** Verifier V2 (existing regression tests)
**Status:** Draft for advisor review — 2026-09-15
**Checklist gate:** Phase 5.1

---

## 1. Purpose and constraint

The verifier runs a subset of the repository's pre-existing tests to determine whether a candidate patch broke previously working behaviour. The subset must be chosen using only information a developer would have with the issue still open: the candidate patch and the repository at the base commit.

The selection must never consult `PASS_TO_PASS`, `FAIL_TO_PASS`, the gold patch, or the gold test patch. This is the property that makes the verifier's decision meaningful; a verifier that selected tests using the benchmark's own relevance list would be answering a question no deployed system can ask.

One structural protection already holds: the gold test patch is not applied at the base commit, so tests introduced by the human fix do not exist in the working tree the verifier reads. Selection cannot reach them even by accident.

---

## 2. Permitted and forbidden inputs

**Permitted**

- the candidate patch (file paths, hunks, changed symbol names)
- the repository tree at the base commit, including all pre-existing test files
- the repository's own test configuration (`pytest.ini`, `setup.cfg`, `tox.ini`, `conftest.py`)
- the issue description

**Forbidden**

- `PASS_TO_PASS`, `FAIL_TO_PASS`
- the gold patch, the gold test patch
- the oracle verdict
- test files created or modified by the *candidate* patch (see §5.3)

---

## 3. Procedure

### 3.1 Convention discovery

Test layout varies by project, so the mapping from source file to test file is derived per repository rather than hardcoded. For each repository, the verifier samples source files and checks which of the following layouts locates a matching test file most often:

- **sibling test package** — `pkg/sub/module.py` → `pkg/sub/tests/test_module.py`, or the `tests/` directory of the nearest enclosing package that has one (`lib/matplotlib/axes/_axes.py` → `lib/matplotlib/tests/test_axes.py`). astropy, scikit-learn, matplotlib.
- **mirrored tree** — `src/pkg/module.py` → `tests/pkg/test_module.py`, or a `tests/` tree that mirrors the inside of the package (`seaborn/_core/scales.py` → `tests/_core/test_scales.py`). seaborn.
- **suffix convention** — `module.py` → `module_test.py`
- **flat test directory** — `tests/test_module.py`, or the module path joined with underscores (`sphinx/ext/autodoc/__init__.py` → `tests/test_ext_autodoc.py`). sphinx.
- **tests tree** — `pkg/area/module.py` → `tests/<area>/test_module.py` with `<area>` free, or a per-app test package `tests/<package>_<module>/tests.py`. Django (`django/utils/dateformat.py` → `tests/utils_tests/test_dateformat.py`, `django/contrib/admin/checks.py` → `tests/admin_checks/tests.py`), pylint (`tests/lint/test_utils.py`). When a common name matches several test files, only those whose area shares a word with the source directory count; if none does, the match is ambiguous and is not a direct correspondence.

Across all layouts, `pkg/__init__.py` is the module `pkg`, and a private module `_axes.py` may be tested as `test_axes.py`.

**Sampling.** Source files are drawn at random across the whole tree (200 files, fixed seed 695, recorded in `configs/verifier/*.yaml`), not taken as a sorted prefix. A sorted prefix is what the repository keeps at the top of the alphabet — `benchmarks/` and `doc/` in scikit-learn, `ci/` and `galleries/` in matplotlib — and it scored every layout at zero on repositories whose own package plainly uses one.

**No floor.** The best-scoring layout wins, however low its score. There is no hit-rate threshold: a threshold is an arbitrary bar, and a layout that correctly locates the test for one file in ten is still the best available evidence of how the repository is laid out. Ties go to the layout listed first above, which is the more specific one. Only a repository where no layout locates any test file is marked `CONVENTION_UNKNOWN`, and selection falls through to Tier 2 only.

The winning layout, its hit rate, and every layout's hit rate are written to the verification record (`selection_convention`, `selection_convention_hit_rate`, `selection_convention_scores`), so a weak winner is visible for any instance after the fact.

**Validated against the pilot repositories (policy v1.1.0).** Under v1.0.0 (sorted 40-file prefix, 20% floor, first four layouts) discovery resolved on none of the ten `pilot_12` instances. On the nine with a patch, v1.1.0 resolves a layout that describes the repository on eight. The ninth is `psf/requests`, whose tests are one root-level `test_requests.py` that no module-level layout names. Tier 1 finds the real test file for every touched module that has one (six instances). For pylint and sphinx the layout is found but the touched module has no test file of its own. The base-tree file lists and the expected mappings are the fixtures in `tests/unit/test_selection_ground_truth.py`. The weakest winner is matplotlib (sibling, 9%), because most of its `.py` files are gallery examples.

### 3.1a Test-runner discovery

Which program executes the selected tests is also derived per repository, and recorded with the evidence that selected it. A module path handed to the wrong runner produces no results, which is an absence the verifier must not treat as a pass and must not paper over by guessing.

- **Django.** A tree that contains `tests/runtests.py` and a `django` package is run with `python tests/runtests.py`. Django does not collect tests under pytest. Labels are the dotted form of the node id (`utils_tests.test_dateformat.DateFormatTests.test_year`), which is what `runtests.py` accepts.
- **pytest.** A tree with `pytest.ini`, a root `conftest.py`, a `[tool.pytest]` section, a `[tool:pytest]` section, or a `tox.ini` that names pytest is run with `python -m pytest` on the node ids.
- **Otherwise pytest is the recorded default**, with evidence that no repo-specific runner was found. The default is a guess and is written as one.

### 3.2 Baseline pass

The selected tests are run **twice**: once against the unpatched base commit, once against the patched tree. Only tests that pass on the base and fail on the patch count as regressions.

This matters because repositories carry pre-existing failures — environment-dependent tests, skips that resolve differently, genuinely broken tests at that commit. Without a baseline, every such failure would be attributed to the candidate patch, inflating the rejection rate with noise and making the verifier look more discriminating than it is.

The baseline result is cached per instance. The base commit never changes, so the baseline is computed once and reused across verifier configurations and ablations.

### 3.3 Selection tiers

Tiers are evaluated in order and unioned. Selection stops when the time budget is projected to be exhausted. The unit of selection is a **node id**, not a file path.

A node id names one test function: `tests/pkg/test_compiler.py::test_as_sql`, or `tests/pkg/test_compiler.py::SQLCompilerTests::test_as_sql` when the function is a method. Tiers still locate files (by convention, by symbol, by package). Each file is then expanded to the `test_*` functions it defines, and only those ids are kept. A file that defines no test function contributes nothing — a bare module path is not a test the runner can execute, and selecting it produced empty results.

**Tier 0 — whole suite, if it fits.** If the repository's full test suite completes within budget on the baseline pass, run the full suite. More evidence is strictly better, and a suite that runs in two minutes should not be artificially narrowed. Observed oracle runs suggest this is feasible for several repositories in the pilot manifest. Off by default; available as an ablation.

**Tier 1 — direct correspondence.** For each non-test source file the patch modifies, locate its corresponding test file via the discovered convention, then the node ids in that file.

**Tier 2 — symbol reference.** Extract the names of functions, classes, and methods whose definitions the patch touches. Include any test file in the repository that references one of those names, expanded to node ids. Resolution is by import graph where the module can be parsed, falling back to textual match where it cannot.

"Touched" includes the enclosing definition git prints after the second `@@` of each hunk header (`@@ -771,10 +771,12 @@ class BaseModelAdminChecks:`). A change inside a method body usually names its class nowhere else in the diff, and until v1.1.0 such a patch contributed no symbol at all.

Tier 2 exists because Tier 1 misses the common case where behaviour lives in one module and is exercised from another — an ORM compiler change tested through a queryset test, for example. Naming convention alone would not find it.

**Tier 3 — containing package.** Run the full test package containing any Tier 1 or Tier 2 hit, if budget remains, again as node ids.

### 3.4 Budget

Five minutes wall-clock per pass, ten minutes per instance including baseline. Tests are ordered Tier 1 → 2 → 3 so that the highest-relevance tests run first and a budget cut removes the weakest evidence rather than an arbitrary slice. Within a tier, a file whose name contains a touched symbol (`DateFormat` → `test_dateformat.py`) runs before a file that merely mentions one, so a one-letter symbol such as `Y` does not consume the budget ahead of the test that is actually about the change.

Five minutes is chosen against the observed oracle evaluation times of 30–120 seconds per instance: generous enough to admit a full suite on most repositories in the manifest, bounded enough that verification cost stays well below repair cost and the whole study remains re-runnable.

**Observed limit (2026-09-30).** `scikit-learn-12973` selects 2387 node ids at Tier 2, and one pass executes about 1400 of them in five minutes; the rest end as `TIMEOUT`, which is not evidence either way. The budget cut falls on the weakest evidence, as designed, but a selection that wide means the regression signal is partial by construction. This is recorded rather than tuned: changing the budget or capping Tier 2 is a selection-policy change and needs a `policy_version` bump.

A working Tier 1 (v1.1.0) does not narrow these selections, because tiers are unioned: `django-14373` still selects 2649 ids, pulled in by the one-letter symbols `Y` and `z`, and `scikit-learn-12973` still selects 2387 through `fit`. What it changes is order. The 19 `test_dateformat` ids and the 28 `test_least_angle` ids are now Tier 1 and run first, so a budget cut can no longer fall on them. Narrowing Tier 2 itself (a minimum symbol length, or dropping Tier 2 when Tier 1 is non-empty) is a separate policy decision and is not made here.

**Execution.** Tests run through each image's own runner with no plugin assumed: pytest results are read from its `-v` lines, and the driver that runs inside the image must work on the oldest Python the images ship (3.6). If pytest aborts a batch because an id does not resolve, the batch is split so only the unresolvable id is lost; that id reads `NOT_RUN`. A runner that reports nothing records why, and is absence `error`, not `disabled`.

---

## 4. Outcome classification

Every selected test resolves to exactly one of:

| Outcome | Meaning |
|---|---|
| `PASS` | passed on base and on patch |
| `REGRESSION` | passed on base, failed on patch |
| `PRE_EXISTING_FAIL` | failed on base — excluded from the regression signal, recorded |
| `NEWLY_PASSING` | failed on base, passes on patch — recorded, not treated as proof of repair |
| `ERROR` | collection or import error, not a test failure |
| `TIMEOUT` | budget exhausted before completion |
| `NOT_RUN` | selected but never reached |

`NOT_RUN` and `TIMEOUT` are never counted as passes. A verifier that treats unexecuted tests as evidence of correctness would accept patches on the strength of work it did not do.

The regression signal passes only if the `REGRESSION` count is zero **and** at least one test actually executed. Zero tests run is `NOT_AVAILABLE`, which cannot produce `ACCEPT`.

### 4.1 Flake handling

Any test classified `REGRESSION` is re-run once in isolation. A test that passes on re-run is marked `FLAKY` and excluded from the regression signal, with the disagreement recorded. Rejecting a correct patch because of a nondeterministic test would land in the false-rejection rate and directly distort the risk–coverage curve.

---

## 5. Edge cases

**5.1 No tests discovered.** Recorded as `NOT_AVAILABLE`, never as a pass. Routes to `FLAG` rather than `ACCEPT`.

This is the designed outcome of the Tier 1 / Tier 2 cap, not a failure of the runner. `psf__requests-1921` is the concrete case: the patch changes `merge_setting` in `requests/sessions.py`, the repository's tests live in a single top-level `test_requests.py` that matches none of the layout conventions, and that file does not name `merge_setting`. Selection therefore returns nothing, and regression is `NOT_AVAILABLE`. Some repositories will yield that result however carefully the tiers are implemented. Tier 0, the whole suite, would have had tests to run here. It stays off by default (§8 question 1) and remains a config-only ablation.

**5.2 Patch touches only non-source files.** Documentation or configuration changes yield no Tier 1 or Tier 2 hits. Tier 3 does not apply. Result is `NOT_AVAILABLE`.

**5.3 Patch adds or modifies test files.** Tests authored or edited by the repair agent are excluded from the regression set entirely. They are the agent's own claim about correctness, not independent evidence, and admitting them would let the agent write its own acceptance criteria. Their existence is recorded as a risk feature for V1 and V5; deletion or weakening of pre-existing tests is an integrity failure, not a selection question.

**5.4 Patch fails to apply.** Selection does not run. The integrity check has already rejected.

**5.5 Baseline is catastrophically broken.** If more than half the selected tests fail on the base commit, the environment is suspect rather than the repository. Recorded as `BASELINE_UNRELIABLE` and routed to `FLAG`.

**5.6 Named failure mode: superseded assertion.** A correct patch that changes behaviour an existing test asserts will fail that test. The verifier reads the failure as a regression and rejects. The oracle does not see a regression, because before it runs anything it applies the gold test patch, which rewrites those assertions to the new behaviour. The verifier never applies the gold test patch and must not (§2). So from inside the constraint, "the patch broke an asserted behaviour" and "the patch correctly changed an asserted behaviour" are the same observation: a test that passed on the base commit and fails on the patch. Only the repository's future, which is the gold test patch, tells them apart.

This is structural to oracle-blind verification. It cannot be fixed from inside the constraint. Neither a better selection policy nor a better flake re-run (§4.1) removes it: the failure is real and deterministic, and the test is the right one to run. Excluding such tests would need exactly the information the verifier is forbidden. It is reported as a finding, not treated as a bug, and it bounds the false-rejection rate from below on any instance whose issue asks for a change in asserted behaviour. Error messages, defaults and output formats are the common cases.

The concrete case is `django__django-16899` in `pilot_13`. The patch changes the text of check `admin.E035` to name the offending field. `tests/admin_checks/tests.py::SystemChecksTestCase::test_nonexistent_field` and `::test_nonexistent_field_on_inline` assert the old text. Both pass on the base commit and fail on the patch, including when re-run one at a time. They are this instance's `FAIL_TO_PASS` tests, and the gold test patch updates their expected message. Verdicts: full verifier `REJECT` ("regression test failed"), oracle `resolved`. The agent's own claim stated the cause before submitting: running the unmodified `admin_checks` suite showed "only the 2 existing assertions that still expect the old message failing". The trajectory held information that the verifier's rules forbid it to use. The agent's account was the only evidence available that these failures were intended. The verifier cannot read it (it is the agent's claim about its own work, §5.3) and may not replace it with the oracle.

---

## 6. What this deliberately does not do

**It does not select tests by what the patch is trying to fix.** Reasoning about which behaviour the issue describes, and choosing tests accordingly, would make the selection an inference about correctness rather than a mechanical function of the patch. Issue-derived evidence belongs to V4, which is generated independently and measured separately, and keeping the two apart is what allows the ablation to attribute value to one or the other.

**It does not run the agent's own tests.** See §5.3.

**It does not adapt the selection based on results.** Widening the net after a failure, or narrowing it after a pass, would make the test set a function of the patch's behaviour and destroy the comparability of the signal across instances.

---

## 7. On overlap with `PASS_TO_PASS`

Any sufficiently broad selection will overlap the benchmark's `PASS_TO_PASS` set, and Tier 0 may overlap it substantially. This is worth stating plainly rather than leaving for a reader to notice.

The overlap is not leakage. Leakage is a question of information flow, not of set intersection: the policy above never reads the benchmark's test lists, and would produce the same selection if they did not exist. `PASS_TO_PASS` is itself derived from the repository's pre-existing tests, so a policy that runs pre-existing tests is expected to intersect it — that is the point of both.

What the overlap does affect is interpretation. SWE-bench resolution requires both `FAIL_TO_PASS` and `PASS_TO_PASS` to pass, so a verifier running a broad slice of the existing suite is approximating one half of the oracle's criterion while remaining genuinely blind to the other. Reported false-acceptance therefore reflects mostly the `FAIL_TO_PASS` dimension.

Checklist item 5.3 measures this overlap per instance and reports it. The measurement is made after the fact, from the oracle record, and is never fed back into selection.

---

## 8. Open questions for advisor

1. **Is Tier 0 the right default?** Running the whole suite where it fits maximises evidence and simplifies the policy, but makes the overlap with `PASS_TO_PASS` largest, and makes the verifier's regression signal least distinguishable from half the oracle. The alternative — capping at Tier 2 even when budget allows more — yields a weaker but more clearly independent signal. This trades evidential strength against interpretive cleanliness. The cost of the cap is visible: `psf__requests-1921` selects nothing under Tier 1 and Tier 2 (§5.1) and would have had a suite to run under Tier 0. The flag stays off; turning it on later is the ablation, not a bugfix.

2. **Is ten minutes per instance defensible**, or should verification cost be held to a fixed fraction of repair cost so that the ratio, rather than an absolute number, is what stays constant as models change?

3. **Is the single flake re-run sufficient**, given that flakiness enters the false-rejection rate directly? A best-of-three would be more robust and roughly doubles the cost of the failure path only.

4. **Should `NEWLY_PASSING` feed the accept decision at all?** It is currently recorded but unused. A pre-existing test that starts passing after the patch is weak evidence of repair, and admitting it would blur the boundary with V4's issue-derived signal — but discarding it may waste real information.
