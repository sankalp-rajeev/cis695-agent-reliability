"""Fix 1 native scoring fixtures; no containers or benchmark source execution."""

from reliability.verifier.container import run_from_capture
from reliability.verifier.regression import (
    Outcome,
    RegressionConfig,
    Signal,
    TestStatus,
    run_regression,
)
from reliability.verifier.result_parser import mapping_for, parse_capture
from reliability.verifier.selection import Selection, TestRunner


def captured(text, tests, runner="pytest", code=0):
    raw = text.encode()
    events = (
        {"event": "start", "batch": 1, "offset": 0},
        {"event": "end", "batch": 1, "offset": len(raw), "returncode": code, "split": False},
        {"event": "complete"},
    )
    return run_from_capture(
        TestRunner(runner, "fixture"), tuple(tests), runner_log=raw, events=events
    )


def score(base, patched, tests):
    class CapturedExecutor:
        def run(self, requested, *, patched, timeout_s):
            assert tuple(requested) == tuple(tests)
            return patched_result if patched else base

    patched_result = patched
    return run_regression(
        "fixture",
        Selection(tests=tuple(tests)),
        CapturedExecutor(),
        RegressionConfig(rerun_flaky=False),
    )


def test_ansi_parameter_and_teardown_error_are_admitted_to_native_scoring():
    family = "t.py::test_it"
    result = captured(
        "\x1b[32mt.py::test_it[a b]\x1b[0m PASSED\nt.py::test_it[a b] ERROR\n", [family], code=1
    )
    assert result.by_id()[family].status is TestStatus.ERROR
    assert result.raw_id_map["t.py::test_it[a b]"] == (family,)


def test_django_bare_status_docstring_and_summary_are_handled_natively():
    node = "tests/a/tests.py::Case::test_it"
    result = captured(
        "test_it (a.tests.Case)\nEnsure ('fieldpath', ClassName) is accepted\n"
        "warning from dependency\nok\nOK (skipped=2)\n",
        [node],
        runner="django",
    )
    assert result.by_id()[node].status is TestStatus.PASSED
    assert [r.test_id for r in result.raw_results] == ["a.tests.Case.test_it"]
    assert result.evidence_complete and not result.unmatched_ids


def test_shortened_django_identity_is_admitted_only_if_unique():
    selected = ["tests/a/tests.py::Case::test_it", "tests/b/tests.py::Case::test_it"]
    assert mapping_for(selected, "django")("Case.test_it") == []
    assert mapping_for(selected[:1], "django")("Case.test_it") == selected[:1]


def test_exact_plus_family_ambiguity_cannot_become_a_pass():
    tests = ["t.py::test_it", "t.py::test_it[1]"]
    result = captured("t.py::test_it[1] PASSED\n", tests)
    assert all(r.status is TestStatus.NOT_RUN for r in result.results)
    assert result.unmatched_ids == ("t.py::test_it[1]",)


def test_a_different_preexisting_parameter_failure_does_not_hide_a_regression():
    tests = ["t.py::test_it"]
    base = captured("t.py::test_it[old] FAILED\nt.py::test_it[new] PASSED\n", tests, code=1)
    patched = captured("t.py::test_it[old] FAILED\nt.py::test_it[new] FAILED\n", tests, code=1)
    report = score(base, patched, tests)
    assert report.signal is Signal.FAIL
    assert report.outcomes == {
        "t.py::test_it[old]": Outcome.PRE_EXISTING_FAIL,
        "t.py::test_it[new]": Outcome.REGRESSION,
    }


def test_changed_parameter_case_is_missing_not_a_cross_case_regression():
    tests = ["t.py::test_it"]
    base = captured("t.py::test_it[one] PASSED\n", tests)
    patched = captured("t.py::test_it[two] FAILED\n", tests, code=1)
    report = score(base, patched, tests)
    assert not report.regressions
    assert all(v is Outcome.NOT_RUN for v in report.outcomes.values())
    assert report.completeness == "INCOMPLETE_CONFIRMED"


def test_concrete_confirmation_does_not_use_a_sibling_failure_as_its_result():
    tests = ["t.py::test_it"]
    base = captured("t.py::test_it[old] FAILED\nt.py::test_it[new] PASSED\n", tests, code=1)
    patched = captured("t.py::test_it[old] FAILED\nt.py::test_it[new] FAILED\n", tests, code=1)
    calls = []

    class RecordedExecutor:
        def run(self, requested, *, patched, timeout_s):
            calls.append(tuple(requested))
            return [base, initial_patch, base][len(calls) - 1]

    initial_patch = patched
    report = run_regression("fixture", Selection(tests=tuple(tests)), RecordedExecutor())
    assert calls[-1] == ("t.py::test_it[new]",)
    assert report.outcomes["t.py::test_it[new]"] is Outcome.FLAKY
    assert report.signal is Signal.PASS


def test_native_loader_placeholder_error_is_not_admitted_as_a_test_body():
    tests = ["tests/a/tests.py::Case::test_missing"]
    result = captured(
        "test_missing (unittest.loader._FailedTest) ... ERROR\n", tests, runner="django", code=1
    )
    assert result.by_id()[tests[0]].status is TestStatus.NOT_RUN
    assert result.raw_results[0].status is TestStatus.ERROR
    assert result.unmatched_ids


def test_runner_abort_blocks_a_pass_even_if_some_results_are_readable():
    tests = ["t.py::test_it"]
    result = captured("t.py::test_it PASSED\n", tests, code=4)
    report = score(result, result, tests)
    assert report.signal is Signal.INCOMPLETE
    assert not result.evidence_complete


def test_xfail_and_xpass_flavors_are_retained_with_legacy_policy_until_fix2():
    parsed = parse_capture("t.py::a xfail\nt.py::b XPASS\n", "pytest")
    assert (parsed["t.py::a"]["flavor"], parsed["t.py::a"]["status"]) == ("XFAIL", "skipped")
    assert (parsed["t.py::b"]["flavor"], parsed["t.py::b"]["status"]) == ("XPASS", "passed")


def test_legacy_parsed_baseline_cache_cannot_mix_with_new_patched_results(tmp_path):
    import json

    from reliability.verifier.regression import load_cached_baseline, run_to_dict, save_baseline

    run = captured("t.py::test_it PASSED\n", ["t.py::test_it"])
    config = RegressionConfig(baseline_cache_dir=tmp_path)
    cache = tmp_path / "fixture.baseline.json"
    old = json.dumps({"instance_id": "fixture", **run_to_dict(run)})
    cache.write_text(old)
    assert load_cached_baseline(config, "fixture") is None
    assert cache.read_text() == old
    save_baseline(config, "fixture", run)
    assert (
        load_cached_baseline(config, "fixture").by_id()["t.py::test_it"].status is TestStatus.PASSED
    )
