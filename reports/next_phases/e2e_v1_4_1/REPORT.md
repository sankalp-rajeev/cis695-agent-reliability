# E2E v1.4.1

**Verdict: STOPPED_INPUT_ACCESS. The requested full pipeline is not implemented or accepted. No freeze tag was created.**

The required input-access preflight found two conflicts with the request's read restrictions. Implementation stopped at this clean point; the frozen executor, selection, policies, guard thresholds, and reproduction setup were not changed. No model call or live Docker acceptance run occurred.

| Check | Result | Evidence / limitation |
|---|---|---|
| A1 selection | NOT RUN | Stopped at input-access preflight. |
| A2 guarded four-policy replay | NOT RUN | No outcome comparison or health-halt claim is made. |
| A3 decision replay | NOT RUN | No ACCEPT/FLAG/REJECT table produced. |
| A4 live Docker checks | NOT RUN | No containers started; `--skip-v4` was not used. |
| A4b registry interface | NOT RUN | Registry and schema not built. |
| A5 fault injection | NOT RUN | New runner not built. |
| A6 unit suite / preservation | IN PROGRESS | Three new access-preflight tests; full-suite comparison pending. 74 permitted artifact hashes match, zero mismatches, one hash blocked. |
| A7 independent acceptance verifier | NOT RUN | The standard-library input-access preflight below is a diagnostic, not the A7 acceptance verifier. |

## Required sources and the read boundary

`scripts/phase4_launch.py:frozen_django_command_choice` looks up one source per Django task in `reports/next_phases/phase4_rerun/fix13_reference/manifest.json`. It verifies that source's hash and projects only the first two calls' `run.events[].argv` before deriving the parallel choice. All 31 Django sources point outside the permitted paired-frozen directory, under:

```
/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/
ubuntu_static_b030e50_20261105T172604_853449Z/
full_83_20261105T231219_643682Z/results/tasks/<instance_id>/v2/result.json
```

Their exact paths and expected hashes are listed in [input_access.json](input_access.json). No such source was opened, resolved, or statted by the preflight. The fix13 reference directory contains `manifest.json`, `reference_ids.json.gz`, and `counts.csv`; it does not contain the command projection. Inferring the choice from a different source would not implement D1's exact source requirement.

Separately, `reports/policy_v1_4/artifact_manifest.sha256` requires hashing `reports/policy_v1_4/golden.csv`. The request expressly prohibits opening any path containing `gold` and says to stop and report when a needed input has one of the forbidden names. Even byte-only hashing would open that file. It was left unopened. The other 74 manifested entries across the two freeze manifests were hashed successfully, with no mismatches.

To resume, the read boundary needs an explicit exception for hash verification and argv-only projection of the 31 listed Django files, and for byte-only hashing of `reports/policy_v1_4/golden.csv`. No outcome or correctness fields are needed from either source.

## Changes and decisions

- Added [scripts/e2e_input_preflight.py](../../../scripts/e2e_input_preflight.py): standard-library diagnostic with structural JSON whitelisting; it refuses to open the blocked input paths and reports their declared provenance.
- Added three tests for skipped-value decoding, unopened out-of-scope command sources, and unopened forbidden artifact names.
- Kept every production verifier file unchanged and stopped before producing a misleading runnable pipeline or registry.
- Recorded one-line reasons in [DECISIONS.md](DECISIONS.md); recorded the stop and environment in root STATUS.md.

## Independent input-access diagnostic output

This output is from the access preflight, not the unimplemented A7 verifier:

```text
{
  "check": "D1_INPUT_ACCESS",
  "status": "BLOCKED_INPUT_ACCESS",
  "frozen_tasks": 83,
  "django_tasks": 31,
  "input_sha256": {
    "/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/paired_frozen/tasks.json": "532df6e8eebd9afa91592ef39aa28f12d8b905fcf3987c7698e06c8ad02ac625",
    "/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/paired_frozen/protocol.json": "2eaf8341274099cf4210674e6418a4b1e44ea2d0babb09a1c2243f77258c5153",
    "/home/sankalp/projects/wt-e2e/reports/next_phases/phase4_rerun/fix13_reference/manifest.json": "5464690f7a64d1bdeeea88f257f8bdedc70a98d7d758a4a298f34e7a6933b792"
  },
  "command_projection_sources_opened": 0,
  "model_calls": 0,
  "acceptance_checks_run": []
}
blocked_source_count=31
frozen_artifact_matches=74
frozen_artifact_mismatches=0
blocked_frozen_artifacts=["reports/policy_v1_4/golden.csv"]
```

## Unit comparison and final branch integration

Pending: exact command and test-id comparison against `/home/sankalp/projects/unit_baseline_7fefe1d/failing_ids.txt`, followed by the requested latest routing-branch merge and unit rerun. Full output is being retained under `runs/e2e_v1_4_1_checks/`.

## Known limitations

This checkpoint is not usable for a pilot or audited rerun. No 83-task registry, v1.4.1 runtime, paid-provider ledger generalization, resume path, or acceptance verifier has been delivered. Registries for new instances remain the task-prep job's responsibility. The requested design would have weaker environment-drift protection on the patched tree. A4 did not run, so no `--skip-v4` evidence exists. The November 18 deadline cannot be certified while the input-access conflict remains unresolved.
