"""Verifier V3: static and build checks (Phase 6).

Discovers which tooling a repository actually configures, runs what is available
inside the task container, and records everything else as `NOT_AVAILABLE`.

**A check that did not run is never evidence of correctness.** This is the same
principle as `NOT_RUN` in Phase 5, and it is the reason the tool discovery step
exists at all: most repositories configure some of these tools and not others, so
a verifier that scored "mypy found no errors" without noticing mypy was never
configured would be manufacturing evidence. `NOT_AVAILABLE` is a distinct outcome
that cannot be read as a pass anywhere downstream.

**Absolute versus relative checks.** Syntax, import, and build are properties of
the patched tree alone: if it does not compile, that is a failure whatever the
base commit looked like. Lint and type errors are not — repositories carry
pre-existing ones, and attributing them to the candidate patch would be the same
mistake the Phase 5 baseline pass exists to prevent. So lint and typecheck are
compared against the base commit and only *new* findings count, while syntax,
import, and build are judged on the patched tree alone.

Checks are scoped to the files the patch touched. A repository-wide lint run
would drown a one-line fix in unrelated pre-existing noise and cost far more
time for no extra signal about this patch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from reliability.verifier.patch import Patch
from reliability.verifier.selection import RepoTree


class CheckKind(str, Enum):
    SYNTAX = "syntax"
    IMPORT = "import"
    LINT = "lint"
    TYPECHECK = "typecheck"
    BUILD = "build"


class CheckStatus(str, Enum):
    """Outcome of one static check.

    `NOT_AVAILABLE` means the tool is not configured for this repository. It is
    not a pass, not a failure, and must never be collapsed into either.
    """

    PASS = "PASS"
    FAIL = "FAIL"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    ERROR = "ERROR"      # the tool itself broke
    TIMEOUT = "TIMEOUT"

    @property
    def is_pass(self) -> bool:
        return self is CheckStatus.PASS

    @property
    def ran(self) -> bool:
        return self in (CheckStatus.PASS, CheckStatus.FAIL)


#: Checks judged on the patched tree alone. A tree that will not compile is
#: broken regardless of what the base commit did.
ABSOLUTE_CHECKS = (CheckKind.SYNTAX, CheckKind.IMPORT, CheckKind.BUILD)

#: Checks compared against the base commit, because repositories carry
#: pre-existing findings that are not the candidate patch's fault.
RELATIVE_CHECKS = (CheckKind.LINT, CheckKind.TYPECHECK)


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """A tool, and the evidence that a repository configures it."""

    kind: CheckKind
    name: str
    #: Files whose presence indicates the tool is configured.
    config_files: tuple[str, ...] = ()
    #: `pyproject.toml` / `setup.cfg` sections that also count as configuration.
    config_sections: tuple[str, ...] = ()
    command: tuple[str, ...] = ()


#: Discovery table. Order within a kind is preference order: the first tool
#: whose configuration is present wins, so a repo configuring both ruff and
#: flake8 is linted with ruff rather than both.
TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec(CheckKind.LINT, "ruff",
             ("ruff.toml", ".ruff.toml"), ("[tool.ruff]",), ("ruff", "check")),
    ToolSpec(CheckKind.LINT, "flake8",
             (".flake8", "tox.ini"), ("[flake8]",), ("flake8",)),
    ToolSpec(CheckKind.LINT, "pylint",
             (".pylintrc", "pylintrc"), ("[tool.pylint]",), ("pylint",)),
    ToolSpec(CheckKind.TYPECHECK, "mypy",
             ("mypy.ini", ".mypy.ini"), ("[tool.mypy]", "[mypy]"), ("mypy",)),
    ToolSpec(CheckKind.TYPECHECK, "pyright",
             ("pyrightconfig.json",), ("[tool.pyright]",), ("pyright",)),
    ToolSpec(CheckKind.BUILD, "build",
             ("setup.py", "pyproject.toml", "setup.cfg"), (), ("python", "-m", "build")),
)

#: Files whose presence indicates a `pyproject.toml`-style section may configure
#: a tool. Checked textually rather than parsed: a malformed pyproject should not
#: crash discovery, and a section header is unambiguous enough.
_SECTION_SOURCES = ("pyproject.toml", "setup.cfg", "tox.ini")


class CommandExecutor(Protocol):
    """Runs a command inside the task container.

    An interface so discovery and classification are gated against fixtures
    rather than requiring Docker in the unit suite — the same pattern as the
    Phase 3 agent backend and the Phase 5 test executor.
    """

    def run(
        self, command: tuple[str, ...], *, patched: bool, timeout_s: int
    ) -> tuple[int, str]: ...


@dataclass(frozen=True, slots=True)
class Availability:
    """Which tools this repository configures, and the evidence for each."""

    tools: dict[CheckKind, ToolSpec | None] = field(default_factory=dict)
    evidence: dict[CheckKind, str] = field(default_factory=dict)

    def tool_for(self, kind: CheckKind) -> ToolSpec | None:
        return self.tools.get(kind)

    def is_available(self, kind: CheckKind) -> bool:
        return self.tools.get(kind) is not None

    @property
    def available_kinds(self) -> tuple[CheckKind, ...]:
        return tuple(k for k in CheckKind if self.is_available(k))


@dataclass(frozen=True, slots=True)
class CheckResult:
    kind: CheckKind
    status: CheckStatus
    tool: str | None = None
    detail: str = ""
    #: For relative checks: the same check's status on the base commit.
    baseline_status: CheckStatus | None = None

    @property
    def is_new_failure(self) -> bool:
        """A failure the patch introduced, as opposed to one it inherited."""
        if self.status is not CheckStatus.FAIL:
            return False
        if self.baseline_status is None:
            return True
        return self.baseline_status is not CheckStatus.FAIL


@dataclass(frozen=True, slots=True)
class StaticConfig:
    timeout_s: int = 120
    compare_baseline: bool = True
    scope_to_patch: bool = True


@dataclass(frozen=True, slots=True)
class StaticReport:
    results: tuple[CheckResult, ...] = ()
    availability: Availability | None = None

    def by_kind(self) -> dict[CheckKind, CheckResult]:
        return {r.kind: r for r in self.results}

    def status_of(self, kind: CheckKind) -> CheckStatus:
        for result in self.results:
            if result.kind is kind:
                return result.status
        return CheckStatus.NOT_AVAILABLE

    @property
    def new_failures(self) -> tuple[CheckResult, ...]:
        return tuple(r for r in self.results if r.is_new_failure)

    @property
    def n_available(self) -> int:
        return sum(1 for r in self.results if r.status is not CheckStatus.NOT_AVAILABLE)

    @property
    def n_ran(self) -> int:
        return sum(1 for r in self.results if r.status.ran)

    @property
    def summary(self) -> dict[str, str]:
        return {r.kind.value: r.status.value for r in self.results}


def discover_tools(tree: RepoTree) -> Availability:
    """Phase 6.1. Determine which tooling this repository actually configures.

    Syntax and import are always available: any Python file can be compiled and
    imported, so they need no project configuration. Everything else must show
    evidence — a config file or a recognised section — and is `NOT_AVAILABLE`
    without it.
    """
    files = set(tree.list_files())

    # Concatenate the section-bearing files once rather than per tool.
    section_text = "\n".join(
        tree.read_text(name) for name in _SECTION_SOURCES if name in files
    )

    tools: dict[CheckKind, ToolSpec | None] = {}
    evidence: dict[CheckKind, str] = {}

    for kind in (CheckKind.SYNTAX, CheckKind.IMPORT):
        tools[kind] = ToolSpec(kind, "python", command=("python",))
        evidence[kind] = "always available for Python sources"

    for kind in (CheckKind.LINT, CheckKind.TYPECHECK, CheckKind.BUILD):
        tools[kind] = None
        evidence[kind] = "no configuration found"

        for spec in (t for t in TOOLS if t.kind is kind):
            found = next((f for f in spec.config_files if f in files), None)
            if found is not None:
                # tox.ini and setup.cfg only count if they carry the section;
                # they are routinely present for unrelated reasons.
                if (found in _SECTION_SOURCES and spec.config_sections
                        and not any(s in section_text for s in spec.config_sections)):
                    continue
                tools[kind] = spec
                evidence[kind] = f"{spec.name}: found {found}"
                break

            if spec.config_sections and any(s in section_text for s in spec.config_sections):
                tools[kind] = spec
                evidence[kind] = f"{spec.name}: section in project config"
                break

    return Availability(tools=tools, evidence=evidence)


def _patch_targets(patch: Patch) -> tuple[str, ...]:
    """Python files the patch touched, for scoping the checks."""
    return tuple(
        f.path for f in patch
        if f.path.endswith(".py") and not f.is_binary and f.kind.value != "deleted"
    )


def _status_from(returncode: int) -> CheckStatus:
    if returncode == 0:
        return CheckStatus.PASS
    if returncode < 0:
        return CheckStatus.ERROR
    return CheckStatus.FAIL


def run_static_checks(
    patch: Patch,
    tree: RepoTree,
    executor: CommandExecutor,
    config: StaticConfig | None = None,
) -> StaticReport:
    """Run every configured check, recording the rest as NOT_AVAILABLE."""
    config = config or StaticConfig()
    availability = discover_tools(tree)
    targets = _patch_targets(patch) if config.scope_to_patch else ()
    results: list[CheckResult] = []

    for kind in CheckKind:
        spec = availability.tool_for(kind)

        if spec is None:
            # The load-bearing branch: unconfigured tooling records
            # NOT_AVAILABLE and can never be read as a pass.
            results.append(CheckResult(
                kind=kind, status=CheckStatus.NOT_AVAILABLE, tool=None,
                detail=availability.evidence.get(kind, "not configured"),
            ))
            continue

        if kind in (CheckKind.SYNTAX, CheckKind.IMPORT) and not targets:
            results.append(CheckResult(
                kind=kind, status=CheckStatus.NOT_AVAILABLE, tool=spec.name,
                detail="patch touches no Python files",
            ))
            continue

        command = _command_for(kind, spec, targets)

        try:
            returncode, output = executor.run(
                command, patched=True, timeout_s=config.timeout_s)
        except TimeoutError:
            results.append(CheckResult(kind, CheckStatus.TIMEOUT, spec.name,
                                       "timed out"))
            continue

        status = _status_from(returncode)
        baseline_status = None

        # Relative checks: a finding that already existed on base is not this
        # patch's fault. Only run the base pass when the patched pass failed,
        # since a clean patched run needs no attribution.
        if (config.compare_baseline and kind in RELATIVE_CHECKS
                and status is CheckStatus.FAIL):
            try:
                base_rc, _ = executor.run(
                    command, patched=False, timeout_s=config.timeout_s)
                baseline_status = _status_from(base_rc)
            except TimeoutError:
                baseline_status = CheckStatus.TIMEOUT

        results.append(CheckResult(
            kind=kind, status=status, tool=spec.name,
            detail=output[:500], baseline_status=baseline_status,
        ))

    return StaticReport(results=tuple(results), availability=availability)


def _command_for(
    kind: CheckKind, spec: ToolSpec, targets: tuple[str, ...]
) -> tuple[str, ...]:
    if kind is CheckKind.SYNTAX:
        return ("python", "-m", "py_compile", *targets)
    if kind is CheckKind.IMPORT:
        modules = [t[:-3].replace("/", ".") for t in targets]
        statements = "; ".join(f"import {m}" for m in modules)
        return ("python", "-c", statements)
    if kind is CheckKind.BUILD:
        return spec.command
    return (*spec.command, *targets)
