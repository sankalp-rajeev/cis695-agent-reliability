#!/usr/bin/env python3
"""Preflight (amendment B9, 7b): the fast container checks of a verification run.

    preflight.py --inputs DIR --manifest IDS --task-specs SPEC... --output runs/... [--workers N]

For each (task, patch) it runs only the checks that can raise or block, using the
verifier's own functions: V1's in-container apply check, V3, and V2's run-health
collection (G1, with amendment A7's paired exclusion) on both trees. No test is
executed, no decision is made and no label is read. Patch contents are never printed.

It prints a table of every task that would raise an exception, block in run health
or set an infrastructure flag, and exits 0 only when there are no run-stopping
conditions (7a: Docker unreachable, disk below 20 GB, three consecutive tasks whose
container starts all failed) and no unclassified exceptions.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reliability.e2e_runner import CONSECUTIVE_START_FAILURES, machine_status  # noqa: E402
from reliability.verifier import container as containers  # noqa: E402
from reliability.verifier.container import ContainerStartError, PatchApplyError  # noqa: E402
from reliability.verifier.patch import PatchParseError  # noqa: E402
from reliability.verifier.run_health import RunHealthError  # noqa: E402

EXPERIMENT = 'preflight'


def classify(exc):
    """The class of an exception a run would meet. Only these two are understood."""
    if isinstance(exc, PatchApplyError):
        return 'patch_does_not_apply'
    if isinstance(exc, ContainerStartError):
        return 'container_start'
    if isinstance(exc, PatchParseError):
        return 'patch_unparseable'  # verify_task records a V1 exception absence on that task
    return 'unclassified'


def g1_row(error: RunHealthError):
    return {'g1': 'BLOCKED', 'g1_category': getattr(error, 'g1_category', None),
            'attribution': getattr(error, 'attribution', 'infrastructure')}


def exception_entry(stage, exc):
    return {'stage': stage, 'type': type(exc).__name__, 'class': classify(exc), 'message': str(exc)[:300]}


def check_task(job):
    """One task's preflight. Runs in a worker process; returns a JSON-able row."""
    from reliability.verifier.archive_tree import ArchiveTree
    from reliability.verifier.generic_health import paired_exception_scope
    from reliability.verifier.native_reference import load_drift
    from reliability.verifier.run_v1_4_1 import (
        container_apply_check, g1_with_paired_exclusion, integrity_signal, load_v2_settings, run_v3,
    )
    from reliability.verifier.selection import select_tests
    from reliability.verifier.task_specs import load_registries

    iid, patch_path, spec_paths, config, output = job
    started, starts_before = time.monotonic(), len(containers.START_EVENTS)
    tasks, _ = load_registries([Path(p) for p in spec_paths])
    task, patch_path = tasks[iid], Path(patch_path)
    patch_text = patch_path.read_bytes().decode('utf-8')
    folder = Path(output) / 'tasks' / iid / 'verification'
    folder.mkdir(parents=True, exist_ok=True)
    row = {'instance_id': iid, 'exceptions': [], 'apply': None, 'v1': None, 'v3': None, 'g1': 'NOT_RUN',
           'g1_category': None, 'attribution': None, 'paired_exclusions': [], 'selected_tests': 0,
           'infrastructure': False}
    integrity = selection = None
    try:
        settings = load_v2_settings(Path(config))
        with ArchiveTree(task.source.archive_path) as tree:
            integrity, signal = integrity_signal(patch_text, tree)
            row['v1'] = signal.outcome.value
            if integrity.patch is not None:
                selection = replace(select_tests(integrity.patch, tree, settings.selection), runner=task.runner)
                row['selected_tests'] = len(selection.tests)
    except Exception as exc:  # noqa: BLE001
        row['exceptions'].append(exception_entry('V1', exc))
    applies = False
    if patch_text.strip():
        try:
            applies, _ = container_apply_check(task, patch_text, folder, EXPERIMENT)
            row['apply'] = 'PASS' if applies else 'FAIL'
            if not applies:
                row['v1'] = 'FAIL'  # does_not_apply: R1 REJECT; V2 and V3 are not run (B9)
        except Exception as exc:  # noqa: BLE001
            row['apply'] = 'UNAVAILABLE'
            row['exceptions'].append(exception_entry('V1 apply', exc))
    if applies and integrity is not None and integrity.patch is not None:
        try:
            v3 = run_v3(task, patch_text, integrity.patch, folder, experiment=EXPERIMENT)
            row['v3'] = v3.outcome.value
        except Exception as exc:  # noqa: BLE001
            row['v3'] = 'EXCEPTION'
            row['exceptions'].append(exception_entry('V3', exc))
            row['infrastructure'] |= classify(exc) != 'patch_does_not_apply'
    if applies and selection is not None and selection.tests:
        try:
            with paired_exception_scope(iid, task.source.pre_install.repo):
                selection, _, exclusions = g1_with_paired_exclusion(
                    task, patch_path, selection, folder, experiment=EXPERIMENT, drift=load_drift(),
                    stamps={'g1_receipt_sha256': {}})
            row.update(g1='READY', paired_exclusions=[e['module'] for e in exclusions])
        except RunHealthError as exc:
            row.update(g1_row(exc))
            row['infrastructure'] |= row['attribution'] == 'infrastructure'
        except Exception as exc:  # noqa: BLE001
            row['g1'] = 'EXCEPTION'
            row['exceptions'].append(exception_entry('V2 G1', exc))
            row['infrastructure'] |= classify(exc) != 'patch_does_not_apply'
    events = containers.START_EVENTS[starts_before:]
    row.update(start_successes=sum(events), start_failures=len(events) - sum(events),
               minutes=round((time.monotonic() - started) / 60, 2))
    (folder.parent / 'preflight.json').write_text(json.dumps(row, indent=2) + '\n')
    return row


def listed(row):
    return bool(row['exceptions'] or row['g1'] not in ('READY', 'NOT_RUN') or row['infrastructure']
                or row.get('apply') == 'FAIL')


def summarize(rows, machine):
    """Which rows to list, and whether the preflight passes (no run-stopping condition
    and no unclassified exception)."""
    stopping = [f'{when}: {reason}' for when, reason in zip(('before', 'after'), machine) if reason]
    streak = 0
    for row in rows:
        only_failed = row['start_failures'] and not row['start_successes']
        streak = streak + 1 if only_failed else 0
        if streak == CONSECUTIVE_START_FAILURES:
            stopping.append(f'{CONSECUTIVE_START_FAILURES} consecutive tasks with only container-start '
                            f'failures ending at {row["instance_id"]}')
    unclassified = [r['instance_id'] for r in rows if any(e['class'] == 'unclassified' for e in r['exceptions'])]
    return {'pass': not stopping and not unclassified, 'run_stopping': stopping, 'unclassified': unclassified,
            'listed': [r['instance_id'] for r in rows if listed(r)]}


def table(rows):
    lines = ['| task | V1 apply | V3 | V2 G1 | attribution | infrastructure | exceptions | min |',
             '|---|---|---|---|---|---|---|---:|']
    for r in rows:
        if listed(r):
            exc = '; '.join(f"{e['stage']} {e['type']} ({e['class']})" for e in r['exceptions']) or '-'
            g1 = r['g1'] + (f" ({r['g1_category']})" if r['g1_category'] else '')
            lines.append(f"| {r['instance_id']} | {r['apply']} | {r['v3']} | {g1} | {r['attribution'] or '-'} | "
                         f"{'yes' if r['infrastructure'] else 'no'} | {exc} | {r['minutes']} |")
    return '\n'.join(lines)


def main(argv=None):
    from run_e2e import frozen_inputs, manifest_ids
    from reliability.verifier.task_specs import ROOT

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--task-specs', type=Path, nargs='+', required=True)
    parser.add_argument('--verifier-config', type=Path, default=ROOT / 'configs/verifier/v1_5.yaml')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / 'runs').resolve()) or (output.exists() and any(output.iterdir())):
        raise SystemExit('--output must be a new or empty folder under runs/')
    output.mkdir(parents=True, exist_ok=True)
    ids = manifest_ids(args.manifest)
    supplied = frozen_inputs(args.inputs, ids)
    started = time.monotonic()
    before = machine_status(output)
    rows = []
    if before is None:
        jobs = [(iid, supplied[iid]['path'], [str(p.resolve()) for p in args.task_specs],
                 str(args.verifier_config.resolve()), str(output)) for iid in ids]
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            for row in pool.map(check_task, jobs):
                rows.append(row)
                print(json.dumps({'event': 'preflight_task', 'task': row['instance_id'],
                                  'listed': listed(row), 'minutes': row['minutes']}), flush=True)
    after = machine_status(output)
    summary = summarize(rows, (before, after))
    summary.update(tasks=len(rows), expected_tasks=len(ids), minutes=round((time.monotonic() - started) / 60, 1),
                   workers=args.workers)
    if len(rows) != len(ids):
        summary['pass'] = False
    (output / 'preflight_rows.json').write_text(json.dumps(rows, indent=2) + '\n')
    (output / 'preflight_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    (output / 'preflight_table.md').write_text(table(rows) + '\n')
    print(table(rows))
    print(json.dumps(summary))
    return 0 if summary['pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
