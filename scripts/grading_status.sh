#!/usr/bin/env bash
set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
"$root/.venv/bin/python" - "$root/runs/grading_B/progress.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.is_file():
    raise SystemExit("Grading progress is unavailable.")
progress = json.loads(path.read_text())
print(f"Arm B  {progress['done']}/{progress['total']}  {progress['status']}  "
      f"current {progress['current_task'] or '—'}")
print("Outcomes  " + "  ".join(f"{name}={count}" for name, count in progress["outcome_counts"].items()))
print("Errors    " + ("  ".join(f"{name}={count}" for name, count in progress["errors"].items()) or "none"))
if progress["last_error"]:
    print(f"Last error  {progress['last_error']}")
print(f"Updated   {progress['updated_at']}")
PY
