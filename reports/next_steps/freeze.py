"""Oracle-free, static-only selection experiment. No repository imports/execution.

The mixed snapshot is lexically projected: only identities and V2 signal fields
are decoded. CSV inputs expose whitelisted non-oracle columns only. This program
never opens ceiling_check, grader records, gold patches or official test lists.
"""
import ast
import csv
import gzip
import hashlib
import io
import json
import re
import tarfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CG = ROOT / "reports/callgraph_selection"
AMEND = CG / "amendment2_72ad21b"
INPUTS = {}


def stamp():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, expected=None):
    raw = path.read_bytes()
    digest = sha(raw)
    if expected and digest != expected.removeprefix("sha256:"):
        raise ValueError("hash mismatch: " + str(path))
    INPUTS[str(path)] = digest
    return raw


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(v) if isinstance(v, (dict, list, tuple)) else v for k, v in r.items()})


def whitespace(text, offset):
    while offset < len(text) and text[offset].isspace():
        offset += 1
    return offset


def skip_json(text, offset):
    offset = whitespace(text, offset)
    if text[offset] == '"':
        offset += 1
        while text[offset] != '"':
            offset += 2 if text[offset] == "\\" else 1
        return offset + 1
    if text[offset] in "[{":
        end = "]" if text[offset] == "[" else "}"
        offset += 1
        while True:
            offset = whitespace(text, offset)
            if text[offset] == end:
                return offset + 1
            if text[offset] in ",:":
                offset += 1
            else:
                offset = skip_json(text, offset)
    while offset < len(text) and text[offset] not in ",]} \r\n\t":
        offset += 1
    return offset


def object_items(text, offset):
    decoder = json.JSONDecoder()
    offset = whitespace(text, offset)
    if text[offset] != "{":
        raise ValueError("expected object")
    offset += 1
    while True:
        offset = whitespace(text, offset)
        if text[offset] == "}":
            return
        if text[offset] == ",":
            offset = whitespace(text, offset + 1)
        key, offset = decoder.raw_decode(text, offset)
        offset = whitespace(text, offset)
        if text[offset] != ":":
            raise ValueError("expected separator")
        offset = whitespace(text, offset + 1)
        yield key, offset
        offset = skip_json(text, offset)


def snapshot_projection():
    text = read(ROOT / "reports/failure_analysis/extracted.json").decode()
    decoder = json.JSONDecoder()
    records = {}
    line = lambda pos: text.count("\n", 0, pos) + 1
    for key, pos in object_items(text, 0):
        if key != "tasks":
            continue
        pos += 1
        while True:
            pos = whitespace(text, pos)
            if text[pos] == "]":
                break
            if text[pos] == ",":
                pos = whitespace(text, pos + 1)
            record = {"source_lines": {}}
            for field, start in object_items(text, pos):
                if field in {"instance_id", "source_run"}:
                    record[field] = decoder.raw_decode(text, start)[0]
                elif field == "signals":
                    for name, value in object_items(text, start):
                        if name in {"regression", "selected_tests", "selection_convention"}:
                            record[name] = decoder.raw_decode(text, value)[0]
                            record["source_lines"][name] = line(value)
                            if name == "regression":
                                for k, v in object_items(text, value):
                                    record["source_lines"]["regression." + k] = line(v)
                # All other fields are skipped, never decoded.
            records[record["instance_id"]] = record
            pos = skip_json(text, pos)
    return records


def diagnostics_projection():
    fields = ("instance_id", "repo", "source_run", "v2_outcome", "artifact_kind",
              "total_selected_tests", "number_executed", "number_timed_out",
              "number_pre_existing_failures", "number_not_run", "v2_runtime_s",
              "not_available_reason", "changed_source_files")
    return {r["instance_id"]: {k: r[k] for k in fields}
            for r in csv.DictReader(io.StringIO(read(ROOT / "reports/v2_diagnostic/patches.csv").decode()))}


def module_name(path):
    parts = path.removesuffix(".py").split("/")
    if parts[0] in {"src", "lib"}:
        parts = parts[1:]
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def archive_index(archive_path, repo, expected_commit):
    """Pure AST import relations and static test definitions; no dynamic imports."""
    sources = {}
    raw = read(archive_path)
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as tar:
        if tar.pax_headers.get("comment") != expected_commit:
            raise ValueError("archive base commit mismatch")
        for member in tar:
            if member.isfile() and member.name.startswith("testbed/") and member.name.endswith(".py"):
                sources[member.name[8:]] = tar.extractfile(member).read().decode("utf-8", errors="replace")
    aliases = defaultdict(set)
    for path in sources:
        name = module_name(path)
        aliases[name].add(path)
        if repo == "django/django" and name.startswith("tests."):
            aliases[name[6:]].add(path)
    imports, tests, errors = defaultdict(set), {}, []
    for path, source in sources.items():
        try:
            tree = ast.parse(source)
        except (SyntaxError, ValueError, RecursionError) as exc:
            errors.append({"path": path, "kind": type(exc).__name__, "line": getattr(exc, "lineno", None)})
            continue
        current = module_name(path).split(".")
        package = current if path.endswith("/__init__.py") else current[:-1]
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    if node.level > len(package):
                        continue
                    prefix = package[:len(package) - node.level + 1]
                    if node.module:
                        prefix += node.module.split(".")
                    parent = ".".join(prefix)
                else:
                    parent = node.module or ""
                names = [parent] + [parent + "." + a.name for a in node.names if a.name != "*"]
            for name in names:
                # Preserve all exact alias candidates; no generic name/tail fallback.
                imports[path].update(aliases.get(name, ()))
        path_tests = []
        is_test = any(p in {"tests", "test"} for p in path.split("/")[:-1]) or Path(path).name.startswith("test_") or Path(path).name.endswith("_test.py")
        if is_test:
            def visit(body, classes=()):
                for n in body:
                    if isinstance(n, ast.ClassDef):
                        visit(n.body, classes + (n.name,))
                    elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_"):
                        path_tests.append(path + "::" + "::".join(classes + (n.name,)))
            visit(tree.body)
        if path_tests:
            tests[path] = sorted(set(path_tests))
    return imports, tests, errors, {k: sorted(v) for k, v in aliases.items() if len(v) > 1}


def reverse_reach(reverse, seeds, depth):
    seen, front = set(seeds), set(seeds)
    for _ in range(depth):
        following = {caller for target in front for caller in reverse.get(target, ())} - seen
        seen |= following
        front = following
    return seen


def select_imports(imports, tests, paths, depth):
    reverse = defaultdict(set)
    for caller, targets in imports.items():
        for target in targets:
            reverse[target].add(caller)
    # Import distance must be positive: same-file tests are not importers of themselves.
    reached = reverse_reach(reverse, paths, depth) - set(paths)
    modules = sorted(reached & tests.keys())
    return sorted({tid for p in modules for tid in tests[p]}), modules


def graph_select(nodes, edges, symbols, tests, ambiguous):
    seeds = {t for s in symbols if s["status"] == "resolved" for t in json.loads(s["targets"])}
    reverse = defaultdict(set)
    for e in edges:
        if e["status"] == "resolved" or ambiguous and e["status"] == "ambiguous":
            for target in e["targets"]:
                reverse[target].add(e["caller"])
    reached = reverse_reach(reverse, seeds, 3) - seeds
    inventory = {tid for tids in tests.values() for tid in tids}
    ids = set()
    for n in nodes:
        if n["id"] in reached and n["kind"] in {"test_function", "test_method"}:
            tid = n["path"] + "::" + n["qualname"].replace(".", "::")
            if tid in inventory:
                ids.add(tid)
    return sorted(ids), sorted({t.split("::")[0] for t in ids}), sorted(seeds)


def main():
    frozen = OUT / "frozen_selections"
    if (frozen / "manifest.json").exists():
        raise SystemExit("Frozen manifest already exists; refusing to alter outputs after freeze")
    frozen.mkdir(parents=True, exist_ok=True)
    started = stamp()
    meta = diagnostics_projection()
    missing = [iid for iid, r in meta.items() if r["v2_outcome"] not in {"PASS", "FAIL", "NOT_AVAILABLE"}]
    if missing:
        dump(OUT / "missing_v2_outcomes.json", missing)
        raise SystemExit("Missing V2 outcomes; stopped")
    snapshots = snapshot_projection()
    dump(OUT / "v2_projection.json", snapshots)
    dump(OUT / "nonoracle_metadata.json", meta)
    na = []
    for iid, r in meta.items():
        if r["v2_outcome"] != "NOT_AVAILABLE":
            continue
        rec = snapshots.get(iid)
        local = ROOT / "runs" / r["source_run"] / "tasks" / iid / "verification_record.full.json"
        if rec is None and local.is_file():
            v = json.loads(read(local))
            rec = {k: v[k] for k in ("regression", "selected_tests") if k in v}
        reg = rec.get("regression", {}) if rec else {}
        summary = reg.get("findings", {}).get("summary", {})
        detail = reg.get("detail", "")
        selected = rec.get("selected_tests") if rec else None
        if selected == [] and "no tests selected" in detail:
            group = "selection-related"
        elif summary.get("TIMEOUT", 0) and not reg.get("findings", {}).get("n_executed"):
            group = "timeout"
        elif "No module named pytest" in detail or "runner" in detail.lower() and "not installed" in detail.lower():
            group = "runner"
        elif "collection" in detail.lower() or "collect" in detail.lower():
            group = "collection"
        else:
            group = "unknown"
        na.append({"instance_id": iid, "source_run": r["source_run"], "v2_outcome": "NOT_AVAILABLE",
                   "group": group, "group_status": "inferred", "selected_count": len(selected) if selected is not None else None,
                   "recorded_summary": summary, "recorded_detail": detail,
                   "evidence": f"reports/failure_analysis/extracted.json:{rec['source_lines']['regression']}" if rec and "source_lines" in rec else str(local.relative_to(ROOT)) if local.exists() else "headline label only; detailed V2 record absent"})
    write_csv(OUT / "no_result_groups.csv", na)
    large = {iid for iid, r in meta.items() if r["total_selected_tests"] and int(r["total_selected_tests"]) >= 1000}
    # Fixed user-requested supplemental cohort from the preceding task, not discovered from labels here.
    supplemental = {"pylint-dev__pylint-6528", "pylint-dev__pylint-7277", "django__django-13297", "matplotlib__matplotlib-25479"}
    selection_na = {r["instance_id"] for r in na if r["group"] == "selection-related"}
    cases = sorted(large | selection_na | supplemental)
    manifest = json.loads(read(AMEND / "graph_manifest.json"))
    symbols = list(csv.DictReader(io.StringIO(read(AMEND / "changed_symbol_resolution.csv").decode())))
    acquisition = json.loads(read(CG / "inputs.json"))
    bases = {r["instance_id"]: r for r in acquisition["tasks"]}
    pv = json.loads(read(AMEND / "patch_verification.json"))
    raw_export = read(Path(pv["export_path"]), pv["export_sha256"])
    patch_meta = {r["instance_id"]: r for r in csv.DictReader(io.StringIO(read(AMEND / "verified_patch_manifest.csv").decode()))}
    patches = {}
    with tarfile.open(fileobj=io.BytesIO(raw_export), mode="r:gz") as tar:
        for iid in cases:
            raw = tar.extractfile("frozen_patches_export/" + iid + ".patch").read()
            if sha(raw) != patch_meta[iid]["patch_sha256"].removeprefix("sha256:"):
                raise ValueError("candidate hash mismatch")
            if patch_meta[iid]["source_run"] != meta[iid]["source_run"]:
                raise ValueError("candidate run mismatch")
            patches[iid] = raw.decode()
    sizes, files, inventories, case_rows = [], {}, {}, []
    for iid in cases:
        r = meta[iid]
        paths = sorted(set(re.findall(r"^\+\+\+ b/(.*\.py)$", patches[iid], re.M)))
        # Only candidate production files. Patch test edits are not selector seeds.
        paths = [p for p in paths if not any(x in {"tests", "test"} for x in p.split("/")[:-1]) and not Path(p).name.startswith("test_")]
        archive_path = Path(bases[iid]["archive_path"])
        imports, tests, errors, aliases = archive_index(archive_path, r["repo"], bases[iid]["base_commit"])
        if INPUTS[str(archive_path)] != bases[iid]["archive_sha256"]:
            raise ValueError("archive acquisition hash mismatch")
        gm = manifest[iid]
        gp = CG / gm["directory"]
        nodes = [json.loads(line) for line in gzip.decompress(read(gp / "nodes.jsonl.gz", gm["artifact_sha256"]["nodes.jsonl.gz"])).splitlines()]
        edges = [json.loads(line) for line in gzip.decompress(read(gp / "edges.jsonl.gz", gm["artifact_sha256"]["edges.jsonl.gz"])).splitlines()]
        gd = json.loads(read(gp / "diagnostics.json", gm["artifact_sha256"]["diagnostics.json"]))
        ss = [s for s in symbols if s["instance_id"] == iid]
        outputs = {}
        for depth in (1, 2):
            ids, modules = select_imports(imports, tests, paths, depth)
            outputs[f"import_depth{depth}"] = (ids, modules)
        for ambiguous in (False, True):
            ids, modules, seeds = graph_select(nodes, edges, ss, tests, ambiguous)
            outputs["graph_depth3_" + ("resolved_plus_ambiguous" if ambiguous else "resolved_only")] = (ids, modules)
        inventories[iid] = {"tests_by_module": tests, "base_commit": bases[iid]["base_commit"],
                            "ast_parse_failures": errors, "duplicate_module_aliases": aliases,
                            "resolved_seed_ids": seeds, "changed_production_paths": paths,
                            "graph_diagnostics": gd}
        for selector, (ids, modules) in outputs.items():
            payload = {"instance_id": iid, "source_run": r["source_run"], "selector": selector,
                       "test_ids": ids, "modules": modules, "changed_production_paths": paths,
                       "status": "inferred", "oracle_inputs": False}
            target = frozen / iid / (selector + ".json")
            target.parent.mkdir(exist_ok=True)
            dump(target, payload)
            files[str(target.relative_to(OUT))] = sha(target.read_bytes())
            timedout = int(r["number_timed_out"] or 0)
            proportional = float(r["v2_runtime_s"]) * len(ids) / int(r["total_selected_tests"]) if r["v2_runtime_s"] and r["total_selected_tests"] and not timedout else None
            sizes.append({"instance_id": iid, "selector": selector, "test_count": len(ids),
                          "module_count": len(modules), "thousands_flag": len(ids) >= 1000,
                          "graph_status": gm["graph_status"], "archive_ast_parse_failures": len(errors),
                          "baseline_v2_selected": r["total_selected_tests"], "baseline_v2_duration_s": r["v2_runtime_s"],
                          "proportional_runtime_proxy_s": round(proportional, 6) if proportional is not None else None,
                          "runtime_note": "not estimated: timeout-censored baseline" if timedout else "aggregate-duration proportional proxy; includes setup/cache; no execution prediction",
                          "status": "inferred"})
        case_rows.append({"instance_id": iid, "source_run": r["source_run"], "large_selection": iid in large,
                          "selection_related_no_result": iid in selection_na, "supplemental_opportunity_cohort": iid in supplemental,
                          "changed_paths": paths, "graph_directory": str(gp.relative_to(ROOT)), "graph_status": gm["graph_status"],
                          "ast_parse_failures": len(errors), "status": "inferred"})
        print(iid, {k: len(v[0]) for k, v in outputs.items()}, flush=True)
    dump(OUT / "base_inventory.json", inventories)
    write_csv(OUT / "selector_sizes.csv", sizes)
    write_csv(OUT / "case_cohort.csv", case_rows)
    read(Path(__file__).resolve())
    dump(OUT / "step_a_inputs.json", INPUTS)
    for path in (OUT / "base_inventory.json", OUT / "selector_sizes.csv", OUT / "case_cohort.csv", OUT / "no_result_groups.csv", OUT / "v2_projection.json", OUT / "nonoracle_metadata.json", OUT / "step_a_inputs.json", Path(__file__).resolve()):
        files[str(path.relative_to(OUT))] = sha(path.read_bytes())
    dump(frozen / "manifest.json", {"started_utc": started, "frozen_utc": stamp(), "stage": "A complete; no Step B label inputs opened",
        "oracle_inputs": False, "cohort_rule": "6 large V2 selections + evidenced selection-related no-results + fixed 4-opportunity supplemental cohort",
        "large_count": len(large), "selection_related_no_result_count": len(selection_na), "cases": cases,
        "selectors": ["import_depth1", "import_depth2", "graph_depth3_resolved_only", "graph_depth3_resolved_plus_ambiguous"],
        "graph_seed_rule": "same uniquely resolved changed-symbol seeds in both graph variants; only edge status differs; no class expansion or fallback",
        "files_sha256": files})
    print("FROZEN", sha((frozen / "manifest.json").read_bytes()), stamp(), flush=True)


if __name__ == "__main__":
    main()
