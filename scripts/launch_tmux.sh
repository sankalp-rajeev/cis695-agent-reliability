#!/usr/bin/env bash
# Start a half in tmux so a dropped SSH session does not kill it.
#
#   scripts/launch_tmux.sh configs/experiments/main_50_a.yaml
#   scripts/launch_tmux.sh configs/experiments/main_50_b.yaml
#
# Resume a stopped session with the same experiment id:
#   env -u PYTHONPATH .venv/bin/python scripts/run_pilot.py --resume main_50_a
#
# Print the window commands and exit, without talking to tmux:
#   scripts/launch_tmux.sh --print-commands configs/experiments/main_50_a.yaml
set -euo pipefail

PRINT_ONLY=0
if [[ "${1:-}" == "--print-commands" ]]; then
  PRINT_ONLY=1
  shift
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXP="${1:?usage: scripts/launch_tmux.sh <experiment-config> [session-name]}"
SESSION="${2:-$(basename "$EXP" .yaml)}"
LOG_DIR="$ROOT/logs"
LOG_FILE="$LOG_DIR/${SESSION}.tmux.log"

# Each window is `env -u PYTHONPATH` plus a non-login shell, so PYTHONPATH is
# gone for that command and every child. That holds when the calling shell has
# it set, and when an already-running tmux server still has it in its environment.
# The tmux client is started the same way, so a server created by this script
# does not store PYTHONPATH either.
RUNNER_INNER="exec .venv/bin/python scripts/run_pilot.py --experiment $(printf '%q' "$EXP") 2>&1 | tee -a $(printf '%q' "$LOG_FILE")"
RUNNER_CMD="exec env -u PYTHONPATH bash --noprofile --norc -c $(printf '%q' "$RUNNER_INNER")"
NOTIFY_CMD="exec env -u PYTHONPATH $(printf '%q' "$ROOT/scripts/notify.sh") $(printf '%q' "$SESSION") $(printf '%q' "$SESSION")"

if [[ "$PRINT_ONLY" == 1 ]]; then
  printf 'runner %s\n' "$RUNNER_CMD"
  printf 'notify %s\n' "$NOTIFY_CMD"
  exit 0
fi

mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session '$SESSION' already exists. Attach with: tmux attach -t $SESSION" >&2
  exit 1
fi

env -u PYTHONPATH tmux new-session -d -s "$SESSION" -c "$ROOT" "$RUNNER_CMD"
env -u PYTHONPATH tmux new-window -d -t "$SESSION" -n notify -c "$ROOT" "$NOTIFY_CMD"

echo "launched session $SESSION"
echo "  windows: runner, notify"
echo "  attach:  tmux attach -t $SESSION"
echo "  resume:  env -u PYTHONPATH .venv/bin/python scripts/run_pilot.py --resume $SESSION"
