POST-HOC ANALYSIS ONLY. Uses oracle fields (FAIL_TO_PASS, PASS_TO_PASS, gold patch, test_patch). Must never feed back into any run.

# pylint-dev__pylint-7277  group=group1_false_accept  run=main_50_a
## ISSUE
`pylint` removes first item from `sys.path` when running from `runpy`.
### Bug description

This is the line where the first item from sys.path is removed.
https://github.com/PyCQA/pylint/blob/ce7cccf96454fb6e286e4a8f38919733a0f28f44/pylint/__init__.py#L99

I think there should be a check to ensure that the first item is `""`, `"."` or `os.getcwd()` before removing.

### Configuration

_No response_

### Command used

```shell
Run programmatically to repro this, using this code:

import sys
import runpy

sys.path.insert(0, "something")

runpy.run_module('pylint', run_name="__main__", alter_sys=True)
```


### Pylint output

```shell
When using pylint extension which bundles the libraries, the extension add them to sys.path depending on user settings. Pylint removes the first entry from sys path causing it to fail to load.
```


### Expected behavior

Check if  `""`, `"."` or `os.getcwd()` before removing the first item from sys.path

### Pylint version

```shell
pylint 2.14.5
```


### OS / Environment

_No response_

### Additional dependencies

_No response_


## AGENT PATCH
diff --git a/pylint/__init__.py b/pylint/__init__.py
index 9f3dd74e..db105f34 100644
--- a/pylint/__init__.py
+++ b/pylint/__init__.py
@@ -86,7 +86,8 @@ def modify_sys_path() -> None:
     stdlib or pylint's own modules.
     CPython issue: https://bugs.python.org/issue33053
 
-    - Remove the first entry. This will always be either "" or the working directory
+    - Remove the first entry if it is the current working directory (or a
+      representation of it such as "" or ".").
     - Remove the working directory from the second and third entries
       if PYTHONPATH includes a ":" at the beginning or the end.
       https://github.com/PyCQA/pylint/issues/3636
@@ -96,9 +97,11 @@ def modify_sys_path() -> None:
       if pylint is installed in an editable configuration (as the last item).
       https://github.com/PyCQA/pylint/issues/4161
     """
+    cwd = os.getcwd()
+    if not sys.path or sys.path[0] not in ("", ".", cwd):
+        return
     sys.path.pop(0)
     env_pythonpath = os.environ.get("PYTHONPATH", "")
-    cwd = os.getcwd()
     if env_pythonpath.startswith(":") and env_pythonpath not in (f":{cwd}", ":."):
         sys.path.pop(0)
     elif env_pythonpath.endswith(":") and env_pythonpath not in (f"{cwd}:", ".:"):


## GOLD PATCH
diff --git a/pylint/__init__.py b/pylint/__init__.py
--- a/pylint/__init__.py
+++ b/pylint/__init__.py
@@ -96,9 +96,10 @@ def modify_sys_path() -> None:
       if pylint is installed in an editable configuration (as the last item).
       https://github.com/PyCQA/pylint/issues/4161
     """
-    sys.path.pop(0)
-    env_pythonpath = os.environ.get("PYTHONPATH", "")
     cwd = os.getcwd()
+    if sys.path[0] in ("", ".", cwd):
+        sys.path.pop(0)
+    env_pythonpath = os.environ.get("PYTHONPATH", "")
     if env_pythonpath.startswith(":") and env_pythonpath not in (f":{cwd}", ":."):
         sys.path.pop(0)
     elif env_pythonpath.endswith(":") and env_pythonpath not in (f"{cwd}:", ".:"):


## GOLD TEST_PATCH
diff --git a/tests/test_self.py b/tests/test_self.py
--- a/tests/test_self.py
+++ b/tests/test_self.py
@@ -759,6 +759,24 @@ def test_modify_sys_path() -> None:
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


## V4 SOURCES
### test_repro_1.py
"""Repro 1: ``pylint.modify_sys_path()`` must not drop a custom leading entry.

Issue: pylint removes the first item from ``sys.path`` unconditionally when it is
executed, e.g. via ``runpy.run_module("pylint", run_name="__main__")``.  The
first entry should only be removed when it actually denotes the current working
directory, i.e. when it is ``""``, ``"."`` or ``os.getcwd()``.

Here we call ``modify_sys_path()`` directly with a custom leading entry and
assert that it survives.  On the buggy code ``sys.path.pop(0)`` removes it and
the assertion fails.
"""

import sys

import pylint


def main() -> None:
    original_path = list(sys.path)
    try:
        sys.path[:] = ["something"] + original_path
        assert sys.path[0] == "something"
        pylint.modify_sys_path()
        assert sys.path[0] == "something", (
            "modify_sys_path() removed a custom leading sys.path entry; "
            "sys.path[:3] = %r" % (sys.path[:3],)
        )
    finally:
        # Do not leave the interpreter state corrupted.
        sys.path[:] = original_path


main()

### test_repro_2.py
"""Repro 2: end-to-end reproduction using ``runpy`` exactly as in the issue.

The issue reports that running pylint through ``runpy.run_module`` removes the
first ``sys.path`` entry even when it is an arbitrary user supplied directory
(the extension bundled libraries in the report).  After the run the injected
entry must still be present and still be the first entry.
"""

import runpy
import sys


def main() -> None:
    original_path = list(sys.path)
    original_argv = list(sys.argv)

    sys.path.insert(0, "something")
    sys.argv = ["pylint", "--version"]
    try:
        try:
            runpy.run_module("pylint", run_name="__main__", alter_sys=True)
        except SystemExit as exc:
            # ``--version`` exits cleanly; that is fine.
            assert exc.code in (0, None), "pylint exited with %r" % (exc.code,)

        assert "something" in sys.path, (
            "runpy-launched pylint dropped the injected sys.path entry; "
            "sys.path[:3] = %r" % (sys.path[:3],)
        )
        assert sys.path[0] == "something", (
            "runpy-launched pylint changed the leading sys.path entry; "
            "sys.path[:3] = %r" % (sys.path[:3],)
        )
    finally:
        sys.path[:] = original_path
        sys.argv[:] = original_argv


main()

### test_repro_3.py
"""Repro 3: removal of the leading entry must be conditional.

The fix requested by the issue is to only remove the first ``sys.path`` item
when it is the working directory, represented by ``""``, ``"."`` or
``os.getcwd()``.  This script verifies both halves of that contract:

* the working-directory forms are stripped, and
* any other leading entry is preserved.

On the buggy code the very first check that uses a custom entry fails because
the unconditional ``sys.path.pop(0)`` removes it.
"""

import os
import sys

import pylint


def call_modify_sys_path_with(entry: str) -> list:
    """Call ``modify_sys_path`` with ``entry`` first and return resulting path."""
    original_path = list(sys.path)
    try:
        sys.path[:] = [entry] + original_path
        assert sys.path[0] == entry
        pylint.modify_sys_path()
        return list(sys.path)
    finally:
        sys.path[:] = original_path


def main() -> None:
    cwd = os.getcwd()

    # The working directory, however it is spelled, should be removed.
    for entry in ("", ".", cwd):
        result = call_modify_sys_path_with(entry)
        assert result[0] != entry, (
            "modify_sys_path() failed to strip the working-directory entry %r; "
            "sys.path[:3] = %r" % (entry, result[:3])
        )

    # A non working-directory entry must be kept.
    custom = "not_the_working_directory"
    result = call_modify_sys_path_with(custom)
    assert result[0] == custom, (
        "modify_sys_path() stripped a custom leading entry %r; "
        "sys.path[:3] = %r" % (custom, result[:3])
    )


main()

