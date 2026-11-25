import pytest

from reliability.provider_spend import ProviderLedger, seed_provider_ledger
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


def test_resume_cannot_reset_a_partially_spent_stage_ceiling(tmp_path):
    first = ledger(tmp_path / 'shared.json')
    paid(first, cost=.1)
    with pytest.raises(BudgetCap, match='already-used per-task ceiling'):
        with first.stage('same_task', 'V4', 1):
            pytest.fail('a fresh full V4 must fail before starting, rather than stop partway')


def test_seeded_legacy_bytes_count_against_um_account_cap(tmp_path):
    import hashlib
    source, destination = tmp_path / 'probe.json', tmp_path / 'runs/provider.json'
    old = SpendLedger(source, job='probe', total_usd=20, job_usd=3)
    call = old.reserve(.66, task='probe', task_cap=1, stage='agent', model_id='mock')
    old.settle(call, .66)
    raw = source.read_bytes()
    result = seed_provider_ledger(source, destination)
    assert source.read_bytes() == destination.read_bytes() == raw
    assert result['sha256'] == hashlib.sha256(raw).hexdigest()
    assert result['accounts'] == [{'provider': 'umgpt', 'account': 'default', 'spent_usd': .66}]
    new = ledger(destination, provider='umgpt', job='new_arm', cap=1)
    with pytest.raises(BudgetCap):
        new.reserve(.35, task='new', task_cap=1, stage='agent', model_id='mock')
    assert len(new.snapshot()['calls']) == 1


def test_seed_refuses_nonempty_destination_without_changing_it(tmp_path):
    source, destination = tmp_path / 'probe.json', tmp_path / 'provider.json'
    source.write_bytes(b'{"version":1,"calls":[]}\n')
    destination.write_bytes(b'preexisting ledger bytes')
    with pytest.raises(ValueError, match='non-empty'):
        seed_provider_ledger(source, destination)
    assert destination.read_bytes() == b'preexisting ledger bytes'


def test_seed_accepts_empty_destination_and_rejects_invalid_source(tmp_path):
    source, destination = tmp_path / 'probe.json', tmp_path / 'provider.json'
    destination.touch()
    source.write_text('{"version":2,"calls":[]}')
    with pytest.raises(ValueError, match='Invalid spend ledger'):
        seed_provider_ledger(source, destination)
    assert destination.read_bytes() == b''
    raw = b'{"version": 1, "calls": []}\n\n'
    source.write_bytes(raw)
    seed_provider_ledger(source, destination)
    assert destination.read_bytes() == raw
