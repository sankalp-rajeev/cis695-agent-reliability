"""scripts/preflight.py (amendment B9, 7b): fast container checks before a run.

Only the pure parts are tested here: how exceptions are classified, and which rows
make the preflight fail. The container checks reuse the verifier's own functions.
"""

import importlib.util
import pathlib

from reliability.verifier.container import ContainerStartError, PatchApplyError
from reliability.verifier.run_health import RunHealthError
from reliability.verifier.source_integrity import SourceIntegrityError

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _script():
    spec = importlib.util.spec_from_file_location("preflight", ROOT / "scripts" / "preflight.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_exceptions_are_classified():
    mod = _script()
    assert mod.classify(PatchApplyError('patch did not apply')) == 'patch_does_not_apply'
    assert mod.classify(ContainerStartError('could not start')) == 'container_start'
    assert mod.classify(SourceIntegrityError({'mismatches': []})) == 'unclassified'
    assert mod.classify(ValueError('anything else')) == 'unclassified'


def test_an_unparseable_patch_is_classified():
    # verify_task records it as a V1 exception absence on that task; it never stops a run.
    from reliability.verifier.patch import PatchParseError
    mod = _script()
    assert mod.classify(PatchParseError("no 'diff --git' file headers")) == 'patch_unparseable'


def test_run_health_attribution_is_reported():
    mod = _script()
    error = RunHealthError({'halt': True})
    error.g1_category, error.attribution = 'module_import_failure', 'patch'
    assert mod.g1_row(error) == {'g1': 'BLOCKED', 'g1_category': 'module_import_failure', 'attribution': 'patch'}


def row(iid, **values):
    return {'instance_id': iid, 'exceptions': [], 'g1': 'READY', 'attribution': None,
            'infrastructure': False, 'start_failures': 0, 'start_successes': 3, **values}


def test_clean_rows_pass_and_are_not_listed():
    mod = _script()
    summary = mod.summarize([row('a__a-1'), row('a__a-2')], machine=[None, None])
    assert summary['pass'] and summary['listed'] == [] and summary['run_stopping'] == []


def test_listed_rows_cover_exceptions_blocks_and_infrastructure():
    mod = _script()
    rows = [row('a__a-1'), row('a__a-2', g1='BLOCKED', attribution='patch'),
            row('a__a-3', exceptions=[{'stage': 'V3', 'class': 'patch_does_not_apply'}]),
            row('a__a-4', infrastructure=True, g1='BLOCKED', attribution='infrastructure'),
            row('a__a-5', apply='FAIL', v1='FAIL', g1='NOT_RUN')]
    summary = mod.summarize(rows, machine=[None, None])
    assert summary['listed'] == ['a__a-2', 'a__a-3', 'a__a-4', 'a__a-5']
    assert summary['pass'] and summary['unclassified'] == []


def test_an_unclassified_exception_fails_the_preflight():
    mod = _script()
    summary = mod.summarize([row('a__a-1', exceptions=[{'stage': 'V2', 'class': 'unclassified'}])],
                            machine=[None, None])
    assert not summary['pass'] and summary['unclassified'] == ['a__a-1']


def test_machine_conditions_and_three_start_failures_in_a_row_are_run_stopping():
    mod = _script()
    failed = lambda i: row(i, start_failures=2, start_successes=0)  # noqa: E731
    summary = mod.summarize([failed('a__a-1'), failed('a__a-2'), failed('a__a-3'), row('a__a-4')],
                            machine=[None, None])
    assert not summary['pass'] and summary['run_stopping'] == [
        '3 consecutive tasks with only container-start failures ending at a__a-3']
    summary = mod.summarize([row('a__a-1')], machine=['disk below 20 GB: 5.0 GB free at /', None])
    assert not summary['pass'] and summary['run_stopping'] == ['before: disk below 20 GB: 5.0 GB free at /']


def test_summary_counts_the_grader_command_that_applied_each_patch():
    mod = _script()
    rows = [row('a__a-1', apply='PASS', apply_command='git apply --verbose'),
            row('a__a-2', apply='PASS', apply_command='patch --batch --forward --fuzz=5 -p1 -i'),
            row('a__a-3', apply='PASS', apply_command='git apply --verbose'),
            row('a__a-4', apply='FAIL', apply_command=None), row('a__a-5', apply=None, apply_command=None)]
    summary = mod.summarize(rows, machine=[None, None])
    assert summary['apply_commands'] == {'git apply --verbose': 2, 'patch --batch --forward --fuzz=5 -p1 -i': 1}
    assert summary['apply_failed'] == ['a__a-4'] and summary['empty'] == ['a__a-5']
