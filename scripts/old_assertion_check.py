"""Screen v1.3.0 regression/V4 disagreement cases for superseded-assertion overlap.

Uses the post-hoc heuristic from the decisions log: string literals appearing in
the agent patch that also appear in assertion-bearing lines of the gold
test_patch (FAIL_TO_PASS tests). A non-empty overlap supports the old-assertion
story; an empty overlap is inconclusive (known limit for cases like sphinx-10449).

Does not re-run pytest; per-test regression outcomes are not stored on disk.

Usage:
  .venv/bin/python scripts/old_assertion_check.py
  .venv/bin/python scripts/old_assertion_check.py --task django__django-12209
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from reliability.benchmark.loader import load_instance

DEFAULT_TASKS = (
    "pytest-dev__pytest-5809",
    "django__django-12209",
    "django__django-14140",
    "django__django-14631",
    "sphinx-doc__sphinx-10435",
)

# merged main-study source runs (reruns applied)
SOURCE_RUN = {
    "pytest-dev__pytest-5809": "main_50_a",
    "django__django-12209": "main_50_b",
    "django__django-14140": "main_50_b",
    "django__django-14631": "main_50_b",
    "sphinx-doc__sphinx-10435": "main_50_b",
}


def _patch_literals(patch_text: str) -> set[str]:
    lits: set[str] = set()
    for line in patch_text.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        body = line[1:]
        for m in re.finditer(r"""['"]([^'"]{4,})['"]""", body):
            lits.add(m.group(1))
    return lits


def _assertion_lines(test_patch: str) -> list[str]:
    lines: list[str] = []
    for line in test_patch.splitlines():
        if line.startswith("+") and "assert" in line.lower():
            lines.append(line[1:].strip())
    return lines


def _overlap(literals: set[str], assertion_lines: list[str]) -> list[str]:
    hits: list[str] = []
    blob = "\n".join(assertion_lines)
    for lit in sorted(literals, key=len, reverse=True):
        if lit in blob:
            hits.append(lit)
    return hits


def _task_dir(instance_id: str) -> Path:
    run = SOURCE_RUN[instance_id]
    return REPO / "runs" / run / "tasks" / instance_id


def check_one(instance_id: str) -> dict:
    task_dir = _task_dir(instance_id)
    ver = json.loads((task_dir / "verification_record.full.json").read_text(encoding="utf-8"))
    ora = json.loads((task_dir / "oracle_record.json").read_text(encoding="utf-8"))
    patch_text = (task_dir / "patch.diff").read_text(encoding="utf-8", errors="replace")

    _, bench = load_instance(instance_id)
    literals = _patch_literals(patch_text)
    asserts = _assertion_lines(bench.test_patch)
    hits = _overlap(literals, asserts)

    return {
        "instance_id": instance_id,
        "source_run": SOURCE_RUN[instance_id],
        "oracle": ora["outcome"],
        "regression": ver["regression"]["outcome"],
        "reproduction": ver["reproduction"]["outcome"],
        "decision": ver["decision"]["decision"],
        "reasons": ver["decision"]["reasons"],
        "n_fail_to_pass": len(bench.fail_to_pass),
        "n_patch_literals": len(literals),
        "n_gold_assert_added_lines": len(asserts),
        "literal_hits_in_gold_test_patch": hits,
        "screen": (
            "supports_old_assertion"
            if hits
            else "inconclusive_no_literal_overlap_in_gold_test_patch"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task",
        action="append",
        dest="tasks",
        help="instance_id to check (default: the five v1.3.0 disagreement cases)",
    )
    args = parser.parse_args()
    tasks = tuple(args.tasks) if args.tasks else DEFAULT_TASKS

    print("old_assertion_check (literal overlap with gold test_patch assertions)")
    print("=" * 72)
    for iid in tasks:
        row = check_one(iid)
        print(f"\n{row['instance_id']}  run={row['source_run']}")
        print(
            f"  oracle={row['oracle']}  regression={row['regression']}  "
            f"reproduction={row['reproduction']}  decision={row['decision']}"
        )
        print(f"  policy reasons: {'; '.join(row['reasons'])}")
        print(
            f"  FAIL_TO_PASS tests: {row['n_fail_to_pass']}  "
            f"patch literals (len>=4): {row['n_patch_literals']}  "
            f"gold test_patch assert+ lines: {row['n_gold_assert_added_lines']}"
        )
        if row["literal_hits_in_gold_test_patch"]:
            print("  literal hits in gold test_patch:")
            for h in row["literal_hits_in_gold_test_patch"][:8]:
                print(f"    - {h!r}")
            if len(row["literal_hits_in_gold_test_patch"]) > 8:
                print(f"    ... +{len(row['literal_hits_in_gold_test_patch']) - 8} more")
        print(f"  screen: {row['screen']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
