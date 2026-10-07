"""First-10 halt, on synthetic rows. No run, no containers."""

from __future__ import annotations

from reliability.checkpoint import first10_halt_reason


def _row(i, **overrides):
    row = {
        "instance_id": f"task-{i}",
        "agent_termination": "completed",
        "cost_usd": 0.05,
        "reproduction_generation_cost_usd": 0.02,
        "oracle_outcome": "resolved",
        "infrastructure_error": False,
    }
    row.update(overrides)
    return row


def _ten(**overrides):
    return [_row(i, **overrides) for i in range(10)]


def test_a_clean_ten_does_not_halt():
    assert first10_halt_reason(_ten(), audit_failed=False) is None


def test_two_infrastructure_failures_do_not_halt():
    rows = _ten()
    rows[0]["infrastructure_error"] = True
    rows[1]["oracle_outcome"] = "infra_error"
    assert first10_halt_reason(rows, audit_failed=False) is None


def test_more_than_two_infrastructure_failures_halt():
    rows = _ten()
    rows[0]["agent_error"] = "boom"
    rows[1]["verifier_error"] = "boom"
    rows[2]["oracle_error"] = "boom"
    reason = first10_halt_reason(rows, audit_failed=False)
    assert reason is not None
    assert "infrastructure" in reason


def test_cost_above_015_per_task_halts():
    rows = _ten(cost_usd=0.10, reproduction_generation_cost_usd=0.06)
    reason = first10_halt_reason(rows, audit_failed=False)
    assert reason is not None
    assert "cost" in reason


def test_cost_at_015_does_not_halt():
    rows = _ten(cost_usd=0.10, reproduction_generation_cost_usd=0.05)
    assert first10_halt_reason(rows, audit_failed=False) is None


def test_a_failed_audit_halts():
    reason = first10_halt_reason(_ten(), audit_failed=True)
    assert reason is not None
    assert "audit" in reason


def test_any_billing_termination_halts():
    rows = _ten()
    rows[4]["agent_termination"] = "insufficient_balance"
    reason = first10_halt_reason(rows, audit_failed=False)
    assert reason is not None
    assert "insufficient_balance" in reason


def test_any_rate_limit_termination_halts():
    rows = _ten()
    rows[4]["agent_termination"] = "rate_limited"
    reason = first10_halt_reason(rows, audit_failed=False)
    assert reason is not None
    assert "rate_limited" in reason


def test_fewer_than_ten_is_not_the_checkpoint():
    assert first10_halt_reason(_ten()[:9], audit_failed=True) is None
