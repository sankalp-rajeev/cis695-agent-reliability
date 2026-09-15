"""Interpreter environment capture and contamination detection.

This host has ROS 2 Jazzy installed, and sourcing its setup script exports
`PYTHONPATH=/opt/ros/jazzy/lib/python3.12/site-packages` into every shell. That
path is placed ahead of the project venv, so a bare interpreter can import
Python 3.12 packages into this 3.11 environment - modules the lockfile never
pinned and `uv run --frozen` cannot account for.

The visible symptom was pytest autoloading ROS plugins and dying on a missing
`lark`, but the dangerous case is quieter: an agent or verifier run that imports
a shadowed module and produces a subtly different result. A verifier that
silently imported a foreign `yaml` or `pytest` would be very hard to diagnose
after the fact, because nothing in the run record would show it.

Two defences, because clearing alone is not auditable:

1. `clean_env()` strips PYTHONPATH from the environment handed to subprocesses.
2. `interpreter_environment()` records the interpreter's actual import state so
   that contamination is visible in `meta.yaml` afterwards, even if a run was
   launched through a path that forgot to clear it.
"""

from __future__ import annotations

import os
import sys
import sysconfig
from pathlib import Path
from typing import Any

#: Environment variables that alter module resolution and so must not leak in.
IMPORT_AFFECTING_VARS = ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONNOUSERSITE")


class InterpreterContaminationError(RuntimeError):
    """Raised when the import path contains entries from outside the project."""


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _trusted_prefixes() -> list[Path]:
    """Directory trees whose presence on sys.path is expected."""
    candidates = [
        Path(sys.prefix),          # the active venv
        Path(sys.base_prefix),     # the stdlib behind it
        project_root(),
    ]
    for key in ("stdlib", "platstdlib", "purelib", "platlib"):
        path = sysconfig.get_paths().get(key)
        if path:
            candidates.append(Path(path))
    return [p.resolve() for p in candidates]


def foreign_sys_path_entries(sys_path: list[str] | None = None) -> list[str]:
    """Return `sys.path` entries that lie outside the venv, stdlib, and project.

    An empty result is the clean state. Anything listed here can shadow a pinned
    dependency and is therefore recorded in the run's provenance block.
    """
    entries = sys.path if sys_path is None else sys_path
    trusted = _trusted_prefixes()
    foreign = []

    for raw in entries:
        # '' means "the current directory", which is the project when runs are
        # launched from the repo root; it shadows nothing that is not ours.
        if not raw:
            continue
        try:
            resolved = Path(raw).resolve()
        except (OSError, ValueError):
            foreign.append(raw)
            continue
        if not any(resolved == t or t in resolved.parents for t in trusted):
            foreign.append(str(resolved))

    return foreign


def clean_env(base: dict[str, str] | None = None) -> dict[str, str]:
    """Return a copy of the environment with import-affecting variables removed.

    Use this for every subprocess that runs project code - agent runs, verifier
    runs, and harness invocations - not only for the test suite.
    """
    env = dict(os.environ if base is None else base)
    for var in IMPORT_AFFECTING_VARS:
        env.pop(var, None)
    return env


def interpreter_environment() -> dict[str, Any]:
    """Capture the import state of the running interpreter for the run record."""
    pythonpath = os.environ.get("PYTHONPATH", "")
    return {
        "python_version": sys.version.split()[0],
        "python_executable": sys.executable,
        "pythonpath": [p for p in pythonpath.split(os.pathsep) if p],
        "sys_path": [p for p in sys.path if p],
        "foreign_sys_path_entries": foreign_sys_path_entries(),
    }


def assert_clean_interpreter() -> None:
    """Raise if the import path is contaminated.

    Call at the start of runs whose results must be attributable to the locked
    dependency set. Recording alone is enough for analysis after the fact, but an
    experiment run is worth failing fast.
    """
    foreign = foreign_sys_path_entries()
    if foreign:
        raise InterpreterContaminationError(
            "sys.path contains entries outside the venv, stdlib, and project: "
            f"{foreign}. Clear PYTHONPATH before running "
            "(see scripts/test.sh and reliability.env.clean_env)."
        )
