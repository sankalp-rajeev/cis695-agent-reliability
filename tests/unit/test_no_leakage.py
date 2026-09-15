"""Phase 2.2 gate: oracle fields are structurally unreachable from an AgentTask.

This is the test the experiment's validity rests on. If an agent can see the gold
patch, the test patch, or the names of the tests it will be judged by, every
downstream number is meaningless.

The checklist states the gate as "serialize an AgentTask to JSON and assert the
strings patch, test_patch, FAIL_TO_PASS, PASS_TO_PASS do not appear anywhere in
the payload". That is necessary but not sufficient, and one part of it is a
false-positive trap:

- Insufficient, because absence in one synthetic object does not prove the type
  cannot carry oracle data. The stronger property is structural: an AgentTask
  holds no reference to the raw dataset row, not even a private one, so there is
  nothing to leak regardless of how it is serialised.
- A trap, because a real issue text may legitimately contain the word "patch"
  ("the attached patch fixes..."). Asserting on bare field names against real
  data would fail on honest input. Field-name assertions therefore run against a
  controlled synthetic task, while real instances are checked against the actual
  oracle *values*, which is the thing that would do harm.
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from reliability.benchmark.loader import AgentTask, OracleRecord, load_instance, load_verified

ORACLE_FIELD_NAMES = ("patch", "test_patch", "FAIL_TO_PASS", "PASS_TO_PASS")

# Chosen in Phase 1.2 for repo diversity; already exercised by the harness.
SANITY_INSTANCE = "django__django-12304"


@pytest.fixture(scope="module")
def dataset():
    return load_verified()


def make_agent_task() -> AgentTask:
    """A task whose every field is controlled, so field-name assertions are sound."""
    return AgentTask(
        instance_id="example__example-1",
        repo="example/example",
        base_commit="0" * 40,
        problem_statement="Calling foo() with a negative argument returns None.",
    )


# --- structural guarantees -------------------------------------------------


def test_agent_task_is_frozen():
    task = make_agent_task()
    with pytest.raises(dataclasses.FrozenInstanceError):
        task.problem_statement = "mutated"  # type: ignore[misc]


def test_agent_task_declares_no_oracle_fields():
    fields = {f.name for f in dataclasses.fields(AgentTask)}
    assert fields == {"instance_id", "repo", "base_commit", "problem_statement"}


def test_agent_task_holds_no_reference_to_the_raw_row():
    """Leakage must be impossible, not merely absent.

    A private attribute holding the source row would keep the oracle reachable
    via the object graph even though every declared field looks clean.
    """
    task = make_agent_task()
    assert not hasattr(task, "__dict__") or set(vars(task)) == {
        "instance_id", "repo", "base_commit", "problem_statement",
    }
    for name in dir(task):
        if name.startswith("__"):
            continue
        value = getattr(task, name)
        assert not isinstance(value, dict), f"{name} holds a mapping that could be the raw row"


# --- serialisation ---------------------------------------------------------


def test_synthetic_task_json_contains_no_oracle_field_names():
    payload = json.dumps(dataclasses.asdict(make_agent_task()))
    for name in ORACLE_FIELD_NAMES:
        assert name not in payload, f"oracle field name {name!r} leaked into payload"


def test_real_task_json_contains_no_oracle_values(dataset):
    """The values are what would actually do harm if an agent saw them."""
    task, oracle = load_instance(SANITY_INSTANCE, dataset)
    payload = json.dumps(dataclasses.asdict(task))

    assert oracle.patch.strip()
    assert oracle.patch not in payload
    assert oracle.test_patch not in payload
    for test_name in oracle.fail_to_pass:
        assert test_name not in payload, f"FAIL_TO_PASS entry {test_name!r} leaked"
    for test_name in oracle.pass_to_pass:
        assert test_name not in payload, f"PASS_TO_PASS entry {test_name!r} leaked"


def test_agent_task_and_oracle_record_are_separate_objects(dataset):
    task, oracle = load_instance(SANITY_INSTANCE, dataset)
    assert isinstance(task, AgentTask)
    assert isinstance(oracle, OracleRecord)
    assert task.instance_id == oracle.instance_id
    # The only shared value is the identifier that joins them.
    assert not set(dataclasses.asdict(task).values()) & {oracle.patch, oracle.test_patch}


def test_whole_dataset_is_free_of_oracle_values(dataset):
    """Spot-checking one instance is weak; sample across repositories."""
    sampled = [dataset[i]["instance_id"] for i in range(0, len(dataset), 97)]
    assert len(sampled) >= 5

    for instance_id in sampled:
        task, oracle = load_instance(instance_id, dataset)
        payload = json.dumps(dataclasses.asdict(task))
        assert oracle.patch not in payload, instance_id
        assert oracle.test_patch not in payload, instance_id
