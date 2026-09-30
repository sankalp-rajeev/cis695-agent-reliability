"""Phase 5.2 gate: baseline pass, outcome classification, and caching.

Covers every outcome the policy defines. The two properties that matter most:
only pass-to-fail transitions count as regressions, and an unexecuted test is
never a pass.
"""

from __future__ import annotations

import pytest

from reliability.verifier.regression import (
    Outcome,
    RegressionConfig,
    RunResult,
    Signal,
    TestResult,
    TestStatus,
    classify,
    load_cached_baseline,
    run_regression,
    save_baseline,
)
from reliability.verifier.selection import Selection

TESTS = ("tests/test_a.py::test_one", "tests/test_b.py::test_two")


def selection(*tests: str) -> Selection:
    return Selection(tests=tests or TESTS)


def result(test_id: str, status: TestStatus) -> TestResult:
    return TestResult(test_id=test_id, status=status)


class ScriptedExecutor:
    """Replays fixed results. Stands in for running tests in the container."""

    def __init__(self, base: dict, patched: dict, rerun: dict | None = None):
        self._base, self._patched, self._rerun = base, patched, rerun or {}
        self.calls: list[tuple[bool, tuple[str, ...]]] = []
        self._patched_calls = 0

    def run(self, tests, *, patched: bool, timeout_s: int) -> RunResult:
        self.calls.append((patched, tuple(tests)))
        if not patched:
            source = self._base
        else:
            self._patched_calls += 1
            source = self._rerun if self._patched_calls > 1 and self._rerun else self._patched
        return RunResult(results=tuple(
            result(t, source[t]) for t in tests if t in source
        ))


# --- classification: every outcome ----------------------------------------


@pytest.mark.parametrize(
    "base,patched,expected",
    [
        (TestStatus.PASSED, TestStatus.PASSED, Outcome.PASS),
        (TestStatus.PASSED, TestStatus.FAILED, Outcome.REGRESSION),
        (TestStatus.FAILED, TestStatus.FAILED, Outcome.PRE_EXISTING_FAIL),
        (TestStatus.FAILED, TestStatus.PASSED, Outcome.NEWLY_PASSING),
        (TestStatus.PASSED, TestStatus.TIMEOUT, Outcome.TIMEOUT),
        (TestStatus.PASSED, TestStatus.NOT_RUN, Outcome.NOT_RUN),
        (TestStatus.PASSED, TestStatus.ERROR, Outcome.ERROR),
        (TestStatus.ERROR, TestStatus.PASSED, Outcome.ERROR),
        (TestStatus.SKIPPED, TestStatus.SKIPPED, Outcome.PASS),
    ],
)
def test_classification_matrix(base, patched, expected):
    assert classify("t", result("t", base), result("t", patched)) is expected


def test_only_pass_to_fail_is_a_regression():
    """A test already failing on base is not the patch's fault."""
    assert classify("t", result("t", TestStatus.FAILED),
                    result("t", TestStatus.FAILED)) is not Outcome.REGRESSION
    assert classify("t", result("t", TestStatus.PASSED),
                    result("t", TestStatus.FAILED)) is Outcome.REGRESSION


def test_missing_from_patched_run_is_not_run_not_pass():
    assert classify("t", result("t", TestStatus.PASSED), None) is Outcome.NOT_RUN


def test_missing_from_base_run_is_not_run_not_pass():
    """Without a baseline there is no transition to establish. Not a pass."""
    assert classify("t", None, result("t", TestStatus.PASSED)) is Outcome.NOT_RUN


def test_unexecuted_outcomes_are_flagged_as_such():
    assert not Outcome.NOT_RUN.executed
    assert not Outcome.TIMEOUT.executed
    assert Outcome.PASS.executed
    assert Outcome.REGRESSION.executed


@pytest.mark.parametrize("outcome", [Outcome.NOT_RUN, Outcome.TIMEOUT])
def test_unexecuted_is_never_a_pass(outcome):
    assert outcome is not Outcome.PASS
    assert not outcome.counts_as_regression


# --- the baseline pass -----------------------------------------------------


def test_pre_existing_failure_does_not_reject_the_patch():
    """The reason the baseline exists at all."""
    executor = ScriptedExecutor(
        base={TESTS[0]: TestStatus.PASSED, TESTS[1]: TestStatus.FAILED},
        patched={TESTS[0]: TestStatus.PASSED, TESTS[1]: TestStatus.FAILED},
    )
    report = run_regression("inst", selection(), executor)

    assert report.signal is Signal.PASS
    assert report.outcomes[TESTS[1]] is Outcome.PRE_EXISTING_FAIL
    assert report.n_regressions == 0


def test_real_regression_fails_the_signal():
    executor = ScriptedExecutor(
        base={TESTS[0]: TestStatus.PASSED, TESTS[1]: TestStatus.PASSED},
        patched={TESTS[0]: TestStatus.PASSED, TESTS[1]: TestStatus.FAILED},
        rerun={TESTS[1]: TestStatus.FAILED},
    )
    report = run_regression("inst", selection(), executor)

    assert report.signal is Signal.FAIL
    assert report.regressions == (TESTS[1],)


def test_both_passes_are_run():
    executor = ScriptedExecutor(
        base={t: TestStatus.PASSED for t in TESTS},
        patched={t: TestStatus.PASSED for t in TESTS},
    )
    run_regression("inst", selection(), executor)
    assert [patched for patched, _ in executor.calls][:2] == [False, True]


# --- caching ---------------------------------------------------------------


def test_baseline_is_cached_and_reused(tmp_path):
    config = RegressionConfig(baseline_cache_dir=tmp_path)
    base = {t: TestStatus.PASSED for t in TESTS}
    patched = {t: TestStatus.PASSED for t in TESTS}

    first = run_regression("inst", selection(), ScriptedExecutor(base, patched), config)
    assert not first.baseline_from_cache

    second_executor = ScriptedExecutor(base, patched)
    second = run_regression("inst", selection(), second_executor, config)

    assert second.baseline_from_cache
    assert [p for p, _ in second_executor.calls] == [True]  # no baseline pass


def test_cache_round_trips(tmp_path):
    config = RegressionConfig(baseline_cache_dir=tmp_path)
    run = RunResult(results=(
        result("a", TestStatus.PASSED), result("b", TestStatus.FAILED)))
    save_baseline(config, "inst", run)

    loaded = load_cached_baseline(config, "inst")
    assert loaded.by_id()["a"].status is TestStatus.PASSED
    assert loaded.by_id()["b"].status is TestStatus.FAILED


def test_cache_is_per_instance(tmp_path):
    config = RegressionConfig(baseline_cache_dir=tmp_path)
    save_baseline(config, "inst_a", RunResult(results=(result("a", TestStatus.PASSED),)))
    save_baseline(config, "inst_b", RunResult(results=(result("b", TestStatus.FAILED),)))

    assert load_cached_baseline(config, "inst_a").by_id().keys() == {"a"}
    assert load_cached_baseline(config, "inst_b").by_id().keys() == {"b"}
    assert load_cached_baseline(config, "inst_c") is None


def test_no_cache_dir_means_no_caching(tmp_path):
    config = RegressionConfig(baseline_cache_dir=None)
    save_baseline(config, "inst", RunResult())
    assert load_cached_baseline(config, "inst") is None
    assert not list(tmp_path.iterdir())


def test_a_baseline_in_which_nothing_ran_is_not_cached(tmp_path):
    """Caching it would hand every later run the same empty answer."""
    config = RegressionConfig(baseline_cache_dir=tmp_path)
    broken = ScriptedExecutor({}, {})

    report = run_regression("inst", selection(), broken, config)

    assert report.signal is Signal.NOT_AVAILABLE
    assert load_cached_baseline(config, "inst") is None


def test_a_runner_that_reported_nothing_says_why_in_the_notes():
    class Crashed:
        def run(self, tests, *, patched, timeout_s):
            return RunResult(
                results=tuple(result(t, TestStatus.NOT_RUN) for t in tests),
                note="the test runner reported no results; output ended: TypeError")

    report = run_regression("inst", selection(), Crashed(), RegressionConfig())

    assert any("baseline: the test runner reported no results" in n for n in report.notes)
    assert any("patched: the test runner reported no results" in n for n in report.notes)


# --- §4.1 flake handling ---------------------------------------------------


def test_regression_that_passes_on_rerun_is_flaky():
    """A nondeterministic test must not land in the false-rejection rate."""
    executor = ScriptedExecutor(
        base={t: TestStatus.PASSED for t in TESTS},
        patched={TESTS[0]: TestStatus.PASSED, TESTS[1]: TestStatus.FAILED},
        rerun={TESTS[1]: TestStatus.PASSED},
    )
    report = run_regression("inst", selection(), executor)

    assert report.outcomes[TESTS[1]] is Outcome.FLAKY
    assert report.signal is Signal.PASS
    assert any("FLAKY" in n for n in report.notes)


def test_flake_rerun_can_be_disabled():
    executor = ScriptedExecutor(
        base={t: TestStatus.PASSED for t in TESTS},
        patched={TESTS[0]: TestStatus.PASSED, TESTS[1]: TestStatus.FAILED},
        rerun={TESTS[1]: TestStatus.PASSED},
    )
    report = run_regression("inst", selection(), executor,
                            RegressionConfig(rerun_flaky=False))
    assert report.signal is Signal.FAIL


# --- §5.1/§5.2/§5.5 edge cases --------------------------------------------


def test_no_tests_selected_is_not_available():
    report = run_regression("inst", Selection(tests=()), ScriptedExecutor({}, {}))
    assert report.signal is Signal.NOT_AVAILABLE
    assert report.signal is not Signal.PASS


def test_selected_but_nothing_executed_is_not_available():
    """The failure this guards: accepting on the strength of work not done."""
    executor = ScriptedExecutor(base={}, patched={})
    report = run_regression("inst", selection(), executor)

    assert report.signal is Signal.NOT_AVAILABLE
    assert report.n_executed == 0
    assert all(o is Outcome.NOT_RUN for o in report.outcomes.values())


def test_catastrophically_broken_baseline_is_flagged():
    """Policy §5.5: a mostly-red baseline indicts the environment."""
    tests = tuple(f"t{i}" for i in range(4))
    executor = ScriptedExecutor(
        base={t: TestStatus.FAILED for t in tests},
        patched={t: TestStatus.PASSED for t in tests},
    )
    report = run_regression("inst", selection(*tests), executor)

    assert report.signal is Signal.BASELINE_UNRELIABLE
    assert report.signal is not Signal.PASS


def test_baseline_at_threshold_is_still_usable():
    tests = tuple(f"t{i}" for i in range(4))
    executor = ScriptedExecutor(
        base={tests[0]: TestStatus.FAILED, tests[1]: TestStatus.FAILED,
              tests[2]: TestStatus.PASSED, tests[3]: TestStatus.PASSED},
        patched={t: TestStatus.PASSED for t in tests},
    )
    report = run_regression("inst", selection(*tests), executor)
    assert report.signal is not Signal.BASELINE_UNRELIABLE


def test_timeout_does_not_produce_a_pass():
    executor = ScriptedExecutor(
        base={t: TestStatus.PASSED for t in TESTS},
        patched={TESTS[0]: TestStatus.PASSED, TESTS[1]: TestStatus.TIMEOUT},
    )
    report = run_regression("inst", selection(), executor)

    assert report.outcomes[TESTS[1]] is Outcome.TIMEOUT
    assert report.count(Outcome.PASS) == 1


def test_newly_passing_is_recorded_but_does_not_drive_the_signal():
    """Policy §8 Q4: recorded, currently unused."""
    executor = ScriptedExecutor(
        base={TESTS[0]: TestStatus.FAILED, TESTS[1]: TestStatus.PASSED},
        patched={TESTS[0]: TestStatus.PASSED, TESTS[1]: TestStatus.PASSED},
    )
    report = run_regression("inst", selection(), executor)

    assert report.outcomes[TESTS[0]] is Outcome.NEWLY_PASSING
    assert report.signal is Signal.PASS


def test_report_summary_counts_outcomes():
    executor = ScriptedExecutor(
        base={TESTS[0]: TestStatus.PASSED, TESTS[1]: TestStatus.FAILED},
        patched={TESTS[0]: TestStatus.PASSED, TESTS[1]: TestStatus.FAILED},
    )
    report = run_regression("inst", selection(), executor)
    assert report.summary == {"PASS": 1, "PRE_EXISTING_FAIL": 1}


def test_signal_pass_requires_both_zero_regressions_and_execution():
    """Policy §4: zero regressions is not sufficient if nothing ran."""
    nothing_ran = run_regression("inst", selection(), ScriptedExecutor({}, {}))
    assert nothing_ran.n_regressions == 0
    assert nothing_ran.signal is Signal.NOT_AVAILABLE  # not PASS
