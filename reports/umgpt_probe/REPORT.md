**Verdict: the three gpt-4.1-mini tasks were attempted without Azure filtering, but 1 V4 generator(s) could not run and 1 ended in error. Observed costs include these incomplete chains; correctness was not evaluated.**

Date: 2026-11-16 (America/Phoenix). Branch: `feature/umgpt-routing`.
All amounts are USD list-price estimates, including ledger costs. No UM billing receipt was collected.

## Scope and provenance

Preflight confirmed a clean tree on the requested branch, origin/main as an ancestor of HEAD, key-entry presence without displaying its value, and all 38 frozen files unchanged.
Only the three authorized tasks were attempted, on gpt-4.1-mini. Each chain is `run_task` → `reliability.verifier.reproduction_v1_4.run_reproduction`, with the UM generator and an 80-step cap. `verify_task` was never called. **V1, V2, V3 and oracle: not run in probe.** No policy decision or correctness grade was produced.
The repair agent retains its existing prompt, decoding parameters, 100-step cap and timeouts; only routing and the explicitly authorized cost ceiling differ. V4 receives the patch and uses its own containers.
Account cap $20; job cap $3 including model verification; task cap $0.75 combined, repair up to $0.60, V4 using the remainder. A conservative uncached reservation precedes every request; an estimate above $0.30 stops before sending.
The ledger was copied from `/home/sankalp/projects/cis695-v2-scg-ubuntu-publication/runs/umgpt_spend_ledger.json` to `runs/umgpt_spend_ledger.json`; its 1 historical entries were preserved. Earlier HTTP 401 cost $0 and was not retried in this session.
The first task startup hit an inherited-Python-path error before any task API call ($0 task spend). Its artifacts remain in `runs/umgpt_probe/precall_bootstrap_20261116`. A dedicated ignored environment was installed offline from `uv.lock`, import-affecting shell variables were cleared, and the same tasks were launched. No paid trajectory was rerun.
Execution commit and interpreter details are preserved in `execution_meta.yaml` (copied from `runs/umgpt_probe/meta.yaml`); sanitized cost records are committed in `task_measurements.json`, `spend_evidence.json` and `verification.json`.

## Live model verification

| Requested | Served model | Fingerprint | Input / cached / output | Cost | Finish |
|---|---|---|---:|---:|---|
| openai/gpt-4.1-mini | gpt-4.1-mini-2025-04-14 | fp_36de3d5958 | 61 / 0 / 16 | $0.00005000 | tool_calls |
| openai/gpt-4.1 | gpt-4.1-2025-04-14 | fp_8c4c3e6d7a | 61 / 0 / 16 | $0.00025000 | tool_calls |
| openai/gpt-4o-mini | gpt-4o-mini-2024-07-18 | fp_486a957a0b | 61 / 0 / 16 | $0.00001875 | tool_calls |

All three passed a real well-formed `bash` tool call in the displayed order. The full `x-ratelimit-*` headers are retained in `verification.json`; they indicate request/token allocations, not a dollar balance. Verification total: **$0.00031875**. gpt-4.1 and gpt-4o-mini were used only for verification.

## Per-task measurements

Input includes cached input; cached is a subset. Repair steps are provider calls (the ledger records retries separately if any). V4 steps come from v1.4 generation telemetry. Wall time includes stage container work. All report figures can be reconstructed from the committed numeric evidence.

| Task | Repair steps | Input / cached / output | Ledger cost | LiteLLM cost | Termination / subtype | Patch bytes | Wall s |
|---|---:|---:|---:|---:|---|---:|---:|
| django__django-14373 | 32 | 118342 / 47488 / 1454 | $0.03541680 | $0.03541680 | submitted | 418 (yes) | 76.74 |
| scikit-learn__scikit-learn-12973 | 97 | 1293922 / 942208 / 6523 | $0.24534320 | $0.24534320 | submitted | 90240 (yes) | 205.25 |
| django__django-16899 | 100 | 1803674 / 1358976 / 15373 | $0.33837360 | $0.33837360 | step limit / configured max_steps=100 | 0 (no) | 247.45 |

| Task | V4 steps | Fired limit / termination | Tests written | Input / cached / output | Ledger cost | LiteLLM cost | Generator / total wall s |
|---|---:|---|---:|---:|---:|---:|---:|
| django__django-14373 | 15 | none / Submitted | 3 | 36111 / 8320 / 2076 | $0.01527000 | $0.01527000 | 36.60 / 42.18 |
| scikit-learn__scikit-learn-12973 | 18 | none / RepeatedFormatError | 3 | 51380 / 7296 / 2624 | $0.02256160 | $0.02256160 | 46.49 / 55.42 |
| django__django-16899 | — | not run: patch is empty | 0 | 0 / 0 / 0 | $0.00000000 | $0.00000000 | — / 0.00 |

The frozen v1.4 trajectory-based token telemetry omits some paid responses. The V4 table and projections use complete per-call ledger usage. Original telemetry totals are retained below:

| Task | V1.4 telemetry input / output | Per-call ledger input / output |
|---|---:|---:|
| django__django-14373 | 29341 / 1794 | 36111 / 2076 |
| scikit-learn__scikit-learn-12973 | 36421 / 1970 | 51380 / 2624 |
| django__django-16899 | None / None | 0 / 0 |

| Task | Repair + V4 ledger cost | Served model(s) | Fingerprint(s) |
|---|---:|---|---|
| django__django-14373 | $0.05068680 | gpt-4.1-mini-2025-04-14 | fp_36de3d5958, fp_8ebcb6c932 |
| scikit-learn__scikit-learn-12973 | $0.26790480 | gpt-4.1-mini-2025-04-14 | fp_36de3d5958, fp_8ebcb6c932 |
| django__django-16899 | $0.33837360 | gpt-4.1-mini-2025-04-14 | fp_36de3d5958, fp_8ebcb6c932 |

Job total including verification: **$0.65728395**. Account ledger total: **$0.65728395**.
No cost ceiling fired. The final repair reached its unchanged 100-step limit; V4 then recorded an empty-patch skip.

## Filtering and prompt caching

Across 265 new provider calls: **0 hard filtering events**, 0 calls with `protected_material_code.detected=true`. Every call records finish reason, protected-code detected/filtered flags, and any-category filtered flags. Detection alone does not stop execution; `content_filter` or any `filtered=true` does.
Hard filtering steps: none.

| Stage | Input | Cached | Cached share |
|---|---:|---:|---:|
| repair | 3215938 | 2348672 | 73.03% |
| V4 | 87491 | 15616 | 17.85% |
| all calls | 3303612 | 2364288 | 71.57% |

0 task calls had a ledger/LiteLLM price difference larger than $0.0000000001. The UM route uses list-price estimates for budget enforcement; the gateway usage and caching metadata do not establish actual UM charges. No distinct UM billing rate or discount was verified.

## 10-task and 83-task projections

List prices are from this branch’s `src/reliability/umgpt.py:PRICES` and model YAML pricing blocks, in USD per million tokens. Input prices below apply to uncached tokens; cached tokens use the separate cache rate.

| Model | Uncached input | Cached input | Output |
|---|---:|---:|---:|
| gpt-4.1-mini | $0.4 | $0.1 | $1.6 |
| gpt-4.1 | $2 | $0.5 | $8 |
| gpt-4o-mini | $0.15 | $0.075 | $0.6 |

The observed mean includes V4 that could not run: django__django-16899: patch is empty. Its zero V4 spend is an observed skip, not a measurement of generator cost for that task.

The measured mean includes early V4 errors: scikit-learn__scikit-learn-12973: RepeatedFormatError. Successful V4 generation could cost more; these projections preserve the observed terminations.

Projections multiply the three measured combined repair+V4 task costs or their repriced token counts. Verification is a one-time probe overhead and is excluded. Worst-case uses the most expensive of these three tasks; it is not a bound on unseen tasks. Repricing assumes identical trajectories and cache shares, which other models may not produce.

| Model / basis | Mean per task | Worst task | 10 × mean | 10 × worst | 83 × mean | 83 × worst |
|---|---:|---:|---:|---:|---:|---:|
| gpt-4.1-mini (measured) | $0.21898840 | $0.33837360 | $2.18988400 | $3.38373600 | $18.17603720 | $28.08500880 |
| gpt-4.1 (repriced, not measured) | $1.09494200 | $1.69186800 | $10.94942000 | $16.91868000 | $90.88018600 | $140.42504400 |
| gpt-4o-mini (repriced, not measured) | $0.11167425 | $0.17785170 | $1.11674250 | $1.77851700 | $9.26896275 | $14.76169110 |

The observed gpt-4.1-mini 83-task projection is $18.17603720 from the mean and $28.08500880 from the worst task, compared with the $20 account cap. The skipped/errored V4 stages limit a full-run budget decision. The gpt-4o-mini projection remains repriced, not measured.

## Stored DeepSeek comparison (read-only numeric extraction)

`scripts/extract_umgpt_deepseek_numeric.py` reads only the authorized repair token/step/cost/time fields and V4 generation numeric telemetry in `~/projects/cis695-agent-reliability/runs/main_50_a` and `main_50_b`. The same three tasks are not all present in either run, so these are **whole-set means**, not matched-task comparisons. No trajectory, issue discussion, patch, correctness decision, or oracle record was read from the old runs. DeepSeek cost values are the stored usage.api_cost_usd and V4 generation.cost_usd; historical billing receipts were not inspected.

| Run | Repair n | Mean input / output | Mean repair cost | Mean repair wall s | V4 numeric n | Mean V4 steps | Mean V4 cost | Paired combined mean (n) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| main_50_a | 50 | 2661851.84 / 33949.66 | $0.06877844 | 348.58 | 43 | 26.16 | $0.02609099 | $0.08289084 (43) |
| main_50_b | 50 | 2514663.02 / 33743.82 | $0.06672511 | 399.60 | 44 | 29.16 | $0.03076409 | $0.09563231 (44) |

Old repair records do not contain numeric step counts or cached-token counts; those are unreported. Old V4 generation records report steps and cost but do not report token counts, cached tokens or generator wall time. Missing V4 values are excluded from V4/paired means and are never treated as zero. Full/baseline V4 telemetry is deduplicated per task. The different populations and unknown historical cache shares limit direct cost comparisons.

## Independent spend and frozen-file check

`python3 scripts/verify_umgpt_probe.py` uses only the standard library. It independently reprices token counts, joins per-call IDs to the persistent ledger, checks the report numbers below, and compares frozen-file bytes/hashes against `origin/main`. It also checks local raw records when available.

Validation: 75 focused tests passed (UM mocked transport, repair runner, direct V4 orchestration, and independent audit tamper checks); Ruff passed for every changed Python file.

```text
PASS: 265 per-call records reconcile with 266 ledger entries; no reservations.
PASS: django__django-14373: repair=$0.03541680 V4=$0.01527000 total=$0.05068680
PASS: scikit-learn__scikit-learn-12973: repair=$0.24534320 V4=$0.02256160 total=$0.26790480
PASS: django__django-16899: repair=$0.33837360 V4=$0.00000000 total=$0.33837360
PASS: verification=$0.00031875; job=$0.65728395; account=$0.65728395; report matches.
PASS: visible task costs/tokens and all 10/83-task projections match independent calculations.
PASS: all 38 frozen-file hashes match origin/main and the recorded manifest.
```

<!-- spend-audit-start -->
```json
{
  "tasks": {
    "django__django-14373": {
      "total": {
        "input_tokens": 154453,
        "cached_input_tokens": 55808,
        "output_tokens": 3530,
        "cost_usd": 0.0506868
      },
      "agent": {
        "input_tokens": 118342,
        "cached_input_tokens": 47488,
        "output_tokens": 1454,
        "cost_usd": 0.0354168
      },
      "V4": {
        "input_tokens": 36111,
        "cached_input_tokens": 8320,
        "output_tokens": 2076,
        "cost_usd": 0.015270000000000002
      }
    },
    "scikit-learn__scikit-learn-12973": {
      "total": {
        "input_tokens": 1345302,
        "cached_input_tokens": 949504,
        "output_tokens": 9147,
        "cost_usd": 0.26790479999999994
      },
      "agent": {
        "input_tokens": 1293922,
        "cached_input_tokens": 942208,
        "output_tokens": 6523,
        "cost_usd": 0.24534320000000007
      },
      "V4": {
        "input_tokens": 51380,
        "cached_input_tokens": 7296,
        "output_tokens": 2624,
        "cost_usd": 0.0225616
      }
    },
    "django__django-16899": {
      "total": {
        "input_tokens": 1803674,
        "cached_input_tokens": 1358976,
        "output_tokens": 15373,
        "cost_usd": 0.33837360000000016
      },
      "agent": {
        "input_tokens": 1803674,
        "cached_input_tokens": 1358976,
        "output_tokens": 15373,
        "cost_usd": 0.33837360000000016
      },
      "V4": {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0
      }
    }
  },
  "verification": {
    "input_tokens": 183,
    "cached_input_tokens": 0,
    "output_tokens": 48,
    "cost_usd": 0.00031875
  },
  "job": {
    "input_tokens": 3303612,
    "cached_input_tokens": 2364288,
    "output_tokens": 28098,
    "cost_usd": 0.6572839499999997
  },
  "account": {
    "input_tokens": 3303612,
    "cached_input_tokens": 2364288,
    "output_tokens": 28098,
    "cost_usd": 0.6572839499999997
  }
}
```
<!-- spend-audit-end -->
