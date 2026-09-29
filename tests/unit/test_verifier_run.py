"""Verifier run: layers record attributed absences, including V4."""

from __future__ import annotations

from reliability.verifier.decision import SignalOutcome
from reliability.verifier.record import SignalAbsence, SignalKind
from reliability.verifier.regression import RegressionReport, Signal
from reliability.verifier.run import run_layers, signal_from_regression, signal_from_static
from reliability.verifier.static_checks import CheckKind, CheckResult, CheckStatus, StaticReport

PATCH = """diff --git a/src/pkg/core.py b/src/pkg/core.py
index 1..2 100644
--- a/src/pkg/core.py
+++ b/src/pkg/core.py
@@ -1,2 +1,2 @@
 def compute(x):
-    return x * 2
+    return x * 3
"""


def test_without_a_container_regression_and_static_are_disabled():
    signals, _ = run_layers(
        PATCH, tree=None, command_executor=None, test_executor=None,
        instance_id="x")
    assert signals[SignalKind.INTEGRITY].outcome is SignalOutcome.PASS
    assert signals[SignalKind.REGRESSION].absence is SignalAbsence.DISABLED
    assert signals[SignalKind.STATIC].absence is SignalAbsence.DISABLED
    assert signals[SignalKind.REPRODUCTION].absence is SignalAbsence.NOT_IMPLEMENTED


def test_empty_patch_is_nothing_to_check_not_a_pass():
    signals, _ = run_layers(
        "", tree=None, command_executor=None, test_executor=None,
        instance_id="x")
    assert signals[SignalKind.REGRESSION].absence is SignalAbsence.NOTHING_TO_CHECK
    assert signals[SignalKind.REGRESSION].outcome is SignalOutcome.NOT_AVAILABLE


def test_unreliable_baseline_is_an_error_absence():
    rec = signal_from_regression(
        RegressionReport(instance_id="x", signal=Signal.BASELINE_UNRELIABLE))
    assert rec.outcome is SignalOutcome.NOT_AVAILABLE
    assert rec.absence is SignalAbsence.ERROR


def test_static_with_no_tools_is_not_configured():
    report = StaticReport(results=tuple(
        CheckResult(kind=k, status=CheckStatus.NOT_AVAILABLE) for k in CheckKind))
    rec = signal_from_static(report)
    assert rec.outcome is SignalOutcome.NOT_AVAILABLE
    assert rec.absence is SignalAbsence.NOT_CONFIGURED
    assert rec.outcome is not SignalOutcome.PASS
