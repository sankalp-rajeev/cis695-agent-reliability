"""Phase 1: offline base-source availability and AST parsing inventory only.

No selectors, traversal, ranking, benchmark imports, oracle reads, or test
execution. Git commands below read only already-local objects, never a worktree.
Missing sources are not replaced with installed packages or code snippets.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "src"))

from reliability.benchmark.manifest import load_manifest

FIELDS = (
    "instance_id", "repo", "source_run", "historical_cohort", "base_commit",
    "source_kind", "source_path", "image_digest", "source_status", "reason",
    "python_files", "parsed_files", "parse_failures", "omitted_files", "source_bytes",
    "ast_nodes", "definitions", "call_sites", "base_python_sha256", "graph_status",
    "changed_symbol_resolution_rate", "resolved_edges", "ambiguous_edges", "unresolved_edges",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_git(root: Path, *args: str, timeout: int = 30) -> bytes:
    env = os.environ.copy()
    env.update(GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0")
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *args],
        env=env, capture_output=True, check=False, timeout=timeout,
    )
    if result.returncode:
        # Do not print remote configuration, environment values, or full errors.
        raise ValueError(f"local git object read failed (exit {result.returncode})")
    return result.stdout


def ast_inventory(root: Path, commit: str) -> tuple[dict, list[dict]]:
    """Read exact base blobs and parse syntax without imports or execution."""
    start = time.monotonic()
    actual = read_git(root, "rev-parse", "--verify", commit + "^{commit}").decode().strip()
    if actual != commit:
        raise ValueError("local base commit verification failed")
    entries = read_git(root, "ls-tree", "-rlz", commit).split(b"\0")
    python = []
    for entry in entries:
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, kind, object_id, size = metadata.split()
        path = raw_path.decode("utf-8", errors="strict")
        if kind == b"blob" and mode in (b"100644", b"100755") and path.endswith(".py"):
            python.append((path, object_id.decode(), int(size)))
    python.sort()
    if len(python) > 50_000:
        raise ValueError("fixed Python-file limit exceeded")
    if sum(size for _, _, size in python) > 512 * 1024 * 1024:
        raise ValueError("fixed total-source-byte limit exceeded")
    counts = {"python_files": len(python), "parsed_files": 0, "parse_failures": 0,
              "omitted_files": 0, "source_bytes": 0, "ast_nodes": 0,
              "definitions": 0, "call_sites": 0}
    failures = []
    digest = hashlib.sha256()
    for path, object_id, size in python:
        if time.monotonic() - start > 600:
            raise ValueError("fixed 600-second static inventory limit exceeded")
        if size > 2 * 1024 * 1024:
            counts["omitted_files"] += 1
            failures.append({"path": path, "reason": "source_blob_over_2_MiB"})
            continue
        payload = read_git(root, "cat-file", "blob", object_id)
        if len(payload) != size:
            raise ValueError("local blob size differs from Git tree metadata")
        counts["source_bytes"] += len(payload)
        digest.update(path.encode() + b"\0" + payload + b"\0")
        try:
            # ast.parse accepts bytes and honors Python source encoding cookies.
            tree = ast.parse(payload, filename=path)
        except (SyntaxError, UnicodeError, ValueError) as exc:
            counts["parse_failures"] += 1
            failures.append({"path": path, "reason": type(exc).__name__,
                             "line": getattr(exc, "lineno", None)})
            continue
        counts["parsed_files"] += 1
        for node in ast.walk(tree):
            counts["ast_nodes"] += 1
            counts["definitions"] += isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            counts["call_sites"] += isinstance(node, ast.Call)
            if (counts["ast_nodes"] > 5_000_000 or counts["definitions"] > 1_000_000
                    or counts["call_sites"] > 2_000_000):
                raise ValueError("fixed AST/definition/call-site limit exceeded")
    counts["base_python_sha256"] = digest.hexdigest()
    return counts, failures


def known_clones(roots: list[Path], repo: str) -> list[Path]:
    owner, name = repo.split("/", 1)
    candidates = []
    for root in roots:
        for relative in (name, repo, owner + "__" + name):
            candidate = root / relative
            if candidate.is_dir() and (candidate / ".git").exists():
                candidates.append(candidate.resolve())
    return sorted(set(candidates))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-sources", type=Path,
                        help="existing CSV: instance_id,source_kind,path,image_digest")
    parser.add_argument("--clone-root", type=Path, action="append", default=[],
                        help="additional existing local clone parent, no fetch/checkout")
    args = parser.parse_args()
    cohort_path = REPO / "reports/v2_diagnostic/patches.csv"
    with cohort_path.open(newline="") as stream:
        # This is an explicit projection of the frozen population/provenance.
        # No oracle fields are used, even for filtering.
        cohort = [{key: row[key] for key in ("instance_id", "repo", "source_run", "artifact_kind")}
                  for row in csv.DictReader(stream)]
    if len(cohort) != 83 or len({r["instance_id"] for r in cohort}) != 83:
        raise ValueError("expected the committed 83-row diagnostic population")
    historical = sum(r["artifact_kind"] == "study_snapshot" for r in cohort)
    if historical != 19:
        raise ValueError("expected the frozen 19-task historical cohort")
    manifest = load_manifest(REPO / "manifests/main_100.csv")
    entries = {r.instance_id: r for r in manifest}
    mappings = {}
    if args.base_sources:
        with args.base_sources.open(newline="") as stream:
            for row in csv.DictReader(stream):
                if row["instance_id"] in mappings:
                    raise ValueError("duplicate explicit base-source mapping")
                if row["source_kind"] not in {"local_clone", "image_extraction"}:
                    raise ValueError("unsupported source kind")
                if row["source_kind"] == "image_extraction" and not row.get("image_digest"):
                    raise ValueError("image extraction needs its recorded immutable image digest")
                mappings[row["instance_id"]] = row
    roots = [REPO.parent, REPO / "base_repos", REPO / "repositories", *args.clone_root]
    rows, errors = [], {}
    for member in cohort:
        entry = entries[member["instance_id"]]
        if entry.repo != member["repo"]:
            raise ValueError("diagnostic and manifest repository disagree")
        row = {field: "" for field in FIELDS}
        row.update(instance_id=entry.instance_id, repo=entry.repo,
                   source_run=member["source_run"], base_commit=entry.base_commit,
                   historical_cohort="confirmed_19" if member["artifact_kind"] == "study_snapshot"
                   else "outside_historical_comparison", source_status="unavailable",
                   reason="no verified local base source found in supplied/conventional locations",
                   graph_status="not_attempted_missing_verified_base")
        explicit = mappings.get(entry.instance_id)
        candidates = ([Path(explicit["path"]).resolve()] if explicit
                      else known_clones(roots, entry.repo))
        for candidate in candidates:
            try:
                counts, failures = ast_inventory(candidate, entry.base_commit)
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                errors.setdefault(entry.instance_id, []).append({"path": str(candidate),
                                                                 "reason": str(exc)[:240]})
                row["source_status"] = "unverified_or_resource_limited"
                row["reason"] = "local source could not pass base-object/static-inventory checks"
                continue
            row.update(counts, source_kind=explicit["source_kind"] if explicit else "local_clone",
                       source_path=str(candidate), image_digest=explicit.get("image_digest", "") if explicit else "",
                       source_status="verified_base_objects",
                       reason="partial syntax inventory" if failures else "AST syntax inventory complete",
                       graph_status="not_implemented_phase_1_source_inventory_only")
            if failures:
                errors.setdefault(entry.instance_id, []).extend(failures)
            break
        rows.append(row)
    inputs = (cohort_path, manifest.path, manifest.path.with_suffix(".csv.sha256"),
              OUT / "design.md", Path(__file__).resolve())
    input_hashes = {str(p): sha(p.read_bytes()) for p in inputs}
    if args.base_sources:
        input_hashes[str(args.base_sources.resolve())] = sha(args.base_sources.read_bytes())
    docker_cli = shutil.which("docker")
    placeholder = None
    if docker_cli:
        try:
            wrapper = Path(docker_cli).read_bytes()[:8192]
            placeholder = b"WSL integration" in wrapper or b"WSL 2 distro" in wrapper
        except OSError:
            pass
    result = {
        "phase": 1, "design_status": "uncommitted_review_draft",
        "command": shlex.join(["env", "-u", "PYTHONPATH", ".venv/bin/python", "-B",
                               "reports/callgraph_selection/feasibility.py", *sys.argv[1:]]),
        "population": len(rows), "confirmed_historical_cohort": historical,
        "source_status_counts": dict(Counter(r["source_status"] for r in rows)),
        "verified_base_snapshots": sum(r["source_status"] == "verified_base_objects" for r in rows),
        "graphs_constructed": 0, "graph_success_rate": None,
        "changed_symbol_resolution_rate": None, "test_execution": "not run",
        "network_data_access": "not used", "docker_extraction": "not attempted",
        "docker_cli_path": docker_cli, "docker_cli_unavailable_wsl_placeholder": placeholder,
        "local_unix_socket_present": Path("/var/run/docker.sock").exists(),
        "clone_roots_checked": [str(p.resolve()) for p in roots],
        "input_sha256": input_hashes, "failures": errors,
        "limitation": "Source/AST feasibility only. No graph or selector success is claimed. "
                      "Docker is inspected locally without contacting an engine or registry; "
                      "this tool never extracts images.",
    }
    with (OUT / "base_feasibility.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "feasibility.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in (
        "population", "confirmed_historical_cohort", "verified_base_snapshots",
        "graphs_constructed", "graph_success_rate", "test_execution")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
