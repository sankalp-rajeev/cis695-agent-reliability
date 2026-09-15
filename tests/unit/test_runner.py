"""Phase 3.1 orchestration, gated with fixtures rather than a live API call.

The live mini-SWE-agent run is deferred until the model decision. Everything
around it - freeze, claim parsing, record writing, per-task isolation, and
count-agnostic iteration - is exercised here against a recorded backend.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from reliability.agent.claim_parser import ClaimStatus
from reliability.agent.records import RepairRecord, RunRole, Termination
from reliability.agent.runner import (
    AgentConfigurationError,
    AgentLimits,
    AgentOutcome,
    MiniSweAgentBackend,
    run_manifest,
    run_task,
)
from reliability.benchmark.loader import AgentTask
from reliability.benchmark.manifest import Manifest, ManifestEntry

PATCH = b"diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-a\n+b\n"

FIXTURE_TASKS = {
    "django__django-14373": AgentTask(
        instance_id="django__django-14373", repo="django/django",
        base_commit="b" * 40, problem_statement="issue text"),
    "psf__requests-1921": AgentTask(
        instance_id="psf__requests-1921", repo="psf/requests",
        base_commit="c" * 40, problem_statement="issue text"),
    "sphinx-doc__sphinx-10449": AgentTask(
        instance_id="sphinx-doc__sphinx-10449", repo="sphinx-doc/sphinx",
        base_commit="d" * 40, problem_statement="issue text"),
}


class RecordedBackend:
    """A backend replaying a fixed outcome. Stands in for a live model."""

    scaffold = "fixture-agent"
    version = "0.0.1"

    def __init__(self, model_id="fixture-model", outcome=None, per_instance=None):
        self.model_id = model_id
        self._outcome = outcome
        self._per_instance = per_instance or {}
        self.calls: list[str] = []

    def run(self, task, workdir: Path, limits: AgentLimits) -> AgentOutcome:
        self.calls.append(task.instance_id)
        if task.instance_id in self._per_instance:
            return self._per_instance[task.instance_id]
        return self._outcome or AgentOutcome(
            final_output="FINAL_STATUS: RESOLVED\nVALIDATION_EVIDENCE: suite green",
            patch=PATCH,
            termination=Termination.COMPLETED,
            commands_run=("pytest -q",),
            tests_run=("tests/test_x.py::test_y",),
            tokens_in=1000, tokens_out=200, api_cost_usd=0.02,
            trajectory=({"step": 1, "action": "ls"}, {"step": 2, "action": "edit"}),
        )


@pytest.fixture(autouse=True)
def stub_dataset(monkeypatch):
    """Avoid loading the real dataset; orchestration is what is under test."""
    monkeypatch.setattr(
        "reliability.agent.runner.load_instance",
        lambda instance_id, dataset=None: (FIXTURE_TASKS[instance_id], None),
    )


def make_manifest(tmp_path: Path, instance_ids) -> Manifest:
    path = tmp_path / "tasks.csv"
    lines = ["instance_id,repo,task_type,base_commit"]
    for i in instance_ids:
        lines.append(f"{i},{FIXTURE_TASKS[i].repo},numerical,{FIXTURE_TASKS[i].base_commit}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return Manifest(
        path=path,
        content_hash="sha256:" + "0" * 64,
        entries=tuple(
            ManifestEntry(i, FIXTURE_TASKS[i].repo, "numerical", FIXTURE_TASKS[i].base_commit)
            for i in instance_ids
        ),
    )


# --- single task -----------------------------------------------------------


def test_run_task_writes_every_artifact(tmp_path):
    manifest = make_manifest(tmp_path, ["django__django-14373"])
    record = run_task(
        manifest.entries[0], RecordedBackend(), tmp_path / "run",
        experiment_id="t", run_role=RunRole.SMOKE,
        manifest_hash=manifest.content_hash,
    )

    task_dir = tmp_path / "run" / "tasks" / "django__django-14373"
    assert (task_dir / "patch.diff").exists()
    assert (task_dir / "trajectory.jsonl").exists()
    assert (task_dir / "repair_record.json").exists()
    assert (task_dir / "agent_output.txt").exists()
    assert record.claim.status is ClaimStatus.RESOLVED


def test_patch_is_frozen_read_only(tmp_path):
    manifest = make_manifest(tmp_path, ["django__django-14373"])
    run_task(manifest.entries[0], RecordedBackend(), tmp_path / "run",
             experiment_id="t", run_role=RunRole.SMOKE,
             manifest_hash=manifest.content_hash)

    patch = tmp_path / "run" / "tasks" / "django__django-14373" / "patch.diff"
    with pytest.raises(PermissionError):
        patch.write_bytes(b"tampered")


def test_unparseable_claim_is_recorded_not_defaulted(tmp_path):
    manifest = make_manifest(tmp_path, ["django__django-14373"])
    backend = RecordedBackend(outcome=AgentOutcome(
        final_output="I think it's resolved.",
        patch=PATCH, termination=Termination.COMPLETED))

    record = run_task(manifest.entries[0], backend, tmp_path / "run",
                      experiment_id="t", run_role=RunRole.SMOKE,
                      manifest_hash=manifest.content_hash)

    assert record.claim.status is ClaimStatus.UNPARSEABLE
    assert record.claim.status is not ClaimStatus.UNRESOLVED
    assert record.claim.raw_output == "I think it's resolved."


def test_empty_patch_is_recorded(tmp_path):
    manifest = make_manifest(tmp_path, ["django__django-14373"])
    backend = RecordedBackend(outcome=AgentOutcome(
        final_output="FINAL_STATUS: UNRESOLVED\nVALIDATION_EVIDENCE: gave up",
        patch=b"", termination=Termination.STEP_LIMIT))

    record = run_task(manifest.entries[0], backend, tmp_path / "run",
                      experiment_id="t", run_role=RunRole.SMOKE,
                      manifest_hash=manifest.content_hash)

    assert record.patch.is_empty
    assert record.termination is Termination.STEP_LIMIT


def test_trajectory_is_jsonl_with_lf(tmp_path):
    manifest = make_manifest(tmp_path, ["django__django-14373"])
    run_task(manifest.entries[0], RecordedBackend(), tmp_path / "run",
             experiment_id="t", run_role=RunRole.SMOKE,
             manifest_hash=manifest.content_hash)

    raw = (tmp_path / "run" / "tasks" / "django__django-14373" / "trajectory.jsonl").read_bytes()
    assert b"\r\n" not in raw
    assert len(raw.strip().split(b"\n")) == 2


# --- count-agnostic --------------------------------------------------------


@pytest.mark.parametrize("n", [1, 2, 3])
def test_runs_whatever_size_manifest_it_is_given(tmp_path, n):
    """The same code must run a 10-task pilot and a 75-task study unchanged."""
    ids = list(FIXTURE_TASKS)[:n]
    manifest = make_manifest(tmp_path, ids)
    backend = RecordedBackend()

    records = run_manifest(manifest, backend, tmp_path / "run",
                           experiment_id="t", run_role=RunRole.SMOKE)

    assert len(records) == n
    assert backend.calls == ids


def test_run_manifest_copies_the_manifest_for_provenance(tmp_path):
    manifest = make_manifest(tmp_path, ["django__django-14373"])
    run_manifest(manifest, RecordedBackend(), tmp_path / "run",
                 experiment_id="t", run_role=RunRole.SMOKE)

    assert (tmp_path / "run" / "manifest.csv").read_bytes() == manifest.path.read_bytes()
    assert manifest.content_hash in (tmp_path / "run" / "manifest.sha256").read_text()


# --- parallel-safe ---------------------------------------------------------


def test_each_task_writes_only_inside_its_own_directory(tmp_path):
    ids = list(FIXTURE_TASKS)
    manifest = make_manifest(tmp_path, ids)
    run_root = tmp_path / "run"
    run_manifest(manifest, RecordedBackend(), run_root,
                 experiment_id="t", run_role=RunRole.SMOKE)

    for i in ids:
        assert (run_root / "tasks" / i / "repair_record.json").exists()
    # Only per-run provenance lives at the root; no shared mutable per-task file.
    assert sorted(p.name for p in run_root.iterdir()) == [
        "manifest.csv", "manifest.sha256", "tasks",
    ]


def test_concurrent_execution_produces_the_same_records(tmp_path):
    ids = list(FIXTURE_TASKS)
    serial = run_manifest(make_manifest(tmp_path, ids), RecordedBackend(),
                          tmp_path / "serial", experiment_id="t",
                          run_role=RunRole.SMOKE, max_workers=1)
    parallel = run_manifest(make_manifest(tmp_path, ids), RecordedBackend(),
                            tmp_path / "parallel", experiment_id="t",
                            run_role=RunRole.SMOKE, max_workers=3)

    assert [r.instance_id for r in serial] == [r.instance_id for r in parallel]
    assert [r.patch.sha256 for r in serial] == [r.patch.sha256 for r in parallel]


def test_interrupted_run_resumes_without_redoing_work(tmp_path):
    ids = list(FIXTURE_TASKS)
    manifest = make_manifest(tmp_path, ids)
    run_root = tmp_path / "run"

    run_task(manifest.entries[0], RecordedBackend(), run_root,
             experiment_id="t", run_role=RunRole.SMOKE,
             manifest_hash=manifest.content_hash)

    backend = RecordedBackend()
    run_manifest(manifest, backend, run_root, experiment_id="t", run_role=RunRole.SMOKE)

    assert ids[0] not in backend.calls
    assert len(backend.calls) == len(ids) - 1


# --- model decision deferral ----------------------------------------------


def test_backend_refuses_to_construct_without_a_model():
    """configs/model/primary.yaml holds model_id: null until the decision."""
    for missing in [None, ""]:
        with pytest.raises(AgentConfigurationError, match="no model_id configured"):
            MiniSweAgentBackend(model_id=missing)


def test_live_backend_is_wired_but_not_runnable_yet():
    backend = MiniSweAgentBackend(model_id="some-model")
    assert backend.scaffold == "mini-swe-agent"
    assert backend.version == "2.4.6"
    with pytest.raises(NotImplementedError, match="pending the model decision"):
        backend.run(FIXTURE_TASKS["django__django-14373"], Path("/tmp"), AgentLimits())


# --- record validity -------------------------------------------------------


def test_written_record_validates_against_the_schema(tmp_path):
    """Phase 3.3's 'one real record validates' - on a fixture, pending 3.1."""
    manifest = make_manifest(tmp_path, ["django__django-14373"])
    run_task(manifest.entries[0], RecordedBackend(), tmp_path / "run",
             experiment_id="t", run_role=RunRole.SMOKE,
             manifest_hash=manifest.content_hash)

    path = tmp_path / "run" / "tasks" / "django__django-14373" / "repair_record.json"
    record = RepairRecord.read(path)

    assert record.run_role is RunRole.SMOKE
    assert record.is_citable_as_result is False
    assert record.patch.sha256.startswith("sha256:")
    assert record.duration_s >= 0
