"""Conda package-cache mask and the newer-copy audit tiers.

Trajectories here are synthetic. Nothing under runs/ is read.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from reliability.agent.isolation import (
    IsolationError,
    assert_network_none,
    isolate_run_args,
)
from reliability.benchmark.leakage import Severity, audit, audit_task

ROOT = Path(__file__).resolve().parents[2]


def _task(tmp_path: Path, instance_id: str, messages: list[dict]) -> Path:
    task_dir = tmp_path / "exp" / "tasks" / instance_id
    task_dir.mkdir(parents=True)
    (task_dir / "repair_record.json").write_text('{"instance_id": "x"}\n')
    (task_dir / "trajectory.jsonl").write_text(
        "".join(json.dumps(message) + "\n" for message in messages)
    )
    return task_dir


def _turn(command: str, *, returncode: int, output: str, call_id: str = "c1") -> list[dict]:
    return [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "id": call_id,
                "type": "function",
                "function": {
                    "name": "bash",
                    "arguments": json.dumps({"command": command}),
                },
            }],
        },
        {
            "role": "tool",
            "tool_call_id": call_id,
            "content": f"<returncode>{returncode}</returncode>\n<output>\n{output}\n</output>",
        },
    ]


def _newer(tmp_path: Path, instance_id: str, messages: list[dict]):
    findings, _ = audit_task(_task(tmp_path, instance_id, messages), None)
    return [finding for finding in findings if finding.kind.startswith("newer-copy")]


def test_a_masked_cache_read_that_returns_content_fails(tmp_path):
    command = (
        "sed -n '300,340p' /opt/miniconda3/pkgs/xarray-2025.4.0-py310h06a4308_0"
        "/lib/python3.10/site-packages/xarray/computation/rolling.py"
    )
    findings = _newer(tmp_path, "pydata__xarray-4629", _turn(command, returncode=0, output="def rolling"))
    assert len(findings) == 1
    assert findings[0].kind == "newer-copy-path"
    assert findings[0].severity is Severity.CONFIRMED


def test_an_unmaskable_requests_copy_is_exposed_and_does_not_fail(tmp_path):
    findings = _newer(
        tmp_path, "psf__requests-1921",
        _turn(
            "cat /opt/miniconda3/lib/python3.11/site-packages/requests/sessions.py",
            returncode=0, output="class Session",
        ),
    )
    assert len(findings) == 1
    assert findings[0].kind == "newer-copy-path"
    assert findings[0].severity is Severity.EXPOSED_COPY
    assert findings[0].severity is not Severity.CONFIRMED
    assert "exposed_copy" in findings[0].detail
    assert "psf__requests-1921" in findings[0].detail


def test_listing_the_masked_cache_is_not_a_failure(tmp_path):
    findings = _newer(
        tmp_path, "pydata__xarray-4629",
        _turn("ls /opt/miniconda3/pkgs", returncode=0, output="xarray-2025.4.0\n"),
    )
    assert len(findings) == 1
    assert findings[0].kind == "newer-copy-listing"
    assert findings[0].severity is not Severity.CONFIRMED


def test_the_repository_and_the_task_install_are_not_newer_copies(tmp_path):
    messages = _turn(
        "cat /testbed/xarray/core/rolling.py", returncode=0, output="def rolling", call_id="a",
    ) + _turn(
        "cat /opt/miniconda3/envs/testbed/lib/python3.9/site-packages/requests/models.py",
        returncode=0, output="class Request", call_id="b",
    )
    assert _newer(tmp_path, "psf__requests-1921", messages) == []


@pytest.mark.parametrize("returncode,output", [(1, "no such file"), (0, ""), (0, "\n")])
def test_a_read_without_content_is_not_counted(tmp_path, returncode, output):
    command = "cat /opt/miniconda3/lib/python3.11/site-packages/requests/sessions.py"
    assert _newer(
        tmp_path, "psf__requests-1921",
        _turn(command, returncode=returncode, output=output),
    ) == []


@pytest.mark.parametrize("name", ["swebench_claim.yaml", "v4_generator.yaml"])
def test_agent_configs_mask_the_package_cache_and_keep_network_none(name):
    config = yaml.safe_load((ROOT / "configs" / "agent" / name).read_text())
    args = config["environment"]["run_args"]
    assert args[args.index("--network") + 1] == "none"
    assert "--tmpfs" in args
    assert "/opt/miniconda3/pkgs" in args
    assert args[args.index("--tmpfs") + 1] == "/opt/miniconda3/pkgs"


def test_any_other_network_is_still_refused():
    with pytest.raises(IsolationError, match="host"):
        isolate_run_args(["--rm", "--tmpfs", "/opt/miniconda3/pkgs", "--network", "host"])


_FP_AGENT = (
    'id; echo "---"; umount /opt/miniconda3/pkgs 2>&1; echo "exit: $?"; '
    "ls -la /opt/miniconda3/pkgs 2>&1 | head"
)
_FP_GENERATOR = (
    "pip cache list 2>/dev/null | head -20; "
    "ls /opt/miniconda3/pkgs 2>/dev/null | grep -i matplotlib | head"
)
_COMPOUND_READS = (
    'grep -R "def polyval" -n /opt/miniconda3/pkgs/X | head; '
    "sed -n '1,40p' /opt/miniconda3/pkgs/X/f.py"
)
_PYTHONPATH_READ = """cd /tmp && PYTHONPATH=/opt/miniconda3/pkgs/X/lib/python3.10/site-packages python - <<EOF
import xarray as xr
print(xr.__version__)
EOF"""


def _kinds(tmp_path, command, output="package text"):
    findings = _newer(
        tmp_path, "pydata__xarray-4629",
        _turn(command, returncode=0, output=output),
    )
    return findings


@pytest.mark.parametrize("command", [_FP_AGENT, _FP_GENERATOR])
def test_compound_commands_whose_output_is_elsewhere_are_ambiguous(tmp_path, command):
    findings = _kinds(tmp_path, command, output="uid=0\nnot a package file")
    assert len(findings) == 1
    assert findings[0].kind == "newer-copy-ambiguous"
    assert findings[0].severity is not Severity.CONFIRMED
    task = _task(tmp_path / "gate", "pydata__xarray-4629", _turn(
        command, returncode=0, output="uid=0\nnot a package file",
    ))
    result = audit([task])
    assert result.passed
    assert not result.confirmed


def test_a_compound_command_of_only_masked_reads_fails(tmp_path):
    findings = _kinds(tmp_path, _COMPOUND_READS, output="def polyval")
    assert len(findings) == 1
    assert findings[0].kind == "newer-copy-path"
    assert findings[0].severity is Severity.CONFIRMED


def test_pythonpath_into_the_masked_cache_fails(tmp_path):
    findings = _kinds(tmp_path, _PYTHONPATH_READ, output="2025.4.0")
    assert len(findings) == 1
    assert findings[0].kind == "newer-copy-path"
    assert findings[0].severity is Severity.CONFIRMED


class _Completed:
    def __init__(self, stdout: str, returncode: int = 0, stderr: str = ""):
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = stderr


def _inspect(monkeypatch, *, network: str, tmpfs: str):
    def fake_run(cmd, **kwargs):
        fmt = cmd[cmd.index("-f") + 1]
        if "NetworkMode" in fmt:
            return _Completed(network)
        if "Tmpfs" in fmt:
            return _Completed(tmpfs)
        raise AssertionError(cmd)

    monkeypatch.setattr("reliability.agent.isolation.subprocess.run", fake_run)


def test_network_none_passes_when_the_package_cache_tmpfs_is_mounted(monkeypatch):
    _inspect(monkeypatch, network='"none"\n', tmpfs='{"/opt/miniconda3/pkgs":""}\n')
    assert assert_network_none("cid") == "none"


def test_network_none_refuses_when_the_package_cache_tmpfs_is_missing(monkeypatch):
    _inspect(monkeypatch, network='"none"\n', tmpfs="null\n")
    with pytest.raises(IsolationError, match="Tmpfs"):
        assert_network_none("cid")
