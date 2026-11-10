# Phase 6a runtime diagnostic

This tool runs only the fixed 13 outcome-informed witnesses from the Phase 4 post-hoc report. Its traces and test list must never feed test selection. It changes no production verifier or selector.

The container-side `sitecustomize.py` uses only `sys.settrace` and Python 3.5-compatible standard-library APIs and syntax. The host driver/summary require Python 3.11 and the existing Docker SDK. There are no image builds, installs, pulls, coverage calls, profiler hooks or thread monkeypatches. The tracer is mounted read-only and enabled through `PYTHONPATH=/runtime_trace`; disabled mode installs no hook. Django runs through `tests/runtests.py`.

`inputs.json` in the report pins the 13 identities, 9 pristine source archives, frozen candidate SHA-256 values, local Phase 4 image IDs, execution revision and static revision. Candidate paths come from the pinned Phase 4 audit, and their bytes must match `audited_labels.csv`. The summary verifies the exact witness list against the pinned Phase 4 report and the graph-builder hashes against the existing SCG source manifest. Labels are not graph inputs.

On a host with the original local archives, frozen patches, images and Python environment available, use a fresh `runs/phase6a_runtime_trace` directory:

```bash
mkdir -p runs/phase6a_runtime_trace
cp reports/next_phases/phase6a_runtime_trace/inputs.json runs/phase6a_runtime_trace/inputs.json
.venv/bin/python tools/runtime_trace/driver.py prepare
.venv/bin/python tools/runtime_trace/driver.py graphs
.venv/bin/python tools/runtime_trace/driver.py run
.venv/bin/python tools/runtime_trace/driver.py summarize
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tools/runtime_trace/test_tracer.py
```

`prepare` applies the candidate to a copy of the pristine source, maps added/deleted hunk lines to the innermost AST-qualified function and retains both definitions/ranges, including candidate-only functions. It does not use a hunk heading as definition identity. Unmapped module edits stay visible. No benchmark source is imported on the host. `graphs` rebuilds the pinned enhanced SCG base graph; no graph is built on patched source. Only `run` executes benchmarks, each in a fresh local image with network none, CPU shares 2048, no quota, and a 600-second process deadline. It verifies all archived source bytes before running. Every traced invocation is followed by an isolated untraced invocation on the same tree; results and exit codes are compared. `TRACE_PERTURBS` and missing/unverified results remain explicit.

Resume uses recorded invocation keys and verifies artifact hashes and tracer bytes. It refuses to overwrite incomplete invocations. Preserve an interrupted attempt in a separate ignored directory before retrying it; the final report records the superseded captures in a hash manifest. Source preparation and graph generation also refuse to overwrite existing outputs.

`sys.settrace` is thread-local. Pool feeder threads are not instrumented, and an asynchronous worker cannot acquire a fabricated hop count from the original test. The report records known unobserved feeder-thread calls as UNKNOWN, retains thread-start receipts, and preserves all Python frames in measured stacks. The first invocation and first invocation with the test still on the stack are separate records; a setup call has no test hop count. Forked processes receive separate first-entry receipts when observed. Native-code calls and other uninstrumented threads remain outside the observation scope.

The first missing edge is the first adjacent caller/callee pair without a resolved edge in the pinned graph, walking forward from the test in the live stack. All later missing edges are retained too. Runtime frames map to AST-qualified definitions on their own tree, then by path/qualified name into the base graph; patched line shifts are never mistaken for new identities. `reached_statically` uses unbounded resolved-edge reachability, with separate shortest-distance/depth-3 columns for SCG's actual bound. This comparison does not change graph resolution rules.

To verify deterministic reporting, capture the hashes of every generated report file, run `summarize` again, and compare. Exclude the check receipt `determinism.json` itself from the set it checks. The committed receipt records both identical maps. Raw `runs/`, `logs/`, JSONL traces and candidate patches remain ignored. The report publishes CSV/JSON summaries, frame evidence, and SHA-256 manifests only.
