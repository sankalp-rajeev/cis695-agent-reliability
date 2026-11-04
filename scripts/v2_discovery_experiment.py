"""Reproduce the bounded discovery comparison using candidate/base inputs only.

Writes machine-readable evidence to a new output directory; never reads benchmark
solutions, official test lists, classifier outputs, or graph construction data.
The original selector is loaded from the pinned pre-change Git revision.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import shlex
import subprocess
import sys
import tarfile
import time
import types
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from reliability.verifier import selection as improved
from reliability.verifier.patch import parse_patch

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = "0c0c87f"
ARCHIVES = Path.home() / "cg_repos/task_archives"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def original_selector():
    source = subprocess.check_output(
        ["git", "show", f"{ORIGINAL}:src/reliability/verifier/selection.py"], cwd=ROOT)
    module = types.ModuleType("reliability.verifier._original_selection")
    sys.modules[module.__name__] = module
    # Execute only the pinned, trusted repository module, never candidate code.
    exec(compile(source, f"git:{ORIGINAL}/selection.py", "exec"), module.__dict__)  # noqa: S102
    return module, sha(source)


class ArchiveTree:
    def __init__(self, path):
        self.archive = tarfile.open(path)  # noqa: SIM115 -- caller closes in finally
        self.files = tuple(sorted(m.name.removeprefix("testbed/")
                                 for m in self.archive.getmembers()
                                 if m.name.startswith("testbed/") and not m.isdir()))
        self.cache = {}

    def list_files(self):
        return self.files

    def read_text(self, path):
        if path not in self.cache:
            self.cache[path] = self.archive.extractfile("testbed/" + path).read().decode(
                "utf-8", errors="replace")
        return self.cache[path]


def compare(iid, source, before, tree, old):
    before = tuple(dict.fromkeys(before))
    after, removed, unknown = [], [], []
    per_file = {}
    for tid in before:
        path = tid.split("::", 1)[0]
        if path not in per_file:
            if path not in tree.files:
                per_file[path] = None
            else:
                text = tree.read_text(path)
                old_ids = old.node_ids(path, text)
                new_ids = improved.node_ids(path, text)
                assert tuple(x for x in old_ids if x in set(new_ids)) == new_ids
                # Independent syntax walk for *retained* suspicious candidates.
                # The implementation's conservative exclusions are not used to
                # decide that these IDs are valid or invalid.
                suspicious = {}
                try:
                    syntax = ast.parse(text)
                    nodes = list(ast.walk(syntax))
                    parents = {c: n for n in nodes for c in ast.iter_child_nodes(n)}
                    for n in nodes:
                        if isinstance(n, ast.Constant) and isinstance(n.value, str):
                            for line in range(n.lineno, n.end_lineno + 1):
                                suspicious[line] = "string"
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            parent = parents.get(n)
                            while parent is not None:
                                if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                    suspicious[n.lineno] = "local definition"
                                    break
                                parent = parents.get(parent)
                except (SyntaxError, ValueError, RecursionError):
                    suspicious = {line: "parse uncertainty" for line, _ in
                                  improved._legacy_node_candidates(path, text)}
                occurrences = {}
                for line, candidate in improved._legacy_node_candidates(path, text):
                    occurrences.setdefault(candidate, []).append(line)
                per_file[path] = (text, set(old_ids), set(new_ids), suspicious,
                                  occurrences, improved._phantom_test_lines(text))
        info = per_file[path]
        if info is None or tid not in info[1]:
            after.append(tid)
            unknown.append({"id": tid, "reason": "source unavailable or historical ID not reproduced"})
        elif tid in info[2]:
            after.append(tid)
            occurrences = info[4][tid]
            if occurrences and all(line in info[3] for line in occurrences):
                unknown.append({"id": tid, "reason": "syntactically suspicious but conservatively retained",
                                "lines": occurrences})
        else:
            text = info[0]
            reasons = info[5]
            lines = info[4][tid]
            assert lines and all(line in reasons for line in lines)
            removed.append({"id": tid, "source_sha256": sha(text.encode()),
                            "occurrences": [{"line": line, "reason": reasons[line],
                                             "source": text.splitlines()[line - 1]}
                                            for line in lines]})
    assert after == [tid for tid in before if tid not in {x["id"] for x in removed}]
    return {"instance_id": iid, "source": source, "original": len(before),
            "added": 0, "removed": len(removed), "retained": len(after),
            "before": before, "after": after, "removal_evidence": removed,
            "uncertain_retained": unknown}


def offline(out):
    out.mkdir(parents=True, exist_ok=False)
    old, original_sha = original_selector()
    frozen = ROOT / "reports/v2_scoring_audit/frozen_inputs"
    manifest = json.loads((frozen / "manifest.json").read_text())
    metadata_path = out.parent / "inputs/tasks.json"
    metadata = json.loads(metadata_path.read_text())["tasks"]
    for path, expected in manifest["files_sha256"].items():
        assert sha((frozen.parent / path).read_bytes()) == expected
    export = (ROOT / "frozen_patches_export.tgz").read_bytes()
    assert sha(export) == manifest["candidate_export_sha256"]
    snapshots = []
    for path in [ROOT / "reports/next_steps/v2_projection.json", frozen / "selections.json"]:
        for iid, row in json.loads(path.read_text()).items():
            snapshots.append((iid, str(path.relative_to(ROOT)), row["selected_tests"]))
    # Compare V2 selections only. SCG/import-selector experiments are excluded.
    # Project only selection fields from saved execution records, never outcomes
    # or any other verifier stage. Include distinct historical variants as well.
    for path in sorted((ROOT / "runs").glob("*/tasks/*/verification_record.full.json")):
        row = json.loads(path.read_text())
        iid = row.get("instance_id") or path.parent.name
        snapshots.append((iid, str(path.relative_to(ROOT)), row.get("selected_tests", [])))
    results, historical, unavailable, outside_cohort = [], [], [], []
    with tarfile.open(fileobj=io.BytesIO(export), mode="r:gz") as patches:
        rows = list(csv.DictReader(io.StringIO(
            patches.extractfile("frozen_patches_export/manifest.csv").read().decode())))
        for row in rows:
            iid = row["instance_id"]
            raw_patch = patches.extractfile(f"frozen_patches_export/{iid}.patch").read()
            assert sha(raw_patch) == row["sha256"].removeprefix("sha256:")
            archive = ARCHIVES / f"{iid}.tar"
            if not archive.exists():
                unavailable.append(iid)
                continue
            tree = ArchiveTree(archive)
            try:
                assert tree.archive.pax_headers.get("comment") == metadata[iid]["base_commit"]
                patch = parse_patch(raw_patch.decode())
                before = old.select_tests(patch, tree)
                after = improved.select_tests(patch, tree)
                result = compare(iid, "frozen candidate + base archive", before.tests, tree, old)
                assert tuple(result["after"]) == after.tests
                assert before.symbols == after.symbols
                assert asdict(before.runner) == asdict(after.runner)
                assert asdict(before.convention) == asdict(after.convention)
                for tier, old_ids in before.by_tier.items():
                    new_ids = after.by_tier[tier]
                    assert tuple(t for t in old_ids if t in set(new_ids)) == new_ids
                result.update(runner=asdict(after.runner), convention=asdict(after.convention),
                              before_by_tier=before.by_tier, after_by_tier=after.by_tier)
                result.update(candidate_sha256=sha(raw_patch), archive_sha256=sha(archive.read_bytes()))
                results.append(result)
                for sid, source, tests in snapshots:
                    if sid == iid:
                        record = compare(iid, source, tests, tree, old)
                        record["matches_reconstructed_original"] = tuple(tests) == before.tests
                        historical.append(record)
                print(iid, result["original"], "->", result["retained"], flush=True)
            finally:
                tree.archive.close()
    processed = {r["instance_id"] for r in results}
    for iid, source, tests in snapshots:
        if iid not in processed:
            outside_cohort.append({"instance_id": iid, "source": source,
                                   "selected": len(tests), "reason": "outside frozen archive cohort"})
    hashes = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in
              [ROOT / "src/reliability/verifier/selection.py", Path(__file__),
               ROOT / "src/reliability/verifier/container.py",
               ROOT / "src/reliability/verifier/regression.py"]}
    payload = {"original_revision": ORIGINAL, "original_selector_sha256": original_sha,
               "source_sha256": hashes, "argv": sys.argv, "tasks": results,
               "saved_selections": historical, "unavailable": unavailable,
               "outside_cohort_saved_selections": outside_cohort,
               "metadata_sha256": sha(metadata_path.read_bytes()),
               "selection_config": asdict(improved.SelectionConfig()),
               "candidate_export_sha256": sha(export)}
    assert {r["instance_id"] for r in results} | set(unavailable) == set(metadata)
    assert len(metadata) == 83
    save(out / "offline.json", payload)
    print("OFFLINE", json.dumps({"tasks": len(results),
          "affected": sum(r["removed"] > 0 for r in results),
          "removed": sum(r["removed"] for r in results),
          "retained": sum(r["retained"] for r in results),
          "saved_selections": len(historical), "unavailable": len(unavailable)}), flush=True)


def docker_confirmation(out):
    """AB/BA diagnostic, using production execution and confirmation unchanged."""
    from reliability.verifier.container import (
        ContainerRepoTree,
        ContainerTestExecutor,
        TaskContainer,
    )
    from reliability.verifier.regression import RegressionConfig, run_regression, run_to_dict
    from reliability.verifier.superseded_shadow_v2 import shadow_from_report

    offline_data = json.loads((out / "offline.json").read_text())
    for path, expected in offline_data["source_sha256"].items():
        assert sha((ROOT / path).read_bytes()) == expected, f"changed after offline check: {path}"
    cases = ("pytest-dev__pytest-5809", "pylint-dev__pylint-6528", "pylint-dev__pylint-7277")
    inputs_path = ROOT / "reports/v2_scoring_audit/frozen_inputs"
    inputs = json.loads((inputs_path / "selections.json").read_text())
    selected = {r["instance_id"]: r for r in offline_data["tasks"]}
    issues = json.loads((out.parent / "inputs/tasks.json").read_text())["tasks"]
    schedule = [(iid, pair, arm) for iid in cases
                for pair, arms in ((1, ("A", "B")), (2, ("B", "A"))) for arm in arms]
    protocol = {"argv": sys.argv, "schedule": schedule, "A": "original committed discovery",
                "B": "syntax/scope filter only", "timeout_per_pass_s": 300,
                "baseline_cache": None, "rerun_flaky": True,
                "confirmation": "one patched-only run of all initial regression suspects, 300s; unchanged run_regression",
                "resources": "identical default TaskContainer limits; sequential execution",
                "network": "none", "pull": "never", "created_utc": datetime.now(timezone.utc).isoformat(),  # noqa: UP017
                "offline_sha256": sha((out / "offline.json").read_bytes()),
                "source_sha256": offline_data["source_sha256"]}
    save(out / "docker_protocol.json", protocol)
    real_run = subprocess.run

    def logged_run(argv, *args, **kwargs):
        stdin = kwargs.get("input")
        entry = {"utc": datetime.now(timezone.utc).isoformat(), "argv": list(argv),  # noqa: UP017
                 "timeout_s": kwargs.get("timeout"),
                 "stdin_sha256": sha(stdin.encode() if isinstance(stdin, str) else stdin)
                 if stdin is not None else None}
        with (out / "commands.jsonl").open("a") as stream:
            stream.write(json.dumps(entry) + "\n")
        return real_run(argv, *args, **kwargs)

    class LocalContainer(TaskContainer):
        def run_args(self):
            argv = super().run_args()
            argv.insert(2, "--pull=never")
            return argv

    class MeasuredExecutor:
        def __init__(self, executor):
            self.executor = executor
            self.container = executor.container
            self.calls = []

        def run(self, tests, *, patched, timeout_s):
            started = time.monotonic()
            result = self.executor.run(tests, patched=patched, timeout_s=timeout_s)
            ends = [e for e in result.events if e.get("event") == "end"]
            self.calls.append({"phase": "confirmation" if len(self.calls) >= 2 else
                               ("patched" if patched else "base"),
                               "patched": patched,
                               "wall_s": time.monotonic() - started,
                               "runner_s": sum(e["duration_s"] for e in ends),
                               "launches": len(ends),
                               "exit4": sum(e["returncode"] == 4 for e in ends),
                               "run": run_to_dict(result, inline_raw=False)})
            return result

    subprocess.run = logged_run
    results = []
    try:
        images = {}
        for iid in cases:
            metadata = json.loads(subprocess.check_output(
                ["docker", "image", "inspect", inputs[iid]["study_image_tag"]]))[0]
            prior = json.loads((ROOT / "reports/v2_stabilization/classifier_v2/live/tasks" /
                                iid / "environment.json").read_text())
            assert metadata["Id"] == prior["image_id"], "image drift"
            images[iid] = metadata["Id"]
            save(out / "images" / f"{iid}.json",
                 {k: metadata.get(k) for k in ("Id", "RepoTags", "RepoDigests", "Architecture", "Os")})
        for iid, pair, arm in schedule:
            folder = out / "docker" / iid / f"pair{pair}_{arm}"
            patch = (inputs_path / f"{iid}.patch").read_bytes()
            assert sha(patch) == inputs[iid]["patch_sha256"]
            assert tuple(selected[iid]["before"]) == tuple(inputs[iid]["selected_tests"])
            tests = tuple(selected[iid]["before" if arm == "A" else "after"])
            container = LocalContainer(iid, patch.decode(), image=images[iid],
                                       experiment_id="v2_discovery")
            start = time.monotonic()
            try:
                container.start()
                # Identical preflight for both arms, outside timed execution.
                paths = sorted({t.split("::")[0] for t in selected[iid]["before"]} |
                               {line[6:] for line in patch.decode().splitlines()
                                if line.startswith("+++ b/")})
                with tarfile.open(ARCHIVES / f"{iid}.tar") as archive:
                    hashes = {p: sha(archive.extractfile("testbed/" + p).read()) for p in paths}
                code = ("import hashlib,json,pathlib,subprocess,sys,pytest; "
                        "print(json.dumps({'head':subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),"
                        "'python':sys.version,'pytest':pytest.__version__,"
                        "'hashes':{p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in "
                        + repr(paths) + "}}))")
                rc, raw = container.exec(shlex.join(["python", "-c", code]), timeout_s=30)
                assert rc == 0, raw
                environment = json.loads(raw)
                assert environment["hashes"] == hashes, "base source differs from frozen archive"
                save(folder / "environment.json", {**environment, "image_id": images[iid],
                                                    "patch_sha256": sha(patch),
                                                    "selection_sha256": sha(json.dumps(tests).encode())})
                executor = MeasuredExecutor(ContainerTestExecutor(
                    container, runner=improved.TestRunner(inputs[iid]["runner"], "frozen runner"),
                    evidence_dir=folder / "raw"))
                report = run_regression(iid, improved.Selection(tests=tests), executor,
                                        RegressionConfig(baseline_cache_dir=None))
                initial_calls = len(executor.calls)
                native_signal = report.signal
                shadow = shadow_from_report(
                    report, issues[iid]["problem_statement"], patch.decode(),
                    ContainerRepoTree(container), executor)
                assert report.signal is native_signal, "shadow changed the verdict"
                row = {"instance_id": iid, "pair": pair, "arm": arm, "selected": len(tests),
                       "signal": report.signal.value, "completeness": report.completeness,
                       "regressions": report.regressions, "summary": report.summary,
                       "incompleteness": report.incompleteness, "notes": report.notes,
                       "regression_wall_s": report.duration_s,
                       "container_before_cleanup_s": time.monotonic() - start,
                       "initial_calls": initial_calls, "shadow": shadow,
                       "calls": executor.calls}
                save(folder / "result.json", row)
                for call in executor.calls:
                    for name, path in call["run"]["evidence_files"].items():
                        assert sha(Path(path).read_bytes()) == call["run"]["evidence_sha256"][name]
                expected = ("testing/test_pastebin.py::TestPaste::test_create_new_paste",) if iid == cases[0] else ()
                assert report.regressions == expected, "STOP: known regression detection changed"
                assert report.patched is not None, "STOP: patched pass missing"
                prior = [r for r in results if r["instance_id"] == iid]
                for previous in prior:
                    for phase in (0, 1):
                        current_raw = {r["test_id"]: r["status"] for r in row["calls"][phase]["run"]["raw_results"]}
                        previous_raw = {r["test_id"]: r["status"] for r in previous["calls"][phase]["run"]["raw_results"]}
                        assert current_raw == previous_raw, "STOP: executed tests or outcomes changed"
                results.append(row)
                print("DOCKER", iid, pair, arm, report.signal.value,
                      report.completeness, "calls", len(executor.calls),
                      "seconds", round(report.duration_s, 3), flush=True)
            finally:
                container.stop()
        save(out / "docker_results.json", results)
    finally:
        subprocess.run = real_run


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["offline", "docker"])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "offline":
        offline(args.out)
    else:
        docker_confirmation(args.out)
