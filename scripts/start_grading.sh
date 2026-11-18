#!/usr/bin/env bash
set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd -- "$root"
sealed=/home/sankalp/projects/wt-e2e/runs/e2e_v1_4_3_armB_um
out=runs/grading_B
mkdir -p -- "$out"

if tmux has-session -t '=grading' 2>/dev/null; then
    printf '%s\n' 'The grading tmux session already exists.' >&2
    exit 1
fi

tmux new-session -d -s grading -c "$root" bash -c '
    export HF_HOME="$PWD/runs/hf_home" HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1
    unset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONNOUSERSITE
    exec .venv/bin/python -u scripts/grade_arm.py --arm B --sealed "$1" --out "$2" >> "$2/grading.log" 2>&1
' bash "$sealed" "$out"
printf '%s\n' 'Started grading in tmux. Log at runs/grading_B/grading.log.'
