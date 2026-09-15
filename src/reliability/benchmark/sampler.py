"""Deterministic stratified sampling of the pilot task manifest.

Phase 2.3. Draws a fixed-size sample spanning both repositories and task types,
reproducibly from a seed.

Two constraints shape the design.

**Selection uses only agent-visible fields.** Task type is derived from `repo`
and `problem_statement` - never from the gold patch's touched paths, which would
be the obvious classifier but would make the sample a function of oracle data.
Nothing here imports `OracleRecord`, and nothing consults any record of model
performance on an instance. The sample must be defensible as chosen before
anyone knew which instances were easy.

**Determinism is total.** Every collection is sorted before use and the only
randomness comes from a seeded `random.Random`. Set and dict iteration order
never reaches an ordering decision, so the same seed reproduces the same
manifest byte-for-byte on any machine.

Task types follow the five categories named in the technical design. Repository
gives the base category, since a repository's domain is stable; django is the one
repository spanning two categories, and is split on problem-statement keywords
because its ORM and its request/response framework are genuinely different
domains and django alone is 46 % of the split.
"""

from __future__ import annotations

import csv
import hashlib
import random
import re
from dataclasses import dataclass
from pathlib import Path

from reliability.benchmark.loader import AgentTask, load_agent_tasks

FRAMEWORK_API = "framework/API"
ORM_DB = "ORM/DB"
NUMERICAL = "numerical"
STATE_BEHAVIOR = "state/behavior"
SYSTEM_RUNTIME = "system/runtime"

TASK_TYPES = (FRAMEWORK_API, ORM_DB, NUMERICAL, STATE_BEHAVIOR, SYSTEM_RUNTIME)

#: Base category per repository. django is resolved separately.
REPO_TASK_TYPE = {
    "astropy/astropy": NUMERICAL,
    "matplotlib/matplotlib": STATE_BEHAVIOR,
    "mwaskom/seaborn": STATE_BEHAVIOR,
    "pallets/flask": FRAMEWORK_API,
    "psf/requests": FRAMEWORK_API,
    "pydata/xarray": NUMERICAL,
    "pylint-dev/pylint": SYSTEM_RUNTIME,
    "pytest-dev/pytest": SYSTEM_RUNTIME,
    "scikit-learn/scikit-learn": NUMERICAL,
    "sphinx-doc/sphinx": SYSTEM_RUNTIME,
    "sympy/sympy": NUMERICAL,
}

#: Terms that mark a django issue as belonging to the ORM/database layer rather
#: than the request/response framework. Matched against the problem statement,
#: which the agent also sees, so this introduces no information the agent lacks.
ORM_TERMS = (
    "queryset", "orm", "migration", "foreign key", "foreignkey", "manytomany",
    "select_related", "prefetch_related", "annotate", "aggregate", "db_index",
    "database", "sql", "model field", "modelfield", "primary key", "related_name",
    "on_delete", "objects.filter", "objects.get", "db backend", "transaction",
)

_ORM_PATTERN = re.compile("|".join(re.escape(t) for t in ORM_TERMS), re.IGNORECASE)


class SamplingError(RuntimeError):
    """Raised when a requested sample cannot satisfy its stratification."""


@dataclass(frozen=True, slots=True)
class ManifestRow:
    instance_id: str
    repo: str
    task_type: str
    base_commit: str


def classify(task: AgentTask) -> str:
    """Assign a task type from agent-visible fields only."""
    if task.repo == "django/django":
        return ORM_DB if _ORM_PATTERN.search(task.problem_statement) else FRAMEWORK_API
    try:
        return REPO_TASK_TYPE[task.repo]
    except KeyError:
        raise SamplingError(f"no task type mapped for repository {task.repo!r}") from None


def stratified_sample(
    tasks: tuple[AgentTask, ...],
    *,
    n: int = 10,
    seed: int = 695,
    min_distinct_repos: int = 3,
) -> list[ManifestRow]:
    """Draw `n` tasks spread across task types, then across repositories.

    Task types are filled round-robin so no category is crowded out by django's
    share of the population. Within a type, repositories are visited round-robin
    before any repository is used twice, which is what pushes repository
    diversity above the required minimum rather than merely meeting it.
    """
    rng = random.Random(seed)

    by_type: dict[str, dict[str, list[str]]] = {t: {} for t in TASK_TYPES}
    for task in sorted(tasks, key=lambda t: t.instance_id):
        by_type[classify(task)].setdefault(task.repo, []).append(task.instance_id)

    available = [t for t in TASK_TYPES if by_type[t]]
    if not available:
        raise SamplingError("no instances available to sample")

    # Per type, a deterministic round-robin queue over its repositories.
    repo_order: dict[str, list[str]] = {}
    for task_type in available:
        repos = sorted(by_type[task_type])
        rng.shuffle(repos)
        repo_order[task_type] = repos

    chosen: list[str] = []
    seen_repos: set[str] = set()
    cursor = {t: 0 for t in available}

    while len(chosen) < n:
        progressed = False
        for task_type in available:
            if len(chosen) >= n:
                break
            repos = repo_order[task_type]
            # Prefer a repository not yet represented anywhere in the sample.
            candidates = sorted(r for r in repos if by_type[task_type][r])
            if not candidates:
                continue
            fresh = [r for r in candidates if r not in seen_repos]
            pool = fresh or candidates
            repo = pool[cursor[task_type] % len(pool)]
            cursor[task_type] += 1

            instances = by_type[task_type][repo]
            instance_id = instances.pop(rng.randrange(len(instances)))
            chosen.append(instance_id)
            seen_repos.add(repo)
            progressed = True

        if not progressed:
            raise SamplingError(
                f"exhausted the population at {len(chosen)} of {n} requested instances"
            )

    if len(seen_repos) < min_distinct_repos:
        raise SamplingError(
            f"sample spans {len(seen_repos)} repositories, need >= {min_distinct_repos}"
        )

    index = {t.instance_id: t for t in tasks}
    rows = [
        ManifestRow(
            instance_id=i,
            repo=index[i].repo,
            task_type=classify(index[i]),
            base_commit=index[i].base_commit,
        )
        for i in chosen
    ]
    # Canonical order, so the manifest and its hash do not depend on draw order.
    return sorted(rows, key=lambda r: r.instance_id)


MANIFEST_COLUMNS = ("instance_id", "repo", "task_type", "base_commit")


def manifest_bytes(rows: list[ManifestRow]) -> bytes:
    """Serialise to canonical CSV bytes - LF endings, fixed column order."""
    from io import StringIO

    buf = StringIO(newline="")
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(MANIFEST_COLUMNS)
    for row in rows:
        writer.writerow([row.instance_id, row.repo, row.task_type, row.base_commit])
    return buf.getvalue().encode("utf-8")


def content_hash(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def write_manifest(path: Path, rows: list[ManifestRow]) -> str:
    """Write the manifest and its sidecar hash; return the hash."""
    payload = manifest_bytes(rows)
    digest = content_hash(payload)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    path.with_suffix(path.suffix + ".sha256").write_text(
        f"{digest}  {path.name}\n", encoding="utf-8"
    )
    return digest


def build_pilot_manifest(
    path: Path, *, n: int = 10, seed: int = 695, dataset=None
) -> tuple[list[ManifestRow], str]:
    tasks = load_agent_tasks(dataset)
    rows = stratified_sample(tasks, n=n, seed=seed)
    return rows, write_manifest(path, rows)
