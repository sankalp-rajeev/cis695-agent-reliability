# Three-task diagnostic pilot — 2026-11-05

**The authorized pilot completed: 3/3 tasks and 6/6 arm records, with CLI exit code 0. The unlabeled harness summary also completed successfully.** All six records have COMPLETE accounting, but only four have a binary PASS outcome. No full-cohort comparison was launched.

**GO for this pilot's collection/integrity checks. NO-GO for expanding execution before review of native parameter-family verdict handling and the remaining import-provenance limits, followed by separate authorization.** This recommendation does not change or relabel any native verdict.

Exact execution identity:

- Harness: `b030e508d849926b9a2260c70e1091adebfee993`, clean detached worktree `/home/sankalp/projects/cis695-v2-scg-paired-review-b030e50`.
- Frozen protocol: `2eaf8341274099cf4210674e6418a4b1e44ea2d0babb09a1c2243f77258c5153`.
- Approved plan: `57c84e2ceb615ebe7df43a5a26cf140b300b5a838f706ce6f7f7a5d2b9a77f1d`; the existing plan and frozen selections were reused unchanged.
- Execution interval: **2026-11-05 11:32:27–11:33:21 MST (America/Phoenix)**.
- Actual harness output directory: `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/pilot_20261105T183041_929325Z/results`.
- Logs, summary, diagnostic tables and report directory: `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/pilot_20261105T183041_929325Z`.

Before launch, frozen validation and all 83 exact tag/host-ID/daemon bindings passed. All **83 base archives** and **1,546 shared source-file entries** were independently hash-checked against the freeze. The guarded `run` command received the exact approved plan hash and only its three-task schedule. Validation passed again after completion. All **766 frozen files** and the approved plan remain byte-identical. No source, selector, classifier, patch, image or plan was modified. No correctness-label or witness sidecar was read or supplied.

Native results, in approved task/arm order:

| Task / arm | Native signal | Execution status | Selected IDs | Raw-accounted selected IDs, base / patched | Unique concrete outcomes per pass | Execution wall |
|---|---|---|---:|---|---|---:|
| Django-15103 V2 | PASS | EXECUTED | 47 | 47 / 47 | 47 passed | 5.117 s |
| Django-15103 SCG | PASS | EXECUTED | 1 | 1 / 1 | 1 passed | 3.367 s |
| Matplotlib-25287 SCG | NOT_AVAILABLE | ZERO_SELECTION | 0 | No passes | 0 | 0.000 s |
| Matplotlib-25287 V2 | NOT_AVAILABLE | EXECUTED | 2 | 2 / 2 | 4 passed, 2 skipped | 11.602 s |
| Xarray-4629 V2 | PASS | EXECUTED | 22 | 22 / 22 | 32 passed | 10.046 s |
| Xarray-4629 SCG | PASS | EXECUTED | 21 | 21 / 21 | 51 passed, 12 XFAIL | 21.758 s |

Every concrete-outcome count above applies independently to both base and patched passes. Parameterized families expand one selected ID into multiple concrete cases. This is normal runner expansion, not test injection. Raw-accounted IDs establish observed case coverage, not that every test body ran successfully: SKIPPED and expected-failure outcomes are shown explicitly. The unchanged adapter maps native XFAIL to SKIPPED internally; the original native outcomes remain in raw logs and the diagnostic inventory.

Totals: **93 selected-ID slots** across the six frozen lists; **186/186 requested selected-ID slots accounted** across ten base/patched pass observations; **298 unique concrete outcomes across those passes**: **270 passed, 4 native SKIPPED and 24 native XFAIL**. There were **12 native runner batches**, all with recorded exit code **0**, because Django V2 splits 47 requested labels into two batches per pass. There were **0 timeouts, 0 crashes, 0 infrastructure errors, 0 unaccounted selected IDs, 0 unmatched/ambiguous raw IDs, 0 runtime source mismatches and 0 evidence-integrity failures**. No production confirmation or shadow confirmation pass was added.

The Matplotlib V2 NOT_AVAILABLE result needs explicit interpretation. Both requested families actually produced their expected parameterized raw cases, and both phases had complete capture with no missing raw ID. The unchanged legacy parser admits only exact selected IDs; the emitted `[png]`, `[pdf]` and `[svg]` IDs leave both unparameterized selected-family statuses as legacy NOT_RUN. Native scoring therefore emits NOT_AVAILABLE, even though lossless raw accounting establishes COMPLETE capture. This is **not** a missing image, runner crash, empty V2 list or genuine absence of test execution. Its verdict is preserved, not promoted to PASS. Xarray also has legacy NOT_RUN family entries (2 for V2 and 4 for SCG per pass), but has other exactly admitted IDs and therefore native PASS outcomes. The distinction should be reviewed before broad comparative execution.

The empty Matplotlib SCG arm behaved correctly: selected list `[]`, ZERO_SELECTION, native NOT_AVAILABLE, zero calls, zero wall time, and no `environment.json` or raw-test directory. Docker corroborates **five unique benchmark containers**: two Django, one Matplotlib and two Xarray, with none left running/existing after cleanup. The sole Matplotlib container served V2. The two Matplotlib NOT_AVAILABLE signals therefore have different causes and must not be interpreted as two unexecuted arms.

Runtime source and import evidence:

| Task | Source equivalence before tests | Actual import-path evidence captured | Remaining limit |
|---|---|---|---|
| Django, both arms | All 6 common selected/changed files per container match the frozen archive hashes | Native runner explicitly reports Django installed in `/testbed/django` | No complete per-module `__file__` or `sys.path` inventory |
| Matplotlib V2 | Both common files match: changed `lib/matplotlib/axis.py` and selected `lib/matplotlib/tests/test_skew.py` | Pytest reports `/testbed` rootdir, selected test IDs and `/opt/miniconda3/envs/testbed/bin/python` | Rootdir/test paths do **not** establish where imported Matplotlib library modules resolve |
| Xarray, both arms | All 7 common files match, including SCG-only selected test files | Runtime warning locations include `/testbed/xarray/__init__.py`, core modules and test modules; interpreter path is recorded | These locate the reported modules only, not every transitive import |

All **5/5 nonempty-arm source preflights passed**, verifying **28 task/arm source entries**. The same common-file union is checked for both arms of each task. The empty SCG arm has no runtime source/import observation, by design. Image Git HEAD differs from the dataset base commit in all five environment records, as anticipated by the approved protocol; the relevant file hashes match. This is not evidence of full historical repository/image equivalence. The source preflight runs before candidate application; successful application of the exact hash-checked patch is recorded by the normal execution path, without a separate complete post-patch/import-origin inventory.

Within each task, both nonempty arms use the same image and runner. Container Python versions recorded are Django **3.9.20**, Matplotlib **3.11.11**, and Xarray **3.10.15**; those differences are between repository environments, not between arms. Matplotlib uses pytest 8.3.4 and Xarray pytest 7.4.0. **Full Python import-path fidelity is not established by this harness**, particularly Matplotlib's library-module origin. No extra diagnostic tests or in-container probes were injected to fill that gap.

A derived import-path extractor was corrected after evidence collection because the substring `testbed` in a Conda path could be mistaken for repository `/testbed`. Raw captures, hash checks, verdicts and counts never changed. The corrected evidence is `runtime_source_and_import_evidence_verified.json`; the original derived file and correction record are preserved for transparency.

Execution time and asymmetry:

- Native collection wall time: **52.167 seconds**. Complete guarded command, including initial validation: **53.587 seconds**.
- Sum of arm execution times: **51.890 seconds**. Per-task walls including arm checks/serialization: Django **8.539 s**, Matplotlib **11.652 s**, Xarray **31.859 s**, totaling **52.050 s**. These measurements exclude frozen historical selection-preparation costs; the native summary preserves those separate cost fields too.
- V2 arm wall sum: **26.765 s**; SCG arm wall sum including its zero arm: **25.125 s**. This heterogeneous three-task diagnostic is not a speed comparison.
- Django uses the same native adapter, with 47 versus 1 selected ID and two versus one runner batches per pass. Matplotlib has an intentional no-container SCG arm versus actual parameterized V2 execution. Xarray SCG requests fewer IDs (21 versus 22) but emits **63 versus 32 concrete outcomes per pass**, including expected-failure cases, and takes **21.758 versus 10.046 s**. Selected-list size is not concrete test count or a runtime guarantee.

The fixed arm order remained Django V2→SCG, Matplotlib SCG→V2, Xarray V2→SCG. Each nonempty arm used a fresh container with network disabled and no image pulls; no baseline cache or shared writable arm state was introduced. All six arm records are COMPLETE, but binary outcomes exist for only **4/6 arms and 2/3 task pairs**. PASS here is a native test result for the selected scope, not a correctness label or full-suite claim. No accuracy, precision, recall or F1 is inferred.

All **40 raw capture files** (stdout, stderr, runner output and event stream for each of ten passes) passed their stored SHA-256 checks. Every base/patched requested list and native runner argument sequence matches the frozen list/normalizer, with no fallback IDs. Full concrete IDs, mappings, exit statuses, skips/XFAILs, timings, cgroup snapshots and environment records are retained in the results. Docker's retrospective event buffer returned its bounded 256-event history; it corroborates five container identities and cleanup but does not prove an unbounded complete daemon history. Native per-pass event streams are complete and independently preserved.

Evidence paths:

- `results/results.json`, `results/collection_complete.json`, `results/run_provenance.json`: three-task completion and approved scope/hash provenance.
- `results/tasks/<instance_id>/<arm>/paired_arm.json`, `result.json`, optional `environment.json`, and `raw/<base-or-patched_uuid>/`: native arm records and lossless raw evidence.
- `unlabeled_summary.json`: successful harness summary without labels/witnesses; equals `results/metrics.json` as parsed JSON.
- `execution_inventory.csv` / `execution_inventory.json`: per-arm/per-pass selected IDs, actual concrete IDs, mappings, statuses, exit codes and times.
- `runtime_source_and_import_evidence_verified.json`, `raw_capture_integrity.json`, `frozen_integrity_after.json`: fidelity, capture-hash and preservation checks.
- `pilot_run.result.json`, `summarize.result.json`, `validate.result.json`, `validate_after.result.json`: all stage exit codes are 0.
- `docker_events.raw.jsonl`, `docker_execution_verification.json`: retained daemon evidence and the event-history caveat.
- `core_evidence_hashes.json` and final `evidence_sha256.json`: exact evidence hashes.

Key hashes:

- `results/results.json`: `1c38559c76a0f62f37bd7f301c988ceb02c6f2ab186b0680670e750cba03a8da`
- `unlabeled_summary.json`: `45209884ae969e644309ff22ea20316f16e9c7a3b3c87c99dc18d7ed0f155e07`

Stop point reached: **pilot and unlabeled summary complete; review the parameter-family scoring behavior and import-evidence limits before authorizing anything broader. No additional benchmark execution, full 83-task comparison, code change, commit or push was performed.**
