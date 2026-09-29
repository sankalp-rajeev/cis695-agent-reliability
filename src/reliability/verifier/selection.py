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

import re
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
    """Test layouts probed by §3.1 convention discovery."""

    SIBLING_TESTS = "sibling_tests"      # pkg/module.py -> pkg/tests/test_module.py
    MIRRORED_TREE = "mirrored_tree"      # src/pkg/module.py -> tests/pkg/test_module.py
    SUFFIX = "suffix"                    # module.py -> module_test.py
    FLAT = "flat"                        # -> tests/test_module.py
    UNKNOWN = "unknown"


#: Below this hit rate across sampled source files, no layout is trusted and
#: selection falls through to Tier 2 only (policy §3.1).
CONVENTION_MIN_HIT_RATE = 0.2


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
    convention_sample_size: int = 40
    exclude_agent_authored_tests: bool = True


@dataclass(frozen=True, slots=True)
class ConventionResult:
    convention: Convention
    hit_rate: float
    sampled: int

    @property
    def is_known(self) -> bool:
        return self.convention is not Convention.UNKNOWN


@dataclass(frozen=True, slots=True)
class Selection:
    """The chosen test set, with why each test was chosen."""

    tests: tuple[str, ...] = ()
    by_tier: dict[int, tuple[str, ...]] = field(default_factory=dict)
    convention: ConventionResult | None = None
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


def _module_name(path: str) -> str:
    return PurePosixPath(path).stem


def _candidate_test_paths(source_path: str, convention: Convention) -> tuple[str, ...]:
    """Where a test for this source file would live under a given layout."""
    p = PurePosixPath(source_path)
    stem, parent = p.stem, p.parent

    if convention is Convention.SIBLING_TESTS:
        return (
            str(parent / "tests" / f"test_{stem}.py"),
            str(parent / "test" / f"test_{stem}.py"),
        )
    if convention is Convention.MIRRORED_TREE:
        parts = list(parent.parts)
        if parts and parts[0] in ("src", "lib"):
            parts = parts[1:]
        mirrored = PurePosixPath("tests", *parts)
        return (str(mirrored / f"test_{stem}.py"),)
    if convention is Convention.SUFFIX:
        return (str(parent / f"{stem}_test.py"),)
    if convention is Convention.FLAT:
        return (f"tests/test_{stem}.py", f"test/test_{stem}.py")
    return ()


def discover_convention(
    tree: RepoTree, config: SelectionConfig | None = None
) -> ConventionResult:
    """Policy §3.1. Determine the repository's test layout empirically.

    Layout varies by project, so it is derived per repository rather than
    hardcoded. The winner and its hit rate are returned for the verification
    record, making the mapping auditable after the fact.
    """
    config = config or SelectionConfig()
    files = tree.list_files()
    file_set = set(files)

    sources = [
        f for f in files
        if f.endswith(".py") and not is_test_file(f) and not f.startswith(".")
    ][: config.convention_sample_size]

    if not sources:
        return ConventionResult(Convention.UNKNOWN, 0.0, 0)

    scores: dict[Convention, int] = {}
    for convention in (Convention.SIBLING_TESTS, Convention.MIRRORED_TREE,
                       Convention.SUFFIX, Convention.FLAT):
        hits = sum(
            1 for src in sources
            if any(c in file_set for c in _candidate_test_paths(src, convention))
        )
        scores[convention] = hits

    best = max(scores, key=lambda c: scores[c])
    hit_rate = scores[best] / len(sources)

    if hit_rate < CONVENTION_MIN_HIT_RATE:
        return ConventionResult(Convention.UNKNOWN, hit_rate, len(sources))
    return ConventionResult(best, hit_rate, len(sources))


def _tier0_whole_suite(tree: RepoTree) -> tuple[str, ...]:
    return tuple(f for f in tree.list_files() if f.endswith(".py") and is_test_file(f))


def _tier1_direct(
    tree: RepoTree, source_paths: tuple[str, ...], convention: ConventionResult
) -> tuple[str, ...]:
    """Policy §3.3 Tier 1: the test file corresponding to each changed source file."""
    if not convention.is_known:
        return ()
    file_set = set(tree.list_files())
    hits = []
    for src in source_paths:
        for candidate in _candidate_test_paths(src, convention.convention):
            if candidate in file_set:
                hits.append(candidate)
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
    return tuple(sorted(hits))


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

    # Union in tier order so the ordering carries relevance: a budget cut removes
    # the weakest evidence rather than an arbitrary slice (policy §3.4).
    ordered: list[str] = []
    seen: set[str] = set()
    excluded: list[str] = []
    for tier in sorted(by_tier):
        for test in by_tier[tier]:
            if test in seen:
                continue
            if config.exclude_agent_authored_tests and test in patch_test_paths:
                excluded.append(test)
                continue
            seen.add(test)
            ordered.append(test)

    return Selection(
        tests=tuple(ordered),
        by_tier={t: tuple(v) for t, v in by_tier.items()},
        convention=convention,
        excluded_agent_tests=tuple(sorted(set(excluded))),
        symbols=symbols,
    )
