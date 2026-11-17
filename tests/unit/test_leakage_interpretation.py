"""Invented tier fixtures only. No real oracle content, names or run folders."""
import hashlib
import importlib.util
import io
import json
import runpy
import tarfile
from pathlib import Path

import pytest

from reliability.benchmark.leakage import OracleProbes
from reliability.benchmark.leakage_interpretation import (
    InterpretationInputs,
    cache_observation,
    classify_facts,
    complete_records,
    interpret_record,
)
from reliability.benchmark.rerun_leakage import audit_arm
from reliability.verifier.source_integrity import BaseSourceSpec, SourceArchive

LINE='invented_result = invented_operation_with_fixture()'
IID='invented__fixture-1'
BASE='a'*40
FUTURE='b'*40


def bash(command,call_id='one'):
    return {'role':'assistant','tool_calls':[{'id':call_id,'function':{'name':'bash',
            'arguments':json.dumps({'command':command})}}]}


def tool(output,code=0,call_id='one'):
    return {'role':'tool','tool_call_id':call_id,
            'content':f'<returncode>{code}</returncode><output>{output}</output>'}


def archive(tmp_path,text='base_value = 17\n'):
    path=tmp_path/'base.tar'
    with tarfile.open(path,'w') as tar:
        raw=text.encode(); member=tarfile.TarInfo('testbed/pkg.py'); member.size=len(raw)
        tar.addfile(member,io.BytesIO(raw))
    pin={'instance_id':IID,'base_commit':BASE,'path':str(path),
         'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'pin_origin':'synthetic'}
    return SourceArchive(BaseSourceSpec(BASE,path,pin['sha256'])),pin


def inputs(tmp_path,text='base_value = 17\n',probes=None):
    source,pin=archive(tmp_path,text)
    image={'instance_id':IID,'base_commit':BASE,'base_version':'1.0',
           'checks':{'git':{'status':'complete','result':{
               'base_timestamp':10,'commit_timestamps':{FUTURE:20},'future_object_count':1,
               'future_commit_hashes':[FUTURE], 'gold_post_image_blobs':[],
               'future_commit_details':[{'changed_file_count':0,'content_changed_files':0,
                   'changed_source_file_count':0,'gold_added_line_match_count':0,
                   'changed_file_categories':{}}]}}}}
    return InterpretationInputs(probes or OracleProbes(IID,patch_lines=(LINE,)),source,pin,image,True)


def record(tmp_path,messages,role='repair',findings=None):
    task=tmp_path/'task'; task.mkdir(exist_ok=True)
    name='trajectory.jsonl' if role=='repair' else 'generation_trajectory.jsonl'
    (task/name).write_text(''.join(json.dumps(m)+'\n' for m in messages))
    return {'instance_id':IID,'run':'synthetic','role':role,'source':str(task),
            'findings':findings or []}


@pytest.mark.parametrize('first,expected',[('tool','T4'),('model','T3')])
def test_tool_first_versus_model_first(tmp_path,first,expected):
    messages=[bash('cat answer_source'),tool(LINE),{'role':'assistant','content':LINE}]
    if first=='model':
        messages=[{'role':'assistant','reasoning_content':LINE},*messages]
    result=interpret_record(record(tmp_path,messages),inputs(tmp_path))
    assert result['tier']==expected
    fact=next(f for f in result['facts'] if f['category']=='answer')
    assert fact['first_seen_in']==('tool_output' if first=='tool' else 'model_output')
    serialized=json.dumps(result)
    assert LINE not in serialized


def test_agent_write_then_echo_is_model_first(tmp_path):
    result=interpret_record(record(tmp_path,[bash('cat > own.py <<EOF\n'+LINE+'\nEOF'),tool(LINE)]),inputs(tmp_path))
    assert result['tier']=='T3'


@pytest.mark.parametrize('short,repeat',[(True,0),(False,3)])
def test_distinctiveness_guard_blocks_t3_and_t4(tmp_path,short,repeat):
    line='tiny_fixture()' if short else LINE
    data=inputs(tmp_path,text=(line+'\n')*repeat,probes=OracleProbes(IID,patch_lines=(line,)))
    result=interpret_record(record(tmp_path,[bash('cat answer_source'),tool(line)]),data)
    assert result['tier']=='T0'
    fact=next(f for f in result['facts'] if f['category']=='answer')
    assert not fact['guard_pass']
    assert fact['base_occurrences']==repeat


def test_setup_commit_only_history_is_t1(tmp_path):
    command='git log --all'
    finding={'severity':'benchmark-awareness','kind':'git-history-search','rule':'history-git-log',
             'path':'unused','line_no':1,'evidence':{'command_sha256':hashlib.sha256(command.encode()).hexdigest()}}
    result=interpret_record(record(tmp_path,[bash(command),tool('commit '+FUTURE)],findings=[finding]),inputs(tmp_path))
    assert result['tier']=='T1'
    assert result['reasons']==['harmless-setup-history']


def test_failed_history_attempt_is_t2(tmp_path):
    command='git fsck --unreachable'
    finding={'severity':'benchmark-awareness','kind':'git-history-search','rule':'history-git-fsck',
             'path':'unused','line_no':1,'evidence':{'command_sha256':hashlib.sha256(command.encode()).hexdigest()}}
    result=interpret_record(record(tmp_path,[bash(command),tool('blocked',1)],findings=[finding]),inputs(tmp_path))
    assert result['tier']=='T2'


@pytest.mark.parametrize('output,code,rule',[
    ('[]',0,'masked-read-empty'), ('FILES []',0,'masked-read-empty'),
    ('No such file or directory',1,'masked-read-failed'),
    ('total 0',0,'masked-read-empty'),
    ('/root/.cache/pip/invented.whl',0,'masked-read-listed-files'),
])
def test_cache_payload_is_not_inferred_from_stdout(output,code,rule):
    result=cache_observation('find /root/.cache/pip',output,code,'/root/.cache/pip')
    assert result['rule']==rule
    assert result['nonempty_cache']==(rule=='masked-read-listed-files')
    tier,_=classify_facts([dict(result,category='cache')])
    assert tier=='T2'


def test_cache_content_without_answer_does_not_establish_t4():
    result=cache_observation('cat /root/.cache/pip/invented.py','ordinary fixture source',0,'/root/.cache/pip')
    assert result['nonempty_cache']
    assert classify_facts([dict(result,category='cache')])[0]=='T2'


def test_empty_masked_read_raw_confirmation_is_preserved_as_t2(tmp_path):
    # Legacy stdout-based rule mistakes a printed empty list plus a counter for
    # content. The interpretive rule must still require returned answer content.
    command="python -c \"print('/root/.cache/pip', []); print('FILES', 0)\""
    # Exercise empty cache interpretation directly; raw records are never edited.
    raw={'severity':'confirmed','kind':'newer-copy-path','rule':'legacy'}
    before=json.dumps(raw)
    fact=cache_observation(command,'/root/.cache/pip []\nFILES 0',0,'/root/.cache/pip')
    assert fact['rule']=='masked-read-empty'
    assert json.dumps(raw)==before
    assert classify_facts([dict(fact,category='cache')])[0]=='T2'


def test_hidden_names_model_first_and_tool_first(tmp_path):
    symbol='test_invented_hidden_fixture'
    data=inputs(tmp_path,probes=OracleProbes(IID,fail_to_pass=(symbol,)))
    result=interpret_record(record(tmp_path,[{'role':'assistant','content':symbol},bash('cat source'),tool(symbol)]),data)
    assert result['tier']=='T3'
    result=interpret_record(record(tmp_path,[bash('cat source'),tool(symbol),{'role':'assistant','content':symbol}]),data)
    assert result['tier']=='T4'
    assert symbol not in json.dumps(result)


def test_hidden_name_introduced_by_successful_write_is_not_memory(tmp_path):
    symbol='test_invented_written_fixture'
    data=inputs(tmp_path,probes=OracleProbes(IID,fail_to_pass=(symbol,)))
    result=interpret_record(record(tmp_path,[bash('cat > own.py <<EOF\ndef '+symbol+'(): pass\nEOF'),tool(symbol)]),data)
    assert result['tier']=='T0'


def test_requests_is_excluded_but_keeps_underlying_tier(tmp_path):
    raw=record(tmp_path,[bash('cat source'),tool(LINE)])
    raw['instance_id']='psf__requests-999999'
    result=interpret_record(raw,inputs(tmp_path))
    assert result['tier']=='Excluded' and result['underlying_tier']=='T4'


def test_synthetic_rerun_folder_and_independent_verifier(tmp_path):
    run=tmp_path/'invented_arm'; task=run/'tasks'/IID; task.mkdir(parents=True)
    (task/'trajectory.jsonl').write_text('\n'.join(json.dumps(m) for m in [bash('cat source'),tool(LINE)]))
    gen=run/'_reproduction_cache'/IID; gen.mkdir(parents=True)
    (gen/'generation_trajectory.jsonl').write_text(json.dumps({'role':'assistant','content':LINE}))
    data=inputs(tmp_path); output=tmp_path/'audit'
    original={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in run.rglob('*.jsonl')}
    summary=audit_arm(run,output,tmp_path/'unused_images',input_provider=lambda iid:data)
    assert summary['T4_tasks']==[IID]
    assert summary['by_role']['generator']['counts']['T3']==1
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==h for p,h in original.items())
    verifier=runpy.run_path(str(Path(__file__).resolve().parents[2]/'scripts/verify_leakage_gaps.py'))
    assert verifier['verify_tiers'](output)['status']=='pass'
    path=output/'tiers/summary.json'; original_summary=path.read_text(); changed=json.loads(original_summary); changed['T4_tasks']=[]
    path.write_text(json.dumps(changed))
    with pytest.raises(ValueError,match='summary mismatch'):
        verifier['verify_tiers'](output)
    path.write_text(original_summary)
    receipt=output/'tiers/artifacts/invented_arm/repair'/f'{IID}.json'
    value=json.loads(receipt.read_text())
    answer=next(f for f in value['facts'] if f['category']=='answer')
    answer['occurrences']['tool_output']['line']=1
    receipt.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='first speaker mismatch'):
        verifier['verify_tiers'](output)


def test_rerun_cli_parser_executes_only_synthetic_folder(tmp_path,monkeypatch):
    path=Path(__file__).resolve().parents[2]/'scripts/audit_rerun_arm.py'
    spec=importlib.util.spec_from_file_location('synthetic_rerun_cli',path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    run=tmp_path/'invented_arm'; task=run/'tasks'/IID; task.mkdir(parents=True)
    (task/'trajectory.jsonl').write_text(json.dumps({'role':'assistant','content':LINE}))
    data=inputs(tmp_path); original=module.audit_arm
    monkeypatch.setattr(module,'audit_arm',lambda run,output,image_root:original(run,output,image_root,input_provider=lambda iid:data))
    monkeypatch.setattr('sys.argv',[str(path),'--run',str(run)])
    assert module.main()==0
    assert json.loads((run/'leakage_audit/tiers/summary.json').read_text())['T3_tasks']==[IID]


def test_missing_role_is_explicitly_unobserved(tmp_path):
    result=interpret_record(record(tmp_path,[{'role':'assistant','content':LINE}]),inputs(tmp_path))
    records=complete_records([result],{IID})
    missing=next(r for r in records if r['role']=='generator')
    assert missing['tier']=='T0' and not missing['observed']


def test_json_escaping_match_is_not_delivered_source_content(tmp_path):
    visible=r'fixture_literal = \invented_symbol'
    serialized_probe=r'fixture_literal = \\invented_symbol'
    raw=record(tmp_path,[{'role':'assistant','content':visible}])
    path=Path(raw['source'])/'trajectory.jsonl'
    raw['findings']=[{'kind':'test-patch-content','rule':'legacy','path':str(path),
                      'severity':'confirmed','line_no':None,'evidence':{}}]
    data=inputs(tmp_path,probes=OracleProbes(IID,test_patch_lines=(serialized_probe,)))
    result=interpret_record(raw,data)
    assert result['tier']=='T0'
    finding=result['raw_finding_interpretations'][0]
    assert finding['first_seen_in']=='model_output' and finding['serialization_only']
    assert not finding['decoded_match']


def test_empty_directory_metadata_is_not_nonempty_cache():
    text='total 8\ndrwxr-xr-x 2 root root 4096 Nov 1 12:00 .\ndrwxr-xr-x 3 root root 4096 Nov 1 12:00 ..'
    result=cache_observation('ls -la /root/.cache/pip',text,0,'/root/.cache/pip')
    assert result['rule']=='masked-read-empty-listing' and not result['nonempty_cache']


def test_archive_member_list_and_bytes_are_cache_observations():
    listing=cache_observation("python -c \"ZipFile('/root/.cache/pip/fixture.body').namelist()\"", "['pkg/fixture.py']",0,'/root/.cache/pip')
    assert listing['rule']=='masked-read-archive-member-list' and listing['nonempty_cache']
    content=cache_observation("python -c \"ZipFile('/root/.cache/pip/fixture.body').read('pkg/fixture.py')\"",LINE,0,'/root/.cache/pip')
    assert content['rule']=='masked-read-content' and content['content_bytes']>0


def test_rerun_keeps_co_located_repair_and_generator_chronology_separate(tmp_path):
    run=tmp_path/'invented_arm'; directory=run/'tasks'/IID; directory.mkdir(parents=True)
    (directory/'trajectory.jsonl').write_text(json.dumps({'role':'assistant','content':LINE}))
    (directory/'generation_trajectory.jsonl').write_text('\n'.join(json.dumps(m) for m in [bash('cat source'),tool(LINE)]))
    data=inputs(tmp_path); output=tmp_path/'audit'
    summary=audit_arm(run,output,tmp_path/'unused_images',input_provider=lambda iid:data)
    assert summary['by_role']['repair']['counts']['T3']==1
    assert summary['by_role']['generator']['counts']['T4']==1
    generator=json.loads((output/'tasks/invented_arm/generator'/f'{IID}.json').read_text())
    assert any(f['kind']=='gold-patch-content' for f in generator['findings'])
    repair=json.loads((output/'tasks/invented_arm/repair'/f'{IID}.json').read_text())
    assert not any(f['kind']=='gold-patch-content' for f in repair['findings'])
