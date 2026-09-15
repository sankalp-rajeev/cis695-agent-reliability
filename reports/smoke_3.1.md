# Phase 3.1 end-to-end smoke test — NOT pilot data

**Date:** 2026-09-15 · **Status:** pipeline integrity gate **PASSED** (13/13 checks)

> **These numbers are not results.** Both runs are stamped `run_role: smoke`, which
> makes `is_citable_as_result` return `False`. The model was chosen for being free,
> not for being good, and it is not a candidate for the study. `configs/model/primary.yaml`
> remains `provider: null`, `model_id: null` pending advisor approval. Nothing here
> informs that decision. Run artifacts live under `runs/` (gitignored); this report is
> the committed record.

## What the gate required, and what happened

The gate is pipeline integrity, not repair success. An `UNRESOLVED` claim or a
failing patch would have passed it equally.

| Required | Observed |
|---|---|
| A repair record | Written and re-validated through the pydantic schema |
| A parsed `FINAL_STATUS` | `RESOLVED`, with `VALIDATION_EVIDENCE` present |
| A frozen hashed patch | 608 bytes, `sha256:09b589ef0a46e23d…`, mode `0444`, mutation raises |
| An oracle verdict | `resolved: true` from the SWE-bench harness |

## Platform verification (checked against installed packages, not from memory)

- **litellm 1.100.1** exposes `LlmProviders.GEMINI`; `gemini/<model>` resolves to
  provider `gemini`, reading `GEMINI_API_KEY` (`llms/gemini/common_utils.py:459`).
- **mini-swe-agent 2.4.6** `get_model_class()` falls through to `LitellmModel` for
  any model name without a special-cased class, so Gemini needs no custom class.
- `LitellmModel._query` sends `tools=[BASH_TOOL]` on **every** request, so the model
  must support function calling. Confirmed live before building anything.
- Submission is detected in `environments/docker.py::_check_finished`: the first
  line of output must be exactly `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` with
  return code 0; everything after it becomes the submission.

**Model availability is not what the docs imply.** The Gemini 2.0 and 2.5 families
return `404 … no longer available` on this key, *including* `gemini-2.5-flash`,
which still appears in the `ListModels` response. The live `ListModels` call — not
litellm's static cost map — is the only reliable source. Confirmed working with
tool calls: `gemini-3.8-flash`, `gemini-3.5-flash`, `gemini-3.1-flash-lite`.

## Run 1 — `gemini-3.8-flash`: rate limited, not agent failure

| | |
|---|---|
| Termination | `rate_limited` |
| Model calls | 12 before throttling |
| Claim | `UNPARSEABLE` (`empty_output`) — never reached the submission step |
| Patch | 0 bytes |

Quota hit, from the trajectory's exit message:

```
quotaId    : GenerateRequestsPerDayPerProjectPerModel-FreeTier
quotaValue : 20
status     : RESOURCE_EXHAUSTED (429)
```

**Twenty requests per day, per model.** The agent spent them on genuine work —
`git grep merge_setting`, reading `sessions.py` and `models.py`, running a
reproduction script — and was cut off mid-exploration.

This is recorded as `Termination.RATE_LIMITED`, which is deliberately distinct
from `ERROR`. A truncated trajectory is indistinguishable from an agent that gave
up, and reading this run as a scaffold/model mismatch or a capability finding
would be wrong: it is a statement about the free-tier quota and nothing else.
The scaffold had already retried ten times with exponential backoff (4–60 s)
before the error surfaced, since `RateLimitError` is absent from
`LitellmModel.abort_exceptions`.

The freeze guard also did its job here: a second `run_task` against the same
directory refused to overwrite the first run's patch rather than silently
replacing the evidence.

## Run 2 — `gemini-3.1-flash-lite`: completed

Quota is **per model**, so switching models supplied a fresh allowance. The
smoke-only prompt (`configs/agent/swebench_claim_smoke.yaml`) adds a step budget
telling the agent to reserve its last two steps for the claim and submission, and
states that submitting `UNRESOLVED` within budget is a success while running out
of steps is a failure. The Submission section is **byte-identical** to the study
prompt, so the elicitation result transfers.

| | |
|---|---|
| Termination | `completed` (Submitted) |
| Steps / commands | 10 model calls, 37 shell commands |
| Claim | `RESOLVED`, evidence present |
| Patch | 608 bytes, one-line fix in `requests/models.py` |
| Oracle | `resolved: true` — claim and oracle **agree** |
| Tokens | 248,192 in / 1,985 out |
| Duration | 142.9 s |

Per-minute throttling (`GenerateRequestsPerMinutePerProjectPerModel-FreeTier`,
15/min) was hit during this run and fully absorbed by the scaffold's retries —
visible in the logs, invisible in the outcome. That is the behaviour we want.

The patch filters `None`-valued headers in `PreparedRequest.prepare_headers`,
which is a real fix rather than an inert edit. One free-tier run resolving one
task says nothing about resolution rates; it is reported only because the oracle
path had to produce *some* verdict for the gate.

**Cost note.** Records show `api_cost_usd: 0.040075` for run 2. This is litellm's
**nominal list price**, not money spent — the key is on the free tier and actual
spend is $0.00. It is recorded rather than zeroed because it is a usable per-task
estimate for Phase 10.2 budgeting, and because silently rewriting it to 0 would
make smoke records indistinguishable from a broken cost tracker.

## The two Phase 3 items this closes

**3.2 — does the modified prompt elicit the markers from a live model?**
Yes. The agent wrote `claim.txt` and submitted it ahead of the patch behind the
`<<<END_CLAIM>>>` delimiter, producing:

```
FINAL_STATUS: RESOLVED
VALIDATION_EVIDENCE: I created a reproduction script (repro.py) that confirmed that
session headers set to None were indeed being sent as "None" in the prepared request.
I modified 'requests/models.py' in the 'prepare_headers' method to filter out headers
with None values. I verified the fix with the reproduction script and added additional
edge case tests ...
```

The parser read it as `RESOLVED` with evidence, and re-parsing the stored
`raw_output` reproduces the same status. The evidence field describes checks the
model actually ran, which is what it was asked for.

Worth stating precisely: this shows the markers *can* be elicited from one model
on one task, not that they always will be. Run 1 produced no claim at all — for
an unrelated reason (throttling), but the `UNPARSEABLE` path is not hypothetical.
Claim capture rate stays a measured quantity, which is what Phase 9.3 gates on.

**3.3 — does a real record validate through the full runner path?**
Yes. `runs/3.1_smoke_gemini-3.1-flash-lite/tasks/psf__requests-1921/repair_record.json`
was produced by the live runner and re-validates through `RepairRecord.read()`
with `extra="forbid"`. Both smoke records validate, including run 1's
rate-limited one — the schema represents a truncated run without special-casing.

## Carried forward

- **Free tier cannot run the pilot.** 20 requests/day/model against ~10–40 model
  calls per instance means roughly one instance per model per day. The pilot
  needs a paid key; this constrains scheduling, not design.
- **`runs/` is gitignored**, so smoke evidence lives in this report. If run
  artifacts should be versioned, that is a deliberate `.gitignore` change and a
  secrets-audit question (trajectories contain full repository contents), not a
  default.
