"""POST-HOC ANALYSIS ONLY. Uses oracle fields (FAIL_TO_PASS, PASS_TO_PASS, gold
test_patch). Must never feed back into any run, policy, or config.

For each V2-failing test in --failing-file, report whether the gold test_patch
rewrites/removes lines in that test (SUPERSEDED), only adds lines, or does not
touch it.

Usage:
  env -u PYTHONPATH .venv/bin/python scripts/old_assertion_check_gold.py \\
      --failing-file reports/failure_analysis/group4_failing_tests.json
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

NOTICE = (
    "POST-HOC ANALYSIS ONLY. This script uses oracle fields (FAIL_TO_PASS, "
    "PASS_TO_PASS, gold test_patch). It must never feed back into any run."
)

_ASSERT_RE = re.compile(
    r"assert\b|self\.assert|pytest\.raises|self\.fail\(|np\.testing\."
)


def test_symbol(node_id: str) -> str:
    if "::" in node_id:
        return node_id.split("::")[-1].split("[")[0].strip()
    if " (" in node_id:
        return node_id.split(" (")[0].strip()
    return node_id.strip()


def file_hint(node_id: str) -> str | None:
    if "::" in node_id:
        return node_id.split("::")[0]
    if " (" in node_id:
        loc = node_id.split(" (", 1)[1].rstrip(")")
        return loc.replace(".", "/") + ".py"
    return None


def parse_test_patch(test_patch: str) -> list[dict]:
    """Split a unified diff into per-file hunks with +/- lines."""
    files: list[dict] = []
    current: dict | None = None
    hunk: dict | None = None
    for raw in test_patch.splitlines():
        if raw.startswith("diff --git "):
            if current is not None:
                if hunk is not None:
                    current["hunks"].append(hunk)
                files.append(current)
            parts = raw.split()
            path = parts[-1][2:] if parts[-1].startswith("b/") else parts[-1]
            current = {"path": path, "hunks": []}
            hunk = None
            continue
        if current is None:
            continue
        if raw.startswith("@@"):
            if hunk is not None:
                current["hunks"].append(hunk)
            hunk = {"header": raw, "removed": [], "added": [], "context": []}
            continue
        if hunk is None:
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            hunk["added"].append(raw[1:])
        elif raw.startswith("-") and not raw.startswith("---"):
            hunk["removed"].append(raw[1:])
        elif raw.startswith(" "):
            hunk["context"].append(raw[1:])
    if current is not None:
        if hunk is not None:
            current["hunks"].append(hunk)
        files.append(current)
    return files


def hunk_mentions_test(hunk: dict, symbol: str) -> bool:
    if not symbol:
        return False
    blob = "\n".join(
        [hunk.get("header", "")]
        + hunk.get("removed", [])
        + hunk.get("added", [])
        + hunk.get("context", [])
    )
    return bool(re.search(rf"\b{re.escape(symbol)}\b", blob))


def file_matches(diff_path: str, hint: str | None, symbol: str) -> bool:
    if hint and (diff_path.endswith(hint) or hint.endswith(diff_path) or hint in diff_path):
        return True
    name = Path(diff_path).name
    if symbol and symbol in name:
        return True
    return False


def classify_test(node_id: str, test_patch: str, f2p: tuple[str, ...], p2p: tuple[str, ...]) -> dict:
    symbol = test_symbol(node_id)
    hint = file_hint(node_id)
    files = parse_test_patch(test_patch)
    touched_hunks: list[dict] = []
    for f in files:
        relevant = file_matches(f["path"], hint, symbol)
        for hunk in f["hunks"]:
            if relevant or hunk_mentions_test(hunk, symbol):
                if relevant and not hunk_mentions_test(hunk, symbol):
                    # File matches but this hunk is a different test in the same file.
                    if any(hunk_mentions_test(h, symbol) for h in f["hunks"]):
                        continue
                touched_hunks.append({"path": f["path"], **hunk})

    minus = [line for h in touched_hunks for line in h["removed"]]
    plus = [line for h in touched_hunks for line in h["added"]]
    minus_assert = [line for line in minus if _ASSERT_RE.search(line)]
    plus_assert = [line for line in plus if _ASSERT_RE.search(line)]

    if not touched_hunks:
        kind = "NOT_TOUCHED"
    elif minus:
        kind = "SUPERSEDED"
    else:
        kind = "ONLY_ADDED"

    in_f2p = any(
        node_id == t or test_symbol(t) == symbol for t in f2p
    )
    in_p2p = any(
        node_id == t or test_symbol(t) == symbol for t in p2p
    )
    membership = (
        "FAIL_TO_PASS" if in_f2p else
        "PASS_TO_PASS" if in_p2p else
        "NEITHER"
    )
    return {
        "test_id": node_id,
        "symbol": symbol,
        "membership": membership,
        "classification": kind,
        "n_hunks": len(touched_hunks),
        "removed_lines": minus,
        "added_lines": plus,
        "removed_assertion_lines": minus_assert,
        "added_assertion_lines": plus_assert,
        "hunk_headers": [h["header"] for h in touched_hunks],
        "paths": sorted({h["path"] for h in touched_hunks}),
    }


def check_task(instance_id: str, failing: list[str]) -> dict:
    _, gold = load_instance(instance_id)
    tests = [
        classify_test(tid, gold.test_patch, gold.fail_to_pass, gold.pass_to_pass)
        for tid in failing
    ]
    if not tests:
        task_class = "NO_FAILING_TESTS"
    elif all(t["classification"] == "SUPERSEDED" for t in tests):
        task_class = "SUPERSEDED_ASSERTION"
    else:
        task_class = "NOT_ALL_SUPERSEDED"
    return {
        "instance_id": instance_id,
        "n_failing": len(failing),
        "task_class": task_class,
        "tests": tests,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--failing-file",
        required=True,
        help='JSON mapping {"<instance_id>": ["test id", ...]}',
    )
    parser.add_argument(
        "--out",
        default=str(REPO / "reports" / "failure_analysis" / "group4_gold_check.json"),
    )
    args = parser.parse_args()

    failing = json.loads(Path(args.failing_file).read_text(encoding="utf-8"))
    print(NOTICE)
    print("=" * 72)
    results = []
    for instance_id, tests in failing.items():
        if instance_id.startswith("_"):
            continue
        row = check_task(instance_id, list(tests))
        results.append(row)
        print(f"\n{instance_id}  {row['task_class']}  n_failing={row['n_failing']}")
        for t in row["tests"]:
            print(f"  {t['test_id']}")
            print(f"    membership={t['membership']}  class={t['classification']}")
            print(f"    paths={t['paths']} hunks={t['n_hunks']}")
            for line in t["removed_lines"][:12]:
                print(f"    - {line}")
            if len(t["removed_lines"]) > 12:
                print(f"    - ... +{len(t['removed_lines']) - 12} more")
            for line in t["added_lines"][:12]:
                print(f"    + {line}")
            if len(t["added_lines"]) > 12:
                print(f"    + ... +{len(t['added_lines']) - 12} more")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({"notice": NOTICE, "tasks": results}, indent=2),
        encoding="utf-8",
    )
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
