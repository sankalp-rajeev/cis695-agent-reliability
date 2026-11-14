"""Collection failures stay missing; module execution isolates load aborts."""

import json
import subprocess
import sys
from collections import Counter

import pytest

from reliability.env import clean_env
from reliability.verifier.collection import _NATIVE_DRIVER, _PYTEST_PLUGIN, ValidationPass
from reliability.verifier.container import _BATCH_DRIVER, run_from_capture
from reliability.verifier.id_validation import IDValidation, merge_native
from reliability.verifier.regression import (
    Outcome,
    RegressionConfig,
    RunResult,
    Signal,
    TestResult,
    TestStatus,
    run_regression,
)
from reliability.verifier.selection import Selection, TestRunner, django_label
from reliability.verifier.validated_run import apply_validation


def test_pytest_validation_collects_containing_files_and_intersects_selected_ids(tmp_path):
    (tmp_path / "test_sample.py").write_text(
        'def test_real(): raise AssertionError("must not execute")\n'
    )
    (tmp_path / "verifier_collect_plugin.py").write_text(_PYTEST_PLUGIN)
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps(
            {"runner": "pytest", "ids": ["test_sample.py::test_unverified"], "module_timeout_s": 30}
        )
    )
    driver = tmp_path / "driver.py"
    driver.write_text(
        _NATIVE_DRIVER.replace("/tmp/verifier_collect_request.json", str(request)).replace(
            "/tmp/verifier_collect_pgid", str(tmp_path / "pid")
        )
    )
    result = subprocess.run(
        [sys.executable, str(driver)],
        cwd=tmp_path,
        env=clean_env(),
        capture_output=True,
        text=True,
        check=True,
    )
    receipt = json.loads(result.stdout)
    command = receipt["groups"][0]["command"]
    assert "--collect-only" in command and "-q" in command
    assert command[-2:] == ["--", "test_sample.py"]
    assert all("::" not in arg for arg in command)
    assert receipt["ids"]["test_sample.py::test_unverified"]["ids"] == []
    assert receipt["ids"]["test_sample.py::test_unverified"]["completed"] is True
    assert receipt["ids"]["test_sample.py::test_unverified"]["reason"] == "native_not_found"


@pytest.mark.parametrize("status", ["COLLECTION_ERROR", "RUNNER_UNAVAILABLE"])
def test_collector_failure_is_missing_under_both_policies(status):
    tid = "t.py::test_a"
    record = IDValidation(tid, "runnable_test", (tid,))
    merged = merge_native(
        (record,),
        {
            tid: {
                "ids": [],
                "reason": status.lower(),
                "collection_status": status,
                "completed": False,
                "returncode": 1,
            }
        },
    )[0]
    assert merged.unavailable and merged.to_dict()["validation_status"] == status
    run = apply_validation(RunResult(evidence_complete=True), ValidationPass((merged,)))
    assert run.results[0].status is TestStatus(status.lower())

    class Executor:
        def run(self, *args, **kwargs):
            return run

    for compatible in (True, False):
        for invalid_missing in (True, False):
            report = run_regression(
                "task",
                Selection(tests=(tid,)),
                Executor(),
                RegressionConfig(skip_compatible=compatible, invalid_as_missing=invalid_missing),
            )
            assert report.signal is Signal.NOT_AVAILABLE
            assert report.completeness != "COMPLETE"
            assert not next(iter(report.outcomes.values())).executed


def test_only_agreed_static_and_native_absence_can_be_invalid():
    tid = "t.py::test_a"
    record = IDValidation(tid, "runnable_test", (tid,))
    for completed, code in ((False, 0), (True, 5), (True, 2)):
        r = merge_native(
            (record,),
            {
                tid: {
                    "ids": [],
                    "reason": "native_not_found",
                    "completed": completed,
                    "returncode": code,
                }
            },
        )[0]
        assert r.unavailable and r.failure_status == "COLLECTION_ERROR"
    r = merge_native((record,), {tid: {"ids": [], "completed": True, "returncode": 0}})[0]
    assert r.unavailable and r.failure_status == "COLLECTION_ERROR"
    proven = IDValidation(tid, "property", reason="property")
    r = merge_native(
        (proven,), {tid: {"ids": [], "completed": False, "collection_status": "RUNNER_UNAVAILABLE"}}
    )[0]
    assert r.unavailable and r.failure_status == "RUNNER_UNAVAILABLE"
    unknown = IDValidation(tid, "not_found", reason="source_parse_error")
    r = merge_native((unknown,), {})[0]
    assert r.unavailable


def test_invalid_denominator_sensitivity_changes_only_would_be_pass():
    ids = ("good", "invalid")
    run = RunResult(
        results=(
            TestResult("good", TestStatus.PASSED),
            TestResult("invalid", TestStatus.INVALID_ID),
        ),
        evidence_complete=True,
    )

    class Executor:
        def run(self, *args, **kwargs):
            return run

    for compatible in (True, False):
        a = run_regression(
            "task", Selection(tests=ids), Executor(), RegressionConfig(skip_compatible=compatible)
        )
        b = run_regression(
            "task",
            Selection(tests=ids),
            Executor(),
            RegressionConfig(skip_compatible=compatible, invalid_as_missing=True),
        )
        assert a.signal is Signal.PASS and b.signal is Signal.INCOMPLETE
        assert a.outcomes["invalid"] is Outcome.INVALID_ID


def driver_run(tmp_path, runner, tests):
    paths = {
        name: str(tmp_path / name)
        for name in (
            "verifier_ids",
            "verifier_out.txt",
            "verifier_events.jsonl",
            "verifier_pgid",
            "verifier_module_ids.json",
        )
    }
    native = [django_label(t) for t in tests] if runner == "django" else list(tests)
    (tmp_path / "verifier_ids").write_text("\n".join(native) + "\n")
    (tmp_path / "verifier_module_ids.json").write_text(
        json.dumps({n: t.split("::")[0] for n, t in zip(native, tests)})
    )
    code = _BATCH_DRIVER.replace('"python"', repr(sys.executable))
    for name, path in paths.items():
        code = code.replace("/tmp/" + name, path)
    driver = tmp_path / "driver.py"
    driver.write_text(code)
    subprocess.run(
        [sys.executable, str(driver), runner],
        cwd=tmp_path,
        env=clean_env(),
        capture_output=True,
        timeout=60,
        check=True,
    )
    events = tuple(
        json.loads(line) for line in (tmp_path / "verifier_events.jsonl").read_text().splitlines()
    )
    raw = (tmp_path / "verifier_out.txt").read_bytes()
    return run_from_capture(
        TestRunner(runner, ""), tuple(tests), runner_log=raw, events=events
    ), events


def test_one_process_per_module_instead_of_batches_of_25(tmp_path):
    (tmp_path / "test_a.py").write_text(
        "\n".join("def test_" + str(i) + "(): pass" for i in range(31))
    )
    (tmp_path / "test_b.py").write_text("def test_b(): pass\n")
    ids = tuple("test_a.py::test_" + str(i) for i in range(31)) + ("test_b.py::test_b",)
    result, events = driver_run(tmp_path, "pytest", ids)
    starts = [e for e in events if e["event"] == "start"]
    assert Counter(e["module"] for e in starts) == {"test_a.py": 1, "test_b.py": 1}
    assert all(r.status is TestStatus.PASSED for r in result.results)


def test_process_death_after_per_test_output_is_not_retried(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "runtests.py").write_text("""import sys
ids=sys.argv[2:]
if len(ids)>1:
 print('test_a (sample.Case.test_a) ... ok')
 print('bad (unittest.loader._FailedTest) ... ERROR')
 sys.exit(1)
for label in ids:
 print(label.rsplit('.',1)[1]+' ('+label+') ... ok')
""")
    ids = ("tests/sample.py::Case::test_a", "tests/sample.py::Case::test_b")
    result, events = driver_run(tmp_path, "django", ids)
    starts = [e for e in events if e["event"] == "start"]
    assert len(starts) == 1
    assert result.results[0].status is TestStatus.PASSED
    assert result.results[1].status is TestStatus.CRASH
    assert "tests/sample.py::Case::test_b" not in result.unmatched_ids
    assert "unittest.loader._FailedTest.bad" in result.unmatched_ids


def test_gis_guard_without_test_progress_retries_then_counts_as_infrastructure(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "runtests.py").write_text("""import sys
ids=sys.argv[2:]
if ids[0].startswith('gis_tests.'):
 print('Aborting: A GIS database backend is required to run gis_tests.')
 sys.exit(1)
for label in ids:
 print(label.rsplit('.',1)[1]+' ('+label+') ... ok')
""")
    ids = ("tests/gis_tests/test_a.py::Case::test_a", "tests/other/test_b.py::Case::test_b")
    result, events = driver_run(tmp_path, "django", ids)
    assert len([e for e in events if e["event"] == "start"]) == 3
    assert result.results[0].status is TestStatus.NOT_RUN
    assert result.results[1].status is TestStatus.PASSED
    assert any("module_execution identity failure" in e for e in result.infrastructure_errors)


def test_h1_invalid_never_increments_primary_numerator():
    from reliability.verifier.accounting import h1_accounting

    result = h1_accounting(range(10), {0, 1, 2, 3}, {2, 3, 4})
    assert result["primary_B1"] == 10
    assert result["admitted_original_slots"] == 2
    assert result["primary_H1_fraction"] == 0.2
    assert result["secondary_denominator"] == 7
    assert "SECONDARY" in result["secondary_label"]


@pytest.mark.parametrize("status", [TestStatus.COLLECTION_ERROR, TestStatus.RUNNER_UNAVAILABLE])
def test_collection_error_with_another_pass_cannot_become_pass(status):
    run = RunResult(
        results=(TestResult("ok", TestStatus.PASSED), TestResult("missing", status)),
        evidence_complete=True,
    )

    class Executor:
        def run(self, *args, **kwargs):
            return run

    for compatible in (True, False):
        for invalid_missing in (True, False):
            report = run_regression(
                "task",
                Selection(tests=("ok", "missing")),
                Executor(),
                RegressionConfig(skip_compatible=compatible, invalid_as_missing=invalid_missing),
            )
            assert report.signal is Signal.INCOMPLETE
