"""Amendment B10: V2 stops after 3 confirmed regressions (pass on base, fail on patched,
reproduced on both trees). V2 is then FAIL, with "regressions >= 3, stopped early" and the
tests run so far recorded. Below 3 confirmed regressions nothing changes."""

import inspect
from dataclasses import replace

from reliability.verifier import guarded_v2
from reliability.verifier.regression import (
    Outcome, RegressionConfig, RunResult, Signal, TestResult, TestStatus, run_regression,
)
from reliability.verifier.run import signal_from_regression
from reliability.verifier.selection import Selection

P, F = TestStatus.PASSED, TestStatus.FAILED


class Executor:
    """Initial runs from `base`/`patched`; confirmations from `confirm_patched` (else `patched`)."""

    def __init__(self, base, patched, confirm_patched=None):
        self.base, self.patched, self.confirm_patched = base, patched, confirm_patched or {}
        self.calls = []

    def run(self, tests, *, patched, timeout_s):
        self.calls.append((tuple(tests), patched))
        confirmation = len(self.calls) > 2
        source = self.patched if patched else self.base
        if confirmation and patched and tests[0] in self.confirm_patched:
            source = self.confirm_patched
        return RunResult(evidence_complete=True, results=tuple(
            TestResult(test_id=t, status=source[t]) for t in tests if t in source))


def make_ids(n):
    return tuple(f"tests/test_m.py::test_{i}" for i in range(n))


def report(executor, ids, stop=3):
    return run_regression("demo", Selection(tests=ids), executor,
                          RegressionConfig(skip_compatible=False, skip_paired=True, stop_after_regressions=stop))


def test_three_confirmed_regressions_stop_v2_early_as_fail():
    ids = make_ids(7)
    base = {t: P for t in ids}
    patched = {t: (F if i < 5 else P) for i, t in enumerate(ids)}
    executor = Executor(base, patched)
    result = report(executor, ids)
    assert result.signal is Signal.FAIL
    confirmations = executor.calls[2:]
    assert len(confirmations) == 3 * 6 and {c[0][0] for c in confirmations} == set(ids[:3])
    assert "regressions >= 3, stopped early" in result.notes
    assert result.early_exit == {
        "stopped_early": True, "after_confirmed_regressions": 3, "confirmed": list(ids[:3]),
        "not_confirmed": list(ids[3:5]), "tests_executed": 7, "confirmation_runs": 18}


def test_below_three_confirmed_regressions_nothing_changes():
    ids = make_ids(5)
    base = {t: P for t in ids}
    patched = {t: (F if i < 2 else P) for i, t in enumerate(ids)}
    stopped, plain = report(Executor(base, patched), ids), report(Executor(base, patched), ids, stop=None)
    same = lambda r: replace(r, duration_s=0.0)  # noqa: E731
    assert same(stopped) == same(plain) and stopped.early_exit is None and stopped.signal is Signal.FAIL


def test_unconfirmed_flaky_candidates_do_not_count():
    ids = make_ids(6)
    base = {t: P for t in ids}
    patched = {t: (F if i < 5 else P) for i, t in enumerate(ids)}
    executor = Executor(base, patched, confirm_patched={ids[0]: P})
    result = report(executor, ids)
    assert result.outcomes[ids[0]] is Outcome.FLAKY
    assert result.early_exit["confirmed"] == list(ids[1:4])
    assert result.early_exit["not_confirmed"] == [ids[4]]


def test_default_config_never_stops_early():
    ids = make_ids(5)
    base = {t: P for t in ids}
    executor = Executor(base, {t: F for t in ids})
    result = report(executor, ids, stop=None)
    assert result.early_exit is None and len(executor.calls[2:]) == 5 * 6


def test_an_early_exit_is_fail_even_when_evidence_is_incomplete():
    ids = make_ids(6)
    base = {t: P for t in ids}
    patched = {t: F for t in ids[:4]}  # ids[4:] never reported on the patched tree
    result = report(Executor(base, patched), ids)
    assert result.signal is Signal.FAIL and result.early_exit["stopped_early"] is True


def test_the_early_exit_is_recorded_in_the_v2_signal():
    ids = make_ids(5)
    result = report(Executor({t: P for t in ids}, {t: F for t in ids}), ids)
    signal = signal_from_regression(result)
    assert signal.findings["early_exit"]["stopped_early"] is True
    assert "regressions >= 3, stopped early" in signal.detail
    quiet = signal_from_regression(report(Executor({t: P for t in ids}, {t: P for t in ids}), ids))
    assert "early_exit" not in quiet.findings


def test_every_v2_policy_run_uses_the_same_stop():
    source = inspect.getsource(guarded_v2.run_policies)
    assert source.count("stop_after_regressions=V2_STOP_AFTER_REGRESSIONS") == 2
    assert guarded_v2.V2_STOP_AFTER_REGRESSIONS == 3
