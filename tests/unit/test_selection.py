"""Phase 5.1 gate: test selection follows VERIFIER_POLICY.md.

The load-bearing property is negative: selection never consults PASS_TO_PASS or
any other oracle field. That is checked structurally here — `select_tests` has no
parameter through which one could be passed.
"""

from __future__ import annotations

import inspect

import pytest

from reliability.verifier.patch import parse_patch, touched_symbols
from reliability.verifier.selection import (
    Convention,
    LocalRepoTree,
    SelectionConfig,
    Tier,
    discover_convention,
    discover_runner,
    django_label,
    node_ids,
    select_tests,
)


@pytest.fixture
def mirrored_repo(tmp_path):
    """src/pkg/*.py with tests/pkg/test_*.py — the mirrored-tree layout."""
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    (tmp_path / "tests" / "pkg").mkdir(parents=True)

    (tmp_path / "src" / "pkg" / "compiler.py").write_text(
        "class SQLCompiler:\n    def as_sql(self):\n        return ''\n"
    )
    (tmp_path / "src" / "pkg" / "query.py").write_text(
        "def build_query(x):\n    return x\n"
    )
    (tmp_path / "src" / "pkg" / "unrelated.py").write_text("def other():\n    pass\n")

    (tmp_path / "tests" / "pkg" / "test_compiler.py").write_text(
        "def test_as_sql():\n    assert True\n"
    )
    (tmp_path / "tests" / "pkg" / "test_query.py").write_text(
        "from src.pkg.query import build_query\ndef test_q():\n    assert build_query(1)\n"
    )
    # References SQLCompiler without being its corresponding test file: the
    # Tier 1 miss that Tier 2 exists to catch.
    (tmp_path / "tests" / "pkg" / "test_queryset.py").write_text(
        "from src.pkg.compiler import SQLCompiler\n"
        "def test_queryset_uses_compiler():\n    assert SQLCompiler\n"
    )
    (tmp_path / "tests" / "pkg" / "test_unrelated.py").write_text(
        "def test_nothing():\n    assert True\n"
    )
    return LocalRepoTree(tmp_path)


COMPILER_PATCH = parse_patch("""diff --git a/src/pkg/compiler.py b/src/pkg/compiler.py
index 1..2 100644
--- a/src/pkg/compiler.py
+++ b/src/pkg/compiler.py
@@ -1,3 +1,3 @@
 class SQLCompiler:
     def as_sql(self):
-        return ''
+        return 'SELECT 1'
""")


# --- §3.1 convention discovery --------------------------------------------


def test_discovers_mirrored_tree_layout(mirrored_repo):
    result = discover_convention(mirrored_repo)
    assert result.convention is Convention.MIRRORED_TREE
    assert result.hit_rate > 0.5
    assert result.is_known


def test_sibling_layout_is_discovered(tmp_path):
    (tmp_path / "pkg" / "tests").mkdir(parents=True)
    (tmp_path / "pkg" / "a.py").write_text("def a(): pass\n")
    (tmp_path / "pkg" / "b.py").write_text("def b(): pass\n")
    (tmp_path / "pkg" / "tests" / "test_a.py").write_text("def test_a(): pass\n")
    (tmp_path / "pkg" / "tests" / "test_b.py").write_text("def test_b(): pass\n")

    assert discover_convention(LocalRepoTree(tmp_path)).convention is Convention.SIBLING_TESTS


def test_unknown_convention_when_nothing_matches(tmp_path):
    """Policy §3.1: a layout that locates nothing is not a layout; Tier 2 only."""
    (tmp_path / "weird").mkdir()
    for i in range(10):
        (tmp_path / "weird" / f"mod{i}.py").write_text("x = 1\n")
    result = discover_convention(LocalRepoTree(tmp_path))
    assert result.convention is Convention.UNKNOWN
    assert not result.is_known


def test_convention_is_reported_for_the_record(mirrored_repo):
    """Policy §3.1: the mapping used must be auditable after the fact."""
    selection = select_tests(COMPILER_PATCH, mirrored_repo)
    assert selection.convention is not None
    assert selection.convention.sampled > 0


# --- §3.3 tiers ------------------------------------------------------------


def test_tier1_finds_the_corresponding_test(mirrored_repo):
    selection = select_tests(COMPILER_PATCH, mirrored_repo)
    assert "tests/pkg/test_compiler.py::test_as_sql" in selection.by_tier[Tier.DIRECT_CORRESPONDENCE.value]


def test_tier2_finds_the_cross_module_test(mirrored_repo):
    """The ORM case: behaviour changed in one module, exercised from another."""
    selection = select_tests(COMPILER_PATCH, mirrored_repo)
    tier2 = selection.by_tier[Tier.SYMBOL_REFERENCE.value]
    assert "tests/pkg/test_queryset.py::test_queryset_uses_compiler" in tier2
    assert "SQLCompiler" in selection.symbols


def test_enclosing_class_named_only_in_the_hunk_header_is_a_symbol(mirrored_repo):
    """django-16899: a method-body edit names its class only after the second @@."""
    patch = parse_patch("""diff --git a/src/pkg/compiler.py b/src/pkg/compiler.py
index 1..2 100644
--- a/src/pkg/compiler.py
+++ b/src/pkg/compiler.py
@@ -2,2 +2,2 @@ class SQLCompiler:
     def as_sql(self):
-        return ''
+        return 'SELECT 1'
""")
    assert patch.files[0].hunks[0].section == "class SQLCompiler:"
    selection = select_tests(patch, mirrored_repo)
    assert "SQLCompiler" in selection.symbols
    assert ("tests/pkg/test_queryset.py::test_queryset_uses_compiler"
            in selection.by_tier[Tier.SYMBOL_REFERENCE.value])


def test_hunk_header_without_a_definition_adds_no_symbol():
    patch = parse_patch("""diff --git a/a.py b/a.py
index 1..2 100644
--- a/a.py
+++ b/a.py
@@ -10,2 +10,2 @@ default: :rc:`scatter.edgecolors`
-x = 1
+x = 2
@@ -20 +20 @@
-y = 1
+y = 2
""")
    assert [h.section for h in patch.files[0].hunks] == ["default: :rc:`scatter.edgecolors`", ""]
    assert touched_symbols(patch) == ()


def test_unrelated_tests_are_not_selected(mirrored_repo):
    selection = select_tests(COMPILER_PATCH, mirrored_repo)
    assert "tests/pkg/test_unrelated.py::test_nothing" not in selection.tests


# --- the tier cap ----------------------------------------------------------


def test_tier0_is_off_by_default(mirrored_repo):
    """Whole-suite must not run unless explicitly enabled."""
    selection = select_tests(COMPILER_PATCH, mirrored_repo)
    assert Tier.WHOLE_SUITE.value not in selection.by_tier
    assert "tests/pkg/test_unrelated.py::test_nothing" not in selection.tests


def test_tier0_can_be_enabled_by_config_without_code_changes(mirrored_repo):
    """Policy §8 Q1: available later as an ablation, flag-only."""
    selection = select_tests(
        COMPILER_PATCH, mirrored_repo, SelectionConfig(enable_tier0=True))
    assert Tier.WHOLE_SUITE.value in selection.by_tier
    assert "tests/pkg/test_unrelated.py::test_nothing" in selection.tests


def test_default_cap_is_tier2(mirrored_repo):
    selection = select_tests(COMPILER_PATCH, mirrored_repo)
    assert max(selection.by_tier) == Tier.SYMBOL_REFERENCE.value
    assert Tier.CONTAINING_PACKAGE.value not in selection.by_tier


def test_tier3_only_when_max_tier_raised(mirrored_repo):
    selection = select_tests(COMPILER_PATCH, mirrored_repo, SelectionConfig(max_tier=3))
    assert Tier.CONTAINING_PACKAGE.value in selection.by_tier


def test_tier_ordering_puts_strongest_evidence_first(mirrored_repo):
    """Policy §3.4: a budget cut must drop the weakest evidence."""
    selection = select_tests(COMPILER_PATCH, mirrored_repo)
    assert selection.tests[0] == "tests/pkg/test_compiler.py::test_as_sql"
    assert selection.tier_of("tests/pkg/test_compiler.py::test_as_sql") == Tier.DIRECT_CORRESPONDENCE.value


def test_unknown_convention_still_yields_tier2(tmp_path):
    (tmp_path / "odd").mkdir()
    (tmp_path / "odd" / "thing.py").write_text("def frobnicate(): pass\n")
    (tmp_path / "odd" / "test_somewhere.py").write_text(
        "def test_it():\n    frobnicate()\n")
    for i in range(10):
        (tmp_path / "odd" / f"filler{i}.py").write_text("x = 1\n")

    patch = parse_patch("""diff --git a/odd/thing.py b/odd/thing.py
index 1..2 100644
--- a/odd/thing.py
+++ b/odd/thing.py
@@ -1,1 +1,1 @@
-def frobnicate(): pass
+def frobnicate(): return 1
""")
    selection = select_tests(patch, LocalRepoTree(tmp_path))
    assert selection.convention.convention is Convention.UNKNOWN
    assert "odd/test_somewhere.py::test_it" in selection.tests


# --- §5.3 agent-authored tests are excluded -------------------------------


def test_agent_authored_tests_are_excluded(mirrored_repo):
    """The agent must not write its own acceptance criteria."""
    patch = parse_patch("""diff --git a/src/pkg/compiler.py b/src/pkg/compiler.py
index 1..2 100644
--- a/src/pkg/compiler.py
+++ b/src/pkg/compiler.py
@@ -1,3 +1,3 @@
 class SQLCompiler:
     def as_sql(self):
-        return ''
+        return 'SELECT 1'
diff --git a/tests/pkg/test_compiler.py b/tests/pkg/test_compiler.py
index 3..4 100644
--- a/tests/pkg/test_compiler.py
+++ b/tests/pkg/test_compiler.py
@@ -1,2 +1,3 @@
 def test_as_sql():
+    assert SQLCompiler().as_sql() == 'SELECT 1'
     assert True
""")
    selection = select_tests(patch, mirrored_repo)
    assert "tests/pkg/test_compiler.py::test_as_sql" not in selection.tests
    assert "tests/pkg/test_compiler.py::test_as_sql" in selection.excluded_agent_tests


# --- §5.2 nothing to select ------------------------------------------------


def test_patch_touching_only_docs_selects_nothing(mirrored_repo):
    patch = parse_patch("""diff --git a/docs/guide.rst b/docs/guide.rst
index 1..2 100644
--- a/docs/guide.rst
+++ b/docs/guide.rst
@@ -1,1 +1,2 @@
 Guide
+More
""")
    assert select_tests(patch, mirrored_repo).is_empty


# --- §1/§2 the oracle constraint, structurally ----------------------------


def test_select_tests_cannot_be_given_oracle_data():
    """No parameter exists through which PASS_TO_PASS could be supplied."""
    params = set(inspect.signature(select_tests).parameters)
    assert params == {"patch", "tree", "config"}

    forbidden = {"pass_to_pass", "fail_to_pass", "oracle", "gold_patch",
                 "test_patch", "oracle_record"}
    assert not (params & forbidden)

    config_fields = set(SelectionConfig.__dataclass_fields__)
    assert not (config_fields & forbidden)


def test_repo_tree_exposes_no_oracle_surface():
    """The tree interface is files and text; there is no dataset row behind it."""
    surface = {m for m in dir(LocalRepoTree) if not m.startswith("_")}
    assert surface == {"root", "list_files", "read_text"}


def test_selection_is_deterministic(mirrored_repo):
    first = select_tests(COMPILER_PATCH, mirrored_repo)
    for _ in range(3):
        assert select_tests(COMPILER_PATCH, mirrored_repo).tests == first.tests


def test_selection_resolves_to_node_ids_not_module_paths(mirrored_repo):
    selection = select_tests(COMPILER_PATCH, mirrored_repo)
    assert selection.tests
    assert all("::" in test for test in selection.tests)
    assert "tests/pkg/test_compiler.py" not in selection.tests


def test_class_methods_become_class_node_ids(tmp_path):
    text = (
        "class DateFormatTests:\n"
        "    def test_year(self):\n"
        "        assert True\n"
        "    def helper(self):\n"
        "        pass\n"
    )
    assert node_ids("tests/utils_tests/test_dateformat.py", text) == (
        "tests/utils_tests/test_dateformat.py::DateFormatTests::test_year",
    )


def test_discovery_ignores_fixture_strings_and_local_helpers():
    text = '''
class TestCapture:
    def test_fixture(self):
        monkeypatch.setattr("pkg.value", 1)
        source = """
        def test_phantom():
            pass
        """
        @contextlib.contextmanager
        def test_helper():
            yield
        with test_helper():
            pass
    @pytest.mark.parametrize("value", [1, 2])
    def test_family(self, value):
        pass
def test_last():
    pass
'''
    assert node_ids("test_capture.py", text) == (
        "test_capture.py::TestCapture::test_fixture",
        "test_capture.py::TestCapture::test_family",
        "test_capture.py::test_last",
    )


@pytest.mark.parametrize("text", [
    "def test_old():\n    print 'old Python'\n",
    "def test_broken(:\n    pass\n",
    "def test_future[T]():\n    pass\n",
])
def test_discovery_preserves_legacy_candidates_when_parse_is_uncertain(text):
    from reliability.verifier.selection import _legacy_node_candidates

    assert node_ids("test_case.py", text) == tuple(
        tid for _, tid in _legacy_node_candidates("test_case.py", text))


def test_discovery_keeps_exported_local_function():
    text = '''
def factory():
    def test_exported():
        pass
    return test_exported
test_exported = factory()
'''
    assert node_ids("test_case.py", text) == ("test_case.py::test_exported",)


def test_discovery_keeps_dynamic_string_definitions():
    text = '''
exec("""
def test_dynamic():
    pass
""")
'''
    assert node_ids("test_case.py", text) == ("test_case.py::test_dynamic",)


@pytest.mark.parametrize("setup,execute", [
    ("from builtins import exec as execute", "execute"),
    ("import builtins", "builtins.exec"),
    ("import builtins as runtime", "runtime.exec"),
])
def test_discovery_keeps_aliased_dynamic_definitions(setup, execute):
    text = setup + '\n' + execute + '("""\ndef test_dynamic():\n    pass\n""")\n'
    assert node_ids("test_case.py", text) == ("test_case.py::test_dynamic",)


def test_discovery_keeps_explicit_global_binding():
    text = '''
def build_tests():
    global test_created
    def test_created():
        pass
build_tests()
'''
    assert node_ids("test_case.py", text) == ("test_case.py::test_created",)


def test_discovery_preserves_first_occurrence_of_duplicate_real_id():
    text = '''
"""
def test_real():
    pass
"""
def test_middle():
    pass
def test_real():
    pass
'''
    assert node_ids("test_case.py", text) == (
        "test_case.py::test_real", "test_case.py::test_middle", "test_case.py::test_real")


def test_discovery_keeps_tests_in_module_conditionals():
    text = '''
if available:
    def test_optional():
        pass
class TestCase:
    if available:
        def test_method(self):
            pass
'''
    assert node_ids("test_case.py", text) == (
        "test_case.py::test_optional", "test_case.py::TestCase::test_method")


def test_discovered_families_preserve_actual_pytest_collection(tmp_path):
    """Independent runner check: real parametrized cases survive the filter."""
    import os
    import subprocess
    import sys

    source = '''
import pytest
class TestExample:
    @pytest.mark.parametrize("value", [1, 2])
    def test_family(self, value):
        def test_helper():
            return value
        assert test_helper() == value
    def test_fixture(self):
        snippet = """
        def test_fake():
            pass
        """
        assert snippet
def test_last():
    pass
'''
    path = tmp_path / "test_example.py"
    path.write_text(source)
    ids = node_ids(str(path), source)
    environment = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    common = [sys.executable, "-m", "pytest", "-c", "/dev/null", "--collect-only", "-q"]
    whole = subprocess.run([*common, str(path)], capture_output=True, text=True,
                           env=environment, check=False)
    selected = subprocess.run([*common, *ids], capture_output=True, text=True,
                              env=environment, check=False)
    assert whole.returncode == selected.returncode == 0, (whole.stdout, selected.stdout)
    def concrete(output):
        return [line for line in output.splitlines() if "::" in line]
    assert concrete(whole.stdout) == concrete(selected.stdout)
    assert len(concrete(selected.stdout)) == 4


def test_django_label_drops_the_tests_prefix_and_uses_dots():
    node = "tests/utils_tests/test_dateformat.py::DateFormatTests::test_year"
    assert django_label(node) == "utils_tests.test_dateformat.DateFormatTests.test_year"


def test_django_tree_discovers_runtests(tmp_path):
    (tmp_path / "django").mkdir()
    (tmp_path / "tests" / "utils_tests").mkdir(parents=True)
    (tmp_path / "django" / "__init__.py").write_text("")
    (tmp_path / "django" / "utils" / "dateformat.py").parent.mkdir()
    (tmp_path / "django" / "utils" / "dateformat.py").write_text(
        "class DateFormat:\n    def Y(self):\n        return self.data.year\n"
    )
    (tmp_path / "tests" / "runtests.py").write_text("raise SystemExit('runner')\n")
    (tmp_path / "tests" / "utils_tests" / "test_dateformat.py").write_text(
        "class DateFormatTests:\n"
        "    def test_year(self):\n"
        "        assert DateFormat\n"
    )
    tree = LocalRepoTree(tmp_path)
    runner = discover_runner(tree)
    assert runner.name == "django"
    assert "runtests.py" in runner.evidence

    patch = parse_patch("""diff --git a/django/utils/dateformat.py b/django/utils/dateformat.py
index 1..2 100644
--- a/django/utils/dateformat.py
+++ b/django/utils/dateformat.py
@@ -1,3 +1,3 @@
 class DateFormat:
     def Y(self):
-        return self.data.year
+        return '%04d' % self.data.year
""")
    selection = select_tests(patch, tree)
    assert selection.runner is not None and selection.runner.name == "django"
    assert "tests/utils_tests/test_dateformat.py::DateFormatTests::test_year" in selection.tests
    command = selection.runner.command(selection.tests, "/tmp/report.json")
    assert command.startswith("python tests/runtests.py")
    assert "utils_tests.test_dateformat.DateFormatTests.test_year" in command
    assert "pytest" not in command


def test_pytest_config_is_recorded(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "core.py").write_text("def f():\n    return 1\n")
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (tmp_path / "test_core.py").write_text("def test_f():\n    assert True\n")
    runner = discover_runner(LocalRepoTree(tmp_path))
    assert runner.name == "pytest"
    assert "pytest.ini" in runner.evidence


# --- config and code must not drift ---------------------------------------


@pytest.mark.parametrize(
    "config_file", ["configs/verifier/full.yaml", "configs/verifier/baseline.yaml"]
)
def test_shipped_configs_match_code_defaults(config_file):
    """A config saying tier0=false while code defaults true would be invisible."""
    import pathlib

    import yaml

    cfg = yaml.safe_load(pathlib.Path(config_file).read_text())["regression"]
    defaults = SelectionConfig()

    assert cfg["enable_tier0"] == defaults.enable_tier0
    assert cfg["max_tier"] == defaults.max_tier
    assert cfg["exclude_agent_authored_tests"] == defaults.exclude_agent_authored_tests
    assert cfg["convention_sample_size"] == defaults.convention_sample_size
    assert cfg["convention_seed"] == defaults.convention_seed
    assert cfg["consult_pass_to_pass"] is False


@pytest.mark.parametrize(
    "config_file", ["configs/verifier/full.yaml", "configs/verifier/baseline.yaml"]
)
def test_configs_never_enable_pass_to_pass(config_file):
    import pathlib

    import yaml

    raw = pathlib.Path(config_file).read_text()
    cfg = yaml.safe_load(raw)["regression"]
    assert cfg["consult_pass_to_pass"] is False
    assert cfg["outcomes"].count("PASS") == 1  # PASS, not PASS_TO_PASS entries
