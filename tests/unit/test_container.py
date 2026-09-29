"""Container execution wiring (Phase 5.2, Phase 6.2).

Docker is not required here. What is tested is the logic that decides what to
run and how to read the result — in particular that a test pytest never
reported on comes back as NOT_RUN rather than being dropped, which is where an
unexecuted test would otherwise quietly stop counting.
"""

from __future__ import annotations

import json

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
        self.states: list[bool] = []
        self.timeout = False

    def exec(self, command, timeout_s=120):
        script = command if isinstance(command, str) else " ".join(command)
        self.calls.append(script)
        if self.timeout:
            raise TimeoutError
        for key, value in self.responses.items():
            if key in script:
                return value
        return 1, ""

    def set_patched(self, patched: bool) -> None:
        self.states.append(patched)


def report_json(**outcomes) -> str:
    return json.dumps({
        "tests": [{"nodeid": k, "outcome": v} for k, v in outcomes.items()]})


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


def test_results_are_read_from_the_json_report():
    container = FakeContainer({
        "pytest": (1, "..."),
        "cat": (0, report_json(**{"t.py::a": "passed", "t.py::b": "failed"})),
    })
    result = ContainerTestExecutor(container).run(
        ("t.py::a", "t.py::b"), patched=True, timeout_s=60)

    by_id = result.by_id()
    assert by_id["t.py::a"].status is TestStatus.PASSED
    assert by_id["t.py::b"].status is TestStatus.FAILED


def test_a_test_pytest_never_reported_is_not_run():
    """The load-bearing case: silence is not a pass."""
    container = FakeContainer({
        "pytest": (1, "collection error"),
        "cat": (0, report_json(**{"t.py::a": "passed"})),
    })
    result = ContainerTestExecutor(container).run(
        ("t.py::a", "t.py::missing"), patched=True, timeout_s=60)

    assert result.by_id()["t.py::missing"].status is TestStatus.NOT_RUN
    assert result.by_id()["t.py::missing"].status is not TestStatus.PASSED


def test_every_requested_test_appears_in_the_result():
    container = FakeContainer({"pytest": (1, ""), "cat": (1, "")})
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


def test_unparseable_report_falls_back_to_the_summary():
    container = FakeContainer({
        "pytest": (1, "t.py::a PASSED\nt.py::b FAILED\n"),
        "cat": (0, "not json at all"),
    })
    result = ContainerTestExecutor(container).run(
        ("t.py::a", "t.py::b"), patched=True, timeout_s=60)

    assert result.by_id()["t.py::a"].status is TestStatus.PASSED
    assert result.by_id()["t.py::b"].status is TestStatus.FAILED


def test_missing_report_falls_back_to_the_summary():
    container = FakeContainer({
        "pytest": (0, "t.py::a PASSED\n"), "cat": (1, "No such file")})
    result = ContainerTestExecutor(container).run(("t.py::a",), patched=True, timeout_s=60)
    assert result.by_id()["t.py::a"].status is TestStatus.PASSED


def test_test_ids_with_spaces_are_quoted():
    """An unquoted parametrised id would silently run the wrong thing."""
    container = FakeContainer({"pytest": (0, ""), "cat": (1, "")})
    ContainerTestExecutor(container).run(
        ("t.py::test[a b]",), patched=True, timeout_s=60)

    pytest_call = next(c for c in container.calls if "pytest" in c)
    assert "'t.py::test[a b]'" in pytest_call


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
