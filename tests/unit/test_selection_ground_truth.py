"""§3.1 convention discovery against the real base trees of the pilot repositories.

The fixtures are `git ls-tree -r --name-only <base_commit>` for nine `pilot_12`
instances, the same list `git ls-files` prints inside each task image. They are
the base tree only, which selection is permitted to read; no oracle field is
involved. `pilot_12` resolved a convention on none of the nine. Each expected
mapping below is where that repository's test for the touched source file
actually lives at the base commit, checked by hand.
"""

from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from reliability.verifier.patch import parse_patch
from reliability.verifier.selection import (
    Convention,
    _corresponding_tests,
    _TreeIndex,
    discover_convention,
    select_tests,
)

FIXTURES = Path(__file__).parent.parent / "fixtures" / "base_trees"

S, M, F, T = (Convention.SIBLING_TESTS, Convention.MIRRORED_TREE,
              Convention.FLAT, Convention.TESTS_TREE)

#: instance -> (layouts that describe the repository, {touched source: its test file}).
#: A test file of None means the repository has no file-level test for that
#: module at the base commit, so Tier 1 correctly finds nothing.
GROUND_TRUTH: dict[str, tuple[set[Convention], dict[str, str | None]]] = {
    "astropy__astropy-12907": (
        {S}, {"astropy/modeling/separable.py": "astropy/modeling/tests/test_separable.py"}),
    "django__django-14373": (
        {T}, {"django/utils/dateformat.py": "tests/utils_tests/test_dateformat.py"}),
    "django__django-16899": (
        {T}, {"django/contrib/admin/checks.py": "tests/admin_checks/tests.py"}),
    "matplotlib__matplotlib-26113": (
        {S}, {"lib/matplotlib/axes/_axes.py": "lib/matplotlib/tests/test_axes.py"}),
    "mwaskom__seaborn-3187": (
        {M, T}, {"seaborn/_core/scales.py": "tests/_core/test_scales.py",
                 "seaborn/utils.py": "tests/test_utils.py"}),
    # One root-level test_requests.py for the whole package: no layout maps a
    # module to it. The repository is the concrete case for Tier 0 (§5.1).
    "psf__requests-1921": (set(), {"requests/sessions.py": None}),
    # tests/lint/test_utils.py for pylint/lint/utils.py; neither touched module
    # has a test file of its own.
    "pylint-dev__pylint-6386": (
        {M, T}, {"pylint/config/utils.py": None, "pylint/lint/base_options.py": None}),
    "scikit-learn__scikit-learn-12973": (
        {S}, {"sklearn/linear_model/least_angle.py":
              "sklearn/linear_model/tests/test_least_angle.py"}),
    # tests/test_ext_autodoc_autoclass.py and friends; typehints is tested from
    # test_ext_autodoc_configs.py, which no layout names.
    "sphinx-doc__sphinx-10449": ({F}, {"sphinx/ext/autodoc/typehints.py": None}),
}


class _FixtureTree:
    def __init__(self, files: tuple[str, ...], texts: dict[str, str] | None = None):
        self._files = files
        self._texts = texts or {}

    def list_files(self) -> tuple[str, ...]:
        return self._files

    def read_text(self, path: str) -> str:
        return self._texts.get(path, "")


def _files(instance: str) -> tuple[str, ...]:
    text = gzip.decompress((FIXTURES / f"{instance}.txt.gz").read_bytes()).decode()
    return tuple(line for line in text.splitlines() if line)


def _discovered(instance: str) -> Convention:
    return discover_convention(_FixtureTree(_files(instance))).convention


def test_discovery_resolves_the_real_layout_on_at_least_seven_of_nine():
    correct = [i for i, (layouts, _) in GROUND_TRUTH.items() if _discovered(i) in layouts]
    assert len(correct) >= 7, f"only {correct}"


@pytest.mark.parametrize("instance", sorted(GROUND_TRUTH))
def test_tier1_maps_each_touched_file_to_its_real_test(instance):
    layouts, mapping = GROUND_TRUTH[instance]
    discovered = _discovered(instance)
    if not layouts:
        pytest.skip("no layout describes this repository")
    index = _TreeIndex.of(_files(instance))
    for source, expected in mapping.items():
        found = _corresponding_tests(source, discovered, index)
        if expected is None:
            assert found == ()
        else:
            assert expected in found


def test_repository_with_no_layout_stays_unknown():
    result = discover_convention(_FixtureTree(_files("psf__requests-1921")))
    assert result.convention is Convention.UNKNOWN
    assert result.hit_rate == 0.0


def test_every_layout_score_is_reported():
    result = discover_convention(_FixtureTree(_files("matplotlib__matplotlib-26113")))
    assert set(result.scores) == {c.value for c in Convention if c is not Convention.UNKNOWN}
    # A weak winner is kept, and its weakness is what the record shows.
    assert result.convention is Convention.SIBLING_TESTS
    assert 0 < result.hit_rate < 0.2


def test_sorted_prefix_sample_would_have_missed_scikit_learn():
    """The pre-v1.1 sample was the first 40 sorted sources: all benchmarks/ and doc/."""
    files = _files("scikit-learn__scikit-learn-12973")
    assert discover_convention(_FixtureTree(files)).convention is Convention.SIBLING_TESTS
    prefix = sorted(f for f in files if f.endswith(".py") and "/tests/" not in f)[:40]
    assert all(not f.startswith("sklearn/") for f in prefix)


def test_discovery_is_deterministic():
    tree = _FixtureTree(_files("django__django-14373"))
    assert discover_convention(tree) == discover_convention(tree)


def test_django_16899_selects_admin_checks():
    """pilot_12 selected nothing for this patch. The real test file is expanded
    to node ids here; every other file reads as empty, so Tier 2 contributes
    only what the real tree would also give it for this patch (nothing)."""
    admin_checks = gzip.decompress(
        (FIXTURES / "django__django-16899.admin_checks_tests.py.gz").read_bytes()).decode()
    tree = _FixtureTree(_files("django__django-16899"),
                        {"tests/admin_checks/tests.py": admin_checks})
    patch = parse_patch((FIXTURES / "django__django-16899.patch").read_text())

    selection = select_tests(patch, tree)

    assert "BaseModelAdminChecks" in selection.symbols
    assert selection.tests
    assert all(t.startswith("tests/admin_checks/tests.py::") for t in selection.tests)
