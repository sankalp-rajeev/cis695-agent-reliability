POST-HOC ANALYSIS ONLY. Uses oracle fields (FAIL_TO_PASS, PASS_TO_PASS, gold patch, test_patch). Must never feed back into any run.

# pylint-dev__pylint-6528  group=group2_false_flag  run=main_50_a
## ISSUE
Pylint does not respect ignores in `--recursive=y` mode
### Bug description

Pylint does not respect the `--ignore`, `--ignore-paths`, or `--ignore-patterns` setting when running in recursive mode. This contradicts the documentation and seriously compromises the usefulness of recursive mode.

### Configuration

_No response_

### Command used

```shell
### .a/foo.py
# import re

### bar.py
# import re

pylint --recursive=y .
pylint --recursive=y --ignore=.a .
pylint --recursive=y --ignore-paths=.a .
pylint --recursive=y --ignore-patterns="^\.a" .
```


### Pylint output

All of these commands give the same output:

```
************* Module bar
bar.py:1:0: C0104: Disallowed name "bar" (disallowed-name)
bar.py:1:0: C0114: Missing module docstring (missing-module-docstring)
bar.py:1:0: W0611: Unused import re (unused-import)
************* Module foo
.a/foo.py:1:0: C0104: Disallowed name "foo" (disallowed-name)
.a/foo.py:1:0: C0114: Missing module docstring (missing-module-docstring)
.a/foo.py:1:0: W0611: Unused import re (unused-import)
```


### Expected behavior

`foo.py` should be ignored by all of the above commands, because it is in an ignored directory (even the first command with no ignore setting should skip it, since the default value of `ignore-patterns` is `"^\."`.

For reference, the docs for the various ignore settings from `pylint --help`:

```
    --ignore=<file>[,<file>...]
                        Files or directories to be skipped. They should be
                        base names, not paths. [current: CVS]
    --ignore-patterns=<pattern>[,<pattern>...]
                        Files or directories matching the regex patterns are
                        skipped. The regex matches against base names, not
                        paths. The default value ignores emacs file locks
                        [current: ^\.#]
    --ignore-paths=<pattern>[,<pattern>...]
                        Add files or directories matching the regex patterns
                        to the ignore-list. The regex matches against paths
                        and can be in Posix or Windows format. [current: none]
```

### Pylint version

```shell
pylint 2.13.7
python 3.9.12
```


### OS / Environment

_No response_

### Additional dependencies

_No response_


## AGENT PATCH
diff --git a/pylint/lint/expand_modules.py b/pylint/lint/expand_modules.py
index b20cd873..50747146 100644
--- a/pylint/lint/expand_modules.py
+++ b/pylint/lint/expand_modules.py
@@ -46,6 +46,21 @@ def _is_in_ignore_list_re(element: str, ignore_list_re: list[Pattern[str]]) -> b
     return any(file_pattern.match(element) for file_pattern in ignore_list_re)
 
 
+def _is_ignored_file(
+    element: str,
+    ignore_list: list[str],
+    ignore_list_re: list[Pattern[str]],
+    ignore_list_paths_re: list[Pattern[str]],
+) -> bool:
+    element = os.path.normpath(element)
+    basename = os.path.basename(element)
+    return (
+        basename in ignore_list
+        or _is_in_ignore_list_re(basename, ignore_list_re)
+        or _is_in_ignore_list_re(element, ignore_list_paths_re)
+    )
+
+
 def expand_modules(
     files_or_modules: Sequence[str],
     ignore_list: list[str],
@@ -61,10 +76,8 @@ def expand_modules(
 
     for something in files_or_modules:
         basename = os.path.basename(something)
-        if (
-            basename in ignore_list
-            or _is_in_ignore_list_re(os.path.basename(something), ignore_list_re)
-            or _is_in_ignore_list_re(something, ignore_list_paths_re)
+        if _is_ignored_file(
+            something, ignore_list, ignore_list_re, ignore_list_paths_re
         ):
             continue
         module_path = get_python_path(something)
@@ -128,9 +141,9 @@ def expand_modules(
             ):
                 if filepath == subfilepath:
                     continue
-                if _is_in_ignore_list_re(
-                    os.path.basename(subfilepath), ignore_list_re
-                ) or _is_in_ignore_list_re(subfilepath, ignore_list_paths_re):
+                if _is_ignored_file(
+                    subfilepath, ignore_list, ignore_list_re, ignore_list_paths_re
+                ):
                     continue
 
                 modpath = _modpath_from_file(
diff --git a/pylint/lint/pylinter.py b/pylint/lint/pylinter.py
index 53345a6b..38353e4c 100644
--- a/pylint/lint/pylinter.py
+++ b/pylint/lint/pylinter.py
@@ -31,7 +31,7 @@ from pylint.constants import (
 )
 from pylint.lint.base_options import _make_linter_options
 from pylint.lint.caching import load_results, save_results
-from pylint.lint.expand_modules import expand_modules
+from pylint.lint.expand_modules import _is_ignored_file, expand_modules
 from pylint.lint.message_state_handler import _MessageStateHandler
 from pylint.lint.parallel import check_parallel
 from pylint.lint.report_functions import (
@@ -564,8 +564,7 @@ class PyLinter(
             if not msg.may_be_emitted():
                 self._msgs_state[msg.msgid] = False
 
-    @staticmethod
-    def _discover_files(files_or_modules: Sequence[str]) -> Iterator[str]:
+    def _discover_files(self, files_or_modules: Sequence[str]) -> Iterator[str]:
         """Discover python modules and packages in sub-directory.
 
         Returns iterator of paths to discovered modules and packages.
@@ -575,10 +574,20 @@ class PyLinter(
                 os.path.join(something, "__init__.py")
             ):
                 skip_subtrees: list[str] = []
-                for root, _, files in os.walk(something):
+                for root, dirs, files in os.walk(something):
                     if any(root.startswith(s) for s in skip_subtrees):
                         # Skip subtree of already discovered package.
                         continue
+                    if _is_ignored_file(
+                        root,
+                        self.config.ignore,
+                        self.config.ignore_patterns,
+                        self.config.ignore_paths,
+                    ):
+                        # Do not descend into ignored directories.
+                        dirs[:] = []
+                        continue
+
                     if "__init__.py" in files:
                         skip_subtrees.append(root)
                         yield root


## GOLD PATCH
diff --git a/pylint/lint/expand_modules.py b/pylint/lint/expand_modules.py
--- a/pylint/lint/expand_modules.py
+++ b/pylint/lint/expand_modules.py
@@ -46,6 +46,20 @@ def _is_in_ignore_list_re(element: str, ignore_list_re: list[Pattern[str]]) -> b
     return any(file_pattern.match(element) for file_pattern in ignore_list_re)
 
 
+def _is_ignored_file(
+    element: str,
+    ignore_list: list[str],
+    ignore_list_re: list[Pattern[str]],
+    ignore_list_paths_re: list[Pattern[str]],
+) -> bool:
+    basename = os.path.basename(element)
+    return (
+        basename in ignore_list
+        or _is_in_ignore_list_re(basename, ignore_list_re)
+        or _is_in_ignore_list_re(element, ignore_list_paths_re)
+    )
+
+
 def expand_modules(
     files_or_modules: Sequence[str],
     ignore_list: list[str],
@@ -61,10 +75,8 @@ def expand_modules(
 
     for something in files_or_modules:
         basename = os.path.basename(something)
-        if (
-            basename in ignore_list
-            or _is_in_ignore_list_re(os.path.basename(something), ignore_list_re)
-            or _is_in_ignore_list_re(something, ignore_list_paths_re)
+        if _is_ignored_file(
+            something, ignore_list, ignore_list_re, ignore_list_paths_re
         ):
             continue
         module_path = get_python_path(something)
diff --git a/pylint/lint/pylinter.py b/pylint/lint/pylinter.py
--- a/pylint/lint/pylinter.py
+++ b/pylint/lint/pylinter.py
@@ -31,7 +31,7 @@
 )
 from pylint.lint.base_options import _make_linter_options
 from pylint.lint.caching import load_results, save_results
-from pylint.lint.expand_modules import expand_modules
+from pylint.lint.expand_modules import _is_ignored_file, expand_modules
 from pylint.lint.message_state_handler import _MessageStateHandler
 from pylint.lint.parallel import check_parallel
 from pylint.lint.report_functions import (
@@ -564,8 +564,7 @@ def initialize(self) -> None:
             if not msg.may_be_emitted():
                 self._msgs_state[msg.msgid] = False
 
-    @staticmethod
-    def _discover_files(files_or_modules: Sequence[str]) -> Iterator[str]:
+    def _discover_files(self, files_or_modules: Sequence[str]) -> Iterator[str]:
         """Discover python modules and packages in sub-directory.
 
         Returns iterator of paths to discovered modules and packages.
@@ -579,6 +578,16 @@ def _discover_files(files_or_modules: Sequence[str]) -> Iterator[str]:
                     if any(root.startswith(s) for s in skip_subtrees):
                         # Skip subtree of already discovered package.
                         continue
+
+                    if _is_ignored_file(
+                        root,
+                        self.config.ignore,
+                        self.config.ignore_patterns,
+                        self.config.ignore_paths,
+                    ):
+                        skip_subtrees.append(root)
+                        continue
+
                     if "__init__.py" in files:
                         skip_subtrees.append(root)
                         yield root


## GOLD TEST_PATCH
diff --git a/tests/lint/unittest_lint.py b/tests/lint/unittest_lint.py
--- a/tests/lint/unittest_lint.py
+++ b/tests/lint/unittest_lint.py
@@ -864,6 +864,49 @@ def test_by_module_statement_value(initialized_linter: PyLinter) -> None:
         assert module_stats["statement"] == linter2.stats.statement
 
 
+@pytest.mark.parametrize(
+    "ignore_parameter,ignore_parameter_value",
+    [
+        ("--ignore", "failing.py"),
+        ("--ignore", "ignored_subdirectory"),
+        ("--ignore-patterns", "failing.*"),
+        ("--ignore-patterns", "ignored_*"),
+        ("--ignore-paths", ".*directory/ignored.*"),
+        ("--ignore-paths", ".*ignored.*/failing.*"),
+    ],
+)
+def test_recursive_ignore(ignore_parameter, ignore_parameter_value) -> None:
+    run = Run(
+        [
+            "--recursive",
+            "y",
+            ignore_parameter,
+            ignore_parameter_value,
+            join(REGRTEST_DATA_DIR, "directory"),
+        ],
+        exit=False,
+    )
+
+    linted_files = run.linter._iterate_file_descrs(
+        tuple(run.linter._discover_files([join(REGRTEST_DATA_DIR, "directory")]))
+    )
+    linted_file_paths = [file_item.filepath for file_item in linted_files]
+
+    ignored_file = os.path.abspath(
+        join(REGRTEST_DATA_DIR, "directory", "ignored_subdirectory", "failing.py")
+    )
+    assert ignored_file not in linted_file_paths
+
+    for regrtest_data_module in (
+        ("directory", "subdirectory", "subsubdirectory", "module.py"),
+        ("directory", "subdirectory", "module.py"),
+        ("directory", "package", "module.py"),
+        ("directory", "package", "subpackage", "module.py"),
+    ):
+        module = os.path.abspath(join(REGRTEST_DATA_DIR, *regrtest_data_module))
+    assert module in linted_file_paths
+
+
 def test_import_sibling_module_from_namespace(initialized_linter: PyLinter) -> None:
     """If the parent directory above `namespace` is on sys.path, ensure that
     modules under `namespace` can import each other without raising `import-error`."""
diff --git a/tests/regrtest_data/directory/ignored_subdirectory/failing.py b/tests/regrtest_data/directory/ignored_subdirectory/failing.py
new file mode 100644
--- /dev/null
+++ b/tests/regrtest_data/directory/ignored_subdirectory/failing.py
@@ -0,0 +1 @@
+import re
diff --git a/tests/test_self.py b/tests/test_self.py
--- a/tests/test_self.py
+++ b/tests/test_self.py
@@ -1228,17 +1228,91 @@ def test_max_inferred_for_complicated_class_hierarchy() -> None:
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
             code=0,
         )
 
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
+            code=0,
+        )
+
     def test_recursive_current_dir(self):
         with _test_sys_path():
             # pytest is including directory HERE/regrtest_data to sys.path which causes
@@ -1249,7 +1323,7 @@ def test_recursive_current_dir(self):
                 if not os.path.basename(path) == "regrtest_data"
             ]
             with _test_cwd():
-                os.chdir(join(HERE, "regrtest_data", "directory"))
+                os.chdir(join(HERE, "regrtest_data", "directory", "subdirectory"))
                 self._runtest(
                     [".", "--recursive=y"],
                     code=0,


## V4 SOURCES
(none on disk)
