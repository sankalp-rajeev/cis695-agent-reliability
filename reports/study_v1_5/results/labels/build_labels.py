"""Build an analysis label file from fetched official logs (report.json, patch.diff). Not committed.

    build_labels.py SYSTEM FOLDER LOGS_DIR IDS_TXT LEADERBOARD_JSON OUT_JSON

Reads only the named system's entry in the leaderboard file. Never prints patch content.
"""
import hashlib
import json
import sys
from pathlib import Path

system, folder, logs, ids_txt, leaderboard, out = sys.argv[1:7]
ids = [l.strip() for l in Path(ids_txt).read_text().splitlines() if l.strip()]
board = None
for b in json.loads(Path(leaderboard).read_text())["leaderboards"]:
    for r in b.get("results", []):
        if b.get("name") == "Verified" and r.get("folder") == folder:
            board = r.get("per_instance_details") or {}
labels, agree, disagree, no_board = {}, 0, [], []
for iid in ids:
    d = Path(logs) / iid
    report = d / "report.json"
    patch = d / "patch.diff"
    entry = {"resolved": None, "official_patch_sha256": None, "evidence": None}
    if report.is_file():
        data = json.loads(report.read_text())
        # Nested {iid: {...}} (e.g. Claude v1.0.0) or flat {"resolved": ...} (Gemini v1.0.0).
        node = data[iid] if isinstance(data.get(iid), dict) else data
        if isinstance(node.get("resolved"), bool):
            entry["resolved"] = node["resolved"]
            shape = "nested" if node is not data else "flat"
            entry["evidence"] = f"logs/{iid}/report.json ({shape}) sha256 {hashlib.sha256(report.read_bytes()).hexdigest()}"
    if patch.is_file():
        entry["official_patch_sha256"] = hashlib.sha256(patch.read_bytes()).hexdigest()
    if board is not None and entry["resolved"] is not None:
        b = board.get(iid)
        if not isinstance(b, dict) or "resolved" not in b:
            no_board.append(iid)
        elif bool(b["resolved"]) == entry["resolved"]:
            agree += 1
        else:
            disagree.append(iid)
    labels[iid] = entry
Path(out).write_text(json.dumps({"system": system, "folder": folder, "source": "official logs/<id>/report.json",
                                 "leaderboard_cross_check": {"agree": agree, "disagree": disagree, "missing": no_board},
                                 "labels": labels}, indent=1) + "\n")
print(json.dumps({"system": system, "ids": len(ids), "with_label": sum(v["resolved"] is not None for v in labels.values()),
                  "with_patch": sum(v["official_patch_sha256"] is not None for v in labels.values()),
                  "leaderboard_agree": agree, "leaderboard_disagree": len(disagree), "leaderboard_missing": len(no_board)}))
