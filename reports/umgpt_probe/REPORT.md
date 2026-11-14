# UM routing and three-task probe

**BLOCKED: UM rejected the first verification request with HTTP 401. No task was launched.**

Date: 2026-11-14 (America/Phoenix). Branch: `feature/umgpt-routing`.
Implementation HEAD tested by the final suite: `5659540b58d7d798751bed9fdf3e104f872e2116`. This report is committed
after that implementation commit; the branch tip identifies the report commit.
Base: fetched `origin/main` at `bc0b8fa`. The auth-only live request happened during
implementation, before the UM additions were committed, at base HEAD `bc0b8fa`.
It produced no model output or performance result.

The existing ignored `.env` survived the branch switch. It was read locally and
was not copied, rewritten, staged, or committed. No label files or files under
`grader_gap/` were opened. No notifications, 10-task pilot, or larger run occurred.

## Candidate verification

| Requested LiteLLM model | Outcome | Served model | Fingerprint | Token usage | Rate-limit headers |
|---|---|---|---|---|---|
| openai/gpt-4.1-mini | HTTP 401 AUTH_ERROR | not returned | not returned | not returned | not persisted on this failed request |
| openai/gpt-4.1 | not attempted: auth stop | — | — | — | — |
| openai/gpt-4o-mini | not attempted: auth stop | — | — | — | — |

Provider: `umgpt`. Host: `api.toolkit.umgpt.umich.edu`. The sanitized body was:

```json
{"status":"failure","message":"Portkey Error: Invalid API Key. Error Code: 03","error":{"message":"Portkey Error: Invalid API Key. Error Code: 03","code":"03"}}
```

Evidence is in `verification.json` and local `runs/umgpt_probe/verification.json`.
There was no inherited UM key overriding `.env`. The 401 was not retried. No
primary/generator model was chosen; both new configs remain unverified without a
`verified:` block. Only `scripts/verify_model.py` creates that block after a real
well-formed bash tool call with `finish_reason: tool_calls`.

The failed attempt did not persist its rate-limit headers, so neither their
presence nor values can be claimed. The final error-path implementation captures
only `x-ratelimit-*` names/values, covered by mocked transport tests. No second
live request was made to fill this metadata gap.

## Routing, budget and validation

The opt-in `UMModel` is selected through mini-swe-agent's existing model factory
by both repair and the new V4 prompt config. Its real LiteLLM/OpenAI serialization
is tested using `httpx.MockTransport`: the UM host and `/v1/chat/completions` path,
`max_completion_tokens: 8192`, no `max_tokens`, temperature 0, top-p 1, and bash
tools. The frozen V4 builder still supplies `max_tokens`; the new model class
replaces it before dispatch. The key is read at call time and excluded from model
configuration, templates, serialized trajectories, logs, and ledger records.
Per-call records retain requested/served model, fingerprint, host, input/cached/
output tokens, estimated cost and LiteLLM cost when a response supplies usage.

`scripts/run_umgpt_probe.py` is a three-task-only successor to `run_pilot.py`,
reusing `run_task` and unchanged `verify_task` logic. The frozen verifier modules,
original model configs, existing prompts and protocols were not edited. `frozen_files.json`
records 38 protected verifier/model/prompt files byte-identical to `origin/main`. Oracle
grading is omitted from this cost probe. The new enum values and optional
verification dispatch are additive; existing DeepSeek routes stay on their old
paths. Live repair and V4 behavior remain untested because authentication blocked
candidate verification.

The primary limits block matches `primary.yaml`: 100 steps, 400000 input tokens,
$0.50 agent cost and a 600-second request timeout. The successor applies a more
restrictive $0.50 combined repair-plus-V4 task cap. The ledger account cap is $20
and this job's cap is $3 including verification. It reserves a conservative
uncached request estimate before every call and refuses a task unless its entire
remaining cap fits. Resumes retain settled spend and any in-flight reservations;
ambiguous transport failures require reconciliation. Budget/auth stops are
infrastructure outcomes. Plain rate limits keep scaffold backoff. HTTP 402 and
quota/budget-style 429 stop; 401/403 stop with sanitized body text.

Explicit pricing uses the requested list-price rates. Mocked custom-base
responses produce a positive LiteLLM cost for all three candidates; real UM
response pricing could not be confirmed because no usage was returned. All cost
figures are estimates; actual UM billing is unconfirmed.

## Three-task probe

| Task | Steps | Input/cached/output tokens | Measured cost | Termination | Patch produced | V4 |
|---|---:|---|---|---|---|---|
| django__django-14373 | 0 | unavailable | unavailable | not started: AUTH_ERROR preflight | no | not run |
| scikit-learn__scikit-learn-12973 | 0 | unavailable | unavailable | not started: AUTH_ERROR preflight | no | not run |
| django__django-16899 | 0 | unavailable | unavailable | not started: AUTH_ERROR preflight | no | not run |

Measured mean cost, maximum cost and cache-hit rate: **unavailable**. Zero tasks
ran; $0 spent on tasks is not a measured $0 task cost.

| Task count | Projection from measured mean | Projection from worst measured task |
|---:|---|---|
| 10 | unavailable | unavailable |
| 83 | unavailable | unavailable |
| 500 | unavailable | unavailable |

## Historical DeepSeek comparison

No `pilot_15` trajectories/repair records were found in accessible project runs,
`/home/sankalp/archive`, or the home-directory trajectory inventory. Available
main-study archives are not substituted for the requested pilot. These are the
same ten pilot manifest tasks, but their requested historical counts are absent:

| Task | Input tokens | Cached input tokens | Output tokens | Steps |
|---|---|---|---|---|
| astropy__astropy-12907 | unavailable | unavailable | unavailable | unavailable |
| django__django-14373 | unavailable | unavailable | unavailable | unavailable |
| django__django-14725 | unavailable | unavailable | unavailable | unavailable |
| django__django-16899 | unavailable | unavailable | unavailable | unavailable |
| matplotlib__matplotlib-26113 | unavailable | unavailable | unavailable | unavailable |
| mwaskom__seaborn-3187 | unavailable | unavailable | unavailable | unavailable |
| psf__requests-1921 | unavailable | unavailable | unavailable | unavailable |
| pylint-dev__pylint-6386 | unavailable | unavailable | unavailable | unavailable |
| scikit-learn__scikit-learn-12973 | unavailable | unavailable | unavailable | unavailable |
| sphinx-doc__sphinx-10449 | unavailable | unavailable | unavailable | unavailable |

The requested 10/83/500-task historical cost table cannot be computed without
these token counts. The following are arithmetic coefficients, **not task-cost
measurements or projections**. Rates were checked against the installed LiteLLM
cost map; all figures are USD per million tokens, with UM billing unconfirmed.

| Model | Assumed cache-hit rate | Effective input rate | Output rate |
|---|---:|---:|---:|
| gpt-4.1 | 0% | 2.0000 | 8.0000 |
| gpt-4.1 | 50% | 1.2500 | 8.0000 |
| gpt-4.1 | 80% | 0.8000 | 8.0000 |
| gpt-4.1-mini | 0% | 0.4000 | 1.6000 |
| gpt-4.1-mini | 50% | 0.2500 | 1.6000 |
| gpt-4.1-mini | 80% | 0.1600 | 1.6000 |
| gpt-4.1-nano | 0% | 0.1000 | 0.4000 |
| gpt-4.1-nano | 50% | 0.0625 | 0.4000 |
| gpt-4.1-nano | 80% | 0.0400 | 0.4000 |
| gpt-4o-mini | 0% | 0.1500 | 0.6000 |
| gpt-4o-mini | 50% | 0.1125 | 0.6000 |
| gpt-4o-mini | 80% | 0.0900 | 0.6000 |

For the same historical token counts, let `I` and `O` be total input and output
tokens across the ten pilot tasks, and `h` the assumed cache-hit rate. At each of
0%, 50% and 80%, the requested estimate is:

`C(N) = (N / 10) * (I * ((1-h) * input_rate + h * cached_input_rate) + O * output_rate) / 1_000_000`

Use `N = 10, 83, 500`. Cached input is a subset of input and is never added to it.
Measured-probe projections would instead be `N * mean_task_cost` and
`N * max_task_cost` once complete repair-plus-V4 costs exist.

## Spend and unit-suite comparison

- Estimated job spend: **$0.00000000**; total persistent ledger spend: **$0.00000000**.
- One settled HTTP rejection, no outstanding reservation, no generated-token usage returned. Provider billing was not queried and no actual charge was reported.
- Baseline: 1375 passed, 6 failures, 47 errors, 6 skipped.
- Final implementation: 1396 passed, 6 failures, 47 errors, 6 skipped.
- No new failing/error test names. Error/failure names match the baseline; the known split remains 30 Hugging Face cache-lock errors plus 17 frozen-input drift errors, with 6 pre-existing failures.
- All 21 new UM tests pass, including both production model factories, all candidate list prices, verification selection/writing, auth/quota/plain-rate-limit branches, ledger refusal/resume and credential redaction. Ruff and `git diff --check` pass. Secret audits ran before commits.

`unit_comparison.json` contains every failing/error test name and raw XML hashes.
Local raw evidence: `runs/umgpt_tests/baseline.{log,xml}` and
`runs/umgpt_tests/final_complete.{log,xml}`. The credential and spend ledger remain
ignored. See `DECISIONS.md` for judgment calls and `BLOCKED.md` for the exact stop
state. A valid local UM credential and authorization to resume are the one
decision needed before any further paid calls; preserve this attempt and ledger.
