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

import base64
import contextvars
import hashlib
import json
import os
import shlex
import subprocess
import uuid
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Self

from reliability.env import clean_env
from reliability.verifier.collection import validate_in_container
from reliability.verifier.regression import RunResult, TestResult, TestStatus
from reliability.verifier.result_parser import mapping_for, parse_capture
from reliability.verifier.selection import TestRunner, django_label
from reliability.verifier.validated_run import apply_validation

NAMESPACE = "swebench/sweb.eval.x86_64"
WORKDIR = "/testbed"
#: Set by a run around container launch. The base-sandbox callable stays
#: `(instance_id)` so it cannot be handed a patch; the label is not a patch.
experiment_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "reliability_experiment_id", default="",
)
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
    experiment_id: str = ""
    _started: bool = field(default=False, init=False)
    _patch_applied: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.image = self.image or image_for(self.instance_id)
        if not self.name:
            label = f"{self.experiment_id}_" if self.experiment_id else ""
            self.name = f"verify_{label}{self.instance_id}_{uuid.uuid4().hex[:8]}".lower()

    # -- lifecycle ---------------------------------------------------------

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, *exc_info) -> None:
        self.stop()

    def run_args(self) -> list[str]:
        """The `docker run` argv, including the experiment label when set."""
        cmd = [_docker_bin(), "run", "-d", "--name", self.name]
        if self.experiment_id:
            cmd.extend(["--label", f"experiment_id={self.experiment_id}"])
        cmd.extend(["-w", WORKDIR, "--network", "none", self.image, "sleep", "infinity"])
        return cmd

    def start(self) -> None:
        proc = subprocess.run(
            self.run_args(),
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

    def exec_raw(self, command: str, timeout_s: int):
        """V2 capture boundary: retain undecoded bytes, including timeout output."""
        try:
            proc = subprocess.run(
                [_docker_bin(), "exec", "-w", WORKDIR, self.name, "bash", "-lc", command],
                capture_output=True, timeout=timeout_s,
                env=clean_env(), check=False,
            )
            return proc.returncode, proc.stdout, proc.stderr, False
        except subprocess.TimeoutExpired as exc:
            return None, exc.stdout or b"", exc.stderr or b"", True

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
#: Validated IDs arrive through stdin, then are grouped by their test module.
#: Each module has one runner process; a load abort retries only unreported
#: valid IDs individually. GIS guard modules stay isolated and missing.
# Embed the shared, Python-3.6-compatible terminal parser in the standalone driver.
# No project package is required in a task image.
_DRIVER_PARSER = Path(__file__).with_name('result_parser.py').read_text().replace(
    'from reliability.verifier.selection import django_label\n', '')
_BATCH_DRIVER = 'exec(' + repr(_DRIVER_PARSER) + ')\n' + r'''
import collections, json, os, pathlib, subprocess, sys, time
kind = sys.argv[1]
ids = [line.strip() for line in pathlib.Path("/tmp/verifier_ids").read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
map_path = pathlib.Path("/tmp/verifier_module_ids.json")
module_map = json.loads(map_path.read_text()) if map_path.exists() else {}
try:
    os.setsid()
except OSError:
    pass
pathlib.Path("/tmp/verifier_pgid").write_text(str(os.getpgrp()))
log = open("/tmp/verifier_out.txt", "wb", buffering=0)
events = open("/tmp/verifier_events.jsonl", "w", buffering=1)
sequence = [0]

def seen(output, part, module):
    observed = parse_capture(output.decode("utf-8", "replace"), kind)
    found = set()
    for rid, value in observed.items():
        if value["kind"] != "case":
            continue
        if rid in part:
            found.add(rid)
        elif kind == "pytest" and "::" in rid:
            path, suffix = rid.split("::", 1)
            canonical = module + "::" + suffix
            if (module == path or module.endswith("/" + path)) and canonical in part:
                found.add(canonical)
    return found

def run(part, module, retry=False, parent=None):
    if kind == "sympy":
        cmd = ["python", "/tmp/verifier_sympy_driver.py", "execute", module] + part
    elif kind == "django":
        cmd = ["python", "tests/runtests.py", "--verbosity=2"] + part
    else:
        cmd = ["python", "-m", "pytest", "-p", "no:cacheprovider", "-v", "--"] + part
    sequence[0] += 1
    index, start = sequence[0], time.monotonic()
    events.write(json.dumps(dict(event="start", batch=index, module=module,
                                retry=retry, parent=parent, argv=cmd, ids=part,
                                offset=log.tell())) + "\n")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    captured = bytearray()
    while True:
        chunk = os.read(proc.stdout.fileno(), 65536)
        if not chunk:
            break
        captured.extend(chunk)
        log.write(chunk)
        sys.stdout.buffer.write(chunk)
        sys.stdout.buffer.flush()
    code = proc.wait()
    observed = seen(bytes(captured), part, module)
    text = bytes(captured).decode("utf-8", "replace")
    gis = "Aborting: A GIS database backend is required to run gis_tests." in text
    missing = [tid for tid in part if tid not in observed]
    # A negative exit with unreported identities is a load/collection abort.
    # Ordinary assertion FAIL/ERROR with every identity observed is not retried.
    load_failure = bool(code and missing)
    retry_ids = missing if load_failure and not retry and not gis else []
    events.write(json.dumps(dict(event="end", batch=index, module=module,
        returncode=code, retry=retry, parent=parent, observed_ids=sorted(observed),
        load_failure=load_failure, gis_guard=gis, split=bool(retry_ids),
        missing_ids=missing, offset=log.tell(), duration_s=time.monotonic()-start)) + "\n")
    return index, retry_ids

modules = collections.OrderedDict()
for identity in ids:
    module = module_map.get(identity)
    if module is None:
        module = identity.rsplit(".", 2)[0] if kind == "django" else identity.split("::", 1)[0]
    modules.setdefault(module, []).append(identity)
for module, part in modules.items():
    parent, remaining = run(part, module)
    for identity in remaining:
        run([identity], module, retry=True, parent=parent)
events.write(json.dumps(dict(event="complete")) + "\n")
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
    evidence_dir: Path | None = None

    def _capture(self, command, timeout_s):
        if hasattr(self.container, "exec_raw"):
            return self.container.exec_raw(command, timeout_s)
        # Structured executors used by unit tests; never claim raw completeness.
        try:
            rc, output = self.container.exec(command, timeout_s=timeout_s)
            return rc, output.encode(), b"", False
        except TimeoutError:
            return None, b"", b"", True

    def run(self, tests: tuple[str, ...], *, patched: bool, timeout_s: int) -> RunResult:
        if not tests:
            return RunResult()

        self.container.set_patched(patched)
        runner = self.runner or TestRunner("pytest", "default")
        validation = validate_in_container(self.container, tests, runner, timeout_s=timeout_s)
        actual = validation.context.get('runner', runner.name)
        runner = TestRunner(actual, validation.context.get('runner_evidence', runner.evidence))
        validation = replace(validation, context={**validation.context,
            'instance_id': getattr(self.container, 'instance_id', ''),
            'tree': 'patched' if patched else 'base', 'runner': runner.name})
        if self.evidence_dir is not None:
            folder = self.evidence_dir / (("patched" if patched else "base") + "_validation_" + uuid.uuid4().hex)
            folder.mkdir(parents=True, exist_ok=False)
            path = folder / 'validation.json'
            raw = (json.dumps(validation.to_dict(), indent=2) + '\n').encode()
            path.write_bytes(raw)
            validation = replace(validation, evidence_files={'validation.json': str(path.resolve())},
                                 evidence_sha256={'validation.json': hashlib.sha256(raw).hexdigest()})
        if validation.errors:
            return apply_validation(RunResult(infrastructure_errors=validation.errors,
                             requested_tests=tests,
                             validation_summary=validation.to_dict(),
                             evidence_files=validation.evidence_files,
                             evidence_sha256=validation.evidence_sha256,
                             note='ID validation unavailable'), validation)
        tests = validation.runnable_ids
        if not tests:
            return apply_validation(RunResult(evidence_complete=True), validation)
        native = (
            tuple(django_label(test) for test in tests)
            if runner.name == "django" else tests
        )
        command = f"python /tmp/verifier_driver.py {runner.name}"
        errors = []
        raw_stdout = raw_stderr = runner_log = b""
        event_bytes = b""
        timed_out = False
        events = ()
        files, digests = {}, {}
        try:
            # The ids go through stdin. Embedding them in `docker exec` argv is
            # what raised E2BIG once a short symbol selected a large tier-2 set.
            rc, _ = self.container.exec_input(
                f"cat > {_IDS_PATH}", "\n".join(native) + "\n", timeout_s=60)
            if rc:
                errors.append("selected-ID upload failed")
            rc, _ = self.container.exec_input(
                "cat > /tmp/verifier_module_ids.json",
                json.dumps({label: test.split('::', 1)[0] for label, test in zip(native, tests)}),
                timeout_s=60)
            if rc:
                errors.append("module-ID upload failed")
            rc, _ = self.container.exec_input(
                "cat > /tmp/verifier_driver.py", _BATCH_DRIVER, timeout_s=60)
            if rc:
                errors.append("capture-driver upload failed")
            # A failed driver must not expose stale logs from an earlier tree/pass.
            rc, _, _, clear_timeout = self._capture(
                "rm -f /tmp/verifier_out.txt /tmp/verifier_events.jsonl /tmp/verifier_pgid", 30)
            if rc or clear_timeout:
                errors.append("could not clear previous capture")
            if errors:
                return apply_validation(RunResult(
                    results=tuple(TestResult(t, TestStatus.NOT_RUN) for t in tests),
                    infrastructure_errors=tuple(errors), requested_tests=tuple(tests),
                    note="; ".join(errors)), validation)
            rc, raw_stdout, raw_stderr, timed_out = self._capture(command, timeout_s)
            if rc not in (0, None):
                errors.append(f"capture driver exit {rc}")
            if timed_out:
                kill = ("python -c 'import os,signal; "
                        "os.killpg(int(open(\"/tmp/verifier_pgid\").read()),signal.SIGKILL)'")
                self._capture(kill, 30)
            rc, logged, _, log_timeout = self._capture("cat " + _OUT_LOG, 30)
            runner_log = logged if rc == 0 and not log_timeout else raw_stdout
            rc, event_bytes, _, event_timeout = self._capture("cat /tmp/verifier_events.jsonl", 30)
            if rc != 0 or event_timeout:
                event_bytes = b""
        except TimeoutError:
            timed_out = True
        # Persist bytes/events BEFORE either legacy parsing or raw-ID accounting.
        if self.evidence_dir is not None:
            folder = self.evidence_dir / (("patched" if patched else "base") + "_" + uuid.uuid4().hex)
            folder.mkdir(parents=True, exist_ok=False)
            for name, data in (("stdout.raw", raw_stdout), ("stderr.raw", raw_stderr),
                               ("runner.raw", runner_log),
                               ("events.jsonl", event_bytes)):
                path = folder / name
                with path.open("xb") as f:
                    f.write(data)
                    f.flush()
                    os.fsync(f.fileno())
                files[name] = str(path.resolve())
                digests[name] = hashlib.sha256(data).hexdigest()
        try:
            events = tuple(json.loads(line) for line in event_bytes.splitlines())
            if not all(isinstance(event, dict) for event in events):
                raise ValueError("capture event is not an object")
        except (ValueError, TypeError):
            events = ()
            errors.append("malformed capture events")
        return apply_validation(run_from_capture(
            runner, tests, runner_log=runner_log, raw_stderr=raw_stderr,
            raw_stdout=raw_stdout, events=events, timed_out=timed_out,
            infrastructure_errors=tuple(errors), evidence_files=files,
            evidence_sha256=digests,
        ), validation)

    def _partial_statuses(self, runner: TestRunner, tests) -> dict:
        """Read whatever a timed-out run managed to write to its log."""
        rc, logged = self.container.exec(("cat", _OUT_LOG), timeout_s=30)
        return _parse_output(runner, logged, tests) if rc == 0 else {}


def run_from_capture(
    runner: TestRunner, tests: tuple[str, ...], *, runner_log: bytes,
    raw_stderr: bytes = b"", raw_stdout: bytes = b"", events: tuple[dict, ...] = (),
    timed_out: bool = False, infrastructure_errors: tuple[str, ...] = (),
    evidence_files: dict[str, str] | None = None,
    evidence_sha256: dict[str, str] | None = None,
) -> RunResult:
    """Parse one captured pass identically for live execution and offline replay.

    This function performs no I/O. Execution failures and event completeness
    remain independent of whether a terminal outcome can be read.
    """
    output = (runner_log + raw_stderr).decode("utf-8", "replace")
    errors = list(infrastructure_errors)
    observed = parse_capture(output, runner.name)
    # A retried module's loader/fixture placeholders are superseded. Preserve
    # actual case outcomes already observed in that attempt and keep raw bytes.
    for event in events:
        if event.get('event') != 'end' or not event.get('split'):
            continue
        start = next((e for e in events if e.get('event') == 'start'
                      and e.get('batch') == event.get('batch')), {})
        begin, finish = start.get('offset'), event.get('offset')
        if not isinstance(begin, int) or not isinstance(finish, int):
            continue
        first, last = runner_log[:begin].count(b'\n') + 1, runner_log[:finish].count(b'\n')
        admitted = set(event.get('observed_ids', ()))
        observed = {rid: value for rid, value in observed.items()
                    if not (first <= value['line'] <= last and
                            (value['kind'] != 'case' or rid not in admitted))}
    statuses = _parse_output(runner, output, tests, observed=observed)
    raw_results, mappings, unmatched = account_raw_output(runner, output, tests, observed=observed)
    complete = bool(events and events[-1].get("event") == "complete")
    starts = {e.get("batch") for e in events if e.get("event") == "start"}
    ends = {e.get("batch") for e in events if e.get("event") == "end"}
    if not starts:
        complete = False
    if starts != ends:
        errors.append("unfinished runner batch")
    for event in events:
        if event.get("event") == "end" and not event.get("split"):
            if event.get("returncode") not in (0, 1):
                errors.append(f"runner batch {event.get('batch')} exit {event.get('returncode')}")
            elif event.get("returncode") == 1:
                start = next((e for e in events if e.get("event") == "start"
                              and e.get("batch") == event.get("batch")), {})
                if "offset" not in start or "offset" not in event:
                    complete = False
                else:
                    batch_output = runner_log[start["offset"]:event["offset"]].decode("utf-8", "replace")
                    cases, _, _ = account_raw_output(runner, batch_output, tests)
                    explained = any(r.status in (TestStatus.FAILED, TestStatus.ERROR)
                                    for r in cases)
                    # unittest treats unexpected success as a nonzero run;
                    # pytest non-strict XPASS alone does not explain exit 1.
                    explained |= runner.name == "django" and any(
                        r.status is TestStatus.XPASS for r in cases)
                    if not explained:
                        errors.append("unexplained nonzero runner exit")
    for event in events:
        if event.get('event') != 'end' or event.get('split') or not event.get('load_failure'):
            continue
        start = next((e for e in events if e.get('event') == 'start'
                      and e.get('batch') == event.get('batch')), {})
        begin, finish = start.get('offset', 0), event.get('offset', len(runner_log))
        message = runner_log[begin:finish].decode('utf-8', 'replace')
        from reliability.verifier.collection import classify_collector_failure
        failure = TestStatus(classify_collector_failure(message).lower())
        mapper = mapping_for(tests, runner.name)
        for missing in event.get('missing_ids', ()):
            for tid in mapper(missing):
                statuses[tid] = failure
        errors.append('GIS environment guard' if event.get('gis_guard') else 'module collection failed')
    # Anything the runner did not report on is NOT_RUN, never an implicit pass.
    return RunResult(
        results=tuple(
            TestResult(t, statuses.get(t, TestStatus.TIMEOUT if timed_out else TestStatus.NOT_RUN))
            for t in tests
        ),
        note="" if statuses else _no_results_note(output),
        timed_out=timed_out, raw_results=raw_results, raw_id_map=mappings,
        unmatched_ids=unmatched, infrastructure_errors=tuple(errors),
        evidence_complete=complete and not errors,
        raw_stdout_b64=base64.b64encode(raw_stdout).decode(),
        raw_stderr_b64=base64.b64encode(raw_stderr).decode(),
        runner_log_b64=base64.b64encode(runner_log).decode(),
        events=events, evidence_files=evidence_files or {}, evidence_sha256=evidence_sha256 or {},
        requested_tests=tuple(tests),
    )


def _parse_output(runner: TestRunner, output: str, tests: tuple[str, ...], *, observed=None) -> dict:
    """Admit only unique selected families; concrete cases remain separately scored."""
    mapper = mapping_for(tests, runner.name)
    statuses = {}
    parsed = parse_capture(output, runner.name) if observed is None else observed
    for raw_id, value in parsed.items():
        selected = mapper(raw_id)
        if len(selected) != 1 or value['kind'] != 'case':
            continue
        status = TestStatus(value['status'])
        earlier = statuses.get(selected[0])
        if earlier is None or _PYTEST_SEVERITY[status] >= _PYTEST_SEVERITY[earlier]:
            statuses[selected[0]] = status
    return statuses


def _no_results_note(output: str) -> str:
    lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
    if not lines:
        return "the test runner produced no output"
    return "the test runner reported no results; output ended: " + " | ".join(lines[-3:])[:400]


# Worst terminal observation wins, including a teardown ERROR after PASSED.
_PYTEST_SEVERITY = {
    TestStatus.SKIPPED: 0, TestStatus.XFAIL: 1, TestStatus.PASSED: 2,
    TestStatus.XPASS: 3, TestStatus.FAILED: 4, TestStatus.ERROR: 5, TestStatus.TIMEOUT: 6,
}


def _parse_pytest(output: str, tests: tuple[str, ...]) -> dict[str, TestStatus]:
    return _parse_output(TestRunner("pytest", "native parser"), output, tests)


def _parse_django(output: str, tests: tuple[str, ...]) -> dict[str, TestStatus]:
    return _parse_output(TestRunner("django", "native parser"), output, tests)


def account_raw_output(runner: TestRunner, output: str, tests: tuple[str, ...], *, observed=None):
    """Preserve each concrete outcome and every ambiguous/unmapped identity."""
    mapper = mapping_for(tests, runner.name)
    parsed = parse_capture(output, runner.name) if observed is None else observed
    mappings = {
        raw_id: tuple(mapper(raw_id)) if observed['kind'] == 'case' else ()
        for raw_id, observed in parsed.items()
    }
    return (
        tuple(TestResult(raw_id, TestStatus(observed['status']))
              for raw_id, observed in parsed.items()),
        mappings,
        tuple(raw_id for raw_id, selected in mappings.items() if len(selected) != 1),
    )
