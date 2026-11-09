"""Identity accounting from masked, freshly reproduced module-import stderr."""

import base64
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from reliability.env import clean_env
from reliability.verifier.container import _BATCH_DRIVER, run_from_capture
from reliability.verifier.regression import TestStatus
from reliability.verifier.result_parser import sympy_import_batches, sympy_import_signature
from reliability.verifier.run_health import health_for_run, module_execution_stages
from reliability.verifier.selection import TestRunner

MODULE = 'sympy/physics/quantum/tests/test_printing.py'
IDENTITY = MODULE + '::test_anticommutator'
HEALTHY = 'sympy/tests/test_healthy.py::test_healthy'
STDERR = (Path(__file__).parents[1]/'fixtures/sympy_module_import_stderr.masked.txt').read_bytes()


def capture(*, healthy=True, stderr=STDERR, stdout_trace=False, base_progress=()):
    # The only terminal token here is synthetic; fixture stderr has none.
    output = b'sympy/tests/test_healthy.py[1]\ntest_healthy ok\n' if healthy else b''
    events = []
    if healthy:
        events.extend((dict(event='start', batch=1, module=HEALTHY.split('::')[0], ids=[HEALTHY], offset=0),
            dict(event='end', batch=1, module=HEALTHY.split('::')[0], returncode=0,
                 observed_ids=[HEALTHY], missing_ids=[], offset=len(output))))
    for batch in (2, 3):
        events.append(dict(event='start', batch=batch, module=MODULE, ids=[IDENTITY], offset=len(output)))
        output += stderr
        events.append(dict(event='end', batch=batch, module=MODULE, returncode=1,
            observed_ids=[], missing_ids=[IDENTITY], load_failure=True,
            retry=batch==3, parent=2 if batch==3 else None, split=batch==2, offset=len(output),
            stderr_b64='' if stdout_trace else base64.b64encode(stderr).decode()))
    events.append(dict(event='complete'))
    ids = (HEALTHY, IDENTITY) if healthy else (IDENTITY,)
    run = run_from_capture(TestRunner('sympy', 'masked fixture'), ids, runner_log=output,
                           events=tuple(events), base_progress_modules=base_progress)
    return replace(run, stage_health=tuple(module_execution_stages('fixture', 'base', 'sympy', run, [])))


def test_both_trees_import_failure_is_missing_evidence_without_identity_halt():
    for tree in ('base', 'patched'):
        run = capture()
        assert run.by_id()[IDENTITY].status is TestStatus.COLLECTION_ERROR
        assert run.evidence_complete and not run.infrastructure_errors
        health = health_for_run('fixture', tree, run, (HEALTHY, IDENTITY))
        assert health['G2']['lost_count'] == 0 and not health['halt']
        assert run.stage_health[0]['import_signature']
        assert not run.stage_health[0]['identity_failure']
        from reliability.verifier.accounting import ADMITTED_STATUSES
        assert run.by_id()[IDENTITY].status not in ADMITTED_STATUSES


def test_patched_only_import_failure_retains_Fix17_ERROR_after_base_progress():
    run = capture(base_progress=(MODULE,))
    assert run.by_id()[IDENTITY].status is TestStatus.ERROR
    assert not health_for_run('fixture', 'patched', run, (HEALTHY, IDENTITY))['halt']
    assert not run.infrastructure_errors


@pytest.mark.parametrize('mode', ['no_stderr', 'stdout_only', 'wrong_module', 'test_body', 'no_healthy'])
def test_unproven_module_identity_loss_halts_even_small_trees(mode):
    stderr = STDERR
    if mode == 'no_stderr': stderr = b''
    if mode == 'wrong_module': stderr = stderr.replace(MODULE.encode(), b'sympy/tests/test_other.py')
    if mode == 'test_body': stderr = stderr.replace(b'in <module>', b'in test_body')
    run = capture(stderr=stderr, stdout_trace=mode=='stdout_only', healthy=mode!='no_healthy')
    assert run.by_id()[IDENTITY].status is TestStatus.NOT_RUN
    health = health_for_run('fixture', 'base', run, run.requested_tests)
    assert health['halt'] and health['G2']['lost_count'] == 1
    assert health['executor_failures']


def test_ordinary_named_import_exception_qualifies():
    stderr = ('Traceback (most recent call last):\n  File "/testbed/'+MODULE+'", line 1, in <module>\n'
              'ModuleNotFoundError: No module named \'optional_dependency\'\n').encode()
    run = capture(stderr=stderr)
    assert run.by_id()[IDENTITY].status is TestStatus.COLLECTION_ERROR
    assert 'ModuleNotFoundError' in run.stage_health[0]['import_signature']


def test_signature_does_not_establish_health_by_itself():
    assert sympy_import_signature(MODULE, STDERR.decode())
    assert not sympy_import_batches(capture(healthy=False).events)


def test_unmapped_SymPy_identity_halts_below_count_threshold():
    run = capture()
    run = replace(run, unmatched_ids=(IDENTITY,),
                  stage_health=(*run.stage_health, {'stage':'execution', 'runner':'sympy',
                      'status':'COMPLETE', 'input_count':2, 'output_count':1}))
    health = health_for_run('fixture', 'base', run, run.requested_tests)
    assert health['G2']['lost_count'] == 1 and health['halt']


def test_health_proof_can_be_another_invocation_of_the_same_module():
    events = [dict(e) for e in capture().events]
    healthy_id = MODULE + '::test_healthy'
    for event in events[:2]:
        event['module'] = MODULE
        if event['event'] == 'start': event['ids'] = [healthy_id]
        else: event['observed_ids'] = [healthy_id]
    assert len(sympy_import_batches(events)) == 2


def test_timed_out_and_unreached_ids_never_become_identity_loss():
    other = MODULE + '::test_big_expr'
    output = (MODULE+'[2]\ntest_anticommutator ').encode()
    events = (dict(event='start', batch=1, module=MODULE, ids=[IDENTITY, other], offset=0),
        dict(event='end', batch=1, module=MODULE, returncode=-9, timed_out=True,
             missing_ids=[IDENTITY, other], offset=len(output), stderr_b64=base64.b64encode(STDERR).decode()),
        dict(event='not_reached', module=MODULE, ids=[IDENTITY, other], elapsed_s=1800),
        dict(event='complete'))
    run = run_from_capture(TestRunner('sympy', 'masked fixture'), (IDENTITY, other),
                           runner_log=output, events=events, budget_s=1800)
    assert run.by_id()[IDENTITY].status is TestStatus.TIMEOUT
    assert run.by_id()[other].status is TestStatus.NOT_REACHED
    assert not health_for_run('fixture', 'base', run, (IDENTITY, other))['halt']


@pytest.mark.parametrize('healthy_first', [True, False])
def test_real_driver_preserves_stderr_attribution_and_same_tree_health(tmp_path, healthy_first):
    ids = [HEALTHY, IDENTITY] if healthy_first else [IDENTITY, HEALTHY]
    (tmp_path/'verifier_ids').write_text('\n'.join(ids)+'\n')
    (tmp_path/'verifier_module_ids.json').write_text(json.dumps({t:t.split('::')[0] for t in ids}))
    (tmp_path/'import.stderr').write_bytes(STDERR)
    (tmp_path/'verifier_sympy_driver.py').write_text(
        'import pathlib,sys\n'
        'if sys.argv[2] == '+repr(MODULE)+':\n'
        ' sys.stderr.buffer.write(pathlib.Path("import.stderr").read_bytes()); sys.exit(1)\n'
        'print("sympy/tests/test_healthy.py[1]\\ntest_healthy ok")\n')
    driver = tmp_path/'driver.py'
    driver.write_text(_BATCH_DRIVER.replace('/tmp/verifier_', str(tmp_path/'verifier_'))
                     .replace('"python"', repr(sys.executable)))
    subprocess.run([sys.executable, str(driver), 'sympy'], cwd=tmp_path, env=clean_env(),
                   check=True, capture_output=True, timeout=30)
    events = tuple(json.loads(line) for line in (tmp_path/'verifier_events.jsonl').read_text().splitlines())
    errors = [e for e in events if e.get('module')==MODULE and e['event']=='end']
    assert len(errors)==2
    assert all(base64.b64decode(e['stderr_b64'])==STDERR for e in errors)
    run = run_from_capture(TestRunner('sympy', 'real driver'), tuple(ids),
        runner_log=(tmp_path/'verifier_out.txt').read_bytes(), events=events)
    assert run.by_id()[IDENTITY].status is TestStatus.COLLECTION_ERROR
    assert not run.infrastructure_errors and run.evidence_complete
