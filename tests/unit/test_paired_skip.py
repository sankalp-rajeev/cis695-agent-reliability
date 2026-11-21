"""Paired-skip accounting over selected tests, raw cases, and confirmations."""

import json

import pytest

from reliability.verifier import guarded_v2
from reliability.verifier.decision import SignalOutcome
from reliability.verifier.regression import (
    Outcome,
    RegressionConfig,
    RegressionReport,
    RunResult,
    Signal,
    TestResult,
    TestStatus,
    completeness_of,
    run_regression,
)
from reliability.verifier.run_v1_4_1 import (
    DEFAULT_VERIFIER_CONFIG,
    load_v2_settings,
    v2_signal_for_decision,
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


@pytest.mark.parametrize(
    ("base_status", "study_outcome", "executed"),
    [(TestStatus.SKIPPED, SignalOutcome.PASS, 1),
     (TestStatus.PASSED, SignalOutcome.NOT_AVAILABLE, 2)],
)
def test_configured_primary_from_all_six_reports(base_status, study_outcome, executed, tmp_path, monkeypatch):
    healthy = "test_example.py::test_healthy"
    selection = Selection(tests=(TEST, healthy), fallback_used=True, fallback_tests=(TEST, healthy),
                          fallback_candidates_total=2)

    class Executor:
        def run(self, tests, *, patched, timeout_s):
            status = TestStatus.SKIPPED if patched else base_status
            return RunResult(results=(TestResult(TEST, status), TestResult(healthy, TestStatus.PASSED)),
                             evidence_complete=True)

    monkeypatch.setattr(guarded_v2, "health_for_run", lambda *args, **kwargs: {"halt_reasons": []})
    legacy = load_v2_settings(DEFAULT_VERIFIER_CONFIG)
    study = load_v2_settings(DEFAULT_VERIFIER_CONFIG.with_name("v1_5.yaml"))
    assert legacy is None
    assert study.selection.fallback_any_convention and study.selection.fallback_max_files == 5
    reports = guarded_v2.run_policies(
        "task", selection, Executor(), {"base": {}, "patched": {}}, tmp_path,
        primary_accounting=study.primary_accounting,
    )
    assert set(reports) == guarded_v2.V2_ACCOUNTINGS
    strict_signal = v2_signal_for_decision(reports, legacy)
    assert strict_signal.outcome is SignalOutcome.NOT_AVAILABLE
    assert "primary_accounting" not in strict_signal.findings
    study_signal = v2_signal_for_decision(reports, study)
    assert study_signal.outcome is study_outcome
    assert study_signal.findings["primary_accounting"] == "P_invalid_excluded"
    if study_outcome is SignalOutcome.PASS:
        assert study_signal.findings["n_executed"] == executed
        assert not study_signal.findings["incompleteness"]
    else:
        assert study_signal.findings["incompleteness"] == [f"patched: {TEST}: skipped"]
    assert study_signal.findings["fallback_candidates_total"] == 2
    assert study_signal.findings["test_results"][healthy] == {"outcome": "PASS", "from_fallback": True}
    payload = json.loads((tmp_path / "v2_policies.json").read_text())
    assert payload["primary_accounting"] == "P_invalid_excluded"
    assert set(payload["policies"]) == guarded_v2.V2_ACCOUNTINGS
    assert payload["policies"]["P_invalid_excluded"]["fallback_tests"] == [TEST, healthy]


def test_fallback_origin_for_concrete_and_nonfallback_outcome_ids():
    other = "test_other.py::test_other"
    report = RegressionReport(
        "task", Signal.FAIL,
        outcomes={RAW: Outcome.REGRESSION, other: Outcome.PASS},
        selection=Selection(tests=(TEST, other), fallback_used=True, fallback_tests=(TEST,)),
        patched=RunResult(raw_id_map={RAW: (TEST,)}),
    )
    assert guarded_v2.fallback_results(report) == {
        RAW: {"outcome": "REGRESSION", "from_fallback": True},
        other: {"outcome": "PASS", "from_fallback": False},
    }
