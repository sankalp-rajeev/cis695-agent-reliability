"""Failure confirmation is isolated, repeated on both trees, and label-free."""

from dataclasses import replace

import pytest

from reliability.verifier.regression import (
    Outcome,
    RegressionConfig,
    RunResult,
    Signal,
    TestResult,
    TestStatus,
    run_from_dict,
    run_regression,
    run_to_dict,
)
from reliability.verifier.run import signal_from_regression
from reliability.verifier.selection import Selection

PASS, FAIL, ERROR = TestStatus.PASSED, TestStatus.FAILED, TestStatus.ERROR
IDS = ('t.py::test_a', 't.py::test_b')


class Executor:
    def __init__(self, initial=FAIL, bases=None, patches=None):
        self.initial = initial
        self.bases = bases or [PASS] * 3
        self.patches = patches or [initial] * 3
        self.calls = []
        self.index = {False: 0, True: 0}

    def run(self, tests, *, patched, timeout_s):
        self.calls.append((tests, patched, timeout_s))
        if len(self.calls) <= 2:
            statuses = [self.initial if patched else PASS, PASS]
        else:
            assert len(tests) == 1
            statuses = [(self.patches if patched else self.bases)[self.index[patched]]]
            self.index[patched] += 1
        return RunResult(results=tuple(TestResult(t, s) for t, s in zip(tests, statuses) if s),
                         requested_tests=tests, evidence_complete=True)


@pytest.mark.parametrize('initial,outcome,signal', [(FAIL, Outcome.REGRESSION, Signal.FAIL),
                                                   (ERROR, Outcome.REGRESSION_ERROR, Signal.REGRESSION_ERROR)])
def test_each_new_failure_requires_three_isolated_calls_per_tree(initial, outcome, signal):
    executor = Executor(initial)
    report = run_regression('task', Selection(tests=IDS), executor)
    assert report.signal is signal and report.outcomes[IDS[0]] is outcome
    assert len(report.confirmations) == 6
    assert executor.calls[2:] == [((IDS[0],), tree, 1800) for tree in (False, True) for _ in range(3)]
    assert report.confirmation_summary[0]['stable']
    assert report.confirmation_summary[0]['base_PASS'] == 3
    assert report.confirmation_summary[0]['patched_non_PASS'] == 3
    for i, run in enumerate(report.confirmations):
        assert run.confirmation == {'candidate_id': IDS[0], 'tree': 'base' if i < 3 else 'patched',
                                    'attempt': i % 3 + 1, 'attempts_per_tree': 3, 'isolated': True}
        assert run_from_dict(run_to_dict(run)) == run
    assert signal_from_regression(report).findings['confirmation_summary'] == list(report.confirmation_summary)


@pytest.mark.parametrize('initial', [FAIL, ERROR])
@pytest.mark.parametrize('tree,status', [('base', FAIL), ('base', TestStatus.SKIPPED),
                                         ('patched', PASS), ('patched', TestStatus.XFAIL),
                                         ('patched', TestStatus.COLLECTION_ERROR), ('patched', None)])
def test_unstable_or_missing_confirmation_is_flaky_and_all_six_attempts_run(initial, tree, status):
    bases, patches = [PASS] * 3, [initial] * 3
    (bases if tree == 'base' else patches)[1] = status
    executor = Executor(initial, bases, patches)
    report = run_regression('task', Selection(tests=IDS), executor)
    expected=(Outcome.COLLECTION_ERROR if status is TestStatus.COLLECTION_ERROR else
              Outcome.NOT_RUN if status is None else
              (Outcome.REGRESSION if initial is FAIL else Outcome.REGRESSION_ERROR) if tree=='patched' and status is TestStatus.XFAIL else Outcome.FLAKY)
    assert report.outcomes[IDS[0]] is expected
    assert len(report.confirmations)==6
    stable=tree=='patched' and status is TestStatus.XFAIL
    assert report.confirmation_summary[0]['stable'] is stable
    if not stable:
        assert report.signal not in (Signal.FAIL,Signal.REGRESSION_ERROR)
    if status is None or status is TestStatus.COLLECTION_ERROR:
        assert report.signal is Signal.INCOMPLETE


def test_multiple_candidates_are_never_batched_in_confirmation():
    class Both:
        def __init__(self): self.calls = []
        def run(self, tests, *, patched, timeout_s):
            self.calls.append((tests, patched))
            return RunResult(results=tuple(TestResult(t, FAIL if patched else PASS) for t in tests),
                             requested_tests=tests, evidence_complete=True)
    executor = Both()
    report = run_regression('task', Selection(tests=IDS), executor)
    assert report.signal is Signal.FAIL
    assert len(report.confirmations) == 12
    assert [t for tests, _ in executor.calls[2:] for t in tests] == [IDS[0]] * 6 + [IDS[1]] * 6


def test_parameter_failure_confirmation_uses_only_its_concrete_identity():
    family, failed = 't.py::test_param', 't.py::test_param[bad]'
    class Parameters:
        def __init__(self): self.calls = []
        def run(self, tests, *, patched, timeout_s):
            self.calls.append(tests)
            concrete = (failed, 't.py::test_param[good]') if tests == (family,) else tests
            cases = tuple(TestResult(t, FAIL if patched and t == failed else PASS) for t in concrete)
            return RunResult(results=tuple(TestResult(t, FAIL if patched else PASS) for t in tests),
                             raw_results=cases, raw_id_map={t: tests for t in concrete},
                             requested_tests=tests, evidence_complete=True)
    executor = Parameters()
    report = run_regression('task', Selection(tests=(family,)), executor)
    assert report.regressions == (failed,)
    assert executor.calls[2:] == [(failed,)] * 6


def test_confirmation_bypasses_cached_initial_baseline(tmp_path):
    from reliability.verifier.regression import save_baseline
    config = RegressionConfig(baseline_cache_dir=tmp_path)
    cached = RunResult(results=tuple(TestResult(t, PASS) for t in IDS), evidence_complete=True)
    save_baseline(config, 'task', cached)
    class Cached(Executor):
        def run(self, tests, *, patched, timeout_s):
            # Account for the cached initial base when using the scripted fixture.
            if not self.calls: self.calls.append((IDS, False, timeout_s))
            return super().run(tests, patched=patched, timeout_s=timeout_s)
    executor = Cached()
    report = run_regression('task', Selection(tests=IDS), executor, config)
    assert report.baseline_from_cache
    assert executor.index == {False: 3, True: 3}
    assert len(report.confirmations) == 6


def test_observed_failures_with_interrupted_confirmation_are_not_stable():
    class Interrupted(Executor):
        def run(self, *args, **kwargs):
            run = super().run(*args, **kwargs)
            return replace(run, timed_out=True) if len(self.calls) == 3 else run
    report = run_regression('task', Selection(tests=IDS), Interrupted())
    assert report.outcomes[IDS[0]] is Outcome.FLAKY
    assert report.signal is Signal.INCOMPLETE
