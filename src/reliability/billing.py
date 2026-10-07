"""Pre-run billing guard (prepared 2026-10-05, ahead of the 100-task main study).

A run that starts without enough balance to finish does not fail cleanly: the
account empties mid-task, that task's agent record gets
`Termination.INSUFFICIENT_BALANCE` (`reliability.agent.records`), and every
task scheduled after it is simply never run, with no record explaining why.
This module is the guard that runs once, before the first task starts, so that
failure mode is a refusal at the top of the log instead of a silent gap at
the bottom of a run directory.

Two inputs, by design, not one:

**Balance** comes from the provider's own balance endpoint when the provider
has one. DeepSeek does (`GET /user/balance`, keyed by the same API key the
agent calls use), so `fetch_deepseek_balance_usd` reads the true, current
account state rather than a number the run happened to be launched with. A
provider without a balance endpoint cannot be queried this way, so an explicit
balance is the required fallback — the guard needs a number from somewhere,
and asking the operator for one beats skipping the check.

**Start threshold** is the measured per-task mean times `n` times 1.5.
The mean is pilot_15's agent cost plus V4 generation cost, $0.084863757 per
task (10 tasks, combined total $0.84863757, measured from `runs/pilot_15` on
2026-10-07; `docs/checklist.md` rounded the same figure to $0.0849). For a
half of 50 that threshold is about $6.36. It is not the configured worst-case
ceiling (`n * ($0.50 repair cap + V4 cap)`), and it is not a $600 ceiling.
`projected_cost_usd` still computes that ceiling for inspection; the guard
does not consult it.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

DEEPSEEK_BALANCE_URL = "https://api.deepseek.com/user/balance"

#: pilot_15 agent `api_cost_usd` + V4 `generation.cost_usd`, 10 tasks.
#: 0.84863757 / 10. Do not replace this with the configured per-task cap.
MEASURED_MEAN_COST_USD_PER_TASK = 0.084863757
START_THRESHOLD_FACTOR = 1.5


def start_threshold_usd(
    n_tasks: int,
    *,
    mean_cost_usd_per_task: float = MEASURED_MEAN_COST_USD_PER_TASK,
    factor: float = START_THRESHOLD_FACTOR,
) -> float:
    """Balance the run must hold before the first task: mean × n × 1.5.

    Not the configured ceiling and not a flat $600. `n_tasks` is the number of
    tasks about to spend, which on a resume is the number still unfinished.
    """
    if n_tasks < 0:
        raise ValueError("n_tasks must be >= 0")
    if mean_cost_usd_per_task < 0 or factor < 0:
        raise ValueError("mean cost and factor must be >= 0")
    return n_tasks * mean_cost_usd_per_task * factor


def projected_cost_usd(
    n_tasks: int, *, max_cost_usd_per_task: float, generator_max_cost_usd: float,
) -> float:
    """Worst-case ceiling implied by the run's own configured budgets.

    Not an average and not a forecast: every task is already permitted to
    spend up to `max_cost_usd_per_task` (agent) plus `generator_max_cost_usd`
    (V4), so the ceiling for `n_tasks` of them is just that, multiplied out.
    """
    if n_tasks < 0:
        raise ValueError("n_tasks must be >= 0")
    if max_cost_usd_per_task < 0 or generator_max_cost_usd < 0:
        raise ValueError("per-task cost ceilings must be >= 0")
    return n_tasks * (max_cost_usd_per_task + generator_max_cost_usd)


def fetch_deepseek_balance_usd(api_key: str, *, timeout_s: float = 10.0) -> float:
    """Query DeepSeek's own balance endpoint. Raises if it cannot be read.

    Response shape (DeepSeek API reference, 2026):
        {"is_available": bool,
         "balance_infos": [{"currency": "USD", "total_balance": "12.34", ...}]}

    `is_available` reflects the account's actual billing state (it can be
    `false` with a nonzero balance showing, e.g. a payment hold), so it is
    checked on its own rather than inferred from the number.
    """
    request = urllib.request.Request(
        DEEPSEEK_BALANCE_URL,
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        raise RuntimeError(
            f"could not read the DeepSeek balance from {DEEPSEEK_BALANCE_URL}: "
            f"{type(exc).__name__}: {exc}. Pass an explicit balance instead."
        ) from exc

    infos = payload.get("balance_infos") or []
    usd = next((info for info in infos if info.get("currency") == "USD"), None)
    if usd is None:
        raise RuntimeError(
            f"DeepSeek balance response has no USD entry: {payload!r}. "
            "Pass an explicit balance instead."
        )
    if not payload.get("is_available", True):
        raise RuntimeError(
            f"DeepSeek reports is_available=false (balance shows "
            f"${usd.get('total_balance')}); the account cannot currently be "
            "billed. Pass an explicit balance only if this is known to be "
            "transient."
        )
    return float(usd["total_balance"])


def require_sufficient_balance(balance_usd: float, projected_cost_usd: float) -> None:
    """Abort the run if the balance cannot cover the projected cost.

    Raised as `SystemExit`, the same convention `reliability.provenance.
    require_clean_tree` uses for a pre-run refusal, with "Insufficient
    Balance" verbatim in the message — its own, grep-able termination reason,
    distinct from every other `SystemExit` a run script raises (dirty tree,
    unverified model, Docker not ready, ...) and from the two agent-level
    outcomes it is not: `Termination.RATE_LIMITED` (throttling; retryable by
    waiting) and the generic `Termination.ERROR`. This is the *pre-run* gate;
    `Termination.INSUFFICIENT_BALANCE` (`reliability.agent.records`) is the
    separate, per-task outcome for the account draining mid-run after this
    check already passed — e.g. spent by a concurrent task between the check
    and that task's own call.
    """
    if balance_usd < projected_cost_usd:
        raise SystemExit(
            f"Insufficient Balance: ${balance_usd:.2f} available, "
            f"${projected_cost_usd:.2f} projected for this run. Refusing to "
            "start. Top up the account or pass a smaller manifest and retry."
        )
