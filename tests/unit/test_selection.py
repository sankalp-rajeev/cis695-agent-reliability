"""Phase 5.1 gate: test selection follows VERIFIER_POLICY.md.

The load-bearing property is negative: selection never consults PASS_TO_PASS or
any other oracle field. That is checked structurally here — `select_tests` has no
parameter through which one could be passed.
"""

from __future__ import annotations

import inspect

import pytest

from reliability.verifier.patch import parse_patch
from reliability.verifier.selection import (
    Convention,
    LocalRepoTree,
    SelectionConfig,
    Tier,
    discover_convention,
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
    """Policy §3.1: below the hit-rate floor, fall through to Tier 2 only."""
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
    assert "tests/pkg/test_compiler.py" in selection.by_tier[Tier.DIRECT_CORRESPONDENCE.value]


def test_tier2_finds_the_cross_module_test(mirrored_repo):
    """The ORM case: behaviour changed in one module, exercised from another."""
    selection = select_tests(COMPILER_PATCH, mirrored_repo)
    tier2 = selection.by_tier[Tier.SYMBOL_REFERENCE.value]
    assert "tests/pkg/test_queryset.py" in tier2
    assert "SQLCompiler" in selection.symbols


def test_unrelated_tests_are_not_selected(mirrored_repo):
    selection = select_tests(COMPILER_PATCH, mirrored_repo)
    assert "tests/pkg/test_unrelated.py" not in selection.tests


# --- the tier cap ----------------------------------------------------------


def test_tier0_is_off_by_default(mirrored_repo):
    """Whole-suite must not run unless explicitly enabled."""
    selection = select_tests(COMPILER_PATCH, mirrored_repo)
    assert Tier.WHOLE_SUITE.value not in selection.by_tier
    assert "tests/pkg/test_unrelated.py" not in selection.tests


def test_tier0_can_be_enabled_by_config_without_code_changes(mirrored_repo):
    """Policy §8 Q1: available later as an ablation, flag-only."""
    selection = select_tests(
        COMPILER_PATCH, mirrored_repo, SelectionConfig(enable_tier0=True))
    assert Tier.WHOLE_SUITE.value in selection.by_tier
    assert "tests/pkg/test_unrelated.py" in selection.tests


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
    assert selection.tests[0] == "tests/pkg/test_compiler.py"
    assert selection.tier_of("tests/pkg/test_compiler.py") == Tier.DIRECT_CORRESPONDENCE.value


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
    assert "odd/test_somewhere.py" in selection.tests


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
    assert "tests/pkg/test_compiler.py" not in selection.tests
    assert "tests/pkg/test_compiler.py" in selection.excluded_agent_tests


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
