"""Verifier V2: baseline pass and outcome classification (Phase 5.2).

Implements `docs/VERIFIER_POLICY.md` §3.2, §4, and §4.1.

**The baseline pass is the whole point of this module.** Selected tests run twice:
once on the unpatched base commit, once on the patched tree. Only a test that
*passed on base and failed on patch* is a regression. Repositories carry
pre-existing failures — environment-dependent tests, skips that resolve
differently, tests simply broken at that commit — and without a baseline every
one of them would be blamed on the candidate patch. That would inflate the
rejection rate with noise and make the verifier look far more discriminating
than it is, which is precisely the error the study is trying to measure rather
than commit.

The baseline is cached per instance. The base commit never changes, so it is
computed once and reused across verifier configurations and ablations — which
also makes ablations comparable, since they then differ only in the patched pass.

**Unexecuted tests are never passes.** `NOT_RUN` and `TIMEOUT` are outcomes in
their own right. A verifier that treated work it did not do as evidence of
correctness would accept patches on the strength of nothing, and the regression
signal requires at least one test to have actually executed before it can say
anything at all.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Protocol

from reliability.verifier.selection import Selection


class TestStatus(str, Enum):
    """Raw result of running one test once."""

    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"        # collection or import failure, not an assertion
    SKIPPED = "skipped"
    XFAIL = "xfail"
    XPASS = "xpass"
    TIMEOUT = "timeout"
    NOT_RUN = "not_run"
    INVALID_ID = "invalid_id"
    COLLECTION_ERROR = "collection_error"
    RUNNER_UNAVAILABLE = "runner_unavailable"


class Outcome(str, Enum):
    """Classification after comparing base and patched runs (policy §4)."""

    PASS = "PASS"                            # passed on base and on patch
    REGRESSION = "REGRESSION"                # passed on base, failed on patch
    PRE_EXISTING_FAIL = "PRE_EXISTING_FAIL"  # failed on base; excluded from signal
    NEWLY_PASSING = "NEWLY_PASSING"          # failed on base, passes on patch
    FLAKY = "FLAKY"                          # regression that vanished on re-run
    REGRESSION_ERROR = "REGRESSION_ERROR"    # base PASS, patched ERROR
    XFAIL = "XFAIL"
    XPASS = "XPASS"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    NOT_RUN = "NOT_RUN"
    INVALID_ID = "INVALID_ID"
    COLLECTION_ERROR = "COLLECTION_ERROR"
    RUNNER_UNAVAILABLE = "RUNNER_UNAVAILABLE"

    @property
    def counts_as_regression(self) -> bool:
        return self is Outcome.REGRESSION

    @property
    def executed(self) -> bool:
        """Whether this outcome reflects a test that actually ran to completion."""
        return self not in (Outcome.NOT_RUN, Outcome.TIMEOUT, Outcome.INVALID_ID,
                            Outcome.COLLECTION_ERROR, Outcome.RUNNER_UNAVAILABLE)


class Signal(str, Enum):
    """The regression verdict for an instance (policy §4, §5)."""

    PASS = "PASS"
    FAIL = "FAIL"
    REGRESSION_ERROR = "REGRESSION_ERROR"    # reported separately from assertion FAIL
    NOT_AVAILABLE = "NOT_AVAILABLE"            # nothing ran; can never ACCEPT
    BASELINE_UNRELIABLE = "BASELINE_UNRELIABLE"  # §5.5
    INCOMPLETE = "INCOMPLETE"                 # would-be PASS without complete evidence


#: Policy §5.5 — above this share of baseline failures the environment is
#: suspect rather than the repository.
BASELINE_FAILURE_THRESHOLD = 0.5

# Parsed baseline caches must preserve the same outcome model as patched results.
_BASELINE_PARSER_REVISION = "native-capture-v4-collection-guard"


@dataclass(frozen=True, slots=True)
class TestResult:
    test_id: str
    status: TestStatus
    duration_s: float = 0.0
    message: str = ""


@dataclass(frozen=True, slots=True)
class RunResult:
    """One pass over the selected tests."""

    results: tuple[TestResult, ...] = ()
    timed_out: bool = False
    duration_s: float = 0.0
    #: Why nothing ran, when the runner reported no results at all.
    note: str = ""
    # Legacy selected-ID results above remain the compatibility scoring input.
    # Concrete raw IDs below are retained even when the legacy parser ignores them.
    raw_results: tuple[TestResult, ...] = ()
    raw_id_map: dict[str, tuple[str, ...]] = field(default_factory=dict)
    unmatched_ids: tuple[str, ...] = ()
    infrastructure_errors: tuple[str, ...] = ()
    evidence_complete: bool = False
    raw_stdout_b64: str = ""
    raw_stderr_b64: str = ""
    runner_log_b64: str = ""
    events: tuple[dict, ...] = ()
    evidence_files: dict[str, str] = field(default_factory=dict)
    evidence_sha256: dict[str, str] = field(default_factory=dict)
    requested_tests: tuple[str, ...] = ()
    validation: tuple[dict, ...] = ()
    execution_results: tuple[TestResult, ...] = ()
    execution_id_map: dict[str, tuple[str, ...]] = field(default_factory=dict)
    raw_execution_map: dict[str, str] = field(default_factory=dict)
    validation_summary: dict = field(default_factory=dict)

    def by_id(self) -> dict[str, TestResult]:
        return {r.test_id: r for r in self.results}


class TestExecutor(Protocol):
    """Runs tests in the task container.

    An interface so the classification logic is gated against fixtures rather
    than requiring Docker in the unit suite — the same pattern as the agent
    backend in Phase 3.
    """

    def run(
        self, tests: tuple[str, ...], *, patched: bool, timeout_s: int
    ) -> RunResult: ...


@dataclass(frozen=True, slots=True)
class RegressionConfig:
    per_pass_timeout_s: int = 300     # policy §3.4: five minutes per pass
    per_instance_timeout_s: int = 600  # ten minutes including baseline
    rerun_flaky: bool = True           # policy §4.1
    baseline_cache_dir: Path | None = None
    skip_compatible: bool = True       # Policy C; False selects Policy S
    invalid_as_missing: bool = False   # required sensitivity report


@dataclass(frozen=True, slots=True)
class RegressionReport:
    instance_id: str
    signal: Signal
    outcomes: dict[str, Outcome] = field(default_factory=dict)
    selection: Selection | None = None
    baseline_from_cache: bool = False
    n_executed: int = 0
    duration_s: float = 0.0
    notes: tuple[str, ...] = ()
    original_signal: Signal | None = None
    completeness: str = "UNVERIFIABLE"
    incompleteness: tuple[str, ...] = ()
    baseline: RunResult | None = None
    patched: RunResult | None = None
    confirmations: tuple[RunResult, ...] = ()

    @property
    def regressions(self) -> tuple[str, ...]:
        return tuple(sorted(t for t, o in self.outcomes.items() if o.counts_as_regression))

    @property
    def n_regressions(self) -> int:
        return len(self.regressions)

    @property
    def regression_errors(self) -> tuple[str, ...]:
        return tuple(sorted(t for t, o in self.outcomes.items()
                            if o is Outcome.REGRESSION_ERROR))

    def count(self, outcome: Outcome) -> int:
        return sum(1 for o in self.outcomes.values() if o is outcome)

    @property
    def summary(self) -> dict[str, int]:
        return {o.value: self.count(o) for o in Outcome if self.count(o)}


def _cache_path(config: RegressionConfig, instance_id: str) -> Path | None:
    if config.baseline_cache_dir is None:
        return None
    return config.baseline_cache_dir / f"{instance_id}.baseline.json"


def load_cached_baseline(config: RegressionConfig, instance_id: str) -> RunResult | None:
    path = _cache_path(config, instance_id)
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("parser_revision") != _BASELINE_PARSER_REVISION:
        return None
    return run_from_dict(payload)


def run_to_dict(run: RunResult, *, inline_raw: bool = True) -> dict:
    payload = asdict(run)
    if not inline_raw and run.evidence_files:
        for key in ("raw_stdout_b64", "raw_stderr_b64", "runner_log_b64"):
            payload.pop(key, None)
    return payload


def run_from_dict(payload: dict) -> RunResult:
    fields = {key: payload[key] for key in RunResult.__dataclass_fields__ if key in payload}
    for key in ("results", "raw_results", "execution_results"):
        fields[key] = tuple(TestResult(r["test_id"], TestStatus(r["status"]),
                                      r.get("duration_s", 0.0), r.get("message", ""))
                            for r in fields.get(key, ()))
    for key in ("unmatched_ids", "infrastructure_errors", "events", "requested_tests", "validation"):
        fields[key] = tuple(fields.get(key, ()))
    fields["raw_id_map"] = {k: tuple(v) for k, v in fields.get("raw_id_map", {}).items()}
    fields["execution_id_map"] = {k: tuple(v) for k, v in fields.get("execution_id_map", {}).items()}
    return RunResult(**fields)


def completeness_of(tests: tuple[str, ...], base: RunResult | None,
                    patched: RunResult | None, *,
                    skip_compatible: bool = True,
                    invalid_as_missing: bool = False) -> tuple[str, tuple[str, ...]]:
    """Separate known execution gaps from missing historical capture evidence."""
    gaps, unknown = [], []
    excluded = {r.test_id for run in (base, patched) if run is not None
                for r in run.results if r.status is TestStatus.INVALID_ID and not invalid_as_missing}
    healthy = {TestStatus.PASSED, TestStatus.XFAIL, TestStatus.XPASS}
    if skip_compatible:
        healthy.add(TestStatus.SKIPPED)
    for label, run in (("base", base), ("patched", patched)):
        if run is None:
            unknown.append(f"{label}: paired evidence unavailable")
            continue
        by_id = run.by_id()
        mapped_raw: dict[str, list[TestResult]] = {}
        for result in run.raw_results:
            mapped = run.raw_id_map.get(result.test_id, ())
            if len(mapped) == 1 or (run.validation and mapped):
                for selected in mapped:
                    mapped_raw.setdefault(selected, []).append(result)
        expected_by_selected = {}
        for identity, owners in run.execution_id_map.items():
            for owner in owners:
                expected_by_selected.setdefault(owner, []).append(identity)
        actual = {r.test_id: r for r in run.execution_results}
        if len(by_id) != len(run.results):
            gaps.append(f"{label}: duplicate selected IDs")
        for tid in tests:
            result = by_id.get(tid)
            if tid in excluded:
                continue
            expected = expected_by_selected.get(tid, ())
            missing_expansion = any(t not in actual or actual[t].status in
                                    (TestStatus.NOT_RUN, TestStatus.TIMEOUT) for t in expected)
            if missing_expansion:
                gaps.append(f"{label}: {tid}: expanded instance not admitted")
            # Lossless accounting can establish a healthy selected parameter
            # family even when the unchanged legacy parser admitted only exact
            # IDs. Do not invent a pass or silently absorb an unscored failure.
            cases = mapped_raw.get(tid, ())
            recovered = (cases and all(r.status in healthy for r in cases))
            if (result is None or result.status is TestStatus.NOT_RUN) and recovered and not missing_expansion:
                continue
            if (result is None or result.status in (TestStatus.NOT_RUN, TestStatus.TIMEOUT,
                                                    TestStatus.ERROR, TestStatus.COLLECTION_ERROR,
                                                    TestStatus.RUNNER_UNAVAILABLE, TestStatus.INVALID_ID)
                    or (not skip_compatible and result.status is TestStatus.SKIPPED)):
                gaps.append(f"{label}: {tid}: {result.status.value if result else 'missing'}")
        if run.timed_out:
            gaps.append(f"{label}: pass timed out (allowed threshold 0%)")
        gaps.extend(f"{label}: infrastructure: {s}" for s in run.infrastructure_errors)
        gaps.extend(f"{label}: unmatched raw ID: {s}" for s in run.unmatched_ids)
        gaps.extend(f"{label}: ambiguous raw ID: {tid}" for tid, ids in run.raw_id_map.items()
                    if len(ids) != 1 and not (run.validation and ids))
        gaps.extend(f"{label}: raw ERROR: {r.test_id}" for r in run.raw_results
                    if r.status is TestStatus.ERROR
                    and not (set(run.raw_id_map.get(r.test_id, ())) <= excluded
                             and run.raw_id_map.get(r.test_id)))
        for result in run.raw_results:
            ids = run.raw_id_map.get(result.test_id, ())
            if ids and set(ids) <= excluded:
                continue
            if not skip_compatible and result.status is TestStatus.SKIPPED:
                gaps.append(f"{label}: raw SKIPPED: {result.test_id}")
            if not ids:
                gaps.append(f"{label}: unaccounted raw ID: {result.test_id}")
            if len(ids) == 1 and result.status in (TestStatus.FAILED, TestStatus.ERROR):
                selected = by_id.get(ids[0])
                if selected and selected.status in healthy:
                    gaps.append(f"{label}: raw/selected status conflict: {result.test_id}")
        if not run.evidence_complete:
            unknown.append(f"{label}: complete raw/runner capture unavailable")
    def comparable_ids(run):
        return {r.test_id for r in run.raw_results
                if not excluded or not set(run.raw_id_map.get(r.test_id, ())) <= excluded}
    if (base and patched and base.raw_results and patched.raw_results
            and comparable_ids(base) != comparable_ids(patched)):
        gaps.append("concrete raw test IDs differ between base and patched")
    state = "INCOMPLETE_CONFIRMED" if gaps else "UNVERIFIABLE" if unknown else "COMPLETE"
    return state, tuple(gaps + unknown)


def integrity_verdict(original: str, completeness: str) -> str:
    """The single permitted migration. Never manufacture historical outcomes."""
    return "INCOMPLETE" if original == "PASS" and completeness != "COMPLETE" else original


def save_baseline(config: RegressionConfig, instance_id: str, run: RunResult) -> None:
    """Persist a baseline. Per-instance file: no shared mutable state.

    Written to a temporary name and moved into place so a concurrent reader
    never sees a half-written cache entry.
    """
    path = _cache_path(config, instance_id)
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"instance_id": instance_id, "parser_revision": _BASELINE_PARSER_REVISION,
               **run_to_dict(run)}
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def classify(
    test_id: str,
    base: TestResult | None,
    patched: TestResult | None,
) -> Outcome:
    """Compare one test's base and patched results (policy §4).

    A test missing from a pass is `NOT_RUN`, never an implicit pass. This is the
    single most important line in the module: absence of evidence is recorded as
    absence, not as success.
    """
    if any(r is not None and r.status is TestStatus.INVALID_ID for r in (base, patched)):
        return Outcome.INVALID_ID
    for status, outcome in ((TestStatus.RUNNER_UNAVAILABLE, Outcome.RUNNER_UNAVAILABLE),
                            (TestStatus.COLLECTION_ERROR, Outcome.COLLECTION_ERROR)):
        if any(r is not None and r.status is status for r in (base, patched)):
            return outcome
    if patched is None or patched.status is TestStatus.NOT_RUN:
        return Outcome.NOT_RUN
    if patched.status is TestStatus.TIMEOUT:
        return Outcome.TIMEOUT
    if base is None or base.status is TestStatus.NOT_RUN:
        # Never ran on base, so no transition can be established. Not a pass.
        return Outcome.NOT_RUN
    if base.status is TestStatus.TIMEOUT:
        return Outcome.TIMEOUT

    # Only an observed base PASS establishes a patched-only ERROR transition.
    if base.status is TestStatus.PASSED and patched.status is TestStatus.ERROR:
        return Outcome.REGRESSION_ERROR

    # Other errors do not establish a patch regression.
    if TestStatus.ERROR in (base.status, patched.status):
        return Outcome.ERROR

    base_ok = base.status in (TestStatus.PASSED, TestStatus.SKIPPED,
                              TestStatus.XFAIL, TestStatus.XPASS)
    patched_ok = patched.status in (TestStatus.PASSED, TestStatus.SKIPPED,
                                    TestStatus.XFAIL, TestStatus.XPASS)

    if base_ok and patched_ok:
        return {TestStatus.XFAIL: Outcome.XFAIL, TestStatus.XPASS: Outcome.XPASS,
                TestStatus.SKIPPED: Outcome.SKIPPED}.get(patched.status, Outcome.PASS)
    if base_ok and not patched_ok:
        return Outcome.REGRESSION
    if not base_ok and patched_ok:
        return Outcome.NEWLY_PASSING
    return Outcome.PRE_EXISTING_FAIL


def concrete_comparison(
    tests: tuple[str, ...], baseline: RunResult, patched: RunResult,
) -> tuple[dict[str, TestResult | None], dict[str, TestResult | None]]:
    """Pair observed concrete cases within each uniquely selected family.

    Cases absent on either tree remain absent; a family's worst status cannot
    stand in for a different parameter case. Historical/structured executors
    without raw identities retain their explicit selected-ID results.
    """
    wanted = set(tests)

    def families(run):
        grouped: dict[str, dict[str, TestResult]] = {}
        for result in run.raw_results:
            selected = run.raw_id_map.get(result.test_id, ())
            if len(selected) == 1 or (run.validation and selected):
                for owner in selected:
                    if owner in wanted:
                        grouped.setdefault(owner, {})[run.raw_execution_map.get(result.test_id, result.test_id)] = result
        return grouped

    base_cases, patch_cases = families(baseline), families(patched)
    base, patch = {}, {}
    base_selected, patch_selected = baseline.by_id(), patched.by_id()
    for test in tests:
        if any(r is not None and r.status is TestStatus.INVALID_ID
               for r in (base_selected.get(test), patch_selected.get(test))):
            base[test], patch[test] = base_selected.get(test), patch_selected.get(test)
            continue
        b, p = base_cases.get(test, {}), patch_cases.get(test, {})
        ids = b.keys() | p.keys()
        if not ids:
            base[test], patch[test] = base_selected.get(test), patch_selected.get(test)
            continue
        for raw_id in sorted(ids):
            # Keep the familiar selected key for a single unparameterized
            # Django/pytest case; parameter cases retain their concrete IDs.
            key = raw_id if (len(ids) > 1 or ("[" in raw_id and raw_id != test)
                             or (raw_id != test and (raw_id in baseline.execution_id_map
                                                     or raw_id in patched.execution_id_map))) else test
            base[key], patch[key] = b.get(raw_id), p.get(raw_id)
    return base, patch


def run_regression(
    instance_id: str,
    selection: Selection,
    executor: TestExecutor,
    config: RegressionConfig | None = None,
) -> RegressionReport:
    """Run the baseline and patched passes and classify every selected test."""
    config = config or RegressionConfig()
    started = time.monotonic()
    notes: list[str] = []

    if selection.is_empty:
        # Policy §5.1/§5.2 — no tests discovered is NOT_AVAILABLE, never a pass.
        return RegressionReport(
            instance_id=instance_id, signal=Signal.NOT_AVAILABLE, selection=selection,
            notes=("no tests selected",),
            original_signal=Signal.NOT_AVAILABLE, completeness="COMPLETE",
        )

    baseline = load_cached_baseline(config, instance_id)
    from_cache = baseline is not None
    if baseline is None:
        baseline = executor.run(
            selection.tests, patched=False, timeout_s=config.per_pass_timeout_s)
        if any(r.status not in (TestStatus.NOT_RUN, TestStatus.TIMEOUT, TestStatus.INVALID_ID,
                                       TestStatus.COLLECTION_ERROR, TestStatus.RUNNER_UNAVAILABLE)
               for r in baseline.results):
            # A pass in which nothing ran is not a baseline, and caching it
            # would hand the same empty answer to every later run.
            save_baseline(config, instance_id, baseline)
    else:
        notes.append("baseline loaded from cache")

    # Policy §5.5: a mostly-red baseline indicts the environment, not the patch.
    baseline_cases, _ = concrete_comparison(selection.tests, baseline, baseline)
    executed_base = [r for r in baseline_cases.values()
                     if r is not None and r.status not in (TestStatus.NOT_RUN, TestStatus.TIMEOUT, TestStatus.INVALID_ID,
                                       TestStatus.COLLECTION_ERROR, TestStatus.RUNNER_UNAVAILABLE)]
    if executed_base:
        failed_base = sum(
            1 for r in executed_base
            if r.status in (TestStatus.FAILED, TestStatus.ERROR))
        if failed_base / len(executed_base) > BASELINE_FAILURE_THRESHOLD:
            return RegressionReport(
                instance_id=instance_id, signal=Signal.BASELINE_UNRELIABLE,
                selection=selection, baseline_from_cache=from_cache,
                duration_s=time.monotonic() - started,
                notes=(
                    (f"{failed_base}/{len(executed_base)} selected tests fail on the "
                     f"base commit; environment is suspect"),
                ),
                original_signal=Signal.BASELINE_UNRELIABLE,
                baseline=baseline,
                incompleteness=("patched pass not executed: unreliable baseline",),
            )

    patched = executor.run(
        selection.tests, patched=True, timeout_s=config.per_pass_timeout_s)
    base_by_id, patched_by_id = concrete_comparison(selection.tests, baseline, patched)

    outcomes = {
        test: classify(test, base_by_id.get(test), patched_by_id.get(test))
        for test in base_by_id
    }

    # Policy §4.1: re-run regressions once in isolation. Rejecting a correct
    # patch over a nondeterministic test lands in the false-rejection rate and
    # distorts the risk-coverage curve directly.
    confirmations = []
    if config.rerun_flaky:
        suspects = tuple(t for t, o in outcomes.items() if o is Outcome.REGRESSION)
        if suspects:
            confirmation = executor.run(
                suspects, patched=True, timeout_s=config.per_pass_timeout_s)
            confirmations.append(confirmation)
            rerun = confirmation.by_id()
            for result in confirmation.raw_results:
                if len(confirmation.raw_id_map.get(result.test_id, ())) == 1:
                    rerun.setdefault(result.test_id, result)
            for test in suspects:
                result = rerun.get(test)
                if result is not None and result.status is TestStatus.PASSED:
                    outcomes[test] = Outcome.FLAKY
                    notes.append(f"{test}: failed then passed on re-run, marked FLAKY")

    n_executed = sum(1 for o in outcomes.values() if o.executed)
    n_regressions = sum(1 for o in outcomes.values() if o.counts_as_regression)

    if n_executed == 0:
        # Tests were selected but none actually ran. Not a pass.
        signal = Signal.NOT_AVAILABLE
        notes.append("tests were selected but none executed")
        notes.extend(
            f"{label}: {run.note}" for label, run in (("baseline", baseline), ("patched", patched))
            if run.note
        )
    elif n_regressions > 0:
        signal = Signal.FAIL
    elif any(o is Outcome.REGRESSION_ERROR for o in outcomes.values()):
        signal = Signal.REGRESSION_ERROR
    else:
        signal = Signal.PASS

    original_signal = signal
    completeness, gaps = completeness_of(selection.tests, baseline, patched,
                                         skip_compatible=config.skip_compatible,
                                         invalid_as_missing=config.invalid_as_missing)
    for confirmation in confirmations:
        state, reasons = completeness_of(
            confirmation.requested_tests or tuple(r.test_id for r in confirmation.results),
            confirmation, confirmation, skip_compatible=config.skip_compatible,
                                         invalid_as_missing=config.invalid_as_missing)
        if state != "COMPLETE":
            completeness = "INCOMPLETE_CONFIRMED" if state == "INCOMPLETE_CONFIRMED" else completeness
            if completeness == "COMPLETE":
                completeness = "UNVERIFIABLE"
            gaps += tuple("confirmation: " + reason for reason in reasons)
    signal = Signal(integrity_verdict(original_signal.value, completeness))
    return RegressionReport(
        instance_id=instance_id, signal=signal, outcomes=outcomes,
        selection=selection, baseline_from_cache=from_cache,
        n_executed=n_executed, duration_s=time.monotonic() - started,
        notes=tuple(notes),
        original_signal=original_signal, completeness=completeness, incompleteness=gaps,
        baseline=baseline, patched=patched, confirmations=tuple(confirmations),
    )
