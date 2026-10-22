# CIS 695 main study: per-task results (n=100, reruns applied)

Per-task fields are read from `repair_record.json` (agent `termination` → `agent_status`, `claim.status` → `claim`), `verification_record.full.json` (`decision.decision` → `verifier_decision`; signal `outcome` fields → V1–V4), and `oracle_record.json` (`outcome` → `oracle`), per `src/reliability/verifier/record.py`. Tabular data: [`docs/results_100.csv`](results_100.csv).

## (a) Counts by half and overall

### Half A (50, reruns applied)

- Oracle (`oracle_record.json`): resolved **37**, unresolved **5**, empty_patch **8**.
- Claims (`repair_record.json`): RESOLVED **42**, UNPARSEABLE **8**.
- Claim matches oracle (patch-level): **37/42**.
- RESOLVED-claim precision (patch-level): **37/42**.

### Half B (50, reruns applied)

- Oracle (`oracle_record.json`): resolved **38**, unresolved **9**, empty_patch **3**.
- Claims (`repair_record.json`): RESOLVED **47**, UNPARSEABLE **3**.
- Claim matches oracle (patch-level): **38/47**.
- RESOLVED-claim precision (patch-level): **38/47**.

### All 100

- Oracle (`oracle_record.json`): resolved **75**, unresolved **14**, empty_patch **11**.
- Claims (`repair_record.json`): RESOLVED **89**, UNPARSEABLE **11**.
- Claim matches oracle (patch-level): **75/89**.
- RESOLVED-claim precision (patch-level): **75/89**.

### Headline (93, requests excluded)

- Oracle (`oracle_record.json`): resolved **69**, unresolved **14**, empty_patch **10**.
- Claims (`repair_record.json`): RESOLVED **83**, UNPARSEABLE **10**.
- Claim matches oracle (patch-level): **69/83**.
- RESOLVED-claim precision (patch-level): **69/83**.

### Requests stratum (7)

- Oracle (`oracle_record.json`): resolved **6**, unresolved **0**, empty_patch **1**.
- Claims (`repair_record.json`): RESOLVED **6**, UNPARSEABLE **1**.
- Claim matches oracle (patch-level): **6/6**.
- RESOLVED-claim precision (patch-level): **6/6**.

## (b) Verifier decision × oracle

### All 100

| verifier \ oracle | resolved | unresolved | empty_patch |
|---|---:|---:|---:|
| ACCEPT | 47 | 7 | 0 |
| FLAG | 28 | 6 | 0 |
| REJECT | 0 | 1 | 11 |

### Headline 93

| verifier \ oracle | resolved | unresolved | empty_patch |
|---|---:|---:|---:|
| ACCEPT | 45 | 7 | 0 |
| FLAG | 24 | 6 | 0 |
| REJECT | 0 | 1 | 10 |

### Half A

| verifier \ oracle | resolved | unresolved | empty_patch |
|---|---:|---:|---:|
| ACCEPT | 24 | 3 | 0 |
| FLAG | 13 | 2 | 0 |
| REJECT | 0 | 0 | 8 |

### Half B

| verifier \ oracle | resolved | unresolved | empty_patch |
|---|---:|---:|---:|
| ACCEPT | 23 | 4 | 0 |
| FLAG | 15 | 4 | 0 |
| REJECT | 0 | 1 | 3 |

## (c) ACCEPT precision, coverage, false accepts

ACCEPT **precision** uses patch-level oracle outcomes only (`resolved` / `unresolved`), per `src/reliability/analysis/metrics.py`. **Coverage** below uses the same valid-patch denominator (tasks with oracle `resolved` or `unresolved`, excluding `empty_patch`).

### All 100

- ACCEPT precision: **47/54 = 87.0% (95% Wilson CI 75.6%–93.6%)**.
- False accepts (7): django__django-13212, django__django-16667, pylint-dev__pylint-7277, django__django-13297, matplotlib__matplotlib-23299, matplotlib__matplotlib-23476, pylint-dev__pylint-4661.
- ACCEPT coverage / valid patches (patch-level tasks): **54/89 = 60.7%** (89 = 75 resolved + 14 unresolved).
- ACCEPT coverage / oracle-resolved only: **54/75 = 72.0% (95% Wilson CI 61.0%–80.9%)**.
- RESOLVED-claim precision: **75/89 = 84.3% (95% Wilson CI 75.3%–90.4%)**.
- Point estimates: ACCEPT precision 87.0% vs RESOLVED-claim precision 84.3%.

### Headline 93

- ACCEPT precision: **45/52 = 86.5% (95% Wilson CI 74.7%–93.3%)**.
- False accepts (7): django__django-13212, django__django-16667, pylint-dev__pylint-7277, django__django-13297, matplotlib__matplotlib-23299, matplotlib__matplotlib-23476, pylint-dev__pylint-4661.
- ACCEPT coverage / valid patches (headline): **52/83 = 62.7% (95% Wilson CI 51.9%–72.3%)** (83 = 69 resolved + 14 unresolved; excludes 10 `empty_patch`).
- ACCEPT coverage / oracle-resolved only: **45/69 = 65.2% (95% Wilson CI 53.4%–75.4%)**.
- RESOLVED-claim precision: **69/83 = 83.1% (95% Wilson CI 73.7%–89.7%)**.
- Point estimates: ACCEPT precision 86.5% vs RESOLVED-claim precision 83.1%.

## (d) V4 (`reproduction`) outcomes

### Half A
- FAIL: 1, NOT_AVAILABLE: 15, PASS: 34 (`verification_record.full.json` → `reproduction.outcome`).

### Half B
- NOT_AVAILABLE: 12, PASS: 38 (`verification_record.full.json` → `reproduction.outcome`).

### All 100
- FAIL: 1, NOT_AVAILABLE: 27, PASS: 72 (`verification_record.full.json` → `reproduction.outcome`).

**V4 FAIL (merged table):** django__django-10973.

## (e) Resolved patches with verifier FLAG or REJECT

| instance_id | half | source_run | decision | signal / reason |
|---|---|---|---|---|
| astropy__astropy-14365 | A | main_50_a | FLAG | regression is NOT_AVAILABLE, not PASS |
| astropy__astropy-14508 | A | main_50_a | FLAG | regression is NOT_AVAILABLE, not PASS |
| django__django-10973 | A | main_50_a | FLAG | reproduction (V4): no issue-specific execution signal supports repair (reproduction is FAIL) |
| django__django-12209 | B | main_50_b | FLAG | regression (V2): signals disagree: regression FAIL, reproduction PASS |
| django__django-13158 | A | main_50_a | FLAG | reproduction NOT_AVAILABLE (V4): no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| django__django-14140 | B | main_50_b | FLAG | regression (V2): signals disagree: regression FAIL, reproduction PASS |
| django__django-14631 | B | main_50_b | FLAG | regression (V2): signals disagree: regression FAIL, reproduction PASS |
| django__django-15037 | A | main_50_a | FLAG | reproduction NOT_AVAILABLE (V4): no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| matplotlib__matplotlib-14623 | A | main_50_a | FLAG | regression is NOT_AVAILABLE, not PASS |
| matplotlib__matplotlib-22871 | A | main_50_a | FLAG | reproduction NOT_AVAILABLE (V4): no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| matplotlib__matplotlib-24177 | B | main_50_b | FLAG | regression is NOT_AVAILABLE, not PASS |
| matplotlib__matplotlib-24637 | B | main_50_b | FLAG | reproduction NOT_AVAILABLE (V4): no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| matplotlib__matplotlib-25287 | A | main_50_a | FLAG | regression is NOT_AVAILABLE, not PASS |
| psf__requests-1142 | B | main_50_b | FLAG | reproduction NOT_AVAILABLE (V4): regression is NOT_AVAILABLE, not PASS / no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| psf__requests-1724 | A | main_50_a | FLAG | regression is NOT_AVAILABLE, not PASS |
| psf__requests-5414 | B | main_50_b | FLAG | regression is NOT_AVAILABLE, not PASS |
| psf__requests-6028 | A | main_50_a | FLAG | reproduction NOT_AVAILABLE (V4): no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| pydata__xarray-4966 | B | main_50_b | FLAG | reproduction NOT_AVAILABLE (V4): regression is NOT_AVAILABLE, not PASS / no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| pylint-dev__pylint-4970 | A | main_50_a | FLAG | reproduction NOT_AVAILABLE (V4): no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| pylint-dev__pylint-6903 | B | main_50_b | FLAG | regression is NOT_AVAILABLE, not PASS |
| pytest-dev__pytest-5809 | A | main_50_a | FLAG | regression (V2): signals disagree: regression FAIL, reproduction PASS |
| sphinx-doc__sphinx-10323 | B | main_50_b | FLAG | reproduction NOT_AVAILABLE (V4): no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| sphinx-doc__sphinx-10435 | B | main_50_b | FLAG | regression (V2): signals disagree: regression FAIL, reproduction PASS |
| sphinx-doc__sphinx-7910 | A | main_50_a | FLAG | high-severity risk flag present |
| sympy__sympy-13480 | B | main_50_b | FLAG | regression is NOT_AVAILABLE, not PASS |
| sympy__sympy-14711 | B | main_50_b | FLAG | regression is NOT_AVAILABLE, not PASS |
| sympy__sympy-19783 | B | main_3_rerun_infra | FLAG | reproduction NOT_AVAILABLE (V4): regression is NOT_AVAILABLE, not PASS / no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| sympy__sympy-24562 | B | main_3_rerun_infra | FLAG | regression is NOT_AVAILABLE, not PASS |

## (f) Reconciliation

### `main_50_a` original (`runs/main_50_a`)

- **Oracle resolved / unresolved / empty_patch**: expected 38 / 5 / 7; observed **38 / 5 / 7** — **match** (from `runs/main_50_a/tasks/*/oracle_record.json`).
- **Verifier ACCEPT / FLAG / REJECT**: expected 28 / 15 / 7; observed **28 / 15 / 7** — **match** (from `verification_record.full.json`).
- **False accepts among ACCEPT**: expected django-13212, django-16667, pylint-7277 (3 tasks; 25 ACCEPT correct); observed **django__django-13212, django__django-16667, pylint-dev__pylint-7277 (3 tasks; 25 ACCEPT ∧ resolved)** — **match** (from verification + oracle records).
- **`summary.json` oracle resolved**: expected 38; observed **38** — **match** (from `runs/main_50_a/summary.json`).

### `main_50_b` before sympy rerun (`runs/main_50_b`)

- **Oracle resolved / unresolved / empty_patch**: expected 36 / 8 / 6; observed **36 / 8 / 6** — **match** (from oracle records).
- **`summary.json` oracle resolved**: expected 36; observed **36** — **match** (from `runs/main_50_b/summary.json`).

### `main_50_b` after sympy rerun replacement

- **Oracle resolved / unresolved / empty_patch**: expected 38 / 9 / 3; observed **38 / 9 / 3** — **match** (from merged half-B in `docs/results_100.csv`).

### `main_3_rerun_infra`

- **sympy__sympy-17318 (expected unresolved, FLAG)**: expected unresolved, FLAG; observed **oracle=unresolved, decision=FLAG, claim=RESOLVED** — **match** (from `runs/main_3_rerun_infra/tasks/sympy__sympy-17318/`, `logs/main_3_rerun_infra.log`).
- **sympy__sympy-19783 (expected resolved, FLAG)**: expected resolved, FLAG; observed **oracle=resolved, decision=FLAG, claim=RESOLVED** — **match** (from `runs/main_3_rerun_infra/tasks/sympy__sympy-19783/`, `logs/main_3_rerun_infra.log`).
- **sympy__sympy-24562 (expected resolved, FLAG)**: expected resolved, FLAG; observed **oracle=resolved, decision=FLAG, claim=RESOLVED** — **match** (from `runs/main_3_rerun_infra/tasks/sympy__sympy-24562/`, `logs/main_3_rerun_infra.log`).

### `main_2_rerun_mpl`

- **matplotlib__matplotlib-20676**: expected claim RESOLVED, FLAG, oracle unresolved; observed **claim=RESOLVED, FLAG, oracle=unresolved** — **match** (from `runs/main_2_rerun_mpl/`, `logs/main_2_rerun_mpl.tmux.log`).
- **matplotlib__matplotlib-21568**: expected UNPARSEABLE, REJECT, empty_patch; observed **claim=UNPARSEABLE, REJECT, oracle=empty_patch** — **match** (from `runs/main_2_rerun_mpl/`, `logs/main_2_rerun_mpl.tmux.log`).

### Half A after `main_2_rerun_mpl` replacement (merged half A in `docs/results_100.csv`)

- **Oracle resolved / unresolved / empty_patch**: expected shift from original 38/5/7 to **37 / 5 / 8** after replacement; observed **37 / 5 / 8** — **match** (from merged half-A rows: `main_2_rerun_mpl` for matplotlib-20676 and matplotlib-21568, otherwise `main_50_a`).
- **Verifier ACCEPT / FLAG / REJECT**: original `main_50_a` was 28/15/7; merged half A is **27 / 15 / 8** — **match** to on-disk merged records (one fewer ACCEPT and one more REJECT vs original, consistent with matplotlib-21568 moving to `empty_patch` + REJECT and matplotlib-20676 moving from ACCEPT to FLAG with oracle `unresolved`).

### Headline stratum (93 tasks)

- **Oracle resolved / unresolved / empty_patch**: expected 69 / 14 / 10; observed **69 / 14 / 10** — **match** (from merged headline rows).
- **Claim matches oracle (patch-level)**: expected 69 / 83; observed **69 / 83** — **match** (from same).

### Log cross-check (merged tasks vs run logs)

- **100** tasks: logged fields match on-disk records; **0** cannot check (no parsed log line); **0** mismatch.
- Note: summary lines in `logs/main_50_*.tmux.log` omit `agent=` and `full=`; cross-check uses inline `agent=… full=…` lines when present and summary `claim`/`oracle` otherwise.

## Data not found

- All required per-task fields were present in the merged run directories (`repair_record.json`, `verification_record.full.json`, `oracle_record.json`) for all 100 tasks.
- No aggregate verifier-decision file beyond per-task `verification_record.full.json` was required for this table.

## Files read

- `docs/results_100.csv`
- `logs/main_2_rerun_mpl.tmux.log`
- `logs/main_3_rerun_infra.log`
- `logs/main_50_a.tmux.log`
- `logs/main_50_b.tmux.log`
- `manifests/main_50_a.csv`
- `manifests/main_50_b.csv`
- `runs/main_2_rerun_mpl/tasks/matplotlib__matplotlib-20676/oracle_record.json`
- `runs/main_2_rerun_mpl/tasks/matplotlib__matplotlib-20676/repair_record.json`
- `runs/main_2_rerun_mpl/tasks/matplotlib__matplotlib-20676/verification_record.full.json`
- `runs/main_2_rerun_mpl/tasks/matplotlib__matplotlib-21568/oracle_record.json`
- `runs/main_2_rerun_mpl/tasks/matplotlib__matplotlib-21568/repair_record.json`
- `runs/main_2_rerun_mpl/tasks/matplotlib__matplotlib-21568/verification_record.full.json`
- `runs/main_3_rerun_infra/tasks/sympy__sympy-17318/oracle_record.json`
- `runs/main_3_rerun_infra/tasks/sympy__sympy-17318/repair_record.json`
- `runs/main_3_rerun_infra/tasks/sympy__sympy-17318/verification_record.full.json`
- `runs/main_3_rerun_infra/tasks/sympy__sympy-19783/oracle_record.json`
- `runs/main_3_rerun_infra/tasks/sympy__sympy-19783/repair_record.json`
- `runs/main_3_rerun_infra/tasks/sympy__sympy-19783/verification_record.full.json`
- `runs/main_3_rerun_infra/tasks/sympy__sympy-24562/oracle_record.json`
- `runs/main_3_rerun_infra/tasks/sympy__sympy-24562/repair_record.json`
- `runs/main_3_rerun_infra/tasks/sympy__sympy-24562/verification_record.full.json`
- `runs/main_50_a/summary.json`
- `runs/main_50_a/tasks/astropy__astropy-14365/oracle_record.json`
- `runs/main_50_a/tasks/astropy__astropy-14365/repair_record.json`
- `runs/main_50_a/tasks/astropy__astropy-14365/verification_record.full.json`
- `runs/main_50_a/tasks/astropy__astropy-14508/oracle_record.json`
- `runs/main_50_a/tasks/astropy__astropy-14508/repair_record.json`
- `runs/main_50_a/tasks/astropy__astropy-14508/verification_record.full.json`
- `runs/main_50_a/tasks/django__django-10973/oracle_record.json`
- `runs/main_50_a/tasks/django__django-10973/repair_record.json`
- `runs/main_50_a/tasks/django__django-10973/verification_record.full.json`
- `runs/main_50_a/tasks/django__django-11095/oracle_record.json`
- `runs/main_50_a/tasks/django__django-11095/repair_record.json`
- `runs/main_50_a/tasks/django__django-11095/verification_record.full.json`
- `runs/main_50_a/tasks/django__django-12663/oracle_record.json`
- `runs/main_50_a/tasks/django__django-12663/repair_record.json`
- `runs/main_50_a/tasks/django__django-12663/verification_record.full.json`
- `runs/main_50_a/tasks/django__django-12965/oracle_record.json`
- `runs/main_50_a/tasks/django__django-12965/repair_record.json`
- `runs/main_50_a/tasks/django__django-12965/verification_record.full.json`
- `runs/main_50_a/tasks/django__django-13158/oracle_record.json`
- `runs/main_50_a/tasks/django__django-13158/repair_record.json`
- `runs/main_50_a/tasks/django__django-13158/verification_record.full.json`
- `runs/main_50_a/tasks/django__django-13212/oracle_record.json`
- `runs/main_50_a/tasks/django__django-13212/repair_record.json`
- `runs/main_50_a/tasks/django__django-13212/verification_record.full.json`
- `runs/main_50_a/tasks/django__django-13807/oracle_record.json`
- `runs/main_50_a/tasks/django__django-13807/repair_record.json`
- `runs/main_50_a/tasks/django__django-13807/verification_record.full.json`
- `runs/main_50_a/tasks/django__django-15037/oracle_record.json`
- `runs/main_50_a/tasks/django__django-15037/repair_record.json`
- `runs/main_50_a/tasks/django__django-15037/verification_record.full.json`
- `runs/main_50_a/tasks/django__django-15103/oracle_record.json`
- `runs/main_50_a/tasks/django__django-15103/repair_record.json`
- `runs/main_50_a/tasks/django__django-15103/verification_record.full.json`
- `runs/main_50_a/tasks/django__django-15278/oracle_record.json`
- `runs/main_50_a/tasks/django__django-15278/repair_record.json`
- `runs/main_50_a/tasks/django__django-15278/verification_record.full.json`
- `runs/main_50_a/tasks/django__django-15499/oracle_record.json`
- `runs/main_50_a/tasks/django__django-15499/repair_record.json`
- `runs/main_50_a/tasks/django__django-15499/verification_record.full.json`
- `runs/main_50_a/tasks/django__django-15572/oracle_record.json`
- `runs/main_50_a/tasks/django__django-15572/repair_record.json`
- `runs/main_50_a/tasks/django__django-15572/verification_record.full.json`
- `runs/main_50_a/tasks/django__django-15930/oracle_record.json`
- `runs/main_50_a/tasks/django__django-15930/repair_record.json`
- `runs/main_50_a/tasks/django__django-15930/verification_record.full.json`
- `runs/main_50_a/tasks/django__django-16612/oracle_record.json`
- `runs/main_50_a/tasks/django__django-16612/repair_record.json`
- `runs/main_50_a/tasks/django__django-16612/verification_record.full.json`
- `runs/main_50_a/tasks/django__django-16667/oracle_record.json`
- `runs/main_50_a/tasks/django__django-16667/repair_record.json`
- `runs/main_50_a/tasks/django__django-16667/verification_record.full.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-14623/oracle_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-14623/repair_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-14623/verification_record.full.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-20676/oracle_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-20676/repair_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-20676/verification_record.full.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-21568/oracle_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-21568/repair_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-21568/verification_record.full.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-22871/oracle_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-22871/repair_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-22871/verification_record.full.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-24026/oracle_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-24026/repair_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-24026/verification_record.full.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-24627/oracle_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-24627/repair_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-24627/verification_record.full.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-25122/oracle_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-25122/repair_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-25122/verification_record.full.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-25287/oracle_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-25287/repair_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-25287/verification_record.full.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-25332/oracle_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-25332/repair_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-25332/verification_record.full.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-26291/oracle_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-26291/repair_record.json`
- `runs/main_50_a/tasks/matplotlib__matplotlib-26291/verification_record.full.json`
- `runs/main_50_a/tasks/pallets__flask-5014/oracle_record.json`
- `runs/main_50_a/tasks/pallets__flask-5014/repair_record.json`
- `runs/main_50_a/tasks/pallets__flask-5014/verification_record.full.json`
- `runs/main_50_a/tasks/psf__requests-1724/oracle_record.json`
- `runs/main_50_a/tasks/psf__requests-1724/repair_record.json`
- `runs/main_50_a/tasks/psf__requests-1724/verification_record.full.json`
- `runs/main_50_a/tasks/psf__requests-1766/oracle_record.json`
- `runs/main_50_a/tasks/psf__requests-1766/repair_record.json`
- `runs/main_50_a/tasks/psf__requests-1766/verification_record.full.json`
- `runs/main_50_a/tasks/psf__requests-2317/oracle_record.json`
- `runs/main_50_a/tasks/psf__requests-2317/repair_record.json`
- `runs/main_50_a/tasks/psf__requests-2317/verification_record.full.json`
- `runs/main_50_a/tasks/psf__requests-6028/oracle_record.json`
- `runs/main_50_a/tasks/psf__requests-6028/repair_record.json`
- `runs/main_50_a/tasks/psf__requests-6028/verification_record.full.json`
- `runs/main_50_a/tasks/pydata__xarray-4629/oracle_record.json`
- `runs/main_50_a/tasks/pydata__xarray-4629/repair_record.json`
- `runs/main_50_a/tasks/pydata__xarray-4629/verification_record.full.json`
- `runs/main_50_a/tasks/pydata__xarray-4695/oracle_record.json`
- `runs/main_50_a/tasks/pydata__xarray-4695/repair_record.json`
- `runs/main_50_a/tasks/pydata__xarray-4695/verification_record.full.json`
- `runs/main_50_a/tasks/pydata__xarray-6599/oracle_record.json`
- `runs/main_50_a/tasks/pydata__xarray-6599/repair_record.json`
- `runs/main_50_a/tasks/pydata__xarray-6599/verification_record.full.json`
- `runs/main_50_a/tasks/pydata__xarray-6744/oracle_record.json`
- `runs/main_50_a/tasks/pydata__xarray-6744/repair_record.json`
- `runs/main_50_a/tasks/pydata__xarray-6744/verification_record.full.json`
- `runs/main_50_a/tasks/pylint-dev__pylint-4551/oracle_record.json`
- `runs/main_50_a/tasks/pylint-dev__pylint-4551/repair_record.json`
- `runs/main_50_a/tasks/pylint-dev__pylint-4551/verification_record.full.json`
- `runs/main_50_a/tasks/pylint-dev__pylint-4970/oracle_record.json`
- `runs/main_50_a/tasks/pylint-dev__pylint-4970/repair_record.json`
- `runs/main_50_a/tasks/pylint-dev__pylint-4970/verification_record.full.json`
- `runs/main_50_a/tasks/pylint-dev__pylint-6528/oracle_record.json`
- `runs/main_50_a/tasks/pylint-dev__pylint-6528/repair_record.json`
- `runs/main_50_a/tasks/pylint-dev__pylint-6528/verification_record.full.json`
- `runs/main_50_a/tasks/pylint-dev__pylint-7277/oracle_record.json`
- `runs/main_50_a/tasks/pylint-dev__pylint-7277/repair_record.json`
- `runs/main_50_a/tasks/pylint-dev__pylint-7277/verification_record.full.json`
- `runs/main_50_a/tasks/pytest-dev__pytest-5809/oracle_record.json`
- `runs/main_50_a/tasks/pytest-dev__pytest-5809/repair_record.json`
- `runs/main_50_a/tasks/pytest-dev__pytest-5809/verification_record.full.json`
- `runs/main_50_a/tasks/pytest-dev__pytest-6202/oracle_record.json`
- `runs/main_50_a/tasks/pytest-dev__pytest-6202/repair_record.json`
- `runs/main_50_a/tasks/pytest-dev__pytest-6202/verification_record.full.json`
- `runs/main_50_a/tasks/pytest-dev__pytest-7432/oracle_record.json`
- `runs/main_50_a/tasks/pytest-dev__pytest-7432/repair_record.json`
- `runs/main_50_a/tasks/pytest-dev__pytest-7432/verification_record.full.json`
- `runs/main_50_a/tasks/scikit-learn__scikit-learn-12585/oracle_record.json`
- `runs/main_50_a/tasks/scikit-learn__scikit-learn-12585/repair_record.json`
- `runs/main_50_a/tasks/scikit-learn__scikit-learn-12585/verification_record.full.json`
- `runs/main_50_a/tasks/scikit-learn__scikit-learn-14141/oracle_record.json`
- `runs/main_50_a/tasks/scikit-learn__scikit-learn-14141/repair_record.json`
- `runs/main_50_a/tasks/scikit-learn__scikit-learn-14141/verification_record.full.json`
- `runs/main_50_a/tasks/scikit-learn__scikit-learn-14629/oracle_record.json`
- `runs/main_50_a/tasks/scikit-learn__scikit-learn-14629/repair_record.json`
- `runs/main_50_a/tasks/scikit-learn__scikit-learn-14629/verification_record.full.json`
- `runs/main_50_a/tasks/scikit-learn__scikit-learn-14894/oracle_record.json`
- `runs/main_50_a/tasks/scikit-learn__scikit-learn-14894/repair_record.json`
- `runs/main_50_a/tasks/scikit-learn__scikit-learn-14894/verification_record.full.json`
- `runs/main_50_a/tasks/sphinx-doc__sphinx-10614/oracle_record.json`
- `runs/main_50_a/tasks/sphinx-doc__sphinx-10614/repair_record.json`
- `runs/main_50_a/tasks/sphinx-doc__sphinx-10614/verification_record.full.json`
- `runs/main_50_a/tasks/sphinx-doc__sphinx-7748/oracle_record.json`
- `runs/main_50_a/tasks/sphinx-doc__sphinx-7748/repair_record.json`
- `runs/main_50_a/tasks/sphinx-doc__sphinx-7748/verification_record.full.json`
- `runs/main_50_a/tasks/sphinx-doc__sphinx-7910/oracle_record.json`
- `runs/main_50_a/tasks/sphinx-doc__sphinx-7910/repair_record.json`
- `runs/main_50_a/tasks/sphinx-doc__sphinx-7910/verification_record.full.json`
- `runs/main_50_b/summary.json`
- `runs/main_50_b/tasks/astropy__astropy-13398/oracle_record.json`
- `runs/main_50_b/tasks/astropy__astropy-13398/repair_record.json`
- `runs/main_50_b/tasks/astropy__astropy-13398/verification_record.full.json`
- `runs/main_50_b/tasks/astropy__astropy-13977/oracle_record.json`
- `runs/main_50_b/tasks/astropy__astropy-13977/repair_record.json`
- `runs/main_50_b/tasks/astropy__astropy-13977/verification_record.full.json`
- `runs/main_50_b/tasks/astropy__astropy-7606/oracle_record.json`
- `runs/main_50_b/tasks/astropy__astropy-7606/repair_record.json`
- `runs/main_50_b/tasks/astropy__astropy-7606/verification_record.full.json`
- `runs/main_50_b/tasks/django__django-11299/oracle_record.json`
- `runs/main_50_b/tasks/django__django-11299/repair_record.json`
- `runs/main_50_b/tasks/django__django-11299/verification_record.full.json`
- `runs/main_50_b/tasks/django__django-11820/oracle_record.json`
- `runs/main_50_b/tasks/django__django-11820/repair_record.json`
- `runs/main_50_b/tasks/django__django-11820/verification_record.full.json`
- `runs/main_50_b/tasks/django__django-12209/oracle_record.json`
- `runs/main_50_b/tasks/django__django-12209/repair_record.json`
- `runs/main_50_b/tasks/django__django-12209/verification_record.full.json`
- `runs/main_50_b/tasks/django__django-13023/oracle_record.json`
- `runs/main_50_b/tasks/django__django-13023/repair_record.json`
- `runs/main_50_b/tasks/django__django-13023/verification_record.full.json`
- `runs/main_50_b/tasks/django__django-13033/oracle_record.json`
- `runs/main_50_b/tasks/django__django-13033/repair_record.json`
- `runs/main_50_b/tasks/django__django-13033/verification_record.full.json`
- `runs/main_50_b/tasks/django__django-13297/oracle_record.json`
- `runs/main_50_b/tasks/django__django-13297/repair_record.json`
- `runs/main_50_b/tasks/django__django-13297/verification_record.full.json`
- `runs/main_50_b/tasks/django__django-13569/oracle_record.json`
- `runs/main_50_b/tasks/django__django-13569/repair_record.json`
- `runs/main_50_b/tasks/django__django-13569/verification_record.full.json`
- `runs/main_50_b/tasks/django__django-13786/oracle_record.json`
- `runs/main_50_b/tasks/django__django-13786/repair_record.json`
- `runs/main_50_b/tasks/django__django-13786/verification_record.full.json`
- `runs/main_50_b/tasks/django__django-13820/oracle_record.json`
- `runs/main_50_b/tasks/django__django-13820/repair_record.json`
- `runs/main_50_b/tasks/django__django-13820/verification_record.full.json`
- `runs/main_50_b/tasks/django__django-14140/oracle_record.json`
- `runs/main_50_b/tasks/django__django-14140/repair_record.json`
- `runs/main_50_b/tasks/django__django-14140/verification_record.full.json`
- `runs/main_50_b/tasks/django__django-14631/oracle_record.json`
- `runs/main_50_b/tasks/django__django-14631/repair_record.json`
- `runs/main_50_b/tasks/django__django-14631/verification_record.full.json`
- `runs/main_50_b/tasks/django__django-15375/oracle_record.json`
- `runs/main_50_b/tasks/django__django-15375/repair_record.json`
- `runs/main_50_b/tasks/django__django-15375/verification_record.full.json`
- `runs/main_50_b/tasks/django__django-16082/oracle_record.json`
- `runs/main_50_b/tasks/django__django-16082/repair_record.json`
- `runs/main_50_b/tasks/django__django-16082/verification_record.full.json`
- `runs/main_50_b/tasks/django__django-16136/oracle_record.json`
- `runs/main_50_b/tasks/django__django-16136/repair_record.json`
- `runs/main_50_b/tasks/django__django-16136/verification_record.full.json`
- `runs/main_50_b/tasks/django__django-16255/oracle_record.json`
- `runs/main_50_b/tasks/django__django-16255/repair_record.json`
- `runs/main_50_b/tasks/django__django-16255/verification_record.full.json`
- `runs/main_50_b/tasks/django__django-16315/oracle_record.json`
- `runs/main_50_b/tasks/django__django-16315/repair_record.json`
- `runs/main_50_b/tasks/django__django-16315/verification_record.full.json`
- `runs/main_50_b/tasks/django__django-16631/oracle_record.json`
- `runs/main_50_b/tasks/django__django-16631/repair_record.json`
- `runs/main_50_b/tasks/django__django-16631/verification_record.full.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-20488/oracle_record.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-20488/repair_record.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-20488/verification_record.full.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-22719/oracle_record.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-22719/repair_record.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-22719/verification_record.full.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-22865/oracle_record.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-22865/repair_record.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-22865/verification_record.full.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-23299/oracle_record.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-23299/repair_record.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-23299/verification_record.full.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-23476/oracle_record.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-23476/repair_record.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-23476/verification_record.full.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-24177/oracle_record.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-24177/repair_record.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-24177/verification_record.full.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-24637/oracle_record.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-24637/repair_record.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-24637/verification_record.full.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-24970/oracle_record.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-24970/repair_record.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-24970/verification_record.full.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-25479/oracle_record.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-25479/repair_record.json`
- `runs/main_50_b/tasks/matplotlib__matplotlib-25479/verification_record.full.json`
- `runs/main_50_b/tasks/mwaskom__seaborn-3069/oracle_record.json`
- `runs/main_50_b/tasks/mwaskom__seaborn-3069/repair_record.json`
- `runs/main_50_b/tasks/mwaskom__seaborn-3069/verification_record.full.json`
- `runs/main_50_b/tasks/psf__requests-1142/oracle_record.json`
- `runs/main_50_b/tasks/psf__requests-1142/repair_record.json`
- `runs/main_50_b/tasks/psf__requests-1142/verification_record.full.json`
- `runs/main_50_b/tasks/psf__requests-2931/oracle_record.json`
- `runs/main_50_b/tasks/psf__requests-2931/repair_record.json`
- `runs/main_50_b/tasks/psf__requests-2931/verification_record.full.json`
- `runs/main_50_b/tasks/psf__requests-5414/oracle_record.json`
- `runs/main_50_b/tasks/psf__requests-5414/repair_record.json`
- `runs/main_50_b/tasks/psf__requests-5414/verification_record.full.json`
- `runs/main_50_b/tasks/pydata__xarray-4966/oracle_record.json`
- `runs/main_50_b/tasks/pydata__xarray-4966/repair_record.json`
- `runs/main_50_b/tasks/pydata__xarray-4966/verification_record.full.json`
- `runs/main_50_b/tasks/pylint-dev__pylint-4661/oracle_record.json`
- `runs/main_50_b/tasks/pylint-dev__pylint-4661/repair_record.json`
- `runs/main_50_b/tasks/pylint-dev__pylint-4661/verification_record.full.json`
- `runs/main_50_b/tasks/pylint-dev__pylint-6903/oracle_record.json`
- `runs/main_50_b/tasks/pylint-dev__pylint-6903/repair_record.json`
- `runs/main_50_b/tasks/pylint-dev__pylint-6903/verification_record.full.json`
- `runs/main_50_b/tasks/pylint-dev__pylint-8898/oracle_record.json`
- `runs/main_50_b/tasks/pylint-dev__pylint-8898/repair_record.json`
- `runs/main_50_b/tasks/pylint-dev__pylint-8898/verification_record.full.json`
- `runs/main_50_b/tasks/pytest-dev__pytest-10051/oracle_record.json`
- `runs/main_50_b/tasks/pytest-dev__pytest-10051/repair_record.json`
- `runs/main_50_b/tasks/pytest-dev__pytest-10051/verification_record.full.json`
- `runs/main_50_b/tasks/pytest-dev__pytest-5787/oracle_record.json`
- `runs/main_50_b/tasks/pytest-dev__pytest-5787/repair_record.json`
- `runs/main_50_b/tasks/pytest-dev__pytest-5787/verification_record.full.json`
- `runs/main_50_b/tasks/pytest-dev__pytest-7236/oracle_record.json`
- `runs/main_50_b/tasks/pytest-dev__pytest-7236/repair_record.json`
- `runs/main_50_b/tasks/pytest-dev__pytest-7236/verification_record.full.json`
- `runs/main_50_b/tasks/pytest-dev__pytest-7521/oracle_record.json`
- `runs/main_50_b/tasks/pytest-dev__pytest-7521/repair_record.json`
- `runs/main_50_b/tasks/pytest-dev__pytest-7521/verification_record.full.json`
- `runs/main_50_b/tasks/scikit-learn__scikit-learn-10908/oracle_record.json`
- `runs/main_50_b/tasks/scikit-learn__scikit-learn-10908/repair_record.json`
- `runs/main_50_b/tasks/scikit-learn__scikit-learn-10908/verification_record.full.json`
- `runs/main_50_b/tasks/sphinx-doc__sphinx-10323/oracle_record.json`
- `runs/main_50_b/tasks/sphinx-doc__sphinx-10323/repair_record.json`
- `runs/main_50_b/tasks/sphinx-doc__sphinx-10323/verification_record.full.json`
- `runs/main_50_b/tasks/sphinx-doc__sphinx-10435/oracle_record.json`
- `runs/main_50_b/tasks/sphinx-doc__sphinx-10435/repair_record.json`
- `runs/main_50_b/tasks/sphinx-doc__sphinx-10435/verification_record.full.json`
- `runs/main_50_b/tasks/sphinx-doc__sphinx-10466/oracle_record.json`
- `runs/main_50_b/tasks/sphinx-doc__sphinx-10466/repair_record.json`
- `runs/main_50_b/tasks/sphinx-doc__sphinx-10466/verification_record.full.json`
- `runs/main_50_b/tasks/sympy__sympy-13480/oracle_record.json`
- `runs/main_50_b/tasks/sympy__sympy-13480/repair_record.json`
- `runs/main_50_b/tasks/sympy__sympy-13480/verification_record.full.json`
- `runs/main_50_b/tasks/sympy__sympy-14711/oracle_record.json`
- `runs/main_50_b/tasks/sympy__sympy-14711/repair_record.json`
- `runs/main_50_b/tasks/sympy__sympy-14711/verification_record.full.json`
- `runs/main_50_b/tasks/sympy__sympy-17318/oracle_record.json`
- `runs/main_50_b/tasks/sympy__sympy-17318/repair_record.json`
- `runs/main_50_b/tasks/sympy__sympy-17318/verification_record.full.json`
- `runs/main_50_b/tasks/sympy__sympy-19783/oracle_record.json`
- `runs/main_50_b/tasks/sympy__sympy-19783/repair_record.json`
- `runs/main_50_b/tasks/sympy__sympy-19783/verification_record.full.json`
- `runs/main_50_b/tasks/sympy__sympy-24562/oracle_record.json`
- `runs/main_50_b/tasks/sympy__sympy-24562/repair_record.json`
- `runs/main_50_b/tasks/sympy__sympy-24562/verification_record.full.json`