"""Phase 3 part G (amendment B9): patch application in V1, infrastructure attribution,
A7 with prelisted stages, and machine-level run stops (7a)."""

import json
from types import SimpleNamespace

import pytest

from reliability import e2e_runner
from reliability.agent.freeze import freeze_patch
from reliability.verifier import container as C
from reliability.verifier.decision import Decision, SignalOutcome
from reliability.verifier.policy_v1_5 import FullPolicyV15, evidence_from_signals
from reliability.verifier.record import SignalAbsence, SignalKind, SignalRecord
from reliability.verifier.run_health import RunHealthError
from reliability.verifier.run_v1_4_1 import g1_attribution, paired_collection_exclusions, verify_task
from reliability.verifier.source_integrity import SourceIntegrityError
from tests.unit.test_e2e_runtime import PATCH, good, task  # noqa: F401  (fixture)


# -- containers ---------------------------------------------------------------

def recorder(calls, rc=0, stderr=''):
    def run(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=rc, stdout='', stderr=stderr)
    return run


def running(name='n'):
    container = C.TaskContainer('demo__repo-1', PATCH, image='img', name=name)
    container._started = True
    return container


# The part G single-command apply (`git apply --check -`) is superseded by amendment B12's
# grader sequence; see tests/unit/test_harness_apply.py.


def test_container_start_failure_is_typed_and_counted(monkeypatch):
    monkeypatch.setattr(C.subprocess, 'run', recorder([], rc=125, stderr='Cannot connect to the Docker daemon'))
    before = len(C.START_EVENTS)
    with pytest.raises(C.ContainerStartError):
        C.TaskContainer('demo__repo-1', PATCH, image='img').start()
    assert C.START_EVENTS[before:] == [False]


# -- V1 applies the patch the way the container does (step 1) -----------------

def verify(directory, task, *, applies=(True, ''), v2_error=None, v3_error=None, apply_error=None):
    called, seen = [], {}
    def v2(*args, **kwargs):
        called.append('V2')
        if v2_error:
            raise v2_error
        return good(SignalKind.REGRESSION)
    def v3(*args, **kwargs):
        called.append('V3')
        if v3_error:
            raise v3_error
        return good(SignalKind.STATIC)
    def v4(instance_id, patch_text, integrity):
        called.append('V4')
        seen['patch_applies'] = integrity.findings['patch_applies']
        return good(SignalKind.REPRODUCTION)
    def apply_check(task_spec, patch_text, folder, experiment):
        called.append('APPLY')
        if apply_error:
            raise apply_error
        return applies
    record = verify_task(directory, instance_id=task.instance_id, task_spec=task, experiment_id='unit',
                         v2_runner=v2, v3_runner=v3, v4_runner=v4, drift={}, apply_check=apply_check)
    return record, called, seen


def assert_does_not_apply(record, seen, kinds):
    assert record.integrity.outcome is SignalOutcome.FAIL
    assert 'does_not_apply' in record.integrity.findings['violations']
    assert record.integrity.findings['patch_applies'] is False
    for kind in kinds:
        signal = record.signals[kind]
        assert signal.outcome is SignalOutcome.NOT_AVAILABLE
        assert signal.findings['absence_reason'] == 'PATCH_DOES_NOT_APPLY'
        assert signal.findings['infrastructure'] is False
    assert seen['patch_applies'] is False
    assert record.decision.decision is Decision.REJECT


def test_patch_that_does_not_apply_fails_v1_and_skips_v2_v3(tmp_path, task):
    freeze_patch(tmp_path / 'patch.diff', PATCH)
    record, called, seen = verify(tmp_path, task, applies=(False, 'error: patch with only garbage at line 5'))
    assert called == ['APPLY', 'V4']
    assert record.integrity.findings['apply_check'] == 'FAIL'
    assert_does_not_apply(record, seen, (SignalKind.REGRESSION, SignalKind.STATIC))


def test_patch_that_applies_passes_v1_and_runs_everything(tmp_path, task):
    freeze_patch(tmp_path / 'patch.diff', PATCH)
    record, called, seen = verify(tmp_path, task)
    assert called == ['APPLY', 'V2', 'V3', 'V4']
    assert record.integrity.outcome is SignalOutcome.PASS
    assert record.integrity.findings['apply_check'] == 'PASS'
    assert seen['patch_applies'] is True


@pytest.mark.parametrize('stage', ['V2', 'V3'])
def test_container_apply_failure_in_v2_or_v3_is_v1_fail_not_an_executor_exception(tmp_path, task, stage):
    freeze_patch(tmp_path / 'patch.diff', PATCH)
    error = C.PatchApplyError('patch did not apply in container: error: corrupt patch')
    record, called, seen = verify(tmp_path, task, **{'v2_error' if stage == 'V2' else 'v3_error': error})
    assert 'V4' in called and (stage == 'V3' or 'V3' not in called)
    assert_does_not_apply(record, seen, (SignalKind.REGRESSION, SignalKind.STATIC) if stage == 'V2'
                          else (SignalKind.STATIC,))
    assert 'corrupt patch' in record.integrity.detail


def test_unavailable_apply_check_leaves_v1_to_its_other_checks(tmp_path, task):
    freeze_patch(tmp_path / 'patch.diff', PATCH)
    record, called, _ = verify(tmp_path, task, apply_error=C.ContainerStartError('could not start'))
    assert called == ['APPLY', 'V2', 'V3', 'V4']
    assert record.integrity.outcome is SignalOutcome.PASS
    assert record.integrity.findings['apply_check'] == 'UNAVAILABLE:ContainerStartError'


def test_apply_check_never_swallows_source_integrity_errors(tmp_path, task):
    freeze_patch(tmp_path / 'patch.diff', PATCH)
    with pytest.raises(SourceIntegrityError):
        verify(tmp_path, task, apply_error=SourceIntegrityError({'mismatches': []}))


# -- infrastructure attribution of run-health blocks (step 2) ----------------

TYPE_ERROR = ('Traceback (most recent call last):\n  File "x.py", line 1\n'
              "TypeError: register_lookup() missing 1 required positional argument: 'lookup_class'")
NO_TESTS = "Traceback (most recent call last):\n  File \"x.py\", line 1\nModuleNotFoundError: No module named 'tests'"
GIS = 'Traceback (most recent call last):\n  File "x.py", line 1\nSystemExit: 1'


def stage(module, status='COLLECTION_ERROR', message=TYPE_ERROR, **extra):
    return {'stage': 'native_collection', 'module': module, 'status': status, 'input_count': 3,
            'output_count': 0, 'messages': [message], 'allowed_exception': [], **extra}


def health(tree, *stages, status=None):
    return {'tree': tree, 'status': status or ('BLOCKED' if stages else 'READY'),
            'stages': list(stages), 'G3': {'halt': bool(stages)}}


def test_base_clean_and_patched_blocked_is_patch_caused():
    assert g1_attribution([health('base'), health('patched', stage('tests/a.py'))]) == 'patch'


def test_base_blocked_only_by_prelisted_guards_counts_as_clean():
    # django-14140: the GIS guard holds on base, but the patched tree fails everywhere,
    # so the generic rule loses its pair proof and is revoked on base.
    base = health('base', stage('tests/gis_tests/a.py', message=GIS, generic_rule_rejected='django_sqlite_gis_guard'),
                  stage('tests/gis_tests/b.py', message=GIS, allowed_exception=['GIS_GUARD']))
    patched = health('patched', stage('tests/gis_tests/a.py'), stage('tests/admin_checks/tests.py'))
    assert g1_attribution([base, patched]) == 'patch'


def test_patched_stage_budget_exhausted_with_clean_base_is_patch_caused():
    patched = health('patched', {'stage': 'runner_startup', 'status': 'NOT_REACHED', 'input_count': 1, 'output_count': 0})
    assert g1_attribution([health('base'), patched]) == 'patch'


def test_both_trees_blocked_is_an_environment_gap_not_infrastructure():
    blocked = lambda tree: health(tree, stage('tests/forms_tests/tests/test_forms.py', message=NO_TESTS))  # noqa: E731
    assert g1_attribution([blocked('base'), blocked('patched')]) == 'environment'


@pytest.mark.parametrize('broken', [
    {'stage': 'pair_error', 'status': 'ERROR', 'input_count': 1, 'output_count': 0,
     'message': "ContainerStartError('could not start img')"},
    stage('tests/a.py', message='OSError: [Errno 28] No space left on device'),
    stage('tests/a.py', message='docker: Cannot connect to the Docker daemon at unix:///var/run/docker.sock.'),
    stage('tests/a.py', message='Killed', collector_exit_codes=[137]),
], ids=['harness-exception', 'disk', 'docker', 'oom'])
@pytest.mark.parametrize('tree', ['base', 'patched'])
def test_machine_failures_are_infrastructure_on_either_tree(broken, tree):
    trees = {'base': health('base'), 'patched': health('patched')}
    trees[tree] = health(tree, broken)
    assert g1_attribution([trees['base'], trees['patched']]) == 'infrastructure'


@pytest.mark.parametrize('attribution,infrastructure', [
    ('patch', False), ('environment', False), ('infrastructure', True)])
def test_v2_absence_records_the_attribution(tmp_path, task, attribution, infrastructure):
    freeze_patch(tmp_path / 'patch.diff', PATCH)
    error = RunHealthError({'halt': True, 'halt_reasons': ['collection']})
    error.g1_category, error.attribution = 'module_import_failure', attribution
    record, _, _ = verify(tmp_path, task, v2_error=error)
    signal = record.regression
    assert signal.outcome is SignalOutcome.NOT_AVAILABLE and signal.absence is SignalAbsence.ERROR
    assert signal.findings['absence_reason'] == 'RUN_HEALTH_G1:module_import_failure'
    assert signal.findings['attribution'] == attribution
    assert signal.findings['infrastructure'] is infrastructure


def test_patch_caused_run_health_block_never_qualifies_for_r6(tmp_path, task):
    freeze_patch(tmp_path / 'patch.diff', PATCH)
    error = RunHealthError({'halt': True, 'halt_reasons': ['collection']})
    error.g1_category, error.attribution = 'module_import_failure', 'patch'
    record, _, _ = verify(tmp_path, task, v2_error=error)
    on = FullPolicyV15(r2_v3_reject=True, r3_extended_reject=True, r6_accept_v2_not_available=True,
                       r6b_accept_one_uncovered=True)
    result = on.decide(evidence_from_signals(record.signals))
    assert result.decision is not Decision.ACCEPT and result.rule_id not in ('R6', 'R6b')


def test_run_health_error_without_attribution_stays_infrastructure(tmp_path, task):
    freeze_patch(tmp_path / 'patch.diff', PATCH)
    record, _, _ = verify(tmp_path, task, v2_error=RunHealthError({'halt': True, 'halt_reasons': ['x']}))
    assert record.regression.findings['infrastructure'] is True


# -- A7 on the Django runner (step 3) -----------------------------------------

def test_paired_exclusion_ignores_prelisted_stages_that_do_not_block():
    # django-15103: test_forms.py fails to import on both trees; the GIS module is a
    # prelisted environment guard, allowed on both trees and never blocking.
    trees = [health(t, stage('tests/forms_tests/tests/test_forms.py', message=NO_TESTS),
                    stage('tests/gis_tests/test_geoforms.py', message=GIS, allowed_exception=['GIS_GUARD']))
             for t in ('base', 'patched')]
    assert paired_collection_exclusions(trees) == [
        {'module': 'tests/forms_tests/tests/test_forms.py', 'exception_type': 'ModuleNotFoundError'}]


def test_paired_exclusion_needs_a_blocking_module_besides_prelisted_ones():
    trees = [health(t, stage('tests/gis_tests/test_geoforms.py', message=GIS, allowed_exception=['GIS_GUARD']))
             for t in ('base', 'patched')]
    assert paired_collection_exclusions(trees) is None


# -- a task can never stop a run (7a) ------------------------------------------

def batch(tmp_path, monkeypatch, task, verification, *, count=4, machine=lambda: None):
    monkeypatch.setattr(e2e_runner, 'ROOT', tmp_path)
    ids = ['demo__repo-' + str(i) for i in range(count)]
    output = tmp_path / 'runs/batch'
    status = e2e_runner.run_batch(ids, output, {'skip_v4': False},
                                  lambda iid, d: freeze_patch(d / 'patch.diff', PATCH), verification,
                                  machine_check=machine)
    return status, json.loads((output / 'completion.json').read_text()), output, ids


def checked(task):
    def verification(iid, directory):
        def apply_check(*args):
            return True, ''
        return verify_task(directory, instance_id=iid, task_spec=task, experiment_id='unit',
                           v2_runner=lambda *a, **k: good(SignalKind.REGRESSION),
                           v3_runner=lambda *a, **k: good(SignalKind.STATIC),
                           v4_runner=lambda *a: good(SignalKind.REPRODUCTION), drift={}, apply_check=apply_check)
    return verification


def test_infrastructure_flags_on_every_task_never_stop_the_run(tmp_path, monkeypatch, task):
    def verification(iid, directory):
        def v2(*args, **kwargs):
            raise RunHealthError({'halt': True, 'halt_reasons': ['injected']})
        return verify_task(directory, instance_id=iid, task_spec=task, experiment_id='unit', v2_runner=v2,
                           v3_runner=lambda *a, **k: good(SignalKind.STATIC),
                           v4_runner=lambda *a: good(SignalKind.REPRODUCTION), drift={},
                           apply_check=lambda *a: (True, ''))
    status, completion, output, ids = batch(tmp_path, monkeypatch, task, verification)
    assert status == 'COMPLETE' and completion['completed_tasks'] == ids
    assert all(json.loads((output / 'tasks' / i / 'task_completion.json').read_text())['infrastructure'] for i in ids)


@pytest.mark.parametrize('error', [ValueError('selection unreadable'),
                                   SourceIntegrityError({'mismatches': [{'path': 'foo.py', 'reason': 'bytes'}]})],
                         ids=['exception', 'source-integrity'])
def test_a_task_exception_is_recorded_on_that_task_and_the_run_moves_on(tmp_path, monkeypatch, task, error):
    good_verification = checked(task)
    def verification(iid, directory):
        if iid == 'demo__repo-1':
            raise error
        return good_verification(iid, directory)
    status, completion, output, ids = batch(tmp_path, monkeypatch, task, verification)
    assert status == 'COMPLETE_WITH_TASK_ERRORS'
    assert completion['completed_tasks'] == [ids[0], ids[2], ids[3]]
    assert completion['task_errors'] == [ids[1]]
    receipt = json.loads((output / 'tasks' / ids[1] / 'task_error.json').read_text())
    assert receipt['error'].startswith(type(error).__name__)
    assert json.loads((output / 'tasks' / ids[1] / 'task_completion.json').read_text())['complete'] is False
    assert (output / 'seal.json').exists()


def test_machine_check_failure_stops_before_the_next_task(tmp_path, monkeypatch, task):
    answers = iter([None, None, 'docker daemon unreachable'])
    status, completion, _, ids = batch(tmp_path, monkeypatch, task, checked(task), machine=lambda: next(answers))
    assert status == 'STOPPED_MACHINE'
    assert completion['completed_tasks'] == ids[:2]
    assert completion['error'] == 'docker daemon unreachable'


def starts(*results):
    def verification(iid, directory, results=list(results)):
        C.START_EVENTS.extend(results.pop(0))
        return checked_task[0](iid, directory)
    return verification


checked_task = []


def test_three_consecutive_tasks_with_only_failed_container_starts_stop_the_run(tmp_path, monkeypatch, task):
    checked_task[:] = [checked(task)]
    status, completion, _, ids = batch(tmp_path, monkeypatch, task,
                                       starts([False], [False, False], [False], [True]), count=4)
    assert status == 'STOPPED_MACHINE'
    assert completion['completed_tasks'] == ids[:3]
    assert 'container-start' in completion['error']


def test_a_successful_start_resets_the_container_start_count(tmp_path, monkeypatch, task):
    checked_task[:] = [checked(task)]
    status, _, _, _ = batch(tmp_path, monkeypatch, task,
                            starts([False], [False], [False, True], [False], [False]), count=5)
    assert status == 'COMPLETE'


def test_machine_status_reports_low_disk(monkeypatch, tmp_path):
    monkeypatch.setattr(e2e_runner, '_docker_info', lambda: {'DockerRootDir': str(tmp_path)})
    monkeypatch.setattr(e2e_runner.shutil, 'disk_usage', lambda p: SimpleNamespace(free=19 * 10**9))
    assert 'disk' in e2e_runner.machine_status(tmp_path)
    monkeypatch.setattr(e2e_runner.shutil, 'disk_usage', lambda p: SimpleNamespace(free=21 * 10**9))
    assert e2e_runner.machine_status(tmp_path) is None


def test_machine_status_reports_unreachable_docker(monkeypatch, tmp_path):
    monkeypatch.setattr(e2e_runner, '_docker_info', lambda: None)
    assert e2e_runner.machine_status(tmp_path) == 'docker daemon unreachable'


def test_run_e2e_passes_the_machine_check():
    import inspect
    import scripts.run_e2e as run_e2e
    assert 'machine_check=lambda: machine_status(output)' in inspect.getsource(run_e2e.main)



@pytest.mark.parametrize('base_src,patched_src,attribution', [
    (None, 'MISSING', 'patch'), ('MISSING', None, 'environment'), ('MISSING', 'IMPORT_ERROR', 'environment')],
    ids=['patched-only', 'base-only', 'different-types'])
def test_run_v2_attributes_the_run_health_block(tmp_path, monkeypatch, base_src, patched_src, attribution):
    from tests.unit import test_v2_paired_collection as paired
    sources = {None: None, 'MISSING': paired.MISSING, 'IMPORT_ERROR': paired.IMPORT_ERROR}
    task, patch, _ = paired.runtime_with_broken(tmp_path, monkeypatch, sources[base_src], sources[patched_src])
    with pytest.raises(RunHealthError) as caught:
        paired.call(task, patch, tmp_path / 'verification', (paired.BROKEN, paired.HEALTHY))
    assert caught.value.attribution == attribution
