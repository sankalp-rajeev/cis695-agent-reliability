#!/usr/bin/env bash
set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd -- "$root"
sealed=/home/sankalp/projects/wt-e2e/runs/e2e_v1_4_3_armB_um
out=runs/grading_B
report=reports/rerun_v1/arm_B
if [[ "$(git branch --show-current)" != results/rerun-v1 ]]; then
    printf '%s\n' 'Run finalization on branch results/rerun-v1.' >&2
    exit 1
fi

.venv/bin/python scripts/verify_grading.py --arm B --sealed "$sealed" --out "$out" --finalize

paths=(STATUS.md "$report/DECISIONS.md" "$report/labels.csv"
       "$report/labels_summary.json" "$report/REPORT.md")
git add -- "${paths[@]}"
if ! git diff --cached --quiet -- "${paths[@]}"; then
    git commit --only -m 'Grade rerun arm B with the frozen oracle' -- "${paths[@]}"
fi
