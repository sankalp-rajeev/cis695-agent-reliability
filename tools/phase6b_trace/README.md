# Phase 6b tracer and repaired-executor harness

`scripts/phase6b_run.py` has two commands. `smoke` uses the smallest nonempty,
executable pytest and Django lists outside the 13-task evaluation set, plus the
smallest non-evaluation Django task with sealed parallel-worker evidence. `run`
requires clean HEAD at the annotated `phase6b-harness-frozen` tag. Evaluation resumes only from hash-verified per-task checkpoints; neither command overwrites captures. All output stays under ignored `runs/`.

```sh
env -u PYTHONPATH .venv/bin/python scripts/phase6b_run.py smoke --output runs/phase6b_smoke_NEW
env -u PYTHONPATH .venv/bin/python scripts/phase6b_run.py run --freeze-tag phase6b-harness-frozen --output runs/phase6b_NEW
```

Evaluation is authorized by the overnight protocol after the build/freeze gates; it runs only from a detached worktree at the annotated harness tag. Smoke outputs are marked `smoke_only` and never enter the
evaluation aggregation. Smoke timing ratios are information only: interpreter startup dominates these
small lists. They never enter experiment overhead or cost numbers.

The harness subclasses Phase 4's `FrozenContainer` only to add a read-only code
bind and a separate writable output bind, and to supply tracing environment
variables to the execution driver. It uses `ContainerTestExecutor`, the immutable
Phase 4 image IDs, source/pre_install proofs, 1800-second pass budget, original
driver, `--pull=never`, `--network none`, and `--cpu-shares 2048`. Collection and
startup probes stay untraced. Every evaluation command prefix is checked against
the manifested Phase 4 capture before any container starts. Unsupported commands halt rather than changing the command. Forked parallel
workers preserve the sealed command, including its existing parallelism.

`sitecustomize` activates only from the harness environment variable and defers
tracer import until a framework is imported. It never reads `sys.argv`, never
raises during startup, and writes a per-PID error marker on an internal failure.
The execution driver does not import a framework, so it remains uninstrumented.
Every global trace callback returns `None`: no local/line trace is installed.
`threading.settrace` and low-level-thread wrappers follow Python threads with
inherited test ownership. The pytest protocol and shared fixture/finalizer hooks
cover setup and teardown. Django's `TestCase.run` wrapper and shared suite calls
cover class setup, `setUpTestData`, and teardown.

The fork hook reinitializes process-local state and locks, preserving inherited
shared setup. Each PID writes its own `<pid>.jsonl.gz` journal: one interned code
index, incremental shared coverage and per-test integer lists. Checkpoints at
test/suite completion and the `os._exit` hook preserve pool-worker output.
Exclusive readiness markers prevent PID collisions. Per-PID readiness/completion
markers are required; any error marker fails the gate. Root and fork-worker PIDs
come from the executor events and the traced fork relationships.

The host merges through the executor's `raw_execution_map` and
`execution_id_map` only, including ancestor shared setup/teardown. It never
re-parses or guesses names. `TRACE_INCOMPLETE` is reserved for executed,
non-skipped tests missing a record or spawning an unfollowed process (including
children that strip the activation environment). Loading native extensions or
successfully followed fork workers does not create an incompleteness flag.
Skipped/untraced/error/not-reached selections remain retained and counted.
The parallel smoke must observe multiple test-running workers and no more than
5% incomplete executed tests. A missing/error marker fails the gate separately.

Changed-file and AST-qualified changed-function targets are built from the
frozen candidate patch and verified base archive, without importing task code.
New definitions/files absent from base and unavailable mappings conservatively
retain the full list. Module-level edits fall back to file hits. Function-level
selection is checked to be a subset of file-level selection.

For evaluation, one untraced base pass and one traced base pass precede the two
selected patched passes. There is no extra full patched baseline pass. That
baseline comes from the sealed Phase 4 module-process durations; all retry and
fallback end events are summed. The harness reports retained IDs, actual
executed-family counts, the frozen reduction/overhead/cost metrics, per-ID
disagreements, Phase 4 FLAKY exclusions, and blind spots. A seeded task's recall
is null (vacuous). Infrastructure halts write an incident and raw evidence but
publish no experiment metrics; amend the plan and restart from task 1.

Synthetic gate command:

```sh
bash scripts/test.sh tests/unit/test_phase6b_trace.py tests/unit/test_phase5_replay.py --tb=short
```

No correctness labels, oracle inputs, coverage.py, image installation, model
calls, or Phase 6a file changes are used by this implementation.

A1 scope records use an interned code index and a `scopes` array: every call-set
record includes session/module/class/test, explicit owning tests, and code IDs.
Primary selection includes every scope. The exploratory test-window selection
uses only test-scope records and conservatively retains missing records. Python
helpers inherit explicit scope ownership even when replacing their environment;
exec replacements write separate PID segments. Non-Python observations do not
flag tests. An unfollowable Python child flags only its recorded scope.

Evaluation task order is exactly eval_set.json. `--task-limit 3` checkpoints in
batches; subsequent invocations use `--resume`. Completed task manifests must
match every capture hash and file path before skipping. `HALT.json` prevents
resuming an infrastructure halt, as required by frozen section h. A disk check
runs before each task; the original wall-clock deadline is retained across
resumption. Scripts, source, and tracer tree hashes identify the frozen code.
