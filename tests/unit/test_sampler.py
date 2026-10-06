"""Phase 2.3 gate: the pilot manifest is stratified, diverse, and reproducible."""

from __future__ import annotations

import csv
import dataclasses

import pytest

from reliability.benchmark.loader import AgentTask, load_agent_tasks
from reliability.benchmark.sampler import (
    MANIFEST_COLUMNS,
    ORM_DB,
    TASK_TYPES,
    SamplingError,
    build_pilot_manifest,
    classify,
    content_hash,
    manifest_bytes,
    stratified_sample,
    write_manifest,
)

SEED = 695


@pytest.fixture(scope="module")
def tasks():
    return load_agent_tasks()


@pytest.fixture(scope="module")
def sample(tasks):
    return stratified_sample(tasks, n=10, seed=SEED)


# --- stratification --------------------------------------------------------


def test_sample_has_requested_size(sample):
    assert len(sample) == 10


def test_sample_spans_at_least_three_repositories(sample):
    assert len({r.repo for r in sample}) >= 3


def test_sample_covers_every_task_type(sample):
    assert {r.task_type for r in sample} == set(TASK_TYPES)


def test_sample_has_no_duplicate_instances(sample):
    ids = [r.instance_id for r in sample]
    assert len(set(ids)) == len(ids)


def test_rows_are_in_canonical_order(sample):
    assert [r.instance_id for r in sample] == sorted(r.instance_id for r in sample)


# --- exclusion --------------------------------------------------------------


def test_excluded_instances_never_appear(tasks, sample):
    """The pilot's own instances must be excludable from a later draw."""
    pilot_ids = frozenset(r.instance_id for r in sample)
    later = stratified_sample(tasks, n=10, seed=SEED + 1000, exclude=pilot_ids)
    assert not (pilot_ids & {r.instance_id for r in later})


def test_exclusion_shrinks_the_population_not_the_request(tasks, sample):
    """A request for n must still return n once exclusions are applied."""
    pilot_ids = frozenset(r.instance_id for r in sample)
    later = stratified_sample(tasks, n=10, seed=SEED + 1000, exclude=pilot_ids)
    assert len(later) == 10


def test_excluding_everything_fails_loudly(tasks):
    all_ids = frozenset(t.instance_id for t in tasks)
    with pytest.raises(SamplingError, match="no instances available"):
        stratified_sample(tasks, n=1, seed=SEED, exclude=all_ids)


def test_no_exclusion_is_the_default(tasks):
    """Omitting `exclude` must reproduce the pre-existing, cited manifest."""
    assert content_hash(manifest_bytes(stratified_sample(tasks, n=10, seed=SEED))) == (
        content_hash(manifest_bytes(
            stratified_sample(tasks, n=10, seed=SEED, exclude=frozenset()))))


# --- determinism -----------------------------------------------------------


def test_same_seed_reproduces_identical_manifest(tasks):
    first = stratified_sample(tasks, n=10, seed=SEED)
    second = stratified_sample(tasks, n=10, seed=SEED)
    assert content_hash(manifest_bytes(first)) == content_hash(manifest_bytes(second))


def test_same_seed_is_stable_across_input_order(tasks):
    """Determinism must not depend on the order the population arrives in."""
    shuffled = tuple(reversed(tasks))
    assert content_hash(manifest_bytes(stratified_sample(tasks, n=10, seed=SEED))) == (
        content_hash(manifest_bytes(stratified_sample(shuffled, n=10, seed=SEED)))
    )


def test_different_seed_gives_a_different_sample(tasks):
    a = stratified_sample(tasks, n=10, seed=SEED)
    b = stratified_sample(tasks, n=10, seed=SEED + 1)
    assert {r.instance_id for r in a} != {r.instance_id for r in b}


def test_rerunning_the_builder_reproduces_the_hash(tmp_path, tasks):
    path = tmp_path / "pilot.csv"
    _, first = build_pilot_manifest(path, n=10, seed=SEED)
    first_bytes = path.read_bytes()
    _, second = build_pilot_manifest(path, n=10, seed=SEED)

    assert first == second
    assert path.read_bytes() == first_bytes


def test_sidecar_hash_matches_file_contents(tmp_path, tasks):
    path = tmp_path / "pilot.csv"
    _, digest = build_pilot_manifest(path, n=10, seed=SEED)

    sidecar = path.with_suffix(".csv.sha256").read_text().split()[0]
    assert sidecar == digest == content_hash(path.read_bytes())


# --- serialisation ---------------------------------------------------------


def test_manifest_is_lf_terminated_and_has_expected_columns(sample):
    payload = manifest_bytes(sample)

    assert b"\r\n" not in payload
    assert payload.splitlines()[0].decode() == ",".join(MANIFEST_COLUMNS)
    assert len(payload.splitlines()) == 11


def test_manifest_round_trips_through_csv(tmp_path, sample):
    path = tmp_path / "pilot.csv"
    write_manifest(path, sample)

    with path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 10
    assert rows[0]["instance_id"] == sample[0].instance_id


# --- classification --------------------------------------------------------


def test_classify_uses_only_agent_visible_fields():
    """The classifier must work on an AgentTask, which carries no oracle data."""
    task = AgentTask(
        instance_id="django__django-1",
        repo="django/django",
        base_commit="0" * 40,
        problem_statement="QuerySet.annotate() raises on a ForeignKey lookup.",
    )
    assert classify(task) == ORM_DB


def test_unmapped_repository_is_an_error_not_a_silent_default():
    task = AgentTask(
        instance_id="who__what-1",
        repo="unknown/repo",
        base_commit="0" * 40,
        problem_statement="something",
    )
    with pytest.raises(SamplingError, match="no task type mapped"):
        classify(task)


def test_every_instance_in_the_population_classifies(tasks):
    assert all(classify(t) in TASK_TYPES for t in tasks)


def test_oversized_request_fails_loudly(tasks):
    with pytest.raises(SamplingError, match="exhausted the population"):
        stratified_sample(tasks, n=len(tasks) + 1, seed=SEED)


def test_manifest_row_is_immutable(sample):
    with pytest.raises(dataclasses.FrozenInstanceError):
        sample[0].repo = "x"  # type: ignore[misc]
