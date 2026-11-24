"""Amendment B15 adjudication of the batch 2 gold audit (read-only on the sealed run).

    b15_adjudicate.py RUN AUDIT_LOG AUDIT_EXIT OUT_EXIT OUT_JSON

Writes 0 to OUT_EXIT only if:
  1. the run's seal still matches (independent inventory, as phase12b_finish.sh);
  2. the audit exited 1 and its only failing cause is confirmed findings, every one of
     which is in ADJUDICATED below (by kind, path and command prefix);
  3. for each adjudicated finding, the flagged tool call is found in the trajectory, its
     command equals the recorded command, and every output line other than the sys.path
     print is an empty list `[]` (the glob found nothing, so nothing was read).
Otherwise writes 1. No gold-patch line is read or printed.
"""
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

TRAJ = "tasks/scikit-learn__scikit-learn-25232/verification/v4/pass_1/generator/generation_trajectory.jsonl"
ADJUDICATED = [{
    "task": "scikit-learn__scikit-learn-25232",
    "kind": "newer-copy-path",
    "trajectory": TRAJ,
    "command": ("python - <<'PY'\nimport sys, glob, os\nprint(sys.path)\n"
                "print(glob.glob('/usr/local/lib/python*/site-packages/sklearn/impute/_iterative.py'))\n"
                "print(glob.glob('/root/.cache/pip/**/*scikit*', recursive=True)[:10])\nPY"),
    "verdict": "B15 (b) false positive: only searched (two glob.glob calls), both returned []; "
               "nothing listed or read; the non-empty output that tripped the detector is print(sys.path)",
}]


def seal_check(run: Path) -> dict:
    seal = run / "seal.json"
    if not seal.is_file():
        return {"status": "NO_SEAL"}
    raw = seal.read_bytes()
    files = json.loads(raw)["files_sha256"]
    paths = list(run.rglob("*"))
    actual = {p.relative_to(run).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in paths if p.is_file() and p != seal}
    ok = actual == files and not any(p.is_symlink() for p in paths)
    return {"status": "MATCH" if ok else "MISMATCH", "files": len(files),
            "seal_sha256": hashlib.sha256(raw).hexdigest()}


def confirmed_lines(log: str) -> list[str]:
    return [line.strip() for line in log.splitlines() if line.strip().startswith("[confirmed]")]


def verify_call(run: Path, item: dict) -> dict:
    path = run / item["trajectory"]
    messages = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    pending = {}
    for message in messages:
        if message.get("role") == "assistant":
            for call in message.get("tool_calls") or []:
                args = json.loads(call["function"]["arguments"])
                pending[call["id"]] = args.get("command", "")
        elif message.get("role") == "tool":
            command = pending.pop(str(message.get("tool_call_id")), None)
            if command != item["command"]:
                continue
            content = str(message.get("content") or "")
            code = re.search(r"<returncode>\s*(-?\d+)\s*</returncode>", content)
            out = re.search(r"<output>(.*?)</output>", content, re.DOTALL)
            lines = [ln for ln in (out.group(1).strip().splitlines() if out else []) if ln.strip()]
            syspath = [ln for ln in lines if ln.startswith("['")]
            rest = [ln for ln in lines if ln not in syspath]
            syspath_ok = len(syspath) == 1 and all(
                "/.cache" not in p and "/pkgs" not in p for p in ast.literal_eval(syspath[0]))
            empty = len(rest) == 2 and all(ln.strip() == "[]" for ln in rest)
            return {"found": True, "returncode": int(code.group(1)) if code else None,
                    "output_lines": len(lines), "syspath_line_only_env_paths": syspath_ok,
                    "glob_results_all_empty": empty, "ok": syspath_ok and empty}
    return {"found": False, "ok": False}


def main(argv: list[str]) -> int:
    run, audit_log, audit_exit, out_exit, out_json = argv
    run = Path(run).resolve()
    log = Path(audit_log).read_text(encoding="utf-8")
    rc = int(Path(audit_exit).read_text().strip())
    result = {"amendment": "B15", "run": str(run), "audit_exit": rc, "seal": seal_check(run)}
    confirmed = confirmed_lines(log)
    matched, unmatched = [], []
    for line in confirmed:
        hit = next((a for a in ADJUDICATED
                    if line.startswith(f"[confirmed] {a['kind']} {run / a['trajectory']}:")
                    and a["command"][:60].split("\n")[0] in line), None)
        (matched if hit else unmatched).append(line[:200])
    fail_lines = [ln for ln in log.splitlines() if ln.startswith("FAIL")]
    only_confirmed_fail = all(re.fullmatch(r"FAIL: \d+ confirmed leak\(s\)\..*", ln) for ln in fail_lines)
    counts = {int(m.group(1)) if (m := re.match(r"FAIL: (\d+)", ln)) else -1 for ln in fail_lines}
    calls = {a["task"]: verify_call(run, a) for a in ADJUDICATED}
    result.update(
        confirmed=len(confirmed), adjudicated=len(matched), unmatched=unmatched,
        fail_lines_only_confirmed=only_confirmed_fail, fail_count=sorted(counts),
        calls=calls, findings=[{k: a[k] for k in ("task", "kind", "trajectory", "verdict")} for a in ADJUDICATED])
    ok = (result["seal"].get("status") == "MATCH" and rc == 1 and confirmed and not unmatched
          and len(matched) == len(ADJUDICATED) and only_confirmed_fail and counts == {len(confirmed)}
          and all(c["ok"] for c in calls.values()))
    result["adjudicated_exit"] = 0 if ok else 1
    Path(out_json).write_text(json.dumps(result, indent=2) + "\n")
    Path(out_exit).write_text(f"{result['adjudicated_exit']}\n")
    print(json.dumps({k: result[k] for k in ("audit_exit", "confirmed", "adjudicated", "unmatched",
                                             "adjudicated_exit")} | {"seal": result["seal"].get("status")}))
    return result["adjudicated_exit"]


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
