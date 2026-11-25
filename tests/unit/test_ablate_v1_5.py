"""scripts/ablate_v1_5.py: Phase 16 ablation helpers (signal drop-outs, V2 accountings, gold causes,
wrong-patch types, git_peek parsing, empty-patch sensitivity)."""

import importlib.util
import pathlib
import sys
from dataclasses import replace

from reliability.verifier.decision import SignalOutcome
from reliability.verifier.policy_v1_5 import EvidenceV15

ROOT = pathlib.Path(__file__).resolve().parents[2]
P, F, NA = SignalOutcome.PASS, SignalOutcome.FAIL, SignalOutcome.NOT_AVAILABLE


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


AB = _load("ablate_v1_5")
AN = sys.modules["analyze_v1_5"]


def ev(**kw):
    base = dict(integrity=P, regression=P, static=P, reproduction=P, patch_applies=True,
                v4_design="per_requirement", v4_full_pass=True, v4_pass_units=2)
    base.update(kw)
    return EvidenceV15(**base)


# Signal drop-outs.

def test_force_v1_clears_v1_flags():
    e = ev(integrity=F, patch_applies=False, prohibited_manipulation=True, high_severity_risk=True,
           v1_analysis_incomplete=True)
    out = AB.force_pass(e, "V1")
    assert out.integrity is P and out.patch_applies is True
    assert not out.prohibited_manipulation and not out.high_severity_risk and not out.v1_analysis_incomplete


def test_force_v2_and_v3():
    e = ev(regression=F, static=F, v3_absolute_failure=True, v2_absence="incomplete")
    assert AB.force_pass(e, "V2").regression is P
    assert AB.force_pass(e, "V2").static is F
    out = AB.force_pass(e, "V3")
    assert out.static is P and out.v3_absolute_failure is False and out.regression is F


def test_force_v4_is_full_pass():
    e = ev(reproduction=F, v4_full_pass=False, v4_failing_units=2, v4_uncovered_units=1, v4_no_result_units=1)
    out = AB.force_pass(e, "V4")
    assert out.reproduction is P and out.v4_full_pass is True
    assert (out.v4_failing_units, out.v4_uncovered_units, out.v4_no_result_units) == (0, 0, 0)


def test_force_pass_rejects_unknown_signal():
    try:
        AB.force_pass(ev(), "V5")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


# V2 accountings from stored per-accounting reports.

def _report(signal, tests=("a.py::t",), patched=None, confirmations=()):
    return {"signal": signal, "selection": {"tests": list(tests)}, "patched": patched,
            "confirmations": list(confirmations)}


def test_accounting_signal_mapping():
    clean = {"results": [{"status": "passed"}]}
    assert AB.v2_from_report(_report("PASS", patched=clean)) == (P, None, False)
    assert AB.v2_from_report(_report("FAIL", patched=clean)) == (F, None, False)
    assert AB.v2_from_report(_report("REGRESSION_ERROR", patched=clean)) == (F, None, False)
    assert AB.v2_from_report(_report("INCOMPLETE", patched=clean)) == (NA, "incomplete", False)
    assert AB.v2_from_report(_report("BASELINE_UNRELIABLE", patched=clean)) == (NA, "error", False)
    assert AB.v2_from_report(_report("NOT_AVAILABLE", patched=clean)) == (NA, "error", False)
    assert AB.v2_from_report(_report("NOT_AVAILABLE", tests=(), patched=clean)) == (NA, "nothing_to_check", False)
    # No stored patched run: a timeout or crash cannot be ruled out.
    assert AB.v2_from_report(_report("PASS"))[2] is True
    assert AB.v2_from_report(_report("PASS", patched={"results": [{"status": "timeout"}]}))[2] is True


def test_with_accounting_replaces_only_v2_fields():
    e = ev(regression=P, v2_absence=None, v2_patched_timeout_or_crash=False, static=F)
    out = AB.with_v2(e, (NA, "incomplete", True))
    assert out.regression is NA and out.v2_absence == "incomplete" and out.v2_patched_timeout_or_crash
    assert out.static is F and out.reproduction is P


# Wrong-patch types (fixed before computing).

def test_wrong_type():
    assert AB.wrong_type({"FAIL_TO_PASS": {"success": [], "failure": ["a"]},
                          "PASS_TO_PASS": {"success": ["b"], "failure": []}}) == "U"
    assert AB.wrong_type({"FAIL_TO_PASS": {"success": ["a"], "failure": []},
                          "PASS_TO_PASS": {"success": [], "failure": ["b"]}}) == "R"
    assert AB.wrong_type({"FAIL_TO_PASS": {"success": [], "failure": ["a"]},
                          "PASS_TO_PASS": {"success": [], "failure": ["b"]}}) == "X"
    assert AB.wrong_type(None) == "unknown"
    assert AB.wrong_type({}) == "unknown"
    # Per-test status exists but nothing failed: not one of the fixed types.
    assert AB.wrong_type({"FAIL_TO_PASS": {"success": ["a"], "failure": []},
                          "PASS_TO_PASS": {"success": [], "failure": []}}) == "no failing test"


def test_tests_status_both_report_shapes():
    status = {"FAIL_TO_PASS": {"success": [], "failure": ["a"]}}
    assert AB.tests_status({"x": {"resolved": False, "tests_status": status}}, "x") == status
    assert AB.tests_status({"resolved": False, "tests_status": status}, "x") == status
    assert AB.tests_status({"resolved": False}, "x") is None


# Gold causes (fixed before computing).

def test_gold_cause_superseded_confirmed_and_not():
    e = ev(regression=F)
    c = AB.gold_cause("R5", "reason", e, {"tests/a/test_x.py"}, {"tests/a/test_x.py"})
    assert c["cause"] == "superseded assertion" and c["confirmed"] is True
    c = AB.gold_cause("R3", "reason", e, {"tests/a/test_x.py"}, {"tests/b/test_y.py"})
    assert c["cause"] == "superseded assertion" and c["confirmed"] is False


def test_gold_cause_r4_r7_and_other():
    assert AB.gold_cause("R4", "r", ev(regression=P, reproduction=F), set(), set())["cause"] == \
        "verifier fault (V4 test asserts the wrong thing)"
    c = AB.gold_cause("R7", "r", ev(regression=NA, v2_absence="nothing_to_check", v4_uncovered_units=1,
                                    v4_full_pass=False), set(), set())
    assert c["cause"] == "issue not reproducible as a test" and c["second_cause"] == "no covering test"
    c = AB.gold_cause("R7", "r", ev(reproduction=NA, v4_full_pass=False, v4_pass_units=0), set(), set())
    assert c["cause"] == "issue not reproducible as a test"
    c = AB.gold_cause("R8", "some reason", ev(), set(), set())
    assert c["cause"] == "verifier fault (R8: some reason)" and c["confirmed"] is None
    # R5 without a V2 FAIL is not the superseded-assertion cause.
    assert AB.gold_cause("R5", "x", ev(regression=P, reproduction=F), set(), set())["cause"].startswith("verifier fault")


def test_failing_v2_files_and_test_patch_files():
    outcomes = {"tests/a/test_x.py::C::t1": "REGRESSION", "tests/a/test_y.py::t2": "PASS",
                "lib/b/test_z.py::t3[svg]": "REGRESSION_ERROR", "tests/q.py::t4": "SKIPPED"}
    assert AB.failing_v2_files(outcomes) == {"tests/a/test_x.py", "lib/b/test_z.py"}
    patch = ("diff --git a/tests/a/test_x.py b/tests/a/test_x.py\n--- a/tests/a/test_x.py\n+++ b/tests/a/test_x.py\n"
             "@@ -1 +1 @@\n-x\n+y\ndiff --git a/tests/new.py b/tests/new.py\nnew file mode 100644\n")
    assert AB.patch_files(patch) == {"tests/a/test_x.py", "tests/new.py"}


# git_peek.

def test_git_peek_ids():
    text = ("# header\nTotal highlighted trajectories: 2\n\nAll iids:\n\n```\ndjango__django-1\nsympy__sympy-2\n```\n\n"
            "All iids as filter\n\n```\ndjango__django-1|sympy__sympy-2\n```\n")
    assert AB.git_peek_ids(text) == ["django__django-1", "sympy__sympy-2"]
    try:
        AB.git_peek_ids("no block here")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


# Empty-patch sensitivity.

def test_empty_as_wrong_reject():
    rows = [AN.Row("s", "t1", True, False, None, {"frozen": "FLAG"}, False, False),
            AN.Row("s", "t2", False, True, True, {"frozen": "ACCEPT"}, True, False)]
    out = AB.empty_as_wrong_reject(rows, "frozen")
    assert [(r.empty, r.labelled, r.correct, r.decisions["frozen"]) for r in out] == \
        [(False, True, False, "REJECT"), (False, True, True, "ACCEPT")]
    m = AN.metrics(out, "frozen")
    assert m["n"] == 2 and m["decisions"]["REJECT_wrong"] == 1
    assert rows[0].empty is True  # inputs unchanged


def test_repo_of():
    assert AB.repo_of("scikit-learn__scikit-learn-25232") == "scikit-learn/scikit-learn"
    assert AB.repo_of("django__django-1") == "django/django"


def test_with_decisions_copies_rows():
    r = AN.Row("s", "t1", False, True, True, {"frozen": "ACCEPT"}, True, False)
    out = AB.with_decisions([r], "v", {("s", "t1"): "FLAG"})
    assert out[0].decisions == {"frozen": "ACCEPT", "v": "FLAG"} and r.decisions == {"frozen": "ACCEPT"}
    assert replace(r) == r
