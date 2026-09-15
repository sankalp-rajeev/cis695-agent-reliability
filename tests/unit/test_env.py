"""Interpreter contamination detection.

Motivated by a real failure on this host: ROS 2 Jazzy exports
PYTHONPATH=/opt/ros/jazzy/lib/python3.12/site-packages, which shadows the
project's pinned 3.11 dependencies.
"""

from __future__ import annotations

import os
import sys
import sysconfig

import pytest

from reliability.env import (
    IMPORT_AFFECTING_VARS,
    InterpreterContaminationError,
    assert_clean_interpreter,
    clean_env,
    foreign_sys_path_entries,
    interpreter_environment,
)

ROS = "/opt/ros/jazzy/lib/python3.12/site-packages"


def test_venv_and_stdlib_paths_are_not_foreign():
    trusted = [sys.prefix, sysconfig.get_paths()["purelib"], sysconfig.get_paths()["stdlib"]]
    assert foreign_sys_path_entries(trusted) == []


def test_empty_entry_meaning_cwd_is_not_foreign():
    assert foreign_sys_path_entries([""]) == []


def test_ros_path_is_detected_as_foreign():
    assert foreign_sys_path_entries([ROS]) == [ROS]


def test_foreign_detection_is_order_independent():
    mixed = [sys.prefix, ROS, ""]
    assert foreign_sys_path_entries(mixed) == [ROS]


def test_clean_env_strips_every_import_affecting_var():
    dirty = {"PATH": "/usr/bin", **{v: "x" for v in IMPORT_AFFECTING_VARS}}
    cleaned = clean_env(dirty)

    assert cleaned["PATH"] == "/usr/bin"
    for var in IMPORT_AFFECTING_VARS:
        assert var not in cleaned


def test_clean_env_does_not_mutate_the_input():
    dirty = {"PYTHONPATH": ROS}
    clean_env(dirty)
    assert dirty == {"PYTHONPATH": ROS}


def test_interpreter_environment_reports_pythonpath(monkeypatch):
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join([ROS, "/other"]))
    assert interpreter_environment()["pythonpath"] == [ROS, "/other"]


def test_interpreter_environment_reports_cleared_pythonpath_as_empty(monkeypatch):
    monkeypatch.delenv("PYTHONPATH", raising=False)
    assert interpreter_environment()["pythonpath"] == []


def test_assert_clean_interpreter_passes_under_the_test_runner():
    """scripts/test.sh clears PYTHONPATH, so the suite itself must run clean."""
    assert_clean_interpreter()


def test_assert_clean_interpreter_raises_when_contaminated(monkeypatch):
    monkeypatch.syspath_prepend(ROS)
    with pytest.raises(InterpreterContaminationError, match="outside the venv"):
        assert_clean_interpreter()
