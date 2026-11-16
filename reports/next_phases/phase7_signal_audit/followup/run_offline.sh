#!/bin/bash
# Report/check scripts only; never execute task code or instantiate a model.
set -euo pipefail
followup_out="$(cd -- "$(dirname -- "$0")" && pwd)"
audit_root="$(git -C "$followup_out" rev-parse --show-toplevel)"
case "$1" in analyze.py|verify.py) ;; *) exit 2 ;; esac
docker run --rm --pull never --network none --read-only --cap-drop ALL --security-opt no-new-privileges \
 --user "$(id -u):$(id -g)" --tmpfs /tmp:rw,nosuid,nodev,size=512m,mode=1777 -e PYTHONDONTWRITEBYTECODE=1 \
 --mount "type=bind,src=$audit_root/reports/next_phases/phase7_signal_audit,dst=/repo/reports/next_phases/phase7_signal_audit,readonly" \
 --mount "type=bind,src=$followup_out,dst=/repo/reports/next_phases/phase7_signal_audit/followup" \
 --mount "type=bind,src=$audit_root/reports/v2_discovery_cleanup/frozen_83,dst=/repo/reports/v2_discovery_cleanup/frozen_83,readonly" \
 --mount "type=bind,src=$audit_root/manifests,dst=/repo/manifests,readonly" \
 --mount "type=bind,src=$audit_root/runs/main_50_a,dst=/repo/runs/main_50_a,readonly" \
 --mount "type=bind,src=$audit_root/runs/main_50_b,dst=/repo/runs/main_50_b,readonly" \
 --mount "type=bind,src=$audit_root/runs/main_2_rerun_mpl,dst=/repo/runs/main_2_rerun_mpl,readonly" \
 --mount "type=bind,src=$audit_root/runs/main_3_rerun_infra,dst=/repo/runs/main_3_rerun_infra,readonly" \
 --mount "type=bind,src=$audit_root/reports/next_phases/phase4_rerun/attempt4_seal/results.json,dst=/repo/reports/next_phases/phase4_rerun/attempt4_seal/results.json,readonly" \
 --mount "type=bind,src=$audit_root/reports/next_phases/phase4_posthoc/label_audit/audited_labels.csv,dst=/repo/reports/next_phases/phase4_posthoc/label_audit/audited_labels.csv,readonly" \
 --mount "type=bind,src=$audit_root/reports/next_phases/phase4_posthoc/grader_gap/classification.csv,dst=/repo/reports/next_phases/phase4_posthoc/grader_gap/classification.csv,readonly" \
 --mount "type=bind,src=$audit_root/reports/next_phases/phase4_plan.md,dst=/repo/reports/next_phases/phase4_plan.md,readonly" \
 --mount "type=bind,src=$audit_root/configs,dst=/repo/configs,readonly" \
 --mount "type=bind,src=$audit_root/src/reliability/verifier,dst=/repo/src/reliability/verifier,readonly" \
 --mount "type=bind,src=$audit_root/.venv/lib/python3.11/site-packages/minisweagent/agents/default.py,dst=/inputs/default_agent.py,readonly" \
 --mount type=bind,src=/tmp/signal_followup_frozen_plan.md,dst=/inputs/phase4_plan_frozen.md,readonly \
 --mount type=bind,src=/home/sankalp/projects/cis695-agent-reliability/runs,dst=/original/runs,readonly \
 --entrypoint /opt/miniconda3/bin/python \
 sha256:b66d524a1b44b0ed09a517d06fcdf5326ff47e64a0cb847a683ba95b8540137d \
 "/repo/reports/next_phases/phase7_signal_audit/followup/$1"
