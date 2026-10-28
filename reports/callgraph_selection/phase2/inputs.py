"""Hash-verified, oracle-blind projections of stored phase-1 and V2 inputs."""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CG = HERE.parent
ROOT = CG.parents[1]
PREVIOUS = CG / "amendment2_72ad21b"
DESIGN_COMMIT = "72ad21bce666aa766cc329c9bef8057f790c0ef5"
sys.path[:0] = [str(CG), str(ROOT / "src"), str(ROOT / "reports/v2_diagnostic")]

from build_graphs import object_items, skip_json, whitespace, changed_symbols
from reliability.verifier.patch import parse_patch
from reliability.verifier.integrity import is_test_file
from reliability.verifier.selection import node_ids

IDENTITY_FIELDS = ("instance_id", "repo", "source_run", "artifact_kind", "v2_outcome")
ALLOWED_PARTIAL = {"SyntaxError", "UnicodeError", "ValueError", "RecursionError", "largest_first_retained_ast_quota"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def csv_write(path, rows, fields=None):
    fields = fields or list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (list, dict, tuple)) else v
                             for k, v in row.items()})


class Registry:
    def __init__(self):
        self.files = {}

    def read(self, path, expected=None):
        path = Path(path)
        data = path.read_bytes()
        actual = sha(data)
        if expected and actual.removeprefix("sha256:") != expected.removeprefix("sha256:"):
            raise ValueError("input hash mismatch: " + str(path))
        self.files[str(path.resolve())] = actual
        return data

    def json(self, path, expected=None):
        return json.loads(self.read(path, expected))

    def csv(self, path):
        return list(csv.DictReader(io.StringIO(self.read(path).decode())))

    def jsonlines(self, path, expected):
        return [json.loads(line) for line in gzip.decompress(self.read(path, expected)).splitlines()]


def stored_selections(text):
    """Lexically skip every unapproved snapshot field, including all oracle data."""
    decoder = json.JSONDecoder()
    result = {}
    for key, offset in object_items(text, 0):
        if key != "tasks":
            continue
        offset += 1
        while True:
            offset = whitespace(text, offset)
            if text[offset] == "]":
                break
            if text[offset] == ",":
                offset = whitespace(text, offset + 1)
            record = {}
            for field, start in object_items(text, offset):
                if field in {"instance_id", "source_run"}:
                    record[field] = decoder.raw_decode(text, start)[0]
                elif field == "signals":
                    for name, value in object_items(text, start):
                        if name == "selected_tests":
                            record[name] = decoder.raw_decode(text, value)[0]
            iid = record["instance_id"]
            if iid in result:
                raise ValueError("duplicate snapshot identity")
            result[iid] = record
            offset = skip_json(text, offset)
    return result


def eligibility(member, task, diagnostic, graph_present):
    if not graph_present:
        return "EXCLUDED", "MISSING_GRAPH"
    status = diagnostic["row"]["graph_status"]
    if task["patch_confirmed"] != "True":
        return "EXCLUDED", "PATCH_MISSING_OR_UNCONFIRMED"
    if status not in {"complete", "partial"}:
        return "EXCLUDED", "RESOURCE_LIMITED_GRAPH"
    failures = diagnostic["parse_and_resource_failures"]
    if status == "partial" and (not failures or any(f["reason"] not in ALLOWED_PARTIAL for f in failures)):
        return "EXCLUDED", "PARTIAL_GRAPH_OTHER_REASONS"
    if not int(task["names_resolved"]):
        if int(task["names_ambiguous"]):
            return "EXCLUDED", "AMBIGUOUS_ONLY_SEEDS"
        if not int(task["names_total"]):
            return "EXCLUDED", "NO_EXTRACTED_SEEDS"
        if int(task["newly_added_names"]) == int(task["names_total"]):
            return "EXCLUDED", "NEW_SYMBOLS_ONLY"
        return "EXCLUDED", "UNRESOLVED_SEEDS"
    return ("PRIMARY_COMPLETE" if status == "complete" else "EXTENDED_PARTIAL"), "ELIGIBLE"


def prepare(registry):
    design = registry.read(CG / "design.md")
    committed = subprocess.run(["git", "show", DESIGN_COMMIT + ":reports/callgraph_selection/design.md"],
                               cwd=ROOT, capture_output=True, check=True).stdout
    if design != committed:
        raise ValueError("design differs from frozen commit")
    members = {r["instance_id"]: {k: r[k] for k in IDENTITY_FIELDS}
               for r in registry.csv(ROOT / "reports/v2_diagnostic/patches.csv")}
    if len(members) != 83 or sum(r["artifact_kind"] == "study_snapshot" for r in members.values()) != 19:
        raise ValueError("frozen population mismatch")
    manifest = registry.json(PREVIOUS / "graph_manifest.json")
    seed_tasks = {r["instance_id"]: r for r in registry.csv(PREVIOUS / "task_resolution.csv")}
    seed_symbols = registry.csv(PREVIOUS / "changed_symbol_resolution.csv")
    provenance = {r["instance_id"]: r for r in registry.csv(PREVIOUS / "verified_patch_manifest.csv")}
    acquisition = registry.json(CG / "inputs.json")
    bases = {r["instance_id"]: r for r in acquisition["tasks"]}
    patch_verification = registry.json(PREVIOUS / "patch_verification.json")
    export = Path(patch_verification["export_path"])
    raw_export = registry.read(export, patch_verification["export_sha256"])
    patches = {}
    with tarfile.open(fileobj=io.BytesIO(raw_export), mode="r:gz") as archive:
        if len(archive.getnames()) != len(set(archive.getnames())):
            raise ValueError("duplicate patch export member")
        manifest_bytes = archive.extractfile("frozen_patches_export/manifest.csv").read()
        if sha(manifest_bytes) != patch_verification["manifest_sha256"]:
            raise ValueError("patch manifest changed")
        exported = list(csv.DictReader(io.StringIO(manifest_bytes.decode())))
        if len(exported) != 83 or {r["instance_id"] for r in exported} != set(members):
            raise ValueError("export/cohort identity mismatch")
        for row in exported:
            iid = row["instance_id"]
            payload = archive.extractfile("frozen_patches_export/" + iid + ".patch").read()
            if (sha(payload) != row["sha256"].removeprefix("sha256:") or
                row["sha256"] != provenance[iid]["patch_sha256"] or
                row["csv_source_run"] != members[iid]["source_run"] or row["is_final_study_patch"] != "yes"):
                raise ValueError("unverified final-study candidate: " + iid)
            parse_patch(payload)  # production parser, never a replacement parser
            patches[iid] = payload
    snapshot_path = ROOT / "reports/failure_analysis/extracted.json"
    original_pins = registry.json(CG / "graph_inputs.json")["input_sha256"]
    snapshot_pin = original_pins.get(str(snapshot_path), original_pins.get(str(snapshot_path.relative_to(ROOT))))
    if not snapshot_pin:
        raise ValueError("missing original snapshot hash pin")
    snapshot = stored_selections(registry.read(snapshot_path, snapshot_pin).decode())
    selections = {}
    for iid, member in members.items():
        if member["artifact_kind"] == "study_snapshot":
            record = snapshot[iid]
            if record["source_run"] != member["source_run"] or "selected_tests" not in record:
                raise ValueError("stored V2 provenance mismatch")
            selections[iid] = record["selected_tests"]
            if any(not value.split("::", 1)[0].endswith(".py") for value in selections[iid]):
                raise ValueError("stored V2 candidate has no computable module path; clarification required: " + iid)
    eligible, diagnostics = [], {}
    for iid, member in sorted(members.items()):
        record = manifest.get(iid)
        present = bool(record and all((CG / record["directory"] / f).is_file()
                                     for f in ("nodes.jsonl.gz", "edges.jsonl.gz", "diagnostics.json")))
        if present:
            diagnostic = registry.json(CG / record["directory"] / "diagnostics.json",
                                       record["artifact_sha256"]["diagnostics.json"])
        else:
            diagnostic = {"row": {"graph_status": "missing"}, "parse_and_resource_failures": []}
        diagnostics[iid] = diagnostic
        stratum, reason = eligibility(member, seed_tasks[iid], diagnostic, present)
        eligible.append(dict(**member, stratum=stratum, eligibility_reason=reason,
                             graph_build_status=diagnostic["row"]["graph_status"],
                             resolved_seeds=int(seed_tasks[iid]["names_resolved"]),
                             ambiguous_seeds=int(seed_tasks[iid]["names_ambiguous"]),
                             unresolved_seeds=int(seed_tasks[iid]["names_unresolved"]),
                             patch_sha256=provenance[iid]["patch_sha256"],
                             incompleteness_reasons=diagnostic["parse_and_resource_failures"]))
    na = [r for r in eligible if r["v2_outcome"] == "NOT_AVAILABLE"]
    if len(na) != 13:
        raise ValueError("NOT_AVAILABLE cohort mismatch")
    freeze = dict(design_commit=DESIGN_COMMIT, tasks=eligible,
                  c3_primary_eligible=sorted(r["instance_id"] for r in na if r["stratum"] == "PRIMARY_COMPLETE"),
                  c3_extended_eligible=sorted(r["instance_id"] for r in na if r["stratum"] == "EXTENDED_PARTIAL"),
                  historical_19=sorted(selections), oracle_inputs=False)
    return dict(members=members, manifest=manifest, bases=bases, patches=patches, provenance=provenance,
                seed_tasks=seed_tasks, seed_symbols=seed_symbols, selections=selections,
                diagnostics=diagnostics, eligibility=freeze)


def base_test_ids(task, registry):
    """Read regular archived test blobs as text, using the existing ID extractor."""
    data = registry.read(task["archive_path"], task["archive_sha256"])
    ids, files = [], {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as archive:
        if archive.pax_headers.get("comment") != task["base_commit"]:
            raise ValueError("base commit mismatch")
        for member in archive:
            if member.isdir() and member.name.rstrip("/") == "testbed":
                continue
            if not member.name.startswith("testbed/"):
                raise ValueError("unexpected base archive root")
            path = member.name.removeprefix("testbed/")
            if path.endswith(".py"):
                files[path] = "unindexed"
            if member.isfile() and path.endswith(".py") and is_test_file(path):
                ids.extend(node_ids(path, archive.extractfile(member).read().decode("utf-8", errors="replace")))
    return tuple(ids), files
