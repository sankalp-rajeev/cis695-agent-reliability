"""V4, first half: generate issue-derived tests, freeze them, screen them.

Everything here happens before any candidate patch exists, and nothing here can
receive one. The generator is given the issue text and the instance id (from
which the base-commit image is derived) and nothing else; tests are read out of
its container, hashed and written to the host, and only then run against a
fresh base-commit container. A test is kept only if every screening run fails
the same way: with an AssertionError, which is the one failure the generator was
asked to produce. Anything else — a pass, an import error, a timeout, or two runs
that disagree — is dropped, and dropped tests never become evidence.

`tests/unit/test_reproduction.py` asserts the input boundary structurally: the
parameter names of every entry point and the fields of every object passed in
are closed sets, so adding a patch, an oracle field, or a trajectory to any of
them fails the suite.

The second half, running the frozen bytes against a patched tree, is
`reliability.verifier.reproduction`.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import shlex
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

import yaml

logger = logging.getLogger(__name__)

#: Where the generator writes, and the only paths read back out.
REPRO_DIR = "v4_repro"


def repro_path(index: int) -> str:
    return f"{REPRO_DIR}/test_repro_{index}.py"


class ReproductionConfigError(ValueError):
    """Raised when the V4 budget or generator pin is incomplete or unverified."""


# --- configuration ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ReproductionBudget:
    """The fixed generation and execution budget.

    Every value is read once from `configs/verifier/full.yaml` and never adjusted
    per instance. `retries` is recorded but must be 0: an instance whose tests
    all fail the screen gets NOT_AVAILABLE, not a second attempt, because a
    retry conditioned on the screen result would make the budget adaptive.
    """

    max_tests: int
    retries: int
    generator_max_steps: int
    generator_max_cost_usd: float
    generator_timeout_s: int
    per_command_timeout_s: int
    screen_runs: int
    patched_runs: int
    per_run_timeout_s: int
    max_test_bytes: int

    @classmethod
    def from_config(cls, cfg: dict[str, Any]) -> ReproductionBudget:
        names = {f for f in cls.__dataclass_fields__}
        missing = sorted(names - set(cfg))
        if missing:
            raise ReproductionConfigError(f"reproduction budget missing {missing}")
        budget = cls(**{name: cfg[name] for name in names})
        if budget.retries != 0:
            raise ReproductionConfigError(
                "reproduction.retries must be 0; the budget is one generation "
                "attempt per instance")
        if budget.max_tests < 1 or budget.screen_runs < 2 or budget.patched_runs < 2:
            raise ReproductionConfigError(
                "need max_tests >= 1 and at least two screen and patched runs; "
                "one run cannot show a result is deterministic")
        return budget

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GeneratorModel:
    """The generator's pin, read from `configs/model/generator.yaml`.

    Refused unless `scripts/verify_model.py` has recorded a successful live
    tool-calling request for exactly this model id.
    """

    config_path: str
    model_id: str
    served_model: str
    system_fingerprint: str
    verified_on: str
    temperature: float
    top_p: float
    max_output_tokens: int
    drop_params: bool

    @classmethod
    def load(cls, path: Path, *, repo_root: Path | None = None) -> GeneratorModel:
        cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if cfg.get("role") != "generator":
            raise ReproductionConfigError(f"{path} is not role: generator")
        verified = cfg.get("verified") or {}
        if verified.get("status") != "ok":
            raise ReproductionConfigError(
                f"{path} is not verified; run scripts/verify_model.py "
                f"--config {path} --update")
        if verified.get("model_id") != cfg.get("model_id"):
            raise ReproductionConfigError(
                f"{path} was verified for {verified.get('model_id')}, "
                f"but pins {cfg.get('model_id')}")
        shown = Path(path)
        if repo_root is not None and shown.is_absolute():
            shown = shown.relative_to(repo_root)
        return cls(
            config_path=str(shown),
            model_id=cfg["model_id"],
            served_model=str(verified.get("served_model", "unreported")),
            system_fingerprint=str(verified.get("system_fingerprint", "unreported")),
            verified_on=str(verified["checked"]),
            temperature=float(cfg.get("temperature", 0.0)),
            top_p=float(cfg.get("top_p", 1.0)),
            max_output_tokens=int(cfg.get("max_output_tokens", 8192)),
            drop_params=bool((cfg.get("model_kwargs") or {}).get("drop_params", True)),
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReproductionSetup:
    """Everything V4 is configured with. Recorded whole in every record."""

    model: GeneratorModel
    budget: ReproductionBudget
    prompt_path: str
    prompt_sha256: str

    @classmethod
    def load(cls, *, verifier_config: Path, repo_root: Path) -> ReproductionSetup:
        cfg = yaml.safe_load(Path(verifier_config).read_text(encoding="utf-8"))
        section = cfg.get("reproduction") or {}
        budget = ReproductionBudget.from_config(section.get("budget") or {})
        prompt = repo_root / section["generator_prompt"]
        return cls(
            model=GeneratorModel.load(
                repo_root / section["generator_model"], repo_root=repo_root),
            budget=budget,
            prompt_path=section["generator_prompt"],
            prompt_sha256=_sha256(prompt.read_bytes()),
        )

    def identity(self) -> dict[str, Any]:
        return {
            "generator": self.model.as_dict(),
            "budget": self.budget.as_dict(),
            "prompt_path": self.prompt_path,
            "prompt_sha256": self.prompt_sha256,
            # How outcomes are read is part of what produced the result.
            "runner_sha256": RUNNER_SHA256,
            "assertion_returncode": ASSERTION_RETURNCODE,
        }


# --- generation ------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GenerationOutcome:
    """What the generator left behind. Files are raw bytes as read out."""

    files: dict[str, bytes]
    termination: str
    n_steps: int = 0
    cost_usd: float = 0.0
    ignored: tuple[str, ...] = ()
    trajectory: tuple[dict[str, Any], ...] = ()


class ReproGenerator(Protocol):
    def generate(self, issue_text: str, instance_id: str) -> GenerationOutcome: ...


@dataclass
class MiniSweGenerator:
    """mini-SWE-agent in a base-commit container with --network none."""

    setup: ReproductionSetup
    repo_root: Path

    def generate(self, issue_text: str, instance_id: str) -> GenerationOutcome:
        from minisweagent.agents.default import DefaultAgent
        from minisweagent.models import get_model
        from minisweagent.run.benchmarks.swebench import get_sb_environment

        from reliability.agent.isolation import (
            IsolationError,
            assert_network_none,
            prepare_environment,
        )

        budget, pin = self.setup.budget, self.setup.model
        config = yaml.safe_load(
            (self.repo_root / self.setup.prompt_path).read_text(encoding="utf-8"))
        config["agent"]["step_limit"] = budget.generator_max_steps
        config["agent"]["cost_limit"] = budget.generator_max_cost_usd
        config["environment"]["timeout"] = budget.per_command_timeout_s
        prepare_environment(config)

        model_config = {
            **config.get("model", {}),
            "model_name": pin.model_id,
            "model_kwargs": {
                **(config.get("model", {}).get("model_kwargs") or {}),
                "drop_params": pin.drop_params,
                "temperature": pin.temperature,
                "top_p": pin.top_p,
                "max_tokens": pin.max_output_tokens,
            },
            "cost_tracking": "ignore_errors",
        }
        model = get_model(pin.model_id, model_config)

        env = get_sb_environment(config, {"instance_id": instance_id})
        try:
            if not env.container_id:
                raise IsolationError("generator container did not start")
            assert_network_none(env.container_id)
            agent = DefaultAgent(
                model, env, **config["agent"],
                wall_time_limit_seconds=budget.generator_timeout_s)
            try:
                termination = agent.run(issue_text).get("exit_status", "") or "unknown"
            except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
                termination = f"{type(exc).__name__}: {exc}"[:300]
            files, ignored = _read_out(env, budget)
            return GenerationOutcome(
                files=files,
                termination=termination,
                n_steps=int(getattr(agent, "n_calls", 0) or 0),
                cost_usd=float(getattr(agent, "cost", 0.0) or 0.0),
                ignored=ignored,
                trajectory=tuple(
                    json.loads(json.dumps(m, default=str)) for m in agent.messages),
            )
        finally:
            try:
                env.cleanup()
            except Exception as exc:  # noqa: BLE001
                logger.warning("generator cleanup failed for %s: %s", instance_id, exc)


def _read_out(env, budget: ReproductionBudget) -> tuple[dict[str, bytes], tuple[str, ...]]:
    """Copy the permitted test files out of the generator's container."""
    wanted = {repro_path(i) for i in range(1, budget.max_tests + 1)}
    listing = _env_run(env, f"find {REPRO_DIR} -type f 2>/dev/null | sort")
    present = [p.strip().removeprefix("./") for p in listing.splitlines() if p.strip()]
    ignored = tuple(p for p in present if p not in wanted)

    files: dict[str, bytes] = {}
    for path in sorted(wanted & set(present)):
        size = _env_run(env, f"stat -c %s {shlex.quote(path)}").strip()
        if not size.isdigit() or int(size) > budget.max_test_bytes:
            ignored += (f"{path} (size {size or 'unknown'})",)
            continue
        encoded = _env_run(env, f"base64 -w0 {shlex.quote(path)}").strip()
        files[path] = base64.b64decode(encoded)
    return files, ignored


def _env_run(env, command: str) -> str:
    try:
        return env.execute({"command": command}).get("output", "") or ""
    except Exception as exc:  # noqa: BLE001 - a file that cannot be read is not kept
        logger.warning("read-out command failed: %s: %s", command, exc)
        return ""


# --- execution -------------------------------------------------------------


class RunOutcome(str, Enum):
    PASS = "pass"
    ASSERTION_FAILURE = "assertion_failure"
    ERROR = "error"
    TIMEOUT = "timeout"


class Sandbox(Protocol):
    """A working tree the frozen tests can be written into and run in."""

    def write_file(self, path: str, data: bytes) -> None: ...
    def sha256(self, path: str) -> str | None: ...
    def run_test(self, path: str, timeout_s: int) -> tuple[int, str]: ...


#: `timeout` exits 124 on expiry. The container runner wraps each run with it
#: so a hung test is killed inside the container, not just abandoned.
TIMEOUT_RETURNCODE = 124

#: Exit code the runner uses for an uncaught AssertionError, and only for that.
#: An earlier version read the last line of the output for "AssertionError",
#: which dropped every test whose message ran over several lines (a numpy array
#: diff, a docstring) — six real tests in pilot_14, two instances.
ASSERTION_RETURNCODE = 97

#: Where the runner is installed. Outside the repository, so no patch can
#: reach it, and written after the patch is applied.
RUNNER_PATH = "/opt/v4/run_test.py"

#: Runs a script as `__main__`, the way `python script.py` would, and turns an
#: uncaught AssertionError into ASSERTION_RETURNCODE. Every other exception
#: exits 1 as it would unwrapped, and SystemExit keeps the script's own code.
#: Plain Python 3.6 syntax: it runs inside every SWE-bench image.
RUNNER_SOURCE = """\
import os
import runpy
import sys
import traceback

script = sys.argv[1]
sys.argv = [script]
sys.path.insert(0, os.path.dirname(os.path.abspath(script)))
try:
    runpy.run_path(script, run_name="__main__")
except AssertionError:
    traceback.print_exc()
    sys.stderr.flush()
    sys.exit(__RC__)
""".replace("__RC__", str(ASSERTION_RETURNCODE))
RUNNER_SHA256 = "sha256:" + hashlib.sha256(RUNNER_SOURCE.encode("utf-8")).hexdigest()


def classify(returncode: int) -> RunOutcome:
    """Only the exit code decides. Nothing in the output can make a failure an assertion."""
    if returncode == 0:
        return RunOutcome.PASS
    if returncode == TIMEOUT_RETURNCODE:
        return RunOutcome.TIMEOUT
    if returncode == ASSERTION_RETURNCODE:
        return RunOutcome.ASSERTION_FAILURE
    return RunOutcome.ERROR


@dataclass(frozen=True, slots=True)
class RunResult:
    outcome: RunOutcome
    returncode: int
    tail: str

    def as_dict(self) -> dict[str, Any]:
        return {"outcome": self.outcome.value, "returncode": self.returncode,
                "tail": self.tail}


def run_frozen(
    sandbox: Sandbox, path: str, data: bytes, *, runs: int, timeout_s: int,
) -> tuple[list[RunResult], str | None]:
    """Write the frozen bytes, prove they are in place, then run them.

    Returns the runs and, if the bytes on disk did not hash to the frozen
    digest, the reason no run happened. The write happens immediately before
    the runs, so whatever the working tree held at `path` — including a
    version the patch wrote — is replaced. The runner is installed and checked
    the same way, and `sandbox.run_test` must execute `path` through it.
    """
    runner = RUNNER_SOURCE.encode("utf-8")
    sandbox.write_file(RUNNER_PATH, runner)
    if (on_disk := sandbox.sha256(RUNNER_PATH)) != RUNNER_SHA256:
        return [], f"runner at {RUNNER_PATH} hashes to {on_disk}, not {RUNNER_SHA256}"
    sandbox.write_file(path, data)
    on_disk = sandbox.sha256(path)
    if on_disk != _sha256(data):
        return [], f"bytes at {path} hash to {on_disk}, not the frozen {_sha256(data)}"
    results = []
    for _ in range(runs):
        try:
            rc, out = sandbox.run_test(path, timeout_s)
        except TimeoutError:
            rc, out = TIMEOUT_RETURNCODE, "host timeout"
        results.append(RunResult(classify(rc), rc, out[-600:]))
    return results, None


# --- freezing and screening ------------------------------------------------


class DropReason(str, Enum):
    PASSES_ON_BASE = "passes_on_base"
    NOT_AN_ASSERTION = "fails_without_assertion"
    NONDETERMINISTIC = "nondeterministic"
    TIMEOUT = "timeout"
    NOT_IN_PLACE = "frozen_bytes_not_in_place"


@dataclass(frozen=True, slots=True)
class FrozenTest:
    path: str
    sha256: str
    size_bytes: int
    base_runs: tuple[RunResult, ...]
    kept: bool
    drop_reason: DropReason | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path, "sha256": self.sha256, "size_bytes": self.size_bytes,
            "base_runs": [r.as_dict() for r in self.base_runs],
            "kept": self.kept,
            "drop_reason": self.drop_reason.value if self.drop_reason else None,
        }


def screen_verdict(results: list[RunResult]) -> DropReason | None:
    """None if the test is kept: every base run was an AssertionError."""
    outcomes = {r.outcome for r in results}
    if len(outcomes) > 1:
        return DropReason.NONDETERMINISTIC
    only = next(iter(outcomes))
    return {
        RunOutcome.ASSERTION_FAILURE: None,
        RunOutcome.PASS: DropReason.PASSES_ON_BASE,
        RunOutcome.ERROR: DropReason.NOT_AN_ASSERTION,
        RunOutcome.TIMEOUT: DropReason.TIMEOUT,
    }[only]


@dataclass(frozen=True, slots=True)
class FrozenSuite:
    """The frozen, screened tests for one instance. Read-only once written."""

    instance_id: str
    directory: Path
    identity: dict[str, Any]
    termination: str
    n_steps: int
    cost_usd: float
    tests: tuple[FrozenTest, ...]
    ignored: tuple[str, ...] = ()
    error: str = ""
    frozen_at: str = field(default="")

    @property
    def kept(self) -> tuple[FrozenTest, ...]:
        return tuple(t for t in self.tests if t.kept)

    @property
    def suite_sha256(self) -> str:
        joined = "\n".join(f"{t.path} {t.sha256}" for t in self.kept)
        return _sha256(joined.encode("utf-8"))

    def bytes_of(self, test: FrozenTest) -> bytes:
        data = (self.directory / "tests" / Path(test.path).name).read_bytes()
        if _sha256(data) != test.sha256:
            raise ReproductionConfigError(
                f"frozen copy of {test.path} changed on the host since freezing")
        return data

    def as_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "identity": self.identity,
            "termination": self.termination,
            "n_steps": self.n_steps,
            "cost_usd": self.cost_usd,
            "tests": [t.as_dict() for t in self.tests],
            "ignored": list(self.ignored),
            "error": self.error,
            "frozen_at": self.frozen_at,
            "suite_sha256": self.suite_sha256,
        }

    @classmethod
    def read(cls, directory: Path) -> FrozenSuite:
        data = json.loads((directory / MANIFEST).read_text(encoding="utf-8"))
        tests = tuple(
            FrozenTest(
                path=t["path"], sha256=t["sha256"], size_bytes=t["size_bytes"],
                base_runs=tuple(
                    RunResult(RunOutcome(r["outcome"]), r["returncode"], r["tail"])
                    for r in t["base_runs"]),
                kept=t["kept"],
                drop_reason=DropReason(t["drop_reason"]) if t["drop_reason"] else None,
            )
            for t in data["tests"]
        )
        return cls(
            instance_id=data["instance_id"], directory=directory,
            identity=data["identity"], termination=data["termination"],
            n_steps=data["n_steps"], cost_usd=data["cost_usd"], tests=tests,
            ignored=tuple(data["ignored"]), error=data["error"],
            frozen_at=data["frozen_at"],
        )


MANIFEST = "frozen.json"

#: Opens a base-commit sandbox for one instance. Takes no patch: there is none yet.
BaseSandboxFactory = Callable[[str], AbstractContextManager[Sandbox]]


def freeze_tests(
    issue_text: str,
    instance_id: str,
    *,
    setup: ReproductionSetup,
    cache_dir: Path,
    generator: ReproGenerator,
    base_sandbox: BaseSandboxFactory,
) -> FrozenSuite:
    """Generate, freeze and screen once per instance; later calls read the freeze.

    A cached freeze made under a different setup is refused rather than reused,
    so a record can never attribute tests to a generator that did not write them.
    """
    directory = Path(cache_dir) / instance_id
    if (directory / MANIFEST).is_file():
        suite = FrozenSuite.read(directory)
        if suite.identity != setup.identity():
            raise ReproductionConfigError(
                f"{directory} was frozen under a different V4 setup; "
                "use a new experiment_id rather than mixing generators")
        return suite

    outcome = generator.generate(issue_text, instance_id)

    tests_dir = directory / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    frozen: list[tuple[str, bytes]] = []
    for path in sorted(outcome.files):
        data = outcome.files[path]
        (tests_dir / Path(path).name).write_bytes(data)
        frozen.append((path, data))
    with (directory / "generation_trajectory.jsonl").open("w", encoding="utf-8") as fh:
        for message in outcome.trajectory:
            fh.write(json.dumps(message) + "\n")

    screened: list[FrozenTest] = []
    error = ""
    if frozen:
        try:
            with base_sandbox(instance_id) as sandbox:
                for path, data in frozen:
                    results, not_in_place = run_frozen(
                        sandbox, path, data,
                        runs=setup.budget.screen_runs,
                        timeout_s=setup.budget.per_run_timeout_s)
                    reason = (DropReason.NOT_IN_PLACE if not_in_place
                              else screen_verdict(results))
                    screened.append(FrozenTest(
                        path=path, sha256=_sha256(data), size_bytes=len(data),
                        base_runs=tuple(results), kept=reason is None,
                        drop_reason=reason))
        except Exception as exc:  # noqa: BLE001 - a broken screen keeps nothing
            error = f"base screen failed: {type(exc).__name__}: {exc}"[:400]
            screened = [
                FrozenTest(path=p, sha256=_sha256(d), size_bytes=len(d),
                           base_runs=(), kept=False,
                           drop_reason=DropReason.NOT_IN_PLACE)
                for p, d in frozen
            ]

    suite = FrozenSuite(
        instance_id=instance_id, directory=directory, identity=setup.identity(),
        termination=outcome.termination, n_steps=outcome.n_steps,
        cost_usd=outcome.cost_usd, tests=tuple(screened), ignored=outcome.ignored,
        error=error, frozen_at=datetime.now(tz=UTC).isoformat(),
    )
    (directory / MANIFEST).write_text(
        json.dumps(suite.as_dict(), indent=2), encoding="utf-8")
    return suite


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()
