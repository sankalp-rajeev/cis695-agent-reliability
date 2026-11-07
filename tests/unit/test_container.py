"""Container execution wiring (Phase 5.2, Phase 6.2).

Docker is not required here. What is tested is the logic that decides what to
run and how to read the result — in particular that a test pytest never
reported on comes back as NOT_RUN rather than being dropped, which is where an
unexecuted test would otherwise quietly stop counting.
"""

from __future__ import annotations

import pytest

from reliability.verifier.container import (
    WORKDIR,
    ContainerCommandExecutor,
    ContainerRepoTree,
    ContainerTestExecutor,
    TaskContainer,
    image_for,
)
from reliability.verifier.regression import TestStatus


class FakeContainer:
    """Stands in for a live container, recording what was asked of it."""

    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls: list[str] = []
        self.inputs: list[tuple[str, str]] = []
        self.states: list[bool] = []
        self.timeout = False

    def exec(self, command, timeout_s=120):
        script = command if isinstance(command, str) else " ".join(command)
        self.calls.append(script)
        if self.timeout:
            raise TimeoutError
        if script.startswith(("cat >", "rm -f")):
            return 0, ""
        for key, value in self.responses.items():
            if key in script:
                return value
        return 1, ""

    def exec_input(self, command, data, timeout_s=60):
        self.inputs.append((command, data))
        return self.exec(command, timeout_s=timeout_s)

    def set_patched(self, patched: bool) -> None:
        self.states.append(patched)


# --- image naming ----------------------------------------------------------


def test_image_is_derived_from_the_instance_id():
    assert image_for("astropy__astropy-12907") == \
        "swebench/sweb.eval.x86_64.astropy_1776_astropy-12907:latest"


def test_image_name_is_lowercased():
    assert image_for("Django__Django-11133").endswith("django_1776_django-11133:latest")


def test_image_derivation_reads_no_oracle_field():
    """Standing a container up must not require the dataset row."""
    import inspect

    assert list(inspect.signature(image_for).parameters) == ["instance_id"]


# --- isolation -------------------------------------------------------------


def test_each_container_gets_a_unique_name():
    a = TaskContainer(instance_id="repo__proj-1", patch_text="")
    b = TaskContainer(instance_id="repo__proj-1", patch_text="")
    assert a.name != b.name
    assert "repo__proj-1".lower() in a.name


def test_stopping_an_unstarted_container_is_harmless():
    TaskContainer(instance_id="repo__proj-1", patch_text="").stop()


def test_exec_before_start_raises():
    from reliability.verifier.container import ContainerError

    with pytest.raises(ContainerError):
        TaskContainer(instance_id="repo__proj-1", patch_text="").exec(("true",))


# --- command executor ------------------------------------------------------


def test_command_executor_moves_the_tree_before_running():
    container = FakeContainer({"ruff": (0, "ok")})
    executor = ContainerCommandExecutor(container)

    assert executor.run(("ruff", "check"), patched=True, timeout_s=60) == (0, "ok")
    assert container.states == [True]


def test_command_executor_can_run_against_the_base_tree():
    container = FakeContainer({"ruff": (1, "E501")})
    ContainerCommandExecutor(container).run(("ruff",), patched=False, timeout_s=60)
    assert container.states == [False]


# --- test executor ---------------------------------------------------------


PYTEST_V = (
    "============ test session starts ============\n"
    "t.py::a PASSED                                          [ 50%]\n"
    "t.py::b FAILED                                          [100%]\n"
    "=========== 1 failed, 1 passed ===========\n"
)


def test_results_are_read_from_pytests_verbose_lines():
    container = FakeContainer({"verifier_driver.py pytest": (1, PYTEST_V)})
    result = ContainerTestExecutor(container).run(
        ("t.py::a", "t.py::b"), patched=True, timeout_s=60)

    by_id = result.by_id()
    assert by_id["t.py::a"].status is TestStatus.PASSED
    assert by_id["t.py::b"].status is TestStatus.FAILED
    assert result.note == ""


def test_the_runner_is_asked_for_no_plugin():
    """The image is whatever SWE-bench built. sklearn-12973 has no pytest-json-report."""
    from reliability.verifier.container import _BATCH_DRIVER

    assert "json-report" not in _BATCH_DRIVER
    assert "-v" in _BATCH_DRIVER


def test_the_driver_uses_nothing_newer_than_python_36():
    """It runs under the image's Python, which goes back to 3.6.

    `text=True` and `capture_output=True` are 3.7. Using them crashed the driver
    on scikit-learn before pytest started, so every selected test read NOT_RUN.
    """
    from reliability.verifier.container import _BATCH_DRIVER

    for needle in ("text=True", "capture_output", "removeprefix", ":=", "from __future__"):
        assert needle not in _BATCH_DRIVER, needle
    compile(_BATCH_DRIVER, "driver", "exec")


@pytest.mark.parametrize("line,expected", [
    ("t.py::a PASSED   [ 10%]", TestStatus.PASSED),
    ("t.py::a FAILED   [ 10%]", TestStatus.FAILED),
    ("t.py::a ERROR    [ 10%]", TestStatus.ERROR),
    ("t.py::a SKIPPED (no network)  [ 10%]", TestStatus.SKIPPED),
    ("t.py::a XFAIL  [ 10%]", TestStatus.XFAIL),
    ("t.py::a XPASS  [ 10%]", TestStatus.XPASS),
    ("t.py::a PASSED", TestStatus.PASSED),  # older pytest, no progress column
])
def test_every_pytest_outcome_word_is_mapped(line, expected):
    container = FakeContainer({"verifier_driver.py pytest": (0, line + "\n")})
    result = ContainerTestExecutor(container).run(("t.py::a",), patched=True, timeout_s=60)
    assert result.by_id()["t.py::a"].status is expected


def test_a_teardown_error_after_a_pass_stands_as_an_error():
    container = FakeContainer({"verifier_driver.py pytest": (1, (
        "t.py::a PASSED   [100%]\nt.py::a ERROR   [100%]\n"))})
    result = ContainerTestExecutor(container).run(("t.py::a",), patched=True, timeout_s=60)
    assert result.by_id()["t.py::a"].status is TestStatus.ERROR


def test_a_parametrised_id_with_a_space_is_matched():
    node = "t.py::test_x[a b]"
    container = FakeContainer({"verifier_driver.py pytest": (0, node + " PASSED  [100%]\n")})
    result = ContainerTestExecutor(container).run((node,), patched=True, timeout_s=60)
    assert result.by_id()[node].status is TestStatus.PASSED


def test_a_line_for_a_test_nobody_asked_about_is_ignored():
    container = FakeContainer({"verifier_driver.py pytest": (0, "other.py::z PASSED\n")})
    result = ContainerTestExecutor(container).run(("t.py::a",), patched=True, timeout_s=60)
    assert result.by_id()["t.py::a"].status is TestStatus.NOT_RUN


def test_a_test_pytest_never_reported_is_not_run():
    """The load-bearing case: silence is not a pass."""
    container = FakeContainer({"verifier_driver.py pytest": (1, "t.py::a PASSED\n")})
    result = ContainerTestExecutor(container).run(
        ("t.py::a", "t.py::missing"), patched=True, timeout_s=60)

    assert result.by_id()["t.py::missing"].status is TestStatus.NOT_RUN
    assert result.by_id()["t.py::missing"].status is not TestStatus.PASSED


def test_a_runner_that_reports_nothing_says_why():
    """A crashed runner must not read as an empty run (sklearn-12973)."""
    crash = (
        "Traceback (most recent call last):\n"
        '  File "/tmp/verifier_driver.py", line 17, in <module>\n'
        "TypeError: __init__() got an unexpected keyword argument 'text'\n"
    )
    container = FakeContainer({"verifier_driver.py pytest": (1, crash)})
    result = ContainerTestExecutor(container).run(("t.py::a",), patched=True, timeout_s=60)

    assert result.by_id()["t.py::a"].status is TestStatus.NOT_RUN
    assert "unexpected keyword argument 'text'" in result.note


def test_every_requested_test_appears_in_the_result():
    container = FakeContainer()
    tests = ("a.py::x", "b.py::y", "c.py::z")
    result = ContainerTestExecutor(container).run(tests, patched=True, timeout_s=60)
    assert set(result.by_id()) == set(tests)


def test_a_timeout_marks_every_test_timed_out():
    container = FakeContainer()
    container.timeout = True
    result = ContainerTestExecutor(container).run(
        ("t.py::a", "t.py::b"), patched=True, timeout_s=1)

    assert result.timed_out
    assert all(r.status is TestStatus.TIMEOUT for r in result.results)


def test_no_tests_means_no_container_work():
    container = FakeContainer()
    assert ContainerTestExecutor(container).run((), patched=True, timeout_s=60).results == ()
    assert container.calls == []


def test_test_ids_with_spaces_are_not_placed_on_the_shell_command():
    """An unquoted parametrised id in argv would silently run the wrong thing.

    Ids are written to a file. The docker exec that runs them stays short.
    """
    container = FakeContainer()
    node = "t.py::test[a b]"
    ContainerTestExecutor(container).run((node,), patched=True, timeout_s=60)

    launched = next(c for c in container.calls if "verifier_driver.py" in c)
    assert node not in launched
    ids = next(data for command, data in container.inputs if "verifier_ids" in command)
    assert node in ids


def test_django_runner_uses_runtests_and_parses_verbose_lines():
    from reliability.verifier.selection import TestRunner

    node = "tests/utils_tests/test_dateformat.py::DateFormatTests::test_year"
    container = FakeContainer({
        "verifier_driver.py django": (0, (
            "test_year (utils_tests.test_dateformat.DateFormatTests.test_year) ... ok\n"
            "\nOK\n"
        )),
    })
    result = ContainerTestExecutor(
        container, runner=TestRunner("django", "found tests/runtests.py"),
    ).run((node,), patched=True, timeout_s=60)

    assert result.by_id()[node].status is TestStatus.PASSED
    ids = next(data for command, data in container.inputs if "verifier_ids" in command)
    assert ids.strip() == "utils_tests.test_dateformat.DateFormatTests.test_year"
    driver = next(data for command, data in container.inputs if "verifier_driver" in command)
    assert "tests/runtests.py" in driver
    launched = next(
        c for c in container.calls if c.startswith("python /tmp/verifier_driver.py"))
    assert "django" in launched
    assert node not in launched


# --- repo tree -------------------------------------------------------------


def test_repo_tree_lists_tracked_files():
    container = FakeContainer({"git ls-files": (0, "b.py\na.py\n\n")})
    assert ContainerRepoTree(container).list_files() == ("a.py", "b.py")


def test_repo_tree_returns_empty_when_git_fails():
    assert ContainerRepoTree(FakeContainer()).list_files() == ()


def test_repo_tree_reads_files():
    container = FakeContainer({"cat": (0, "contents")})
    assert ContainerRepoTree(container).read_text("a.py") == "contents"


def test_repo_tree_returns_empty_for_a_missing_file():
    assert ContainerRepoTree(FakeContainer()).read_text("gone.py") == ""


def test_repo_tree_satisfies_the_selection_protocol():
    """Selection must not be able to reach anything else through the tree."""
    surface = {n for n in dir(ContainerRepoTree) if not n.startswith("_")}
    assert surface == {"container", "list_files", "read_text"}


def test_workdir_is_the_harness_testbed():
    assert WORKDIR == "/testbed"


# --- the driver itself, run for real ---------------------------------------


def _run_driver(tmp_path, ids):
    """Execute the in-container driver here, against real pytest, in a tmp project."""
    import subprocess
    import sys

    from reliability.verifier.container import _BATCH_DRIVER

    (tmp_path / "test_sample.py").write_text(
        "import pytest\n"
        "def test_ok():\n    assert True\n"
        "def test_bad():\n    assert False\n"
        "@pytest.mark.skip(reason='x')\n"
        "def test_skipped():\n    pass\n"
        "@pytest.mark.parametrize('v', ['a b', 'c'])\n"
        "def test_param(v):\n    assert v\n"
    )
    (tmp_path / "ids").write_text("\n".join(ids) + "\n")
    driver = (
        _BATCH_DRIVER.replace("/tmp/verifier_ids", str(tmp_path / "ids"))
        .replace("/tmp/verifier_out.txt", str(tmp_path / "out.txt"))
        .replace('"python"', repr(sys.executable))
    )
    script = tmp_path / "driver.py"
    script.write_text(driver)
    proc = subprocess.run(
        [sys.executable, str(script), "pytest"], cwd=tmp_path,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return proc.stdout.decode()


def test_the_real_driver_reports_results_without_any_plugin(tmp_path):
    from reliability.verifier.container import _parse_pytest

    ids = ("test_sample.py::test_ok", "test_sample.py::test_bad",
           "test_sample.py::test_skipped", "test_sample.py::test_param[a b]")
    statuses = _parse_pytest(_run_driver(tmp_path, ids), ids)

    assert statuses["test_sample.py::test_ok"] is TestStatus.PASSED
    assert statuses["test_sample.py::test_bad"] is TestStatus.FAILED
    assert statuses["test_sample.py::test_skipped"] is TestStatus.SKIPPED
    assert statuses["test_sample.py::test_param[a b]"] is TestStatus.PASSED


def test_one_unresolvable_id_does_not_take_its_batch_down(tmp_path):
    """Pytest aborts a whole batch on one bad id. Only that id may be lost."""
    from reliability.verifier.container import _parse_pytest

    ids = ("test_sample.py::test_ok", "test_sample.py::does_not_exist",
           "test_sample.py::test_bad")
    statuses = _parse_pytest(_run_driver(tmp_path, ids), ids)

    assert statuses["test_sample.py::test_ok"] is TestStatus.PASSED
    assert statuses["test_sample.py::test_bad"] is TestStatus.FAILED
    assert "test_sample.py::does_not_exist" not in statuses
