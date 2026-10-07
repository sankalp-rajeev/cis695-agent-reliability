"""The two halves of main_100, checked against the files on disk."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import yaml

from reliability.benchmark.manifest import load_manifest
from reliability.benchmark.sampler import ManifestRow
from reliability.benchmark.split import FRONT_REPOS, split_halves
from reliability.run_plan import serial_ids

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "manifests" / "main_100.csv"
PILOT = ROOT / "manifests" / "pilot.csv"
HALF_A = ROOT / "manifests" / "main_50_a.csv"
HALF_B = ROOT / "manifests" / "main_50_b.csv"


def _rows(path: Path) -> list[ManifestRow]:
    with path.open(newline="") as fh:
        return [
            ManifestRow(
                instance_id=row["instance_id"], repo=row["repo"],
                task_type=row["task_type"], base_commit=row["base_commit"],
            )
            for row in csv.DictReader(fh)
        ]


def test_halves_match_the_seeded_split_and_the_rules():
    source = _rows(SOURCE)
    pilot = {row["instance_id"] for row in csv.DictReader(PILOT.open(newline=""))}
    expected_a, expected_b = split_halves(source)
    manifest_a = load_manifest(HALF_A)
    manifest_b = load_manifest(HALF_B)
    ids_a = [row.instance_id for row in expected_a]
    ids_b = [row.instance_id for row in expected_b]

    assert list(manifest_a.instance_ids) == ids_a
    assert list(manifest_b.instance_ids) == ids_b
    assert set(ids_a).isdisjoint(ids_b)
    assert set(ids_a) | set(ids_b) == {row.instance_id for row in source}
    assert not (set(ids_a) | set(ids_b)) & pilot
    for manifest in (manifest_a, manifest_b):
        counts = Counter(
            row.task_type for row in _rows(manifest.path)
        )
        assert counts == {task_type: 10 for task_type in counts}
        assert len(counts) == 5
    front = [
        row.repo for row in expected_a
        if row.repo in FRONT_REPOS
    ]
    assert front
    assert all(row.repo in FRONT_REPOS for row in expected_a[:len(front)])
    assert serial_ids(manifest_a) == ids_a
    assert serial_ids(manifest_a) != sorted(ids_a)


def test_half_configs_pin_one_worker():
    for name in ("main_50_a.yaml", "main_50_b.yaml"):
        experiment = yaml.safe_load(
            (ROOT / "configs" / "experiments" / name).read_text())
        assert experiment["execution"]["max_workers"] == 1
