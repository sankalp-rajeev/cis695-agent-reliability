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
    without_base_lines,
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
    n_generator = sum(1 for d in task_dirs if d.parent.name == "_reproduction_cache")
    print(f"scope: {len(task_dirs) - n_generator} agent task directories and "
          f"{n_generator} V4 generator directories under {runs_root}")

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

    awareness = result.benchmark_awareness
    if awareness:
        searches = [f for f in awareness if f.kind == "answer-key-search"]
        recalled = [f for f in awareness if f.kind == "benchmark-awareness"]
        print(f"\n{len(recalled)} benchmark-awareness finding(s) and "
              f"{len(searches)} answer-key search(es). The model produced "
              "these field names itself; nothing delivered them. Counted, "
              "and they do not fail the gate.")

    ambiguous = [f for f in result.findings if f.kind == "newer-copy-ambiguous"]
    if ambiguous:
        print(f"\n{len(ambiguous)} newer-copy-ambiguous finding(s). A masked "
              "package path shares the command with another segment that can "
              "produce the output. Counted, and they do not fail the gate.")

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


def lines_present_at_base(instance_id: str, lines: tuple[str, ...]) -> set[str]:
    """Which probe lines already occur in the instance image at the base commit.

    A failure to search does not drop probes. Dropping them on a failed search
    would let a real leak through.
    """
    if not lines:
        return set()
    import subprocess

    from reliability.agent.isolation import docker_bin
    from reliability.verifier.container import image_for

    try:
        proc = subprocess.run(
            [docker_bin(), "run", "--rm", "--cpu-shares", "2048", "--network", "none", "-i",
             "-w", "/testbed", "--entrypoint", "git", image_for(instance_id),
             "grep", "-F", "-I", "-f", "/dev/stdin", "--", "."],
            input="\n".join(lines) + "\n",
            capture_output=True, text=True, errors="replace",
            timeout=180, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"  WARNING: could not search the base tree of {instance_id}: {exc}")
        return set()
    # `git grep` exits 1 with no output when nothing matched. Exit 1 with
    # anything on stderr is a failure that happens to share the code (a missing
    # docker CLI shim does exactly this), and it must not read as "no matches".
    searched = proc.returncode == 0 or (proc.returncode == 1 and not proc.stderr.strip())
    if not searched:
        print(f"  WARNING: base-tree search failed for {instance_id} "
              f"(exit {proc.returncode}): {proc.stderr.strip()[:120]}; probes are not reduced")
        return set()
    found = set()
    for raw in proc.stdout.splitlines():
        content = raw.split(":", 1)[-1]
        for line in lines:
            if line in content:
                found.add(line)
    # `git grep` sees only tracked files. A line can also sit in an installed
    # dependency (numpy's docstring example for __array_ufunc__ did), and an
    # agent that reads that library has not seen the test patch.
    remaining = tuple(line for line in lines if line not in found)
    if remaining:
        found |= lines_in_testbed_site_packages(instance_id, remaining)
    return found


#: The task image's own installed dependencies, as they were before any patch.
#: Vendored copies (`pip/_vendor/requests`, ...) are excluded in the grep: the
#: unmaskable requests copies are newer than the base commit and must still count.
TESTBED_SITE_PACKAGES = "/opt/miniconda3/envs/testbed/lib/python*/site-packages"


def lines_in_testbed_site_packages(instance_id: str, lines: tuple[str, ...]) -> set[str]:
    """Probe lines that occur in the testbed env's site-packages, outside `_vendor`."""
    if not lines:
        return set()
    import subprocess

    from reliability.agent.isolation import docker_bin
    from reliability.verifier.container import image_for

    try:
        proc = subprocess.run(
            [docker_bin(), "run", "--rm", "--cpu-shares", "2048", "--network", "none", "-i",
             "--entrypoint", "bash", image_for(instance_id), "-c",
             "grep -rFIsh --exclude-dir=_vendor -f /dev/stdin -- "
             + TESTBED_SITE_PACKAGES],
            input="\n".join(lines) + "\n",
            capture_output=True, text=True, errors="replace",
            timeout=300, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"  WARNING: could not search site-packages of {instance_id}: {exc}")
        return set()
    # A line grep printed is a real match, even if grep also exited 2 over an
    # unreadable file. With no output, an exit other than 0/1 is a failed search
    # and drops nothing.
    if proc.returncode not in (0, 1) and not proc.stdout:
        print(f"  WARNING: site-packages search failed for {instance_id} "
              f"(exit {proc.returncode}): {proc.stderr.strip()[:120]}; probes are not reduced")
        return set()
    return {line for line in lines if line in proc.stdout}


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
        if task_dir.name in probes:
            continue
        try:
            task, oracle = load_instance(task_dir.name, dataset)
        except KeyError:
            print(f"  WARNING: {task_dir.name} is not in the dataset; "
                  "content checks cannot run for it")
            continue
        # The problem statement is passed in to subtract probes, never to search
        # for: a string the agent was legitimately given cannot evidence a leak.
        built = probes_from_oracle(oracle, task.problem_statement)
        probes[task_dir.name] = without_base_lines(
            built,
            lines_present_at_base(
                task_dir.name, built.patch_lines + built.test_patch_lines),
        )

    return probes, True


def _severity_names() -> tuple[str, ...]:  # pragma: no cover
    return tuple(s.value for s in Severity)


if __name__ == "__main__":
    raise SystemExit(main())
