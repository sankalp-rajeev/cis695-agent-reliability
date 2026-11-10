# Why the six historical grader witnesses pass in Phase 4

Five Pylint witnesses were **SKIPPED**, not failed assertions, in the archived official grader output. Docker CPU shares explain the change from SKIPPED to PASS. The Django witness failed on a **different candidate patch** in the archived grader log. Its frozen candidate passes with and without the official test patch. The Matplotlib control fails in both the archived grader and the sealed patched tree.

This is analysis after `phase4-run-sealed`. Executor sources, sealed results, labels, tags, and the original artifacts are unchanged. The sealed directory was reverified against all 1,799 manifest entries before this analysis. Twelve official-harness invocations each selected exactly one test; three further containers only measured resources. No full-suite or full-benchmark rerun was performed.

## Per-test classification

| Task | Test | Historical native status | Frozen candidate with / without test_patch | Sealed patched | Classification |
|---|---|---|---|---|---|
| django__django-13297 | `test_template_params_warning` | FAIL | PASS / PASS | PASSED | OTHER |
| matplotlib__matplotlib-25479 | `test_register_cmap` | FAIL | not rerun; control already agrees | FAILED | OTHER |
| pylint-dev__pylint-6528 | `test_custom_should_analyze_file` | SKIPPED | SKIPPED / SKIPPED | PASSED | ENVIRONMENT |
| pylint-dev__pylint-6528 | `test_multiprocessing[1]` | SKIPPED | SKIPPED / SKIPPED | PASSED | ENVIRONMENT |
| pylint-dev__pylint-6528 | `test_multiprocessing[2]` | SKIPPED | SKIPPED / SKIPPED | PASSED | ENVIRONMENT |
| pylint-dev__pylint-6528 | `test_jobs_score` | SKIPPED | SKIPPED / SKIPPED | PASSED | ENVIRONMENT |
| pylint-dev__pylint-7277 | `test_jobs_score` | SKIPPED | SKIPPED / SKIPPED | PASSED | ENVIRONMENT |

**Ceiling:** 4 of 14 incorrect patches (28.6%) have any pre-existing test in the historical grader’s failure bucket. That bucket includes five CPU skips and a Django candidate-binding mismatch; it is not evidence that four frozen candidates have old tests that fail assertions. No test is causally classified TEST_PATCH_CHANGED, and no gap remains GRADER_ONLY_FAILURE_UNEXPLAINED under the evidence below.

## Test-patch comparison

The cached SWE-bench Verified revision is `78f471bf655a3137b2e8a75af1501690ec009ec3`. Every cached `test_patch` matches the archived grader’s applied test-patch heredoc after stripping trailing newlines. Base sources are the exact hash-pinned task archives from the sealed launch plan. The evidence JSON records archive, oracle, source-scope, helper/fixture, and log hashes. The comparison applies only `test_patch` to isolated copies; it never applies the gold solution. All seven target function bodies **including decorators** are byte-identical before/after. Every test’s file is nevertheless touched.

- Pylint 6528: the oracle adds recursive-ignore tests and an unused ignored-subdirectory fixture. `_CustomPyLinter`, the CPU collection hook, scoring helpers, and all fixtures read by the targets are unchanged. The full `TestRunTC` class gains unrelated methods/docstrings, shown below; jobs_score itself is unchanged.
- Pylint 7277: the oracle extends `test_modify_sys_path`; jobs_score, its helper chain, its unused_variable.py fixture, CPU query, and collection guard are unchanged.
- Django 13297: the oracle changes the enclosing class from SimpleTestCase to TestCase, adds a RequestFactory and a new filtering test. The warning method and warning assertion helpers are unchanged. This is different enclosing test code, but the paired replay shows that it does not cause the gap for the frozen candidate.
- Matplotlib 25479: the oracle changes sibling colormap-equality expectations and adds a mismatched-name test. test_register_cmap and its test infrastructure are unchanged. It has no explicit fixture arguments and exercises the same colormap APIs in both versions.

### django__django-13297

| Target scope | Before lines | After lines | Scope SHA-256 (same in both) |
|---|---|---|---|
| `tests/generic_views/test_base.py::DeprecationTests::test_template_params_warning` | 593–605 | 597–609 | `32f4f9f54835496a545d4a05d2b80d006c920946d3fb2f58fc0d7cc38c74b253` |

Enclosing class diff (`tests/generic_views/test_base.py:DeprecationTests`):

```diff
--- pre-existing/tests/generic_views/test_base.py:DeprecationTests
+++ test_patch/tests/generic_views/test_base.py:DeprecationTests
@@ -1,5 +1,7 @@
 @override_settings(ROOT_URLCONF='generic_views.urls')
-class DeprecationTests(SimpleTestCase):
+class DeprecationTests(TestCase):
+    rf = RequestFactory()
+
     @ignore_warnings(category=RemovedInDjango40Warning)
     def test_template_params(self):
         """A generic template view passes kwargs as context."""
@@ -31,3 +33,17 @@
             str(response.context['foo2'])
         self.assertEqual(response.context['key'], 'value')
         self.assertIsInstance(response.context['view'], View)
+
+    @ignore_warnings(category=RemovedInDjango40Warning)
+    def test_template_params_filtering(self):
+        class ArtistView(TemplateView):
+            template_name = 'generic_views/about.html'
+
+            def get_context_data(self, *, artist_name, **kwargs):
+                context = super().get_context_data(**kwargs)
+                artist = Artist.objects.get(name=artist_name)
+                return {**context, 'artist': artist}
+
+        artist = Artist.objects.create(name='Rene Magritte')
+        response = ArtistView.as_view()(self.rf.get('/'), artist_name=artist.name)
+        self.assertEqual(response.context_data['artist'], artist)
```

Compared helpers/fixtures (whole-file hashes or named scopes in evidence.json):

`django/test/client.py`; `django/test/testcases.py`; `django/test/utils.py`; `django/utils/deprecation.py`; `tests/generic_views/models.py`; `tests/generic_views/templates/generic_views/about.html`; `tests/generic_views/urls.py`; `tests/generic_views/views.py`; `tests/runtests.py`; `tests/test_sqlite.py`.

Named helper comparisons: `DeprecationTests` changed (diff above), `SimpleTestCase.assertRaisesMessage` identical, `SimpleTestCase._assert_raises_or_warns_cm` identical.
### matplotlib__matplotlib-25479

| Target scope | Before lines | After lines | Scope SHA-256 (same in both) |
|---|---|---|---|
| `lib/matplotlib/tests/test_colors.py::test_register_cmap` | 75–117 | 75–117 | `0b765fa45cba5c5ca2eed2c8ab1ac2388a7d585bbcabec29f79662e1f4101720` |

Compared helpers/fixtures (whole-file hashes or named scopes in evidence.json):

`lib/matplotlib/testing/__init__.py`; `lib/matplotlib/testing/conftest.py`; `lib/matplotlib/testing/decorators.py`; `lib/matplotlib/tests/conftest.py`; `pytest.ini`; `setup.cfg`.
### pylint-dev__pylint-6528

| Target scope | Before lines | After lines | Scope SHA-256 (same in both) |
|---|---|---|---|
| `tests/lint/unittest_lint.py::test_custom_should_analyze_file` | 774–798 | 774–798 | `4c1aada4f10466aa5e743892e3dc78ea2b6a5c6bbb6af59c805c6036aad68e8c` |
| `tests/lint/unittest_lint.py::test_multiprocessing[1]` | 803–831 | 803–831 | `4fc3bbb1eec49a6fc02184801d8b56f0beee898871ce2cb2e136616205c7fe51` |
| `tests/lint/unittest_lint.py::test_multiprocessing[2]` | 803–831 | 803–831 | `4fc3bbb1eec49a6fc02184801d8b56f0beee898871ce2cb2e136616205c7fe51` |
| `tests/test_self.py::TestRunTC::test_jobs_score` | 1050–1054 | 1050–1054 | `2dbfaf2fbc5a44af6a3a85928b84d7ba885eaa4c1b284a9b934ef56cc389311f` |

Enclosing class diff (`tests/test_self.py:TestRunTC`):

```diff
--- pre-existing/tests/test_self.py:TestRunTC
+++ test_patch/tests/test_self.py:TestRunTC
@@ -1105,14 +1105,88 @@
         assert not ex.value.code % 2

     def test_regression_recursive(self):
+        """Tests if error is raised when linter is executed over directory not using --recursive=y"""
         self._test_output(
             [join(HERE, "regrtest_data", "directory", "subdirectory"), "--recursive=n"],
             expected_output="No such file or directory",
         )

     def test_recursive(self):
+        """Tests if running linter over directory using --recursive=y"""
         self._runtest(
             [join(HERE, "regrtest_data", "directory", "subdirectory"), "--recursive=y"],
+            code=0,
+        )
+
+    def test_ignore_recursive(self):
+        """Tests recursive run of linter ignoring directory using --ignore parameter.
+
+        Ignored directory contains files yielding lint errors. If directory is not ignored
+        test would fail due these errors.
+        """
+        self._runtest(
+            [
+                join(HERE, "regrtest_data", "directory"),
+                "--recursive=y",
+                "--ignore=ignored_subdirectory",
+            ],
+            code=0,
+        )
+
+        self._runtest(
+            [
+                join(HERE, "regrtest_data", "directory"),
+                "--recursive=y",
+                "--ignore=failing.py",
+            ],
+            code=0,
+        )
+
+    def test_ignore_pattern_recursive(self):
+        """Tests recursive run of linter ignoring directory using --ignore-parameter parameter.
+
+        Ignored directory contains files yielding lint errors. If directory is not ignored
+        test would fail due these errors.
+        """
+        self._runtest(
+            [
+                join(HERE, "regrtest_data", "directory"),
+                "--recursive=y",
+                "--ignore-pattern=ignored_.*",
+            ],
+            code=0,
+        )
+
+        self._runtest(
+            [
+                join(HERE, "regrtest_data", "directory"),
+                "--recursive=y",
+                "--ignore-pattern=failing.*",
+            ],
+            code=0,
+        )
+
+    def test_ignore_path_recursive(self):
+        """Tests recursive run of linter ignoring directory using --ignore-path parameter.
+
+        Ignored directory contains files yielding lint errors. If directory is not ignored
+        test would fail due these errors.
+        """
+        self._runtest(
+            [
+                join(HERE, "regrtest_data", "directory"),
+                "--recursive=y",
+                "--ignore-path=.*ignored.*",
+            ],
+            code=0,
+        )
+
+        self._runtest(
+            [
+                join(HERE, "regrtest_data", "directory"),
+                "--recursive=y",
+                "--ignore-path=.*failing.*",
+            ],
             code=0,
         )

@@ -1126,7 +1200,7 @@
                 if not os.path.basename(path) == "regrtest_data"
             ]
             with _test_cwd():
-                os.chdir(join(HERE, "regrtest_data", "directory"))
+                os.chdir(join(HERE, "regrtest_data", "directory", "subdirectory"))
                 self._runtest(
                     [".", "--recursive=y"],
                     code=0,
```

Compared helpers/fixtures (whole-file hashes or named scopes in evidence.json):

`pylint/lint/run.py`; `pylint/reporters/__init__.py`; `pylint/testutils/__init__.py`; `pylint/testutils/_run.py`; `pylint/testutils/lint_module_test.py`; `pylint/testutils/reporter_for_tests.py`; `pylint/testutils/testing_pylintrc`; `pylint/testutils/utils.py`; `pylintrc`; `setup.cfg`; `tests/conftest.py`; `tests/regrtest_data/bad_package/__init__.py`; `tests/regrtest_data/bad_package/wrong.py`; `tests/regrtest_data/special_attr_scope_lookup_crash.py`; `tests/regrtest_data/syntax_error.py`; `tests/regrtest_data/unused_variable.py`; `tests/regrtest_data/wildcard.py`; `tests/regrtest_data/wrong_import_position.py`.

Named helper comparisons: `TestRunTC` changed (diff above), `TestRunTC._run_pylint` identical, `TestRunTC._clean_paths` identical, `TestRunTC._test_output` identical, `pytest_collection_modifyitems` identical, `_query_cpu` identical, `_cpu_count` identical, `_CustomPyLinter` identical.
### pylint-dev__pylint-7277

| Target scope | Before lines | After lines | Scope SHA-256 (same in both) |
|---|---|---|---|
| `tests/test_self.py::TestRunTC::test_jobs_score` | 909–913 | 927–931 | `2dbfaf2fbc5a44af6a3a85928b84d7ba885eaa4c1b284a9b934ef56cc389311f` |

Enclosing class diff (`tests/test_self.py:TestRunTC`):

```diff
--- pre-existing/tests/test_self.py:TestRunTC
+++ test_patch/tests/test_self.py:TestRunTC
@@ -648,6 +648,24 @@
                 modify_sys_path()
             assert sys.path == paths[1:]

+            paths = ["", *default_paths]
+            sys.path = copy(paths)
+            with _test_environ_pythonpath():
+                modify_sys_path()
+            assert sys.path == paths[1:]
+
+            paths = [".", *default_paths]
+            sys.path = copy(paths)
+            with _test_environ_pythonpath():
+                modify_sys_path()
+            assert sys.path == paths[1:]
+
+            paths = ["/do_not_remove", *default_paths]
+            sys.path = copy(paths)
+            with _test_environ_pythonpath():
+                modify_sys_path()
+            assert sys.path == paths
+
             paths = [cwd, cwd, *default_paths]
             sys.path = copy(paths)
             with _test_environ_pythonpath("."):
```

Compared helpers/fixtures (whole-file hashes or named scopes in evidence.json):

`pylint/lint/run.py`; `pylint/reporters/__init__.py`; `pylint/testutils/__init__.py`; `pylint/testutils/_run.py`; `pylint/testutils/lint_module_test.py`; `pylint/testutils/reporter_for_tests.py`; `pylint/testutils/testing_pylintrc`; `pylint/testutils/utils.py`; `pylintrc`; `pyproject.toml`; `setup.cfg`; `tests/conftest.py`; `tests/regrtest_data/special_attr_scope_lookup_crash.py`; `tests/regrtest_data/syntax_error.py`; `tests/regrtest_data/unused_variable.py`; `tests/regrtest_data/wildcard.py`; `tests/regrtest_data/wrong_import_position.py`.

Named helper comparisons: `TestRunTC` changed (diff above), `TestRunTC._run_pylint` identical, `TestRunTC._clean_paths` identical, `TestRunTC._test_output` identical, `pytest_collection_modifyitems` identical, `_query_cpu` identical, `_cpu_count` identical.

## Archived official grader evidence

All four official report/log sets exist behind the label sidecars. `evidence.json` records their absolute paths and SHA-256 digests, and preserves the report buckets separately from native test status. A fresh partial-task harness report is not a replacement task label. Historical exact cgroup counters, os.cpu_count, PYTHONHASHSEED values, and the live warning-filter list were not logged. Absence of an export is reported as absence of evidence, not proof of a historical environment value.

### django__django-13297

Log directory: `/home/sankalp/projects/cis695-agent-reliability/logs/run_evaluation/main_50_b__django__django-13297/deepseek_deepseek-v4-flash/django__django-13297`.

Exact recorded test command:

```sh
./tests/runtests.py --verbosity 2 --settings=test_sqlite --parallel 1 generic_views.test_base
```

Recorded setup:

```sh
source /opt/miniconda3/bin/activate
conda activate testbed
sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
source /opt/miniconda3/bin/activate
conda activate testbed
python -m pip install -e .
export LANG=en_US.UTF-8
export LANGUAGE=en_US:en
export LC_ALL=en_US.UTF-8
```

Recorded versions: Python 3.6 paths in the Django traceback; no pytest header.

Native evidence (`test_output.txt` line numbers):

- L430: `test_template_params_warning (generic_views.test_base.DeprecationTests) ... FAIL`
- L503: `FAIL: test_template_params_warning (generic_views.test_base.DeprecationTests)`
- L506: `File "/testbed/tests/generic_views/test_base.py", line 605, in test_template_params_warning`
- L512: `AssertionError: RemovedInDjango40Warning not raised`

Frozen candidate SHA-256: `69181c9a98281a325159813f1b8a53aa13bf3dd5bb8bd375894c1d344a9cdc85`.
Archived applied candidate SHA-256: `25022237ebec1e6eb372fa015fabd303550f8ab77d773d81e0e3fc050397fc68`. Match: **False**.

### matplotlib__matplotlib-25479

Log directory: `/home/sankalp/projects/cis695-agent-reliability/logs/run_evaluation/main_50_b__matplotlib__matplotlib-25479/deepseek_deepseek-v4-flash/matplotlib__matplotlib-25479`.

Exact recorded test command:

```sh
pytest -rA lib/matplotlib/tests/test_colors.py
```

Recorded setup:

```sh
source /opt/miniconda3/bin/activate
conda activate testbed
source /opt/miniconda3/bin/activate
conda activate testbed
python -m pip install -e .
```

Recorded versions: platform linux -- Python 3.11.11, pytest-8.3.4, pluggy-1.5.0 / plugins: xdist-3.6.1, timeout-2.3.1, rerunfailures-15.0, cov-6.0.0

Native evidence (`test_output.txt` line numbers):

- L414: `______________________________ test_register_cmap ______________________________`
- L416: `def test_register_cmap():`
- L424: `>       assert mpl.colormaps[target] == new_cm`
- L745: `FAILED lib/matplotlib/tests/test_colors.py::test_register_cmap - assert <matp...`

Frozen candidate SHA-256: `5cabaa4a2bc80de34b9ca6c49c1ebbba00cb7be597b5dce3f3c0c3e0519c7740`.
Archived applied candidate SHA-256: `5cabaa4a2bc80de34b9ca6c49c1ebbba00cb7be597b5dce3f3c0c3e0519c7740`. Match: **True**.

### pylint-dev__pylint-6528

Log directory: `/home/sankalp/projects/cis695-agent-reliability/logs/run_evaluation/main_50_a__pylint-dev__pylint-6528/deepseek_deepseek-v4-flash/pylint-dev__pylint-6528`.

Exact recorded test command:

```sh
pytest -rA tests/lint/unittest_lint.py tests/regrtest_data/directory/ignored_subdirectory/failing.py tests/test_self.py
```

Recorded setup:

```sh
source /opt/miniconda3/bin/activate
conda activate testbed
source /opt/miniconda3/bin/activate
conda activate testbed
python -m pip install -e .
```

Recorded versions: platform linux -- Python 3.9.20, pytest-7.4.4, pluggy-1.5.0 / plugins: xdist-2.5.0, benchmark-3.4.1, cov-3.0.0, forked-1.6.0, profiling-1.7.0, timeout-2.3.1

Native evidence (`test_output.txt` line numbers):

- L1951: `SKIPPED [1] tests/lint/unittest_lint.py:774: Need 2 or more cores for test to be meaningful`
- L1952: `SKIPPED [2] tests/lint/unittest_lint.py:803: Need 2 or more cores for test to be meaningful`
- L1953: `SKIPPED [1] tests/test_self.py:1050: Need 2 or more cores for test to be meaningful`

Frozen candidate SHA-256: `f7e4f6955ed10efc5cdc95faefd807bbbc63dff78ad28818c52c14115b111d0d`.
Archived applied candidate SHA-256: `f7e4f6955ed10efc5cdc95faefd807bbbc63dff78ad28818c52c14115b111d0d`. Match: **True**.

### pylint-dev__pylint-7277

Log directory: `/home/sankalp/projects/cis695-agent-reliability/logs/run_evaluation/main_50_a__pylint-dev__pylint-7277/deepseek_deepseek-v4-flash/pylint-dev__pylint-7277`.

Exact recorded test command:

```sh
pytest -rA tests/test_self.py
```

Recorded setup:

```sh
source /opt/miniconda3/bin/activate
conda activate testbed
source /opt/miniconda3/bin/activate
conda activate testbed
python -m pip install -e .
```

Recorded versions: platform linux -- Python 3.9.20, pytest-7.4.4, pluggy-1.5.0 / plugins: xdist-2.5.0, cov-3.0.0, forked-1.6.0, profiling-1.7.0, timeout-2.3.1, benchmark-4.0.0

Native evidence (`test_output.txt` line numbers):

- L1851: `SKIPPED [1] tests/test_self.py:927: Need 2 or more cores for test to be meaningful`

Frozen candidate SHA-256: `b8f25fcc32031c547c2a6856c78518f6dfe20256924f232c4d6b06fda2fb6e1f`.
Archived applied candidate SHA-256: `b8f25fcc32031c547c2a6856c78518f6dfe20256924f232c4d6b06fda2fb6e1f`. Match: **True**.

## The Django binding mismatch

The frozen 1,770-byte candidate is also the patch in the original repair record/prediction and the hash declared by oracle_record.json. The official grader directory instead contains a 4,454-byte patch; run_instance.log records applying that patch. The archived patch removes the warning machinery, while the frozen patch retains it and wraps kwargs after get_context_data. The target requires RemovedInDjango40Warning to be raised when the context values are read. Its archived failure, “RemovedInDjango40Warning not raised”, follows directly from removing that machinery. The original label stays unchanged; this report does not claim the archived failure belongs to the frozen patch.

This is classified **OTHER: evaluated candidate differs**. The official single-test pair on the frozen incorrect-labelled candidate returns PASS with and without test_patch, so neither the class-base change nor warning flags is required to explain the observed agreement in those replays.

Candidate patch-text difference (not a new candidate or a committed patch file):

```diff
--- frozen-candidate/candidate-patch-text
+++ archived-grader-candidate/candidate-patch-text
@@ -1,41 +1,117 @@
 diff --git a/django/views/generic/base.py b/django/views/generic/base.py
-index ea5baca08d..2462b46672 100644
+index ea5baca08d..07bcb189fb 100644
 --- a/django/views/generic/base.py
 +++ b/django/views/generic/base.py
-@@ -157,17 +157,19 @@ class TemplateResponseMixin:
+@@ -1,5 +1,4 @@
+ import logging
+-import warnings
+ from functools import update_wrapper
+
+ from django.core.exceptions import ImproperlyConfigured
+@@ -10,8 +9,6 @@ from django.http import (
+ from django.template.response import TemplateResponse
+ from django.urls import reverse
+ from django.utils.decorators import classonlymethod
+-from django.utils.deprecation import RemovedInDjango40Warning
+-from django.utils.functional import SimpleLazyObject
+
+ logger = logging.getLogger('django.request')
+
+@@ -156,32 +153,12 @@ class TemplateResponseMixin:
+
  class TemplateView(TemplateResponseMixin, ContextMixin, View):
      """Render a template."""
++
      def get(self, request, *args, **kwargs):
 -        # RemovedInDjango40Warning: when the deprecation ends, replace with:
 -        #   context = self.get_context_data()
 -        context_kwargs = _wrap_url_kwargs_with_deprecation_warning(kwargs)
 -        context = self.get_context_data(**context_kwargs)
 +        context = self.get_context_data(**kwargs)
-+        # RemovedInDjango40Warning: when the deprecation ends, remove the
-+        # _wrap_url_kwargs_with_deprecation_warning() call.
-+        context = _wrap_url_kwargs_with_deprecation_warning(kwargs, context)
          return self.render_to_response(context)


- # RemovedInDjango40Warning
+-# RemovedInDjango40Warning
 -def _wrap_url_kwargs_with_deprecation_warning(url_kwargs):
 -    context_kwargs = {}
-+def _wrap_url_kwargs_with_deprecation_warning(url_kwargs, context):
-     for key, value in url_kwargs.items():
-+        # Don't override values set by a subclass in get_context_data().
-+        if context.get(key, value) is not value:
-+            continue
-         # Bind into function closure.
-         @SimpleLazyObject
-         def access_value(key=key, value=value):
-@@ -178,8 +180,8 @@ def _wrap_url_kwargs_with_deprecation_warning(url_kwargs):
-                 RemovedInDjango40Warning, stacklevel=2,
-             )
-             return value
+-    for key, value in url_kwargs.items():
+-        # Bind into function closure.
+-        @SimpleLazyObject
+-        def access_value(key=key, value=value):
+-            warnings.warn(
+-                'TemplateView passing URL kwargs to the context is '
+-                'deprecated. Reference %s in your template through '
+-                'view.kwargs instead.' % key,
+-                RemovedInDjango40Warning, stacklevel=2,
+-            )
+-            return value
 -        context_kwargs[key] = access_value
 -    return context_kwargs
-+        context[key] = access_value
-+    return context
+-
+-
+ class RedirectView(View):
+     """Provide a redirect on any GET request."""
+     permanent = False
+diff --git a/docs/internals/deprecation.txt b/docs/internals/deprecation.txt
+index 1f1364897e..46a1aaaee6 100644
+--- a/docs/internals/deprecation.txt
++++ b/docs/internals/deprecation.txt
+@@ -98,9 +98,6 @@ details on these changes.

+ * The ``list`` message for ``ModelMultipleChoiceField`` will be removed.

- class RedirectView(View):
+-* ``django.views.generic.TemplateView`` will no longer pass URL kwargs directly
+-  to the ``context``.
+-
+ * Support for passing raw column aliases to ``QuerySet.order_by()`` will be
+   removed.
+
+diff --git a/docs/ref/class-based-views/base.txt b/docs/ref/class-based-views/base.txt
+index de45ae3a5e..7906c56846 100644
+--- a/docs/ref/class-based-views/base.txt
++++ b/docs/ref/class-based-views/base.txt
+@@ -117,7 +117,8 @@ MRO is an acronym for Method Resolution Order.
+
+ .. class:: django.views.generic.base.TemplateView
+
+-    Renders a given template.
++    Renders a given template, with the context containing parameters captured
++    in the URL.
+
+     **Ancestors (MRO)**
+
+@@ -161,17 +162,12 @@ MRO is an acronym for Method Resolution Order.
+
+     **Context**
+
+-    * Populated (through :class:`~django.views.generic.base.ContextMixin`).
++    * Populated (through :class:`~django.views.generic.base.ContextMixin`) with
++      the keyword arguments captured from the URL pattern that served the view.
+     * You can also add context using the
+       :attr:`~django.views.generic.base.ContextMixin.extra_context` keyword
+       argument for :meth:`~django.views.generic.base.View.as_view`.
+
+-    .. deprecated:: 3.1
+-
+-        Starting in Django 4.0, the keyword arguments captured from the URL
+-        pattern won't be passed to the context. Reference them with
+-        ``view.kwargs`` instead.
+-
+ ``RedirectView``
+ ================
+
+diff --git a/docs/releases/3.1.txt b/docs/releases/3.1.txt
+index f44bef411d..a37fa2b9fb 100644
+--- a/docs/releases/3.1.txt
++++ b/docs/releases/3.1.txt
+@@ -794,10 +794,6 @@ Miscellaneous
+ * The ``list`` message for :class:`~django.forms.ModelMultipleChoiceField` is
+   deprecated in favor of ``invalid_list``.
+
+-* The passing of URL kwargs directly to the context by
+-  :class:`~django.views.generic.base.TemplateView` is deprecated. Reference
+-  them in the template with ``view.kwargs`` instead.
+-
+ * Passing raw column aliases to :meth:`.QuerySet.order_by` is deprecated. The
+   same result can be achieved by passing aliases in a
+   :class:`~django.db.models.expressions.RawSQL` instead beforehand.
```

## Fresh official harness and environment comparison

Installed SWE-bench **5.0.2** entry points `make_test_spec` and `run_instance` were called directly. Six relevant installed modules match their distribution RECORD hashes (recorded in evidence.json). Each pair differs only in applying the official test_patch. The suite command is narrowed to one exact node; image tags are replaced with the immutable image IDs used at seal; a read-only environment probe is inserted before the test-output marker. The historical locale/setup commands and all test-command flags are preserved. Each invocation uses a fresh container with the official default resource profile. No native skip guard is overridden.

The replay logs retain the full original task FAIL_TO_PASS/PASS_TO_PASS references, so their task-resolution reports are intentionally partial and are **not new labels**. In all-skipped single-test Pylint runs, the parser can return no PASS/FAIL entries and leave patch_successfully_applied false; run_instance.log explicitly proves candidate application succeeded. Pylint 6528’s stock final git checkout also mentions the newly added fixture path absent from the base tree; its pathspec diagnostic occurs after the test and is not an assertion failure.

| Task/profile | os.cpu_count / affinity | cgroup cpu.shares | cpu.max | Pylint _query_cpu / _cpu_count | PYTHONHASHSEED / PYTHONWARNINGS |
|---|---|---|---|---|---|
| pylint-dev__pylint-6528 / official default (measured now) | 16 / 16 | 1024 | absent (cgroup v1) | 1 / 1 | None / None |
| pylint-dev__pylint-6528 / executor resource profile (measured now) | 16 / 16 | 2048 | absent (cgroup v1) | 2 / 2 | None / None |
| pylint-dev__pylint-7277 / official default (measured now) | 16 / 16 | 1024 | absent (cgroup v1) | 1 / 1 | None / None |
| pylint-dev__pylint-7277 / executor resource profile (measured now) | 16 / 16 | 2048 | absent (cgroup v1) | 2 / 2 | None / None |
| django__django-13297 / official default (measured now) | 16 / 16 | 1024 | absent (cgroup v1) | n/a / n/a | None / None |
| django__django-13297 / executor resource profile (measured now) | 16 / 16 | 2048 | absent (cgroup v1) | n/a / n/a | None / None |

These are current replay measurements, not a reconstruction of unlogged historical counters. The archived skip message plus the unchanged `_cpu_count() < 2` guard proves why the historical Pylint tests did not run. On cgroup v1, Pylint uses int(cpu.shares / 1024) when quota is unlimited, even though shares express scheduling weight rather than a CPU-count limit. Our executor’s 2048 shares therefore make its query return 2 instead of 1; the sealed captures show all five tests actually PASS.

Warning/flag comparison:

- Official Pylint: `pytest -rA <one node>`; sealed executor: `python -m pytest -p no:cacheprovider -v -- <selected IDs>`. Neither adds -W or xdist parallel flags. The tests themselves retain jobs=1/2, and jobs_score explicitly passes `--jobs=2 -ry`; its helper ignores warnings inside a catch_warnings block in both source versions.
- Official Django: `./tests/runtests.py --verbosity 2 --settings=test_sqlite --parallel 1 <one dotted test>`. Sealed executor: `python tests/runtests.py --verbosity=2 <dotted selections>`; this task’s frozen django_parallel_one is false, so no explicit --parallel is added. The unchanged runner defaults to --parallel=0 (automatic), sets DJANGO_SETTINGS_MODULE to test_sqlite unless already provided, and promotes RemovedInDjango40Warning/41Warning, ResourceWarning and RuntimeWarning to errors. These source filter rules apply on both paths; the target uses assertRaisesMessage on the warning category. No explicit -W or -p flag is used on either Django path.
- Official Matplotlib command has only -rA. Its sealed executor uses the same pytest flag pattern as Pylint. The archived and sealed target failures agree; no extra replay was needed for this control.
- Fresh interpreter startup warning filters, sys.warnoptions, exact cgroup quota/period files, image IDs, Python versions and the two allowlisted environment values are recorded for each replay/probe in evidence.json. These are startup probes, not a claim to have captured the live pytest/Django in-test filter stack. Project warning configuration is preserved there; the Django assertion uses the identical assertRaisesMessage helper, so helper-induced warning differences are ruled out. Historical in-test warning filters were not recorded.

## Reproduction and limits

From the project root, `env -u PYTHONPATH .venv/bin/python reports/next_phases/phase4_posthoc/grader_gap/analyze.py` regenerates the report and CSV without executing tests. `replay.py --execute` is a separate explicit twelve-invocation diagnostic and refuses to overwrite existing logs. Raw logs and oracle inputs stay in ignored `runs/phase4_grader_gap/`; no runs/, logs/, or *.patch file is committed. Full archived logs, rather than a newly inferred grader status, support all historical statements.

The report explains the six observed gaps. It does not establish that the frozen Django candidate is correct, that old tests cover the benchmark’s new behavior, or that the historical task label can be transferred across different patch bytes. The two incorrect-labelled Pylint candidates pass these unchanged CPU-enabled old tests; recursive-ignore/sys.path behavior is outside these witnesses. Their grader-derived labels do not, by themselves, prove a semantic bug in those candidates, particularly when the report failures are skips. The Matplotlib old test remains a useful assertion-failure control.
