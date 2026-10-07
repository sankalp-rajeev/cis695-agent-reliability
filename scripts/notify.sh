#!/usr/bin/env bash
# Post counts for one half. No task ids, no patches, no claim text.
#
#   scripts/notify.sh main_50_a
#
# Reads NTFY_TOPIC from the environment, or from .env in the repo root.
# Posts to https://ntfy.sh every 30 minutes while the run is in progress,
# and once immediately when the run halts, errors, or finishes. If the topic
# is unset, this exits without posting.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXP="${1:?usage: scripts/notify.sh <experiment-id> [tmux-session]}"
SESSION="${2:-$EXP}"
RUN="$ROOT/runs/$EXP"
INTERVAL=1800

topic_from_env() {
  local line
  if [[ -n "${NTFY_TOPIC:-}" ]]; then
    printf '%s' "$NTFY_TOPIC"
    return
  fi
  if [[ -f "$ROOT/.env" ]]; then
    line="$(grep -E '^[[:space:]]*NTFY_TOPIC=' "$ROOT/.env" | tail -n 1 || true)"
    line="${line#*=}"
    line="${line%\"}"
    line="${line#\"}"
    line="${line%\'}"
    line="${line#\'}"
    line="${line%"${line##*[![:space:]]}"}"
    printf '%s' "$line"
  fi
}

TOPIC="$(topic_from_env)"
if [[ -z "$TOPIC" ]]; then
  echo "NTFY_TOPIC is unset in the environment and in .env; not posting" >&2
  exit 1
fi

event_now() {
  local from_files pane
  from_files="$("$ROOT/.venv/bin/python" - "$RUN" <<'PY'
import json
import sys
from pathlib import Path

run = Path(sys.argv[1])
checkpoint = run / "checkpoint.json"
if checkpoint.is_file():
    data = json.loads(checkpoint.read_text(encoding="utf-8"))
    if data.get("halt"):
        print("halt")
        raise SystemExit
summary = run / "summary.json"
if summary.is_file():
    data = json.loads(summary.read_text(encoding="utf-8"))
    gates = data.get("gates") or {}
    print("error" if gates.get("all_passed") is False else "finish")
    raise SystemExit
print("progress")
PY
)"
  if [[ "$from_files" != "progress" ]]; then
    printf '%s' "$from_files"
    return
  fi
  pane="$(tmux list-panes -t "${SESSION}:0" -F '#{pane_dead}' 2>/dev/null || true)"
  if [[ "$pane" == "1" ]]; then
    printf '%s' "error"
    return
  fi
  printf '%s' "progress"
}

post() {
  local event="$1"
  local body
  body="$("$ROOT/.venv/bin/python" "$ROOT/scripts/interim_report.py" \
    "$EXP" --notify-line --event "$event")"
  if [[ "${NOTIFY_DRY_RUN:-}" == "1" ]]; then
    printf '%s\n' "$body"
    return 0
  fi
  curl -fsS --retry 3 --retry-delay 5 \
    -H "Title: ${EXP}" \
    -d "$body" \
    "https://ntfy.sh/${TOPIC}" >/dev/null
}

last_periodic="$(date +%s)"
posted_terminal=""
while true; do
  event="$(event_now)"
  now="$(date +%s)"
  if [[ "$event" != "progress" && "$posted_terminal" != "$event" ]]; then
    post "$event"
    posted_terminal="$event"
    exit 0
  fi
  if (( now - last_periodic >= INTERVAL )); then
    post progress
    last_periodic="$now"
  fi
  sleep 20
done
