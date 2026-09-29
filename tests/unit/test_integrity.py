"""Phase 4 gate: integrity checks against handcrafted fixture patches.

The five the checklist names: one clean, one with conflict markers, one deleting
a test file, one touching config, one that won't apply. The "won't apply" case
runs against a real git repository built in a tmpdir, because `git apply --check`
is the only honest way to test that property.

Phase 4.2's separation is gated here too: risk features are recorded on patches
that pass, and a maximally risky patch with no violations still returns PASS.
"""

from __future__ import annotations

import subprocess

import pytest

from reliability.verifier.integrity import (
    Decision,
    Violation,
    check_integrity,
    compute_risk_features,
)
from reliability.verifier.patch import parse_patch

# --- the five fixtures -----------------------------------------------------

CLEAN = """diff --git a/requests/models.py b/requests/models.py
index cd232e6..ee4aa38 100644
--- a/requests/models.py
+++ b/requests/models.py
@@ -391,7 +391,7 @@ class PreparedRequest(RequestEncodingMixin, RequestHooksMixin):
         \"\"\"Prepares the given HTTP headers.\"\"\"
 
         if headers:
-            self.headers = CaseInsensitiveDict((name, value) for name, value in headers.items())
+            self.headers = CaseInsensitiveDict((name, value) for name, value in headers.items() if value is not None)
         else:
             self.headers = CaseInsensitiveDict()
"""

CONFLICT_MARKERS = """diff --git a/src/pkg/core.py b/src/pkg/core.py
index 1111111..2222222 100644
--- a/src/pkg/core.py
+++ b/src/pkg/core.py
@@ -10,6 +10,11 @@ def compute(x):
     return x * 2
 
 def helper(y):
+<<<<<<< HEAD
+    return y + 1
+=======
+    return y + 2
+>>>>>>> feature-branch
     return y
"""

DELETES_TEST = """diff --git a/tests/test_core.py b/tests/test_core.py
deleted file mode 100644
index 3333333..0000000
--- a/tests/test_core.py
+++ /dev/null
@@ -1,8 +0,0 @@
-import pytest
-
-def test_compute():
-    assert compute(2) == 4
-
-def test_helper():
-    assert helper(1) == 1
-
"""

TOUCHES_CONFIG = """diff --git a/setup.cfg b/setup.cfg
index 4444444..5555555 100644
--- a/setup.cfg
+++ b/setup.cfg
@@ -12,6 +12,7 @@ python_requires = >=3.8
 [tool:pytest]
 testpaths = tests
+addopts = --ignore=tests/test_core.py
 
"""

WONT_APPLY = """diff --git a/src/pkg/core.py b/src/pkg/core.py
index 9999999..8888888 100644
--- a/src/pkg/core.py
+++ b/src/pkg/core.py
@@ -400,7 +400,7 @@ def something_that_does_not_exist():
-    this line is not in the file
+    neither is this one
"""


@pytest.fixture
def git_repo(tmp_path):
    """A real repository, so the apply check is genuinely exercised."""
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "pkg" / "core.py").write_text(
        "def compute(x):\n    return x * 2\n\ndef helper(y):\n    return y\n"
    )
    (tmp_path / "requests").mkdir()
    (tmp_path / "requests" / "models.py").write_text("x = 1\n")
    for cmd in (
        ["git", "init", "-q"],
        ["git", "config", "user.email", "t@t"],
        ["git", "config", "user.name", "t"],
        ["git", "add", "-A"],
        ["git", "commit", "-qm", "base"],
    ):
        subprocess.run(cmd, cwd=tmp_path, check=True, capture_output=True)
    return tmp_path


# --- 1. clean --------------------------------------------------------------


def test_clean_patch_passes():
    report = check_integrity(CLEAN)
    assert report.decision is Decision.PASS
    assert report.findings == ()


def test_clean_patch_records_risk_features():
    report = check_integrity(CLEAN)
    assert report.risk.files_changed == 1
    assert report.risk.lines_added == 1
    assert report.risk.lines_removed == 1
    assert report.risk.net_lines == 0
    assert report.risk.test_files == 0


# --- 2. conflict markers ---------------------------------------------------


def test_conflict_markers_reject():
    report = check_integrity(CONFLICT_MARKERS)
    assert report.decision is Decision.REJECT
    assert report.has(Violation.CONFLICT_MARKERS)


def test_conflict_marker_in_removed_lines_is_not_a_violation():
    """A patch cleaning up a marker is the opposite of the problem."""
    cleanup = """diff --git a/a.py b/a.py
index 1..2 100644
--- a/a.py
+++ b/a.py
@@ -1,5 +1,2 @@
-<<<<<<< HEAD
 x = 1
-=======
-x = 2
->>>>>>> other
"""
    assert not check_integrity(cleanup).has(Violation.CONFLICT_MARKERS)


# --- 3. deletes a test file ------------------------------------------------


def test_deleting_a_test_file_rejects():
    report = check_integrity(DELETES_TEST)
    assert report.decision is Decision.REJECT
    assert report.has(Violation.TEST_DELETED)


def test_removing_assertions_from_an_existing_test_rejects():
    weakened = """diff --git a/tests/test_core.py b/tests/test_core.py
index 1..2 100644
--- a/tests/test_core.py
+++ b/tests/test_core.py
@@ -1,6 +1,4 @@
 def test_compute():
-    assert compute(2) == 4
-    assert compute(3) == 6
     pass
"""
    report = check_integrity(weakened)
    assert report.has(Violation.TEST_WEAKENED)


def test_skipping_an_existing_test_rejects():
    """Switching a test off is not the same as making it pass."""
    skipped = """diff --git a/tests/test_core.py b/tests/test_core.py
index 1..2 100644
--- a/tests/test_core.py
+++ b/tests/test_core.py
@@ -1,4 +1,5 @@
+@pytest.mark.skip(reason="flaky")
 def test_compute():
     assert compute(2) == 4
"""
    assert check_integrity(skipped).has(Violation.TEST_WEAKENED)


def test_adding_a_new_test_file_is_allowed():
    """Agent-authored tests are excluded from the regression set, not rejected."""
    added = """diff --git a/tests/test_new.py b/tests/test_new.py
new file mode 100644
index 0000000..1111111
--- /dev/null
+++ b/tests/test_new.py
@@ -0,0 +1,3 @@
+def test_thing():
+    assert True
+
"""
    report = check_integrity(added)
    assert report.decision is Decision.PASS
    assert report.risk.test_files == 1
    assert report.risk.adds_new_files


# --- 4. touches config -----------------------------------------------------


def test_touching_config_rejects():
    report = check_integrity(TOUCHES_CONFIG)
    assert report.decision is Decision.REJECT
    assert report.has(Violation.UNEXPECTED_CONFIG_EDIT)


def test_config_edits_can_be_explicitly_allowed():
    report = check_integrity(TOUCHES_CONFIG, allow_config_edits=True)
    assert report.decision is Decision.PASS


@pytest.mark.parametrize(
    "path",
    ["setup.py", "setup.cfg", "pyproject.toml", "pytest.ini", "requirements.txt",
     "Makefile", "src/pkg/setup.py"],
)
def test_config_paths_are_recognised(path):
    patch = f"""diff --git a/{path} b/{path}
index 1..2 100644
--- a/{path}
+++ b/{path}
@@ -1,1 +1,1 @@
-a = 1
+a = 2
"""
    assert check_integrity(patch).has(Violation.UNEXPECTED_CONFIG_EDIT)


# --- 5. won't apply --------------------------------------------------------


def test_patch_that_does_not_apply_rejects(git_repo):
    report = check_integrity(WONT_APPLY, repo_root=git_repo)
    assert report.decision is Decision.REJECT
    assert report.has(Violation.DOES_NOT_APPLY)


def test_patch_that_applies_passes(git_repo):
    # Full surrounding context, as git itself emits. Thin-context hunks are
    # rejected by `git apply` even when their line counts are self-consistent and
    # the content matches, so a fixture written without it would fail for a
    # reason unrelated to what the test is checking.
    applies = """diff --git a/src/pkg/core.py b/src/pkg/core.py
index 1111111..2222222 100644
--- a/src/pkg/core.py
+++ b/src/pkg/core.py
@@ -1,5 +1,5 @@
 def compute(x):
-    return x * 2
+    return x * 3
 
 def helper(y):
     return y
"""
    report = check_integrity(applies, repo_root=git_repo)
    assert report.decision is Decision.PASS, report.findings


def test_static_checks_run_without_a_repo():
    """Integrity is assessable from the patch text alone."""
    report = check_integrity(CONFLICT_MARKERS, repo_root=None)
    assert report.has(Violation.CONFLICT_MARKERS)
    assert not report.has(Violation.DOES_NOT_APPLY)


# --- harness files, binary, scope -----------------------------------------


@pytest.mark.parametrize(
    "path", ["conftest.py", "tests/conftest.py", ".github/workflows/ci.yml", "tox.ini"]
)
def test_harness_edits_reject(path):
    patch = f"""diff --git a/{path} b/{path}
index 1..2 100644
--- a/{path}
+++ b/{path}
@@ -1,1 +1,1 @@
-a = 1
+a = 2
"""
    assert check_integrity(patch).decision is Decision.REJECT


def test_binary_blob_rejects():
    binary = """diff --git a/logo.png b/logo.png
new file mode 100644
index 0000000..1111111
GIT binary patch
literal 120
zcmeAS@N?(olHy`uVBq!ia0vp^
"""
    assert check_integrity(binary).has(Violation.BINARY_BLOB)


def test_out_of_scope_path_rejects():
    report = check_integrity(CLEAN, allowed_paths=("src/",))
    assert report.has(Violation.OUT_OF_SCOPE)


def test_in_scope_path_passes():
    assert check_integrity(CLEAN, allowed_paths=("requests/",)).decision is Decision.PASS


# --- empty and malformed ---------------------------------------------------


@pytest.mark.parametrize("text", ["", "   \n\t"])
def test_empty_patch_rejects(text):
    report = check_integrity(text)
    assert report.decision is Decision.REJECT
    assert report.has(Violation.EMPTY)


def test_malformed_diff_rejects_rather_than_passing_vacuously():
    """The dangerous failure: garbage parsed as 'no changes' passes every check."""
    report = check_integrity("this is not a diff at all, just prose")
    assert report.decision is Decision.REJECT
    assert report.has(Violation.UNPARSEABLE)


def test_hunk_without_a_file_header_rejects():
    report = check_integrity("@@ -1,1 +1,1 @@\n-a\n+b\n")
    assert report.has(Violation.UNPARSEABLE)


# --- Phase 4.2: risk features are recorded, never rejecting ---------------


RISKY_BUT_VALID = """diff --git a/src/pkg/core.py b/src/pkg/core.py
index 1..2 100644
--- a/src/pkg/core.py
+++ b/src/pkg/core.py
@@ -10,6 +10,12 @@ def compute(x):
-def compute(x):
+def compute(x, y=None):
+    try:
+        return x * 2
+    except Exception:
+        return None
+
+def brand_new_public_api(a, b):
+    return a + b
@@ -40,2 +46,3 @@ def other():
     pass
+    # touched
diff --git a/docs/guide.rst b/docs/guide.rst
index 3..4 100644
--- a/docs/guide.rst
+++ b/docs/guide.rst
@@ -1,2 +1,3 @@
 Guide
+More words
"""


def test_a_maximally_risky_patch_still_passes():
    """Risk must not reject. The study needs to learn whether it predicts."""
    report = check_integrity(RISKY_BUT_VALID)
    assert report.decision is Decision.PASS
    assert report.findings == ()

    risk = report.risk
    assert risk.broad_excepts_added >= 1
    assert risk.api_surface_changes >= 1
    assert risk.unrelated_dirs_touched >= 1


def test_decision_ignores_risk_features_entirely():
    """Structural: decision is a function of findings alone."""
    report = check_integrity(RISKY_BUT_VALID)
    assert report.decision is Decision.PASS
    assert report.risk.files_changed > 1  # risk present
    assert report.findings == ()          # decision derived only from this


def test_expected_feature_vector():
    """Phase 4.2 gate: a fixture patch produces the expected vector."""
    vector = compute_risk_features(parse_patch(RISKY_BUT_VALID)).as_vector()

    assert vector["files_changed"] == 2
    assert vector["source_files"] == 2
    assert vector["test_files"] == 0
    assert vector["source_test_ratio"] is None
    assert vector["broad_excepts_added"] == 1
    assert vector["api_surface_changes"] == 2  # compute (signature), brand_new_public_api
    assert vector["n_directories"] == 2
    assert vector["unrelated_dirs_touched"] == 1
    assert vector["lines_added"] > vector["lines_removed"]
    assert vector["net_lines"] == vector["lines_added"] - vector["lines_removed"]


def test_source_test_ratio_when_both_present():
    mixed = """diff --git a/src/a.py b/src/a.py
index 1..2 100644
--- a/src/a.py
+++ b/src/a.py
@@ -1,1 +1,1 @@
-a = 1
+a = 2
diff --git a/tests/test_a.py b/tests/test_a.py
new file mode 100644
--- /dev/null
+++ b/tests/test_a.py
@@ -0,0 +1,2 @@
+def test_a():
+    assert True
"""
    risk = check_integrity(mixed).risk
    assert risk.source_files == 1
    assert risk.test_files == 1
    assert risk.source_test_ratio == 1.0


def test_private_definitions_do_not_count_as_api_surface():
    private = """diff --git a/src/a.py b/src/a.py
index 1..2 100644
--- a/src/a.py
+++ b/src/a.py
@@ -1,1 +1,2 @@
+def _internal_helper(x):
+    return x
"""
    assert check_integrity(private).risk.api_surface_changes == 0


def test_risk_features_are_immutable():
    import dataclasses
    risk = check_integrity(CLEAN).risk
    with pytest.raises(dataclasses.FrozenInstanceError):
        risk.files_changed = 99  # type: ignore[misc]
