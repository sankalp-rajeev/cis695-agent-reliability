# Task preparation

Run from this worktree root with its own `.venv`:

```bash
export HF_HOME="$PWD/runs/hf_home"
export HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1
env -u PYTHONPATH PYTHONPATH=src .venv/bin/python scripts/prepare_tasks.py \
  --manifest configs/e2e/rest10_ids.json --cohort example \
  --out configs/e2e/task_specs_example.json
```

Choose a fresh output filename. Manifests accept JSON lists, cohort JSON objects
with `instance_ids`, CSV `instance_id` columns, or one ID per line. Default archive
folder is `/home/sankalp/cg_repos/task_archives`. Existing files are verified,
never replaced. Pulling requires `--allow-pull`; preparation containers always use
immutable image IDs, `--pull=never`, network none and both package-cache masks.
The CLI exits nonzero if any task fails and publishes only VERIFIED tasks.
Ineligible tasks have eligibility evidence and no registry entry.

The wheel under `runs/phase4_fix10_provenance/` is hash-verified against
`4e315ac60ff7b5b7186592b84d22df9befd898bba296a6b9665fdb3487fcd8f7`.
The installed swebench package is never an authority for task specs. Frozen tasks
retain the exact original projection; other tasks have a four-column projection
in their evidence directory. No oracle columns are decoded.

`build_task_prep_cohorts.py` inspects local images, never pulls, and publishes
ID-only cohorts plus eligibility records. UNCHECKED images must pass the same
eligibility check when later prepared. `project_task_prep.py` uses the exact OCI
layer-union method from `manifest_disk_cost.py`; if registry manifests are rate
limited, `project_task_prep_sizes.py` reports tag-size-based estimates with the
sharing assumptions made explicit.

`verify_task_prep.py` uses the standard library and Docker CLI only. It checks
registry schema/identity, archive bytes and pax commit, receipt hashes/content,
local image IDs, golden expectations and cohort nesting/pilot rules. No candidate
patch, selected test list, model call or benchmark test execution is involved in
preparation. Existing source-integrity and pre-install authorities are unchanged.
