"""--resume, with fixtures. No containers are started."""

from __future__ import annotations

from pathlib import Path

import pytest

from reliability.provenance import require_resumable
from reliability.run_plan import pending_stages, resolve_max_workers, serial_ids


def test_resume_refuses_a_dirty_tree():
    with pytest.raises(SystemExit, match="dirty"):
        require_resumable(
            dirty=True, head="abc", recorded_head="abc",
            config_hash="sha256:aa", recorded_config_hash="sha256:aa",
        )


def test_resume_refuses_a_head_mismatch():
    with pytest.raises(SystemExit, match="HEAD"):
        require_resumable(
            dirty=False, head="abc", recorded_head="def",
            config_hash="sha256:aa", recorded_config_hash="sha256:aa",
        )


def test_resume_refuses_a_config_hash_mismatch():
    with pytest.raises(SystemExit, match="config hash"):
        require_resumable(
            dirty=False, head="abc", recorded_head="abc",
            config_hash="sha256:aa", recorded_config_hash="sha256:bb",
        )


def test_completed_stages_are_skipped(tmp_path: Path):
    task = tmp_path / "tasks" / "example__example-1"
    task.mkdir(parents=True)
    assert pending_stages(task) == ("agent", "verifier", "oracle")
    (task / "repair_record.json").write_text("{}", encoding="utf-8")
    assert pending_stages(task) == ("verifier", "oracle")
    (task / "verification_record.full.json").write_text("{}", encoding="utf-8")
    assert pending_stages(task) == ("oracle",)
    (task / "oracle_record.json").write_text("{}", encoding="utf-8")
    assert pending_stages(task) == ()


def test_serial_runner_keeps_file_order_and_halves_are_pinned():
    class Entry:
        def __init__(self, instance_id):
            self.instance_id = instance_id

    entries = [Entry("z"), Entry("a"), Entry("m")]
    assert serial_ids(entries) == ["z", "a", "m"]
    experiment = {"experiment_id": "main_50_a", "execution": {"max_workers": 1}}
    assert resolve_max_workers(None, experiment) == 1
    with pytest.raises(SystemExit, match="pinned to max_workers=1"):
        resolve_max_workers(3, experiment)
