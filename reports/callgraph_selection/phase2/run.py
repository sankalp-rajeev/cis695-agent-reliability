"""Run the frozen phase-2 selectors, freeze outputs, then report. No phase 3."""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

from inputs import (HERE, CG, ROOT, PREVIOUS, DESIGN_COMMIT, Registry, sha, dump, csv_write,
                    prepare, base_test_ids, changed_symbols)
from callgraph_selector import (VARIANTS, DEPTHS, BUDGETS, Identities, Traversal, features,
                                rank_candidates, membership, canonical, family)

PROVENANCE_FIELDS = ("record_type", "instance_id", "repo", "source_run", "stratum", "strategy", "edge_variant", "depth",
    "test_id", "graph_status", "rank", "changed_seed", "distance", "distance_bin", "path_nodes", "path_calls",
    "uses_ambiguous_edge", "ambiguous_hop_count", "ambiguous_hop_positions", "reachable_resolved_only_same_depth",
    "applicable_budgets", "test_count", "omitted_seed_paths", "chosen_ambiguous_tests", "requires_ambiguity_tests",
    "selection_reason", "source_identity", "uncertainty_flags")


class Provenance:
    def __init__(self, path):
        self.stream = path.open("w", newline="")
        self.writer = csv.DictWriter(self.stream, PROVENANCE_FIELDS, lineterminator="\n")
        self.writer.writeheader()
        self.full_paths = Counter()
        self.records = Counter()

    def row(self, value):
        self.records[value["record_type"]] += 1
        self.writer.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (list, dict, tuple)) else v
                              for k, v in value.items()})

    def emit(self, identity, candidates, paths, traversal, primary_paths):
        aggregates = defaultdict(Counter)
        for rank, candidate in enumerate(candidates, 1):
            selected_paths = {s: p for s, p in paths.get(candidate["graph_node_id"], {}).items()
                              if len(p.edges) <= identity["depth"]}
            resolved = candidate["reachable_resolved_only_same_depth"]
            ambiguity = any(traversal.edges[e]["status"] == "ambiguous" for p in selected_paths.values() for e in p.edges)
            budgets = membership(rank)
            if rank <= 25:
                chosen = sorted(selected_paths)[:3]
                omitted = max(0, len(selected_paths) - 3)
                if not chosen:
                    self.row(dict(**identity, record_type="TOP_NO_PATH", test_id=candidate["test_id"], rank=rank,
                        graph_status=candidate["graph_status"], applicable_budgets=budgets,
                        reachable_resolved_only_same_depth=resolved, omitted_seed_paths=0,
                        selection_reason="shared_tail", uncertainty_flags=[candidate.get("mapping_reason", "no_path")]))
                for seed in chosen:
                    detail = traversal.provenance(selected_paths[seed])
                    self.full_paths[identity["edge_variant"]] += 1
                    self.row(dict(**identity, **detail, record_type="FULL_PATH", test_id=candidate["test_id"],
                        graph_status=candidate["graph_status"], rank=rank, changed_seed=seed,
                        applicable_budgets=budgets, reachable_resolved_only_same_depth=resolved,
                        omitted_seed_paths=omitted if seed == chosen[0] else 0, selection_reason="frozen_specificity_ranking",
                        uncertainty_flags=["static_only", *( ["ambiguous_candidate_edge"] if detail["uses_ambiguous_edge"] else [])]))
            else:
                distance_bin = candidate["minimum_distance"] or ("unresolved" if candidate["graph_status"] == "unmappable" else "unreachable")
                key = (str(distance_bin), tuple(budgets))
                aggregate = aggregates[key]
                aggregate["test_count"] += 1
                aggregate["omitted_seed_paths"] += len(selected_paths)
                aggregate["chosen_ambiguous_tests"] += ambiguity
                aggregate["requires_ambiguity_tests"] += bool(selected_paths) and not resolved
        for (distance, budgets), counts in sorted(aggregates.items(), key=lambda pair: str(pair[0])):
            self.row(dict(**identity, record_type="AGGREGATE_AFTER_TOP25", distance_bin=distance,
                          applicable_budgets=budgets, **counts, selection_reason="beyond_provenance_cap",
                          uncertainty_flags=["static_only", "aggregate_provenance"]))

    def close(self):
        self.stream.close()
        if any(count > 22_950 for count in self.full_paths.values()):
            raise ValueError("provenance cap exceeded")


def hash_files(paths):
    return {str(p.relative_to(HERE)): sha(p.read_bytes()) for p in sorted(paths) if p.is_file()}


def freeze_code():
    tracked = sorted(HERE.glob("*.py")) + sorted(HERE.glob("*.sh")) + [HERE / "README.md"]
    tracked += [CG / "build_graphs.py", CG / "static_graph.py", ROOT / "reports/v2_diagnostic/oracle_posthoc.py",
                ROOT / "reports/v2_diagnostic/diagnostic.py", ROOT / "src/reliability/verifier/patch.py",
                ROOT / "src/reliability/verifier/selection.py", ROOT / "src/reliability/verifier/integrity.py"]
    return {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in tracked}


def prefix_rows(identity, candidates, stored, outcome):
    rows = []
    all_statuses = Counter(c["graph_status"] for c in candidates) if candidates is not None else None
    for budget in (*BUDGETS, "ALL"):
        chosen = (candidates if budget == "ALL" else candidates[:budget]) if candidates is not None else None
        row = dict(**identity, budget=budget, outcome=outcome, selected_count=len(chosen) if chosen is not None else None,
                   unbudgeted_count=len(candidates) if candidates is not None else None,
                   v2_count=len(stored) if stored is not None else None,
                   v2_same_budget_count=(len(stored) if budget == "ALL" else min(budget, len(stored))) if stored is not None else None)
        for status in ("reachable", "mapped_unreachable", "unmappable"):
            row[status + "_candidate_count"] = all_statuses[status] if all_statuses is not None else None
            row[status + "_selected_count"] = sum(c["graph_status"] == status for c in chosen) if chosen is not None else None
        if chosen is not None:
            for distance in DEPTHS:
                row["distance_" + str(distance) + "_selected_count"] = sum(c["minimum_distance"] == distance for c in chosen)
            row["resolved_only_reachable_selected_count"] = sum(c["reachable_resolved_only_same_depth"] is True for c in chosen)
        if stored is not None and chosen is not None:
            keys = {canonical(c["test_id"], identity["repo"])[0] for c in chosen}
            def hit(raw):
                key = canonical(raw, identity["repo"])[0]
                return bool(key and (key in keys or ("[" in key and family(key) in keys)))
            retained = sum(hit(t) for t in stored)
            row.update(v2_retained_count=retained, v2_retention_fraction=retained / len(stored) if stored else None,
                       original_prefix_overlap_count=sum(hit(t) for t in (stored if budget == "ALL" else stored[:budget])),
                       delta_vs_same_budget_A=len(chosen) - row["v2_same_budget_count"],
                       reduction_vs_same_budget_A=(1 - len(chosen) / row["v2_same_budget_count"]) if row["v2_same_budget_count"] else None)
        rows.append(row)
    return rows


def selectors(registry, prepared):
    manifest, bases = prepared["manifest"], prepared["bases"]
    eligibilities = prepared["eligibility"]["tasks"]
    per_task, graph_rows, specificity_rows = [], [], []
    provenance = Provenance(HERE / "per_test_provenance.csv")
    log = (HERE / "execution.log").open("w")
    with (HERE / "ranked_outputs.jsonl.gz").open("wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as frozen:
        for entry in eligibilities:
            started = time.monotonic()
            iid, repo = entry["instance_id"], entry["repo"]
            record = manifest.get(iid)
            diagnostic = prepared["diagnostics"][iid]
            stored = prepared["selections"].get(iid)
            nodes, edges, parsed_symbols, base_ids = {}, [], [], ()
            identities = None
            seed_ids = set()
            present = entry["graph_build_status"] != "missing"
            if present:
                directory = CG / record["directory"]
                nodes = {n["id"]: n for n in registry.jsonlines(directory / "nodes.jsonl.gz", record["artifact_sha256"]["nodes.jsonl.gz"])}
                edges = registry.jsonlines(directory / "edges.jsonl.gz", record["artifact_sha256"]["edges.jsonl.gz"])
                base_ids, files = base_test_ids(bases[iid], registry)
                for node in nodes.values():
                    if node["kind"] == "module":
                        files[node["path"]] = "parsed"
                for failure in diagnostic["parse_and_resource_failures"]:
                    if failure.get("path"):
                        files[failure["path"]] = "omitted_or_unparseable"
                parsed_symbols = changed_symbols(prepared["patches"][iid], SimpleNamespace(nodes=nodes, files=files))
                seed_ids = {s["targets"][0] for s in parsed_symbols if s["status"] == "resolved"}
                expected_seeds = {json.loads(s["targets"])[0] for s in prepared["seed_symbols"]
                                  if s["instance_id"] == iid and s["status"] == "resolved"}
                if seed_ids != expected_seeds:
                    raise ValueError("fresh parser/extractor disagrees with accepted seed inventory: " + iid)
                identities = Identities(nodes, base_ids, repo)
            can_compute = bool(present and seed_ids and entry["graph_build_status"] in {"complete", "partial"})
            graph_row = dict(instance_id=iid, repo=repo, source_run=entry["source_run"], stratum=entry["stratum"],
                graph_build_status=entry["graph_build_status"], eligibility_reason=entry["eligibility_reason"],
                resolved_seeds=len(seed_ids), ambiguous_seeds=entry["ambiguous_seeds"], unresolved_seeds=entry["unresolved_seeds"],
                graph_directory=record["directory"] if record else None,
                incompleteness_reasons=diagnostic["parse_and_resource_failures"],
                base_test_ids=len(base_ids), distinct_base_ids=len(set(base_ids)),
                represented_base_test_definitions=len(identities.test_definitions) if identities else None,
                uniquely_emittable_base_test_ids=len(identities.emittable) if identities else None,
                base_identity_unmappable_count=sum(identities.lookup(t)["node_id"] is None for t in set(base_ids)) if identities else None,
                nodes=len(nodes), edges=len(edges), edge_status_counts=dict(Counter(e["status"] for e in edges)),
                edge_reason_counts=dict(Counter(e["reason"] for e in edges)),
                graph_build_counts=diagnostic["row"], fresh_patch_symbols=parsed_symbols)
            graph_rows.append(graph_row)
            traversals = {variant: Traversal(nodes, edges, variant) for variant in VARIANTS} if present else {}
            path_sets, fan_ins = {}, {}
            for variant in VARIANTS:
                if can_compute:
                    path_sets[variant], fan_ins[variant] = traversals[variant].test_paths(seed_ids, identities.test_definitions)
                else:
                    path_sets[variant], fan_ins[variant] = {}, {}
            seed_modules = {nodes[s]["module"] for s in seed_ids}
            for variant in VARIANTS:
                traversal = traversals.get(variant)
                paths, fan_in = path_sets[variant], fan_ins[variant]
                if can_compute:
                    for seed in sorted(seed_ids):
                        specificity_rows.append(dict(instance_id=iid, repo=repo, stratum=entry["stratum"], edge_variant=variant,
                            node_id=seed, qualname=nodes[seed]["qualname"], path=nodes[seed]["path"], role="CHANGED_SEED",
                            fan_in_depth3=fan_in[seed], weight=1 / (1 + fan_in[seed]), weight_denominator=1 + fan_in[seed]))
                    # Independent diagnostic only: never adds a seed or ranking feature.
                    hubs = [n for n in nodes.values() if n["path"] == "django/db/models/base.py" and n["qualname"] == "Model.save"]
                    for hub in hubs:
                        hub_fan = sum(n in identities.test_definitions and 1 <= len(p.edges) <= 3
                                      for n, p in traversal.from_seed(hub["id"]).items())
                        specificity_rows.append(dict(instance_id=iid, repo=repo, stratum=entry["stratum"], edge_variant=variant,
                            node_id=hub["id"], qualname=hub["qualname"], path=hub["path"], role="HUB_DIAGNOSTIC_ONLY",
                            fan_in_depth3=hub_fan, weight=1 / (1 + hub_fan), weight_denominator=1 + hub_fan))
                for depth in DEPTHS:
                    strategies = ("A", "B", "C") if stored is not None else ("B",)
                    for strategy in strategies:
                        identity = dict(instance_id=iid, repo=repo, source_run=entry["source_run"], stratum=entry["stratum"],
                            historical_19=stored is not None, strategy=strategy, edge_variant=variant, depth=depth,
                            graph_build_status=entry["graph_build_status"], eligibility_reason=entry["eligibility_reason"],
                            resolved_seeds=len(seed_ids), ambiguous_seeds=entry["ambiguous_seeds"], unresolved_seeds=entry["unresolved_seeds"],
                            patch_sha256=entry["patch_sha256"], graph_directory=record["directory"] if record else None,
                            v2_outcome=entry["v2_outcome"], evaluation_eligible=entry["stratum"] != "EXCLUDED")
                        candidates = None
                        if strategy == "A" or can_compute:
                            candidates = []
                            pool = ([(value, identities.lookup(value)["node_id"] if identities else None, position,
                                      identities.lookup(value) if identities else dict(mapping_reason="missing_graph"))
                                     for position, value in enumerate(stored, 1)] if strategy in {"A", "C"} else
                                    [(raw_id, node, None, identities.lookup(raw_id)) for node, raw_id in identities.emittable.items()])
                            for value, node, position, mapping in pool:
                                row, reachable, score = features(value, node, nodes, seed_modules, paths, fan_in, depth,
                                                                path_sets[VARIANTS[0]], position, mapping)
                                if strategy == "B" and not reachable:
                                    continue
                                candidates.append(row)
                            candidates = rank_candidates(strategy, candidates)
                            outcome = ("EMPTY_REACHABILITY" if strategy == "B" and not candidates else
                                       "SELECTED_DIAGNOSTIC_EXCLUDED" if entry["stratum"] == "EXCLUDED" else "SELECTED")
                            frozen.write((json.dumps(dict(**identity, outcome=outcome, candidates=candidates),
                                                     sort_keys=True, separators=(",", ":")) + "\n").encode())
                            if strategy in {"B", "C"} and traversal:
                                prov_identity = {k: identity[k] for k in ("instance_id", "repo", "source_run", "stratum", "strategy", "edge_variant", "depth")}
                                prov_identity["source_identity"] = dict(base_commit=bases[iid]["base_commit"],
                                    archive_sha256=bases[iid]["archive_sha256"], patch_sha256=entry["patch_sha256"],
                                    nodes_sha256=record["artifact_sha256"]["nodes.jsonl.gz"], edges_sha256=record["artifact_sha256"]["edges.jsonl.gz"])
                                provenance.emit(prov_identity, candidates, paths, traversal, path_sets[VARIANTS[0]])
                        else:
                            outcome = entry["eligibility_reason"]
                        per_task.extend(prefix_rows(identity, candidates, stored, outcome))
            log.write(json.dumps(dict(instance_id=iid, stratum=entry["stratum"], can_compute=can_compute,
                                      seconds=round(time.monotonic() - started, 6))) + "\n")
            log.flush()
            print(iid, entry["stratum"], "done", flush=True)
    provenance.close()
    csv_write(HERE / "per_task.csv", per_task)
    csv_write(HERE / "graph_diagnostics.csv", graph_rows)
    csv_write(HERE / "seed_specificity.csv", specificity_rows)
    dump(HERE / "provenance_counts.json", dict(record_counts=dict(provenance.records), full_paths_by_variant=dict(provenance.full_paths),
        per_variant_upper_bound=22_950, overall_full_path_upper_bound=45_900, top_tests=25, paths_per_test=3, max_hops=3))
    completion = dict(event="SELECTOR_RUN_COMPLETE", tasks=len(graph_rows),
        applicable_B_tasks=sum(r["resolved_seeds"] > 0 and r["graph_build_status"] in {"complete", "partial"} for r in graph_rows),
        stored_A_C_tasks=len(prepared["selections"]))
    log.write(json.dumps(completion, sort_keys=True) + "\n")
    log.close()
    dump(HERE / "selector_completion.json", completion)
    print("SELECTOR_RUN_COMPLETE tasks=" + str(completion["tasks"]), flush=True)


def verify_freeze():
    frozen = json.loads((HERE / "selector_freeze.json").read_text())
    for name, expected in frozen["output_sha256"].items():
        if sha((HERE / name).read_bytes()) != expected:
            raise ValueError("frozen selector output changed: " + name)
    return frozen


def finalize_outputs():
    paths = [p for p in HERE.rglob("*") if p.is_file() and p.name not in {"outputs.sha256.json", "outputs.sha256.json.sha256"}]
    dump(HERE / "outputs.sha256.json", dict(design_commit=DESIGN_COMMIT, output_sha256=hash_files(paths),
        manifest_self_hash="outputs.sha256.json.sha256; self-reference excluded"))
    (HERE / "outputs.sha256.json.sha256").write_text(sha((HERE / "outputs.sha256.json").read_bytes()) + "  outputs.sha256.json\n")


def freeze_outputs():
    """Freeze only after the task log and all selector artifacts are complete."""
    if (HERE / "selector_freeze.json").exists():
        raise ValueError("selector outputs already frozen")
    inputs = json.loads((HERE / "inputs.json").read_text())
    if inputs["code_sha256"] != freeze_code():
        raise ValueError("code changed since completed execution")
    eligibility = json.loads((HERE / "eligibility.json").read_text())
    expected = {t["instance_id"] for t in eligibility["tasks"]}
    progress = [json.loads(line) for line in (HERE / "execution.log").read_text().splitlines()]
    tasks = [r["instance_id"] for r in progress if "instance_id" in r]
    if set(tasks) != expected or len(tasks) != len(expected) or progress[-1].get("event") != "SELECTOR_RUN_COMPLETE":
        raise ValueError("selector execution is incomplete; refusing to hash/freeze outputs")
    if progress[-1]["tasks"] != 83 or progress[-1]["stored_A_C_tasks"] != 19:
        raise ValueError("completion cohort mismatch")
    ef = json.loads((HERE / "eligibility_freeze.json").read_text())
    if ef["sha256"] != sha((HERE / "eligibility.json").read_bytes()):
        raise ValueError("eligibility freeze changed")
    for filename, expected_sha in inputs["input_sha256"].items():
        if sha(Path(filename).read_bytes()) != expected_sha:
            raise ValueError("input changed after execution: " + filename)
    outputs = [HERE / name for name in ("ranked_outputs.jsonl.gz", "per_task.csv", "per_test_provenance.csv",
               "graph_diagnostics.csv", "seed_specificity.csv", "provenance_counts.json", "eligibility.json",
               "eligibility_freeze.json", "inputs.json", "execution.log", "selector_completion.json", "README.md", "incidents.json")]
    outputs += sorted(HERE.glob("background_attempt_*.log"))
    if (HERE / "selector_exit_status.txt").exists():
        if (HERE / "selector_exit_status.txt").read_text().strip() != "0":
            raise ValueError("background process did not exit successfully")
        outputs.append(HERE / "selector_exit_status.txt")
    dump(HERE / "selector_freeze.json", dict(design_commit=DESIGN_COMMIT, code_revision=inputs["code_revision"],
        frozen_before_analysis=True, completion_verified=True, output_sha256=hash_files(outputs), oracle_inputs=False))
    print("SELECTOR OUTPUTS FROZEN", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("execute", "freeze", "select", "report", "all"), default="all")
    args = parser.parse_args()
    if args.stage in {"execute", "select", "all"}:
        if (HERE / "selector_freeze.json").exists():
            raise ValueError("selector outputs are frozen; refusing to overwrite or rerun")
        registry = Registry()
        code = freeze_code()
        prepared = prepare(registry)
        if (HERE / "eligibility.json").exists():
            if json.loads((HERE / "eligibility.json").read_text()) != prepared["eligibility"]:
                raise ValueError("previously frozen eligibility changed")
        else:
            dump(HERE / "eligibility.json", prepared["eligibility"])
        eligibility_freeze = dict(sha256=sha((HERE / "eligibility.json").read_bytes()),
                                  design_commit=DESIGN_COMMIT, frozen_before_selectors=True)
        if (HERE / "eligibility_freeze.json").exists():
            if json.loads((HERE / "eligibility_freeze.json").read_text()) != eligibility_freeze:
                raise ValueError("eligibility freeze changed")
        else:
            dump(HERE / "eligibility_freeze.json", eligibility_freeze)
        selectors(registry, prepared)
        if code != freeze_code():
            raise ValueError("research code changed during selector execution")
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        dump(HERE / "inputs.json", dict(design_commit=DESIGN_COMMIT, code_revision=revision, code_uncommitted=True,
            code_sha256=code, input_sha256=registry.files, depths=DEPTHS, budgets=BUDGETS, variants=VARIANTS,
            oracle_inputs=False, benchmark_execution=False, eligibility_sha256=sha((HERE / "eligibility.json").read_bytes()),
            command="env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/phase2/run.py --stage " + args.stage))
        if args.stage == "execute":
            print("EXECUTION COMPLETE; outputs not yet hashed or frozen", flush=True)
    if args.stage in {"freeze", "select", "all"}:
        freeze_outputs()
    if args.stage in {"report", "all"}:
        verify_freeze()
        from analysis import report
        report()
        verify_freeze()
        finalize_outputs()
        print("Report written; stop for review. No phase 3.", flush=True)


if __name__ == "__main__":
    main()
