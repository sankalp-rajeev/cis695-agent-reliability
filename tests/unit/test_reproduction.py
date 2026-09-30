"""V4 gates: what the generator can see, what gets kept, and what executes.

Three named gates, each stated the way the Phase 2 leakage gate is — as a
closed structural property, so that widening the boundary fails the suite
rather than relying on a reviewer to notice:

1. The generator's input carries no candidate patch, gold patch, gold test
   patch, FAIL_TO_PASS, PASS_TO_PASS, or agent trajectory. Every entry point's
   parameters and every configuration object's fields are asserted as exact
   sets, and the prompt template's only variable is the issue text.
2. A test whose base-commit result is not deterministic is dropped.
3. The frozen bytes are what execute: a patch that rewrites the generated
   test's path changes nothing that runs.

The sandboxes here are local directories and the tests are real Python
scripts run by a real interpreter; only the container is swapped out.
"""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import inspect
import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest
import yaml

from reliability.verifier import reproduction_freeze
from reliability.verifier.decision import SignalOutcome
from reliability.verifier.record import SignalAbsence
from reliability.verifier.reproduction import (
    base_container_sandbox,
    evaluate_frozen,
    patched_verdict,
    signal_from_reproduction,
)
from reliability.verifier.reproduction_freeze import (
    DropReason,
    GenerationOutcome,
    GeneratorModel,
    MiniSweGenerator,
    ReproductionBudget,
    ReproductionConfigError,
    ReproductionSetup,
    ReproGenerator,
    RunOutcome,
    RunResult,
    classify,
    freeze_tests,
    repro_path,
    screen_verdict,
)
from reliability.verifier.run import run_reproduction

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTANCE = "example__example-1"
ISSUE = "mod.value should be 2, but it is 1."

#: Anything that would let the generator see the answer, or see the repair.
#: Matched as whole `_`-separated tokens, so `patch_text`, `gold_patch` and
#: `test_patch` match and the run count `patched_runs` does not.
FORBIDDEN_TOKENS = {"patch", "diff", "gold", "trajectory", "oracle", "repair",
                    "claim", "hints"}
FORBIDDEN_PHRASES = ("fail_to_pass", "pass_to_pass")


def _forbidden(name: str) -> bool:
    lowered = name.lower()
    return (bool(set(lowered.split("_")) & FORBIDDEN_TOKENS)
            or any(p in lowered for p in FORBIDDEN_PHRASES))


# --- fixtures ----------------------------------------------------------------


def make_setup(**budget) -> ReproductionSetup:
    values = {
        "max_tests": 3, "retries": 0, "generator_max_steps": 40,
        "generator_max_cost_usd": 1.0, "generator_timeout_s": 1200,
        "per_command_timeout_s": 60, "screen_runs": 2, "patched_runs": 2,
        "per_run_timeout_s": 30, "max_test_bytes": 65536,
        **budget,
    }
    return ReproductionSetup(
        model=GeneratorModel(
            config_path="configs/model/generator.yaml",
            model_id="deepseek/deepseek-v4-flash", served_model="deepseek-flash",
            system_fingerprint="fp", verified_on="2026-09-30", temperature=0.0,
            top_p=1.0, max_output_tokens=8192, drop_params=True),
        budget=ReproductionBudget(**values),
        prompt_path="configs/agent/v4_generator.yaml",
        prompt_sha256="sha256:" + "0" * 64,
    )


class LocalSandbox:
    """A working tree on disk, run by this interpreter with a scrubbed env."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def write_file(self, path: str, data: bytes) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def sha256(self, path: str) -> str | None:
        target = self.root / path
        if not target.is_file():
            return None
        return "sha256:" + hashlib.sha256(target.read_bytes()).hexdigest()

    def run_test(self, path: str, timeout_s: int) -> tuple[int, str]:
        proc = subprocess.run(
            [sys.executable, path], cwd=self.root, capture_output=True, text=True,
            timeout=timeout_s, check=False,
            env={"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(self.root)})
        return proc.returncode, proc.stdout + proc.stderr


class Trees:
    """Fresh copies of a base tree, optionally with a patch applied."""

    def __init__(self, tmp_path: Path) -> None:
        self.tmp = tmp_path
        self.base = tmp_path / "base"
        self.base.mkdir()
        (self.base / "mod.py").write_text("value = 1\n")
        self.opened: list[Path] = []

    def _copy(self) -> Path:
        dest = self.tmp / f"tree_{len(self.opened)}"
        shutil.copytree(self.base, dest)
        self.opened.append(dest)
        return dest

    @contextmanager
    def base_sandbox(self, instance_id: str):
        yield LocalSandbox(self._copy())

    @contextmanager
    def patched_sandbox(self, instance_id: str, patch_text: str):
        root = self._copy()
        proc = subprocess.run(["git", "apply", "-"], cwd=root, input=patch_text,
                              text=True, capture_output=True, check=False)
        assert proc.returncode == 0, proc.stderr
        yield LocalSandbox(root)


@dataclasses.dataclass
class RecordingGenerator:
    files: dict[str, bytes]
    calls: list[tuple] = dataclasses.field(default_factory=list)

    def generate(self, issue_text: str, instance_id: str) -> GenerationOutcome:
        self.calls.append((issue_text, instance_id))
        return GenerationOutcome(files=dict(self.files), termination="Submitted")


GOOD = b"import mod\nassert mod.value == 2, mod.value\n"
PASSES_ON_BASE = b"import mod\nassert mod.value == 1\n"
IMPORT_ERROR = b"import no_such_module_anywhere\n"
#: Alternates between failing and passing, keyed off a counter in the tree.
ALTERNATES = b"""import pathlib
p = pathlib.Path(".v4_count")
n = int(p.read_text()) if p.exists() else 0
p.write_text(str(n + 1))
assert n % 2 == 1, "fails on even runs"
"""
#: Deterministic AssertionError at the base commit; alternates once patched.
FLAKY_ONLY_WHEN_PATCHED = b"""import mod, pathlib
assert mod.value == 2, "bug present"
p = pathlib.Path(".v4_count")
n = int(p.read_text()) if p.exists() else 0
p.write_text(str(n + 1))
assert n % 2 == 1, "flaky once fixed"
"""

FIX = """diff --git a/mod.py b/mod.py
--- a/mod.py
+++ b/mod.py
@@ -1 +1 @@
-value = 1
+value = 2
"""

#: Leaves the bug in place, and plants a test at the generated path that passes.
PLANT_PASSING_TEST = """diff --git a/v4_repro/test_repro_1.py b/v4_repro/test_repro_1.py
new file mode 100644
--- /dev/null
+++ b/v4_repro/test_repro_1.py
@@ -0,0 +1,2 @@
+print("PLANTED")
+raise SystemExit(0)
"""

#: Fixes the bug, and plants a test at the generated path that fails.
FIX_AND_PLANT_FAILING_TEST = FIX + """diff --git a/v4_repro/test_repro_1.py b/v4_repro/test_repro_1.py
new file mode 100644
--- /dev/null
+++ b/v4_repro/test_repro_1.py
@@ -0,0 +1,2 @@
+print("PLANTED")
+raise AssertionError("planted")
"""


def freeze(tmp_path, trees, files, setup=None):
    generator = RecordingGenerator(files)
    suite = freeze_tests(
        ISSUE, INSTANCE, setup=setup or make_setup(), cache_dir=tmp_path / "cache",
        generator=generator, base_sandbox=trees.base_sandbox)
    return suite, generator


def verify(tmp_path, trees, files, patch_text, setup=None):
    setup = setup or make_setup()
    generator = RecordingGenerator(files)
    signal = run_reproduction(
        INSTANCE, patch_text, setup, use_container=True, patch_applies=True,
        cache_dir=tmp_path / "cache", generator=generator,
        base_sandbox=trees.base_sandbox, patched_sandbox=trees.patched_sandbox,
        issue_text=ISSUE)
    return signal, generator


# --- gate 1: the generator's input -----------------------------------------


def _params(fn) -> set[str]:
    return set(inspect.signature(fn).parameters)


def test_freeze_takes_the_issue_text_and_nothing_derived_from_a_repair():
    assert _params(freeze_tests) == {
        "issue_text", "instance_id", "setup", "cache_dir", "generator", "base_sandbox"}


def test_the_generator_is_called_with_issue_text_and_instance_id_only():
    for fn in (ReproGenerator.generate, MiniSweGenerator.generate):
        assert _params(fn) == {"self", "issue_text", "instance_id"}


def test_the_base_sandbox_is_opened_without_a_patch():
    assert _params(base_container_sandbox) == {"instance_id"}


@pytest.mark.parametrize("cls, fields", [
    (ReproductionSetup, {"model", "budget", "prompt_path", "prompt_sha256"}),
    (GeneratorModel, {"config_path", "model_id", "served_model", "system_fingerprint",
                      "verified_on", "temperature", "top_p", "max_output_tokens",
                      "drop_params"}),
    (ReproductionBudget, {"max_tests", "retries", "generator_max_steps",
                          "generator_max_cost_usd", "generator_timeout_s",
                          "per_command_timeout_s", "screen_runs", "patched_runs",
                          "per_run_timeout_s", "max_test_bytes"}),
    (MiniSweGenerator, {"setup", "repo_root"}),
])
def test_everything_handed_to_the_generator_is_a_closed_set(cls, fields):
    assert {f.name for f in dataclasses.fields(cls)} == fields


def test_no_input_name_refers_to_a_patch_an_oracle_field_or_a_trajectory():
    """Redundant with the closed sets, on purpose: this one says *why* it failed."""
    names = (_params(freeze_tests) | _params(MiniSweGenerator.generate)
             | {f.name for cls in (ReproductionSetup, GeneratorModel,
                                   ReproductionBudget, MiniSweGenerator)
                for f in dataclasses.fields(cls)})
    assert sorted(n for n in names if _forbidden(n)) == []


@pytest.mark.parametrize("name", ["patch_text", "candidate_patch", "gold_patch",
                                  "test_patch", "FAIL_TO_PASS", "pass_to_pass",
                                  "agent_trajectory", "trajectory", "diff"])
def test_the_name_check_would_catch_each_forbidden_input(name):
    assert _forbidden(name)


def test_the_prompt_template_has_one_variable_and_it_is_the_issue():
    from jinja2 import Environment, meta

    cfg = yaml.safe_load((REPO_ROOT / "configs/agent/v4_generator.yaml").read_text())
    env = Environment()
    assert meta.find_undeclared_variables(
        env.parse(cfg["agent"]["instance_template"])) == {"task"}
    assert meta.find_undeclared_variables(
        env.parse(cfg["agent"]["system_template"])) == set()


def test_the_freeze_module_imports_nothing_that_holds_a_patch_or_the_oracle():
    tree = ast.parse(inspect.getsource(reproduction_freeze))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported |= {f"{node.module}.{a.name}" for a in node.names}
        elif isinstance(node, ast.Import):
            imported |= {a.name for a in node.names}
    banned = ("reliability.agent.freeze", "reliability.agent.records",
              "reliability.agent.runner", "reliability.benchmark",
              "reliability.oracle", "reliability.verifier.patch",
              "reliability.verifier.reproduction.", "reliability.verifier.run")
    assert sorted(i for i in imported if i.startswith(banned)) == []


def test_a_candidate_patch_never_reaches_the_generator(tmp_path):
    marker = "CANDIDATE_PATCH_MARKER_7f3a"
    patch_text = FIX.replace("+value = 2", f"+value = 2  # {marker}")
    signal, generator = verify(tmp_path, Trees(tmp_path), {repro_path(1): GOOD},
                               patch_text)
    assert generator.calls == [(ISSUE, INSTANCE)]
    assert marker not in repr(generator.calls)
    assert signal.outcome is SignalOutcome.PASS


# --- gate 2: nondeterministic base-commit failures are dropped --------------


def test_a_nondeterministic_base_failure_is_dropped(tmp_path):
    suite, _ = freeze(tmp_path, Trees(tmp_path), {repro_path(1): ALTERNATES})
    (test,) = suite.tests
    assert [r.outcome for r in test.base_runs] == [
        RunOutcome.ASSERTION_FAILURE, RunOutcome.PASS]
    assert test.kept is False
    assert test.drop_reason is DropReason.NONDETERMINISTIC
    assert suite.kept == ()


def test_a_dropped_test_never_becomes_evidence(tmp_path):
    signal, _ = verify(tmp_path, Trees(tmp_path),
                       {repro_path(1): ALTERNATES}, FIX)
    assert signal.outcome is SignalOutcome.NOT_AVAILABLE
    assert signal.absence is SignalAbsence.NOTHING_TO_CHECK
    assert "no retry" in signal.detail


def test_only_the_deterministic_test_counts(tmp_path):
    signal, _ = verify(tmp_path, Trees(tmp_path),
                       {repro_path(1): ALTERNATES, repro_path(2): GOOD}, FIX)
    assert signal.outcome is SignalOutcome.PASS
    assert [t["path"] for t in signal.findings["patched"]] == [repro_path(2)]


def test_a_test_flaky_on_the_patched_tree_is_dropped_not_counted(tmp_path):
    signal, _ = verify(tmp_path, Trees(tmp_path),
                       {repro_path(1): FLAKY_ONLY_WHEN_PATCHED}, FIX)
    (patched,) = signal.findings["patched"]
    assert patched["verdict"] == "flaky"
    assert signal.outcome is SignalOutcome.NOT_AVAILABLE
    assert signal.absence is SignalAbsence.NOTHING_TO_CHECK


#: Fails its assertion at the base commit; once patched, reaches an attribute
#: the fix does not provide.
ERRORS_WHEN_PATCHED = b"""import mod
assert mod.value == 2, "bug present"
mod.helper_the_test_assumed()
"""


def test_a_deterministic_error_on_the_patched_tree_is_dropped_not_a_fail(tmp_path):
    """An AttributeError means the test cannot run there, not that the bug persists."""
    signal, _ = verify(tmp_path, Trees(tmp_path),
                       {repro_path(1): ERRORS_WHEN_PATCHED}, FIX)
    (patched,) = signal.findings["patched"]
    assert [r["outcome"] for r in patched["runs"]] == ["error", "error"]
    assert patched["verdict"] == "error"
    assert signal.outcome is SignalOutcome.NOT_AVAILABLE
    assert signal.absence is SignalAbsence.NOTHING_TO_CHECK


def test_an_erroring_test_does_not_outvote_a_passing_one(tmp_path):
    signal, _ = verify(tmp_path, Trees(tmp_path),
                       {repro_path(1): ERRORS_WHEN_PATCHED, repro_path(2): GOOD}, FIX)
    assert signal.outcome is SignalOutcome.PASS
    assert "1 dropped (error)" in signal.detail


def test_only_a_repeated_assertion_failure_is_a_fail():
    def runs(*outcomes):
        return [RunResult(o, 0 if o is RunOutcome.PASS else 1, "") for o in outcomes]

    assert patched_verdict(runs(RunOutcome.ASSERTION_FAILURE,
                                RunOutcome.ASSERTION_FAILURE)) == "fail"
    assert patched_verdict(runs(RunOutcome.ERROR, RunOutcome.ERROR)) == "error"
    assert patched_verdict(runs(RunOutcome.TIMEOUT, RunOutcome.TIMEOUT)) == "timeout"
    assert patched_verdict(runs(RunOutcome.PASS, RunOutcome.PASS)) == "pass"


@pytest.mark.parametrize("script, reason", [
    (PASSES_ON_BASE, DropReason.PASSES_ON_BASE),
    (IMPORT_ERROR, DropReason.NOT_AN_ASSERTION),
])
def test_only_an_assertion_failure_on_base_is_kept(tmp_path, script, reason):
    suite, _ = freeze(tmp_path, Trees(tmp_path), {repro_path(1): script})
    assert suite.tests[0].drop_reason is reason


def test_mixed_failure_kinds_are_nondeterministic():
    assert screen_verdict([
        RunResult(RunOutcome.ASSERTION_FAILURE, 1, ""),
        RunResult(RunOutcome.ERROR, 1, ""),
    ]) is DropReason.NONDETERMINISTIC
    assert patched_verdict([
        RunResult(RunOutcome.PASS, 0, ""),
        RunResult(RunOutcome.ASSERTION_FAILURE, 1, ""),
    ]) == "flaky"


# --- gate 3: the frozen bytes are what execute ------------------------------


def test_a_patch_that_plants_a_passing_test_still_runs_the_snapshot(tmp_path):
    trees = Trees(tmp_path)
    signal, _ = verify(tmp_path, trees, {repro_path(1): GOOD}, PLANT_PASSING_TEST)

    (patched,) = signal.findings["patched"]
    assert patched["patch_touched_path"] is True
    assert all("PLANTED" not in run["tail"] for run in patched["runs"])
    assert patched["verdict"] == "fail"
    assert signal.outcome is SignalOutcome.FAIL

    # The file left in the patched tree is the snapshot, byte for byte.
    patched_tree = trees.opened[-1]
    assert (patched_tree / repro_path(1)).read_bytes() == GOOD
    assert patched["sha256"] == signal.findings["frozen"][0]["sha256"]


def test_a_fix_that_plants_a_failing_test_still_passes_on_the_snapshot(tmp_path):
    signal, _ = verify(tmp_path, Trees(tmp_path), {repro_path(1): GOOD},
                       FIX_AND_PLANT_FAILING_TEST)
    (patched,) = signal.findings["patched"]
    assert patched["patch_touched_path"] is True
    assert all("PLANTED" not in run["tail"] for run in patched["runs"])
    assert signal.outcome is SignalOutcome.PASS


def test_bytes_that_do_not_land_are_an_error_not_a_run(tmp_path):
    trees = Trees(tmp_path)
    suite, _ = freeze(tmp_path, trees, {repro_path(1): GOOD})

    class Swallowing(LocalSandbox):
        def write_file(self, path, data):
            super().write_file(path, b"raise SystemExit(0)\n")

    patched = evaluate_frozen(suite, FIX, Swallowing(trees._copy()), make_setup())
    assert patched[0].verdict == "not_in_place"
    assert patched[0].runs == ()
    signal = signal_from_reproduction(suite, patched, make_setup())
    assert signal.absence is SignalAbsence.ERROR


def test_a_host_copy_changed_after_freezing_is_refused(tmp_path):
    trees = Trees(tmp_path)
    suite, _ = freeze(tmp_path, trees, {repro_path(1): GOOD})
    (suite.directory / "tests" / "test_repro_1.py").write_bytes(b"pass\n")
    with pytest.raises(ReproductionConfigError, match="changed on the host"):
        evaluate_frozen(suite, FIX, LocalSandbox(trees._copy()), make_setup())


# --- freeze-once, budget, and configuration ---------------------------------


def test_a_freeze_is_generated_once_and_reused(tmp_path):
    trees = Trees(tmp_path)
    first, gen1 = freeze(tmp_path, trees, {repro_path(1): GOOD})
    second, gen2 = freeze(tmp_path, trees, {repro_path(1): PASSES_ON_BASE})
    assert len(gen1.calls) == 1 and gen2.calls == []
    assert second.suite_sha256 == first.suite_sha256


def test_a_freeze_from_another_setup_is_refused(tmp_path):
    trees = Trees(tmp_path)
    freeze(tmp_path, trees, {repro_path(1): GOOD})
    with pytest.raises(ReproductionConfigError, match="different V4 setup"):
        freeze(tmp_path, trees, {repro_path(1): GOOD}, setup=make_setup(max_tests=2))


def test_no_files_written_is_nothing_to_check(tmp_path):
    signal, _ = verify(tmp_path, Trees(tmp_path), {}, FIX)
    assert signal.absence is SignalAbsence.NOTHING_TO_CHECK
    assert signal.findings["setup"]["generator"]["model_id"] == "deepseek/deepseek-v4-flash"


def test_the_signal_carries_the_test_hashes(tmp_path):
    signal, _ = verify(tmp_path, Trees(tmp_path), {repro_path(1): GOOD}, FIX)
    digest = "sha256:" + hashlib.sha256(GOOD).hexdigest()
    assert signal.findings["frozen"][0]["sha256"] == digest
    assert signal.findings["patched"][0]["sha256"] == digest
    assert signal.findings["suite_sha256"].startswith("sha256:")


@pytest.mark.parametrize("rc, output, outcome", [
    (0, "", RunOutcome.PASS),
    (1, "Traceback...\nAssertionError: value is 1\n", RunOutcome.ASSERTION_FAILURE),
    (1, "Traceback...\nAssertionError\n", RunOutcome.ASSERTION_FAILURE),
    (1, "Traceback...\nImportError: no module\n", RunOutcome.ERROR),
    (2, "AssertionError\n", RunOutcome.ERROR),
    (124, "", RunOutcome.TIMEOUT),
])
def test_classify(rc, output, outcome):
    assert classify(rc, output) is outcome


def test_the_shipped_budget_is_fixed_and_loads():
    setup = ReproductionSetup.load(
        verifier_config=REPO_ROOT / "configs/verifier/full.yaml", repo_root=REPO_ROOT)
    assert setup.budget.max_tests == 3
    assert setup.budget.retries == 0
    assert setup.model.config_path == "configs/model/generator.yaml"
    assert setup.prompt_sha256 == "sha256:" + hashlib.sha256(
        (REPO_ROOT / "configs/agent/v4_generator.yaml").read_bytes()).hexdigest()


def test_a_retry_budget_is_refused():
    cfg = yaml.safe_load((REPO_ROOT / "configs/verifier/full.yaml").read_text())
    budget = dict(cfg["reproduction"]["budget"], retries=1)
    with pytest.raises(ReproductionConfigError, match="retries must be 0"):
        ReproductionBudget.from_config(budget)


def test_the_generator_pin_is_separate_and_live_verified():
    cfg = yaml.safe_load((REPO_ROOT / "configs/model/generator.yaml").read_text())
    assert cfg["role"] == "generator"
    assert cfg["verified"]["status"] == "ok"
    assert cfg["verified"]["model_id"] == cfg["model_id"]
    assert cfg["verified"]["served_model"] not in (None, "", "unreported")


def test_an_unverified_generator_is_refused(tmp_path):
    cfg = yaml.safe_load((REPO_ROOT / "configs/model/generator.yaml").read_text())
    cfg["verified"] = {"status": "pending"}
    path = tmp_path / "generator.yaml"
    path.write_text(yaml.safe_dump(cfg))
    with pytest.raises(ReproductionConfigError, match="not verified"):
        GeneratorModel.load(path)


def test_the_generator_prompt_names_the_paths_that_are_read_out():
    text = (REPO_ROOT / "configs/agent/v4_generator.yaml").read_text()
    for i in range(1, make_setup().budget.max_tests + 1):
        assert repro_path(i) in text
