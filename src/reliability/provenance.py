"""Run provenance: the reproducibility block written once per run directory.

Every run emits exactly one `meta.yaml`. Its purpose is to make a result
re-derivable months later, so each field is required and must be non-null: a
missing model id or an unrecorded verifier policy version makes a run
uninterpretable rather than merely under-documented. Validation therefore
rejects `None` and empty strings instead of filling defaults.

`git_dirty` is recorded rather than enforced. Refusing to run on a dirty tree
would be hostile during development, but a result produced from uncommitted code
is not reproducible from `git_commit` alone and must be visible as such.
"""

from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from reliability.env import interpreter_environment

REQUIRED_FIELDS = (
    "task_manifest_hash",
    "git_commit",
    "git_dirty",
    "agent_scaffold",
    "agent_version",
    "model_id",
    "temperature",
    "max_steps",
    "max_input_tokens_per_task",
    "max_output_tokens",
    "per_task_timeout_s",
    "verifier_policy_version",
    "docker_image",
    "swebench_version",
    "timestamp_utc",
    # Interpreter import state. Recorded because a contaminated sys.path can
    # shadow a pinned dependency inside an agent or verifier run, and nothing
    # else in the record would reveal it afterwards. See reliability.env.
    "python_version",
    "python_executable",
    "pythonpath",
    "sys_path",
    "foreign_sys_path_entries",
)


class ProvenanceError(ValueError):
    """Raised when a reproducibility block is incomplete."""


@dataclass(frozen=True)
class RunProvenance:
    """The reproducibility block for a single run."""

    task_manifest_hash: str
    git_commit: str
    git_dirty: bool
    agent_scaffold: str
    agent_version: str
    model_id: str
    temperature: float
    max_steps: int
    max_input_tokens_per_task: int
    max_output_tokens: int
    per_task_timeout_s: int
    verifier_policy_version: str
    docker_image: str
    swebench_version: str
    timestamp_utc: str
    python_version: str
    python_executable: str
    pythonpath: list[str]
    sys_path: list[str]
    foreign_sys_path_entries: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def interpreter_is_clean(self) -> bool:
        return not self.foreign_sys_path_entries

    @classmethod
    def capture(cls, **fields: Any) -> RunProvenance:
        """Build a block, filling the interpreter fields from this process.

        Callers supply the experiment-specific values; the import state is read
        here rather than passed in, so it cannot be reported as clean by a caller
        that never looked.
        """
        return cls(**fields, **interpreter_environment())


def git_commit(repo_root: Path | None = None) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root, capture_output=True, text=True, check=True,
    ).stdout.strip()


def git_dirty(repo_root: Path | None = None) -> bool:
    out = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root, capture_output=True, text=True, check=True,
    ).stdout
    return bool(out.strip())


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def validate(block: dict[str, Any]) -> None:
    """Raise unless every required field is present and non-null.

    `False` and `0` are legitimate values (a clean tree, a zero temperature), so
    emptiness is checked per type rather than by truthiness.
    """
    missing = [k for k in REQUIRED_FIELDS if k not in block]
    if missing:
        raise ProvenanceError(f"missing required provenance fields: {sorted(missing)}")

    null = [k for k in REQUIRED_FIELDS if block[k] is None]
    if null:
        raise ProvenanceError(f"null provenance fields: {sorted(null)}")

    blank = [
        k for k in REQUIRED_FIELDS
        if isinstance(block[k], str) and not block[k].strip()
    ]
    if blank:
        raise ProvenanceError(f"blank provenance fields: {sorted(blank)}")

    extra = sorted(set(block) - set(REQUIRED_FIELDS))
    if extra:
        raise ProvenanceError(f"unexpected provenance fields: {extra}")


def write_meta(run_dir: Path, provenance: RunProvenance, *, overwrite: bool = False) -> Path:
    """Write `meta.yaml` into `run_dir` after validating it.

    A run directory carries exactly one reproducibility block; silently replacing
    it would let a rerun masquerade as the original, so overwriting is opt-in.
    """
    block = provenance.to_dict()
    validate(block)

    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "meta.yaml"
    if path.exists() and not overwrite:
        raise ProvenanceError(f"refusing to overwrite existing provenance: {path}")

    path.write_text(yaml.safe_dump(block, sort_keys=True), encoding="utf-8")
    return path


def read_meta(run_dir: Path) -> dict[str, Any]:
    """Load and validate the reproducibility block from a run directory."""
    block = yaml.safe_load((run_dir / "meta.yaml").read_text(encoding="utf-8"))
    validate(block)
    return block
