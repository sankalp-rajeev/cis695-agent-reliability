"""Counts-only smoke through phase4_launch.run_task; stop before policy scoring.

Run after committing the new G1 pin. Raw captures stay in the ignored run tree.
No launcher main/execute path, confirmations, labels, or verdicts are used.
"""

import collections
import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts'))
import phase4_launch as launch
from reliability.verifier.g1_reference import native_collected_ids, read_collection
from reliability.verifier.regression import TestStatus

REPORT = Path(__file__).resolve().parent
RAW = ROOT / 'runs/phase4_fix18b_identity_smoke'
NON_RUN = (TestStatus.COLLECTION_ERROR, TestStatus.SKIPPED, TestStatus.TIMEOUT,
           TestStatus.NOT_REACHED, TestStatus.INVALID_ID, TestStatus.NOT_RUN,
           TestStatus.RUNNER_UNAVAILABLE)
UNEXPLAINED = (TestStatus.INVALID_ID, TestStatus.NOT_RUN, TestStatus.RUNNER_UNAVAILABLE)


class IdentityBoundary(BaseException):
    """Exit the real per-task path before scoring or a base-only patched pass."""


def main():
    if RAW.exists():
        raise ValueError('Use a fresh raw smoke directory')
    RAW.mkdir()
    head = launch.subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    pin = launch.require_g1(launch.G1_PREFLIGHT)
    manifest = json.loads((launch.G1_PREFLIGHT / 'manifest.json').read_bytes())
    specs = launch.validate_inputs(launch.DEFAULT_FROZEN, Path('/home/sankalp/cg_repos/task_archives'),
        ROOT / 'runs/phase4_fix10_provenance/swebench-4.0.4-py3-none-any.whl',
        launch.PROVENANCE, launch.PREFLIGHT)
    reference = launch.with_g1_references(launch.load_reference(), specs, launch.G1_PREFLIGHT)
    sympy = [s for s in specs if s.runner.name == 'sympy']
    first = next(s for s in sympy if s.instance_id == 'sympy__sympy-13480')
    assert specs[0].runner.name == 'pytest'
    django = next(s for s in specs if s.runner.name == 'django')
    previous = json.loads((ROOT / 'reports/next_phases/phase4_rerun/fix18_validation/base_smoke.json').read_text())
    expected = {r['task']: r for r in previous['rows']}
    assert set(expected) == {s.instance_id for s in sympy}
    # The base pass of the paired 13480 check also belongs to the five-base check.
    scope = [(first, False)] + [(s, True) for s in sympy if s != first]
    scope += [(specs[0], False), (django, False)]
    rows = []
    all_clean = True
    count_matches = True
    actual_calls = launch.Calls.run

    for spec, base_only in scope:
        folder = RAW / 'tasks' / spec.instance_id
        captured = {}
        executor_ids = set()
        started = time.monotonic()
        print(json.dumps({'event': 'smoke_start', 'task': spec.instance_id,
                          'trees': ['base'] if base_only else ['base', 'patched']}), flush=True)

        def capture_call(calls, tests, *, patched, timeout_s):
            if base_only and patched:
                raise IdentityBoundary()
            executor_ids.add(id(calls.executor))
            result = actual_calls(calls, tests, patched=patched, timeout_s=timeout_s)
            captured['patched' if patched else 'base'] = result
            print(json.dumps({'event': 'tree_captured', 'task': spec.instance_id,
                              'tree': 'patched' if patched else 'base'}), flush=True)
            return result

        def before_scoring(*args, **kwargs):
            raise IdentityBoundary()

        task_error = None
        try:
            with patch.object(launch.Calls, 'run', capture_call), patch.object(launch, 'run_regression', before_scoring):
                launch.run_task(spec, folder, 'phase4_fix18b_identity_smoke',
                                reference=reference[spec.instance_id], health_path=folder / 'health.jsonl')
        except IdentityBoundary:
            pass
        except Exception as exc:
            task_error = type(exc).__name__

        for tree in (('base',) if base_only else ('base', 'patched')):
            if tree not in captured:
                row = {'task': spec.instance_id, 'tree': tree, 'health_trip': True,
                       'identity_check_clean': False, 'stage_exception': task_error or 'MissingCapture'}
                rows.append(row)
                all_clean = False
                print(json.dumps({'event': 'smoke_end', **row}), flush=True)
                continue
            run = captured[tree]
            collection = read_collection(launch.G1_PREFLIGHT / 'tasks' / spec.instance_id / tree / 'collection.json',
                                         root=launch.G1_PREFLIGHT, manifest=manifest)
            native = set(native_collected_ids(collection))
            counts = collections.Counter(r.test_id for r in run.results)
            non_run = collections.Counter(r.status.value for r in run.results
                                          if r.test_id in native and r.status in NON_RUN)
            unexplained = sum(r.test_id in native and r.status in UNEXPLAINED for r in run.results)
            health = launch.health_for_run(spec.instance_id, tree, run, reference[spec.instance_id][tree])
            missing = len(native - counts.keys())
            duplicates = sum(counts[t] > 1 for t in native)
            signatures = sorted({stage['import_signature'] for stage in run.stage_health if stage.get('import_signature')})
            stderr_keys = sum('stderr_b64' in event for event in run.events)
            row = {'task': spec.instance_id, 'tree': tree, 'runner': spec.runner.name,
                   'selected_ids': len(spec.tests), 'G1_collected_ids': len(native),
                   'recorded_once': sum(counts[t] == 1 for t in native),
                   'missing_ids_count': missing, 'duplicate_ids_count': duplicates,
                   'non_run_category_counts': dict(non_run), 'unexplained_non_run_count': unexplained,
                   'module_import_signatures': signatures, 'health_trip': health['halt'],
                   'health_reasons': health['halt_reasons'], 'cap_hit': run.timed_out,
                   'evidence_complete': run.evidence_complete,
                   'same_executor_across_trees': len(executor_ids) == 1,
                   'stderr_b64_event_count': stderr_keys, 'elapsed_task_s': time.monotonic() - started}
            row['identity_check_clean'] = (not health['halt'] and missing == duplicates == unexplained == 0
                and row['recorded_once'] == len(native) and len(executor_ids) == 1
                and (spec.runner.name == 'sympy' or stderr_keys == 0))
            if spec.runner.name == 'sympy' and tree == 'base':
                old = expected[spec.instance_id]
                row['matches_Fix18_base_counts'] = (len(native) == old['G1_collected_ids']
                    and row['recorded_once'] == old['recorded_once']
                    and dict(non_run) == old['allowed_non_run_counts'])
                count_matches &= row['matches_Fix18_base_counts']
            if spec == first:
                row['matches_13480_expectation'] = (len(native) == row['recorded_once'] == 763
                    and non_run['collection_error'] == 16 and bool(signatures) and not health['halt'])
                count_matches &= row['matches_13480_expectation']
            rows.append(row)
            all_clean &= row['identity_check_clean']
            print(json.dumps({'event': 'smoke_end', **row}), flush=True)
        launch.write(REPORT / 'identity_smoke_partial.json', {'rows': rows, 'complete': False})
        if not all_clean:
            break

    for source, digest in manifest['source_sha256'].items():
        launch.require_hash(ROOT / source, digest)
    expected_trees = sum(1 if base_only else 2 for _, base_only in scope)
    summary = {'rows': rows, 'complete': len(rows) == expected_trees,
               'expected_trees': expected_trees, 'identity_checks_clean': all_clean,
               'expected_counts_match': count_matches, 'G1_manifest_sha256': pin,
               'validated_HEAD': head, 'source_sha256': manifest['source_sha256'],
               'launcher_path': 'run_task -> Calls.run -> ContainerTestExecutor.run',
               'scoring_boundary': 'run_regression replaced by immediate IdentityBoundary; no scoring/confirmations',
               'base_only_boundary': 'IdentityBoundary immediately before patched Calls.run',
               'five_base_tasks': [s.instance_id for s in sympy],
               'task_1': specs[0].instance_id, 'first_django_task': django.instance_id,
               'correctness_labels_read': False, 'oracle_data_read': False,
               'benchmark_test_outcomes_decoded_for_analysis': False,
               'benchmark_outcome_tokens_masked': True, 'experiment_launched': False,
               'new_freeze_tag_created': False}
    launch.write(REPORT / 'identity_smoke.json', summary)
    launch.write(RAW / 'summary.json', summary)
    launch.capture_manifest(RAW)
    launch.write(REPORT / 'identity_smoke_capture_manifest.json',
                 {'root': str(RAW.relative_to(ROOT)),
                  'manifest_sha256': launch.sha(RAW / 'capture_manifest.json'),
                  'file_sha256': json.loads((RAW / 'capture_manifest.json').read_bytes()),
                  'outcome_fields_decoded': False})
    if summary['complete']:
        (REPORT / 'identity_smoke_partial.json').unlink()
    print(json.dumps({'event': 'smoke_complete', 'trees': len(rows),
                      'identity_checks_clean': all_clean, 'expected_counts_match': count_matches}), flush=True)
    return 0 if summary['complete'] and all_clean and count_matches else 1


if __name__ == '__main__':
    raise SystemExit(main())
