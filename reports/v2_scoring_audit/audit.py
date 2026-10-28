"""V2 scoring audit; writes only under its own report directory.

Preflight never pulls images, launches containers, runs tests or accesses gold.
"""
import argparse
import ast
import csv
import hashlib
import io
import json
import os
import shlex
import shutil
import subprocess
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCES = ROOT / "src/reliability/verifier"


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(name, data):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")


def csv_write(name, rows, fields=None):
    path = OUT / name
    fields = fields or list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in r.items()})


def image(iid):
    return "swebench/sweb.eval.x86_64." + iid.replace("__", "_1776_").lower() + ":latest"


def read_json(path):
    return json.loads(path.read_text())


def prepare():
    scope = read_json(OUT / "target_scope.json")["targets"]
    projection = read_json(ROOT / "reports/next_steps/v2_projection.json")
    source_hashes = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in SOURCES.glob("*.py")}
    protocol = {
        "frozen_before_execution_utc": now(), "target_count": 8,
        "output_root": str(OUT), "network": "none; never pull/build/install/download",
        "source_hashes": source_hashes,
        "full_pass_timeout_s": 300, "per_patch_full_pair_budget_s": 600,
        "individual_rerun_timeout_s": 300, "docker_preflight_timeout_s": 20,
        "phase2": "one full original-selection pass on each tree, raw runner bytes/events captured before old/fixed parsing; no baseline-cache substitution",
        "phase3_candidates": "every selected test with differing base/patched outcomes in either direction, UNION every base-FAIL selected test; use raw concrete parameter cases where available; preserve unmapped/missing cases as unknown",
        "phase3_reruns_per_tree": 3,
        "stability": "STABLE only after at least 3 additional completed reruns on EACH tree, no contradictory initial/repeat PASS/FAIL outcomes within either tree; initial plus 3 yields >=4 observations per tree. Any within-tree PASS/FAIL mixture is FLAKY. Errors/timeouts/inadequate repeats cannot establish STABLE.",
        "rerun_counts": "report initial and repeat PASS/FAIL/ERROR/SKIP/TIMEOUT/NOT_RUN counts for each tree and number of valid repeats",
        "usable_v2_exact_user_definition": "V2 ran at least one selected test on both trees and every selected test has a recorded base and patched outcome.",
        "usable_implementation": "derive a fixed per-patch raw-evidence flag independent of old/fixed parser output; no fabricated PASS for absent IDs; declare the treatment of explicit timeout/not-run records; absence of a raw outcome stays missing. Use the same raw evidence and fixed usable flag for paired metrics.",
        "phase4": "apply old and fixed parser to the identical immutable Phase-2 raw evidence, with the same flake evidence; no second full Docker run",
        "phase5_limit": "only patches with sufficient paired raw V2 evidence can be re-scored; list exact IDs/size of this subset, same-subset original metrics next to corrected metrics; do not substitute the selected eight for all 83",
        "phase5_unit_tests": "actual raw ID formats observed in these reruns only; no invented outcome-directed fixtures. No observed format means its test is unavailable, not passed.",
        "environment": "inspect local image ID/RepoDigests and compare with a recorded historical study image digest; tag equality does not prove hash equality. Also verify base commit, runner/Python versions, patch hash, frozen selection and timeout. Drift/unverifiable identity is separate from flakiness.",
        "labels": ["PARSER_ID_MISMATCH", "TRUE_REGRESSION", "FLAKY", "TIMEOUT_OR_NOT_RUN", "PRE_EXISTING_FAILURE", "RUNNER_OR_COLLECTION_FAILURE", "OTHER", "UNKNOWN"],
        "label_notes": "PRE_EXISTING_FAILURE includes a real patched failure absorbed by a confirmed failing base. TRUE_REGRESSION on a post-hoc right patch is a V2 design limit, not by itself a parser/scoring bug. There are eight listed labels, including UNKNOWN.",
        "oracle_gate": "no grader/gold/official test list access before raw evidence collection; narrow cohort-identification exception for the user's mandated five committed right/FAIL rows; diagnosis and parser design never use oracle labels",
        "interpretation6": "state wrong/total counts for corrected FAIL precision and compare explicitly with 14/83 = 16.8674698795%; include subset wrong/base rate separately and do not generalize a targeted or incomplete subset",
        "hard_gate_recommendation": "evidence-based interpretation only, no production/policy change or label-based tuning",
    }
    dump("protocol.json", protocol)
    pv = read_json(ROOT / "reports/callgraph_selection/amendment2_72ad21b/patch_verification.json")
    raw_export = Path(pv["export_path"]).read_bytes()
    if sha(raw_export) != pv["export_sha256"]:
        raise ValueError("candidate export changed")
    rows, source_files = [], []
    selection_payload = {}
    old_reruns = read_json(ROOT / "reports/failure_analysis/group4_regression_rerun.json")
    old_by_id = {r["instance_id"]: r for r in old_reruns["tasks"]}
    with tarfile.open(fileobj=io.BytesIO(raw_export), mode="r:gz") as tar:
        manifest = {r["instance_id"]: r for r in csv.DictReader(io.StringIO(tar.extractfile("frozen_patches_export/manifest.csv").read().decode()))}
        for t in scope:
            iid, run = t["instance_id"], t["source_run"]
            rec = projection[iid]
            if rec["source_run"] != run:
                raise ValueError("snapshot source run mismatch")
            patch = tar.extractfile("frozen_patches_export/" + iid + ".patch").read()
            if sha(patch) != manifest[iid]["sha256"].removeprefix("sha256:") or manifest[iid]["csv_source_run"] != run:
                raise ValueError("candidate identity mismatch")
            (OUT / "frozen_inputs").mkdir(exist_ok=True)
            (OUT / "frozen_inputs" / (iid + ".patch")).write_bytes(patch)
            selection_payload[iid] = {"source_run": run, "selected_tests": rec["selected_tests"],
                "runner": "django" if iid.startswith("django__") else "pytest", "patch_sha256": sha(patch),
                "study_image_tag": image(iid), "historical_image_digest": None,
                "historical_image_digest_status": "UNKNOWN: not stored in inspected execution snapshots/cache/schema"}
            seen = set()
            duplicates = []
            for tid in rec["selected_tests"]:
                if tid in seen:
                    duplicates.append(tid)
                seen.add(tid)
            cachepaths = [ROOT / "runs" / run / "_baseline_cache" / (iid + ".baseline.json"),
                          ROOT / "reports/failure_analysis/_baseline_cache_copy" / (iid + ".baseline.json")]
            cachepath = next((p for p in cachepaths if p.exists()), None)
            cache = read_json(cachepath) if cachepath else None
            failed = [r["test_id"] for r in cache["results"] if r["status"] == "failed"] if cache else []
            rows.append({"instance_id": iid, "source_run": run, "selected": len(seen), "original_v2": rec["regression"]["outcome"],
                "summary": rec["regression"]["findings"]["summary"], "snapshot_evidence": "reports/failure_analysis/extracted.json:" + str(rec["source_lines"]["regression"]),
                "existing_baseline_cache": str(cachepath.relative_to(ROOT)) if cachepath else None,
                "baseline_failed_ids": failed, "existing_v2_regression_ids": old_by_id.get(iid, {}).get("failing", []),
                "duplicate_selected_ids": duplicates, "baseline_duplicates": len(cache["results"]) - len({r["test_id"] for r in cache["results"]}) if cache else None,
                "raw_preparser_base_and_patch_available": False,
                "current_primary_diagnosis": "UNKNOWN", "status": "confirmed stored fields; inferred diagnosis",
                "cannot_determine": "same-run raw paired IDs/statuses; completed test-specific timeout evidence; stable/flaky classification; causal parser or baseline absorption; historical image digest"})
            source_files.extend(cachepaths)
    dump("frozen_inputs/selections.json", selection_payload)
    csv_write("phase1_existing_evidence.csv", rows)
    dump("phase1_existing_v2_evidence.json", {"snapshots": {iid: projection[iid] for iid in selection_payload},
        "previous_v2_rerun_records": {iid: old_by_id[iid] for iid in old_by_id if iid in selection_payload},
        "notice": "V2 fields only, no grader/gold/official test lists. Old reruns are parsed/aggregate evidence, not pre-parser raw logs."})
    frozen = {str(p.relative_to(OUT)): sha(p.read_bytes()) for p in (OUT / "frozen_inputs").glob('*') if p.is_file()}
    dump("frozen_inputs/manifest.json", {"created_utc": now(), "protocol_sha256": sha((OUT / "protocol.json").read_bytes()),
         "files_sha256": frozen, "candidate_export_sha256": sha(raw_export), "oracle_inputs": False})
    lines = ["# V2 scoring audit — amended protocol and Phase 1", "",
        "[confirmed] The five requested committed right/FAIL candidate IDs were identified solely for cohort scope. No grader, gold patch or official test list has been opened for this audit. All candidate patches and original selections are copied/hash-frozen under this directory; no production code or prior report was changed.", "",
        "[confirmed] Your five fixes and two notes are frozen in `protocol.json` before Docker/test execution. Phase 2 is one full selected-suite pass per side; Phase 3 adds at least three individual reruns per side for every raw base/patched difference (either direction) and every base FAIL. Any within-tree PASS/FAIL mixture is FLAKY. Four observations per side including the initial run are required for STABLE.", "",
        "[confirmed] Usable V2 is defined before execution: **V2 ran at least one selected test on both trees and every selected test has a recorded base and patched outcome.** Raw coverage, not parser-specific success, fixes the same paired denominator for old and corrected metrics. Missing outcomes are not fabricated passes.", "",
        "[confirmed] Full-pass timeout: 300 s per tree; 600 s per initial pair. Individual confirmation timeout: 300 s per tree/attempt. Read-only Docker preflight timeout: 20 s. No historical per-task override was found in the inspected snapshots; 300/600 s matches `src/reliability/verifier/regression.py:122`.", "",
        "[unknown] Historical image IDs/digests are absent from the inspected V2 snapshots/cache/schema. Tags are recorded but do not establish environment-hash equality. Preflight will record current image IDs/digests and explicitly preserve UNKNOWN if comparison is impossible; environment drift will not be called flakiness.", "",
        "## Existing evidence", "", "| Patch | Selected | Stored V2 | Base cache | Existing primary diagnosis |", "|---|---:|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['instance_id']} | {r['selected']} | {r['original_v2']} | {'present' if r['existing_baseline_cache'] else 'missing'} | [unknown] UNKNOWN |")
    lines += ["", "[confirmed] Five existing Group-4 V2 rerun records name regression IDs, and five base caches preserve parsed baseline statuses. They contain no paired pre-parser runner logs and cannot establish the required stability repetitions. All eight same-study snapshots have selected-ID unions and aggregate histograms. `phase1_existing_evidence.csv` records exact snapshot line evidence, duplicate counts, cached failed-base IDs and named prior regressions.", "",
        "[confirmed] Source review: pytest parser exact ID admission `container.py:365` drops parameterized case output if the selected ID is its family. Django fallback `container.py:399` includes an unqualified suffix match and last-write assignment at `:405`; collisions/duplicate output need raw-log checking. Selection emits families at `selection.py:407`; Django conversion is at `:441`. Missing/timeout results remain NOT_RUN/TIMEOUT at `regression.py:213`; base failure is excluded at `:237`; the current flake rerun is one-sided at `:303`. Patch PASS with partial execution is possible at `:314`–`:328`. Per-test final classifications are not serialized by `run.py:376`.", "",
        "[inferred] These establish source-level mechanisms, not that any specific historical FAIL or PASS was caused by them. No individual primary cause is forced. All filenames in the previous paragraph are under `src/reliability/verifier/`.", "",
        "[confirmed] Corrected re-scoring will cover only the raw-evidence-supported subset, whose size/IDs will be reported explicitly, with original metrics on the identical subset. The eight deliberately selected targets will never be presented as all-83 corrected results. Only raw formats actually observed in audit reruns may supply parser test fixtures.", "",
        "[inferred] PRE_EXISTING_FAILURE covers a real patched failure absorbed by a confirmed failing base. TRUE_REGRESSION on a post-hoc right patch is a V2 design limit, not automatically a bug. Interpretation 6 will state corrected FAIL wrong/total counts against **14/83**, and separately state the subset's own wrong-patch rate; no label-based scoring tuning.", "",
        "[unknown] Phases 2–6 await environment preflight. No benchmark or parser-unit tests have run.", ""]
    (OUT / "report.md").write_text("\n".join(lines))
    print('PREPARED',len(rows),'patches;',sum(r['selected'] for r in rows),'selected families')


def recorded_command(argv, key, timeout=20):
    entry = {"time_utc_before_execution": now(), "argv": argv, "shell_display": shlex.join(argv), "timeout_s": timeout, "purpose": key}
    with (OUT / "commands.jsonl").open("a") as f:
        f.write(json.dumps(entry) + "\n")
        f.flush()
        os.fsync(f.fileno())
    print("EXACT COMMAND BEFORE EXECUTION:", entry["shell_display"], flush=True)
    start = time.monotonic()
    try:
        proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        stdout, stderr, rc, status = proc.stdout, proc.stderr, proc.returncode, "completed"
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, rc, status = exc.stdout or b"", exc.stderr or b"", None, "timeout"
    except OSError as exc:
        stdout, stderr, rc, status = b"", str(exc).encode(), None, "launch_error"
    folder = OUT / "preflight"
    folder.mkdir(exist_ok=True)
    stdout_path, stderr_path = folder / (key + ".stdout"), folder / (key + ".stderr")
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    result = dict(entry, returncode=rc, status=status, duration_s=time.monotonic() - start,
                  stdout=str(stdout_path.relative_to(OUT)), stderr=str(stderr_path.relative_to(OUT)))
    dump("preflight/" + key + ".json", result)
    print(json.dumps(result), flush=True)
    if stderr:
        print(stderr.decode(errors="replace")[:2000], flush=True)
    if stdout:
        print(stdout.decode(errors="replace")[:2000], flush=True)
    return result, stdout, stderr


def preflight():
    if not (OUT / "protocol.json").exists() or not (OUT / "report.md").exists():
        raise SystemExit("Phase 1 and protocol must exist before Docker")
    cli = shutil.which("docker")
    fallback = Path("/mnt/wsl/docker-desktop/cli-tools/usr/bin/docker")
    if cli is None and fallback.exists():
        cli = str(fallback)
    if cli is None:
        dump("preflight/status.json", {"docker_available": False, "reason": "Docker CLI absent", "tests_executed": False})
        return
    result, raw, _ = recorded_command([cli, "version", "--format", "{{json .}}"], "docker_version")
    if result["returncode"] != 0:
        dump("preflight/status.json", {"docker_available": False, "reason": "Docker version/server preflight failed", "command": result,
             "tests_executed": False, "image_hash_match": "UNKNOWN; no server/image access"})
        return
    try:
        version = json.loads(raw)
    except (ValueError, TypeError):
        version = {}
    if not version.get("Server"):
        dump("preflight/status.json", {"docker_available": False, "reason": "No Docker server in version response", "tests_executed": False})
        return
    rows = []
    for iid, r in read_json(OUT / "frozen_inputs/selections.json").items():
        result, raw, _ = recorded_command([cli, "image", "inspect", r["study_image_tag"]], "image_" + iid)
        inspected = json.loads(raw)[0] if result["returncode"] == 0 else {}
        rows.append({"instance_id": iid, "tag": r["study_image_tag"], "image_available": bool(inspected),
             "current_image_id": inspected.get("Id"), "current_repo_digests": inspected.get("RepoDigests"),
             "study_image_hash": None, "image_hash_match": "UNKNOWN: historical image digest not stored", "tests_executed": False})
    csv_write("environment_sanity.csv", rows)
    dump("preflight/status.json", {"docker_available": True, "image_status": rows, "tests_executed": False})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["prepare", "preflight"])
    args = parser.parse_args()
    {"prepare": prepare, "preflight": preflight}[args.stage]()
