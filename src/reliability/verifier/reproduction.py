"""V4, second half: run the frozen tests against the patched tree.

The suite was frozen and screened by `reproduction_freeze` before this module
saw a patch. Here the patch is applied to a fresh base-commit container, and
then every kept test's frozen bytes are written over whatever the patch left at
that path, their hash is checked on disk, and they are run. A patch that edits
or replaces a generated test therefore changes nothing that executes.

Each kept test runs `patched_runs` times. Only two results count, and each
must repeat on every run: a pass, or an AssertionError. Anything else drops the
test rather than counting it either way — runs that disagree (flaky), a timeout,
or a deterministic error that is not an assertion. An ImportError or an
AttributeError says the test cannot run on the patched tree, not that the bug
is still there. The signal:

- PASS           at least one test gave a stable result and every stable
                 result was a pass;
- FAIL           some test failed its assertion on every patched run: the
                 behaviour the issue asks for is still absent;
- NOT_AVAILABLE  nothing kept, nothing stable, or the layer itself broke.

FAIL does not REJECT: the full policy treats it as an unmet ACCEPT condition,
because a generated test is weaker evidence than the repository's own tests.
"""

from __future__ import annotations

import base64
import shlex
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reliability.verifier.container import TaskContainer
from reliability.verifier.decision import SignalOutcome
from reliability.verifier.patch import parse_patch
from reliability.verifier.record import SignalAbsence, SignalKind, SignalRecord
from reliability.verifier.reproduction_freeze import (
    RUNNER_PATH,
    FrozenSuite,
    ReproductionSetup,
    RunOutcome,
    RunResult,
    Sandbox,
    run_frozen,
)


@dataclass
class ContainerSandbox:
    """A `Sandbox` over a verifier container."""

    container: TaskContainer

    def write_file(self, path: str, data: bytes) -> None:
        parent = shlex.quote(str(Path(path).parent))
        rc, out = self.container.exec_input(
            f"mkdir -p {parent} && base64 -d > {shlex.quote(path)}",
            base64.b64encode(data).decode("ascii"))
        if rc != 0:
            raise OSError(f"could not write {path} in container: {out[:200]}")

    def sha256(self, path: str) -> str | None:
        rc, out = self.container.exec(("sha256sum", path), timeout_s=60)
        if rc != 0 or not out.split():
            return None
        return "sha256:" + out.split()[0]

    def run_test(self, path: str, timeout_s: int) -> tuple[int, str]:
        return self.container.exec(
            f"PYTHONPATH=/testbed timeout -k 5 {int(timeout_s)} "
            f"python {RUNNER_PATH} {shlex.quote(path)}",
            timeout_s=timeout_s + 30)

    def set_patched(self, patched: bool) -> None:
        self.container.set_patched(patched)


@contextmanager
def base_container_sandbox(instance_id: str) -> Iterator[ContainerSandbox]:
    """A base-commit container with no patch text at all."""
    with TaskContainer(instance_id=instance_id, patch_text="") as container:
        yield ContainerSandbox(container)


@dataclass(frozen=True, slots=True)
class PatchedTest:
    path: str
    sha256: str
    patch_touched_path: bool
    runs: tuple[RunResult, ...]
    verdict: str   # pass | fail | flaky | error | timeout | not_in_place

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path, "sha256": self.sha256,
            "patch_touched_path": self.patch_touched_path,
            "runs": [r.as_dict() for r in self.runs], "verdict": self.verdict,
        }


def patched_verdict(results: list[RunResult]) -> str:
    """`pass` and `fail` count; `flaky`, `error` and `timeout` drop the test."""
    outcomes = {r.outcome for r in results}
    if len(outcomes) > 1:
        return "flaky"
    return {
        RunOutcome.PASS: "pass",
        RunOutcome.ASSERTION_FAILURE: "fail",
        RunOutcome.ERROR: "error",
        RunOutcome.TIMEOUT: "timeout",
    }[next(iter(outcomes))]


def evaluate_frozen(
    suite: FrozenSuite, patch_text: str, sandbox: Sandbox, setup: ReproductionSetup,
) -> list[PatchedTest]:
    """Run each kept test on a tree the patch has already been applied to."""
    touched = _touched_paths(patch_text)
    results = []
    for test in suite.kept:
        runs, not_in_place = run_frozen(
            sandbox, test.path, suite.bytes_of(test),
            runs=setup.budget.patched_runs, timeout_s=setup.budget.per_run_timeout_s)
        results.append(PatchedTest(
            path=test.path, sha256=test.sha256,
            patch_touched_path=test.path in touched, runs=tuple(runs),
            verdict="not_in_place" if not_in_place else patched_verdict(runs)))
    return results


def signal_from_reproduction(
    suite: FrozenSuite, patched: list[PatchedTest], setup: ReproductionSetup,
    *, duration_s: float = 0.0,
) -> SignalRecord:
    findings = _findings(suite, setup, patched)
    if any(t.verdict == "not_in_place" for t in patched):
        return _absent(SignalAbsence.ERROR,
                       "frozen bytes could not be placed in the patched tree",
                       findings, duration_s)
    stable = [t for t in patched if t.verdict in ("pass", "fail")]
    if not stable:
        return _absent(
            SignalAbsence.NOTHING_TO_CHECK,
            f"none of {len(patched)} kept tests gave a stable result on the "
            f"patched tree ({', '.join(sorted({t.verdict for t in patched}))})",
            findings, duration_s)
    failed = [t.path for t in stable if t.verdict == "fail"]
    outcome = SignalOutcome.FAIL if failed else SignalOutcome.PASS
    detail = (f"{len(failed)}/{len(stable)} stable generated tests fail on the "
              f"patched tree: {', '.join(failed)}" if failed else
              f"{len(stable)}/{len(stable)} stable generated tests pass on the "
              f"patched tree")
    dropped = len(patched) - len(stable)
    if dropped:
        reasons = sorted({t.verdict for t in patched if t.verdict not in ("pass", "fail")})
        detail += f"; {dropped} dropped ({', '.join(reasons)})"
    return SignalRecord(kind=SignalKind.REPRODUCTION, outcome=outcome,
                        detail=detail, duration_s=duration_s, findings=findings)


def signal_before_patch(
    suite: FrozenSuite, setup: ReproductionSetup, *, duration_s: float = 0.0,
) -> SignalRecord | None:
    """The absence to record when the freeze left nothing to run, else None."""
    findings = _findings(suite, setup, [])
    if suite.error:
        return _absent(SignalAbsence.ERROR, suite.error, findings, duration_s)
    if not suite.tests:
        if suite.termination not in ("Submitted", "LimitsExceeded", "TimeExceeded"):
            return _absent(SignalAbsence.ERROR,
                           f"generator did not run: {suite.termination}",
                           findings, duration_s)
        return _absent(SignalAbsence.NOTHING_TO_CHECK,
                       f"generator wrote no test files ({suite.termination})",
                       findings, duration_s)
    if not suite.kept:
        reasons = sorted({t.drop_reason.value for t in suite.tests if t.drop_reason})
        return _absent(
            SignalAbsence.NOTHING_TO_CHECK,
            f"none of {len(suite.tests)} generated tests failed deterministically "
            f"on the base commit ({', '.join(reasons)}); no retry by design",
            findings, duration_s)
    return None


def not_run(absence: SignalAbsence, detail: str, setup: ReproductionSetup | None,
            ) -> SignalRecord:
    findings = {"setup": setup.identity()} if setup else {}
    return SignalRecord(kind=SignalKind.REPRODUCTION,
                        outcome=SignalOutcome.NOT_AVAILABLE, absence=absence,
                        detail=detail, findings=findings)


def _absent(absence, detail, findings, duration_s) -> SignalRecord:
    return SignalRecord(kind=SignalKind.REPRODUCTION,
                        outcome=SignalOutcome.NOT_AVAILABLE, absence=absence,
                        detail=detail, duration_s=duration_s, findings=findings)


def _findings(suite: FrozenSuite, setup: ReproductionSetup,
              patched: list[PatchedTest]) -> dict[str, Any]:
    return {
        "setup": setup.identity(),
        "suite_sha256": suite.suite_sha256,
        "generation": {
            "termination": suite.termination, "n_steps": suite.n_steps,
            "cost_usd": suite.cost_usd, "frozen_at": suite.frozen_at,
            "ignored_files": list(suite.ignored),
        },
        "frozen": [t.as_dict() for t in suite.tests],
        "patched": [t.as_dict() for t in patched],
    }


def _touched_paths(patch_text: str) -> set[str]:
    if not patch_text.strip():
        return set()
    try:
        patch = parse_patch(patch_text)
    except Exception:  # noqa: BLE001 - only used to annotate the record
        return set()
    return {p for f in patch.files for p in (f.old_path, f.path) if p}

