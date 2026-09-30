"""Verifier V2: regression test selection (Phase 5.1).

Implements `docs/VERIFIER_POLICY.md` §3.1 and §3.3. The policy is the
specification; this module is the implementation, and where the two could
diverge the policy wins.

The governing constraint (§1, §2): selection reads only the candidate patch and
the repository tree at the base commit. It never consults `PASS_TO_PASS`,
`FAIL_TO_PASS`, the gold patch, or the gold test patch. That is what makes the
verifier's decision mean anything — a selector that used the benchmark's own
relevance list would be answering a question no deployed system can ask. Nothing
in this module accepts an oracle record, so the constraint holds by construction
rather than by discipline.

**Tier cap.** Selection is capped at Tier 2 by default, per the decision recorded
against policy §8 open question 1. Tier 0 (whole suite) is available behind
`enable_tier0`, defaulted off, so it can be turned on later as an ablation
without touching code. Tier 3 sits behind `max_tier`. Running the whole suite
maximises evidence but also maximises overlap with `PASS_TO_PASS`, making the
regression signal hardest to distinguish from half the oracle's criterion; the
cap buys interpretive cleanliness at the cost of evidential strength.
"""

from __future__ import annotations

import random
import re
import shlex
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Protocol

from reliability.verifier.integrity import is_test_file
from reliability.verifier.patch import Patch, touched_symbols


class Tier(int, Enum):
    """Selection tiers, per policy §3.3. Lower is broader."""

    WHOLE_SUITE = 0
    DIRECT_CORRESPONDENCE = 1
    SYMBOL_REFERENCE = 2
    CONTAINING_PACKAGE = 3


class Convention(str, Enum):
    """Test layouts probed by §3.1 convention discovery.

    Listed most specific first. Discovery breaks a score tie in this order, so
    a layout that names one exact path wins over one that searches.
    """

    SIBLING_TESTS = "sibling_tests"      # pkg/sub/module.py -> pkg/sub/tests/test_module.py, or pkg/tests/
    MIRRORED_TREE = "mirrored_tree"      # src/pkg/module.py -> tests/pkg/test_module.py, or tests/module path
    SUFFIX = "suffix"                    # module.py -> module_test.py
    FLAT = "flat"                        # -> tests/test_module.py, tests/test_sub_module.py
    TESTS_TREE = "tests_tree"            # pkg/area/module.py -> tests/<area>/test_module.py
    UNKNOWN = "unknown"


_PROBED = (Convention.SIBLING_TESTS, Convention.MIRRORED_TREE, Convention.SUFFIX,
           Convention.FLAT, Convention.TESTS_TREE)
_TEST_ROOTS = ("tests", "test")


class RepoTree(Protocol):
    """The repository at the base commit, read-only.

    An interface rather than a path because the real tree lives inside the task
    container while tests run against a local directory. Deliberately narrow: it
    exposes no way to reach a dataset row, so an oracle field cannot be read
    through it even by mistake.
    """

    def list_files(self) -> tuple[str, ...]: ...

    def read_text(self, path: str) -> str: ...


@dataclass(frozen=True, slots=True)
class LocalRepoTree:
    """A RepoTree backed by a directory on disk."""

    root: Path

    def list_files(self) -> tuple[str, ...]:
        return tuple(sorted(
            str(p.relative_to(self.root))
            for p in self.root.rglob("*")
            if p.is_file() and ".git/" not in str(p.relative_to(self.root))
        ))

    def read_text(self, path: str) -> str:
        try:
            return (self.root / path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""


@dataclass(frozen=True, slots=True)
class SelectionConfig:
    """Knobs from configs/verifier/*.yaml.

    Defaults encode the Phase 5 decision: Tier 0 off, cap at Tier 2.
    """

    enable_tier0: bool = False
    max_tier: int = 2
    convention_sample_size: int = 200
    convention_seed: int = 695
    exclude_agent_authored_tests: bool = True


@dataclass(frozen=True, slots=True)
class ConventionResult:
    """The winning layout, its hit rate, and every layout's hit rate.

    There is no hit-rate floor. A weak winner is still the best evidence of how
    the repository is laid out, and ``hit_rate`` is recorded so a reader sees
    how weak it was. Only a layout that located nothing at all is UNKNOWN.
    """

    convention: Convention
    hit_rate: float
    sampled: int
    scores: dict[str, float] = field(default_factory=dict)

    @property
    def is_known(self) -> bool:
        return self.convention is not Convention.UNKNOWN


@dataclass(frozen=True, slots=True)
class TestRunner:
    """How this repository executes a selected test.

    Discovered per repository, the same way the layout convention is. The name
    and the evidence are recorded so a later reader can see why pytest or
    Django's ``tests/runtests.py`` was used.
    """

    name: str
    evidence: str

    def command(self, tests: tuple[str, ...], report_path: str) -> str:
        if self.name == "django":
            labels = " ".join(shlex.quote(django_label(t)) for t in tests)
            return f"python tests/runtests.py --verbosity=2 {labels}"
        targets = " ".join(shlex.quote(t) for t in tests)
        return (
            f"python -m pytest {targets} -p no:cacheprovider -q "
            f"--json-report --json-report-file={report_path} || true"
        )


@dataclass(frozen=True, slots=True)
class Selection:
    """The chosen test set, with why each test was chosen.

    ``tests`` are node ids (``path::test`` or ``path::Class::test``), not
    module paths. A path is not something either runner can execute as one test.
    """

    tests: tuple[str, ...] = ()
    by_tier: dict[int, tuple[str, ...]] = field(default_factory=dict)
    convention: ConventionResult | None = None
    runner: TestRunner | None = None
    excluded_agent_tests: tuple[str, ...] = ()
    symbols: tuple[str, ...] = ()

    def __len__(self) -> int:
        return len(self.tests)

    @property
    def is_empty(self) -> bool:
        return not self.tests

    def tier_of(self, test: str) -> int | None:
        """The strongest (lowest) tier that selected this test."""
        for tier in sorted(self.by_tier):
            if test in self.by_tier[tier]:
                return tier
        return None


@dataclass(frozen=True, slots=True)
class _TreeIndex:
    """The file list, plus test files under a top-level test root by basename."""

    files: frozenset[str]
    by_name: dict[str, tuple[str, ...]]

    @classmethod
    def of(cls, files: tuple[str, ...]) -> _TreeIndex:
        by_name: dict[str, list[str]] = {}
        for f in files:
            p = PurePosixPath(f)
            if len(p.parts) > 1 and p.parts[0] in _TEST_ROOTS and p.suffix == ".py":
                by_name.setdefault(p.name, []).append(f)
        return cls(frozenset(files), {k: tuple(v) for k, v in by_name.items()})


def _module_parts(source_path: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Directory parts and the names a test file could use for this module.

    ``pkg/__init__.py`` is the module ``pkg``. A private module ``_axes.py`` is
    tested as ``test_axes.py`` as often as ``test__axes.py``, so both are tried.
    """
    p = PurePosixPath(source_path)
    parts = list(p.parent.parts)
    stem = p.stem
    if stem == "__init__" and parts:
        stem = parts.pop()
    public = stem.lstrip("_")
    stems = (stem, public) if public and public != stem else (stem,)
    return tuple(parts), stems


def _tokens(parts: tuple[str, ...]) -> set[str]:
    return {
        token for part in parts for token in part.lstrip("_").split("_")
        if token and token not in _TEST_ROOTS
    }


def _candidate_test_paths(source_path: str, convention: Convention) -> tuple[str, ...]:
    """Exact paths a test for this source file would have under a given layout.

    TESTS_TREE is not an exact path and is resolved against the tree in
    `_corresponding_tests` instead.
    """
    parts, stems = _module_parts(source_path)
    out: list[str] = []

    if convention is Convention.SIBLING_TESTS:
        # The nearest enclosing package that has a tests/ directory:
        # sklearn/linear_model/tests/ for sklearn/linear_model/least_angle.py,
        # lib/matplotlib/tests/ for lib/matplotlib/axes/_axes.py.
        for depth in range(len(parts), 0, -1):
            for root in _TEST_ROOTS:
                out.extend(str(PurePosixPath(*parts[:depth], root, f"test_{s}.py")) for s in stems)
    elif convention is Convention.MIRRORED_TREE:
        inner = parts[1:] if parts and parts[0] in ("src", "lib") else parts
        # tests/ mirrors either the package (tests/pkg/sub/) or its inside
        # (seaborn/_core/scales.py -> tests/_core/test_scales.py).
        for mirrored in (inner, inner[1:]) if inner else (inner,):
            for root in _TEST_ROOTS:
                out.extend(str(PurePosixPath(root, *mirrored, f"test_{s}.py")) for s in stems)
    elif convention is Convention.SUFFIX:
        out.extend(str(PurePosixPath(*parts, f"{s}_test.py")) for s in stems)
    elif convention is Convention.FLAT:
        inner = parts[1:] if parts and parts[0] in ("src", "lib") else parts
        for root in _TEST_ROOTS:
            out.extend(f"{root}/test_{s}.py" for s in stems)
            if len(inner) > 1:
                # sphinx/ext/autodoc/typehints.py -> tests/test_ext_autodoc_typehints.py
                joined = "_".join((*inner[1:], stems[-1]))
                out.append(f"{root}/test_{joined}.py")
    return tuple(dict.fromkeys(out))


def _corresponding_tests(
    source_path: str, convention: Convention, index: _TreeIndex
) -> tuple[str, ...]:
    """Existing test files that correspond to one source file under a layout."""
    if convention is not Convention.TESTS_TREE:
        return tuple(c for c in _candidate_test_paths(source_path, convention)
                     if c in index.files)

    # tests/<area>/test_<module>.py, with <area> free: Django's
    # tests/utils_tests/test_dateformat.py, pylint's tests/lint/test_utils.py.
    parts, stems = _module_parts(source_path)
    named = tuple(dict.fromkeys(
        f for s in stems for f in index.by_name.get(f"test_{s}.py", ())))
    if len(named) > 1:
        # A common name (test_utils.py) is a correspondence only where the
        # area shares a word with the source directory. With no such area the
        # match is ambiguous, and an ambiguous match is not a direct one.
        own = _tokens(parts)
        named = tuple(f for f in named
                      if _tokens(PurePosixPath(f).parent.parts[1:]) & own)

    # Django's per-app test packages: django/contrib/admin/checks.py is tested
    # in tests/admin_checks/tests.py.
    packages: list[str] = []
    for root in _TEST_ROOTS:
        for s in stems:
            if parts:
                packages.append(f"{root}/{parts[-1]}_{s}/tests.py")
            packages.append(f"{root}/{s}/tests.py")
    return tuple(dict.fromkeys(
        (*named, *(p for p in packages if p in index.files))))


def discover_convention(
    tree: RepoTree, config: SelectionConfig | None = None
) -> ConventionResult:
    """Policy §3.1. Determine the repository's test layout empirically.

    Layout varies by project, so it is derived per repository rather than
    hardcoded. Source files are sampled at random across the whole tree with a
    fixed seed: a sorted prefix is all ``benchmarks/`` in scikit-learn and all
    ``galleries/`` in matplotlib, and scores a layout the package itself uses
    at zero. The best-scoring layout wins with no floor, and every layout's hit
    rate is returned for the verification record.
    """
    config = config or SelectionConfig()
    files = tree.list_files()
    index = _TreeIndex.of(files)

    sources = sorted(
        f for f in files
        if f.endswith(".py") and not is_test_file(f) and not f.startswith(".")
    )
    if not sources:
        return ConventionResult(Convention.UNKNOWN, 0.0, 0)
    if len(sources) > config.convention_sample_size:
        sources = random.Random(config.convention_seed).sample(
            sources, config.convention_sample_size)

    scores = {
        convention: sum(
            1 for src in sources if _corresponding_tests(src, convention, index)
        ) / len(sources)
        for convention in _PROBED
    }
    # max() keeps the first of equal scores, and _PROBED is most specific first.
    best = max(_PROBED, key=lambda c: scores[c])
    recorded = {c.value: round(rate, 4) for c, rate in scores.items()}
    if scores[best] == 0:
        return ConventionResult(Convention.UNKNOWN, 0.0, len(sources), recorded)
    return ConventionResult(best, scores[best], len(sources), recorded)


def _tier0_whole_suite(tree: RepoTree) -> tuple[str, ...]:
    return tuple(f for f in tree.list_files() if f.endswith(".py") and is_test_file(f))


def _tier1_direct(
    tree: RepoTree, source_paths: tuple[str, ...], convention: ConventionResult
) -> tuple[str, ...]:
    """Policy §3.3 Tier 1: the test file corresponding to each changed source file."""
    if not convention.is_known:
        return ()
    index = _TreeIndex.of(tree.list_files())
    hits = []
    for src in source_paths:
        hits.extend(_corresponding_tests(src, convention.convention, index))
    return tuple(sorted(set(hits)))


def _tier2_symbols(tree: RepoTree, symbols: tuple[str, ...]) -> tuple[str, ...]:
    """Policy §3.3 Tier 2: test files referencing a touched symbol.

    Tier 2 exists because Tier 1 misses the common case where behaviour lives in
    one module and is exercised from another — an ORM compiler change tested
    through a queryset test. Naming convention alone would never find it.

    Textual match on word boundaries. The policy permits import-graph resolution
    where the module parses; text is the documented fallback and is what runs
    here, which over-selects rather than under-selects. For a regression check
    that is the safe direction: a test that need not have run costs time, a test
    that should have run and did not costs a missed regression.
    """
    if not symbols:
        return ()
    pattern = re.compile(r"\b(" + "|".join(re.escape(s) for s in symbols) + r")\b")
    hits = []
    for path in tree.list_files():
        if not path.endswith(".py") or not is_test_file(path):
            continue
        if pattern.search(tree.read_text(path)):
            hits.append(path)

    def rank(path: str) -> tuple:
        # A budget cut drops the tail. Prefer a file whose name contains a
        # touched symbol (DateFormat → test_dateformat) over an alphabetical
        # hit on a one-letter name, so the time is spent on the likely tests.
        low = path.lower()
        named = any(len(symbol) >= 4 and symbol.lower() in low for symbol in symbols)
        return (0 if named else 1, path)

    return tuple(sorted(hits, key=rank))


def _tier3_packages(tree: RepoTree, seeds: tuple[str, ...]) -> tuple[str, ...]:
    """Policy §3.3 Tier 3: the full test package containing any earlier hit."""
    if not seeds:
        return ()
    dirs = {str(PurePosixPath(s).parent) for s in seeds}
    return tuple(sorted(
        f for f in tree.list_files()
        if f.endswith(".py") and is_test_file(f)
        and str(PurePosixPath(f).parent) in dirs
    ))


_CLASS_LINE = re.compile(r"^([ \t]*)class\s+(\w+)")
_TEST_DEF = re.compile(r"^([ \t]*)def\s+(test_\w+)\s*\(")


def _indent(prefix: str) -> int:
    return len(prefix.replace("\t", "    "))


def node_ids(path: str, text: str) -> tuple[str, ...]:
    """Pytest node ids for the test functions in one file.

    A file with no ``test_*`` function contributes nothing. Emitting the bare
    path is what left the executor with a module and no test to run.
    """
    ids: list[str] = []
    classes: list[tuple[int, str]] = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        class_match = _CLASS_LINE.match(line)
        def_match = _TEST_DEF.match(line)
        if class_match:
            indent = _indent(class_match.group(1))
            while classes and classes[-1][0] >= indent:
                classes.pop()
            classes.append((indent, class_match.group(2)))
        elif def_match:
            indent = _indent(def_match.group(1))
            while classes and classes[-1][0] >= indent:
                classes.pop()
            name = def_match.group(2)
            if classes:
                ids.append(f"{path}::{classes[-1][1]}::{name}")
            else:
                ids.append(f"{path}::{name}")
    return tuple(ids)


def node_path(node_id: str) -> str:
    return node_id.split("::", 1)[0]


def django_label(node_id: str) -> str:
    """``tests/utils_tests/test_dateformat.py::DateFormatTests::test_year``
    becomes ``utils_tests.test_dateformat.DateFormatTests.test_year``.
    """
    path, _, rest = node_id.partition("::")
    path = path.removeprefix("tests/")
    module = path[:-3].replace("/", ".") if path.endswith(".py") else path.replace("/", ".")
    if rest:
        return module + "." + rest.replace("::", ".")
    return module


def discover_runner(tree: RepoTree) -> TestRunner:
    """Policy §3.1. Which program runs the tests this repository ships.

    Django does not use pytest. Its runner is ``tests/runtests.py``, and a
    pytest invocation against a Django tree collects nothing useful. Other
    repositories are pytest when they carry pytest configuration, and pytest
    by default when they carry none — that default is recorded as a guess.
    """
    files = set(tree.list_files())
    if "tests/runtests.py" in files and any(
        f == "django/__init__.py" or f.startswith("django/") for f in files
    ):
        return TestRunner(
            "django", "found tests/runtests.py in a Django tree",
        )

    evidence: list[str] = []
    if "pytest.ini" in files or "conftest.py" in files:
        evidence.append("pytest.ini or conftest.py")
    if "pyproject.toml" in files and "[tool.pytest" in tree.read_text("pyproject.toml"):
        evidence.append("[tool.pytest] in pyproject.toml")
    if "setup.cfg" in files and "[tool:pytest]" in tree.read_text("setup.cfg"):
        evidence.append("[tool:pytest] in setup.cfg")
    if "tox.ini" in files and "pytest" in tree.read_text("tox.ini"):
        evidence.append("pytest referenced in tox.ini")
    if evidence:
        return TestRunner("pytest", "; ".join(evidence))
    return TestRunner("pytest", "default; no repo-specific runner found")


def _expand_node_ids(tree: RepoTree, paths: tuple[str, ...]) -> tuple[str, ...]:
    ids: list[str] = []
    for path in paths:
        ids.extend(node_ids(path, tree.read_text(path)))
    return tuple(ids)


def select_tests(
    patch: Patch,
    tree: RepoTree,
    config: SelectionConfig | None = None,
) -> Selection:
    """Choose the regression test set from the patch and the base tree alone.

    Takes no oracle record and no benchmark test lists — there is no parameter
    through which they could be supplied.

    Tests authored or modified by the candidate patch are excluded (§5.3): they
    are the agent's claim about correctness, not independent evidence, and
    admitting them would let the agent write its own acceptance criteria.
    """
    config = config or SelectionConfig()

    patch_test_paths = {f.path for f in patch if is_test_file(f.path)}
    source_paths = tuple(
        f.path for f in patch
        if not is_test_file(f.path) and f.path.endswith(".py") and not f.is_binary
    )

    convention = discover_convention(tree, config)
    symbols = touched_symbols(patch)

    by_tier: dict[int, tuple[str, ...]] = {}

    if config.enable_tier0:
        by_tier[Tier.WHOLE_SUITE.value] = _tier0_whole_suite(tree)

    if config.max_tier >= Tier.DIRECT_CORRESPONDENCE.value:
        by_tier[Tier.DIRECT_CORRESPONDENCE.value] = _tier1_direct(
            tree, source_paths, convention)

    if config.max_tier >= Tier.SYMBOL_REFERENCE.value:
        by_tier[Tier.SYMBOL_REFERENCE.value] = _tier2_symbols(tree, symbols)

    if config.max_tier >= Tier.CONTAINING_PACKAGE.value:
        seeds = tuple(
            by_tier.get(Tier.DIRECT_CORRESPONDENCE.value, ())
        ) + tuple(by_tier.get(Tier.SYMBOL_REFERENCE.value, ()))
        by_tier[Tier.CONTAINING_PACKAGE.value] = _tier3_packages(tree, seeds)

    # Files are an intermediate. What gets executed, recorded, and ordered is
    # the node id of each test function inside those files.
    by_tier = {
        tier: _expand_node_ids(tree, paths) for tier, paths in by_tier.items()
    }
    runner = discover_runner(tree)

    # Union in tier order so the ordering carries relevance: a budget cut removes
    # the weakest evidence rather than an arbitrary slice (policy §3.4).
    ordered: list[str] = []
    seen: set[str] = set()
    excluded: list[str] = []
    for tier in sorted(by_tier):
        for test in by_tier[tier]:
            if test in seen:
                continue
            if config.exclude_agent_authored_tests and node_path(test) in patch_test_paths:
                excluded.append(test)
                continue
            seen.add(test)
            ordered.append(test)

    return Selection(
        tests=tuple(ordered),
        by_tier={t: tuple(v) for t, v in by_tier.items()},
        convention=convention,
        runner=runner,
        excluded_agent_tests=tuple(sorted(set(excluded))),
        symbols=symbols,
    )
