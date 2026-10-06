"""Pre-run billing guard: projected cost, balance lookup, and the abort gate."""

from __future__ import annotations

import json
import urllib.error

import pytest

from reliability.billing import (
    DEEPSEEK_BALANCE_URL,
    fetch_deepseek_balance_usd,
    projected_cost_usd,
    require_sufficient_balance,
)

# --- projected_cost_usd ------------------------------------------------------


def test_projected_cost_is_the_worst_case_ceiling_not_an_average():
    assert projected_cost_usd(
        100, max_cost_usd_per_task=5.00, generator_max_cost_usd=1.00) == 600.00


def test_projected_cost_of_zero_tasks_is_zero():
    assert projected_cost_usd(
        0, max_cost_usd_per_task=5.00, generator_max_cost_usd=1.00) == 0.0


def test_negative_task_count_is_rejected():
    with pytest.raises(ValueError, match="n_tasks"):
        projected_cost_usd(-1, max_cost_usd_per_task=5.00, generator_max_cost_usd=1.00)


@pytest.mark.parametrize(
    "max_cost,gen_cost", [(-1.0, 1.0), (1.0, -1.0)],
)
def test_negative_budget_ceilings_are_rejected(max_cost, gen_cost):
    with pytest.raises(ValueError, match="per-task cost ceilings"):
        projected_cost_usd(
            10, max_cost_usd_per_task=max_cost, generator_max_cost_usd=gen_cost)


# --- require_sufficient_balance ---------------------------------------------


def test_sufficient_balance_passes_silently():
    require_sufficient_balance(600.01, 600.00)
    require_sufficient_balance(600.00, 600.00)  # exactly enough is enough


def test_insufficient_balance_aborts_with_its_own_reason():
    with pytest.raises(SystemExit, match="Insufficient Balance"):
        require_sufficient_balance(8.49, 600.00)


def test_insufficient_balance_message_is_not_rate_limited_or_generic_error():
    """The abort reason must read as billing, not be mistaken for the other
    two per-task outcomes it is explicitly kept separate from."""
    with pytest.raises(SystemExit) as excinfo:
        require_sufficient_balance(0.0, 1.0)
    message = str(excinfo.value)
    assert "Insufficient Balance" in message
    assert "rate" not in message.lower()
    assert "RATE_LIMITED" not in message


# --- fetch_deepseek_balance_usd ----------------------------------------------


class _FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_fetch_balance_reads_the_usd_entry(monkeypatch):
    payload = {
        "is_available": True,
        "balance_infos": [
            {"currency": "CNY", "total_balance": "999.00"},
            {"currency": "USD", "total_balance": "12.34"},
        ],
    }

    def fake_urlopen(request, timeout):
        assert request.full_url == DEEPSEEK_BALANCE_URL
        assert request.get_header("Authorization") == "Bearer sk-test"
        return _FakeResponse(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    assert fetch_deepseek_balance_usd("sk-test") == 12.34


def test_fetch_balance_rejects_an_unavailable_account(monkeypatch):
    payload = {
        "is_available": False,
        "balance_infos": [{"currency": "USD", "total_balance": "12.34"}],
    }
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout: _FakeResponse(json.dumps(payload).encode("utf-8")),
    )
    with pytest.raises(RuntimeError, match="is_available=false"):
        fetch_deepseek_balance_usd("sk-test")


def test_fetch_balance_rejects_a_response_with_no_usd_entry(monkeypatch):
    payload = {"is_available": True, "balance_infos": [{"currency": "CNY", "total_balance": "1"}]}
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout: _FakeResponse(json.dumps(payload).encode("utf-8")),
    )
    with pytest.raises(RuntimeError, match="no USD entry"):
        fetch_deepseek_balance_usd("sk-test")


def test_fetch_balance_surfaces_network_failure_as_a_clear_runtime_error(monkeypatch):
    def raise_url_error(request, timeout):
        raise urllib.error.URLError("no route to host")

    monkeypatch.setattr("urllib.request.urlopen", raise_url_error)
    with pytest.raises(RuntimeError, match="could not read the DeepSeek balance"):
        fetch_deepseek_balance_usd("sk-test")


def test_fetch_balance_surfaces_malformed_json_as_a_clear_runtime_error(monkeypatch):
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda request, timeout: _FakeResponse(b"not json")
    )
    with pytest.raises(RuntimeError, match="could not read the DeepSeek balance"):
        fetch_deepseek_balance_usd("sk-test")
