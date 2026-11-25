"""Amendment A6: a V3 syntax/import failure counts only if the same check passes on base.

Pre-existing (base fails with the same exception type in the same file) and an
import failure in a patch-added module (no base version to compare) are V3 not
available for that check: never PASS, never a failure. A stored syntax FAIL with
no base result stays a failure (base unknown).
"""

import pytest

from reliability.verifier.decision import Decision, SignalOutcome
from reliability.verifier.patch import parse_patch
from reliability.verifier.policy_v1_4 import evidence_from_signals as v1_4_evidence
from reliability.verifier.policy_v1_5 import FullPolicyV15, evidence_from_signals
from reliability.verifier.record import SignalKind, SignalRecord
from reliability.verifier.static_v1_4 import paired_v3, run_static_checks

IMPORT_TB = ('Traceback (most recent call last):\n  File "<string>", line 1, in <module>\n'
             '  File "/testbed/{path}", line 57, in <module>\n    class A(models.Model):\n'
             '  File "/testbed/pkg/base.py", line 129, in __new__\n    x = y()\n'
             '{exc}: {msg}\n')
SYNTAX_SORRY = "Sorry: {exc}: unexpected indent ({name}, line 5)\n"
SYNTAX_TB = '  File "{path}", line 3\n    def f(:\n          ^\nSyntaxError: invalid syntax\n'


def result(status, stderr=""):
    return {"command": ["x"], "exit_code": 0 if status == "PASS" else 1, "stdout": "",
            "stderr": stderr, "timed_out": status == "TIMEOUT", "status": status}


def check(kind, patched_err, base, status="FAIL", targets=("pkg/mod.py",)):
    command = (["python", "-m", "py_compile", *targets] if kind == "syntax"
               else ["python", "-c", "; ".join("import " + t[:-3].replace("/", ".") for t in targets)])
    return {"kind": kind, "status": status, "command": command, "exit_code": 1,
            "stdout": "", "stderr": patched_err, "base_result": base}


def imp(path="pkg/mod.py", exc="ImproperlyConfigured", msg="settings"):
    return IMPORT_TB.format(path=path, exc=exc, msg=msg)


@pytest.mark.parametrize("base,expected,failure", [
    (result("PASS"), "FAIL", True),
    (result("FAIL", imp()), "PRE_EXISTING", False),
    (result("FAIL", imp(exc="TypeError")), "FAIL", True),
    (result("FAIL", imp(path="pkg/other.py")), "FAIL", True),
    (None, "FAIL_BASE_UNKNOWN", True),
], ids=["base-pass", "same-type-same-file", "other-type", "other-file", "no-base"])
def test_import_failure_is_paired_with_base(base, expected, failure):
    verdict = paired_v3([check("import", imp(), base)], added_paths=())
    assert verdict["checks"]["import"] == expected
    assert verdict["failure"] is failure


def test_import_failure_in_a_patch_added_module_is_base_unknown_not_available():
    base = result("FAIL", "ModuleNotFoundError: No module named 'pkg.new'\n")
    verdict = paired_v3([check("import", imp(path="pkg/new.py"), base, targets=("pkg/new.py",))],
                        added_paths=("pkg/new.py",))
    assert verdict["checks"]["import"] == "BASE_UNKNOWN" and verdict["failure"] is False


def test_import_failure_in_an_existing_module_still_counts_when_another_target_is_new():
    base = result("FAIL", "ModuleNotFoundError: No module named 'pkg.new'\n")
    verdict = paired_v3([check("import", imp(path="pkg/mod.py", exc="TypeError"), base,
                               targets=("pkg/mod.py", "pkg/new.py"))], added_paths=("pkg/new.py",))
    assert verdict["checks"]["import"] == "FAIL" and verdict["failure"] is True


@pytest.mark.parametrize("patched,base,added,expected", [
    (SYNTAX_SORRY.format(exc="IndentationError", name="mod.py"), result("PASS"), (), "FAIL"),
    (SYNTAX_SORRY.format(exc="IndentationError", name="mod.py"),
     result("FAIL", SYNTAX_SORRY.format(exc="IndentationError", name="mod.py")), (), "PRE_EXISTING"),
    (SYNTAX_SORRY.format(exc="IndentationError", name="mod.py"),
     result("FAIL", SYNTAX_SORRY.format(exc="TabError", name="mod.py")), (), "FAIL"),
    (SYNTAX_TB.format(path="pkg/mod.py"), result("FAIL", SYNTAX_TB.format(path="pkg/mod.py")), (),
     "PRE_EXISTING"),
    # Only a syntax error counts for a module the patch adds: it is always a failure.
    (SYNTAX_TB.format(path="pkg/mod.py"), result("FAIL", SYNTAX_TB.format(path="pkg/mod.py")),
     ("pkg/mod.py",), "FAIL"),
    (SYNTAX_SORRY.format(exc="IndentationError", name="mod.py"), None, (), "FAIL_BASE_UNKNOWN"),
], ids=["base-pass", "same", "other-type", "traceback-form", "patch-added", "no-base"])
def test_syntax_failure_is_paired_with_base(patched, base, added, expected):
    verdict = paired_v3([check("syntax", patched, base)], added_paths=added)
    assert verdict["checks"]["syntax"] == expected
    assert verdict["failure"] is (expected in ("FAIL", "FAIL_BASE_UNKNOWN"))


@pytest.mark.parametrize("status", ["PASS", "TIMEOUT", "NOT_AVAILABLE"])
def test_non_failures_are_left_alone(status):
    verdict = paired_v3([check("import", "", None, status=status)], added_paths=())
    assert verdict["checks"]["import"] == status and verdict["failure"] is False


def test_unattributable_failure_is_pre_existing_only_with_no_patch_added_target():
    patched = "ImportError: cannot import name 'x'\n"
    base = result("FAIL", patched)
    assert paired_v3([check("import", patched, base)], added_paths=())["checks"]["import"] == "PRE_EXISTING"
    added = paired_v3([check("import", patched, base, targets=("pkg/mod.py", "pkg/new.py"))],
                      added_paths=("pkg/new.py",))
    assert added["checks"]["import"] == "FAIL" and added["failure"] is True


def test_any_counted_failure_makes_v3_a_failure():
    verdict = paired_v3([check("syntax", SYNTAX_SORRY.format(exc="IndentationError", name="mod.py"),
                               result("PASS")),
                         check("import", imp(), result("FAIL", imp()))], added_paths=())
    assert verdict["checks"] == {"syntax": "FAIL", "import": "PRE_EXISTING"}
    assert verdict["failure"] is True and verdict["pre_existing"] == ["import"]


# Live V3: syntax now also runs on base when it fails on the patched tree.

class Tree:
    def list_files(self):
        return ("setup.py",)

    def read_text(self, path):
        return ""


class Executor:
    def __init__(self, base_fails):
        self.base_fails = base_fails
        self.calls = []

    def run_capture(self, command, *, patched, timeout_s):
        self.calls.append((tuple(command), patched))
        version = "--version" in command
        fails = not version and ("py_compile" in command or "-c" in command) and (patched or self.base_fails)
        err = imp() if "-c" in command else SYNTAX_SORRY.format(exc="IndentationError", name="mod.py")
        return {"exit_code": int(fails), "stdout": "", "stderr": err if fails else "", "timed_out": False}


SOURCE_PATCH = ("diff --git a/pkg/mod.py b/pkg/mod.py\n--- a/pkg/mod.py\n+++ b/pkg/mod.py\n"
                "@@ -1 +1 @@\n-x = 1\n+x = 2\n")


@pytest.mark.parametrize("base_fails", [True, False])
def test_live_v3_runs_syntax_on_base_and_records_the_paired_verdict(base_fails):
    executor = Executor(base_fails)
    report = run_static_checks(parse_patch(SOURCE_PATCH), Tree(), executor)
    syntax = next(c for c in report.findings["checks"] if c["kind"] == "syntax")
    assert syntax["base_result"] is not None
    assert any("py_compile" in c and not patched for c, patched in executor.calls)
    # v1.4.1 evidence is unchanged; the paired verdict is recorded beside it.
    assert report.findings["v3_absolute_failure"] is True and report.outcome is SignalOutcome.FAIL
    paired = report.findings["v3_paired"]
    assert paired["failure"] is (not base_fails)
    assert paired["checks"]["syntax"] == ("PRE_EXISTING" if base_fails else "FAIL")
    assert report.findings["patch_added_paths"] == []


def _signals(static_findings):
    def sig(kind, outcome, findings=None):
        return SignalRecord(kind=kind, outcome=outcome, detail="x", findings=findings or {},
                            **({"absence": "nothing_to_check"} if outcome is SignalOutcome.NOT_AVAILABLE else {}))
    return {
        SignalKind.INTEGRITY: sig(SignalKind.INTEGRITY, SignalOutcome.PASS, {"ast_analysis": []}),
        SignalKind.REGRESSION: sig(SignalKind.REGRESSION, SignalOutcome.PASS),
        SignalKind.STATIC: sig(SignalKind.STATIC, SignalOutcome.FAIL, static_findings),
        SignalKind.REPRODUCTION: sig(SignalKind.REPRODUCTION, SignalOutcome.PASS, {
            "setup": {"design": "per_requirement", "passes": 1}, "full_pass": True,
            "verdict_counts": {"PASS": 2}}),
    }


def stored_static(base):
    """A stored V3 record, as Phase 6 and arm B wrote them (no v3_paired field)."""
    return {"summary": {"syntax": "PASS", "import": "FAIL"}, "v3_absolute_failure": True,
            "checks": [check("syntax", "", None, status="PASS"), check("import", imp(), base)]}


def test_v1_5_evidence_recomputes_the_paired_rule_from_stored_checks():
    signals = _signals(stored_static(result("FAIL", imp())))
    assert v1_4_evidence(signals).v3_absolute_failure is True          # v1.4.1 unchanged
    evidence = evidence_from_signals(signals, added_paths=())
    assert evidence.v3_absolute_failure is False and evidence.v3_pre_existing == ("import",)
    assert FullPolicyV15(r2_v3_reject=True).decide(evidence).decision is Decision.ACCEPT
    real = evidence_from_signals(_signals(stored_static(result("PASS"))), added_paths=())
    assert real.v3_absolute_failure is True and real.v3_pre_existing == ()
    assert FullPolicyV15(r2_v3_reject=True).decide(real).rule_id == "R2"


def test_v1_5_evidence_reads_added_paths_from_live_records():
    findings = stored_static(result("FAIL", "ModuleNotFoundError: No module named 'pkg.new'\n"))
    findings["checks"][1] = check("import", imp(path="pkg/new.py"), findings["checks"][1]["base_result"],
                                  targets=("pkg/new.py",))
    findings["patch_added_paths"] = ["pkg/new.py"]
    evidence = evidence_from_signals(_signals(findings))
    assert evidence.v3_absolute_failure is False and evidence.v3_base_unknown == ("import",)
