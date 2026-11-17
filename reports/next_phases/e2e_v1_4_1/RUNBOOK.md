# E2E v1.4.1 runbook

Run from `/home/sankalp/projects/wt-e2e` with this worktree's `.venv`. The 83-task registry, manifests, wheel, archives and local images are prepared. Model configs must be verified; provide their named API-key environment variables. No model call was made during implementation. The commands below describe future runs, not authorization to launch them in this session.

Three-task pilot (repair agent and V4 enabled):

```bash
env -u PYTHONPATH HF_HOME=/home/sankalp/projects/wt-e2e/runs/hf_home HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1 PYTHONPATH=src .venv/bin/python scripts/run_e2e.py \
  --mode pilot --manifest configs/e2e/live_checks_3.txt \
  --task-specs configs/e2e/task_specs_83.json \
  --primary-config configs/model/primary.yaml --generator-config configs/model/generator.yaml \
  --ledger-file runs/provider_spend_ledger.json --deepseek-cap-usd 4.00 \
  --output runs/e2e_v1_4_1_pilot
```

Audited 83-task UM repair arm, DeepSeek V4 (clean HEAD must equal the annotated tag):

```bash
env -u PYTHONPATH HF_HOME=/home/sankalp/projects/wt-e2e/runs/hf_home HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1 PYTHONPATH=src .venv/bin/python scripts/run_e2e.py \
  --mode audited --freeze-tag e2e-v1.4.1-frozen --manifest configs/e2e/tasks_83.txt \
  --task-specs configs/e2e/task_specs_83.json \
  --primary-config configs/model/primary_umgpt.yaml --generator-config configs/model/generator.yaml \
  --ledger-file runs/provider_spend_ledger.json --deepseek-cap-usd 4.00 \
  --um-cap-usd 20.00 --um-job-cap-usd 3.00 --output runs/e2e_v1_4_1_um_audited
```

For the DeepSeek repair arm, change only `--primary-config` to `configs/model/primary.yaml` and use a separate output folder. Both arms must keep the same ledger file: changing output folders does not reset the shared DeepSeek cap. The fixed caps can stop a run before all 83 tasks complete. Every stop records completed/not-completed IDs in `completion.json`; grading is a separate step after the run is sealed.

Resume by repeating the identical command and output folder. A complete frozen repair patch is never regenerated; unfinished verification moves into the task's `attempts/`. Previously paid work remains charged. A fresh V4 stage cannot silently reset a spent per-task ceiling; it stops before new paid work if its full ceiling cannot fit.

For new instances, supply the task-prep job's validated registries with `--task-specs file1.json file2.json`; no cohort name is special. Missing task specs become per-task `NO_TASK_SPEC` V2/V3 absences. The shared schema is in `docs/TASK_SPEC_SCHEMA.md`. Do not rebuild the already frozen registry before an audited run at this tag.

Reproduce the no-model live check in a fresh output folder:

```bash
env -u PYTHONPATH HF_HOME=/home/sankalp/projects/wt-e2e/runs/hf_home HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1 PYTHONPATH=src .venv/bin/python scripts/run_e2e.py \
  --mode pilot --manifest configs/e2e/live_checks_3.txt --task-specs configs/e2e/task_specs_83.json \
  --primary-config configs/model/primary.yaml --generator-config configs/model/generator.yaml \
  --verify-only-from /home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/paired_frozen \
  --skip-v4 --output runs/e2e_v1_4_1_checks/live_recheck
```

Offline A1/A2, followed by the independent checker (raw sealed captures remain read-only):

```bash
env -u PYTHONPATH PYTHONPATH=src .venv/bin/python scripts/check_e2e_offline.py --output runs/e2e_v1_4_1_checks/offline_final --captures /home/sankalp/projects/cis695-v2-scg-ubuntu-publication/runs/phase4_v4_attempt4_20261109T185713Z
env -u PYTHONPATH PYTHONPATH=src .venv/bin/python scripts/verify_e2e_v1_4_1.py --live runs/e2e_v1_4_1_checks/live_recheck
```

Full unit suite with the approved offline cache:

```bash
env -u PYTHONPATH HF_HOME=/home/sankalp/projects/wt-e2e/runs/hf_home HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1 PYTHONPATH=src .venv/bin/python -m pytest -p no:cacheprovider -rfE
```

A6 compares IDs with the supplied reference, not the pytest exit code alone. The known reference failures/errors remain. This agent does not push; publication is left to the user.
