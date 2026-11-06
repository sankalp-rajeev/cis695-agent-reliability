# Read-only live paired-experiment monitor

Helper: `/home/sankalp/projects/cis695-agent-reliability/scripts/monitor_v2_scg_live.py`.
It is outside the detached execution worktree and frozen inputs. It reads
completed `paired.json` and `paired_arm.json` records only, imports no experiment
module, and invokes no subprocess, Docker command or process control operation.
It does not change the existing `progress.py`, experiment outputs or verdicts.

Use the following in an Ubuntu terminal:

```bash
MONITOR='/home/sankalp/projects/cis695-agent-reliability/scripts/monitor_v2_scg_live.py'
RESULTS='/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results'

# Latest completed task with explanations; refresh every 15 seconds.
watch -n 15 "env -u PYTHONPATH /usr/bin/python3 -B '$MONITOR' --results '$RESULTS' --latest --reason-limit 2"

# All-completed-task verdict totals and task-arm reason counts, every 15 seconds.
watch -n 15 "env -u PYTHONPATH /usr/bin/python3 -B '$MONITOR' --results '$RESULTS' --summary"
```

Each watch command runs until Ctrl+C, which stops only the display. Run the two
modes in separate terminals or invoke them sequentially after stopping a display.
The helper prints task-file count/83, percentage and arm-file count/166. It does
not rely on `results.json`, which is published only at the end of collection.

For every exact recorded reason, or details for every completed task:

```bash
env -u PYTHONPATH /usr/bin/python3 -B "$MONITOR" --results "$RESULTS" --latest --all-reasons
env -u PYTHONPATH /usr/bin/python3 -B "$MONITOR" --results "$RESULTS" --all --all-reasons
env -u PYTHONPATH /usr/bin/python3 -B "$MONITOR" --results "$RESULTS" --task astropy__astropy-13977 --all-reasons
```

`--json` prints the full structured snapshot without truncating reason lists.
The default text limit is eight entries per diagnostic list. `--reason-limit 0`
and `--all-reasons` both print every entry; smaller limits explicitly state how
many entries were omitted. Exact incompleteness strings are never paraphrased
into replacement verdicts. Terminal control escapes are removed for text display.

## Explanation semantics

- `ZERO_SELECTION`: available empty selection; no selected tests or runner calls.
- `UNAVAILABLE_SELECTION`: unavailable selection/shared preparation; show the
  recorded reason and selection status. Null selections remain null.
- `EXECUTED + NOT_AVAILABLE`: a nonempty request produced no native-counted
  executions. The raw case inventory may still contain outcomes. The helper
  displays both without promoting them to native PASS or FAIL.
- `INCOMPLETE`: show recorded original and final verdicts, completeness and exact
  incompleteness strings, including timeouts, runner errors and missing-ID gaps.
- `PASS`/`FAIL`: show the unchanged native verdict, selected count, per-phase
  execution coverage, outcome counts and regression IDs. A recorded FAIL retains
  its precedence even when other evidence gaps exist.
- Other verdicts and missing verdicts remain explicit, including
  `BASELINE_UNRELIABLE` and `NO_VERDICT` in the summary.

Raw coverage is the number of concrete `raw_results` entries. Mapped coverage is
the number of requested selected IDs represented by recorded raw-ID mappings.
Admitted coverage is the number of requested selected-ID results with statuses
passed/failed/skipped/error, excluding NOT_RUN/TIMEOUT. These are distinct units;
parameterized families can expand into multiple concrete cases.

The native-counted outcome total follows the frozen `Outcome.executed` display
definition: all recorded outcomes except NOT_RUN/TIMEOUT, including ERROR. This
is a count of recorded classifications, not a new execution or verdict rule.
Missing fields are labelled unknown where appropriate. Confirmation/shadow calls
are shown separately from initial base/patched calls and are not silently merged.

NOT_RUN and absent raw mappings do not by themselves prove a test is missing:
parameter-family admission, collection behavior or incomplete capture can also
produce gaps. A parameter-family admission flag requires actual bracketed raw
IDs mapped to a bare selected NOT_RUN ID in the saved evidence. No new ID
normalization or test collection is performed.

SCG graph status, selection status, resolved-seed count, graph failures and mapping
diagnostics come from the selection record embedded in each arm. An empty list
is not called a graph failure. An exact failure mechanism is unknown unless the
recorded diagnostics establish it; graph completeness alone is not dynamic
reachability proof.

Summary reason counts count each task-arm once per group. Groups overlap, so
their totals are not expected to sum to the completed-task count. The summary
also lists selection-status counts, including specific unavailable statuses.
Detailed mode exposes exact reasons behind those groups.

Files may appear during writes. The progress line counts existing completion
files, while malformed/partial JSON is deferred with a warning until the next
refresh. A paired/arm disagreement is flagged; the helper retains the paired
record's native verdict and does not repair or overwrite either file. It does
not rehash raw captures or make a new evidence-integrity certification.

Validation for this helper uses synthetic monitoring records only:

```bash
env -u PYTHONPATH /usr/bin/python3 -B tests/unit/test_monitor_v2_scg_live.py
```

No benchmark test, scientific audit, experiment validation or Docker operation is
part of this helper's checks.
