# Report-only follow-up artifacts

Start with REPORT.md. The complete 15 post-hoc metric rows, full false-accept lists, agent precision, candidate-file inventory, V3 record review and V4 resource limits are in the adjacent CSV files. independent_verification.json records the separate standard-library check.

No existing source code, policy, configuration, frozen data, sealed report or tag is changed. analyze.py and verify.py are report/check helpers confined to this directory; verify.py imports no producer or parent-audit analysis module. No task tests or models are run.

To reproduce the independent check from the repository root, with the original local evidence and recorded Docker image available:

```sh
git show phase4-plan-frozen:reports/next_phases/phase4_plan.md > /tmp/signal_followup_frozen_plan.md
bash reports/next_phases/phase7_signal_audit/followup/run_offline.sh verify.py
```

The helper runs with --pull never and --network none, a read-only container root and read-only raw input mounts. Only this follow-up directory is writable. Original claim/patch evidence is mounted from /home/sankalp/projects/cis695-agent-reliability/runs; /original in table paths refers to that project root. /inputs/default_agent.py is a read-only mount of the repository virtualenv's minisweagent/agents/default.py, inspected as text and never imported.

The first launch did not run Python because Docker rejected a duplicate mount; initial_launch.stdout.txt and initial_launch_execution.json preserve that error. Only the duplicate mount was removed; the first executed independent check passed without comparison changes.

From this directory, verify the final output manifest with:

```sh
sha256sum -c artifact_manifest.sha256
```

The manifest excludes itself and Python caches. baseline_seal.json and preservation_check.json retain the original tag identities and 82 sealed artifact hashes.
