"""The launch script must clear PYTHONPATH in every window it starts."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "launch_tmux.sh"
PY = ROOT / ".venv" / "bin" / "python"


def _commands() -> list[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "/opt/ros/jazzy/lib/python3.12/site-packages"
    proc = subprocess.run(
        ["bash", str(SCRIPT), "--print-commands",
         "configs/experiments/main_50_a.yaml"],
        cwd=ROOT, env=env, capture_output=True, text=True, check=True,
    )
    return proc.stdout.splitlines()


def test_generated_tmux_commands_clear_pythonpath():
    lines = _commands()
    runner = next(line for line in lines if line.startswith("runner "))
    notify = next(line for line in lines if line.startswith("notify "))
    for command in (runner, notify):
        assert "env -u PYTHONPATH" in command
    assert "run_pilot.py" in runner
    assert "notify.sh" in notify
    assert "bash --noprofile --norc" in runner


def test_print_commands_does_not_start_tmux():
    before = subprocess.run(
        ["tmux", "ls"], capture_output=True, text=True, check=False,
    ).stdout
    _commands()
    after = subprocess.run(
        ["tmux", "ls"], capture_output=True, text=True, check=False,
    ).stdout
    assert after == before


def test_resume_contamination_prints_an_instruction_without_a_traceback():
    env = os.environ.copy()
    env["PYTHONPATH"] = "/opt/ros/jazzy/lib/python3.12/site-packages"
    proc = subprocess.run(
        [str(PY), str(ROOT / "scripts" / "run_pilot.py"), "--resume", "main_50_a"],
        cwd=ROOT, env=env, capture_output=True, text=True, check=False,
    )
    combined = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "Traceback" not in combined
    assert "env -u PYTHONPATH" in combined
    assert "--resume main_50_a" in combined
    assert "This resume was not started" in combined
