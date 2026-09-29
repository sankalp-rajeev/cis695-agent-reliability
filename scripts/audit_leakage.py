"""Phase 8.3: audit every agent prompt and verifier input for oracle data.

ORACLE ACCESS. This script reads ground truth in order to search for it. It is
the one place where doing so is the point. Nothing under `src/reliability/agent`
or the verifier's selection path may import it.

    .venv/bin/python scripts/audit_leakage.py               # all runs
    .venv/bin/python scripts/audit_leakage.py --runs runs/9_pilot
    .venv/bin/python scripts/audit_leakage.py --no-content  # names only, FAILS

Exit codes:
    0  every in-scope artifact scanned, both checks ran, nothing confirmed
    1  confirmed leakage, or the audit could not complete

There is no exit code for "checked some of it". A partial audit is reported as a
failure, because a clean result over an unknown fraction of the artifacts is not
evidence of anything — the same rule that makes `NOT_RUN` an outcome rather than
a silent pass in Phase 5.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from reliability.benchmark.leakage import (
    Severity,
    audit,
    find_task_dirs,
    probes_from_oracle,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", default="runs",
                        help="root to scan (default: runs/)")
    parser.add_argument("--no-content", action="store_true",
                        help="skip dataset-backed content checks; still exits 1, "
                             "because a partial audit is not a pass")
    args = parser.parse_args()

    runs_root = (REPO_ROOT / args.runs).resolve()
    if not runs_root.is_dir():
        print(f"FAIL: no such runs directory: {runs_root}")
        return 1

    task_dirs = find_task_dirs(runs_root)
    print(f"scope: {len(task_dirs)} agent task directories under {runs_root}")

    if not task_dirs:
        print("FAIL: no agent task directories found. An audit that scanned "
              "nothing has not passed — check the runs root.")
        return 1

    probes, content_ok = ({}, False) if args.no_content else load_probes(task_dirs)

    result = audit(task_dirs, probes)

    print(f"scanned: {result.scanned_files} files across "
          f"{result.scanned_tasks} tasks")
    print(f"content-checked: {result.content_checked_tasks}/{result.scanned_tasks} "
          f"tasks against real oracle values")

    for finding in result.findings:
        print(f"  {finding}")

    if result.review:
        print(f"\n{len(result.review)} finding(s) need review. These are not "
              "automatic failures, but each must be explained before the run "
              "is cited.")

    incomplete = (
        not content_ok
        or result.content_checked_tasks < result.scanned_tasks
    )

    if result.confirmed:
        print(f"\nFAIL: {len(result.confirmed)} confirmed leak(s). "
              "This invalidates every result from the affected runs.")
        return 1
    if incomplete:
        print(f"\nFAIL: audit incomplete — content checks ran for "
              f"{result.content_checked_tasks} of {result.scanned_tasks} tasks. "
              "A clean result over part of the artifacts is not a pass.")
        return 1
    if not result.passed:
        print("\nFAIL: audit scanned no files.")
        return 1

    print(f"\nPASS: no oracle data in {result.scanned_files} agent-visible or "
          f"verifier-input artifacts across {result.scanned_tasks} tasks.")
    return 0


def load_probes(task_dirs) -> tuple[dict, bool]:
    """Load the oracle values to search for.

    A dataset failure is a hard failure, not a downgrade to name-only checking.
    The content half is the one that catches a leak which was reformatted on the
    way in, so skipping it would leave the gate reporting clean on exactly the
    case it exists to find.
    """
    try:
        from reliability.benchmark.loader import load_instance, load_verified

        dataset = load_verified()
    except Exception as exc:  # noqa: BLE001 - any failure here fails the gate
        print(f"  could not load the dataset for content checks: {exc}")
        return {}, False

    probes = {}
    for task_dir in task_dirs:
        try:
            task, oracle = load_instance(task_dir.name, dataset)
        except KeyError:
            print(f"  WARNING: {task_dir.name} is not in the dataset; "
                  "content checks cannot run for it")
            continue
        # The problem statement is passed in to subtract probes, never to search
        # for: a string the agent was legitimately given cannot evidence a leak.
        probes[task_dir.name] = probes_from_oracle(oracle, task.problem_statement)

    return probes, True


def _severity_names() -> tuple[str, ...]:  # pragma: no cover
    return tuple(s.value for s in Severity)


if __name__ == "__main__":
    raise SystemExit(main())
