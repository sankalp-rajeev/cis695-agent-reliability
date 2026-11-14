# Phase 3 Fixes 6–8 and base-only cost measurements

Preflight passed: worktree `cis695-v2-scg-ubuntu-publication`, branch `experiment/v2-execution-repair`, clean; local HEAD, upstream ref, and live origin were all `ae9e4a7247df99cf94b5b050d63cd6b8c1c47a1d`.

The plan amendment was committed first in `171dbfc`, before code: H1b is explicitly added after the Fix 5 projection and before Phase 4. Its fixed residual is 13,853 B1 slots (37,614 minus 23,761); predicted live admissions at least 6,927, falsified below 25% (3,463). Invalid IDs never count as admitted. H1 is already met offline at 63.17%, largely from parsing. H2's primary yes/no is PASS or FAIL, with REGRESSION_ERROR added only in a secondary count. Existing H1/H2/B1/B2 thresholds and baselines were preserved.

SymPy warning alignment is committed separately in `9c0f387`. See [the harness comparison and quantum module load check](../phase3_fix6/SYMPY_ALIGNMENT.md). The requested single-module check admitted all 16 identities to collection, with zero test bodies executed. It does not establish execution outcomes for that module.

- Fix 6, `24b1822`: every shared verifier launch requests `--cpu-shares 2048`; base and patched trees use the same container. Agent/generator launch preparation and standalone audit/helper launches also set the shares. No CPU-time cap is added. Tests cover all three runner repositories on both trees and idempotent agent configuration.
- Fix 7, `a8e1691`: default per-pass budget is a recorded parameter of 1,800 s, covering tree preparation, static/native validation, uploads, and runner execution. The deadline is passed through collection and execution; completed collector modules retain atomic partial receipts. At a cap, completed outcomes survive and unreached IDs carry `NOT_REACHED` plus elapsed seconds. Driver process groups are killed and pending modules are not retried. Evidence persistence and container cleanup may add wall time after the execution deadline. Historical caches cannot cross the CPU/budget revision or a different configured pass budget. The old per-instance budget remains metadata rather than a hard stop; its nominal initial-pair default is now 3,600 s.
- Fix 8, `de3090f`: each new assertion FAIL or REGRESSION_ERROR gets six isolated invocations: three base and three patched. Baseline cache entries are bypassed for these invocations. Stability requires base PASS 3/3 and observed patched FAILED/ERROR 3/3; skips, xfails, missing evidence, timeouts, and infrastructure errors cannot establish stable failure. All six attempts run even if an earlier attempt is unstable. The original failure kind is retained for stable cases; others become FLAKY. Missing confirmation evidence blocks a would-be PASS. Each receipt identifies candidate, tree, attempt, and the aggregate stability decision. Concrete parameter identities and inherited owner instances are confirmed separately, without adding families.

Full unit suite in this worktree's environment: **1,137 passed, 6 failed, 6 skipped, 17 setup errors**, 16.69 s. The exact 23 failure/error identities match the pre-existing baseline. Reasons: one missing ignored patch fixture; three Landlock ABI failures; one stale historical configuration-default assertion; historical source seals (one failure and 17 setup errors). No seals, historical protocols, correctness fixtures, or unrelated failure causes were changed. See [the identity comparison](../phase3_fix8/preexisting_unit_failures.csv) and [unit counts](../phase3_fix8/unit_summary.json). Fix-specific tests: 10 CPU, 6 budget, 18 confirmation.

## Cost protocol

Driver commit: `92c55b9`; `scripts/phase3_cost_probes.py` selects only by frozen V2 selection size, with task ID as a tie breaker. Native SymPy repositories are classified as SymPy, rather than the frozen incorrect pytest designation. Frozen totals: 31 Django tasks / 39,082 IDs; 47 pytest tasks / 15,978 IDs; 5 SymPy tasks / 2,622 IDs. Total: 83 tasks and 57,682 original selected IDs per tree.

Largest selections: Django-13297 (8,152), Astropy-13977 (3,080), SymPy-13480 (781). Each cost probe runs base only, once, serially, with no paired verdict or correctness comparison. The probe verifies archived source hashes and effective configs, and Docker's actual CpuShares=2048, NanoCpus=0, NetworkMode=none. Frozen selections and images are unchanged. A cap hit is retained as a censored measurement and never retried. No Phase 4 concurrency has been selected, and no controlled Phase 4 run has started.

## Measured base-only costs

Wall time below includes the measured selected-task archive/input preparation, container setup, pass, capture persistence, and cleanup. The one-time 83-task size scan and later report derivation are outside that timer. The recorded pass budget applies to the executor pass, shown separately. All three finished without a cap hit, with zero NOT_REACHED or TIMEOUT slots. These are cost measurements and original-slot evidence counts, not task verdicts.

| Runner / size-selected task | Selected IDs | Collection s | Pass s | Total wall s | Initial / fallback processes | Admitted C / missing C / invalid | Admitted S / missing S |
|---|---:|---:|---:|---:|---:|---:|---:|
| Django / django__django-13297 | 8,152 | 103.37 | 311.60 | 314.82 | 258 / 0 | 7,827 / 303 / 22 | 7,121 / 1,009 |
| pytest / astropy__astropy-13977 | 3,080 | 121.47 | 341.95 | 344.26 | 91 / 0 | 2,914 / 150 / 16 | 2,727 / 337 |
| SymPy / sympy__sympy-13480 | 781 | 32.61 | 1,151.12 | 1,152.48 | 15 / 16 | 744 / 19 / 18 | 715 / 48 |

Each row balances selected = admitted + missing + invalid under either policy. Strict accounting checks every concrete instance; mixed parameter/owner families containing a skip are missing even when the original slot's worst aggregate status is PASS or FAIL. All owned containers were removed.

Owner expansion is reported separately from original slots and parameter cases:

| Task | Owner-expanded original slots | Predicted owner instances | Native runnable instances (including parameters) |
|---|---:|---:|---:|
| Django-13297 | 199 | 1,041 | 8,679 |
| Astropy-13977 | 65 | 330 | 11,525 |
| SymPy-13480 | 0 | 0 | 763 |

Expansion retains the same inherited test code and never adds a family. Per-slot validation receipts retain the owner/parameter identities and reasons. The archived Astropy pyproject.toml was restored to its frozen source/config bytes; no packages or test code were changed. The other two needed no config restoration. Verified base Python/bin-test/config file counts were 2,675 / 934 / 1,182 respectively.

SymPy's 16 execution collection errors remain in the quantum-printing module (one initial attempt and 16 individual fallbacks); three other test ERROR slots are also missing. Its successful 16-ID load-only check does not imply successful native CLI execution. The native execution framework installs warning-as-error filters later, and the prior load-time DeprecationWarning/Reporter failure remains captured. The 18 INVALID_ID slots came from successful native absence; none was inferred from a collector failure. No SymPy runner-unavailable slots remain in this fresh native run.

## Estimates for 83 tasks × 2 trees

Two explicit models show sensitivity to the extrapolation assumption; this range is not a confidence interval. Every task's frozen size and estimated cost appears in all_83_selection_sizes.csv and the two task-estimate CSVs.

1. **Selected-ID model:** measured setup per task plus pass time proportional to the task's selected-ID count within its runner, with each estimated pass capped at 1,800 s.
2. **Secondary stage-aware model:** measured fixed pass overhead per task, native collection time proportional to module count, and execution time proportional to selected-ID count. Each estimated pass is capped at 1,800 s.

Both use base cost as the patched-cost proxy, charge setup twice conservatively, and schedule each task's two trees together. Two/four-container estimates use deterministic longest-first scheduling and assume no resource contention. Those parallel timings were not measured. One largest-task observation per runner cannot capture differences among repositories, native parameter multiplicities, test complexity, import errors, or patched runtime changes.

| Containers | Selected-ID model | Secondary stage-aware model |
|---:|---:|---:|
| 1 (serial) | 14,695.94 s = **4.08 h** | 17,508.04 s = **4.86 h** |
| 2 | 7,347.99 s = **2.04 h** | 8,758.29 s = **2.43 h** |
| 4 | 3,676.17 s = **1.02 h** | 4,395.18 s = **1.22 h** |

These are the **166 initial passes**, before new-failure confirmation. Total Phase 4 cost adds six isolated passes per new candidate; the candidate count cannot be inferred from base-only measurements. As module-sized planning proxies, six confirmations cost about 83 s (Django), 202 s (pytest), or 164 s (SymPy) using measured median module times plus fixed pass overhead; corresponding p95-module proxies are 90 / 227 / 409 s. They are not measurements of isolated selected-ID confirmations or probability bounds. For example, ten candidates add roughly 14–34 serial minutes using the median proxies. Six full pass budgets allow up to 10,800 s (3 h) of budgeted work per candidate, plus cleanup. The 166 full initial-pass budgets alone sum to 83 serial hours; this is a budget-only ceiling, not the estimate. The unchanged Phase 4 plan stops at 12 h and reports partial evidence.

**No concurrency is chosen.** No Phase 4 execution/tag, paired task verdict, or correctness comparison was made.

## Capture integrity and final reader check

All timing-capture component hashes match committed version `92c55b9`. Afterwards `0f193b4` added only host capture interpretation of an explicitly started but unfinished verbose test: TIMEOUT, while pending tests remain NOT_REACHED. It changes no runner argv, test process, selected identity, or measured timing. Four added unit cases cover pytest, Django, SymPy, and sibling-name/ANSI matching. Replaying all three stored base captures with this reader changed **zero outcomes, admissions, missing counts, or timings**; all three probes had completed within budget. No test execution was repeated. Each base_probes/*/classification_replay.json records the original and reader commits and source hashes.

Final unit suite after that correction: **1,141 passed, 6 failed, 6 skipped, 17 setup errors**, 16.80 s. The failure/error identity set still exactly matches the pre-existing baseline; see unit_summary.json and ../phase3_fix8/preexisting_unit_failures.csv. The prior 1,137-pass result above describes the Fix 8 commit before these four added cases.

base_probe_summary.csv is the small combined chart table. Each base_probes subdirectory contains a summary, per-module process CSV, original source/input manifest, corrected run JSON (gzip), unchanged original capture archive, and a SHA-256 index of its raw evidence. capture_index.json explains path remapping for replay. estimates.json and stage_aware_estimates.json preserve the formulas' inputs, assumptions, timings, and explicit null concurrency choice. artifact_manifest.json seals the report package. Correctness labels were not opened or used.

Reproduction (use fresh directories; probes are serial):

```bash
env -u PYTHONPATH .venv/bin/python scripts/phase3_cost_probes.py --runner django --output /tmp/new-cost/django
env -u PYTHONPATH .venv/bin/python scripts/phase3_cost_probes.py --runner pytest --output /tmp/new-cost/pytest
env -u PYTHONPATH .venv/bin/python scripts/phase3_cost_probes.py --runner sympy --output /tmp/new-cost/sympy
env -u PYTHONPATH .venv/bin/python scripts/phase3_cost_probes.py --output /tmp/new-cost
env -u PYTHONPATH .venv/bin/python scripts/phase3_cost_sensitivity.py --output /tmp/new-cost
```
