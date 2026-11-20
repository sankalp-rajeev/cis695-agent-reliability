"""Paired-skip accounting over selected tests, raw cases, and confirmations."""

import pytest

from reliability.verifier.regression import (
    RegressionConfig,
    RunResult,
    Signal,
    TestResult,
    TestStatus,
    completeness_of,
    run_regression,
)
from reliability.verifier.selection import Selection

PAIRED = {"skip_compatible": False, "skip_paired": True}
TEST = "test_example.py::test_case"
RAW = TEST + "[a]"


def result(status):
    return RunResult(results=(TestResult(TEST, status),), evidence_complete=True)


@pytest.mark.parametrize(
    ("base", "patched", "expected"),
    [
        (TestStatus.SKIPPED, TestStatus.SKIPPED, "COMPLETE"),
        (TestStatus.PASSED, TestStatus.SKIPPED, "INCOMPLETE_CONFIRMED"),
        (TestStatus.SKIPPED, TestStatus.PASSED, "INCOMPLETE_CONFIRMED"),
        (TestStatus.SKIPPED, TestStatus.FAILED, "INCOMPLETE_CONFIRMED"),
    ],
)
def test_paired_selected_statuses(base, patched, expected):
    assert completeness_of((TEST,), result(base), result(patched), **PAIRED)[0] == expected


def test_confirmation_uses_strict_accounting():
    run = result(TestStatus.SKIPPED)
    strict = completeness_of((TEST,), run, run, skip_compatible=False)
    assert strict[0] == "INCOMPLETE_CONFIRMED"
    assert completeness_of((TEST,), run, run, **PAIRED) == strict


def test_no_skips_give_identical_results():
    base, patched = result(TestStatus.PASSED), result(TestStatus.FAILED)
    assert (
        completeness_of((TEST,), base, patched, skip_compatible=False)
        == completeness_of((TEST,), base, patched, skip_compatible=True)
        == completeness_of((TEST,), base, patched, **PAIRED)
        == ("COMPLETE", ())
    )


@pytest.mark.parametrize(
    ("patched_id", "patched_status", "expected"),
    [
        (RAW, TestStatus.SKIPPED, "COMPLETE"),
        (RAW, TestStatus.PASSED, "INCOMPLETE_CONFIRMED"),
        (TEST + "[b]", TestStatus.SKIPPED, "INCOMPLETE_CONFIRMED"),
    ],
)
def test_paired_raw_statuses_use_exact_id(patched_id, patched_status, expected):
    def raw_run(raw_id, status):
        return RunResult(
            results=(TestResult(TEST, TestStatus.NOT_RUN),),
            raw_results=(TestResult(raw_id, status),),
            raw_id_map={raw_id: (TEST,)},
            evidence_complete=True,
        )

    base = raw_run(RAW, TestStatus.SKIPPED)
    patched = raw_run(patched_id, patched_status)
    assert completeness_of((TEST,), base, patched, **PAIRED)[0] == expected


def test_paired_skips_are_not_executed_evidence():
    class Executor:
        def run(self, tests, *, patched, timeout_s):
            return result(TestStatus.SKIPPED)

    report = run_regression("test", Selection(tests=(TEST,)), Executor(), RegressionConfig(**PAIRED))
    assert report.signal is Signal.NOT_AVAILABLE
    assert report.n_executed == 0
    assert report.completeness == "COMPLETE"


def test_skip_modes_are_mutually_exclusive():
    with pytest.raises(ValueError, match="mutually exclusive"):
        RegressionConfig(skip_compatible=True, skip_paired=True)
    with pytest.raises(ValueError, match="mutually exclusive"):
        completeness_of((TEST,), None, None, skip_compatible=True, skip_paired=True)
