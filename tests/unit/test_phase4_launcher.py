"""Launcher invariants using synthetic captures; no native containers."""

import importlib.util
import io
import json
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from reliability.verifier.regression import RunResult, TestResult, TestStatus
from reliability.verifier.selection import TestRunner
from reliability.verifier.source_integrity import BaseSourceSpec, SourceIntegrityError

MODULE = Path(__file__).resolve().parents[2]/'scripts/phase4_launch.py'
import sys

loader = importlib.util.spec_from_file_location('phase4_launch_tested', MODULE)
launch = importlib.util.module_from_spec(loader)
sys.modules[loader.name] = launch
loader.loader.exec_module(launch)


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    monkeypatch.setattr(launch, 'ROOT', tmp_path)
    monkeypatch.setattr(launch, 'TASK_COUNT', 2)
    frozen, archives, provenance, preflight = [tmp_path/p for p in ['frozen','archives','provenance','preflight']]
    for p in [frozen, archives, provenance, preflight]:
        p.mkdir()
    tasks, specs, artifacts, receipts = [], {}, {}, {}
    for n in range(2):
        iid, base = 'example__project-'+str(n), str(n+1)*40
        patch, selection = frozen/(iid+'.patch'), frozen/(iid+'.json')
        patch.write_text('candidate patch\n')
        launch.write(selection, {'arm':'v2','instance_id':iid,'tests':['test_module.py::test_case']})
        artifacts[patch.name], artifacts[selection.name] = launch.sha(patch), launch.sha(selection)
        archive = archives/(iid+'.tar')
        with tarfile.open(archive, 'w', format=tarfile.PAX_FORMAT, pax_headers={'comment':base}) as stream:
            data = b'def test_case(): pass\n'
            member = tarfile.TarInfo('testbed/test_module.py')
            member.size = len(data)
            stream.addfile(member, io.BytesIO(data))
        image = 'sha256:'+str(n)*64
        tasks.append({'instance_id':iid,'repo':'example/project','base_commit':base,
                      'selections':{'v2':selection.name},'patch_path':patch.name,
                      'patch_sha256':launch.sha(patch),'base_archive_sha256':launch.sha(archive),
                      'image_binding':{'host_image_id':image},'runner':{'name':'pytest','evidence':'frozen'}})
        specs[iid] = SimpleNamespace(repo='example/project', version='1', base_commit=base, resolve=lambda: {'commands': []})
        identity = preflight/'tasks'/iid/'identity.json'
        launch.write(identity, {'image_id':image,'base_commit':base,'archive_sha256':launch.sha(archive)})
        receipts[str(identity.relative_to(preflight))] = launch.sha(identity)
    launch.write(frozen/'tasks.json', tasks)
    launch.write(frozen/'protocol.json', {'task_artifact_sha256':artifacts})
    monkeypatch.setattr(launch,'FROZEN_TASKS_SHA256',launch.sha(frozen/'tasks.json'))
    monkeypatch.setattr(launch,'FROZEN_PROTOCOL_SHA256',launch.sha(frozen/'protocol.json'))
    launch.write(provenance/'dataset_projection.json',{'four':'columns'})
    projection_sha = launch.sha(provenance/'dataset_projection.json')
    launch.write(provenance/'provenance.json',{'dataset_projection_sha256':projection_sha,'wheel_sha256':'wheel-sha'})
    launch.write(preflight/'summary.json',{'statuses':{'VERIFIED':2},'tasks_with_unresolved_mismatches':[]})
    receipts['summary.json'] = launch.sha(preflight/'summary.json')
    launch.write(preflight/'manifest.json',{'frozen_tasks_sha256':launch.FROZEN_TASKS_SHA256,
        'source_sha256':{},'receipt_sha256':receipts,'pre_install_provenance':{
        'wheel_sha256':'wheel-sha','dataset_projection_sha256':projection_sha}})
    monkeypatch.setattr(launch,'load_specs',lambda *a: specs)
    return frozen, archives, tmp_path/'wheel', provenance, preflight


def test_dry_run_validates_every_spec_without_docker(inputs, tmp_path, monkeypatch):
    def forbidden(*a, **k):
        pytest.fail('Dry run attempted container execution')
    monkeypatch.setattr(launch.FrozenContainer,'start',forbidden)
    monkeypatch.setattr(launch,'execute',forbidden)
    monkeypatch.setattr(launch.subprocess,'check_output',lambda *a, **k: 'fixture-head\n')
    frozen, archives, wheel, provenance, preflight = inputs
    output = tmp_path/'dry'
    assert launch.main(['--dry-run','--output',str(output),'--frozen',str(frozen),
        '--archives',str(archives),'--wheel',str(wheel),'--provenance',str(provenance),
        '--preflight',str(preflight)]) == 0
    plan = json.loads((output/'dry_run.json').read_text())
    assert plan['tasks']==2 and plan['containers_started']==0
    assert plan['trees']==['base','patched'] and plan['parallelism']==1
    assert plan['per_pass_budget_s']==1800 and plan['cpu_shares']==2048
    assert plan['network']=='none' and not plan['notifications'] and not plan['resume']


@pytest.mark.parametrize('changed',['patch','selection','archive','provenance','receipt'])
def test_frozen_input_or_receipt_tampering_stops_validation(inputs, changed):
    frozen, archives, _, provenance, preflight = inputs
    path = {'patch':next(frozen.glob('*.patch')),'selection':frozen/'example__project-0.json',
            'archive':next(archives.glob('*.tar')),'provenance':provenance/'dataset_projection.json',
            'receipt':preflight/'tasks/example__project-0/identity.json'}[changed]
    with path.open('ab') as stream:
        stream.write(b'changed')
    with pytest.raises(ValueError,match='SHA-256 mismatch'):
        launch.validate_inputs(*inputs)


def task_spec(tmp_path):
    patch = tmp_path/'candidate.patch'
    patch.write_text('candidate\n')
    return launch.TaskSpec('task','sha256:'+'0'*64,patch,tmp_path/'selected',('test_module.py::test_case',),
                           TestRunner('pytest','fixture'),BaseSourceSpec('base',tmp_path/'base.tar','archive-sha'))


@pytest.mark.parametrize('base_status',[TestStatus.PASSED,TestStatus.FAILED])
def test_both_trees_and_single_confirmation_set_for_four_policies(tmp_path,monkeypatch,base_status):
    native_calls = []
    spec = task_spec(tmp_path)
    class Container:
        def __init__(self,*a,**kwargs):
            self.source_integrity={'status':'VERIFIED'}
            assert kwargs['source_spec'] is spec.source
            assert kwargs['source_receipt_path'].name=='pristine_source_receipt.json'
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def generated_snapshot(self): return {'files':{}}
    class Executor:
        def __init__(self,*a,**k): pass
        def run(self,tests,*,patched,timeout_s):
            native_calls.append((tests,patched,timeout_s))
            status = TestStatus.FAILED if patched else base_status
            return RunResult(results=tuple(TestResult(t,status) for t in tests),
                             requested_tests=tests,evidence_complete=True)
    monkeypatch.setattr(launch,'FrozenContainer',Container)
    monkeypatch.setattr(launch,'ContainerTestExecutor',Executor)
    folder=tmp_path/'task'
    launch.run_task(spec,folder,'experiment')
    data=json.loads((folder/'result.json').read_text())
    assert [call[1] for call in native_calls[:2]]==[False,True]
    assert all(call[2]==1800 for call in native_calls)
    assert len(data['policies'])==4
    # A red baseline abstains, but the patched tree was still captured. A new
    # failure has exactly six extra isolated calls, independent of 4 policies.
    assert len(native_calls)==(8 if base_status is TestStatus.PASSED else 2)
    if base_status is TestStatus.PASSED:
        assert sum(not c[1] for c in native_calls[2:])==3
        assert sum(c[1] for c in native_calls[2:])==3


def test_source_failure_aborts_attempt_and_never_runs_next_task(tmp_path,monkeypatch):
    monkeypatch.setattr(launch,'ROOT',tmp_path)
    monkeypatch.setattr(launch,'require_frozen_head',lambda tag:'new-executor')
    monkeypatch.setattr(launch,'plan_for',lambda specs:{'tasks':len(specs)})
    specs=[task_spec(tmp_path),task_spec(tmp_path)]
    calls=[]
    receipt={'status':'MISMATCH','mismatches':[{'path':'source.py','reason':'real_edit'}]}
    def fail(spec,*a):
        calls.append(spec.instance_id)
        raise SourceIntegrityError(receipt)
    monkeypatch.setattr(launch,'run_task',fail)
    output=tmp_path/'runs/attempt'
    assert launch.execute(specs,output,'new-freeze',{'task':{}})==2
    assert calls==['task']
    complete=json.loads((output/'completion.json').read_text())
    assert complete['status']=='ABORTED_INTEGRITY' and complete['completed_tasks']==[]
    assert json.loads((output/'integrity_abort.json').read_text())['receipt']==receipt
    assert (output/'capture_manifest.json').is_file()
    with pytest.raises(FileExistsError):
        launch.execute(specs,output,'new-freeze',{'task':{}})


def test_twelve_hour_stop_uses_same_cleanup_and_no_next_task(tmp_path,monkeypatch):
    monkeypatch.setattr(launch,'ROOT',tmp_path)
    monkeypatch.setattr(launch,'require_frozen_head',lambda tag:'executor')
    monkeypatch.setattr(launch,'plan_for',lambda specs:{})
    def timed_out(*a): launch.time_limit_handler()
    monkeypatch.setattr(launch,'run_task',timed_out)
    output=tmp_path/'runs/cap'
    assert launch.execute([task_spec(tmp_path)],output,'new-freeze',{'task':{}})==3
    assert json.loads((output/'completion.json').read_text())['status']=='STOPPED_12H'


def test_real_container_configuration_and_old_tag_barrier():
    container=launch.FrozenContainer('task','',image='sha256:'+'0'*64)
    args=container.run_args()
    assert '--pull=never' in args and args[args.index('--cpu-shares')+1]=='2048'
    assert args[args.index('--network')+1]=='none'
    with pytest.raises(ValueError,match='new approved'):
        launch.require_frozen_head('phase4-plan-frozen')


def test_runtime_refuses_unverified_pristine_receipt(tmp_path,monkeypatch):
    class Container:
        def __init__(self,*a,**k): self.source_integrity={'status':'MISMATCH'}
        def __enter__(self): return self
        def __exit__(self,*a): pass
    monkeypatch.setattr(launch,'FrozenContainer',Container)
    with pytest.raises(ValueError,match='fresh VERIFIED'):
        launch.run_task(task_spec(tmp_path),tmp_path/'task','experiment')
