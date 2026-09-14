#!/usr/bin/env bash
# Phase 1.2 / 1.3 harness feasibility runs.
#
# Usage: harness_sanity.sh <run_label> <predictions_path>
#
# Runs one instance at a time so wall-clock is attributable per instance, and
# times image acquisition separately from evaluation. SWE-bench Verified ships
# prebuilt images, so "image build" is really a registry pull.
set -uo pipefail

RUN_LABEL="$1"
PREDICTIONS="$2"

REPO="$HOME/projects/cis695-agent-reliability"
cd "$REPO"

OUTDIR="runs/${RUN_LABEL}"
LOG="${OUTDIR}/run.log"
METRICS="${OUTDIR}/metrics.tsv"
mkdir -p "$OUTDIR"

INSTANCES=(
  django__django-12304
  sympy__sympy-15599
  matplotlib__matplotlib-25287
)

images_size() {
  docker system df | awk '$1 == "Images" { print $4 }'
}

: > "$LOG"
printf 'instance\tpull_s\teval_s\ttotal_s\timages_size_after\n' > "$METRICS"

echo "run_label=${RUN_LABEL}" >> "$LOG"
echo "predictions=${PREDICTIONS}" >> "$LOG"
echo "started=$(date -Is)" >> "$LOG"
echo "images_size_before=$(images_size)" >> "$LOG"

for inst in "${INSTANCES[@]}"; do
  img="$(.venv/bin/python scripts/image_for.py "$inst")"

  {
    echo ""
    echo "===================== ${inst} ====================="
    echo "image: ${img}"
  } >> "$LOG"

  p0=$(date +%s)
  docker pull "$img" >> "$LOG" 2>&1
  p1=$(date +%s)
  pull_s=$(( p1 - p0 ))
  echo "PULL_SECONDS=${pull_s}" >> "$LOG"

  e0=$(date +%s)
  .venv/bin/python -m swebench.harness.run_evaluation \
    --dataset_name SWE-bench/SWE-bench_Verified \
    --split test \
    --predictions_path "$PREDICTIONS" \
    --instance_ids "$inst" \
    --max_workers 1 \
    --run_id "${RUN_LABEL}__${inst}" \
    --report_dir "$OUTDIR" \
    --timeout 1800 >> "$LOG" 2>&1
  e1=$(date +%s)
  eval_s=$(( e1 - e0 ))
  echo "EVAL_SECONDS=${eval_s}" >> "$LOG"

  printf '%s\t%s\t%s\t%s\t%s\n' \
    "$inst" "$pull_s" "$eval_s" "$(( pull_s + eval_s ))" "$(images_size)" >> "$METRICS"
done

echo "" >> "$LOG"
echo "images_size_after=$(images_size)" >> "$LOG"
echo "finished=$(date -Is)" >> "$LOG"
echo "ALL_DONE" >> "$LOG"
