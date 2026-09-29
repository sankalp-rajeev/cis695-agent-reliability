#!/usr/bin/env bash
# Phase 8.3 gate: no oracle data in any agent prompt or verifier input.
#
# NON-NEGOTIABLE. If ground truth reached the agent or the verifier's selection
# step, the experiment measures nothing and no other result survives it. This
# gate therefore fails closed: it exits non-zero on a confirmed leak, on an
# audit that could not complete, and on an audit that found nothing to scan.
#
# "Nothing to scan" is a failure rather than a pass for the same reason NOT_RUN
# is an outcome in Phase 5 and NOT_AVAILABLE is one in Phase 6 — a clean result
# over zero files is not evidence of cleanliness.
#
# Two layers, because either alone would miss the other's cases:
#   1. a fast structural grep for oracle field names, runnable with no dataset
#   2. audit_leakage.py, which compares against the instance's actual oracle
#      values and so catches a leak that was reformatted on the way in
#
# Scope is agent-produced task directories only. The Phase 1 harness controls in
# runs/1.2_gold_sanity and runs/1.3b_wrong_patch legitimately contain gold
# patches — evaluating them is what they are for — so scanning them would
# guarantee a hit and train the reader to ignore this gate.
set -uo pipefail
unset PYTHONPATH

cd "$(dirname "$0")/.."

RUNS_ROOT="${1:-runs}"
PY=".venv/bin/python"
failed=0

echo "=== Phase 8.3 leakage audit: $RUNS_ROOT ==="

if [ ! -d "$RUNS_ROOT" ]; then
  echo "FAIL: no such runs directory: $RUNS_ROOT" >&2
  exit 1
fi

# --- layer 1: oracle field names in agent-visible artifacts ------------------
# Runs even if the dataset is unavailable, so a structural leak is still caught
# when layer 2 cannot run.
echo
echo "--- layer 1: oracle field names ---"

# <runs_root>/<experiment>/tasks/<instance_id>/repair_record.json
mapfile -t TASK_DIRS < <(find "$RUNS_ROOT" -mindepth 4 -maxdepth 4 \
  -name repair_record.json -printf '%h\n' 2>/dev/null | sort)

if [ "${#TASK_DIRS[@]}" -eq 0 ]; then
  echo "FAIL: no agent task directories found under $RUNS_ROOT." >&2
  echo "      An audit that scanned nothing has not passed." >&2
  exit 1
fi

echo "scope: ${#TASK_DIRS[@]} agent task directories"

IN_SCOPE=(trajectory.jsonl agent_output.txt submission_raw.txt \
          repair_record.json patch.diff prompt.txt system_prompt.txt)
FIELDS='FAIL_TO_PASS|PASS_TO_PASS|test_patch|hints_text|eval_script|environment_setup_commit|gold_patch|golden_patch'

scanned=0
for dir in "${TASK_DIRS[@]}"; do
  for name in "${IN_SCOPE[@]}"; do
    [ -f "$dir/$name" ] || continue
    scanned=$((scanned + 1))
    if grep -nE "$FIELDS" "$dir/$name" > /dev/null 2>&1; then
      echo "FAIL: oracle field name in $dir/$name" >&2
      grep -nE "$FIELDS" "$dir/$name" | head -5 >&2
      failed=1
    fi
  done
  for vr in "$dir"/verification_record.*.json; do
    [ -f "$vr" ] || continue
    scanned=$((scanned + 1))
    if grep -nE "$FIELDS" "$vr" > /dev/null 2>&1; then
      echo "FAIL: oracle field name in $vr" >&2
      failed=1
    fi
  done
done

if [ "$scanned" -eq 0 ]; then
  echo "FAIL: task directories exist but contain no in-scope artifacts." >&2
  exit 1
fi
echo "scanned $scanned in-scope artifacts; field-name check $(
  [ "$failed" -eq 0 ] && echo clean || echo FAILED)"

# --- layer 2: actual oracle values ------------------------------------------
# A leak need not carry its label. This compares against the real gold patch,
# test patch, hints text and FAIL_TO_PASS names for each instance.
echo
echo "--- layer 2: oracle content ---"

if [ ! -x "$PY" ]; then
  echo "FAIL: $PY not found; layer 2 cannot run and a partial audit is not a pass" >&2
  exit 1
fi

if ! "$PY" scripts/audit_leakage.py --runs "$RUNS_ROOT"; then
  failed=1
fi

echo
if [ "$failed" -eq 0 ]; then
  echo "PASS: no oracle data reached any agent prompt or verifier input."
else
  echo "FAIL: leakage audit did not pass. This gate is non-negotiable —" >&2
  echo "      a failure invalidates the affected runs." >&2
fi
exit "$failed"
