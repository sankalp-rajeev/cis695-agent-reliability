**Verdict: Frozen E2E runner integration PASS; main run cohort is 92. Golden and independent verification pass, with zero new unit failure/error IDs. Sphinx 10614 remains excluded, failing closed.**

`scripts/prepare_tasks.py` and `reliability.task_prep` prepare patch-independent Verified tasks. The frozen runner consumes its own `configs/e2e/task_specs_83.json` together with `configs/e2e/task_specs_add9_e2e_v141.json` from this branch. The earlier merged and additions registries remain preparation provenance. Accepted eligibility manifests and projections are retained; the execution cohort excludes Sphinx 10614 and is defined by `configs/e2e/cohorts/main92_run_order.txt`. No push or tag was made.

## Runner integration

`scripts/export_frozen_registry.py` exports the nine additions to cohort `main92_additions` using exactly the schema read with `git show e2e-v1.4.1-frozen:<path>` after `git fetch --tags origin`. The annotated tag resolves to `c5b352c83c6bd7e9afdcb465bf966535543192fc`; its schema documentation and `REGISTRY_SCHEMA` source hashes are pinned in the exporter. Exporter implementation: `215327a`.

The export supplies absolute `pre_install.wheel_path` and `pre_install.dataset_projection_path` values. Only the pinned wheel and the nine exact projections were copied to `/home/sankalp/projects/wt-e2e/runs/task_prep_inputs/`; every copy was hash-verified. All resolved specs, archive paths/hashes and receipt paths/hashes are unchanged. The three preparation-only fields moved into `task_specs_add9_e2e_v141.provenance.json`, keyed by instance ID under `tasks`, with the exported registry SHA-256. Reconstructing the original registry from the export and sidecar succeeds exactly (`export_integrity.json`), including all original task metadata.

| File | SHA-256 |
|---|---|
| `/home/sankalp/projects/wt-e2e/configs/e2e/task_specs_83.json` | `9e55c5a82501753f19f5f83cdcab69afe178a9800aaa848918867a5a8af1d5fb` |
| `configs/e2e/task_specs_add9_e2e_v141.json` | `bee27f256d507da44b8fe9583b5dddd2023700e728690cce34c3434475e39e2d` |
| `configs/e2e/task_specs_add9_e2e_v141.provenance.json` | `33a81ff380012ba354d769ffd9e7fe4f186cbcb51c861aa66cbf16fb450d0ee2` |
| `configs/e2e/cohorts/main92_run_order.txt` | `9f0164f539539699acea3208f2af1a8ae6bfd31e3390f4aa7a9be5e6a93769ca` |
| `reports/next_phases/task_prep/frozen_runner_load.json` | `1c63f013644d2d6de60ad7ff06b3b495920d76c2ffa8464d26ebee1c10f72dae` |

The frozen consumer's own `reliability.verifier.task_specs.load_registries` was run from `/home/sankalp/projects/wt-e2e` with that worktree's `.venv/bin/python`, `PYTHONPATH=src` and bytecode writes disabled. It loaded the two registries above and returned **92 tasks with no error**, re-resolving all pre-install specs. `frozen_runner_load.json` records both registry hashes, validator hash, interpreter, commit and clean-checkout proof. No frozen runner file, existing frozen input, `source_integrity` or `pre_install` was edited.

`main92_run_order.txt` contains the 83 IDs from the tag's `configs/e2e/tasks_83.txt` in exactly that order, followed by the nine additions in sorted order. All 92 IDs are unique; requests and Sphinx 10614 are absent. The comparable 83 therefore precede every addition under a budget stop.

The full unit suite was run once more with the same prescribed command and offline HF environment: `6 failed, 1484 passed, 7 skipped, 17 errors in 60.24s (0:01:00)`. ID comparison against the local `7fefe1d` reference finds **zero new failed/error IDs** and **no reference failures now passing** (`unit_comparison_runner_integration.json`). The independent checker also passes all nine registries, **208 retained entries**, plus golden and cohort checks; output is in `independent_check_runner_integration.txt`. Its registry list excludes the provenance sidecar, which is not a task registry. Ruff passes for the export implementation.

## Golden

Before preparing the remaining tasks, `check_task_prep_parity.py` called `phase4_launch.validate_inputs` against the full frozen inputs. Three fresh scratch preparations matched every requested field and the entire decoded source receipt. Final committed code also rebuilt the three into a second fresh scratch folder; the independent checker compared both preparations with the frozen expectations and receipts.

| Instance | Archive SHA-256 | Image ID | Resolved pre_install | Preflight identity / full receipt | Runner | Django parallel |
|---|---|---|---|---|---|---|
| django__django-10973 | equal | equal | equal | equal / equal | django (equal) | False (equal) |
| sympy__sympy-13480 | equal | equal | equal | equal / equal | pytest (equal) | None (equal) |
| pytest-dev__pytest-10051 | equal | equal | equal | equal / equal | pytest (equal) | None (equal) |

Exact expected fields and hashes are in `parity.json`; actual artifacts are in both parity registries. The wheel SHA-256 in every registry entry is `4e315ac60ff7b5b7186592b84d22df9befd898bba296a6b9665fdb3487fcd8f7`. Specs resolve through the pinned 4.0.4 wheel only; the installed 5.0.2 package is never used for that purpose.

The original golden archive bytes matched directly: Git order, commit mtimes, `testbed/` prefix and global pax commit comment were preserved. Two later Matplotlib tasks exposed Git 2.25's unsupported `%(describe:tags=true)` expansion. New `.expanded.tar` files materialize only the exact bytes already proven by unchanged `source_integrity`; a second full preflight verifies them. Their old archives remain intact. Tar member order, metadata and pax comment are retained deterministically; unit tests check repeatability and original-file preservation.

Frozen SymPy runner metadata remains `pytest`, as `validate_inputs` derives it. `discover_runner` is called, and `runner_provenance.effective_name` records `sympy`; the existing collection adapter repairs the frozen metadata when it finds SymPy's native runner.

## Eligibility

All 106 locally present Verified images were checked using static package names/version assignments in offline, masked containers: **98 ELIGIBLE, eight INELIGIBLE_UNMASKABLE_COPY**. The other 394 are UNCHECKED until their images are pulled and checked. No repository code was imported by the version probe. It scans `/opt` (including conda envs and pip/_vendor), `/usr/local/lib`, `/usr/lib`, `/root` and `/tmp`, pruning the two masks and prohibited paths.

| Main-study excluded instance | Base version | Observed newer version | Evidence path |
|---|---|---|---|
| psf__requests-1142 | 1.1.0 | 2.32.3 | `/opt/miniconda3/envs/testbed/lib/python3.9/site-packages/pip/_vendor/requests/__version__.py` |
| psf__requests-1724 | 2.0.1 | 2.22.0 | `/opt/miniconda3/envs/testbed/lib/python2.7/site-packages/pip/_vendor/requests/__version__.py` |
| psf__requests-1766 | 2.0.1 | 2.32.3 | `/opt/miniconda3/envs/testbed/lib/python3.9/site-packages/pip/_vendor/requests/__version__.py` |
| psf__requests-2317 | 2.4.3 | 2.32.3 | `/opt/miniconda3/envs/testbed/lib/python3.9/site-packages/pip/_vendor/requests/__version__.py` |
| psf__requests-2931 | 2.9.0 | 2.32.3 | `/opt/miniconda3/envs/testbed/lib/python3.9/site-packages/pip/_vendor/requests/__version__.py` |
| psf__requests-5414 | 2.26.0 | 2.32.3 | `/opt/miniconda3/envs/testbed/lib/python3.9/site-packages/pip/_vendor/requests/__version__.py` |
| psf__requests-6028 | 2.27.0 | 2.32.3 | `/opt/miniconda3/envs/testbed/lib/python3.9/site-packages/pip/_vendor/requests/__version__.py` |

The seven-task gate succeeded automatically before preparing the ten. All seven images remain present. The additional locally present ineligible instance is psf__requests-1921. All eight requests instances are excluded from the larger cohorts. Complete base/copy paths and versions are in `eligibility.json`; `requests_gate.json` preserves the prerequisite gate.

## The ten additions

Only stored `instance_id`, `termination`, patch `size_bytes` and infrastructure fields were projected from repair records. The final run for each of these ten has `termination=step_limit` and patch size zero. Matplotlib 21568's initial completed 589-byte patch was superseded by the stored rerun with zero bytes. Requests records are also projected in `run_status.json`; their package-copy exclusion is independent of whether their agent produced a patch.

| Instance | Stored final agent run | Eligibility | Preparation |
|---|---|---|---|
| astropy__astropy-13398 | step_limit; 0 bytes | ELIGIBLE | VERIFIED |
| django__django-12663 | step_limit; 0 bytes | ELIGIBLE | VERIFIED |
| matplotlib__matplotlib-21568 | step_limit; 0 bytes | ELIGIBLE | VERIFIED |
| matplotlib__matplotlib-22865 | step_limit; 0 bytes | ELIGIBLE | VERIFIED |
| matplotlib__matplotlib-24627 | step_limit; 0 bytes | ELIGIBLE | VERIFIED |
| matplotlib__matplotlib-25332 | step_limit; 0 bytes | ELIGIBLE | VERIFIED |
| pylint-dev__pylint-4551 | step_limit; 0 bytes | ELIGIBLE | VERIFIED |
| pylint-dev__pylint-8898 | step_limit; 0 bytes | ELIGIBLE | VERIFIED |
| sphinx-doc__sphinx-10614 | step_limit; 0 bytes | ELIGIBLE | FAIL: tox.ini source mismatch (no registry entry) |
| sphinx-doc__sphinx-7748 | step_limit; 0 bytes | ELIGIBLE | VERIFIED |

Sphinx 10614's pinned spec contains `sed -i 's/pytest/pytest -rA/' tox.ini` followed by `apt-get`. `pre_install.source_edit_commands` deliberately refuses a mixed source/system-command sequence as byte-proof authority. Its archive equals the base blob while the image tox.ini includes `-rA`, so unchanged `source_integrity` returns `non_export_subst_source_mismatch`. The task is eligible but not runnable under the present guard. No source-integrity/pre-install change, frozen-input change, image edit or exemption was introduced. The failed receipt and `failures.json` are in the final evidence folder.

## Cohorts and repo counts

The deterministic nesting is **93 ⊂ 200 ⊂ 492**. `main100.json` retains the 93 eligible IDs and lists the seven excluded main-study requests IDs. Readiness is separate: 92 currently have registry entries.

The 200 starts with those 93 and adds 107 using seed 695. Hamilton largest-remainder quotas weight additions by the non-excluded Verified repo mix; quotas are capacity constrained after fixed and pilot exclusions, with lexicographic ties. Each repo samples sorted IDs with `random.Random(695)`, iterating repos in sorted order. Every ID in `manifests/pilot.csv` is excluded from the 200. This follows the tuning-task exclusion rationale in `main_100.yaml`.

`verified500.json` contains every non-excluded Verified instance: 492 after excluding all eight requests instances. Its `pilot_instances` field lists the nine eligible pilot IDs for separate reporting. UNCHECKED members are provisional and must be dropped if their on-pull eligibility check fails.

| Repo | Main eligible | 200 | Full eligible population |
|---|---:|---:|---:|
| astropy/astropy | 5 | 10 | 22 |
| django/django | 32 | 83 | 231 |
| matplotlib/matplotlib | 19 | 26 | 34 |
| mwaskom/seaborn | 1 | 1 | 2 |
| pallets/flask | 1 | 1 | 1 |
| pydata/xarray | 5 | 10 | 22 |
| pylint-dev/pylint | 7 | 9 | 10 |
| pytest-dev/pytest | 7 | 11 | 19 |
| scikit-learn/scikit-learn | 5 | 12 | 32 |
| sphinx-doc/sphinx | 6 | 16 | 44 |
| sympy/sympy | 5 | 21 | 75 |

Full-population pilot IDs: `astropy__astropy-12907`, `django__django-14373`, `django__django-14725`, `django__django-16899`, `matplotlib__matplotlib-26113`, `mwaskom__seaborn-3187`, `pylint-dev__pylint-6386`, `scikit-learn__scikit-learn-12973`, `sphinx-doc__sphinx-10449`.

## Disk and time projection (dry run)

No image layers were pulled and no archives were built for the 200/492 expansion. Exact OCI layer-union queries following `manifest_disk_cost.py` were blocked by Docker Hub's unauthenticated registry pull limit. A throttled metadata-only fallback collected all 500 amd64 tag sizes and digests (`image_sizes.json`, with source URLs). The estimates below explicitly differ from an exact shared-layer union.

Free disk at projection: **285.97 GB** (decimal GB). Local Docker image store: 153.50 GB for 106 Verified images. Store-average estimates apply the current store/compressed-image-sum ratio (0.9581); conservative estimates give no sharing credit and apply each repo's maximum observed extracted/compressed ratio. Neither is a mathematical bound.

| Cohort | Missing images | Missing compressed sum, no sharing (GB) | Image disk: calibrated / conservative (GB) | New archive estimate (GB) | Free after: calibrated / conservative (GB) |
|---|---:|---:|---:|---:|---:|
| verified200 (200) | 107 | 142.90 | 136.91 / 355.90 | 3.86 | 145.20 / -73.79 |
| verified500 (492) | 394 | 503.99 | 482.87 / 1261.58 | 14.25 | -211.15 / -989.86 |

The 200 preserves the 50 GB reserve only under the calibrated estimate; exact layer resolution is still needed before treating that scale as disk-safe. The 492 expansion exceeds available disk even under the calibrated estimate. No expansion is authorized or attempted.

Observed initial plus repair-attempt preparation time on the ten: **5.37 s/task**. A fresh final pass with the finished tool averaged **3.36 s/task**. Both include the Sphinx failure and assume images are local; no pull time is measured. Archive estimates use observed per-repo tar means.

| Cohort | Serial preparation projection, initial + retry cost | Remaining after main 93 |
|---|---:|---:|
| verified200 (200) | 17.90 min | 9.58 min |
| verified500 (492) | 44.03 min | 35.71 min |

These are preparation-attempt times, not guarantees that every task reaches VERIFIED; they exclude future image downloads, model work, collection and test execution. `projection.json` records all assumptions and individual timing values.

## prepared_default Django choices

- `django__django-12663`: `django_parallel_one=false`, `prepared_default`. Fix 17 used observed frozen commands, not a label-free rule; every frozen Django task used false, so the prepared task takes that majority setting.

## Independent check

Command (with the same absolute HF_HOME and both offline flags as all other project runs):

```bash
env -u PYTHONPATH PYTHONPATH=src .venv/bin/python scripts/verify_task_prep.py --registries configs/e2e/task_specs_*.json
```

The checker uses only the standard library and Docker CLI. Repeated entries across retained attempts are intentional; registry task IDs are unique within each file. Output:

```text
REGISTRY configs/e2e/task_specs_main100.json: 92 tasks OK (schema, archive hash/pax, local image, receipt)
REGISTRY configs/e2e/task_specs_main100_rest10.json: 6 tasks OK (schema, archive hash/pax, local image, receipt)
REGISTRY configs/e2e/task_specs_main100_rest10_final.json: 9 tasks OK (schema, archive hash/pax, local image, receipt)
REGISTRY configs/e2e/task_specs_main100_rest10_retry1.json: 1 tasks OK (schema, archive hash/pax, local image, receipt)
REGISTRY configs/e2e/task_specs_main100_rest10_retry2.json: 2 tasks OK (schema, archive hash/pax, local image, receipt)
REGISTRY configs/e2e/task_specs_parity_attempt1.json: 3 tasks OK (schema, archive hash/pax, local image, receipt)
REGISTRY configs/e2e/task_specs_parity_final.json: 3 tasks OK (schema, archive hash/pax, local image, receipt)
REGISTRY configs/e2e/task_specs_phase4.json: 83 tasks OK (schema, archive hash/pax, local image, receipt)
GOLDEN: 3/3 task fields equal phase4_launch.validate_inputs expectations
COHORTS: 93 < 200 <= 492; nested, duplicate-free, requests excluded, pilot rules OK
MAIN COVERAGE: 92/93 have VERIFIED registry entries; 1 preparation failures
PASS: 199 registry entries independently verified; no reliability imports
```

## Unit suite and provenance

Exact suite command, from this worktree root and this worktree's own offline-created `.venv`:

```bash
env -u PYTHONPATH PYTHONPATH=src .venv/bin/python -m pytest -p no:cacheprovider -rfE
```

Every run set `HF_HOME=/home/sankalp/projects/wt-task-prep/runs/hf_home`, `HF_DATASETS_OFFLINE=1`, and `HF_HUB_OFFLINE=1`. Only Verified dataset/hub entries were copied; allocated cache size is **15 MB** (15499264 bytes). No shared-cache lock was needed.

Original preparation run result: `6 failed, 1484 passed, 7 skipped, 17 errors in 60.72s (0:01:00)`. Compared **test IDs**, not counts, with `/home/sankalp/projects/unit_baseline_7fefe1d/failing_ids.txt`: **zero new failing/error IDs**; all 23 reference failure/error IDs recur. **Reference failures now passing: none**, so there are no improvements requiring attribution. `unit_comparison.json` lists both complete ID maps. All 13 new tests pass in a focused run; Ruff passes for every new/modified source file. The three kernel isolation failures remain in the reference set.

No existing test, reference, `source_integrity.py`, `pre_install.py`, or frozen input was changed. The preparation and cohort-selection code consumes no candidate patch or prohibited dataset columns. The golden authority validates frozen candidate-artifact hashes as part of its established input check. Dataset rows are four-column Arrow IPC projections before decoding; only the original Arrow cache file is hashed opaquely as the existing frozen provenance requires.

Final preparation code is committed at `750af1f`; the merged registry is built at `8e2e438`. The branch remains local. No image, archive or registry was overwritten/deleted, and no task container used network access.
