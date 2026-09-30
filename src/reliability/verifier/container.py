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

import re
import shlex
import subprocess
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

from reliability.env import clean_env
from reliability.verifier.regression import RunResult, TestResult, TestStatus
from reliability.verifier.selection import TestRunner, django_label

NAMESPACE = "swebench/sweb.eval.x86_64"
WORKDIR = "/testbed"
_DOCKER_CLI = Path("/mnt/wsl/docker-desktop/cli-tools/usr/bin/docker")


def _docker_bin() -> str:
    """Resolve the docker CLI even when Docker Desktop is not on PATH."""
    import shutil

    found = shutil.which("docker")
    if found and Path(found).exists():
        return found
    if _DOCKER_CLI.exists():
        return str(_DOCKER_CLI)
    return "docker"


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
            [_docker_bin(), "run", "-d", "--name", self.name, "-w", WORKDIR,
             "--network", "none", self.image, "sleep", "infinity"],
            capture_output=True, text=True, env=clean_env(), check=False,
        )
        if proc.returncode != 0:
            raise ContainerError(f"could not start {self.image}: {proc.stderr.strip()}")
        self._started = True

    def stop(self) -> None:
        if not self._started:
            return
        subprocess.run([_docker_bin(), "rm", "-f", self.name],
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
                [_docker_bin(), "exec", "-w", WORKDIR, self.name,
                 "bash", "-lc", script],
                capture_output=True, text=True, errors="replace", timeout=timeout_s,
                env=clean_env(), check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"command timed out after {timeout_s}s") from exc
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")

    def exec_input(self, command: str, data: str, timeout_s: int = 60) -> tuple[int, str]:
        """Run a command with `data` on stdin.

        Used to place the selected node ids in the container without putting
        them on the docker exec argument list, which overflows when a patch
        touches a widely referenced symbol.
        """
        if not self._started:
            raise ContainerError("container is not running")
        try:
            proc = subprocess.run(
                [_docker_bin(), "exec", "-i", "-w", WORKDIR, self.name,
                 "bash", "-lc", command],
                input=data, capture_output=True, text=True, errors="replace",
                timeout=timeout_s, env=clean_env(), check=False,
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
            [_docker_bin(), "exec", "-i", "-w", WORKDIR, self.name,
             "bash", "-lc", f"git apply {flag} -"],
            input=self.patch_text, capture_output=True, text=True, errors="replace",
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


_IDS_PATH = "/tmp/verifier_ids"
_OUT_LOG = "/tmp/verifier_out.txt"

#: Runs inside the container, under whatever Python the image ships. SWE-bench
#: images go back to Python 3.6, so nothing here may need 3.7 or later: no
#: `text=`, no `capture_output=`. Output is read as bytes and decoded by hand.
#:
#: Node ids arrive in a file, not on argv, and run in batches so one widely
#: referenced symbol cannot overflow exec. No pytest plugin is required: results
#: come from pytest's own `-v` lines, which every version prints.
#:
#: Pytest exits 4 and runs nothing in a batch when one id does not resolve. A
#: batch that does that is split in half and each half run again, so one bad id
#: costs its own result and not its neighbours'. The splitting is capped so a
#: usage error cannot turn into hundreds of runs.
_BATCH_DRIVER = r'''
import pathlib, subprocess, sys
kind = sys.argv[1]
ids = [line.strip() for line in pathlib.Path("/tmp/verifier_ids").read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
log = pathlib.Path("/tmp/verifier_out.txt")
log.write_text("", encoding="utf-8")
budget = [200]

def run(part):
    if kind == "django":
        cmd = ["python", "tests/runtests.py", "--verbosity=2"] + part
    else:
        cmd = ["python", "-m", "pytest"] + part + ["-p", "no:cacheprovider", "-v"]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode("utf-8", "replace")
    with log.open("a", encoding="utf-8") as fh:
        fh.write(text)
    print(text, end="")
    return proc.returncode

def execute(part):
    code = run(part)
    if kind == "pytest" and code == 4 and len(part) > 1 and budget[0] > 0:
        budget[0] -= 1
        mid = len(part) // 2
        execute(part[:mid])
        execute(part[mid:])

for start in range(0, len(ids), 25):
    execute(ids[start:start + 25])
'''


@dataclass
class ContainerTestExecutor:
    """Phase 5 TestExecutor backed by a live container.

    The command is the runner discovered for this repository. Pytest results
    are read from its own ``-v`` lines, so no plugin has to exist in the image;
    Django's ``tests/runtests.py`` is parsed from its verbose lines. Tests the
    runner never reported on are returned as NOT_RUN rather than omitted, so
    the classifier sees an explicit absence instead of inferring one. When
    nothing at all was reported, the tail of the runner's output rides along on
    the result, so a broken runner says why instead of reading as an empty run.
    """

    container: TaskContainer
    runner: TestRunner | None = None

    def run(self, tests: tuple[str, ...], *, patched: bool, timeout_s: int) -> RunResult:
        if not tests:
            return RunResult()

        self.container.set_patched(patched)
        runner = self.runner or TestRunner("pytest", "default")
        native = (
            tuple(django_label(test) for test in tests)
            if runner.name == "django" else tests
        )
        command = f"python /tmp/verifier_driver.py {runner.name}"
        try:
            # The ids go through stdin. Embedding them in `docker exec` argv is
            # what raised E2BIG once a short symbol selected a large tier-2 set.
            self.container.exec_input(
                f"cat > {_IDS_PATH}", "\n".join(native) + "\n", timeout_s=60)
            self.container.exec_input(
                "cat > /tmp/verifier_driver.py", _BATCH_DRIVER, timeout_s=60)
            _, output = self.container.exec(command, timeout_s=timeout_s)
        except TimeoutError:
            try:
                statuses = self._partial_statuses(runner, tests)
            except TimeoutError:
                statuses = {}
            return RunResult(
                results=tuple(
                    TestResult(t, statuses.get(t, TestStatus.TIMEOUT)) for t in tests
                ),
                timed_out=True,
            )

        statuses = _parse_output(runner, output, tests)

        # Anything the runner did not report on is NOT_RUN, never an implicit pass.
        return RunResult(
            results=tuple(
                TestResult(t, statuses.get(t, TestStatus.NOT_RUN)) for t in tests
            ),
            note="" if statuses else _no_results_note(output),
        )

    def _partial_statuses(self, runner: TestRunner, tests) -> dict:
        """Read whatever a timed-out run managed to write to its log."""
        rc, logged = self.container.exec(("cat", _OUT_LOG), timeout_s=30)
        return _parse_output(runner, logged, tests) if rc == 0 else {}


def _parse_output(runner: TestRunner, output: str, tests: tuple[str, ...]) -> dict:
    if runner.name == "django":
        return _parse_django(output, tests)
    return _parse_pytest(output, tests)


def _no_results_note(output: str) -> str:
    lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
    if not lines:
        return "the test runner produced no output"
    return "the test runner reported no results; output ended: " + " | ".join(lines[-3:])[:400]


_PYTEST_LINE = re.compile(
    r"^(?P<id>\S.*?::\S.*?) (?P<outcome>PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b"
)
_PYTEST_OUTCOME = {
    "PASSED": TestStatus.PASSED,
    "XPASS": TestStatus.PASSED,      # non-strict unexpected pass; strict is reported FAILED
    "FAILED": TestStatus.FAILED,
    "ERROR": TestStatus.ERROR,
    "SKIPPED": TestStatus.SKIPPED,
    "XFAIL": TestStatus.SKIPPED,     # an expected failure neither passed nor regressed
}
#: A test can print PASSED and then ERROR at teardown. The worse one stands.
_PYTEST_SEVERITY = {
    TestStatus.SKIPPED: 0, TestStatus.PASSED: 1, TestStatus.FAILED: 2, TestStatus.ERROR: 3,
}


def _parse_pytest(output: str, tests: tuple[str, ...]) -> dict[str, TestStatus]:
    """Read ``pytest -v`` lines. Only ids that were asked for are accepted."""
    wanted = set(tests)
    statuses: dict[str, TestStatus] = {}
    for line in output.splitlines():
        match = _PYTEST_LINE.match(line.strip())
        if match is None or match.group("id") not in wanted:
            continue
        test, status = match.group("id"), _PYTEST_OUTCOME[match.group("outcome")]
        earlier = statuses.get(test)
        if earlier is None or _PYTEST_SEVERITY[status] >= _PYTEST_SEVERITY[earlier]:
            statuses[test] = status
    return statuses


_DJANGO_LINE = re.compile(
    r"^(?P<name>\w+) \((?P<label>[^)]+)\) \.\.\. (?P<outcome>ok|FAIL|ERROR|skipped)\b",
    re.IGNORECASE,
)
_DJANGO_OUTCOME = {
    "ok": TestStatus.PASSED,
    "fail": TestStatus.FAILED,
    "error": TestStatus.ERROR,
    "skipped": TestStatus.SKIPPED,
}


def _parse_django(output: str, tests: tuple[str, ...]) -> dict[str, TestStatus]:
    """Map ``tests/runtests.py --verbosity=2`` lines back onto node ids."""
    by_label = {django_label(test): test for test in tests}
    statuses: dict[str, TestStatus] = {}
    for line in output.splitlines():
        match = _DJANGO_LINE.match(line.strip())
        if match is None:
            continue
        label = match.group("label")
        status = _DJANGO_OUTCOME[match.group("outcome").lower()]
        node = by_label.get(label)
        if node is None:
            # Django sometimes prints ``module.Class`` without the method.
            node = next(
                (test for lab, test in by_label.items()
                 if lab == f"{label}.{match.group('name')}" or lab.endswith("." + label)),
                None,
            )
        if node is not None:
            statuses[node] = status
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
