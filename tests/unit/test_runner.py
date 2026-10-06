"""Phase 3.1 orchestration, gated with fixtures rather than a live API call.

The live mini-SWE-agent run is deferred until the model decision. Everything
around it - freeze, claim parsing, record writing, per-task isolation, and
count-agnostic iteration - is exercised here against a recorded backend.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from reliability.agent.claim_parser import ClaimStatus, UnparseableReason, parse_claim
from reliability.agent.records import RepairRecord, RunRole, Termination
from reliability.agent.records import summarise as summarise_records
from reliability.agent.runner import (
    CLAIM_DELIMITER,
    AgentConfigurationError,
    AgentLimits,
    AgentOutcome,
    MiniSweAgentBackend,
    _is_insufficient_balance,
    _split_submission,
    _step_limit_reached,
    _termination_for,
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


def test_live_backend_is_wired():
    backend = MiniSweAgentBackend(model_id="some-model")
    assert backend.scaffold == "mini-swe-agent"
    assert backend.version == "2.4.6"
    assert callable(backend.run)


# --- submission parsing ----------------------------------------------------


def test_claim_and_patch_are_split_on_the_delimiter():
    claim, patch = _split_submission(
        "FINAL_STATUS: RESOLVED\nVALIDATION_EVIDENCE: ran pytest\n"
        f"{CLAIM_DELIMITER}\n"
        "diff --git a/x.py b/x.py\n+new\n"
    )
    assert "FINAL_STATUS: RESOLVED" in claim
    assert patch.startswith(b"diff --git")
    assert CLAIM_DELIMITER.encode() not in patch


def test_patch_bytes_survive_the_split_exactly():
    body = "diff --git a/x b/x\n--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n"
    _, patch = _split_submission(f"FINAL_STATUS: UNRESOLVED\n{CLAIM_DELIMITER}\n{body}")
    assert patch == body.encode()


def test_missing_delimiter_falls_back_without_inventing_a_claim():
    """An agent that ignored the submission format must not parse as a claim."""
    claim, patch = _split_submission("diff --git a/x.py b/x.py\n+new\n")
    assert patch.startswith(b"diff --git")
    assert parse_claim(claim).status is ClaimStatus.UNPARSEABLE


def test_empty_submission_yields_an_empty_patch():
    claim, patch = _split_submission("")
    assert patch == b""
    assert parse_claim(claim).status is ClaimStatus.UNPARSEABLE


# --- termination mapping ---------------------------------------------------


@pytest.mark.parametrize(
    "exit_status,expected",
    [
        ("Submitted", Termination.COMPLETED),
        ("LimitsExceeded", Termination.STEP_LIMIT),
        ("TimeExceeded", Termination.TIMEOUT),
        ("RepeatedFormatError", Termination.ERROR),
        ("SomethingUnexpected", Termination.ERROR),
    ],
)
def test_exit_status_maps_to_termination(exit_status, expected):
    assert _termination_for(exit_status, rate_limited=False) is expected


def test_a_cost_stop_is_not_reported_as_a_step_stop():
    """mini-SWE-agent raises one LimitsExceeded for both budgets."""
    assert _termination_for(
        "LimitsExceeded", False, step_limit_reached=True) is Termination.STEP_LIMIT
    assert _termination_for(
        "LimitsExceeded", False, step_limit_reached=False) is Termination.COST_LIMIT
    # Undetermined stays the step limit, the check that runs first in the agent.
    assert _termination_for("LimitsExceeded", False) is Termination.STEP_LIMIT


@pytest.mark.parametrize("n_calls,expected", [(50, True), (49, False), (51, True)])
def test_step_limit_is_read_from_the_call_count(n_calls, expected):
    class Agent:
        pass

    agent = Agent()
    agent.n_calls = n_calls
    assert _step_limit_reached(agent, 50) is expected
    assert _step_limit_reached(Agent(), 50) is None


def test_a_budget_stop_is_never_finished_not_a_bad_status(tmp_path):
    """No submission means nothing to parse. The reason says so."""
    manifest = make_manifest(tmp_path, ["django__django-14373"])
    backend = RecordedBackend(outcome=AgentOutcome(
        final_output="", patch=b"", termination=Termination.STEP_LIMIT))

    record = run_task(manifest.entries[0], backend, tmp_path / "run",
                      experiment_id="t", run_role=RunRole.SMOKE,
                      manifest_hash=manifest.content_hash)

    assert record.claim.status is ClaimStatus.UNPARSEABLE
    assert record.claim.reason is UnparseableReason.NEVER_FINISHED
    assert record.termination is Termination.STEP_LIMIT


def test_a_finished_run_with_a_bad_status_keeps_its_parse_reason(tmp_path):
    manifest = make_manifest(tmp_path, ["django__django-14373"])
    backend = RecordedBackend(outcome=AgentOutcome(
        final_output="I think it's resolved.", patch=PATCH,
        termination=Termination.COMPLETED))

    record = run_task(manifest.entries[0], backend, tmp_path / "run",
                      experiment_id="t", run_role=RunRole.SMOKE,
                      manifest_hash=manifest.content_hash)

    assert record.claim.reason is UnparseableReason.MISSING


def test_summary_separates_never_finished_from_badly_stated(tmp_path):
    manifest = make_manifest(tmp_path, ["django__django-14373", "psf__requests-1921"])
    outcomes = [
        AgentOutcome(final_output="", patch=b"", termination=Termination.STEP_LIMIT),
        AgentOutcome(final_output="looks fine", patch=PATCH,
                     termination=Termination.COMPLETED),
    ]
    records = []
    for entry, outcome in zip(manifest.entries, outcomes, strict=True):
        records.append(run_task(entry, RecordedBackend(outcome=outcome), tmp_path / "run",
                                experiment_id="t", run_role=RunRole.SMOKE,
                                manifest_hash=manifest.content_hash))
    summary = summarise_records(records)

    assert summary["parseable_claims"] == 0
    assert summary["never_finished"] == 1
    assert summary["never_finished_by_termination"] == {"step_limit": 1}
    assert summary["unparseable_after_finishing"] == 1
    assert summary["terminations"] == {"completed": 1, "step_limit": 1}


def test_rate_limiting_is_not_reported_as_agent_failure():
    """A throttled run is a throughput result, not a finding about the model."""
    for exit_status in ["", "LimitsExceeded", "RepeatedFormatError"]:
        assert _termination_for(exit_status, rate_limited=True) is Termination.RATE_LIMITED


def test_insufficient_balance_is_its_own_termination_reason():
    """A drained account is a billing state, distinct from a repair failure
    and from RATE_LIMITED (not a throughput limit; waiting does not fix it)."""
    for exit_status in ["", "LimitsExceeded", "RepeatedFormatError"]:
        result = _termination_for(
            exit_status, rate_limited=False, insufficient_balance=True)
        assert result is Termination.INSUFFICIENT_BALANCE
        assert result is not Termination.RATE_LIMITED
        assert result is not Termination.ERROR


def test_insufficient_balance_dominates_rate_limited():
    """Both flags should never be set together in practice, but if they were,
    the more specific, non-retryable reason is reported, not the throttle."""
    assert _termination_for(
        "", rate_limited=True, insufficient_balance=True
    ) is Termination.INSUFFICIENT_BALANCE


@pytest.mark.parametrize(
    "status_code,message,expected",
    [
        (402, "payment required", True),
        (None, "Error code: 402 - {'error': {'message': 'Insufficient Balance'}}", True),
        (None, "DeepSeekException - insufficient_balance", True),
        (429, "rate limit exceeded", False),
        (400, "invalid_request_error: bad model name", False),
        (None, "connection reset by peer", False),
    ],
)
def test_is_insufficient_balance_detects_by_status_code_or_message(
    status_code, message, expected,
):
    class FakeAPIError(Exception):
        def __init__(self, msg, code):
            super().__init__(msg)
            self.status_code = code

    exc = FakeAPIError(message, status_code)
    assert _is_insufficient_balance(exc) is expected


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
