"""Run verifier checks inside the task container (Phase 5.2, Phase 6.2).

One container per verification, started from the instance's prebuilt SWE-bench
image with the repository already at the base commit. The patched tree is
produced by applying the frozen patch; the base tree by reverting it. Both
states are reachable in the same container, which is what makes the baseline
pass cheap enough to run for every instance.

The image name is derived from the instance id by the same rule the harness
uses, so no oracle field is read to stand a container up.

Isolation, matching the Phase 3 runner: one container per instance, named after
it, removed on exit. Nothing is shared between concurrent verifications.
"""

from __future__ import annotations

import json
import shlex
import subprocess
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

from reliability.env import clean_env
from reliability.verifier.regression import RunResult, TestResult, TestStatus

NAMESPACE = "swebench/sweb.eval.x86_64"
WORKDIR = "/testbed"


def image_for(instance_id: str) -> str:
    """Prebuilt evaluation image for an instance.

    Derived from the id rather than looked up, which avoids materialising the
    dataset and keeps this path free of any oracle surface.
    """
    return f"{NAMESPACE}.{instance_id.replace('__', '_1776_').lower()}:latest"


class ContainerError(RuntimeError):
    pass


@dataclass
class TaskContainer:
    """A running container for one instance, with patch apply/revert.

    Usable as a context manager; the container is removed on exit even if a
    check raises, so a failed verification does not leak a container.
    """

    instance_id: str
    patch_text: str
    image: str | None = None
    name: str = field(default="")
    _started: bool = field(default=False, init=False)
    _patch_applied: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.image = self.image or image_for(self.instance_id)
        self.name = self.name or f"verify_{self.instance_id}_{uuid.uuid4().hex[:8]}".lower()

    # -- lifecycle ---------------------------------------------------------

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, *exc_info) -> None:
        self.stop()

    def start(self) -> None:
        proc = subprocess.run(
            ["docker", "run", "-d", "--name", self.name, "-w", WORKDIR,
             "--network", "none", self.image, "sleep", "infinity"],
            capture_output=True, text=True, env=clean_env(), check=False,
        )
        if proc.returncode != 0:
            raise ContainerError(f"could not start {self.image}: {proc.stderr.strip()}")
        self._started = True

    def stop(self) -> None:
        if not self._started:
            return
        subprocess.run(["docker", "rm", "-f", self.name],
                       capture_output=True, env=clean_env(), check=False)
        self._started = False

    # -- execution ---------------------------------------------------------

    def exec(self, command: tuple[str, ...] | str, timeout_s: int = 120) -> tuple[int, str]:
        """Run a command in the container, returning (returncode, combined output)."""
        if not self._started:
            raise ContainerError("container is not running")
        script = command if isinstance(command, str) else shlex.join(command)
        try:
            proc = subprocess.run(
                ["docker", "exec", "-w", WORKDIR, self.name,
                 "bash", "-lc", script],
                capture_output=True, text=True, timeout=timeout_s,
                env=clean_env(), check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"command timed out after {timeout_s}s") from exc
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")

    # -- tree state --------------------------------------------------------

    def set_patched(self, patched: bool) -> None:
        """Move the working tree to the patched or base state.

        Idempotent, so a caller can ask for the state it already has without
        paying for a redundant apply or revert.
        """
        if patched == self._patch_applied:
            return
        if patched:
            rc, out = self._apply(reverse=False)
            if rc != 0:
                raise ContainerError(f"patch did not apply in container: {out[:300]}")
        else:
            rc, out = self._apply(reverse=True)
            if rc != 0:
                raise ContainerError(f"patch did not revert in container: {out[:300]}")
        self._patch_applied = patched

    def _apply(self, *, reverse: bool) -> tuple[int, str]:
        flag = "-R" if reverse else ""
        proc = subprocess.run(
            ["docker", "exec", "-i", "-w", WORKDIR, self.name,
             "bash", "-lc", f"git apply {flag} -"],
            input=self.patch_text, capture_output=True, text=True,
            env=clean_env(), check=False,
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


@dataclass(frozen=True, slots=True)
class ContainerRepoTree:
    """A RepoTree backed by the container's working tree at the base commit."""

    container: TaskContainer

    def list_files(self) -> tuple[str, ...]:
        rc, out = self.container.exec("git ls-files", timeout_s=120)
        if rc != 0:
            return ()
        return tuple(sorted(line for line in out.splitlines() if line.strip()))

    def read_text(self, path: str) -> str:
        rc, out = self.container.exec(("cat", path), timeout_s=60)
        return out if rc == 0 else ""


@dataclass
class ContainerCommandExecutor:
    """Phase 6 CommandExecutor backed by a live container."""

    container: TaskContainer

    def run(self, command, *, patched: bool, timeout_s: int) -> tuple[int, str]:
        self.container.set_patched(patched)
        return self.container.exec(tuple(command), timeout_s=timeout_s)


@dataclass
class ContainerTestExecutor:
    """Phase 5 TestExecutor backed by a live container.

    Results are read from pytest's JSON report where available, falling back to
    parsing the short summary. Tests that pytest never reported on are returned
    as NOT_RUN rather than omitted, so the classifier sees an explicit absence
    instead of inferring one.
    """

    container: TaskContainer
    report_path: str = "/tmp/verifier_report.json"

    def run(self, tests: tuple[str, ...], *, patched: bool, timeout_s: int) -> RunResult:
        if not tests:
            return RunResult()

        self.container.set_patched(patched)
        target = " ".join(shlex.quote(t) for t in tests)
        command = (
            f"python -m pytest {target} -p no:cacheprovider -q "
            f"--json-report --json-report-file={self.report_path} || true"
        )

        try:
            _, output = self.container.exec(command, timeout_s=timeout_s)
        except TimeoutError:
            return RunResult(
                results=tuple(TestResult(t, TestStatus.TIMEOUT) for t in tests),
                timed_out=True,
            )

        statuses = self._parse_report() or self._parse_summary(output, tests)

        # Anything pytest did not report on is NOT_RUN, never an implicit pass.
        return RunResult(results=tuple(
            TestResult(t, statuses.get(t, TestStatus.NOT_RUN)) for t in tests
        ))

    def _parse_report(self) -> dict[str, TestStatus]:
        rc, out = self.container.exec(("cat", self.report_path), timeout_s=60)
        if rc != 0:
            return {}
        try:
            payload = json.loads(out)
        except json.JSONDecodeError:
            return {}
        mapping = {
            "passed": TestStatus.PASSED, "failed": TestStatus.FAILED,
            "error": TestStatus.ERROR, "skipped": TestStatus.SKIPPED,
        }
        return {
            t["nodeid"]: mapping.get(t.get("outcome", ""), TestStatus.ERROR)
            for t in payload.get("tests", [])
        }

    def _parse_summary(self, output: str, tests: tuple[str, ...]) -> dict[str, TestStatus]:
        """Fallback for images without pytest-json-report installed."""
        statuses: dict[str, TestStatus] = {}
        markers = {
            "PASSED": TestStatus.PASSED, "FAILED": TestStatus.FAILED,
            "ERROR": TestStatus.ERROR, "SKIPPED": TestStatus.SKIPPED,
        }
        for line in output.splitlines():
            for marker, status in markers.items():
                if marker in line:
                    for test in tests:
                        if test in line:
                            statuses[test] = status
        return statuses


def verify_in_container(
    instance_id: str,
    patch_text: str,
    *,
    image: str | None = None,
) -> tuple[TaskContainer, ContainerRepoTree, ContainerCommandExecutor, ContainerTestExecutor]:
    """Start a container and return the pieces Phases 5 and 6 need.

    The caller is responsible for stopping the container; use `TaskContainer` as
    a context manager directly where possible.
    """
    container = TaskContainer(instance_id=instance_id, patch_text=patch_text, image=image)
    container.start()
    return (
        container,
        ContainerRepoTree(container),
        ContainerCommandExecutor(container),
        ContainerTestExecutor(container),
    )


def cache_dir_for(run_root: Path) -> Path:
    """Baseline cache location for a run. Per-instance files live underneath."""
    return run_root / "_baseline_cache"
