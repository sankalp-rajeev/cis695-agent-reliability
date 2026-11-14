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
import time
import uuid
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Self

from reliability.env import clean_env
from reliability.verifier.accounting import ADMITTED_STATUSES
from reliability.verifier.collection import validate_in_container
from reliability.verifier.node_ids import normalize_pytest_id
from reliability.verifier.regression import RunResult, TestResult, TestStatus
from reliability.verifier.result_parser import (active_test, mapping_for, module_identity_failures,
    parse_capture, sympy_import_batches, sympy_silent_nonzero)
from reliability.verifier.selection import TestRunner, django_label
from reliability.verifier.source_integrity import (
    BaseSourceSpec,
    GeneratedInputAudit,
    SourceIntegrityError,
    generated_inventory,
    runtime_stage_var,
    verify_base_source,
)
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
    source_spec: BaseSourceSpec | None = None
    source_receipt_path: Path | None = None
    source_integrity: dict = field(default_factory=dict, init=False)
    _generated_pin: dict | None = field(default=None, init=False)
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
        cmd = [_docker_bin(), "run", "-d", "--cpu-shares", "2048", "--name", self.name]
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
        if self.source_spec is not None:
            try:
                try:
                    self.source_integrity = verify_base_source(self, self.source_spec)
                except SourceIntegrityError as exc:
                    self.source_integrity = exc.receipt
                    raise
                finally:
                    self._save_source_receipt()
            except BaseException:
                self.stop()
                raise

    def _save_source_receipt(self):
        if self.source_receipt_path is not None:
            self.source_receipt_path.parent.mkdir(parents=True, exist_ok=True)
            self.source_receipt_path.write_text(json.dumps(self.source_integrity, indent=2) + "\n")

    def generated_snapshot(self, previous=(), *, timeout_s=60):
        paths = set(previous) | set(self._generated_pin or {})
        value = generated_inventory(self, paths, timeout_s=timeout_s)
        if self._generated_pin is None:
            self._generated_pin = dict(value['files'])
        value['pinned_files'] = self._generated_pin
        return value

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
    'from reliability.verifier.selection import django_label\n', '').replace(
    'from reliability.verifier.node_ids import normalize_pytest_id\n',
    Path(__file__).with_name('node_ids.py').read_text() + '\n')
_BATCH_DRIVER = 'exec(' + repr(_DRIVER_PARSER) + ')\n' + r'''
import collections, json, os, pathlib, select, signal, subprocess, sys, time
import base64
kind = sys.argv[1]
budget = float(sys.argv[2]) if len(sys.argv) > 2 else 1800.0
prior_elapsed = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
pass_start = time.monotonic()
deadline = pass_start + budget
cap_hit = [False]
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
        if kind == "pytest":
            rid = normalize_pytest_id(rid)
        if rid in part:
            found.add(rid)
        elif kind == "pytest" and "::" in rid:
            path, suffix = rid.split("::", 1)
            canonical = normalize_pytest_id(module + "::" + suffix)
            if (module == path or module.endswith("/" + path)) and canonical in part:
                found.add(canonical)
    return found

def not_reached(part, module):
    cap_hit[0] = True
    events.write(json.dumps(dict(event="not_reached", module=module, ids=part,
        elapsed_s=prior_elapsed + time.monotonic()-pass_start, reason="per_pass_budget")) + "\n")

def run(part, module, retry=False, parent=None):
    if time.monotonic() >= deadline:
        not_reached(part, module)
        return None, []
    if kind == "sympy":
        cmd = ["python", "/tmp/verifier_sympy_driver.py", "execute", module] + part
    elif kind == "django":
        cmd = ["python", "tests/runtests.py", "--verbosity=2"]
        if len(sys.argv) > 4 and sys.argv[4] == "parallel_one":
            cmd += ["--parallel", "1"]
        cmd += part
    else:
        cmd = ["python", "-m", "pytest", "-p", "no:cacheprovider", "-v", "--"] + part
    sequence[0] += 1
    index, start = sequence[0], time.monotonic()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE if kind == "sympy" else subprocess.STDOUT, start_new_session=True)
    events.write(json.dumps(dict(event="start", batch=index, module=module, pid=proc.pid,
                                retry=retry, parent=parent, argv=cmd, ids=part,
                                offset=log.tell())) + "\n")
    captured = bytearray()
    captured_stderr = bytearray()
    streams = {proc.stdout.fileno(): proc.stdout, proc.stderr.fileno(): proc.stderr} if kind == "sympy" else None
    timed_out = False
    while streams if kind == "sympy" else True:
        remaining = deadline - time.monotonic()
        if remaining <= 0 and not timed_out:
            timed_out = True
            cap_hit[0] = True
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        ready, _, _ = select.select(list(streams) if kind == "sympy" else [proc.stdout], [], [], max(0.001, min(0.1, remaining)))
        if not ready:
            continue
        if kind != "sympy":
            chunk = os.read(proc.stdout.fileno(), 65536)
            if not chunk:
                break
            captured.extend(chunk)
            log.write(chunk)
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
            continue
        for descriptor in ready:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                streams.pop(descriptor)
                continue
            if descriptor == proc.stderr.fileno():
                captured_stderr.extend(chunk)
            captured.extend(chunk)
            log.write(chunk)
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
    code = proc.wait()
    observed = seen(bytes(captured), part, module)
    text = bytes(captured).decode("utf-8", "replace")
    gis = "Aborting: A GIS database backend is required to run gis_tests." in text
    missing = [tid for tid in part if tid not in observed]
    active = active_test(kind, missing, text)
    per_test_output=any(v["kind"]=="case" for v in parse_capture(text,kind).values())
    progress = bool(per_test_output or active)
    # A process death after execution progress is an outcome, never a loader retry.
    load_failure = bool(missing and not timed_out and not progress)
    retry_ids = missing if load_failure and not retry else []
    events.write(json.dumps(dict(event="end", batch=index, module=module,
        returncode=code, retry=retry, parent=parent, observed_ids=sorted(observed), timed_out=timed_out,
        load_failure=load_failure, gis_guard=gis, split=bool(retry_ids),
        active_id=active, test_started=bool(active), per_test_output=per_test_output,
        missing_ids=missing, offset=log.tell(), duration_s=time.monotonic()-start,
        **({'stderr_b64':base64.b64encode(bytes(captured_stderr)).decode('ascii')} if kind == "sympy" else {}))) + "\n")
    if timed_out:
        not_reached(missing, module)
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
events.write(json.dumps(dict(event="complete", timed_out=cap_hit[0], budget_s=budget, elapsed_s=prior_elapsed+time.monotonic()-pass_start)) + "\n")
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
    _base_progress_modules: frozenset[str] = field(default_factory=frozenset, init=False, repr=False)

    def _capture(self, command, timeout_s):
        if hasattr(self.container, "exec_raw"):
            return self.container.exec_raw(command, timeout_s)
        # Structured executors used by unit tests; never claim raw completeness.
        try:
            rc, output = self.container.exec(command, timeout_s=timeout_s)
            return rc, output.encode(), b"", False
        except TimeoutError:
            return None, b"", b"", True

    def _execute_once(self, command, timeout_s):
        result = self._capture(command, timeout_s)
        if result[3]:
            kill_code = "import os,signal,json,pathlib\n"
            kill_code += "p=pathlib.Path('/tmp/verifier_events.jsonl')\n"
            kill_code += "events=[json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []\n"
            kill_code += "pids=[e['pid'] for e in events if e.get('event')=='start' and 'pid' in e]\n"
            kill_code += "pids.append(int(open('/tmp/verifier_pgid').read()))\n"
            kill_code += "for pid in pids:\n try: os.killpg(pid,signal.SIGKILL)\n except ProcessLookupError: pass\n"
            kill = "python -c " + shlex.quote(kill_code)
            self._capture(kill, 30)
        return result

    def run(self, tests: tuple[str, ...], *, patched: bool, timeout_s: int) -> RunResult:
        if isinstance(self.container, TaskContainer) and self.container.source_spec is None:
            raise ValueError("Fix 9 requires a pinned BaseSourceSpec before runtime")
        if isinstance(self.container, TaskContainer) and self.container.source_integrity.get('status') != 'VERIFIED':
            raise ValueError("Fix 9 requires a verified pristine base-source receipt")
        if timeout_s <= 0:
            raise ValueError("per-pass budget must be positive")
        started = time.monotonic()
        deadline = started + timeout_s
        snapshot = getattr(self.container, 'generated_snapshot', None)
        if snapshot is not None:
            method = snapshot
            snapshot = lambda previous: method(previous, timeout_s=30)
        audit = GeneratedInputAudit(snapshot)
        boundary_stage = 'confirmation' if runtime_stage_var.get() == 'confirmation' else 'pass'
        audit.capture(boundary_stage, 'before')
        result = None
        stages = [{'stage':'pristine_source','status':getattr(self.container,'source_integrity',{}).get('status','STRUCTURED_EXECUTOR'),
                   'input_count':1,'output_count':1}]
        try:
            result = self._run_audited(tests, patched=patched, timeout_s=timeout_s, audit=audit, started=started, deadline=deadline, stages=stages)
        finally:
            audit.capture(boundary_stage, 'after')
            details = audit.to_dict()
            details.update(tree='patched' if patched else 'base', runtime_kind=runtime_stage_var.get())
            files = dict(result.evidence_files) if result is not None else {}
            hashes = dict(result.evidence_sha256) if result is not None else {}
            if self.evidence_dir is not None:
                folder = self.evidence_dir / (('patched' if patched else 'base') + '_generated_' + uuid.uuid4().hex)
                folder.mkdir(parents=True, exist_ok=False)
                path = folder / 'generated_inputs.json'
                raw = (json.dumps(details, indent=2) + '\n').encode()
                path.write_bytes(raw)
                files['generated_inputs.json'] = str(path.resolve())
                hashes['generated_inputs.json'] = hashlib.sha256(raw).hexdigest()
        if not patched:
            self._base_progress_modules = frozenset(e.get('module', '') for e in result.events
                if e.get('event') == 'end' and (e.get('observed_ids') or e.get('test_started')
                    or e.get('active_id') or e.get('per_test_output')))
        return replace(result, generated_inputs=details, duration_s=time.monotonic()-started, budget_s=timeout_s,
                       evidence_flags=tuple(dict.fromkeys((*result.evidence_flags, *audit.flags,
                           *(('COLLECTOR_FALLBACK',) if any(r.get('collector_fallback') for r in result.validation) else ())))),
                       stage_health=tuple(stages),
                       source_integrity=getattr(self.container, 'source_integrity', {}),
                       evidence_files=files, evidence_sha256=hashes)

    def _run_audited(self, tests, *, patched, timeout_s, audit, started, deadline, stages) -> RunResult:
        if not tests:
            stages.extend({'stage':name,'status':'EMPTY_INPUT','input_count':0,'output_count':0}
                          for name in ('patch_application','native_collection','runner_startup','execution','admission'))
            return RunResult(requested_tests=tests)

        if timeout_s <= 0:
            raise ValueError("per-pass budget must be positive")
        def remaining(limit=None):
            value = max(0.001, deadline - time.monotonic())
            return min(value, limit) if limit is not None else value
        def finish(result, validation):
            mapped = apply_validation(result, validation)
            from reliability.verifier.run_health import allowed_failure, exception_rules, module_execution_stages
            tree='patched' if patched else 'base'
            task=getattr(self.container,'instance_id','')
            exceptions=exception_rules()
            execution_stages=module_execution_stages(task,tree,runner.name,result,exceptions)
            stages.extend(execution_stages)
            allowed_execution={t for stage in execution_stages if stage.get('allowed_exception') for t in stage['input_ids']}
            for stage in stages:
                if stage['stage']=='execution' and allowed_execution:
                    stage['original_input_count']=stage['input_count']
                    stage['input_count']=max(0,stage['input_count']-len(allowed_execution))
                    stage['excluded_prelisted_ids']=sorted(allowed_execution)
            by_id=result.by_id()
            allowed_native={r.selected_id for r in validation.records if r.unavailable and allowed_failure(
                exceptions,task,r.selected_id.split('::',1)[0],'native_collection',r.message,tree=tree)}
            eligible=[]
            for record in validation.records:
                if record.native_proven_absent or record.selected_id in allowed_native:
                    continue
                gaps={t for t in record.runnable_ids if t not in by_id or by_id[t].status not in ADMITTED_STATUSES}
                if gaps and gaps <= allowed_execution:
                    continue
                eligible.append(record)
            allowed_modules={s.get('module') for s in (*validation.stage_health,*execution_stages) if s.get('allowed_exception')}
            if not any(s['stage']=='execution' for s in stages):
                stages.append({'stage':'execution','status':'NOT_STARTED' if validation.runnable_ids else 'EMPTY_INPUT',
                    'input_count':len(validation.runnable_ids),'output_count':0})
            stages.append({'stage':'admission','status':'COMPLETE' if any(r.get('admitted') for r in mapped.validation) else 'ZERO_OUTPUT' if eligible else 'ALL_PROVEN_INVALID' if validation.records and all(r.native_proven_absent for r in validation.records) else 'EMPTY_INPUT',
                'input_count':len(eligible),'output_count':sum(r.get('admitted',False) for r in mapped.validation),
                'original_input_count':len(validation.records),
                'proven_absent_count':sum(r.native_proven_absent for r in validation.records),
                'excluded_prelisted_modules':sorted(allowed_modules)})
            for name in ('native_collection','runner_startup'):
                if not any(s['stage']==name for s in stages):
                    stages.append({'stage':name,'status':'BLOCKED_UPSTREAM','input_count':0,'output_count':0})
            return replace(mapped,
                           duration_s=time.monotonic()-started, budget_s=timeout_s,
                           timed_out=result.timed_out or any(r.failure_status == "NOT_REACHED" for r in validation.records))

        audit.stage('patch_application', lambda: self.container.set_patched(patched))
        stages.append({'stage':'patch_application','status':'APPLIED' if patched else 'BASE_READY','input_count':1,'output_count':1})
        runner = self.runner or TestRunner("pytest", "default")
        validation = audit.stage('native_collection', lambda: validate_in_container(
            self.container, tests, runner, timeout_s=remaining(),tree='patched' if patched else 'base'))
        actual = validation.context.get('runner', runner.name)
        runner = replace(runner, name=actual, evidence=validation.context.get('runner_evidence', runner.evidence))
        validation = replace(validation, context={**validation.context,
            'instance_id': getattr(self.container, 'instance_id', ''),
            'tree': 'patched' if patched else 'base', 'runner': runner.name})
        stages.extend(validation.stage_health)
        if self.evidence_dir is not None:
            folder = self.evidence_dir / (("patched" if patched else "base") + "_validation_" + uuid.uuid4().hex)
            folder.mkdir(parents=True, exist_ok=False)
            path = folder / 'validation.json'
            raw = (json.dumps(validation.to_dict(), indent=2) + '\n').encode()
            path.write_bytes(raw)
            validation = replace(validation, evidence_files={'validation.json': str(path.resolve())},
                                 evidence_sha256={'validation.json': hashlib.sha256(raw).hexdigest()})
        if validation.errors:
            return finish(RunResult(infrastructure_errors=validation.errors,
                             requested_tests=tests,
                             validation_summary=validation.to_dict(),
                             evidence_files=validation.evidence_files,
                             evidence_sha256=validation.evidence_sha256,
                             note='ID validation unavailable'), validation)
        tests = validation.runnable_ids
        if not tests:
            return finish(RunResult(evidence_complete=True), validation)
        if isinstance(self.container,TaskContainer):
            from reliability.verifier.run_health import runner_startup
            startup = audit.stage('runner_startup',lambda:runner_startup(self.container,runner.name,timeout_s=remaining(60)))
            stages.append(startup)
            if startup['status'] != 'COMPLETE':
                return finish(RunResult(results=tuple(TestResult(t,TestStatus.RUNNER_UNAVAILABLE,
                    message=startup['message']) for t in tests),requested_tests=tests),validation)
        else:
            stages.append({'stage':'runner_startup','status':'STRUCTURED_EXECUTOR_NO_CONTAINER','input_count':0,'output_count':0})
        if time.monotonic() >= deadline:
            return finish(RunResult(results=tuple(TestResult(t, TestStatus.NOT_REACHED,
                elapsed_s=time.monotonic()-started, message="per-pass budget exhausted before execution")
                for t in tests), timed_out=True, evidence_complete=True), validation)
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
        driver_started = False
        try:
            # The ids go through stdin. Embedding them in `docker exec` argv is
            # what raised E2BIG once a short symbol selected a large tier-2 set.
            rc, _ = self.container.exec_input(
                f"cat > {_IDS_PATH}", "\n".join(native) + "\n", timeout_s=remaining(60))
            if rc:
                errors.append("selected-ID upload failed")
            rc, _ = self.container.exec_input(
                "cat > /tmp/verifier_module_ids.json",
                json.dumps({label: test.split('::', 1)[0] for label, test in zip(native, tests)}),
                timeout_s=remaining(60))
            if rc:
                errors.append("module-ID upload failed")
            rc, _ = self.container.exec_input(
                "cat > /tmp/verifier_driver.py", _BATCH_DRIVER, timeout_s=remaining(60))
            if rc:
                errors.append("capture-driver upload failed")
            # A failed driver must not expose stale logs from an earlier tree/pass.
            rc, _, _, clear_timeout = self._capture(
                "rm -f /tmp/verifier_out.txt /tmp/verifier_events.jsonl /tmp/verifier_pgid", remaining(30))
            if rc or clear_timeout:
                errors.append("could not clear previous capture")
            if errors:
                return finish(RunResult(
                    results=tuple(TestResult(t, TestStatus.NOT_RUN) for t in tests),
                    infrastructure_errors=tuple(errors), requested_tests=tuple(tests),
                    note="; ".join(errors)), validation)
            if time.monotonic() >= deadline:
                return finish(RunResult(
                    results=tuple(TestResult(t, TestStatus.NOT_REACHED, elapsed_s=time.monotonic()-started,
                        message="per-pass budget exhausted before execution") for t in tests),
                    timed_out=True, evidence_complete=True), validation)
            command += " " + str(remaining()) + " " + str(time.monotonic()-started)
            if runner.name == 'django' and runner.django_parallel_one:
                command += " parallel_one"
            driver_started = True
            rc, raw_stdout, raw_stderr, timed_out = audit.stage('execution',
                lambda: self._execute_once(command, remaining() + 2))
            if rc not in (0, None):
                errors.append(f"capture driver exit {rc}")
            rc, logged, _, log_timeout = self._capture("cat " + _OUT_LOG, 30)
            runner_log = logged if rc == 0 and not log_timeout else raw_stdout
            rc, event_bytes, _, event_timeout = self._capture("cat /tmp/verifier_events.jsonl", 30)
            if rc != 0 or event_timeout:
                event_bytes = b""
        except TimeoutError:
            timed_out = True
            if not driver_started:
                return finish(RunResult(results=tuple(TestResult(t, TestStatus.NOT_REACHED,
                    elapsed_s=time.monotonic()-started, message="per-pass budget exhausted during upload")
                    for t in tests), timed_out=True), validation)
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
            if any(event.get('event') not in ('start', 'end', 'complete', 'not_reached') for event in events):
                raise ValueError("unknown capture event")
        except (ValueError, TypeError):
            events = ()
            errors.append("malformed capture events")
        if driver_started and not timed_out and (not events or events[-1].get('event') != 'complete'):
            errors.append("capture driver did not complete")
        parsed = run_from_capture(
            runner, tests, runner_log=runner_log, raw_stderr=raw_stderr,
            raw_stdout=raw_stdout, events=events, timed_out=timed_out,
            infrastructure_errors=tuple(errors), evidence_files=files,
            evidence_sha256=digests, budget_s=timeout_s,
            base_progress_modules=self._base_progress_modules if patched else (),
        )
        stages.append({'stage':'execution','runner':runner.name,'status':'NOT_REACHED' if timed_out else 'COMPLETE',
            'input_count':len(tests),'output_count':sum(r.status in ADMITTED_STATUSES for r in parsed.results)})
        return finish(parsed, validation)

    def _partial_statuses(self, runner: TestRunner, tests) -> dict:
        """Read whatever a timed-out run managed to write to its log."""
        rc, logged = self.container.exec(("cat", _OUT_LOG), timeout_s=30)
        return _parse_output(runner, logged, tests) if rc == 0 else {}


def _active_test(kind, missing_ids, output):
    return active_test(kind, missing_ids, output)


def run_from_capture(
    runner: TestRunner, tests: tuple[str, ...], *, runner_log: bytes,
    raw_stderr: bytes = b"", raw_stdout: bytes = b"", events: tuple[dict, ...] = (),
    timed_out: bool = False, infrastructure_errors: tuple[str, ...] = (),
    evidence_files: dict[str, str] | None = None,
    evidence_sha256: dict[str, str] | None = None,
    budget_s: float | None = None,
    base_progress_modules: tuple[str, ...] | frozenset[str] = (),
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
                            (value['kind'] != 'case' or
                             (normalize_pytest_id(rid) if runner.name == 'pytest' else rid) not in admitted))}
    statuses = _parse_output(runner, output, tests, observed=observed)
    raw_results, mappings, unmatched = account_raw_output(runner, output, tests, observed=observed)
    complete = bool(events and events[-1].get("event") == "complete")
    timed_out |= any(e.get("timed_out") or e.get("event") == "not_reached" for e in events)
    reached_elapsed = {}
    # A verbose runner can name the interrupted test before its terminal word.
    # Preserve that positive start evidence as TIMEOUT; only the other pending
    # identities are NOT_REACHED. This is capture interpretation, not a rerun.
    for event in events:
        if event.get("event") != "end" or not event.get("timed_out"):
            continue
        start = next((e for e in events if e.get("event") == "start"
                      and e.get("batch") == event.get("batch")), {})
        begin, finish = start.get("offset", 0), event.get("offset", len(runner_log))
        text = runner_log[begin:finish].decode("utf-8", "replace")
        active = _active_test(runner.name, event.get("missing_ids", ()), text)
        elapsed = next((e.get("elapsed_s", 0.0) for e in events
                        if e.get("event") == "not_reached"
                        and e.get("module") == event.get("module")), budget_s or 0.0)
        if active:
            for tid in mapping_for(tests, runner.name)(active):
                statuses[tid] = TestStatus.TIMEOUT
                reached_elapsed[tid] = elapsed
    for event in events:
        if event.get("event") == "not_reached":
            mapper = mapping_for(tests, runner.name)
            for identity in event.get("ids", ()):
                for tid in mapper(identity):
                    if tid not in statuses:
                        statuses[tid] = TestStatus.NOT_REACHED
                        reached_elapsed[tid] = event.get("elapsed_s", 0.0)
    # A host watchdog can interrupt the driver before its final receipt. IDs
    # outside every started process are still provably not reached.
    if timed_out and events:
        attempted = {t for e in events if e.get("event") == "start" for t in e.get("ids", ())}
        mapper = mapping_for(tests, runner.name)
        attempted = {t for identity in attempted for t in mapper(identity)}
        for tid in tests:
            if tid not in attempted and tid not in statuses:
                statuses[tid] = TestStatus.NOT_REACHED
                reached_elapsed[tid] = budget_s or 0.0
    crashed_batches=set(); messages={}; unmapped_requested=set()
    for event in events:
        if event.get('event')!='end' or event.get('timed_out'):
            continue
        start=next((e for e in events if e.get('event')=='start' and e.get('batch')==event.get('batch')), {})
        text=runner_log[start.get('offset',0):event.get('offset',len(runner_log))].decode('utf-8','replace')
        missing=event.get('missing_ids',())
        _,_,batch_unmatched=account_raw_output(runner,text,tests)
        unmapped_cases=set(batch_unmatched) & {rid for rid,value in parse_capture(text,runner.name).items() if value['kind']=='case'}
        if unmapped_cases:
            for native in missing:
                unmapped_requested.update(mapping_for(tests,runner.name)(native))
        active=event.get('active_id') or _active_test(runner.name,missing,text)
        progress=bool(active or event.get('observed_ids') or event.get('per_test_output')
                      or any(value['kind']=='case' for value in parse_capture(text,runner.name).values()))
        if progress and missing:
            crashed_batches.add(event.get('batch'))
            active=active or missing[0]
            for native in missing:
                for tid in mapping_for(tests,runner.name)(native):
                    if tid not in statuses:
                        statuses[tid]=TestStatus.CRASH if native==active else TestStatus.NOT_REACHED
                        messages[tid]='process died after observed test progress' if native==active else 'not started after test process crash'
                        if native==active and not any(r.test_id==native and r.status is TestStatus.CRASH for r in raw_results):
                            raw_results += (TestResult(native,TestStatus.CRASH,message=messages[tid]),)
                            mappings[native]=mapping_for(tests,runner.name)(native)
    starts = {e.get("batch") for e in events if e.get("event") == "start"}
    ends = {e.get("batch") for e in events if e.get("event") == "end"}
    if not starts:
        complete = False
    if starts != ends:
        errors.append("unfinished runner batch")
    proven_failures=module_identity_failures(events)
    induced_batches={batch for e in proven_failures if e.get('module') in base_progress_modules
                     for batch in (e.get('batch'), e.get('parent'))}
    import_batches = sympy_import_batches(events) if runner.name == 'sympy' else {}
    for event in events:
        if event.get("event") == "end" and not event.get("split") and not event.get("timed_out") and event.get("batch") not in crashed_batches | induced_batches | import_batches.keys():
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
    import_events = [e for e in events if e.get('event') == 'end' and e.get('batch') in import_batches]
    for event in [*import_events, *(e for e in proven_failures if e not in import_events)]:
        for missing in event.get('missing_ids',()):
            induced = event.get('module') in base_progress_modules
            if induced and not any(r.test_id == missing for r in raw_results):
                selected = mapping_for(tests, runner.name)(missing)
                raw_results += (TestResult(missing, TestStatus.ERROR,
                    message='patched module silent after base module progress'),)
                mappings[missing] = selected
            for tid in mapping_for(tests,runner.name)(missing):
                if runner.name == 'sympy' and tid in statuses:
                    continue
                statuses[tid]=(TestStatus.ERROR if induced else TestStatus.COLLECTION_ERROR
                    if event.get('batch') in import_batches else TestStatus.NOT_RUN)
                messages[tid]=('patched module silent after base module progress' if induced else
                    'sympy_module_import: ' + import_batches[event['batch']] if event.get('batch') in import_batches else
                    'infrastructure: module_execution produced no test progress on first attempt and retry')
        if event.get('module') not in base_progress_modules and event.get('batch') not in import_batches:
            errors.append('module_execution identity failure: no test progress on first attempt and retry')
    if runner.name == 'sympy':
        unproven = [e for e in events if sympy_silent_nonzero(e) and not e.get('split')
                    and e.get('batch') not in import_batches and e.get('batch') not in induced_batches
                    and any(tid not in statuses
                            for native in e.get('missing_ids', ())
                            for tid in mapping_for(tests, runner.name)(native))]
        for event in unproven:
            start = next((e for e in events if e.get('event') == 'start'
                          and e.get('batch') == event.get('batch')), {})
            for native in event.get('missing_ids', start.get('ids', ())):
                for tid in mapping_for(tests, runner.name)(native):
                    if tid not in statuses:
                        statuses[tid] = TestStatus.NOT_RUN
                        messages[tid] = 'infrastructure: unproven SymPy module-import identity loss'
        if unproven or any(e.get('batch') not in import_batches and e.get('batch') not in induced_batches
                           for e in proven_failures):
            errors.append('SymPy module identity loss: no verified stderr traceback and healthy-runner proof')
    # A lone failed module attempt is not the required two-attempt proof.
    for event in events:
        if event.get('event')=='end' and event.get('load_failure') and event not in proven_failures:
            for missing in event.get('missing_ids',()):
                for tid in mapping_for(tests,runner.name)(missing):
                    if tid not in statuses:
                        statuses[tid]=TestStatus.NOT_REACHED
                        messages[tid]='module retry evidence unavailable'
    # Anything the runner did not report on is NOT_RUN, never an implicit pass.
    return RunResult(
        results=tuple(
            TestResult(t, statuses.get(t, TestStatus.TIMEOUT if timed_out else TestStatus.NOT_RUN),
                       elapsed_s=reached_elapsed.get(t, 0.0),
                       message=messages.get(t,"per-pass budget exhausted; no terminal outcome" if t in reached_elapsed else ""))
            for t in tests
        ),
        note="" if statuses else _no_results_note(output),
        timed_out=timed_out, budget_s=budget_s, raw_results=raw_results, raw_id_map=mappings,
        unmatched_ids=tuple(dict.fromkeys((*unmatched,*sorted(unmapped_requested)))), infrastructure_errors=tuple(errors),
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
    TestStatus.XPASS: 3, TestStatus.FAILED: 4, TestStatus.ERROR: 5, TestStatus.CRASH: 5.5, TestStatus.TIMEOUT: 6,
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
