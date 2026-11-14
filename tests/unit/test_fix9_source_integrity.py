"""Source-only Git proofs and generated-input evidence; no task test execution."""

import ast
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from reliability.env import clean_env
from reliability.verifier.regression import (
    RegressionConfig,
    RunResult,
    Signal,
    TestResult,
    TestStatus,
    run_from_dict,
    run_regression,
    run_to_dict,
)
from reliability.verifier.selection import Selection
from reliability.verifier.source_integrity import (
    _GENERATED_PROBE,
    _SOURCE_PROBE,
    BaseSourceSpec,
    GeneratedInputAudit,
    SourceIntegrityError,
    generated_inventory,
    only_format_expansions,
    verify_base_source,
)


class LocalContainer:
    def __init__(self, root): self.root = root
    def exec_input(self, command, data, timeout_s=60):
        path = command.removeprefix('cat > ')
        Path(path).write_text(data)
        return 0, ''
    def exec(self, command, timeout_s=180):
        command = command.replace('python -c ', shlex.quote(sys.executable)+' -c ', 1)
        process = subprocess.run(command, shell=True, cwd=self.root, env=clean_env(),
                                 capture_output=True, text=True, timeout=timeout_s, check=False)
        return process.returncode, process.stdout + process.stderr


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root)


def spec_for(root, archive):
    return BaseSourceSpec(git(root, 'rev-parse', 'HEAD').decode().strip(), archive,
                          hashlib.sha256(archive.read_bytes()).hexdigest())


@pytest.fixture
def source_repo(tmp_path):
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'config', 'user.name', 'Source fixture')
    git(tmp_path, 'config', 'user.email', 'fixture@example.invalid')
    (tmp_path/'pkg').mkdir()
    (tmp_path/'.gitattributes').write_text('pkg/_version.py export-subst\n')
    (tmp_path/'pkg/_version.py').write_text('revision = "$Format:%H$"\nrefs = "$Format:%d$"\ndef stable(): return 7\n')
    (tmp_path/'plain.py').write_text('value = 9\n')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-qm', 'base')
    archive = tmp_path/'frozen.tar'
    archive.write_bytes(git(tmp_path, 'archive', '--format=tar', '--prefix=testbed/', 'HEAD'))
    return tmp_path, archive, LocalContainer(tmp_path)


def test_export_subst_proof_accepts_only_the_base_blob_and_exact_git_expansion(source_repo):
    root, archive, container = source_repo
    receipt = verify_base_source(container, spec_for(root, archive))
    assert receipt['status']=='VERIFIED'
    assert receipt['accepted_export_subst_differences']==['pkg/_version.py']
    assert receipt['export_subst_files']==['pkg/_version.py']
    assert receipt['tests_executed']==0 and not receipt['collection_performed']


@pytest.mark.parametrize('path,reason', [('pkg/_version.py','image_differs_from_base_blob'),
                                       ('plain.py','non_export_subst_source_mismatch')])
def test_real_source_edit_halts_even_for_export_subst(source_repo, path, reason):
    root, archive, container = source_repo
    (root/path).write_text((root/path).read_text()+'real_edit = True\n')
    with pytest.raises(SourceIntegrityError) as error:
        verify_base_source(container, spec_for(root, archive))
    mismatch = next(r for r in error.value.receipt['mismatches'] if r['path']==path)
    assert mismatch['reason']==reason
    assert mismatch['observed_b64'] and mismatch['archive_b64']


@pytest.mark.parametrize('attribute_location', ['worktree','info'])
def test_attributes_outside_base_commit_cannot_grant_export_exception(source_repo, attribute_location):
    root, archive, container = source_repo
    if attribute_location=='worktree':
        (root/'.gitattributes').write_text('*.py export-subst\n')
    else:
        (root/'.git/info/attributes').write_text('plain.py export-subst\n')
    (root/'plain.py').write_text('wrong = True\n')
    receipt = verify_base_source(container, spec_for(root, archive), halt=False)
    mismatch = next(r for r in receipt['mismatches'] if r['path']=='plain.py')
    assert not mismatch['export_subst']
    assert mismatch['reason']=='non_export_subst_source_mismatch'


def test_archive_real_edit_is_not_format_expansion(source_repo):
    import io
    import tarfile
    root, archive, container = source_repo
    with tarfile.open(archive) as tar:
        members = [(m.name, tar.extractfile(m).read()) for m in tar if m.isfile()]
    with tarfile.open(archive, 'w') as tar:
        for name, raw in members:
            if name.endswith('_version.py'): raw += b'danger = True\n'
            info=tarfile.TarInfo(name);info.size=len(raw);tar.addfile(info, io.BytesIO(raw))
    receipt=verify_base_source(container,spec_for(root,archive),halt=False)
    assert receipt['mismatches'][0]['reason']=='archive_differs_from_base_git_archive'


def test_no_non_placeholder_byte_can_be_ignored():
    assert only_format_expansions(b'x=$Format:%H$\nend',b'x=abc\nend')
    assert not only_format_expansions(b'x=$Format:%H$\nend',b'x=abc\nEDIT')
    assert not only_format_expansions(b'plain source',b'edited source')


def test_ignored_untracked_version_is_inventoried_and_tracked_version_is_not(source_repo):
    root, _, container = source_repo
    (root/'.gitignore').write_text('pkg/version.py\n')
    (root/'pkg/version.py').write_text('version="generated"\n')
    receipt=generated_inventory(container)
    assert set(receipt['files'])=={'pkg/version.py'}
    assert receipt['tests_executed']==0 and not receipt['collection_performed']


def test_generated_change_is_reported_without_halting_or_overriding_outcome(source_repo):
    root, _, container = source_repo
    target=root/'pkg/version.py';target.write_text('one')
    audit=GeneratedInputAudit(lambda old:generated_inventory(container,old))
    audit.capture('pass','before')
    value=audit.stage('native_collection', lambda:target.write_text('two'))
    assert value==3
    assert audit.flags==('GENERATED_INPUT_CHANGED',)
    assert audit.changes[0]['stage']=='native_collection'
    assert audit.changes[0]['before']!=audit.changes[0]['after']


@pytest.mark.parametrize('operation', ['create','delete'])
def test_generated_creation_and_deletion_are_changes(source_repo,operation):
    root, _, container=source_repo;target=root/'pkg/version.py'
    if operation=='delete':target.write_text('one')
    audit=GeneratedInputAudit(lambda old:generated_inventory(container,old));audit.capture('execution','before')
    if operation=='delete':target.unlink()
    else:target.write_text('new')
    audit.capture('execution','after')
    assert 'GENERATED_INPUT_CHANGED' in audit.flags
    assert (audit.changes[0]['after'] is None)==(operation=='delete')


def test_after_snapshot_is_taken_even_when_runtime_stage_raises():
    snapshots=[]
    audit=GeneratedInputAudit(lambda old:snapshots.append(old) or {'files':{'version.py':str(len(snapshots))}})
    with pytest.raises(RuntimeError):
        audit.stage('execution',lambda:(_ for _ in ()).throw(RuntimeError('runner')))
    assert len(snapshots)==2 and audit.flags==('GENERATED_INPUT_CHANGED',)


def test_generated_flags_round_trip_and_include_confirmation_evidence():
    tid='t.py::test_a'
    class Executor:
        def __init__(self):self.calls=0
        def run(self, tests, *, patched, timeout_s):
            self.calls+=1
            return RunResult(results=tuple(TestResult(t,TestStatus.FAILED if patched else TestStatus.PASSED) for t in tests),
                             requested_tests=tests,evidence_complete=True,
                             evidence_flags=('GENERATED_INPUT_CHANGED',) if self.calls==3 else (),
                             generated_inputs={'snapshots':[{'stage':'pass','boundary':'before'},{'stage':'pass','boundary':'after'}]})
    report=run_regression('task',Selection(tests=(tid,)),Executor(),RegressionConfig())
    assert report.signal is Signal.FAIL and report.evidence_flags==('GENERATED_INPUT_CHANGED',)
    assert report.confirmations[0].generated_inputs['runtime_kind']=='confirmation'
    assert run_from_dict(run_to_dict(report.confirmations[0]))==report.confirmations[0]


def test_standalone_probes_support_historical_python36():
    ast.parse(_SOURCE_PROBE,feature_version=(3,6));ast.parse(_GENERATED_PROBE,feature_version=(3,6))


def test_source_failure_removes_container_and_saves_receipt(tmp_path, monkeypatch):
    import reliability.verifier.container as module
    receipt={'status':'MISMATCH','mismatches':[{'path':'plain.py','reason':'non_export_subst_source_mismatch'}]}
    monkeypatch.setattr(module.subprocess,'run',lambda *a,**k:type('Proc',(),{'returncode':0})())
    def bad(*args):raise SourceIntegrityError(receipt)
    monkeypatch.setattr(module,'verify_base_source',bad)
    path=tmp_path/'source.json'
    container=module.TaskContainer('task','',source_spec=BaseSourceSpec('base',tmp_path/'x','sha'),source_receipt_path=path)
    with pytest.raises(SourceIntegrityError):container.start()
    assert not container._started and json.loads(path.read_text())==receipt


def test_runtime_audits_every_stage_and_confirmation_without_changing_status(tmp_path,monkeypatch):
    from reliability.verifier.collection import ValidationPass
    from reliability.verifier.container import ContainerTestExecutor
    from reliability.verifier.id_validation import IDValidation
    from reliability.verifier.source_integrity import runtime_stage_var
    tid='t.py::test_a';log=b't.py::test_a PASSED\n'
    events=[{'event':'start','batch':1,'offset':0},{'event':'end','batch':1,'offset':len(log),'returncode':0},{'event':'complete'}]
    class Container:
        value='build'
        def __init__(self): self.source_integrity={'status':'VERIFIED'}
        def generated_snapshot(self,previous,**kwargs):return {'files':{'pkg/_version.py':self.value}}
        def set_patched(self,value):self.value='patch'
        def exec_input(self,*args,**kwargs):return 0,''
        def exec_raw(self,command,timeout_s):
            if command.startswith('python /tmp/verifier_driver.py'):
                self.value='execution';return 0,log,b'',False
            if command=='cat /tmp/verifier_out.txt':return 0,log,b'',False
            if command=='cat /tmp/verifier_events.jsonl':return 0,'\n'.join(map(json.dumps,events)).encode(),b'',False
            return 0,b'',b'',False
    container=Container()
    def validate(*a,**k):
        container.value='collection';return ValidationPass((IDValidation(tid,'runnable_test',(tid,)),))
    monkeypatch.setattr('reliability.verifier.container.validate_in_container',validate)
    token=runtime_stage_var.set('confirmation')
    try:result=ContainerTestExecutor(container,evidence_dir=tmp_path).run((tid,),patched=True,timeout_s=1800)
    finally:runtime_stage_var.reset(token)
    assert result.results[0].status is TestStatus.PASSED
    assert result.evidence_flags==('GENERATED_INPUT_CHANGED',)
    changes=result.generated_inputs['changes']
    assert {r['stage'] for r in changes}=={'patch_application','native_collection','execution'}
    snapshots=result.generated_inputs['snapshots']
    for stage in ('confirmation','patch_application','native_collection','execution'):
        assert {r['boundary'] for r in snapshots if r['stage']==stage}=={'before','after'}
    assert json.loads(Path(result.evidence_files['generated_inputs.json']).read_text())==result.generated_inputs


def test_generated_stage_receipt_survives_unrelated_runtime_exception(tmp_path):
    from reliability.verifier.container import ContainerTestExecutor
    class Container:
        value='before'
        def generated_snapshot(self,previous,**kwargs):return {'files':{'version.py':self.value}}
        def set_patched(self,value):
            self.value='after';raise RuntimeError('patch failed')
    with pytest.raises(RuntimeError,match='patch failed'):
        ContainerTestExecutor(Container(),evidence_dir=tmp_path).run(('t.py::test_a',),patched=True,timeout_s=1800)
    path=next(tmp_path.rglob('generated_inputs.json'))
    assert json.loads(path.read_text())['flags']==['GENERATED_INPUT_CHANGED']


def test_exported_image_copy_is_rejected_even_if_it_matches_the_archive(source_repo):
    import tarfile
    root,archive,container=source_repo
    with tarfile.open(archive) as tar:
        raw=tar.extractfile('testbed/pkg/_version.py').read()
    (root/'pkg/_version.py').write_bytes(raw)
    with pytest.raises(SourceIntegrityError,match='image_differs_from_base_blob'):
        verify_base_source(container,spec_for(root,archive))


@pytest.mark.parametrize('compatible',[True,False])
def test_generated_flag_alone_never_changes_a_healthy_policy_verdict(compatible):
    tid='t.py::test_a'
    class Executor:
        def run(self,tests,**kwargs):
            return RunResult(results=(TestResult(tid,TestStatus.PASSED),),requested_tests=tests,
                             evidence_complete=True,evidence_flags=('GENERATED_INPUT_CHANGED',))
    report=run_regression('task',Selection(tests=(tid,)),Executor(),RegressionConfig(skip_compatible=compatible))
    assert report.signal is Signal.PASS
    assert report.evidence_flags==('GENERATED_INPUT_CHANGED',)


def test_old_git_describe_placeholder_uses_equivalent_read_only_command(source_repo):
    import base64

    from reliability.verifier.source_integrity import _SOURCE_PROBE
    root,archive,container=source_repo
    # Commit a real tag and a describe placeholder, then simulate the old
    # pretty formatter returning the literal expression. Git describe itself
    # is unchanged and supplies the verified expansion.
    (root/'pkg/_version.py').write_text('description = "$Format:%(describe:tags=true)$"\n')
    git(root,'add','pkg/_version.py');git(root,'commit','-qm','describe source')
    git(root,'tag','v1.0')
    archive.write_bytes(git(root,'archive','--format=tar','--prefix=testbed/','HEAD'))
    old = "value = git(['show', '-s', '--format=format:' + fmt.decode(), base], environment)"
    simulated = _SOURCE_PROBE.replace(old, "value = fmt if fmt.startswith(b'%(describe') else git(['show', '-s', '--format=format:' + fmt.decode(), base], environment)")
    container.exec_input('cat > /tmp/verifier_source_request.json',json.dumps({'base_commit':spec_for(root,archive).base_commit,'files':{}}))
    code,raw=container.exec('python -c '+shlex.quote(simulated));assert code==0,raw
    probe=json.loads(raw);record=probe['records']['pkg/_version.py']
    assert record['describe_fallback_proofs'][0]['command'][:2]==['describe','--tags']
    assert base64.b64decode(record['git_archive_b64'])==b'description = "v1.0"\n'


def test_describe_default_abbreviation_is_a_query_not_arbitrary_metadata_acceptance():
    import base64

    from reliability.verifier.source_integrity import describe_abbreviation_queries
    commit='a'*40
    blob=b'describe: $Format:%(describe:tags=true)$\n'
    row={'base_blob_b64':base64.b64encode(blob).decode(),
         'git_archive_b64':base64.b64encode(b'describe: v1-3-gaaaaaaaaaa\n').decode(),
         'describe_fallback_proofs':[{'format':'%(describe:tags=true)'}]}
    probe={'base_commit':commit,'records':{'version.py':row}}
    assert describe_abbreviation_queries({'version.py':b'describe: v1-3-gaaaaaaaaa\n'},probe)=={'version.py':{'%(describe:tags=true)':9}}
    assert describe_abbreviation_queries({'version.py':b'describe: v1-3-gbbbbbbbbb\n'},probe)=={}
    assert describe_abbreviation_queries({'version.py':b'EDIT: v1-3-gaaaaaaaaa\n'},probe)=={}
