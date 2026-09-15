"""Phase 2.1 gate: the Verified split loads as exactly 500 complete instances."""

from __future__ import annotations

import pytest

from reliability.benchmark.loader import (
    AGENT_VISIBLE_COLUMNS,
    EXPECTED_INSTANCES,
    AgentTask,
    DatasetIntegrityError,
    agent_task_from_row,
    load_agent_tasks,
    load_instance,
    load_verified,
)

ORACLE_COLUMNS = ("patch", "test_patch", "FAIL_TO_PASS", "PASS_TO_PASS", "eval_script")


@pytest.fixture(scope="module")
def dataset():
    return load_verified()


def test_dataset_has_exactly_500_instances(dataset):
    assert len(dataset) == 500
    assert EXPECTED_INSTANCES == 500


def test_required_fields_are_present(dataset):
    for column in (*AGENT_VISIBLE_COLUMNS, *ORACLE_COLUMNS):
        assert column in dataset.column_names, column


def test_instance_ids_are_unique(dataset):
    ids = dataset.select_columns(["instance_id"])["instance_id"]
    assert len(set(ids)) == 500


def test_every_instance_yields_a_task_with_populated_fields(dataset):
    tasks = load_agent_tasks(dataset)

    assert len(tasks) == 500
    assert all(isinstance(t, AgentTask) for t in tasks)
    for task in tasks:
        assert task.instance_id.strip()
        assert task.repo.strip()
        assert len(task.base_commit) == 40, task.instance_id
        assert task.problem_statement.strip(), task.instance_id


def test_spans_multiple_repositories(dataset):
    """Phase 2.3 stratifies by repo, which requires the population to vary."""
    repos = {t.repo for t in load_agent_tasks(dataset)}
    assert len(repos) >= 3
    assert "django/django" in repos


def test_load_instance_returns_matching_halves(dataset):
    task, oracle = load_instance("django__django-12304", dataset)

    assert task.instance_id == oracle.instance_id == "django__django-12304"
    assert task.repo == "django/django"
    assert oracle.patch.strip()
    assert oracle.fail_to_pass


def test_unknown_instance_raises(dataset):
    with pytest.raises(KeyError, match="no such instance"):
        load_instance("nope__nope-1", dataset)


def test_test_name_lists_are_normalised_to_tuples(dataset):
    _, oracle = load_instance("django__django-12304", dataset)

    assert isinstance(oracle.fail_to_pass, tuple)
    assert isinstance(oracle.pass_to_pass, tuple)
    assert all(isinstance(t, str) for t in oracle.fail_to_pass)


def test_unexpected_columns_do_not_reach_the_agent():
    """A new upstream column must not become agent-visible by default."""
    row = {
        "instance_id": "x__x-1",
        "repo": "x/x",
        "base_commit": "0" * 40,
        "problem_statement": "boom",
        "some_new_upstream_column": "SHOULD_NOT_APPEAR",
        "patch": "GOLD",
    }
    task = agent_task_from_row(row)

    assert "SHOULD_NOT_APPEAR" not in str(task)
    assert "GOLD" not in str(task)


def test_integrity_error_is_available_for_wrong_population():
    assert issubclass(DatasetIntegrityError, RuntimeError)
