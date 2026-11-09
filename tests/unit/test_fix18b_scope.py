"""Synthetic split/rerun evidence and real merged-pipe driver checks."""

import base64
import json
import subprocess
import sys
from pathlib import Path

import pytest

from reliability.env import clean_env
from reliability.verifier.container import _BATCH_DRIVER, run_from_capture
from reliability.verifier.regression import TestStatus
from reliability.verifier.run_health import health_for_run
from reliability.verifier.selection import TestRunner

MODULE = 'sympy/physics/quantum/tests/test_printing.py'
IDS = (MODULE + '::test_one', MODULE + '::test_two')
IMPORT_STDERR = (Path(__file__).parents[1] / 'fixtures/sympy_module_import_stderr.masked.txt').read_bytes()


def split_capture(*, silent_retry=False, parent_stderr=b''):
    output = parent_stderr
    events = [dict(event='start', batch=1, module=MODULE, ids=IDS, offset=0),
              dict(event='end', batch=1, module=MODULE, returncode=1, observed_ids=[],
                   missing_ids=IDS, load_failure=True, split=True, offset=len(output),
                   stderr_b64=base64.b64encode(parent_stderr).decode())]
    # These terminal tokens and statuses are entirely synthetic.
    for batch, (identity, token) in enumerate(zip(IDS, ('ok', 'F')), 2):
        silent = silent_retry and batch == 3
        events.append(dict(event='start', batch=batch, module=MODULE, ids=[identity], offset=len(output)))
        if not silent:
            output += (MODULE + '[1]\n' + identity.split('::')[1] + ' ' + token + '\n').encode()
        events.append(dict(event='end', batch=batch, module=MODULE, returncode=int(batch == 3),
                           retry=True, parent=1, split=False, load_failure=silent,
                           observed_ids=[] if silent else [identity],
                           missing_ids=[identity] if silent else [], offset=len(output), stderr_b64=''))
    events.append(dict(event='complete'))
    return run_from_capture(TestRunner('sympy', 'synthetic split'), IDS,
                            runner_log=output, events=tuple(events))


@pytest.mark.parametrize('parent_stderr', [b'', IMPORT_STDERR], ids=['silent-parent', 'proven-parent'])
def test_split_parent_keeps_all_rerun_statuses_without_halt(parent_stderr):
    run = split_capture(parent_stderr=parent_stderr)
    assert [r.status for r in run.results] == [TestStatus.PASSED, TestStatus.FAILED]
    assert run.evidence_complete and not run.infrastructure_errors
    assert not health_for_run('fixture', 'base', run, IDS)['halt']
    assert len(run.results) == len({r.test_id for r in run.results}) == 2


def test_silent_rerun_without_import_proof_still_halts():
    run = split_capture(silent_retry=True)
    assert run.by_id()[IDS[0]].status is TestStatus.PASSED
    assert run.by_id()[IDS[1]].status is TestStatus.NOT_RUN
    health = health_for_run('fixture', 'base', run, IDS)
    assert health['halt'] and health['G2']['lost_count'] == 1
    assert any('SymPy module identity loss' in error for error in run.infrastructure_errors)


@pytest.mark.parametrize('kind', ['pytest', 'django'])
def test_real_driver_matches_merged_pipe_with_no_stderr_key(tmp_path, kind):
    identity = 'fake_test.py::test_case' if kind == 'pytest' else 'fake_test.TestCase.test_case'
    terminal = ('fake_test.py::test_case PASSED\n' if kind == 'pytest'
                else 'test_case (fake_test.TestCase) ... ok\n')
    # Alternate writes faster than the reader can schedule. Separate pipes can
    # reorder these bytes; the shared pipe preserves the writer's order.
    fake = ('import os\nfor index in range(200):\n'
            ' os.write(1, ("stdout %d\\n" % index).encode())\n'
            ' os.write(2, ("stderr %d\\n" % index).encode())\n'
            'os.write(2, ' + repr(terminal.encode()) + ')\n')
    if kind == 'pytest':
        (tmp_path / 'pytest.py').write_text(fake)
        argv = [sys.executable, '-m', 'pytest', '-p', 'no:cacheprovider', '-v', '--', identity]
    else:
        (tmp_path / 'tests').mkdir()
        (tmp_path / 'tests/runtests.py').write_text(fake)
        argv = [sys.executable, 'tests/runtests.py', '--verbosity=2', identity]
    expected = subprocess.run(argv, cwd=tmp_path, env=clean_env(), stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, check=True, timeout=30).stdout
    (tmp_path / 'verifier_ids').write_text(identity + '\n')
    driver = tmp_path / 'driver.py'
    driver.write_text(_BATCH_DRIVER.replace('/tmp/verifier_', str(tmp_path / 'verifier_'))
                      .replace('"python"', repr(sys.executable)))
    actual = subprocess.run([sys.executable, str(driver), kind], cwd=tmp_path, env=clean_env(),
                            capture_output=True, check=True, timeout=30)
    assert actual.stdout == (tmp_path / 'verifier_out.txt').read_bytes() == expected
    assert actual.stderr == b''
    events = [json.loads(line) for line in (tmp_path / 'verifier_events.jsonl').read_text().splitlines()]
    assert not any('stderr_b64' in event for event in events)
    ends = [event for event in events if event['event'] == 'end']
    assert len(ends) == 1 and ends[0]['observed_ids'] == [identity]
    assert not ends[0]['split']
