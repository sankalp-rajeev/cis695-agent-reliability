#!/usr/bin/env python3
"""Fresh serial Phase 4 V2 attempt. Dry run starts no containers.

Execution requires an explicit --execute and a new, already approved freeze
tag at clean HEAD. This script never tags, pushes, resumes, or sends messages.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import signal
import subprocess
import tarfile
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from reliability.verifier.accounting import ADMITTED_STATUSES
from reliability.verifier.admission_reference import JSONProjection
from reliability.verifier.container import ContainerTestExecutor, TaskContainer
from reliability.verifier.g1_reference import (PUBLISHED_HYGIENE_PATH, assert_reference_hygiene, clean_reference, native_collected_ids, read_collection, read_receipt)
from reliability.verifier.pre_install import load_specs
from reliability.verifier.regression import RegressionConfig, run_regression, run_to_dict
from reliability.verifier.run_health import (
    RunHealthError,
    append_health,
    covering_order,
    health_for_run,
    explicit_executor_failures,
)
from reliability.verifier.selection import Selection, TestRunner
from reliability.verifier.source_integrity import (
    BaseSourceSpec,
    SourceArchive,
    SourceIntegrityError,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FROZEN = Path('/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/paired_frozen')
PROVENANCE = ROOT/'reports/next_phases/phase4_rerun/fix10_provenance'
PREFLIGHT = ROOT/'reports/next_phases/phase4_rerun/fix10_integrity_preflight'
FROZEN_PROTOCOL_SHA256 = '2eaf8341274099cf4210674e6418a4b1e44ea2d0babb09a1c2243f77258c5153'
FROZEN_TASKS_SHA256 = '532df6e8eebd9afa91592ef39aa28f12d8b905fcf3987c7698e06c8ad02ac625'
TASK_COUNT = 83
PASS_BUDGET_S = 1800
STOP_S = 12*60*60
REFERENCE = ROOT/'reports/next_phases/phase4_rerun/fix13_reference'
DRIFT_REFERENCE_RELATIVE = 'reports/next_phases/phase4_rerun/fix16_reference'
DRIFT_REFERENCE = ROOT/DRIFT_REFERENCE_RELATIVE
G1_PREFLIGHT = ROOT/'reports/next_phases/phase4_rerun/fix18_g1'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2)+'\n')
    temporary.replace(path)


def confined(root, relative):
    path = (root/relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError('Missing or out-of-root frozen input: '+relative)
    return path


def require_hash(path, expected):
    if sha(path) != expected:
        raise ValueError('Frozen input SHA-256 mismatch: '+str(path))


@dataclass(frozen=True)
class TaskSpec:
    instance_id: str
    image_id: str
    patch_path: Path
    selection_path: Path
    tests: tuple[str, ...]
    runner: TestRunner
    source: BaseSourceSpec


def frozen_django_command_choice(instance_id):
    """Project command argv only; never decode outcomes, verdicts or labels."""
    manifest = json.loads((REFERENCE/'manifest.json').read_text())
    matches = [(Path(path), digest) for path, digest in manifest['input_sha256'].items()
               if Path(path).parts[-3:] == (instance_id, 'v2', 'result.json')]
    if len(matches) != 1:
        raise ValueError('Missing unique frozen Django command: ' + instance_id)
    path, digest = matches[0]
    require_hash(path, digest)
    calls = JSONProjection(path.read_text()).project(
        {'calls': {'*': {'run': {'events': {'*': {'argv': True}}}}}})['calls']
    commands = [event['argv'] for call in calls for event in call['run'].get('events', ())
                if 'argv' in event]
    choices = set()
    for argv in commands:
        if argv[:3] != ['python', 'tests/runtests.py', '--verbosity=2']:
            raise ValueError('Unexpected frozen Django command: ' + instance_id)
        parallel = [token for token in argv if token.startswith('--parallel')]
        enabled = '--parallel' in argv and argv[argv.index('--parallel')+1:argv.index('--parallel')+2] == ['1']
        if parallel and (parallel != ['--parallel'] or not enabled):
            raise ValueError('Unsupported frozen Django parallel choice: ' + instance_id)
        choices.add(enabled)
    if len(choices) != 1:
        raise ValueError('Missing or inconsistent frozen Django commands: ' + instance_id)
    return {'parallel_one': choices.pop(), 'source': str(path), 'source_sha256': digest}


def validate_inputs(frozen, archives, wheel, provenance, preflight):
    """Only frozen V2 artifacts, four-column metadata and source receipts."""
    require_hash(frozen/'protocol.json', FROZEN_PROTOCOL_SHA256)
    require_hash(frozen/'tasks.json', FROZEN_TASKS_SHA256)
    protocol = json.loads((frozen/'protocol.json').read_text())
    tasks = json.loads((frozen/'tasks.json').read_text())
    if len(tasks) != TASK_COUNT or len({t['instance_id'] for t in tasks}) != TASK_COUNT:
        raise ValueError('Wrong frozen cohort')
    metadata = json.loads((provenance/'provenance.json').read_text())
    require_hash(provenance/'dataset_projection.json', metadata['dataset_projection_sha256'])
    specs = load_specs(wheel, provenance/'dataset_projection.json')
    if set(specs) != {t['instance_id'] for t in tasks}:
        raise ValueError('Pre_install/frozen cohort mismatch')
    manifest = json.loads((preflight/'manifest.json').read_text())
    summary = json.loads((preflight/'summary.json').read_text())
    if summary['statuses'] != {'VERIFIED': TASK_COUNT} or summary['tasks_with_unresolved_mismatches']:
        raise ValueError('Pristine preflight did not verify every image')
    if manifest['frozen_tasks_sha256'] != FROZEN_TASKS_SHA256:
        raise ValueError('Pristine preflight used different tasks')
    for path, expected in manifest['source_sha256'].items():
        # Fix 10's byte-proof authority is unchanged. Collection/execution code
        # is sealed by the new exhaustive G1 preflight instead of the old audit.
        if path in ('src/reliability/verifier/source_integrity.py','src/reliability/verifier/pre_install.py','scripts/phase4_integrity_preflight.py'):
            require_hash(confined(ROOT, path), expected)
    for path, expected in manifest['receipt_sha256'].items():
        require_hash(confined(preflight, path), expected)
    if manifest['pre_install_provenance'] != {
        'wheel_sha256': metadata['wheel_sha256'],
        'dataset_projection_sha256': metadata['dataset_projection_sha256'],
    }:
        raise ValueError('Preflight/provenance mismatch')
    result = []
    for task in tasks:
        iid = task['instance_id']
        if '/' in iid or '\\' in iid or iid in ('.', '..'):
            raise ValueError('Unsafe instance ID')
        selection = confined(frozen, task['selections']['v2'])
        patch = confined(frozen, task['patch_path'])
        require_hash(selection, protocol['task_artifact_sha256'][task['selections']['v2']])
        require_hash(patch, task['patch_sha256'])
        require_hash(patch, protocol['task_artifact_sha256'][task['patch_path']])
        selected = json.loads(selection.read_text())
        if selected['arm'] != 'v2' or selected['instance_id'] != iid:
            raise ValueError('Wrong selection arm/task')
        tests = tuple(selected['tests'])
        if len(tests) != len(set(tests)) or not all(isinstance(t, str) for t in tests):
            raise ValueError('Invalid frozen selection list')
        proof = specs[iid]
        if proof.repo != task['repo'] or proof.base_commit != task['base_commit']:
            raise ValueError('Dataset/frozen source identity mismatch')
        source = BaseSourceSpec(task['base_commit'], archives/(iid+'.tar'), task['base_archive_sha256'], proof)
        SourceArchive(source)  # Verify the entire archive hash and safe source paths.
        with tarfile.open(source.archive_path) as archive:
            if archive.pax_headers.get('comment') != source.base_commit:
                raise ValueError('Archive commit differs from frozen base')
        image = task['image_binding']['host_image_id']
        if len(image) != 71 or not image.startswith('sha256:') or any(c not in '0123456789abcdef' for c in image[7:]):
            raise ValueError('Image must be an immutable SHA-256 ID')
        identity = json.loads((preflight/'tasks'/iid/'identity.json').read_text())
        if identity['image_id'] != image or identity['base_commit'] != source.base_commit or identity['archive_sha256'] != source.archive_sha256:
            raise ValueError('Pristine preflight identity mismatch')
        runner = TestRunner(**task['runner'])
        if runner.name == 'django':
            choice = frozen_django_command_choice(iid)
            runner = TestRunner(runner.name, runner.evidence, choice['parallel_one'])
        result.append(TaskSpec(iid, image, patch, selection, tests, runner, source))
    return covering_order(result)


def plan_for(specs):
    return {'mode': 'V2 only', 'tasks': len(specs), 'trees': ['base', 'patched'],
            'parallelism': 1, 'cpu_shares': 2048, 'network': 'none', 'pull': 'never',
            'per_pass_budget_s': PASS_BUDGET_S, 'stop_s': STOP_S,
            'confirmations': '3 isolated runs per tree for each new FAIL/REGRESSION_ERROR',
            'baseline_cache': None, 'resume': False, 'notifications': False,
            'fresh_pristine_receipt_required_before_runtime': True,
            'run_health_guards': ['G1','G2','G3','G4','G5','G6'],
            'task_order': [s.instance_id for s in specs],
            'task_specs': [{'instance_id': s.instance_id, 'image_id': s.image_id,
                'base_commit': s.source.base_commit, 'archive_sha256': s.source.archive_sha256,
                'archive_path': str(s.source.archive_path), 'selected_ids': len(s.tests),
                'selection_sha256': sha(s.selection_path), 'patch_sha256': sha(s.patch_path),
                'django_parallel_one': s.runner.django_parallel_one if s.runner.name == 'django' else None,
                'pre_install': s.source.pre_install.resolve()} for s in specs]}


class FrozenContainer(TaskContainer):
    def run_args(self):
        args = super().run_args()
        args.insert(2, '--pull=never')
        return args


class AttemptTimeLimit(BaseException):
    """Global stop; intentionally bypasses runner retry/error handling."""


def time_limit_handler(*_):
    raise AttemptTimeLimit('12 h attempt stop reached')


class Calls:
    """Capture both initial trees, then confirm once; policy replays do no I/O."""
    def __init__(self, executor, task=None, health_path=None, g1_reference=None):
        self.executor = executor
        self.task = task
        self.health_path = health_path
        self.g1_reference = g1_reference or {}
        self.calls = []

    def run(self, tests, *, patched, timeout_s):
        confirmation = len(self.calls) >= 2 and self.task is not None
        try:
            result = self.executor.run(tests, patched=patched, timeout_s=timeout_s)
        except Exception as exc:
            if not confirmation:
                raise
            record = {'task': self.task, 'scope': 'confirmation', 'halt': True,
                      'halt_reasons': ['confirmation stage error: '+repr(exc)],
                      'G2': 'BLOCKED_UPSTREAM', 'G3': 'BLOCKED_UPSTREAM'}
            append_health(self.health_path, record)
            raise RunHealthError(record) from exc
        failures = explicit_executor_failures(result)
        if failures:
            record = {'task': self.task, 'scope': 'confirmation' if confirmation else 'initial',
                      'tree': 'patched' if patched else 'base', 'halt': True,
                      'halt_reasons': failures, 'capture': run_to_dict(result, inline_raw=False)}
            append_health(self.health_path, record)
            raise RunHealthError(record)
        if confirmation:
            initial = self.calls[int(patched)][3]
            tree='patched' if patched else 'base'
            evidence=self.g1_reference.get(tree,{})
            g1_ids=evidence.get('g1_collected_ids',()) if isinstance(evidence,dict) else ()
            reference = confirmation_reference(initial, tests, g1_ids)
            record = health_for_run(self.task, 'patched' if patched else 'base', result, reference, confirmation=True)
            record['scope'] = 'confirmation'
            record['call'] = len(self.calls) + 1
            append_health(self.health_path, record)
            if record['halt']:
                raise RunHealthError(record)
        self.calls.append((tests, patched, timeout_s, result))
        return result


def confirmation_reference(initial, tests, g1_ids=()):
    receipts = {r['selected_id']: r for r in initial.validation}
    admitted = {r.test_id for r in initial.results if r.status in ADMITTED_STATUSES
                and (not receipts or (receipts.get(r.test_id, {}).get('admitted')
                     and not receipts.get(r.test_id, {}).get('collector_fallback')))}
    concrete = {r.test_id for r in initial.execution_results if r.status in ADMITTED_STATUSES
                and set(initial.execution_id_map.get(r.test_id, ())) & admitted}
    blocked = {r.test_id for r in (*initial.results, *initial.execution_results)
               if r.status.value in ('passed', 'failed', 'error', 'crash')}
    return {'admitted_ids': sorted((admitted | concrete) & set(tests)),
            'module_skip_blocked_ids': sorted(blocked & set(tests)),
            'drift_reference_ids': sorted(blocked & set(tests)),
            'g1_collected_ids': sorted(t for t in tests if t in g1_ids or set(initial.execution_id_map.get(t,())) & set(g1_ids)), 'reference_source': 'INITIAL_ADMITTED_SUBSET'}


class Replay:
    def __init__(self, calls, fallback=None):
        self.calls = iter(tuple(calls))
        self.fallback = fallback

    def run(self, tests, *, patched, timeout_s):
        entry = next(self.calls, None)
        if entry is None:
            if self.fallback is None:
                raise ValueError('Policy replay requested unrecorded execution')
            return self.fallback.run(tests, patched=patched, timeout_s=timeout_s)
        if entry[:3] != (tests, patched, timeout_s):
            raise ValueError('Policy replay request differs from captured execution')
        return entry[3]


def report_json(report):
    data = asdict(report)
    for field in ('baseline', 'patched'):
        run = getattr(report, field)
        data[field] = run_to_dict(run, inline_raw=False) if run is not None else None
    data['confirmations'] = [run_to_dict(r, inline_raw=False) for r in report.confirmations]
    return data


def run_task(spec, folder, experiment, reference=None, health_path=None):
    folder.mkdir(parents=True, exist_ok=False)
    with FrozenContainer(spec.instance_id, spec.patch_path.read_text(), image=spec.image_id,
                         experiment_id=experiment, source_spec=spec.source,
                         source_receipt_path=folder/'pristine_source_receipt.json') as container:
        if container.source_integrity.get('status') != 'VERIFIED':
            raise ValueError('A fresh VERIFIED pristine receipt is required')
        # Pin the generated-input inventory before any runtime stage. The
        # executor takes before/after hashes and carries changes across passes.
        write(folder/'pristine_generated_inputs.json', container.generated_snapshot())
        calls = Calls(ContainerTestExecutor(container, runner=spec.runner, evidence_dir=folder/'raw'),
                      spec.instance_id, health_path or folder/'health.jsonl', reference)
        # Both trees are captured even if scoring later abstains on a red base.
        for patched in (False, True):
            run = calls.run(spec.tests, patched=patched, timeout_s=PASS_BUDGET_S)
            write(folder/('patched.json' if patched else 'base.json'), run_to_dict(run, inline_raw=False))
        health = None
        if reference is not None:
            trees = [health_for_run(spec.instance_id, tree, calls.calls[i][3], reference[tree])
                     for i,tree in enumerate(('base','patched'))]
            reasons = [reason for tree in trees for reason in tree['halt_reasons']]
            health = {'task':spec.instance_id,'trees':trees,'halt':bool(reasons),'halt_reasons':reasons}
            if reasons:
                append_health(health_path,health)
                raise RunHealthError(health)
        selection = Selection(tests=spec.tests, runner=spec.runner)
        primary = run_regression(spec.instance_id, selection, Replay(calls.calls, fallback=calls),
                                 RegressionConfig(per_pass_timeout_s=PASS_BUDGET_S, rerun_flaky=True,
                                                  baseline_cache_dir=None))
        reports = {'C_invalid_excluded': report_json(primary)}
        for policy, skip, invalid_missing in [('C', True, True), ('S', False, False), ('S', False, True)]:
            report = run_regression(spec.instance_id, selection, Replay(calls.calls),
                RegressionConfig(per_pass_timeout_s=PASS_BUDGET_S, rerun_flaky=True,
                                 baseline_cache_dir=None, skip_compatible=skip,
                                 invalid_as_missing=invalid_missing))
            reports[policy+('_invalid_missing' if invalid_missing else '_invalid_excluded')] = report_json(report)
        write(folder/'result.json', {'instance_id': spec.instance_id, 'policies': reports,
                                    'native_passes': len(calls.calls), 'both_initial_trees_captured': True})
        if health is not None:
            health['confirmation_collector_statuses'] = [r.validation_summary.get('collector_status','NOT_REPORTED')
                                                        for _,_,_,r in calls.calls[2:]]
            append_health(health_path,health)
        return health


def require_frozen_head(tag):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()
    if not tag or tag in ('phase4-plan-frozen','phase4-plan-frozen-v2'):
        raise ValueError('Execution requires a new approved freeze tag')
    if git('cat-file', '-t', 'refs/tags/'+tag) != 'tag':
        raise ValueError('Freeze tag must be annotated')
    head = git('rev-parse', 'HEAD')
    if git('rev-parse', 'refs/tags/'+tag+'^{}') != head or git('status', '--porcelain'):
        raise ValueError('Execution requires clean worktree at the freeze tag')
    return head


def capture_manifest(output):
    write(output/'capture_manifest.json', {str(p.relative_to(output)): sha(p)
        for p in sorted(output.rglob('*')) if p.is_file() and p.name != 'capture_manifest.json'})


def execute(specs, output, tag, reference=None, *, g1_manifest_sha256=None):
    head = require_frozen_head(tag)
    if reference is None or set(reference) != {s.instance_id for s in specs}:
        raise ValueError('G2 requires an admission reference for every task')
    if not output.resolve().is_relative_to((ROOT/'runs').resolve()):
        raise ValueError('Raw captures must go in the ignored runs directory')
    output.mkdir(parents=True, exist_ok=False)  # No resume/restart into an existing attempt.
    started, completed = time.monotonic(), []
    current = None
    experiment = 'phase4_v2_'+output.name

    def event(kind, **values):
        with (output/'progress.jsonl').open('a') as stream:
            stream.write(json.dumps({'utc': datetime.now(UTC).isoformat(), 'elapsed_s': time.monotonic()-started,
                                     'event': kind, **values})+'\n')

    execution_plan=plan_for(specs)
    execution_plan['G1_manifest_sha256']=g1_manifest_sha256
    write(output/'plan.json', execution_plan)
    write(output/'attempt.json', {'executor_commit': head, 'freeze_tag': tag, 'status': 'RUNNING', 'G1_manifest_sha256':g1_manifest_sha256,
        'fresh_start_from_task': 1, 'started_utc': datetime.now(UTC).isoformat(),
        'attempt1_used': False, 'correctness_labels_read': False})
    previous_handler = signal.signal(signal.SIGALRM, time_limit_handler)
    signal.setitimer(signal.ITIMER_REAL, STOP_S)
    status, error, exit_code = 'COMPLETE', None, 0
    try:
        for index, spec in enumerate(specs, 1):
            current = spec.instance_id
            if time.monotonic()-started >= STOP_S:
                raise AttemptTimeLimit('12 h attempt stop reached')
            event('task_start', task=current, index=index, total=len(specs))
            try:
                run_task(spec, output/'tasks'/current, experiment,
                         reference[current] if reference is not None else None, output/'health.jsonl')
            except (SourceIntegrityError, RunHealthError):
                raise
            except Exception as exc:
                record={'task':current,'halt':True,'halt_reasons':['explicit task-stage error: '+repr(exc)],
                        'stage_status':'ERROR','G2':'NOT_EVALUATED','G3':'BLOCKED_UPSTREAM'}
                append_health(output/'health.jsonl',record)
                raise RunHealthError(record) from exc
            completed.append(current)
            event('task_complete', task=current, index=index, total=len(specs))
    except SourceIntegrityError as exc:
        status, exit_code = 'ABORTED_INTEGRITY', 2
        error = str(exc)
        write(output/'integrity_abort.json', {'task': current, 'receipt': exc.receipt,
            'status': 'aborted, not analyzed', 'rule': 'Label-free repair, new executor/version and freeze tag; fresh run from task 1; never move old tag.'})
        append_health(output/'health.jsonl',{'task':current,'halt':True,'stage_status':'SOURCE_INTEGRITY_ERROR',
            'halt_reasons':[str(exc)],'G2':'NOT_EVALUATED','G3':'BLOCKED_UPSTREAM'})
    except RunHealthError as exc:
        status,error,exit_code='ABORTED_HEALTH',str(exc),2
        write(output/'health_abort.json',exc.record)
    except AttemptTimeLimit as exc:
        status, error, exit_code = 'STOPPED_12H', str(exc), 3
    except KeyboardInterrupt:
        status, error, exit_code = 'ABORTED_INTERRUPT', 'Interrupted', 130
    except Exception as exc:  # noqa: BLE001
        status, error, exit_code = 'ABORTED_RUNNER', repr(exc), 1
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        event('attempt_end', status=status, completed_tasks=len(completed), error=error)
        write(output/'completion.json', {'status': status, 'completed_tasks': completed,
            'current_task': current, 'not_completed_tasks': [s.instance_id for s in specs if s.instance_id not in completed],
            'wall_s': time.monotonic()-started, 'error': error,
            'outcomes_analyzed': False, 'correctness_labels_read': False})
        capture_manifest(output)
    return exit_code


def load_reference(path=REFERENCE):
    manifest=json.loads((path/'manifest.json').read_text())
    if manifest.get('reference_schema') != 2:
        raise ValueError('G2 requires module-skip-aware original-run references')
    require_hash(path/'reference_ids.json.gz',manifest['reference_sha256'])
    for source,expected in manifest['source_sha256'].items():
        require_hash(confined(ROOT,source),expected)
    references=json.loads(gzip.decompress((path/'reference_ids.json.gz').read_bytes()))
    drift_manifest=json.loads((DRIFT_REFERENCE/'manifest.json').read_bytes())
    for source,expected in drift_manifest['source_sha256'].items():
        require_hash(confined(ROOT,source),expected)
    if drift_manifest['original_reference_sha256']!=manifest['reference_sha256']:
        raise ValueError('Drift/original reference provenance mismatch')
    raw=(DRIFT_REFERENCE/'drift_ids.json.gz').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=drift_manifest['data_sha256']:
        raise ValueError('Drift reference SHA-256 mismatch')
    drift=json.loads(gzip.decompress(raw))
    if set(drift)!=set(references):
        raise ValueError('Drift/original reference cohort mismatch')
    for task,trees in references.items():
        for tree,evidence in trees.items():
            if not set(drift[task][tree]) <= set(evidence['module_skip_blocked_ids']):
                raise ValueError('Drift identities exceed original strong reference')
            evidence['drift_reference_ids']=drift[task][tree]
    return references


def with_g1_references(reference, specs, path):
    """Fill empty original tree references from sealed G1 collection only."""
    require_g1(path)
    manifest,_=pinned_g1_manifest(path)
    result = {}
    exclusions=[]
    for spec in specs:
        result[spec.instance_id] = {}
        for tree in ('base', 'patched'):
            original = reference[spec.instance_id][tree]
            receipt = path/'tasks'/spec.instance_id/tree/'collection.json'
            collection = read_collection(receipt,root=path,manifest=manifest)
            evidence = clean_reference(original, collection,task=spec.instance_id,tree=tree)
            records = collection['records']
            if {r['selected_id'] for r in records} != set(spec.tests):
                raise ValueError('G1 collection/selection identity mismatch: '+spec.instance_id)
            evidence['g1_collected_ids'] = native_collected_ids(collection)
            evidence['g1_reference_required'] = True
            exclusions.extend(dict(instance_id=spec.instance_id,tree=tree,selected_id=t) for t in evidence['excluded_spurious_ids'])
            result[spec.instance_id][tree] = evidence
    assert_reference_hygiene(exclusions)
    return result


def committed_g1_manifest_sha():
    """Read the checksum from the freeze commit, never a mutable working copy."""
    relative='reports/next_phases/phase4_plan.md'
    try:
        plan=subprocess.check_output(['git','show','HEAD:'+relative],cwd=ROOT,text=True)
    except subprocess.CalledProcessError as exc:
        raise ValueError('Committed G1 manifest checksum is unavailable') from exc
    matches=re.findall(r'^Fix 18 G1 manifest SHA-256: ([0-9a-f]{64})$',plan,re.MULTILINE)
    if not matches:
        matches=re.findall(r'^Fix 17 G1 manifest SHA-256: ([0-9a-f]{64})$',plan,re.MULTILINE)
    if not matches:
        matches=re.findall(r'^Fix 16 G1 manifest SHA-256: ([0-9a-f]{64})$',plan,re.MULTILINE)
    if len(matches)!=1:
        raise ValueError('Committed Fix 17 G1 manifest checksum is unset or ambiguous')
    return matches[0]


def pinned_g1_manifest(path):
    pin=committed_g1_manifest_sha()
    raw=(path/'manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=pin:
        raise ValueError('SHA-256 mismatch: G1 manifest')
    return json.loads(raw),pin


def require_g1(path):
    manifest,pin=pinned_g1_manifest(path)
    required_sources={PUBLISHED_HYGIENE_PATH,DRIFT_REFERENCE_RELATIVE+'/manifest.json',DRIFT_REFERENCE_RELATIVE+'/drift_ids.json.gz'}
    if not required_sources <= manifest['source_sha256'].keys():
        raise ValueError('G1 manifest does not pin the published reference hygiene list')
    for source,expected in manifest['source_sha256'].items():
        require_hash(confined(ROOT,source),expected)
    summary=read_receipt(path,'summary.json',manifest)
    if (not summary['launch_allowed'] or summary['task_tree_count'] != TASK_COUNT*2
        or not summary.get('exhaustive') or not summary.get('gate_evaluated_after_all_pairs') or summary.get('projected_halts')):
        raise ValueError('G1 exhaustive stage preflight blocks launch')
    for name,expected in manifest['receipt_sha256'].items():
        require_hash(confined(path,name),expected)
    hygiene=read_receipt(path,'reference_hygiene.json',manifest)
    assert_reference_hygiene(hygiene['exclusions'])
    return pin


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--execute', action='store_true')
    parser.add_argument('--freeze-tag')
    parser.add_argument('--frozen', type=Path, default=DEFAULT_FROZEN)
    parser.add_argument('--archives', type=Path, default=Path('/home/sankalp/cg_repos/task_archives'))
    parser.add_argument('--wheel', type=Path, default=ROOT/'runs/phase4_fix10_provenance/swebench-4.0.4-py3-none-any.whl')
    parser.add_argument('--provenance', type=Path, default=PROVENANCE)
    parser.add_argument('--preflight', type=Path, default=PREFLIGHT)
    parser.add_argument('--health-preflight',type=Path,default=G1_PREFLIGHT)
    parser.add_argument('--admission-reference',type=Path,default=REFERENCE)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise ValueError('Output already exists; attempts are never resumed')
    if args.execute:
        require_frozen_head(args.freeze_tag)
        g1_sha=require_g1(args.health_preflight)
    specs = validate_inputs(args.frozen, args.archives, args.wheel, args.provenance, args.preflight)
    if args.dry_run:
        plan = plan_for(specs)
        plan.update(dry_run=True, containers_started=0, tests_executed=0, collection_performed=False,
                    new_tag_created=False, executor_commit=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip())
        write(args.output/'dry_run.json', plan)
        print(json.dumps({'dry_run': True, 'specs_validated': len(specs), 'containers_started': 0,
                          'output': str(args.output)}))
        return 0
    reference=with_g1_references(load_reference(args.admission_reference), specs, args.health_preflight)
    if set(reference) != {s.instance_id for s in specs}:
        raise ValueError('G2 reference/frozen cohort mismatch')
    return execute(specs, args.output, args.freeze_tag, reference, g1_manifest_sha256=g1_sha)


if __name__ == '__main__':
    raise SystemExit(main())
