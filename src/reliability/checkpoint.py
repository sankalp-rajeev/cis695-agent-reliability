"""First-10 halt for a half of the main study.

Checked once, after ten tasks have finished, before the rest of the half is
allowed to continue. The thresholds are the ones pre-declared for this
checkpoint, not the looser end-of-half interim gates.
"""

from __future__ import annotations

FIRST10_MAX_INFRA = 2
FIRST10_MAX_MEAN_COST_USD = 0.15

_BILLING_OR_RATE = frozenset({"insufficient_balance", "rate_limited"})


def is_infrastructure_failure(row: dict) -> bool:
    """A task whose result is not a verdict on the patch.

    Billing and rate-limit stops are reported separately and are not counted
    here, so a drained account is not also called an infrastructure failure.
    """
    if row.get("agent_termination") in _BILLING_OR_RATE:
        return False
    if row.get("infrastructure_error"):
        return True
    if row.get("oracle_outcome") == "infra_error":
        return True
    return any(row.get(key) for key in ("agent_error", "verifier_error", "oracle_error"))


def task_cost_usd(row: dict) -> float:
    """Agent spend plus V4 generation spend, the same sum as the measured mean."""
    return float(row.get("cost_usd") or 0.0) + float(
        row.get("reproduction_generation_cost_usd") or 0.0
    )


def first10_halt_reason(
    rows: list[dict],
    *,
    audit_failed: bool,
    max_infra: int = FIRST10_MAX_INFRA,
    max_mean_cost_usd: float = FIRST10_MAX_MEAN_COST_USD,
) -> str | None:
    """Return a halt message after ten tasks, or None to continue.

    `rows` is the tasks finished so far, in completion order. Fewer than ten
    is not yet the checkpoint.
    """
    if len(rows) < 10:
        return None
    sample = rows[:10]
    infra = [row for row in sample if is_infrastructure_failure(row)]
    if len(infra) > max_infra:
        return (
            f"first-10 checkpoint: {len(infra)} infrastructure failures "
            f"(halt when more than {max_infra})"
        )
    mean = sum(task_cost_usd(row) for row in sample) / len(sample)
    if mean > max_mean_cost_usd:
        return (
            f"first-10 checkpoint: mean cost ${mean:.4f} per task "
            f"exceeds ${max_mean_cost_usd:.2f}"
        )
    if audit_failed:
        return "first-10 checkpoint: leakage audit failed"
    for row in sample:
        termination = row.get("agent_termination")
        if termination in _BILLING_OR_RATE:
            return (
                f"first-10 checkpoint: {termination} on {row.get('instance_id')} "
                "(billing or rate-limit termination)"
            )
    return None
