"""Read-only static scientific audit. Benchmark source is archive/AST data only.

Frozen selector sources and outputs are never edited. Rebuild the same pinned
graph with its original limits, compare frozen outputs, then independently
compute resolved-only ancestor distances and strategy-B ranking. Four parallel
audit workers only affect audit cost, never original preparation measurements.
"""
from __future__ import annotations
from collections import Counter, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from fractions import Fraction
import gc
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import traceback


def dump(path, data):
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def ancestors(seed, reverse, max_depth=3):
    distances = {seed: 0}
    witness = {seed: []}
    queue = deque([seed])
    while queue:
        node = queue.popleft()
        if distances[node] == max_depth:
            continue
        for caller, ordinal in reverse.get(node, ()):
            if caller not in distances:
                distances[caller] = distances[node] + 1
                witness[caller] = [ordinal, *witness[node]]
                queue.append(caller)
    return distances, witness


def worker(review, frozen, iid, target):
    sys.path[:0] = [str(review / "src"), str(review / "scripts")]
    import v2_scg_select as selector_worker
    from reliability.verifier.patch import parse_patch
    started = time.monotonic()
    tasks = {t["instance_id"]: t for t in json.loads((frozen / "tasks.json").read_text())}
    task = tasks[iid]
    expected = json.loads((frozen / task["selections"]["scg"]).read_text())
    typeprop, mapper, selector, inputs, builders = selector_worker.load_scg(frozen / "scg_source")
    manifest = json.loads((frozen / "scg_source" / selector_worker.SCG_FILES[-1]).read_text())
    cls = typeprop.TypeAmendedGraph if manifest[iid]["directory"].startswith("amendment2_") else typeprop.TypeGraph
    archive = Path.home() / "cg_repos/task_archives" / (iid + ".tar")
    patch_path = frozen / task["patch_path"]
    assert selector_worker.digest(patch_path) == task["patch_sha256"]
    assert selector_worker.CONFIGURATION == {"strategy":"B", "depth":3, "budget":"ALL", "edge_variant":"PRIMARY_RESOLVED_ONLY"}
    with tempfile.TemporaryDirectory(prefix="readonly-scg-audit-") as temporary:
        root = Path(temporary) / "testbed"
        archive_sha, skipped = builders.extract(dict(archive_path=str(archive), archive_sha256=task["base_archive_sha256"], base_commit=task["base_commit"]), Path(temporary))
        graph = cls().build(root)
        for item in skipped:
            if item["path"].endswith(".py"):
                graph.files[item["path"]] = "omitted_archive_link"
                graph.failures.append(item)
                graph.counts["omitted_files"] += 1
        if graph.status == "complete" and graph.failures:
            graph.status = "partial"
        assert graph.status == expected["graph_status"], (iid, "graph status drift")
        assert dict(graph.counts) == expected["graph_counts"], (iid, "graph count drift")
        assert graph.failures == expected["graph_failures"], (iid, "graph diagnostics drift")
        assert graph.status != "resource_limited"
        registry = inputs.Registry()
        base_ids, _ = inputs.base_test_ids(dict(archive_path=str(archive), archive_sha256=task["base_archive_sha256"], base_commit=task["base_commit"]), registry)
        patch = patch_path.read_text()
        tests, detail = selector_worker.corrected_selection(graph, base_ids, task["repo"], patch, root, mapper, selector)
        assert tests == expected["tests"], (iid, "frozen selector replay drift")
        for key in ("mapping", "mapping_diagnostics", "resolved_seeds", "selection_status"):
            assert detail[key] == expected[key], (iid, key)
        seeds = set(detail["resolved_seeds"])
        assert seeds == {t for r in detail["mapping"] if r["status"] == "resolved" for t in r["targets"]}
        identities = selector.Identities(graph.nodes, base_ids, task["repo"])
        reverse = defaultdict(list)
        for ordinal, edge in enumerate(graph.edges):
            if edge["status"] != "resolved":
                continue
            for callee in sorted(set(edge["targets"])):
                if callee in graph.nodes and edge["caller"] in graph.nodes:
                    reverse[callee].append((edge["caller"], ordinal))
        by_seed, routes = {}, {}
        fan = {}
        test_definitions = identities.test_definitions
        for seed in sorted(seeds):
            distances, witness = ancestors(seed, reverse)
            by_seed[seed], routes[seed] = distances, witness
            fan[seed] = sum(n in test_definitions and 1 <= d <= 3 for n, d in distances.items())
        modules = {graph.nodes[s]["module"] for s in seeds}
        packages = {module.rpartition(".")[0] for module in modules}
        scored = []
        proof = {}
        for node, raw in identities.emittable.items():
            reachable = {s: by_seed[s][node] for s in seeds if node in by_seed[s] and 1 <= by_seed[s][node] <= 3}
            if not reachable:
                continue
            score = sum((Fraction(1, (1 + fan[s]) * distance) for s, distance in reachable.items()), Fraction())
            direct = sum(d == 1 for d in reachable.values())
            minimum = min(reachable.values())
            module = graph.nodes[node]["module"]
            rank_key = (-score, -direct, minimum, -int(module in modules), -int(module.rpartition(".")[0] in packages), raw, raw)
            scored.append((rank_key, raw))
            seed = min(reachable, key=lambda s: (reachable[s], s))
            route = routes[seed][node]
            assert len(route) == reachable[seed] and 1 <= len(route) <= 3
            assert all(graph.edges[o]["status"] == "resolved" for o in route)
            proof[raw] = dict(seed=seed, distance=len(route), path_calls=[{k:graph.edges[o][k] for k in ("caller","targets","status","path","line","column","reason")} for o in route],
                              specificity_score_numerator=score.numerator, specificity_score_denominator=score.denominator)
        independent = [raw for _, raw in sorted(scored)] if seeds else None
        assert independent == tests, (iid, "independent BFS/ranking disagreement")
        if tests is None:
            classification = "NO_BASE_SEEDS_CANDIDATE_ONLY_DEFINITION" if any(r["status"] == "new_definition" for r in detail["mapping"]) else "NO_BASE_SEEDS_EDITS_OUTSIDE_NAMED_DEFINITION"
        elif tests:
            classification = "RESOLVED_DEPTH_1_TO_3_REACHABILITY"
        elif not identities.emittable:
            classification = "NO_UNIQUE_EMITTABLE_BASE_TEST_IDENTITIES"
        elif not any(fan.values()):
            classification = "NO_GRAPH_TEST_DEFINITION_REACHABLE_IN_3_RESOLVED_CALLS"
        else:
            classification = "REACHABLE_TEST_DEFINITIONS_NOT_UNIQUELY_EMITTABLE"
        failure_paths = {r["path"] for r in graph.failures if "path" in r}
        changed_paths = {r.path for r in parse_patch(patch)}
        result = dict(instance_id=iid, passed=True, archive_sha256=archive_sha, graph_status=graph.status,
            graph_counts=dict(graph.counts), graph_failures=graph.failures,
            frozen_output_exactly_reproduced=True, mapping_exactly_reproduced=True,
            independent_resolved_only_depth3_membership_and_order_match=True,
            seed_count=len(seeds), base_raw_test_ids=len(base_ids), graph_test_definitions=len(identities.test_definitions),
            unique_emittable_test_definitions=len(identities.emittable), resolved_edges_considered=sum(e["status"]=="resolved" for e in graph.edges),
            reachable_graph_test_definitions=len({n for ds in by_seed.values() for n,d in ds.items() if n in test_definitions and 1<=d<=3}),
            selected_count=len(tests) if tests is not None else None, tests=tests, classification=classification,
            missing_changed_files=[p for p in changed_paths if not (root / p).exists()],
            graph_failure_changed_path_intersection=sorted(failure_paths & changed_paths),
            mapping_errors=[r for r in detail["mapping"] if r.get("record_kind")=="file_analysis_error"],
            selected_path_proofs=proof, audit_worker_wall_s=time.monotonic()-started,
            benchmark_code_imported=False, benchmark_tests_executed=0)
        dump(target,result)
        del graph
        gc.collect()


def parent(review, frozen, out):
    tasks=json.loads((frozen/"tasks.json").read_text())
    folder=out/"graph_replay"
    folder.mkdir(exist_ok=False)
    env=dict(os.environ,PYTHONPATH=str(review/"src"),PYTHONDONTWRITEBYTECODE="1")
    def run(task):
        iid=task["instance_id"]
        command=[str(review/".venv/bin/python"),"-B",str(Path(__file__).resolve()),"--worker",str(review),str(frozen),iid,str(folder/(iid+".json"))]
        with (folder/(iid+".stdout")).open("x") as stdout,(folder/(iid+".stderr")).open("x") as stderr:
            p=subprocess.run(command,env=env,stdout=stdout,stderr=stderr,check=False)
        if p.returncode:
            return dict(instance_id=iid,passed=False,returncode=p.returncode,stderr=(folder/(iid+".stderr")).read_text()[-3000:])
        return json.loads((folder/(iid+".json")).read_text())
    results=[]
    started=time.monotonic()
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs={pool.submit(run,t):t["instance_id"] for t in tasks}
        for future in as_completed(jobs):
            row=future.result();results.append(row)
            print(json.dumps({"done":len(results),"instance_id":row["instance_id"],"passed":row["passed"],"classification":row.get("classification")}),flush=True)
    results.sort(key=lambda r:r["instance_id"])
    summary=dict(tasks=len(results),passed=sum(r["passed"] for r in results),
        failure_records=[r for r in results if not r["passed"]],
        classifications=dict(Counter(r.get("classification","AUDIT_FAILURE") for r in results)),
        audit_wall_s=time.monotonic()-started,audit_parallel_workers=4,
        original_freeze_and_original_costs_modified=False,benchmark_tests_executed=0,containers_started=0,
        interpretation="Zero reachability means no eligible path in the retained static graph under the frozen policy; graph completeness is not proof of dynamic call completeness.")
    dump(out/"graph_replay_summary.json",summary)
    print(json.dumps(summary),flush=True)
    if summary["passed"]!=83:
        raise SystemExit(1)


if __name__=="__main__":
    if sys.argv[1]=="--worker":
        worker(Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4],Path(sys.argv[5]))
    else:
        parent(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]))
