# E2E v1.4.2 runbook

Run from `/home/sankalp/projects/wt-e2e` with this worktree's `.venv`. The 83-task registry, manifests, wheel, archives and local images are prepared. Model configs must be verified; provide their named API-key environment variables. No model call was made during implementation. The commands below describe future runs, not authorization to launch them in this session.

Release tag: `e2e-v1.4.2-frozen`. Do not resume v1.4.1 pilot folders, including `runs/e2e_v1_4_1_pilot_A`; they are immutable pilot evidence from the old runtime. Start a fresh v1.4.2 output folder and retain the same shared spend ledger. The published `e2e-v1.4.1-frozen` tag remains unchanged.

Before the first paid run, seed the shared ledger from the probe's existing **$0.66 UM spend**:

```bash
env -u PYTHONPATH PYTHONPATH=src .venv/bin/python scripts/seed_provider_ledger.py \
  --from /home/sankalp/projects/wt-umgpt-probe/runs/umgpt_spend_ledger.json
```

The destination defaults to `/home/sankalp/projects/wt-e2e/runs/provider_spend_ledger.json`. The command makes a byte copy, verifies its SHA-256, prints per-provider/account spent totals, and refuses to overwrite a non-empty ledger. Legacy entries count against the UM/default-account cap. Run this once; retain the same ledger for every pilot, arm and resume. Do not seed again over a ledger that has recorded paid work.

Set `--deepseek-cap-usd` from the funded balance minus a **$0.50 margin**, rounding down conservatively. As of 17 November 2026 the funded balance is $4.78 and the chosen cap is **$4.00**. Once the account is topped up, raise this value by resuming the same output folder.

Three-task pilot (repair agent and V4 enabled):

```bash
env -u PYTHONPATH HF_HOME=/home/sankalp/projects/wt-e2e/runs/hf_home HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1 PYTHONPATH=src .venv/bin/python scripts/run_e2e.py \
  --mode pilot --manifest configs/e2e/live_checks_3.txt \
  --task-specs configs/e2e/task_specs_83.json \
  --primary-config configs/model/primary.yaml --generator-config configs/model/generator.yaml \
  --ledger-file runs/provider_spend_ledger.json --deepseek-cap-usd 4.00 \
  --output runs/e2e_v1_4_2_pilot
```

Audited 83-task UM repair arm, DeepSeek V4 (clean HEAD must equal the annotated tag):

```bash
env -u PYTHONPATH HF_HOME=/home/sankalp/projects/wt-e2e/runs/hf_home HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1 PYTHONPATH=src .venv/bin/python scripts/run_e2e.py \
  --mode audited --freeze-tag e2e-v1.4.2-frozen --manifest configs/e2e/tasks_83.txt \
  --task-specs configs/e2e/task_specs_83.json \
  --primary-config configs/model/primary_umgpt.yaml --generator-config configs/model/generator.yaml \
  --ledger-file runs/provider_spend_ledger.json --deepseek-cap-usd 4.00 \
  --um-cap-usd 20.00 --um-job-cap-usd 20.00 --output runs/e2e_v1_4_2_um_audited
```

The **UM account cap protects the key** across runs and includes the probe's $0.66 spend. The $20 job cap allows the audited arm to use the remaining account allowance; the probe's $3 job cap is unsuitable for 83 tasks.

For the DeepSeek repair arm, change only `--primary-config` to `configs/model/primary.yaml` and use a separate output folder. Both arms must keep the same ledger file: changing output folders does not reset the shared DeepSeek cap. Caps can stop a run before all 83 tasks complete. Every stop records completed/not-completed IDs in `completion.json`; grading is a separate step after the run is sealed.

Resume by repeating the command with the same output folder and ledger file. Only `--deepseek-cap-usd`, `--um-cap-usd` and `--um-job-cap-usd` may change; all other header fields remain strict, including HEAD and model/config/registry identities. Caps may increase or decrease. For example, after a top-up, repeat the original command with a newly calculated `--deepseek-cap-usd`. The header retains the first attempt's caps; `attempt.json` records each attempt's caps and provider/account totals at its start, including conservative unresolved request reservations. A cap below existing spend stops with `STOPPED_BUDGET` before any new paid call. Previously paid work remains charged.

A complete frozen repair patch is never regenerated; unfinished verification moves into the task's `attempts/`. A fresh V4 stage cannot silently reset a spent per-task ceiling; it stops before new paid work if its full ceiling cannot fit.

Transient provider attempts retain their conservative charge and retry through the native scaffold loop (ten total attempts by default, exponential waits capped at 60 seconds). An exhausted repair writes `agent_absence.json` with `AGENT_INFRA:<type>` and `infrastructure: true`, freezes the current working-tree diff, and continues verification. `completion.json` lists these in `agent_infrastructure_tasks` separately from `no_patch_tasks`; an infrastructure task can have either a nonempty or empty diff. Empty patches receive V2–V4 `EMPTY_PATCH` absences without infrastructure flags, containers, or V4 spend; unchanged V1 and policy produce REJECT. A nonempty patch selecting no tests has a normal V2 absence; skipped selected tests remain non-PASS evidence.

For new instances, supply the task-prep job's validated registries with `--task-specs file1.json file2.json`; no cohort name is special. Missing task specs become per-task `NO_TASK_SPEC` V2/V3 absences. The shared schema is in `docs/TASK_SPEC_SCHEMA.md`. Do not rebuild the already frozen registry before an audited run at this tag.

Reproduce the no-model live check in a fresh output folder:

```bash
env -u PYTHONPATH HF_HOME=/home/sankalp/projects/wt-e2e/runs/hf_home HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1 PYTHONPATH=src .venv/bin/python scripts/run_e2e.py \
  --mode pilot --manifest configs/e2e/live_checks_3.txt --task-specs configs/e2e/task_specs_83.json \
  --primary-config configs/model/primary.yaml --generator-config configs/model/generator.yaml \
  --verify-only-from /home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/paired_frozen \
  --skip-v4 --output runs/e2e_v1_4_2_checks/live_recheck
```

Offline A1/A2, followed by the independent checker (raw sealed captures remain read-only):

```bash
env -u PYTHONPATH PYTHONPATH=src .venv/bin/python scripts/check_e2e_offline.py --output runs/e2e_v1_4_2_checks/offline --captures /home/sankalp/projects/cis695-v2-scg-ubuntu-publication/runs/phase4_v4_attempt4_20261109T185713Z
env -u PYTHONPATH PYTHONPATH=src .venv/bin/python scripts/verify_e2e_v1_4_1.py --offline runs/e2e_v1_4_2_checks/offline --live runs/e2e_v1_4_2_checks/live_recheck
```

Full unit suite with the approved offline cache:

```bash
env -u PYTHONPATH HF_HOME=/home/sankalp/projects/wt-e2e/runs/hf_home HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1 PYTHONPATH=src .venv/bin/python -m pytest -p no:cacheprovider -rfE
```

A6 compares IDs with the supplied reference, not the pytest exit code alone. The known reference failures/errors remain. This agent does not push; publication is left to the user.
