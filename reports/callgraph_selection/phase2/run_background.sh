#!/usr/bin/env bash
# Runtime wrapper only. Selector constants, ranking and eligibility are untouched.
set -u
env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/phase2/run.py --stage execute
cg_selector_exit=$?
printf '%s\n' "$cg_selector_exit" > reports/callgraph_selection/phase2/selector_exit_status.txt
if [ "$cg_selector_exit" -eq 0 ]; then
    printf '%s\n' 'BACKGROUND_RUN_COMPLETE exit=0'
else
    printf 'BACKGROUND_RUN_FAILED exit=%s\n' "$cg_selector_exit"
fi
exit "$cg_selector_exit"
