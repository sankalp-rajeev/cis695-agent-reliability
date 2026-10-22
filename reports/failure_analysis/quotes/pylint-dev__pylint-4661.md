POST-HOC ANALYSIS ONLY. Uses oracle fields (FAIL_TO_PASS, PASS_TO_PASS, gold patch, test_patch). Must never feed back into any run.

# pylint-dev__pylint-4661  group=group1_false_accept  run=main_50_b
## ISSUE
Make pylint XDG Base Directory Specification compliant
I have this really annoying `.pylint.d` directory in my home folder. From what I can tell (I don't do C or C++), this directory is storing data. 

The problem with this is, quite simply, that data storage has a designated spot. The `$HOME/.local/share/<PROGRAM_NAME>` folder. This is a part of the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html). A system that designates the folders for specific things like cached files (`$HOME/.cache/<PROGRAM_NAME>`), configuration files (`$HOME/.config/<PROGRAM_NAME>`), and data files (`$HOME/.local/share/<PROGRAM_NAME>`), among other things. The point is to keep user home directories clean and the user sane. 

This should be pretty easy to implement. Simply change the variables/constants for where these files are made and stored to the appropriate directory. Simple as that, even for a large codebase (if it was done right). 


## AGENT PATCH
diff --git a/doc/faq.rst b/doc/faq.rst
index c817855f..f4fd788c 100644
--- a/doc/faq.rst
+++ b/doc/faq.rst
@@ -93,10 +93,8 @@ localized using the following rules:
 
 * value of the PYLINTHOME environment variable if set
 
-* ".pylint.d" subdirectory of the user's home directory if it is found
-	(not always findable on Windows platforms)
-
-* ".pylint.d" directory in the current directory
+* the user data directory for pylint, as determined by the ``platformdirs``
+  library (for example ``~/.local/share/pylint`` on Linux)
 
 3.3 How do I find the option name (for pylintrc) corresponding to a specific command line option?
 --------------------------------------------------------------------------------------------------------
diff --git a/pylint/config/__init__.py b/pylint/config/__init__.py
index 84774d0e..8bacae85 100644
--- a/pylint/config/__init__.py
+++ b/pylint/config/__init__.py
@@ -36,6 +36,8 @@ import os
 import pickle
 import sys
 
+from platformdirs import user_data_dir
+
 from pylint.config.configuration_mixin import ConfigurationMixIn
 from pylint.config.find_default_config_files import find_default_config_files
 from pylint.config.man_help_formatter import _ManHelpFormatter
@@ -55,15 +57,7 @@ __all__ = [
     "UnsupportedAction",
 ]
 
-USER_HOME = os.path.expanduser("~")
-if "PYLINTHOME" in os.environ:
-    PYLINT_HOME = os.environ["PYLINTHOME"]
-    if USER_HOME == "~":
-        USER_HOME = os.path.dirname(PYLINT_HOME)
-elif USER_HOME == "~":
-    PYLINT_HOME = ".pylint.d"
-else:
-    PYLINT_HOME = os.path.join(USER_HOME, ".pylint.d")
+PYLINT_HOME = os.environ.get("PYLINTHOME", user_data_dir("pylint", "pylint"))
 
 
 def _get_pdata_path(base_name, recurs):
@@ -83,7 +77,7 @@ def load_results(base):
 def save_results(results, base):
     if not os.path.exists(PYLINT_HOME):
         try:
-            os.mkdir(PYLINT_HOME)
+            os.makedirs(PYLINT_HOME, exist_ok=True)
         except OSError:
             print("Unable to create directory %s" % PYLINT_HOME, file=sys.stderr)
     data_file = _get_pdata_path(base, 1)
@@ -110,8 +104,8 @@ ENV_HELP = (
 The following environment variables are used:
     * PYLINTHOME
     Path to the directory where persistent data for the run will be stored. If
-not found, it defaults to ~/.pylint.d/ or .pylint.d (in the current working
-directory).
+not found, it defaults to the platform-specific user data directory for
+pylint (for example ~/.local/share/pylint on Linux).
     * PYLINTRC
     Path to the configuration file. See the documentation for the method used
 to search for configuration file.


## GOLD PATCH
diff --git a/pylint/config/__init__.py b/pylint/config/__init__.py
--- a/pylint/config/__init__.py
+++ b/pylint/config/__init__.py
@@ -36,6 +36,8 @@
 import pickle
 import sys
 
+import appdirs
+
 from pylint.config.configuration_mixin import ConfigurationMixIn
 from pylint.config.find_default_config_files import find_default_config_files
 from pylint.config.man_help_formatter import _ManHelpFormatter
@@ -63,7 +65,15 @@
 elif USER_HOME == "~":
     PYLINT_HOME = ".pylint.d"
 else:
-    PYLINT_HOME = os.path.join(USER_HOME, ".pylint.d")
+    PYLINT_HOME = appdirs.user_cache_dir("pylint")
+
+    old_home = os.path.join(USER_HOME, ".pylint.d")
+    if os.path.exists(old_home):
+        print(
+            f"PYLINTHOME is now '{PYLINT_HOME}' but obsolescent '{old_home}' is found; "
+            "you can safely remove the latter",
+            file=sys.stderr,
+        )
 
 
 def _get_pdata_path(base_name, recurs):
diff --git a/setup.cfg b/setup.cfg
index 62a3fd7a5f..146f9e69bb 100644
--- a/setup.cfg
+++ b/setup.cfg
@@ -42,6 +42,7 @@ project_urls =
 [options]
 packages = find:
 install_requires =
+    appdirs>=1.4.0
     astroid>=2.6.5,<2.7 # (You should also upgrade requirements_test_min.txt)
     isort>=4.2.5,<6
     mccabe>=0.6,<0.7
@@ -74,7 +75,7 @@ markers =
 [isort]
 multi_line_output = 3
 line_length = 88
-known_third_party = astroid, sphinx, isort, pytest, mccabe, six, toml
+known_third_party = appdirs, astroid, sphinx, isort, pytest, mccabe, six, toml
 include_trailing_comma = True
 skip_glob = tests/functional/**,tests/input/**,tests/extensions/data/**,tests/regrtest_data/**,tests/data/**,astroid/**,venv/**
 src_paths = pylint
@@ -82,6 +83,9 @@ src_paths = pylint
 [mypy]
 scripts_are_modules = True
 
+[mypy-appdirs]
+ignore_missing_imports = True
+
 [mypy-astroid.*]
 ignore_missing_imports = True
 


## GOLD TEST_PATCH
diff --git a/tests/lint/unittest_lint.py b/tests/lint/unittest_lint.py
--- a/tests/lint/unittest_lint.py
+++ b/tests/lint/unittest_lint.py
@@ -46,6 +46,7 @@
 from os.path import abspath, basename, dirname, isdir, join, sep
 from shutil import rmtree
 
+import appdirs
 import pytest
 
 from pylint import checkers, config, exceptions, interfaces, lint, testutils
@@ -631,7 +632,7 @@ def test_pylint_home():
     if uhome == "~":
         expected = ".pylint.d"
     else:
-        expected = os.path.join(uhome, ".pylint.d")
+        expected = appdirs.user_cache_dir("pylint")
     assert config.PYLINT_HOME == expected
 
     try:


## V4 SOURCES
### test_repro_1.py
"""Reproduction test for: pylint should be XDG Base Directory compliant.

Correct behaviour (per the issue): when ``PYLINTHOME`` is not set, pylint's
persistent data directory must live in the XDG data directory instead of the
legacy ``~/.pylint.d``.  A valid XDG data location is either
``$XDG_DATA_HOME/pylint`` (when ``XDG_DATA_HOME`` is set) or its fallback
``$HOME/.local/share/pylint``.

On the buggy code ``PYLINT_HOME`` is ``$HOME/.pylint.d``, so this script
fails with an AssertionError.
"""

import importlib
import os
import tempfile

# Build a fully isolated / deterministic environment *before* importing pylint.
_tmp = tempfile.mkdtemp(prefix="pylint_xdg_")
_home = os.path.join(_tmp, "home")
_xdg_data_home = os.path.join(_tmp, "xdg_data")
os.makedirs(_home)
os.makedirs(_xdg_data_home)

os.environ["HOME"] = _home
os.environ["XDG_DATA_HOME"] = _xdg_data_home
os.environ.pop("PYLINTHOME", None)
os.environ.pop("PYLINTRC", None)

import pylint.config  # noqa: E402  (import has to happen after env setup)

# Reload in case pylint.config was imported as a side effect of anything else.
importlib.reload(pylint.config)

valid_locations = {
    os.path.join(_xdg_data_home, "pylint"),
    os.path.join(_home, ".local", "share", "pylint"),
}
assert pylint.config.PYLINT_HOME in valid_locations, (
    "pylint data should be stored in an XDG data directory "
    f"({sorted(valid_locations)}), got {pylint.config.PYLINT_HOME!r}"
)

# It must no longer be the legacy ~/.pylint.d directory.
legacy = os.path.join(_home, ".pylint.d")
assert pylint.config.PYLINT_HOME != legacy, (
    f"pylint data should not be stored in the legacy location {legacy!r}"
)

# The persisted statistics file must also be located there.
data_file = pylint.config._get_pdata_path("somebase", 1)
assert data_file.startswith(pylint.config.PYLINT_HOME + os.sep), (
    "the statistics file should be stored inside the data directory, "
    f"got {data_file!r}"
)

print("OK: PYLINT_HOME is an XDG data directory, not ~/.pylint.d")

### test_repro_2.py
"""Reproduction test for: pylint should be XDG Base Directory compliant.

Correct behaviour (per the issue): when neither ``PYLINTHOME`` nor
``XDG_DATA_HOME`` is set, pylint's persistent data directory must default to
``$HOME/.local/share/pylint`` (the XDG data directory fallback).

On the buggy code ``PYLINT_HOME`` is ``$HOME/.pylint.d``, so this script
fails with an AssertionError.
"""

import importlib
import os
import tempfile

# Deterministic environment built before importing pylint.
_tmp = tempfile.mkdtemp(prefix="pylint_xdg_")
_home = os.path.join(_tmp, "home")
os.makedirs(_home)

os.environ["HOME"] = _home
os.environ.pop("XDG_DATA_HOME", None)
os.environ.pop("PYLINTHOME", None)
os.environ.pop("PYLINTRC", None)

import pylint.config  # noqa: E402

importlib.reload(pylint.config)

expected = os.path.join(_home, ".local", "share", "pylint")
assert pylint.config.PYLINT_HOME == expected, (
    "pylint data should default to the XDG data directory "
    f"($HOME/.local/share/pylint): expected {expected!r}, "
    f"got {pylint.config.PYLINT_HOME!r}"
)

# It must definitely no longer be the legacy ~/.pylint.d directory.
legacy = os.path.join(_home, ".pylint.d")
assert pylint.config.PYLINT_HOME != legacy, (
    f"pylint data should not be stored in the legacy location {legacy!r}"
)

print("OK: PYLINT_HOME defaults to $HOME/.local/share/pylint")

### test_repro_3.py
"""Reproduction test for: pylint should be XDG Base Directory compliant.

This is a functional test: it drives pylint's result persistence API and
checks that the files it writes actually end up inside an XDG data directory
(``$XDG_DATA_HOME/pylint`` or the ``$HOME/.local/share/pylint`` fallback)
instead of the legacy ``~/.pylint.d``.

On the buggy code the file is written to ``$HOME/.pylint.d``, so this script
fails with an AssertionError.
"""

import importlib
import os
import tempfile

# Deterministic environment built before importing pylint.
_tmp = tempfile.mkdtemp(prefix="pylint_xdg_")
_home = os.path.join(_tmp, "home")
_xdg_data_home = os.path.join(_tmp, "xdg_data")
os.makedirs(_home)
os.makedirs(_xdg_data_home)

os.environ["HOME"] = _home
os.environ["XDG_DATA_HOME"] = _xdg_data_home
os.environ.pop("PYLINTHOME", None)
os.environ.pop("PYLINTRC", None)

import pylint.config  # noqa: E402

importlib.reload(pylint.config)

valid_locations = {
    os.path.join(_xdg_data_home, "pylint"),
    os.path.join(_home, ".local", "share", "pylint"),
}
assert pylint.config.PYLINT_HOME in valid_locations, (
    f"PYLINT_HOME should be an XDG data directory, "
    f"got {pylint.config.PYLINT_HOME!r}"
)

# Make sure the parent directory exists so that save_results can create the
# data directory (the buggy code uses the parent folder for the legacy dir).
os.makedirs(os.path.dirname(pylint.config.PYLINT_HOME), exist_ok=True)

# Persist some data and make sure it lands inside the data directory.
payload = {"run": 1, "stats": [1, 2, 3]}
pylint.config.save_results(payload, "repro_check")

data_file = pylint.config._get_pdata_path("repro_check", 1)
assert data_file.startswith(pylint.config.PYLINT_HOME + os.sep), (
    "the persisted statistics file should live inside the data directory, "
    f"got {data_file!r}"
)
assert os.path.exists(data_file), f"expected data file {data_file!r} to exist"

# And the data must still round-trip correctly.
loaded = pylint.config.load_results("repro_check")
assert loaded == payload, f"expected to load back {payload!r}, got {loaded!r}"

print("OK: persisted pylint results are stored in an XDG data directory")

