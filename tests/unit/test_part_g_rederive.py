"""scripts/part_g_rederive.py: stored signals under the part G classification (B9 step 6)."""

import importlib.util
import pathlib

from reliability.verifier.decision import SignalOutcome
from reliability.verifier.record import SignalAbsence, SignalKind, SignalRecord
from tests.unit.test_part_g import GIS, NO_TESTS, health, stage

ROOT = pathlib.Path(__file__).resolve().parents[2]
FORMS = 'tests/forms_tests/tests/test_forms.py'


def _script():
    spec = importlib.util.spec_from_file_location("part_g_rederive", ROOT / "scripts" / "part_g_rederive.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def passed(kind, **findings):
    return SignalRecord(kind=kind, outcome=SignalOutcome.PASS, findings=findings)


def absent(kind, reason, infrastructure):
    record = SignalRecord.absent(kind, SignalAbsence.ERROR, reason)
    record.findings.update(absence_reason=reason, infrastructure=infrastructure)
    return record


def signals(**override):
    base = {SignalKind.INTEGRITY: passed(SignalKind.INTEGRITY, violations=[], patch_applies=True),
            SignalKind.REGRESSION: passed(SignalKind.REGRESSION),
            SignalKind.STATIC: passed(SignalKind.STATIC),
            SignalKind.REPRODUCTION: passed(SignalKind.REPRODUCTION)}
    base.update(override)
    return base


def test_unchanged_task_is_identical():
    mod = _script()
    out = mod.rederive(signals(), g1=None, after=None, applies=True, selected=())
    assert mod.compare(signals(), out['signals']) == [] and not out['v2_rerun_needed']


def test_patch_caused_block_loses_its_infrastructure_flag():
    mod = _script()
    old = signals(**{SignalKind.REGRESSION: absent(SignalKind.REGRESSION, 'RUN_HEALTH_G1:x', True)})
    g1 = [health('base'), health('patched', stage('tests/a.py'))]
    out = mod.rederive(old, g1=g1, after=None, applies=True, selected=('tests/a.py::T::t',))
    assert out['signals'][SignalKind.REGRESSION].findings['infrastructure'] is False
    assert out['signals'][SignalKind.REGRESSION].findings['attribution'] == 'patch'
    assert mod.compare(old, out['signals']) == ['V2 infrastructure True -> False']


def test_newly_paired_exclusion_means_v2_must_rerun():
    mod = _script()
    old = signals(**{SignalKind.REGRESSION: absent(SignalKind.REGRESSION, 'RUN_HEALTH_G1:x', True)})
    g1 = [health(t, stage(FORMS, message=NO_TESTS),
                 stage('tests/gis_tests/test_geoforms.py', message=GIS, allowed_exception=['GIS_GUARD']))
          for t in ('base', 'patched')]
    out = mod.rederive(old, g1=g1, after=None, applies=True, selected=(FORMS + '::T::t', 'tests/b.py::T::t'))
    assert out['v2_rerun_needed'] and out['notes'] == ['A7 now excludes ' + FORMS]


def test_patch_that_does_not_apply_fails_v1_and_drops_executor_exceptions():
    mod = _script()
    old = signals(**{SignalKind.STATIC: absent(SignalKind.STATIC, 'EXECUTOR_EXCEPTION:ContainerError', True),
                     SignalKind.REPRODUCTION: absent(SignalKind.REPRODUCTION, 'V4_EXCEPTION:ContainerError', True),
                     SignalKind.REGRESSION: SignalRecord.absent(SignalKind.REGRESSION, SignalAbsence.NOTHING_TO_CHECK,
                                                                'no tests selected')})
    out = mod.rederive(old, g1=None, after=None, applies=False, selected=())
    new = out['signals']
    assert new[SignalKind.INTEGRITY].outcome is SignalOutcome.FAIL
    assert new[SignalKind.STATIC].findings == {'absence_reason': 'PATCH_DOES_NOT_APPLY', 'infrastructure': False}
    assert new[SignalKind.REPRODUCTION].absence is SignalAbsence.NOTHING_TO_CHECK
    assert new[SignalKind.REGRESSION].findings['absence_reason'] == 'PATCH_DOES_NOT_APPLY'
    assert 'V1 PASS -> FAIL' in mod.compare(old, new)
