"""Amendment B8: V1 blocks a patch that adds sitecustomize.py or any file under v4_repro/."""

import pytest

from reliability.verifier.evidence import has_prohibited_manipulation
from reliability.verifier.integrity import Violation, check_integrity


def added(path, body="x = 1\n"):
    return (f"diff --git a/{path} b/{path}\nnew file mode 100644\n--- /dev/null\n+++ b/{path}\n"
            f"@@ -0,0 +1 @@\n+{body}")


def modified(path):
    return f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n@@ -1 +1 @@\n-x = 1\n+x = 2\n"


def renamed(old, new):
    return f"diff --git a/{old} b/{new}\nsimilarity index 100%\nrename from {old}\nrename to {new}\n"


@pytest.mark.parametrize("patch", [
    added("sitecustomize.py"), added("src/pkg/sitecustomize.py"), added("v4_repro/test_repro_R1_p1.py"),
    added("v4_repro/helpers/__init__.py"), renamed("pkg/tools.py", "sitecustomize.py"),
], ids=["root-sitecustomize", "nested-sitecustomize", "v4-test", "v4-subdir", "renamed-to-sitecustomize"])
def test_injection_paths_are_blocked(patch):
    report = check_integrity(patch)
    assert Violation.HARNESS_FILE_EDIT in report.violations and not report.passed
    assert has_prohibited_manipulation(report)
    assert any("amendment B8" in f.detail for f in report.findings)


@pytest.mark.parametrize("patch", [
    added("pkg/v4_repro_notes.py"), added("docs/v4_repro.txt"), added("pkg/customize.py"),
    added("pkg/sub/v4_repro/x.py"),
], ids=["prefix-only", "file-named-v4_repro", "other-name", "nested-v4_repro"])
def test_other_paths_are_not_blocked(patch):
    report = check_integrity(patch)
    assert not any("amendment B8" in f.detail for f in report.findings)
