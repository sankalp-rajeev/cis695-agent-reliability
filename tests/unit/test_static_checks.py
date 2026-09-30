"""Phase 6 gate: static and build checks.

The named gate is a repository with no mypy configuration yielding
`NOT_AVAILABLE` rather than `PASS`. The broader property, which several tests
here pin from different angles, is that an unavailable check can never be read
as evidence of correctness anywhere.
"""

from __future__ import annotations

import pytest

from reliability.verifier.patch import parse_patch
from reliability.verifier.selection import LocalRepoTree
from reliability.verifier.static_checks import (
    ABSOLUTE_CHECKS,
    RELATIVE_CHECKS,
    CheckKind,
    CheckResult,
    CheckStatus,
    StaticConfig,
    discover_tools,
    run_static_checks,
)

PATCH = parse_patch("""diff --git a/src/pkg/core.py b/src/pkg/core.py
index 1..2 100644
--- a/src/pkg/core.py
+++ b/src/pkg/core.py
@@ -1,2 +1,2 @@
 def compute(x):
-    return x * 2
+    return x * 3
""")


def make_repo(tmp_path, files: dict[str, str]):
    for name, content in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return LocalRepoTree(tmp_path)


# Each fixture gets its own subdirectory. Sharing tmp_path would let the
# configured repo's pyproject.toml leak into the bare one whenever a single test
# requests both, silently making "bare" not bare.
@pytest.fixture
def bare_repo(tmp_path):
    """No lint, type, or build configuration at all."""
    return make_repo(tmp_path / "bare",
                     {"src/pkg/core.py": "def compute(x):\n    return x * 2\n"})


@pytest.fixture
def fully_configured_repo(tmp_path):
    return make_repo(tmp_path / "configured", {
        "src/pkg/core.py": "def compute(x):\n    return x * 2\n",
        "pyproject.toml": (
            "[build-system]\nrequires = ['setuptools']\n\n"
            "[tool.ruff]\nline-length = 100\n\n"
            "[tool.mypy]\nstrict = true\n"
        ),
    })


class ScriptedExecutor:
    """Replays return codes per command kind."""

    def __init__(self, patched: dict | None = None, base: dict | None = None):
        self._patched = patched or {}
        self._base = base or {}
        self.commands: list[tuple[bool, tuple[str, ...]]] = []

    def _key(self, command):
        joined = " ".join(command)
        for key in ("py_compile", "ruff", "mypy", "flake8", "pylint", "build", "-c"):
            if key in joined:
                return "import" if key == "-c" else key
        return joined

    def run(self, command, *, patched: bool, timeout_s: int):
        self.commands.append((patched, tuple(command)))
        table = self._patched if patched else self._base
        return table.get(self._key(command), 0), "output"


# --- the named gate --------------------------------------------------------


def test_repo_with_no_mypy_config_is_not_available(bare_repo):
    """The gate: no mypy configuration must yield NOT_AVAILABLE, not PASS."""
    report = run_static_checks(PATCH, bare_repo, ScriptedExecutor())
    typecheck = report.by_kind()[CheckKind.TYPECHECK]

    assert typecheck.status is CheckStatus.NOT_AVAILABLE
    assert typecheck.status is not CheckStatus.PASS
    assert typecheck.tool is None


def test_not_available_is_never_a_pass():
    assert not CheckStatus.NOT_AVAILABLE.is_pass
    assert not CheckStatus.NOT_AVAILABLE.ran


def test_unconfigured_tools_are_never_executed(bare_repo):
    """An unavailable check must not quietly run some default tool."""
    executor = ScriptedExecutor()
    run_static_checks(PATCH, bare_repo, executor)

    joined = " ".join(" ".join(c) for _, c in executor.commands)
    assert "mypy" not in joined
    assert "ruff" not in joined
    assert "flake8" not in joined


# --- discovery -------------------------------------------------------------


def test_syntax_and_import_are_always_available(bare_repo):
    availability = discover_tools(bare_repo)
    assert availability.is_available(CheckKind.SYNTAX)
    assert availability.is_available(CheckKind.IMPORT)


def test_bare_repo_has_no_lint_type_or_build(bare_repo):
    availability = discover_tools(bare_repo)
    for kind in (CheckKind.LINT, CheckKind.TYPECHECK, CheckKind.BUILD):
        assert not availability.is_available(kind), kind


def test_pyproject_sections_are_discovered(fully_configured_repo):
    availability = discover_tools(fully_configured_repo)
    assert availability.tool_for(CheckKind.LINT).name == "ruff"
    assert availability.tool_for(CheckKind.TYPECHECK).name == "mypy"
    assert availability.is_available(CheckKind.BUILD)


@pytest.mark.parametrize(
    "filename,kind,tool",
    [
        ("mypy.ini", CheckKind.TYPECHECK, "mypy"),
        (".flake8", CheckKind.LINT, "flake8"),
        ("ruff.toml", CheckKind.LINT, "ruff"),
        (".pylintrc", CheckKind.LINT, "pylint"),
        ("pyrightconfig.json", CheckKind.TYPECHECK, "pyright"),
        ("setup.py", CheckKind.BUILD, "build"),
    ],
)
def test_config_files_are_discovered(tmp_path, filename, kind, tool):
    repo = make_repo(tmp_path, {"src/a.py": "x = 1\n", filename: "\n"})
    assert discover_tools(repo).tool_for(kind).name == tool


def test_tox_ini_without_the_section_does_not_count(tmp_path):
    """A tox.ini present for other reasons is not flake8 configuration."""
    repo = make_repo(tmp_path, {"src/a.py": "x = 1\n", "tox.ini": "[tox]\nenvlist = py311\n"})
    assert not discover_tools(repo).is_available(CheckKind.LINT)


def test_tox_ini_with_the_section_does_count(tmp_path):
    repo = make_repo(tmp_path, {
        "src/a.py": "x = 1\n", "tox.ini": "[tox]\nenvlist = py311\n\n[flake8]\nmax-line-length = 100\n"})
    assert discover_tools(repo).tool_for(CheckKind.LINT).name == "flake8"


def test_discovery_records_its_evidence(fully_configured_repo):
    """The availability decision must be auditable after the fact."""
    availability = discover_tools(fully_configured_repo)
    assert "ruff" in availability.evidence[CheckKind.LINT]
    assert "no configuration" in availability.evidence[CheckKind.BUILD] or \
        "build" in availability.evidence[CheckKind.BUILD]


def test_malformed_pyproject_does_not_crash_discovery(tmp_path):
    repo = make_repo(tmp_path, {"src/a.py": "x = 1\n", "pyproject.toml": "[[[not valid toml"})
    assert discover_tools(repo) is not None


# --- running ---------------------------------------------------------------


def test_all_checks_pass(fully_configured_repo):
    report = run_static_checks(PATCH, fully_configured_repo, ScriptedExecutor())
    assert report.status_of(CheckKind.SYNTAX) is CheckStatus.PASS
    assert report.status_of(CheckKind.LINT) is CheckStatus.PASS
    assert report.status_of(CheckKind.TYPECHECK) is CheckStatus.PASS


def test_syntax_failure_is_recorded(fully_configured_repo):
    executor = ScriptedExecutor(patched={"py_compile": 1})
    report = run_static_checks(PATCH, fully_configured_repo, executor)
    assert report.status_of(CheckKind.SYNTAX) is CheckStatus.FAIL


def test_every_kind_appears_in_the_report(bare_repo):
    """No check may be silently omitted; each resolves to an explicit status."""
    report = run_static_checks(PATCH, bare_repo, ScriptedExecutor())
    assert set(report.by_kind()) == set(CheckKind)


def test_report_summary_lists_every_kind(bare_repo):
    summary = run_static_checks(PATCH, bare_repo, ScriptedExecutor()).summary
    assert set(summary) == {k.value for k in CheckKind}


def test_checks_are_scoped_to_patched_files(fully_configured_repo):
    executor = ScriptedExecutor()
    run_static_checks(PATCH, fully_configured_repo, executor)
    compile_cmd = next(c for _, c in executor.commands if "py_compile" in " ".join(c))
    assert "src/pkg/core.py" in compile_cmd


def test_patch_touching_no_python_files_marks_syntax_unavailable(fully_configured_repo):
    docs_only = parse_patch("""diff --git a/docs/g.rst b/docs/g.rst
index 1..2 100644
--- a/docs/g.rst
+++ b/docs/g.rst
@@ -1,1 +1,2 @@
 Guide
+More
""")
    report = run_static_checks(docs_only, fully_configured_repo, ScriptedExecutor())
    assert report.status_of(CheckKind.SYNTAX) is CheckStatus.NOT_AVAILABLE


def test_timeout_is_not_a_pass(fully_configured_repo):
    class TimingOut:
        def run(self, command, *, patched, timeout_s):
            raise TimeoutError

    report = run_static_checks(PATCH, fully_configured_repo, TimingOut())
    assert report.status_of(CheckKind.SYNTAX) is CheckStatus.TIMEOUT
    assert report.status_of(CheckKind.SYNTAX) is not CheckStatus.PASS


# --- absolute vs relative --------------------------------------------------


def test_pre_existing_lint_failure_is_not_blamed_on_the_patch(fully_configured_repo):
    """Same principle as the Phase 5 baseline: inherited noise is not a regression."""
    executor = ScriptedExecutor(patched={"ruff": 1}, base={"ruff": 1})
    report = run_static_checks(PATCH, fully_configured_repo, executor)

    lint = report.by_kind()[CheckKind.LINT]
    assert lint.status is CheckStatus.FAIL
    assert lint.baseline_status is CheckStatus.FAIL
    assert not lint.is_new_failure
    assert report.new_failures == ()


def test_new_lint_failure_is_attributed_to_the_patch(fully_configured_repo):
    executor = ScriptedExecutor(patched={"ruff": 1}, base={"ruff": 0})
    report = run_static_checks(PATCH, fully_configured_repo, executor)

    lint = report.by_kind()[CheckKind.LINT]
    assert lint.is_new_failure
    assert lint in report.new_failures


def test_syntax_failure_needs_no_baseline(fully_configured_repo):
    """A tree that will not compile is broken regardless of the base commit."""
    executor = ScriptedExecutor(patched={"py_compile": 1}, base={"py_compile": 1})
    report = run_static_checks(PATCH, fully_configured_repo, executor)

    syntax = report.by_kind()[CheckKind.SYNTAX]
    assert syntax.baseline_status is None
    assert syntax.is_new_failure


def test_baseline_is_only_run_when_the_patched_check_failed(fully_configured_repo):
    executor = ScriptedExecutor(patched={"ruff": 0})
    run_static_checks(PATCH, fully_configured_repo, executor)
    assert all(patched for patched, _ in executor.commands)


def test_baseline_comparison_can_be_disabled(fully_configured_repo):
    executor = ScriptedExecutor(patched={"ruff": 1}, base={"ruff": 1})
    report = run_static_checks(PATCH, fully_configured_repo, executor,
                               StaticConfig(compare_baseline=False))
    assert report.by_kind()[CheckKind.LINT].is_new_failure


def test_absolute_and_relative_sets_are_disjoint_and_complete():
    assert set(ABSOLUTE_CHECKS) | set(RELATIVE_CHECKS) == set(CheckKind)
    assert not set(ABSOLUTE_CHECKS) & set(RELATIVE_CHECKS)


# --- counting --------------------------------------------------------------


def test_availability_counts(bare_repo, fully_configured_repo):
    bare = run_static_checks(PATCH, bare_repo, ScriptedExecutor())
    full = run_static_checks(PATCH, fully_configured_repo, ScriptedExecutor())
    assert bare.n_available == 2          # syntax + import only
    assert full.n_available == 5
    assert bare.n_ran == 2


def test_unavailable_result_has_no_baseline():
    result = CheckResult(CheckKind.TYPECHECK, CheckStatus.NOT_AVAILABLE)
    assert not result.is_new_failure


class _OutputExecutor:
    """Returns a scripted (code, output) for one command key."""

    def __init__(self, outputs: dict[str, tuple[int, str]]):
        self.outputs = outputs

    def run(self, command, *, patched: bool, timeout_s: int):
        joined = " ".join(command)
        for key, value in self.outputs.items():
            if key in joined:
                return value
        return 0, ""


def test_missing_build_module_is_not_available_not_a_new_failure(fully_configured_repo):
    """python -m build absent from the image must not fail every patch."""
    executor = _OutputExecutor({
        "py_compile": (0, ""),
        "-c": (0, ""),
        "ruff": (0, ""),
        "mypy": (0, ""),
        "build": (1, "/usr/bin/python: No module named build"),
    })
    report = run_static_checks(PATCH, fully_configured_repo, executor)
    build = report.by_kind()[CheckKind.BUILD]

    assert build.status is CheckStatus.NOT_AVAILABLE
    assert build.status is not CheckStatus.FAIL
    assert "No module named build" in build.detail
    assert build not in report.new_failures
    assert "build" not in {r.kind for r in report.new_failures}


@pytest.mark.parametrize(
    "key,kind,config_file,config_body,output",
    [
        ("ruff", CheckKind.LINT, "ruff.toml", "\n", "ruff: command not found"),
        ("flake8", CheckKind.LINT, ".flake8", "[flake8]\n", "flake8: command not found"),
        ("pylint", CheckKind.LINT, ".pylintrc", "\n", "pylint: command not found"),
        ("mypy", CheckKind.TYPECHECK, "mypy.ini", "\n",
         "/usr/bin/python: No module named mypy"),
        ("pyright", CheckKind.TYPECHECK, "pyrightconfig.json", "{}\n",
         "pyright: not found"),
    ],
)
def test_absent_external_tool_is_not_available(
    tmp_path, key, kind, config_file, config_body, output
):
    """The same class of error as a missing build module, for every Phase 6 tool."""
    repo = make_repo(tmp_path / key, {
        "src/pkg/core.py": "def compute(x):\n    return x * 2\n",
        config_file: config_body,
    })
    executor = _OutputExecutor({
        key: (127, output),
        "py_compile": (0, ""),
        "-c": (0, ""),
    })
    report = run_static_checks(PATCH, repo, executor)
    result = report.by_kind()[kind]
    assert result.status is CheckStatus.NOT_AVAILABLE
    assert result.tool == key
    assert result not in report.new_failures
    assert key in result.detail


def test_import_failure_of_the_patched_module_stays_fail(bare_repo):
    """A missing project module is a real failure; only a missing tool is not."""
    executor = _OutputExecutor({
        "py_compile": (0, ""),
        "-c": (1, "ModuleNotFoundError: No module named 'src.pkg.core'"),
    })
    report = run_static_checks(PATCH, bare_repo, executor)
    assert report.by_kind()[CheckKind.IMPORT].status is CheckStatus.FAIL
    assert report.by_kind()[CheckKind.IMPORT] in report.new_failures


def test_syntax_error_stays_fail(bare_repo):
    executor = _OutputExecutor({
        "py_compile": (1, "Sorry: SyntaxError: invalid syntax"),
        "-c": (0, ""),
    })
    report = run_static_checks(PATCH, bare_repo, executor)
    assert report.by_kind()[CheckKind.SYNTAX].status is CheckStatus.FAIL


def test_missing_interpreter_is_not_available(bare_repo):
    executor = _OutputExecutor({
        "py_compile": (127, "python: command not found"),
        "-c": (127, "python: command not found"),
    })
    report = run_static_checks(PATCH, bare_repo, executor)
    assert report.by_kind()[CheckKind.SYNTAX].status is CheckStatus.NOT_AVAILABLE
    assert report.by_kind()[CheckKind.IMPORT].status is CheckStatus.NOT_AVAILABLE
    assert report.new_failures == ()


# --- config and code must not drift ----------------------------------------


def test_shipped_config_matches_the_absolute_relative_split():
    import pathlib

    import yaml

    cfg = yaml.safe_load(pathlib.Path("configs/verifier/full.yaml").read_text())["static"]

    assert cfg["unavailable_is_pass"] is False
    assert [k.value for k in ABSOLUTE_CHECKS] == cfg["absolute_checks"]
    assert [k.value for k in RELATIVE_CHECKS] == cfg["relative_checks"]
    assert cfg["checks"] == [k.value for k in CheckKind]
    assert cfg["compare_baseline"] is StaticConfig().compare_baseline
    assert cfg["scope_to_patch"] is StaticConfig().scope_to_patch
    assert cfg["timeout_s"] == StaticConfig().timeout_s
