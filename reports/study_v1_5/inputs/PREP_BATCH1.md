# Phase 10 batch 1 preparation

## Disk before preparation

`df -h /`

```text
Filesystem      Size  Used Avail Use% Mounted on
/dev/nvme0n1p6  520G  245G  250G  50% /
```

Available bytes from `df -B1 --output=avail /` were 267,570,450,432. The 150 GB gate passed.

`docker system df`

```text
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          107       1         153.5GB   151.6GB (98%)
Containers      1         0         71.68MB   71.68MB (100%)
Local Volumes   0         0         0B        0B
Build Cache     0         0         0B        0B
```

## Preparation environment

The job uses this worktree's offline-synced `.venv`, `PYTHONPATH=src`, `HF_HOME=$PWD/runs/hf_home`, `HF_DATASETS_OFFLINE=1`, and `HF_HUB_OFFLINE=1`. The local Verified cache and pinned preparation wheel passed their hash checks.

None of the 60 requested IDs had a `.tar` in `/home/sankalp/cg_repos/task_archives` before preparation. The task-prep README and report use the default container Git archive path for new tasks, so the job uses that path with `--allow-pull`.

## Initial preparation and Docker Hub wait

The initial pass verified 52 tasks. Three tasks failed source integrity and five stopped at the image stage. The independent verifier passed all 52 prepared entries alongside its three frozen parity anchors.

Docker Hub returned `toomanyrequests` on the last two failed image tags. The tmux resume job waits on the existing tag, then retries original image-stage failures before allocating reserves. Its output appends to `runs/study_v1_5/prep_batch1.log`.

At the 15:54 Phoenix-time check on 20 Nov, Docker Hub was still rate-limiting the same tag. The resume session remained active. Root availability at this checkpoint was 218 GiB (233,420,587,008 bytes), and Docker reported 161 images occupying 183.2 GB. The post-preparation disk snapshot is pending the completed batch.

## Preparation results

The final batch has 60 tasks with 4 replacement slots. Reserve IDs were consumed in order from draw position 109 onward.

| Original slot | Failed ID | Stage | Reason | Reserve ID |
|---:|---|---|---|---|
| 1 | `sphinx-doc__sphinx-9229` | `integrity_preflight` | Source integrity mismatch: setup.py (non_export_subst_source_mismatch), tox.ini (non_export_subst_source_mismatch) | `pydata__xarray-4356` |
| 19 | `sphinx-doc__sphinx-9281` | `integrity_preflight` | Source integrity mismatch: setup.py (non_export_subst_source_mismatch), tox.ini (non_export_subst_source_mismatch) | `django__django-13343` |
| 26 | `sphinx-doc__sphinx-9258` | `integrity_preflight` | Source integrity mismatch: setup.py (non_export_subst_source_mismatch), tox.ini (non_export_subst_source_mismatch) | `sympy__sympy-15017` |
| 59 | `sphinx-doc__sphinx-9367` | `integrity_preflight` | Source integrity mismatch: setup.py (non_export_subst_source_mismatch), tox.ini (non_export_subst_source_mismatch) | `pydata__xarray-4687` |

Original IDs recovered on the same Docker image tags

- `django__django-13925` passed on retry after an image metadata error. Command '['/usr/bin/docker', 'manifest', 'inspect', 'swebench/sweb.eval.x86_64.django_1776_django-13925@sha256:dfcffa35bc68e3b014c6e4c041210721cfc17179fd372e4f7385c6e6384d5db6']' returned non-zero exit status 1.
- `sphinx-doc__sphinx-8269` passed on retry after an image metadata error. Command '['/usr/bin/docker', 'manifest', 'inspect', 'swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-8269:latest']' returned non-zero exit status 1.
- `sympy__sympy-23262` passed on retry after an image metadata error. Command '['/usr/bin/docker', 'manifest', 'inspect', 'swebench/sweb.eval.x86_64.sympy_1776_sympy-23262@sha256:7c8f88bc121da29758c49f4877c3b34d5503e30d81b53b7f7e6bc802ad3a7170']' returned non-zero exit status 1.
- `django__django-14493` passed on retry after an image metadata error. Command '['/usr/bin/docker', 'manifest', 'inspect', 'swebench/sweb.eval.x86_64.django_1776_django-14493:latest']' returned non-zero exit status 1.

## Verification

- Checked 420 Phase 2 manifest records and local file presence for the final 60 IDs across six public systems and the reference set.
- Ran `verify_task_prep.py` on the batch registries with the three frozen parity anchors required by its CLI. All final tasks passed.
- Exported `configs/e2e/task_specs_test1_e2e_v141.json` and its hash-bound provenance sidecar in final slot order. The validator from `e2e-v1.4.1-frozen` loaded all 60 entries from the export.
- Docker returned the recorded pinned image ID for all 60 final task tags.

## Disk after preparation

`df -h /`

```text
Filesystem      Size  Used Avail Use% Mounted on
/dev/nvme0n1p6  520G  278G  217G  57% /
```

Available bytes were 232,280,428,544. Root filesystem availability fell by 35,290,021,888 bytes (32.87 GiB) during preparation.

`docker system df`

```text
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          170       1         183.9GB   182GB (98%)
Containers      1         0         71.68MB   71.68MB (100%)
Local Volumes   0         0         0B        0B
Build Cache     0         0         0B        0B
```
