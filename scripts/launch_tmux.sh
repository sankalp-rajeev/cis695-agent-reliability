#!/usr/bin/env bash
# Start a half in tmux so a dropped SSH session does not kill it.
#
#   scripts/launch_tmux.sh configs/experiments/main_50_a.yaml
#   scripts/launch_tmux.sh configs/experiments/main_50_b.yaml
#
# Resume a stopped session with the same experiment id:
#   .venv/bin/python scripts/run_pilot.py --resume main_50_a
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXP="${1:?usage: scripts/launch_tmux.sh <experiment-config> [session-name]}"
SESSION="${2:-$(basename "$EXP" .yaml)}"
LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session '$SESSION' already exists. Attach with: tmux attach -t $SESSION" >&2
  exit 1
fi

tmux new-session -d -s "$SESSION" -c "$ROOT" \
  "exec .venv/bin/python scripts/run_pilot.py --experiment '$EXP' 2>&1 | tee -a '$LOG_DIR/${SESSION}.tmux.log'"

echo "launched session $SESSION"
echo "  attach:  tmux attach -t $SESSION"
echo "  resume:  .venv/bin/python scripts/run_pilot.py --resume $SESSION"
