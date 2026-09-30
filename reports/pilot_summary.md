# Pilot 10 — DeepSeek V4 Flash

Single pass, no retries, no config changes mid-run.
`experiment_id: pilot_10` · `runs/pilot_10/` · 2026-09-29T23:46Z–2026-09-30T00:16Z
Wall clock **1638 s** (~27 min) · total API cost **$0.2548**

## Phase 9 gates

| Gate | Need | Got | Result |
|---|---|---|---|
| 9.2 complete without infrastructure failure | ≥8/10 | **9/10** | PASS |
| 9.3 parseable `FINAL_STATUS` | ≥9/10 | **9/10** | PASS |
| 9.4 RESOLVED claims | ≥4/10 | **9/10** | PASS |

The tenth task (`pylint-dev__pylint-6386`) hit the step limit, produced an empty patch, and claimed `UNPARSEABLE`. That is an agent outcome, not an infrastructure failure. `sphinx-doc__sphinx-10449` produced a repair record and a parseable RESOLVED claim, then the verifier crashed on a non-UTF-8 file during Tier-2 selection (`UnicodeDecodeError` in `ContainerRepoTree.read_text`). No verification or oracle record for that instance.

**These three numbers may not be cited as study results.** See leakage below.

## Per task

| Instance | Claim | Term | Cost | Wall | Full | Oracle |
|---|---|---|---|---|---|---|
| astropy__astropy-12907 | RESOLVED | completed | $0.0323 | 184s | FLAG | resolved |
| django__django-14373 | RESOLVED | completed | $0.0068 | 306s | FLAG | resolved |
| django__django-14725 | RESOLVED | completed | $0.0420 | 141s | FLAG | resolved |
| django__django-16899 | RESOLVED | completed | $0.0154 | 72s | FLAG | resolved |
| matplotlib__matplotlib-26113 | RESOLVED | completed | $0.0271 | 203s | FLAG | resolved |
| mwaskom__seaborn-3187 | RESOLVED | completed | $0.0286 | 262s | FLAG | resolved |
| psf__requests-1921 | RESOLVED | completed | $0.0287 | 145s | FLAG | resolved |
| pylint-dev__pylint-6386 | UNPARSEABLE | step_limit | $0.0302 | 118s | REJECT | empty_patch |
| scikit-learn__scikit-learn-12973 | RESOLVED | completed | $0.0094 | 80s | FLAG | resolved |
| sphinx-doc__sphinx-10449 | RESOLVED | completed | $0.0341 | 128s | — | — |

Oracle among evaluated patches: 8 resolved, 0 unresolved, 0 infra, 1 empty. `resolved` is `None` on the empty patch, not `false`.

## FLAG is the V4 build-order state

Every instance that produced a non-empty patch was `FLAG` under both `full` and `baseline`. Integrity passed on all of those. Reproduction is `NOT_AVAILABLE (not_implemented)` on every record. Regression is `NOT_AVAILABLE` on every record (see 5.2). The full policy names both unmet conditions. This is the known build-order state, not a finding that the patches looked suspicious. When V4 reports and regression actually executes, ACCEPT becomes reachable with no change to the rule.

`pylint` is the one REJECT: empty patch, integrity failed.

## 8.3 — this run is invalid as a reliability result

`scripts/audit_leakage.sh runs` exits 1: **55 confirmed findings** on `runs/pilot_10`. Non-negotiable: a confirmed failure invalidates the affected runs.

The agent containers were started **without `--network none`**. `configs/agent/mini_swe_agent.yaml` asks for `network: none`; the claim prompt handed to mini-SWE-agent does not, and `get_sb_environment` launched:

```
docker run -d --name minisweagent-… -w /testbed --rm <image> sleep 2h
```

The requests trajectory shows the model curling GitHub:

```
curl https://raw.githubusercontent.com/psf/requests/v2.4.0/requests/sessions.py
curl "https://api.github.com/search/issues?q=repo:psf/requests+1935+…"
```

and then writing “verify against the upstream fix”. Field names `FAIL_TO_PASS` / `PASS_TO_PASS` appear in the matplotlib and requests trajectories. Gold-patch lines appear in several `patch.diff` files.

An 8/8 oracle resolve rate after the model fetched upstream is not a measurement of self-assessment. **Do not put that rate in a table.** The next pilot is a new `experiment_id`, with network isolation enforced in the environment that mini-SWE-agent actually launches, and 8.3 passing before any number is cited.

## Deferred gates this run was supposed to close

### 5.2 Regression outcomes on real patches

Recorded, but almost nothing executed.

- 7/9 verified instances: `NOT_AVAILABLE (nothing_to_check)` — selection returned no tests (`convention: unknown`).
- 2/9 (`django-14373`, `sklearn-12973`): tests were selected (62 and 118 **file paths**, not node ids) and every one came back `NOT_RUN`. The executor always invokes `pytest`, which is the wrong runner for Django and, here, produced no parseable results.

So the outcomes that exist are `NOT_RUN` and `NOT_AVAILABLE`. There is no `PASS` / `REGRESSION` / `PRE_EXISTING_FAIL` from a test that actually ran. The schema did its job — absence is visible — but the 5.2 gate is **not** closed as an execution signal.

### 5.3 PASS_TO_PASS overlap

**0 / 180** selected paths also appear in `PASS_TO_PASS` (`fraction_of_selected = 0.0`).

That number is real and should stay in the record. It is not evidence that selection is cleanly independent of the oracle: most instances selected nothing, and the 180 paths are whole test modules from a `CONVENTION_UNKNOWN` fall-through, which cannot match SWE-bench node ids. Recompute after selection produces node ids.

### 6.2 Static results across the 10 instances

9/10 produced a static block (sphinx never got a verification record).

| Check | Notes |
|---|---|
| syntax | PASS on every non-empty patch |
| import | PASS on every non-empty patch |
| lint | FAIL on most (pre-existing; not in `new_failures`); PASS on seaborn; NOT_AVAILABLE on requests |
| typecheck | NOT_AVAILABLE except matplotlib and seaborn (FAIL, not a new failure) |
| build | FAIL and listed as a **new failure** on every non-empty patch |

The build “new failure” is almost certainly `python -m build` missing from the eval image, not a broken package. Absence of a tool was recorded as FAIL rather than `NOT_AVAILABLE`. That overstates how much the static layer rejected. Syntax and import, which need no extra tooling, are the only static checks that actually ran as designed.

## Other apparatus notes (do not fix into this run)

1. Agent environment has network. Must be closed before any rerun.
2. `ContainerRepoTree.read_text` decodes as UTF-8 and crashes on binary/legacy encodings — sphinx.
3. Selection convention discovery returned `unknown` on 7/9 repos, so Tier 1/2 produced nothing useful.
4. Cost limit was taken from `primary.yaml` ($5), not the claim prompt’s $1 ceiling. No task approached it.
5. 9.1 (2-task dry run) was skipped at request; the network leak is exactly what that dry run was for.

Records: `runs/pilot_10/summary.json`, per-task `repair_record.json` / `verification_record.{full,baseline}.json` / `oracle_record.json`, `meta.yaml`.
