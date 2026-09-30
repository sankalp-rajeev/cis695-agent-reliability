"""Load SWE-bench Verified, split into agent-visible and oracle-only halves.

This module is the single place where oracle data is read. Everything it hands
to the agent layer is an `AgentTask`; everything withheld is an `OracleRecord`.

The separation is structural rather than conventional. `AgentTask` is a frozen,
slotted dataclass built from four explicitly named fields, and it never receives
the source row - not as an argument, not as a private attribute. A slotted class
has no `__dict__`, so a later caller cannot attach the raw row to an instance
even by accident. The guarantee is the same one `RunProvenance.capture()` makes:
the safe value is read at the boundary, not supplied by a caller who might not
have checked.

Withheld columns and why:

- `patch`              the gold fix; the answer.
- `test_patch`         adds the tests the repair is graded by.
- `FAIL_TO_PASS`       names the tests that must flip; reveals the fix's shape.
- `PASS_TO_PASS`       the regression set. Phase 5.1 forbids the verifier from
                       consulting it, so it must not be casually reachable.
- `eval_script`        the harness's own evaluation commands.
- `hints_text`         free-text discussion from the originating pull request,
                       which frequently contains the fix or a direct description
                       of it. Not ground truth, but the most easily overlooked
                       leak here, so it is withheld with the oracle fields.

`environment_setup_commit`, `image`, and `log_parser` are execution metadata. The
harness needs them; the agent does not, so they stay on the oracle side too.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

DATASET_NAME = "SWE-bench/SWE-bench_Verified"
DATASET_SPLIT = "test"

#: SWE-bench Verified is a fixed, human-reviewed split. A different count means
#: the wrong dataset or revision was loaded, which would silently change the
#: population every downstream number is computed over.
EXPECTED_INSTANCES = 500

#: Columns an AgentTask may be built from. Anything absent here is oracle-side
#: by default, so a new upstream column cannot quietly become agent-visible.
AGENT_VISIBLE_COLUMNS = ("instance_id", "repo", "base_commit", "problem_statement")


class DatasetIntegrityError(RuntimeError):
    """Raised when the loaded dataset is not the expected 500-instance split."""


@dataclass(frozen=True, slots=True)
class AgentTask:
    """What the repair agent is allowed to see.

    Slotted so instances have no `__dict__`; there is nowhere to stash the source
    row, and `test_no_leakage.py` asserts that property directly.
    """

    instance_id: str
    repo: str
    base_commit: str
    problem_statement: str


@dataclass(frozen=True, slots=True)
class OracleRecord:
    """Ground truth and execution metadata. Never reaches the agent layer.

    Read by the oracle runner (Phase 8) and, for `patch` only, by the Phase 1
    harness controls. `PASS_TO_PASS` is additionally off-limits to the verifier's
    test selection under Phase 5.1.
    """

    instance_id: str
    patch: str
    test_patch: str
    fail_to_pass: tuple[str, ...]
    pass_to_pass: tuple[str, ...]
    eval_script: str
    hints_text: str
    environment_setup_commit: str
    image: str
    log_parser: str


@lru_cache(maxsize=1)
def load_verified():
    """Load the Verified split, asserting it is the expected population."""
    import warnings

    warnings.filterwarnings("ignore")
    from datasets import load_dataset

    dataset = load_dataset(DATASET_NAME, split=DATASET_SPLIT)

    if len(dataset) != EXPECTED_INSTANCES:
        raise DatasetIntegrityError(
            f"expected {EXPECTED_INSTANCES} instances in {DATASET_NAME}, "
            f"got {len(dataset)}"
        )
    missing = sorted(set(AGENT_VISIBLE_COLUMNS) - set(dataset.column_names))
    if missing:
        raise DatasetIntegrityError(f"dataset is missing required columns: {missing}")

    return dataset


@lru_cache(maxsize=4)
def _index_by_instance_id(fingerprint: str, _dataset_ref: Any) -> dict[str, int]:
    """Map instance id to row position.

    Built from a single-column projection. Iterating the full dataset
    materialises `problem_statement`, `patch`, and `test_patch` for every row,
    which made an earlier lookup take minutes per call.
    """
    ids = _dataset_ref.select_columns(["instance_id"])["instance_id"]
    return {instance_id: i for i, instance_id in enumerate(ids)}


def _as_tuple(value: Any) -> tuple[str, ...]:
    """Normalise a test-name list, which upstream has encoded both ways."""
    if isinstance(value, str):
        import json

        value = json.loads(value)
    return tuple(value)


def agent_task_from_row(row: dict[str, Any]) -> AgentTask:
    """Build an AgentTask by reading exactly the whitelisted fields.

    The row is consumed here and not retained. Constructing from explicit reads
    rather than `**row` is deliberate: an upstream schema change adds a column
    that this function ignores, instead of one that silently reaches the agent.
    """
    return AgentTask(
        instance_id=row["instance_id"],
        repo=row["repo"],
        base_commit=row["base_commit"],
        problem_statement=row["problem_statement"],
    )


def oracle_record_from_row(row: dict[str, Any]) -> OracleRecord:
    return OracleRecord(
        instance_id=row["instance_id"],
        patch=row["patch"],
        test_patch=row["test_patch"],
        fail_to_pass=_as_tuple(row["FAIL_TO_PASS"]),
        pass_to_pass=_as_tuple(row["PASS_TO_PASS"]),
        eval_script=row.get("eval_script", ""),
        hints_text=row.get("hints_text", ""),
        environment_setup_commit=row["environment_setup_commit"],
        image=row["image"],
        log_parser=row.get("log_parser", ""),
    )


def load_instance(instance_id: str, dataset=None) -> tuple[AgentTask, OracleRecord]:
    """Return the agent-visible and oracle-only halves of one instance.

    Both are returned so a caller must choose explicitly which half to use; there
    is no single object carrying everything that could be passed along by mistake.
    """
    dataset = load_verified() if dataset is None else dataset
    index = _index_by_instance_id(dataset._fingerprint, dataset)

    if instance_id not in index:
        raise KeyError(f"no such instance in {DATASET_NAME}: {instance_id}")

    row = dataset[index[instance_id]]
    return agent_task_from_row(row), oracle_record_from_row(row)


def load_agent_task(instance_id: str, dataset=None) -> AgentTask:
    """One instance's agent-visible half only; no OracleRecord is built."""
    dataset = load_verified() if dataset is None else dataset
    index = _index_by_instance_id(dataset._fingerprint, dataset)
    if instance_id not in index:
        raise KeyError(f"no such instance in {DATASET_NAME}: {instance_id}")
    projection = dataset.select_columns(list(AGENT_VISIBLE_COLUMNS))
    return agent_task_from_row(projection[index[instance_id]])


def load_agent_tasks(dataset=None) -> tuple[AgentTask, ...]:
    """Every instance as an AgentTask, with no oracle data loaded at all."""
    dataset = load_verified() if dataset is None else dataset
    projection = dataset.select_columns(list(AGENT_VISIBLE_COLUMNS))
    return tuple(agent_task_from_row(row) for row in projection)
