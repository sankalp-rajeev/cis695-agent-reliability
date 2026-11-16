#!/bin/bash
# Offline execution with explicit input mounts; post-hoc inputs require the seal.
set -euo pipefail
audit_out="$(cd -- "$(dirname -- "$0")" && pwd)"
audit_root="$(git -C "$audit_out" rev-parse --show-toplevel)"
audit_script="$1"
audit_extra=()
case "$audit_script" in
  run_v1.py|stage2.py|stage3.py|stage4.py) ;;
  stage5.py|verify_all.py)
    git -C "$audit_root" rev-parse --verify 'refs/tags/signal-audit-labelfree^{}' >/dev/null
    git -C "$audit_root" merge-base --is-ancestor signal-audit-labelfree HEAD
    audit_extra+=(
      --mount "type=bind,src=$audit_root/reports/next_phases/phase4_posthoc/label_audit/audited_labels.csv,dst=/repo/reports/next_phases/phase4_posthoc/label_audit/audited_labels.csv,readonly"
      --mount "type=bind,src=$audit_root/reports/next_phases/phase4_posthoc/grader_gap/classification.csv,dst=/repo/reports/next_phases/phase4_posthoc/grader_gap/classification.csv,readonly"
      --mount type=bind,src=/home/sankalp/projects/cis695-agent-reliability/runs,dst=/original/runs,readonly
    ) ;;
  *) exit 2 ;;
esac
docker run --rm --pull never --network none --read-only --cap-drop ALL --security-opt no-new-privileges \
 --user "$(id -u):$(id -g)" --tmpfs /tmp:rw,nosuid,nodev,size=512m,mode=1777 \
 -e PYTHONDONTWRITEBYTECODE=1 \
 --mount "type=bind,src=$audit_out,dst=/repo/reports/next_phases/phase7_signal_audit" \
 --mount "type=bind,src=$audit_out,dst=/out" \
 --mount "type=bind,src=$audit_root/manifests,dst=/repo/manifests,readonly" \
 --mount "type=bind,src=$audit_root/reports/v2_discovery_cleanup/frozen_83/tasks.json,dst=/repo/reports/v2_discovery_cleanup/frozen_83/tasks.json,readonly" \
 --mount "type=bind,src=$audit_root/reports/v2_discovery_cleanup/frozen_83/patches,dst=/repo/reports/v2_discovery_cleanup/frozen_83/patches,readonly" \
 --mount "type=bind,src=$audit_root/reports/v2_discovery_cleanup/frozen_83/patches/scikit-learn__scikit-learn-14141.patch,dst=/inputs/candidate.patch,readonly" \
 --mount "type=bind,src=$audit_root/runs/main_50_a,dst=/repo/runs/main_50_a,readonly" \
 --mount "type=bind,src=$audit_root/runs/main_50_b,dst=/repo/runs/main_50_b,readonly" \
 --mount "type=bind,src=$audit_root/runs/main_2_rerun_mpl,dst=/repo/runs/main_2_rerun_mpl,readonly" \
 --mount "type=bind,src=$audit_root/runs/main_3_rerun_infra,dst=/repo/runs/main_3_rerun_infra,readonly" \
 --mount "type=bind,src=$audit_root/src/reliability/verifier,dst=/repo/src/reliability/verifier,readonly" \
 --mount "type=bind,src=$audit_root/src/reliability/verifier/patch.py,dst=/verifier/patch.py,readonly" \
 --mount "type=bind,src=$audit_root/src/reliability/verifier/integrity.py,dst=/verifier/integrity.py,readonly" \
 --mount "type=bind,src=$audit_root/docs/VERIFIER_POLICY.md,dst=/repo/docs/VERIFIER_POLICY.md,readonly" \
 --mount "type=bind,src=$audit_root/tests/unit/test_integrity.py,dst=/repo/tests/unit/test_integrity.py,readonly" \
 --mount "type=bind,src=$audit_root/reports/next_phases/phase4_rerun/attempt4_seal/results.json,dst=/repo/reports/next_phases/phase4_rerun/attempt4_seal/results.json,readonly" \
 --mount type=bind,src=/home/sankalp/cg_repos/task_archives/scikit-learn__scikit-learn-14141.tar,dst=/inputs/base.tar,readonly \
 "${audit_extra[@]}" --entrypoint /opt/miniconda3/bin/python \
 sha256:b66d524a1b44b0ed09a517d06fcdf5326ff47e64a0cb847a683ba95b8540137d \
 "/repo/reports/next_phases/phase7_signal_audit/$audit_script"
