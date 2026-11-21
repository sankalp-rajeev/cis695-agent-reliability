# Phase 4: V4 pilot

Status: ⛔ run sealed; failed: G1, G3.

## Pre-flight (20 Nov 2026)

### Pilot ids

The 51 arm B patch ids come from the `instance_id` column of `reports/rerun_v1/arm_B/analysis/patch_tasks.csv`. They were sorted, and then `random.Random(20261121).sample(sorted_ids, 10)` drew the pilot. The ids below are in sample order. None was hand-picked or replaced. They are written to `configs/study_v1_5/pilot_ids.json` (sha256 `9a5a79985b5f741cf71c02370b54c880fd1f55c0927e31379330fb8d8aeb89e0`).

| # | instance_id | repo |
|---:|---|---|
| 1 | matplotlib__matplotlib-25479 | matplotlib/matplotlib |
| 2 | django__django-13807 | django/django |
| 3 | django__django-15572 | django/django |
| 4 | django__django-16667 | django/django |
| 5 | pytest-dev__pytest-5809 | pytest-dev/pytest |
| 6 | django__django-12965 | django/django |
| 7 | django__django-16631 | django/django |
| 8 | django__django-11095 | django/django |
| 9 | astropy__astropy-13398 | astropy/astropy |
| 10 | sympy__sympy-13480 | sympy/sympy |

The sorted list of all 51 ids is in `reports/study_v1_5/pilot/dev_reference_ids.json` (sha256 `45aaf4ea8198a3ca59a170349149254596938a371c6f6bb2dc3e53e179f3e371`). Phase 6 reuses this list.

### Verify inputs

`scripts/make_verify_inputs.py` read the reference manifest (`runs/study_v1_5/patches/reference/tasks.json`, sha256 `5982ba8aed23769d95c0dc591eb0501d3b049bd5c22a572a7d59f3006b452ed7`) and wrote the 51 ids to `runs/study_v1_5/verify_inputs/dev_reference/`. It copied 51 patches, 0 of them empty, and each copy's sha256 matched the manifest. Phase 6 reuses this folder.

### Pinned images

For each of the 10 pilot tasks, `docker image inspect` returned the image id recorded in `task_specs_83.json` or the add9 e2e export. Result: 10 of 10 matched.

### Model and key

- `configs/model/generator.yaml` loads. Its provider is `deepseek`, its model id is `deepseek/deepseek-v4-flash`, its `verified.status` is `ok` and its sha256 is `c482616de300f99bac835f0a54983422f661dbf8f63d53e5970cda8ab2992c27`.
- The first key check stopped with `DEEPSEEK_API_KEY is not set`, because the worktree had no `.env`. A gitignored `.env` was then added.
- Key check passed. `scripts/verify_model.py --config configs/model/generator.yaml` sent one tool-calling request and was run without `--update`, so it wrote no config. The response had finish reason `tool_calls`, used 308 input and 39 output tokens and cost $0.00013920. The served model was `deepseek-flash`.
- The system fingerprint was `bc19ba97cbe016479903222bb1578db6`. That differs from the `aeb56401ca74e127821c4f9126dcb669` recorded in `generator.yaml` on 2026-09-30. The run does not check the fingerprint, and the protocol does not mention it. This is recorded and not acted on, as configs are frozen for this phase. The later study runs use the same served model.
- Provider balance from `GET /user/balance`: $9.03 USD, all topped up and none granted. That meets the ≥ $7 rule for two passes.

### V4 settings (`configs/verifier/v1_5.yaml`, sha256 `f3efb4ea8306e2b581216720e47d32a179484abd4a39515b63dd8e9c0fc8de72`)

| Setting | Value |
|---|---|
| v4_design | per_requirement |
| v4_passes | 2 |
| v4_max_requirements | 4 |
| `configs/agent/v4_requirements.yaml` sha256 | `85155d9494c3aaa7ce088551fbc400aa65f94992870170c7acc9911f1009297e` |
| `configs/agent/v4_tests_per_requirement.yaml` sha256 | `0a56118eb58e69ef1f18c973f25ee083f6b8e1a78ce0c3777d05f369772fe32a` |

### Run settings

The run will use `--mode pilot`. `audited` mode needs a freeze tag, and that tag is not created until Phase 5. The run will use the default ledger, `runs/provider_spend_ledger.json` in this worktree. That ledger does not exist yet, so it starts at $0, and the $1 cap then applies to both the account and the job. The header records `git_dirty: true`, because the pre-flight files are uncommitted at launch. They are committed with the phase, and the header's manifest sha256 binds the pilot id list.

## Results

The run ended with status `COMPLETE`. The seal check is `MATCH`: 685 files, and the `seal.json` sha256 is `ff2fe8d5b9ac11fd2eb21b26d2a2492a531d24f401efade7144fb80a603cd254`. The ledger records 558 calls for this job, 0 of them unsettled.

### Gates

| Gate | Rule | Measured | Result |
|---|---|---|---|
| G1 cost | mean ≤ $0.06 per task and no task above $0.15 | total $0.6703, mean $0.0670, max task $0.1585 | ⛔ fail |
| G2 coverage | ≥ 7 of 10 tasks with every requirement covered | 10 of 10 | ✅ pass |
| G3 leakage | audit exits 0, with no GOLD_LINE_IN_GENERATOR | exit 1, 122 GOLD_LINE_IN_GENERATOR | ⛔ fail |
| G4 infrastructure | errors on ≤ 1 of 10 tasks | 0 (none) | ✅ pass |

A task counts as an error for G4 if any of the following holds: it did not complete, its V2 or V3 infrastructure flag is set, it has no verification record, or its V4 absence is `error`. Costs are the ledger's settled call costs for this run's job key.

### Per task (gold patches, label-free)

Each requirement's verdict is shown as `id:verdict`. A requirement is UNCOVERED when it has no kept test. The decision and rule come from `scripts/decide_v1_5.py --switches r2=0,r3=0,r6=0`.

| instance_id | repo | reqs | kept p1/p2 | verdicts | V4 full pass | V2 (P) | decision | rule | min | cost |
|---|---|---:|---:|---|---|---|---|---|---:|---:|
| matplotlib__matplotlib-25479 | matplotlib/matplotlib | 3 | 3/3 | R1:PASS, R2:PASS, R3:PASS | yes | FAIL | FLAG | R5 | 22.2 | $0.1585 |
| django__django-13807 | django/django | 4 | 4/4 | R1:PASS, R2:PASS, R3:PASS, R4:PASS | yes | PASS | ACCEPT | R6 | 5.5 | $0.0597 |
| django__django-15572 | django/django | 4 | 4/4 | R1:PASS, R2:PASS, R3:PASS, R4:PASS | yes | PASS | ACCEPT | R6 | 4.5 | $0.0413 |
| django__django-16667 | django/django | 2 | 2/2 | R1:FAIL_CONFIRMED, R2:PASS | no | PASS | FLAG | R4 | 2.7 | $0.0203 |
| pytest-dev__pytest-5809 | pytest-dev/pytest | 1 | 1/1 | R1:PASS | yes | FAIL | FLAG | R5 | 1.8 | $0.0097 |
| django__django-12965 | django/django | 2 | 2/2 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | 5.4 | $0.0782 |
| django__django-16631 | django/django | 4 | 4/4 | R1:FAIL_CONFIRMED, R2:FAIL_SINGLE, R3:PASS, R4:FAIL_SINGLE | no | PASS | FLAG | R4 | 8.5 | $0.1108 |
| django__django-11095 | django/django | 3 | 3/3 | R1:NO_RESULT, R2:PASS, R3:PASS | no | NOT_AVAILABLE | FLAG | R7 | 4.6 | $0.0318 |
| astropy__astropy-13398 | astropy/astropy | 4 | 4/4 | R1:FAIL_CONFIRMED, R2:FAIL_CONFIRMED, R3:FAIL_CONFIRMED, R4:FAIL_CONFIRMED | no | NOT_AVAILABLE | FLAG | R4 | 10.8 | $0.1316 |
| sympy__sympy-13480 | sympy/sympy | 3 | 3/3 | R1:PASS, R2:PASS, R3:PASS | yes | NOT_AVAILABLE | FLAG | R8 | 42.4 | $0.0282 |

### Totals

- Minutes per task: median 5.4, max 42.4.
- Total DeepSeek cost: $0.6703.
- Gold patches with any V4 FAIL: 3 of 10.

Phase 4 outcome: ⛔ failed: G1, G3. Machine-readable results: `reports/study_v1_5/pilot/pilot_results.json`.
