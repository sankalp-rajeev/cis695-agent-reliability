"""Split a stratified manifest into two halves, deterministically.

The main study is launched as two halves of 50 so a first-half checkpoint can
stop the second half. The split is a function of the manifest bytes and a
seed, not of draw order or of which machine runs it: within each task type the
rows are sorted by instance id, then shuffled with one `random.Random` walked
in task-type order. Each half receives the same number of tasks of each type.
"""

from __future__ import annotations

import random
from collections import defaultdict

from reliability.benchmark.sampler import TASK_TYPES, ManifestRow

#: Distinct from the manifest draw seed (20261005) and from the pilot seed (695).
SPLIT_SEED = 20261007
PER_TYPE = 10
#: These repositories were not in the pilot. Their rows in half A are written
#: first so a serial run hits them before the rest of the file.
FRONT_REPOS = ("pytest-dev/pytest", "pydata/xarray", "pallets/flask")


class SplitError(ValueError):
    """The manifest cannot be split into equal per-type halves."""


def split_halves(
    rows: list[ManifestRow],
    *,
    seed: int = SPLIT_SEED,
    per_type: int = PER_TYPE,
) -> tuple[list[ManifestRow], list[ManifestRow]]:
    """Return `(half_a, half_b)`.

    Membership is the seeded per-type shuffle. `half_b` is sorted by instance
    id. `half_a` is not: `order_half_a` writes it in a second seeded shuffle,
    with pytest, xarray and flask rows from this half first.
    """
    if per_type < 1:
        raise SplitError("per_type must be >= 1")

    by_type: dict[str, list[ManifestRow]] = defaultdict(list)
    for row in rows:
        by_type[row.task_type].append(row)

    missing = [task_type for task_type in TASK_TYPES if task_type not in by_type]
    if missing:
        raise SplitError(f"manifest is missing task types: {missing}")
    extra = sorted(set(by_type) - set(TASK_TYPES))
    if extra:
        raise SplitError(f"manifest has unknown task types: {extra}")

    rng = random.Random(seed)
    half_a: list[ManifestRow] = []
    half_b: list[ManifestRow] = []
    for task_type in TASK_TYPES:
        group = sorted(by_type[task_type], key=lambda row: row.instance_id)
        if len(group) != per_type * 2:
            raise SplitError(
                f"{task_type} has {len(group)} tasks, need {per_type * 2} "
                f"to put {per_type} in each half"
            )
        rng.shuffle(group)
        half_a.extend(group[:per_type])
        half_b.extend(group[per_type:])

    return (
        order_half_a(half_a, seed=seed),
        sorted(half_b, key=lambda row: row.instance_id),
    )


def order_half_a(
    rows: list[ManifestRow], *, seed: int = SPLIT_SEED,
) -> list[ManifestRow]:
    """Seeded shuffle of half A, front repos first.

    Both groups are sorted before the shuffle, so the file order depends on
    the seed and the membership, not on the order `rows` arrived in.
    """
    rng = random.Random(seed)
    front = sorted(
        (row for row in rows if row.repo in FRONT_REPOS),
        key=lambda row: row.instance_id,
    )
    rest = sorted(
        (row for row in rows if row.repo not in FRONT_REPOS),
        key=lambda row: row.instance_id,
    )
    rng.shuffle(front)
    rng.shuffle(rest)
    return front + rest
