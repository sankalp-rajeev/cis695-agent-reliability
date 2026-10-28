"""Round-trip the native INCOMPLETE result through the unchanged policy input."""
import pytest
from pydantic import ValidationError

from reliability.verifier.decision import (
    BaselinePolicy,
    Decision,
    Evidence,
    FullPolicy,
    RelaxedPolicy,
    SignalOutcome,
)
from reliability.verifier.record import (
    DecisionEntry,
    SignalKind,
    SignalRecord,
    VerificationRecord,
    evidence_from_record,
    load_records,
    summarise,
)
from reliability.verifier.regression import RegressionReport, Signal
from reliability.verifier.run import signal_from_regression


def test_incomplete_survives_serialization_loading_and_policy(tmp_path):
    regression=signal_from_regression(RegressionReport(
        instance_id='fixture',signal=Signal.INCOMPLETE,original_signal=Signal.PASS,
        completeness='INCOMPLETE_CONFIRMED',incompleteness=('base: missing fixture',)))
    evidence=Evidence(integrity=SignalOutcome.PASS,regression=regression.outcome,
                      static=SignalOutcome.PASS,reproduction=SignalOutcome.PASS)
    record=VerificationRecord(instance_id='fixture',experiment_id='fixture',verifier_config='full',
        patch_sha256='sha256:'+'ab'*32,regression=regression,
        integrity=SignalRecord(kind=SignalKind.INTEGRITY,outcome=SignalOutcome.PASS),
        static=SignalRecord(kind=SignalKind.STATIC,outcome=SignalOutcome.PASS),
        reproduction=SignalRecord(kind=SignalKind.REPRODUCTION,outcome=SignalOutcome.PASS),
        reproduction_generator={'generator':{'model_id':'fixture-only-no-model-call'}},
        decision=DecisionEntry.from_record(FullPolicy().decide(evidence)),verified_at='2026-10-26T00:00:00Z')
    record.write(tmp_path/'tasks/fixture/verification_record.full.json')
    loaded,=load_records(tmp_path,'full')
    assert loaded.regression.outcome is SignalOutcome.NOT_AVAILABLE
    assert loaded.regression.absence.value=='incomplete'
    assert loaded.regression.findings['signal']=='INCOMPLETE'
    assert loaded.regression.findings['original_signal']=='PASS'
    rebuilt=evidence_from_record(loaded)
    assert not rebuilt.regression.is_pass
    assert FullPolicy().decide(rebuilt).decision is Decision.FLAG
    assert BaselinePolicy().decide(rebuilt).decision is Decision.FLAG
    # Document, do not change, the pre-existing secondary policy exception.
    assert RelaxedPolicy().decide(rebuilt).decision is Decision.ACCEPT
    assert summarise([loaded])['signals_absent']=={'regression:incomplete':1}
    assert summarise([loaded])['n_complete']==0


def test_native_incomplete_is_not_silently_coerced_to_a_neutral_pass():
    with pytest.raises(ValidationError):
        SignalRecord(kind=SignalKind.REGRESSION,outcome='INCOMPLETE')
