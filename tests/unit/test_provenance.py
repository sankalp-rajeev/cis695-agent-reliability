"""Phase 0.3 gate: every run directory carries a complete reproducibility block."""

from __future__ import annotations

import sys

import pytest
import yaml

from reliability.provenance import (
    REQUIRED_FIELDS,
    ProvenanceError,
    RunProvenance,
    read_meta,
    require_clean_tree,
    validate,
    write_meta,
)


def make_provenance(**overrides) -> RunProvenance:
    base = {
        "task_manifest_hash": "sha256:0d1f" + "a" * 60,
        "git_commit": "9a95e38c4b1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f",
        "git_dirty": False,
        "agent_scaffold": "mini-swe-agent",
        "agent_version": "2.4.6",
        "model_id": "example-model-2026-01-01",
        "temperature": 0.0,
        "max_steps": 50,
        "max_input_tokens_per_task": 400000,
        "max_output_tokens": 8192,
        "per_task_timeout_s": 1800,
        "verifier_policy_version": "v1.0.0-full",
        "docker_image": "swebench/sweb.eval.x86_64.django_1776_django-12304:latest",
        "swebench_version": "5.0.2",
        "timestamp_utc": "2026-09-15T00:00:00+00:00",
        "python_version": "3.11.9",
        "python_executable": "/home/x/proj/.venv/bin/python",
        "pythonpath": [],
        "sys_path": ["/home/x/proj/src"],
        "foreign_sys_path_entries": [],
        "agent_network_mode": "none",
        "reproduction_generator_model_id": "deepseek/deepseek-v4-flash",
        "reproduction_generator_served_model": "deepseek-flash",
        "reproduction_generator_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "reproduction_generator_verified_on": "2026-09-30",
        "reproduction_generator_prompt_sha256": "sha256:" + "c" * 64,
        "reproduction_max_tests": 3,
        "reproduction_retries": 0,
        "reproduction_generator_max_steps": 40,
        "reproduction_generator_max_cost_usd": 1.0,
        "reproduction_runner_sha256": "sha256:" + "d" * 64,
    }
    base.update(overrides)
    return RunProvenance(**base)


def test_all_required_fields_present_and_non_null(tmp_path):
    path = write_meta(tmp_path, make_provenance())
    block = yaml.safe_load(path.read_text())

    assert set(block) == set(REQUIRED_FIELDS)
    for field in REQUIRED_FIELDS:
        assert block[field] is not None, field


def test_round_trips_through_disk(tmp_path):
    write_meta(tmp_path, make_provenance())
    assert read_meta(tmp_path)["swebench_version"] == "5.0.2"


@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_null_in_any_required_field_is_rejected(field):
    block = make_provenance().to_dict()
    block[field] = None
    with pytest.raises(ProvenanceError, match="null provenance fields"):
        validate(block)


@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_missing_any_required_field_is_rejected(field):
    block = make_provenance().to_dict()
    del block[field]
    with pytest.raises(ProvenanceError, match="missing required provenance fields"):
        validate(block)


def test_falsey_but_legitimate_values_are_accepted():
    """A clean tree and a zero temperature are real values, not absences."""
    validate(make_provenance(git_dirty=False, temperature=0.0).to_dict())


def test_blank_string_is_rejected():
    block = make_provenance().to_dict()
    block["model_id"] = "   "
    with pytest.raises(ProvenanceError, match="blank provenance fields"):
        validate(block)


def test_dirty_tree_is_recorded_in_meta(tmp_path):
    """A dry run allowed to start dirty must still say so."""
    path = write_meta(tmp_path, make_provenance(git_dirty=True))
    assert yaml.safe_load(path.read_text())["git_dirty"] is True


def test_an_experiment_refuses_a_dirty_tree():
    with pytest.raises(SystemExit, match="dirty"):
        require_clean_tree(True, experiment_id="pilot_13", allow_dirty=False)


def test_the_dirty_override_is_refused_outside_dry_runs():
    with pytest.raises(SystemExit, match="dry runs"):
        require_clean_tree(True, experiment_id="pilot_13", allow_dirty=True)


def test_a_dry_run_may_start_dirty_with_the_override():
    require_clean_tree(True, experiment_id="dry_9_2", allow_dirty=True)
    with pytest.raises(SystemExit):
        require_clean_tree(True, experiment_id="dry_9_2", allow_dirty=False)


def test_a_clean_tree_needs_no_override():
    require_clean_tree(False, experiment_id="pilot_13", allow_dirty=False)


def test_refuses_to_silently_overwrite(tmp_path):
    write_meta(tmp_path, make_provenance())
    with pytest.raises(ProvenanceError, match="refusing to overwrite"):
        write_meta(tmp_path, make_provenance())
    write_meta(tmp_path, make_provenance(git_dirty=True), overwrite=True)
    assert read_meta(tmp_path)["git_dirty"] is True


def test_empty_interpreter_lists_are_the_clean_state_not_an_absence():
    """A cleared PYTHONPATH is an empty list, which must validate."""
    block = make_provenance(pythonpath=[], foreign_sys_path_entries=[]).to_dict()
    validate(block)
    assert make_provenance().interpreter_is_clean is True


def test_contamination_is_recorded_not_rejected(tmp_path):
    """A contaminated run must still be written, or the evidence is lost."""
    ros = "/opt/ros/jazzy/lib/python3.12/site-packages"
    prov = make_provenance(pythonpath=[ros], foreign_sys_path_entries=[ros])
    path = write_meta(tmp_path, prov)

    assert prov.interpreter_is_clean is False
    assert yaml.safe_load(path.read_text())["foreign_sys_path_entries"] == [ros]


def test_capture_fills_interpreter_fields_from_this_process():
    fields = {
        k: make_provenance().to_dict()[k]
        for k in REQUIRED_FIELDS
        if k not in {
            "python_version", "python_executable", "pythonpath",
            "sys_path", "foreign_sys_path_entries",
        }
    }
    prov = RunProvenance.capture(**fields)

    validate(prov.to_dict())
    assert prov.python_version == ".".join(map(str, sys.version_info[:3]))
    assert prov.python_executable == sys.executable


def test_unexpected_field_is_rejected():
    """An unrecognised key usually means a renamed field silently lost its value."""
    block = make_provenance().to_dict()
    block["temprature"] = 0.7
    with pytest.raises(ProvenanceError, match="unexpected provenance fields"):
        validate(block)
