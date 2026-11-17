import pytest

from reliability.provider_spend import ProviderLedger
from reliability.umgpt_spend import BudgetCap, SpendLedger


def ledger(path, provider='deepseek', job='arm_ds', cap=4):
    return ProviderLedger(path, provider=provider, job=job, total_usd=cap, job_usd=cap)


def paid(value, task='same_task', stage='V4', cost=.7):
    with value.stage(task, stage, 1.0):
        call = value.reserve(.9, task=task, task_cap=1, stage=stage, model_id='mock')
        value.settle(call, cost, input_tokens=100, output_tokens=10)


def test_both_repair_arms_share_deepseek_generator_cap(tmp_path):
    path = tmp_path / 'shared.json'
    arm_ds = ledger(path)
    paid(arm_ds, stage='agent', cost=.5)
    paid(arm_ds, cost=.8)
    arm_um = ledger(path, 'umgpt', 'arm_um', 20)
    paid(arm_um, stage='agent', cost=.4)
    generator_um_arm = ledger(path, job='arm_um')
    paid(generator_um_arm, cost=.8)
    paid(generator_um_arm, task='next_task', cost=.8)
    # DeepSeek spend is 2.9: an entire $1 V4 still fits, but a $1.2 stage cannot start.
    with pytest.raises(BudgetCap):
        with generator_um_arm.stage('third', 'V4', 1.2):
            pytest.fail('V4 must not run partway when its full ceiling cannot fit')
    assert len(generator_um_arm.account_calls(generator_um_arm.snapshot())) == 4
    assert len(arm_um.account_calls(arm_um.snapshot())) == 1


def test_pending_request_blocks_resume(tmp_path):
    first = ledger(tmp_path / 'shared.json')
    first.reserve(.1, task='x', task_cap=1, stage='V4', model_id='mock')
    with pytest.raises(BudgetCap, match='Unsettled'):
        with ledger(first.path, job='second').stage('x', 'V4', 1):
            pytest.fail('unsettled spend must fail closed')


def test_stage_escrow_releases_unused_ceiling(tmp_path):
    first = ledger(tmp_path / 'shared.json', cap=1.1)
    paid(first, cost=.1)
    paid(ledger(first.path, job='second', cap=1.1), cost=.1)
    assert sum(c['cost_usd'] for c in first.snapshot()['calls']) == pytest.approx(.2)


def test_legacy_um_ledger_entries_count_toward_account_cap(tmp_path):
    path = tmp_path / 'legacy.json'
    old = SpendLedger(path, job='probe', total_usd=20, job_usd=3)
    call = old.reserve(.8, task='x', task_cap=1, stage='agent', model_id='mock')
    old.settle(call, .8)
    new = ledger(path, 'umgpt', 'new_arm', 1)
    with pytest.raises(BudgetCap):
        with new.stage('x', 'V4', 1):
            pytest.fail('legacy spend must not reset on a new run')
