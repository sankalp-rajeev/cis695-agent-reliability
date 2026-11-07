"""Outcome separation, policy completeness and patched-only errors."""

import json

import pytest

from reliability.verifier.container import run_from_capture
from reliability.verifier.decision import SignalOutcome
from reliability.verifier.evidence import regression_outcome
from reliability.verifier.regression import (
    Outcome,
    RegressionConfig,
    Signal,
    TestResult,
    TestStatus,
    classify,
    load_cached_baseline,
    run_from_dict,
    run_regression,
    run_to_dict,
)
from reliability.verifier.selection import Selection, TestRunner


def capture(text, tests, runner="pytest", code=0):
    raw = text.encode()
    return run_from_capture(
        TestRunner(runner, ""),
        tests,
        runner_log=raw,
        events=(
            {"event": "start", "batch": 0, "offset": 0},
            {"event": "end", "batch": 0, "offset": len(raw), "returncode": code},
            {"event": "complete"},
        ),
    )


class Paired:
    def __init__(self, base, patched):
        self.base, self.patched = base, patched
        self.calls = []

    def run(self, tests, *, patched, timeout_s):
        self.calls.append((tests, patched))
        return self.patched if patched else self.base


def score(base, patch, tests, strict=False):
    return run_regression(
        "task",
        Selection(tests=tests),
        Paired(base, patch),
        RegressionConfig(skip_compatible=not strict),
    )


@pytest.mark.parametrize(
    "runner,text,tests",
    [
        (
            "pytest",
            "t.py::a XFAIL\nt.py::b XPASS\nt.py::c SKIPPED\n",
            ("t.py::a", "t.py::b", "t.py::c"),
        ),
        (
            "django",
            (
                "a (suite.Tests) ... expected failure\n"
                "b (suite.Tests) ... unexpected success\nc (suite.Tests) ... skipped x\n"
            ),
            ("tests/suite.py::Tests::a", "tests/suite.py::Tests::b", "tests/suite.py::Tests::c"),
        ),
    ],
)
def test_statuses_survive_capture_and_serialization(runner, text, tests):
    run = capture(text, tests, runner)
    restored = run_from_dict(json.loads(json.dumps(run_to_dict(run))))
    assert [r.status for r in restored.results] == [
        TestStatus.XFAIL,
        TestStatus.XPASS,
        TestStatus.SKIPPED,
    ]
    assert [r.status for r in restored.raw_results] == [
        TestStatus.XFAIL,
        TestStatus.XPASS,
        TestStatus.SKIPPED,
    ]
    assert score(run, run, tests).summary == {"XFAIL": 1, "XPASS": 1, "SKIPPED": 1}
    assert score(run, run, tests).signal is Signal.PASS
    assert score(run, run, tests, strict=True).signal is Signal.INCOMPLETE


@pytest.mark.parametrize("word,outcome", [("XFAIL", Outcome.XFAIL), ("XPASS", Outcome.XPASS)])
def test_expected_outcomes_are_evidence_under_both_policies(word, outcome):
    tests = ("t.py::a",)
    run = capture(f"t.py::a {word}\n", tests)
    for strict in (False, True):
        report = score(run, run, tests, strict=strict)
        assert report.signal is Signal.PASS
        assert report.outcomes == {tests[0]: outcome}


def test_mixed_parameter_family_preserves_skip_gap_under_strict_policy():
    tests = ("t.py::a",)
    run = capture("t.py::a[one] XPASS\nt.py::a[two] SKIPPED\n", tests)
    assert score(run, run, tests).signal is Signal.PASS
    assert score(run, run, tests, strict=True).signal is Signal.INCOMPLETE


def test_pass_to_error_has_separate_signal_even_with_missing_evidence():
    tests = ("t.py::a", "t.py::b")
    base = capture("t.py::a PASSED\n", tests)
    patch = capture("t.py::a ERROR\n", tests, code=1)
    for strict in (False, True):
        report = score(base, patch, tests, strict=strict)
        assert report.signal is Signal.REGRESSION_ERROR
        assert report.regression_errors == ("t.py::a",)
        assert report.regressions == ()  # assertion regressions remain separate
        assert report.summary == {"REGRESSION_ERROR": 1, "NOT_RUN": 1}
        assert regression_outcome(report) is SignalOutcome.FAIL


def test_assertion_fail_takes_priority_and_retains_error_details():
    tests = ("t.py::a", "t.py::b")
    base = capture("t.py::a PASSED\nt.py::b PASSED\n", tests)
    patch = capture("t.py::a FAILED\nt.py::b ERROR\n", tests, code=1)
    report = score(base, patch, tests)
    assert report.signal is Signal.FAIL
    assert report.regressions == ("t.py::a",)
    assert report.regression_errors == ("t.py::b",)


@pytest.mark.parametrize(
    "base",
    [TestStatus.ERROR, TestStatus.FAILED, TestStatus.SKIPPED, TestStatus.XFAIL, TestStatus.XPASS],
)
def test_error_without_observed_base_pass_is_not_regression_error(base):
    assert classify("a", TestResult("a", base), TestResult("a", TestStatus.ERROR)) is Outcome.ERROR


def test_xpass_nonzero_exit_is_accounted_for_in_django():
    tests = ("tests/suite.py::Tests::a",)
    run = capture("a (suite.Tests) ... unexpected success\n", tests, "django", code=1)
    assert run.evidence_complete
    assert not run.infrastructure_errors
    assert run.results[0].status is TestStatus.XPASS


def test_fix1_cache_is_invalidated(tmp_path):
    config = RegressionConfig(baseline_cache_dir=tmp_path)
    (tmp_path / "task.baseline.json").write_text(
        json.dumps(
            {
                "parser_revision": "native-capture-v1",
                "results": [],
            }
        )
    )
    assert load_cached_baseline(config, "task") is None


def test_pytest_xpass_does_not_explain_nonzero_exit():
    run = capture("t.py::a XPASS\n", ("t.py::a",), code=1)
    assert "unexplained nonzero runner exit" in run.infrastructure_errors


def test_signal_record_preserves_regression_error_separately():
    from reliability.verifier.run import signal_from_regression

    tests = ("t.py::a",)
    report = score(
        capture("t.py::a PASSED\n", tests), capture("t.py::a ERROR\n", tests, code=1), tests
    )
    record = signal_from_regression(report)
    assert record.outcome is SignalOutcome.FAIL
    assert record.findings["signal"] == "REGRESSION_ERROR"
    assert record.findings["regression_errors"] == ["t.py::a"]
    assert record.findings["n_regression_errors"] == 1
    assert record.findings["summary"] == {"REGRESSION_ERROR": 1}
