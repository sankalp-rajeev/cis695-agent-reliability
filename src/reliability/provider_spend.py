"""Persistent provider/account caps with a whole-stage budget escrow.

Uses the UM branch's version-1 ledger and lock discipline. Legacy entries are
UM/default-account calls; both repair arms can share a single ledger file.
"""

from __future__ import annotations

import math
import fcntl
import hashlib
import json
import os
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path

from reliability.umgpt_spend import BudgetCap, SpendLedger


def account_totals(data):
    """Recorded costs by account, including conservative unresolved reservations."""
    if data.get('version') != 1 or not isinstance(data.get('calls'), list):
        raise ValueError('Invalid spend ledger; manual reconciliation required')
    totals = {}
    for call in data['calls']:
        cost = float(call['cost_usd'])
        if not math.isfinite(cost) or cost < 0:
            raise ValueError('Invalid ledger cost')
        key = (call.get('provider', 'umgpt'), call.get('account', 'default'))
        totals[key] = totals.get(key, 0.0) + cost
    return [{'provider': provider, 'account': account, 'spent_usd': spent}
            for (provider, account), spent in sorted(totals.items())]


def seed_provider_ledger(source, destination):
    """Seed once from legacy bytes under the destination ledger's normal lock."""
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination:
        raise ValueError('Source and destination ledger must differ')
    raw = source.read_bytes()
    totals = account_totals(json.loads(raw))
    expected = hashlib.sha256(raw).hexdigest()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if destination.exists() and destination.stat().st_size:
            raise ValueError('Refusing to overwrite a non-empty ledger')
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(raw)
            if hashlib.sha256(temporary.read_bytes()).hexdigest() != expected:
                raise ValueError('Ledger copy SHA-256 mismatch')
            os.replace(temporary, destination)
            if hashlib.sha256(destination.read_bytes()).hexdigest() != expected:
                raise ValueError('Ledger copy SHA-256 mismatch')
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return {'source': str(source), 'destination': str(destination), 'sha256': expected,
            'accounts': totals}


class AuthStop(BudgetCap):
    termination = 'AUTH_ERROR'


class ProviderLedger(SpendLedger):
    def __init__(self, path, *, provider, job, total_usd, job_usd, account='default'):
        super().__init__(path, job=job, total_usd=total_usd, job_usd=job_usd)
        if provider not in ('umgpt', 'deepseek'):
            raise ValueError('Unsupported paid provider')
        if not all(math.isfinite(x) and x >= 0 for x in (self.total_usd, self.job_usd)):
            raise ValueError('Invalid spend cap')
        self.provider, self.account, self.stage_id = provider, account, None

    def owns(self, row):
        return row.get('provider', 'umgpt') == self.provider and row.get('account', 'default') == self.account

    def account_calls(self, data):
        return [c for c in data['calls'] if self.owns(c)]

    def _total(self, data, *, job=None):
        calls = sum(float(c['cost_usd']) for c in self.account_calls(data) if job is None or c['job'] == job)
        holds = sum(float(h['remaining_usd']) for h in data.get('stage_escrows', [])
                    if self.owns(h) and h['state'] == 'active' and (job is None or h['job'] == job))
        return calls + holds

    def _budget_check(self, data, amount):
        if not math.isfinite(amount) or amount < 0:
            raise ValueError('Cost must be finite and nonnegative')
        if self._total(data) + amount > self.total_usd + 1e-12:
            raise BudgetCap(self.provider + ' account ledger budget would be exceeded')
        if self._total(data, job=self.job) + amount > self.job_usd + 1e-12:
            raise BudgetCap(self.provider + ' run budget would be exceeded')

    def check_current_budget(self, data):
        """Stop an attempt below existing commitments before any paid work."""
        self._budget_check(data, 0.0)

    @contextmanager
    def stage(self, task, stage, maximum_usd):
        """Reserve the complete stage ceiling before its first paid call."""
        if self.stage_id is not None:
            raise ValueError('Nested paid stages are unsupported')
        with self.locked() as data:
            if any(c['state'] == 'reserved' for c in self.account_calls(data)) or any(
                self.owns(h) and h['state'] == 'active' for h in data.get('stage_escrows', [])):
                raise BudgetCap('Unsettled paid stage/request; reconcile before resuming')
            spent = sum(c['cost_usd'] for c in self.account_calls(data)
                        if c['job'] == self.job and c['task'] == task and c['stage'] == stage)
            if spent > 1e-12:
                raise BudgetCap('A full fresh stage would reset its already-used per-task ceiling')
            self._budget_check(data, maximum_usd)
            token = uuid.uuid4().hex
            data.setdefault('stage_escrows', []).append({'id': token, 'provider': self.provider,
                'account': self.account, 'job': self.job, 'task': task, 'stage': stage,
                'maximum_usd': maximum_usd, 'remaining_usd': maximum_usd, 'state': 'active'})
        self.stage_id = token
        try:
            yield
        finally:
            with self.locked() as data:
                hold = next(h for h in data['stage_escrows'] if h['id'] == token)
                hold.update(state='closed', remaining_usd=0.0)
            self.stage_id = None

    def reserve(self, amount, *, task, task_cap, stage, model_id):
        if not math.isfinite(amount) or amount < 0:
            raise ValueError('Cost must be finite and nonnegative')
        with self.locked() as data:
            calls = self.account_calls(data)
            if any(c['state'] == 'reserved' for c in calls):
                raise BudgetCap('Unsettled paid request; reconcile before resuming')
            stage_spent = sum(c['cost_usd'] for c in calls if c['job'] == self.job
                              and c['task'] == task and c['stage'] == stage)
            if stage_spent + amount > task_cap + 1e-12:
                raise BudgetCap('Per-stage cost cap would be exceeded')
            hold = next((h for h in data.get('stage_escrows', []) if h['id'] == self.stage_id), None)
            if hold is not None:
                if hold['task'] != task or hold['stage'] != stage or hold['state'] != 'active':
                    raise ValueError('Paid stage escrow identity mismatch')
                if amount > hold['remaining_usd'] + 1e-12:
                    raise BudgetCap('Per-stage conservative request exceeds its remaining ceiling')
                hold['remaining_usd'] -= amount
            else:
                self._budget_check(data, amount)
            call_id = uuid.uuid4().hex
            data['calls'].append({'id': call_id, 'job': self.job, 'task': task, 'stage': stage,
                'model_id': model_id, 'provider': self.provider, 'account': self.account,
                'escrow_id': self.stage_id, 'state': 'reserved', 'cost_usd': amount})
            return call_id

    def settle(self, call_id, cost, **usage):
        if not math.isfinite(cost) or cost < 0:
            raise ValueError('Invalid response cost')
        with self.locked() as data:
            call = next(c for c in data['calls'] if c['id'] == call_id)
            if not self.owns(call) or call['state'] != 'reserved':
                raise ValueError('Wrong account or already-settled request')
            reserved = call['cost_usd']
            hold = next((h for h in data.get('stage_escrows', []) if h['id'] == call.get('escrow_id')), None)
            if hold is not None and hold['state'] == 'active':
                hold['remaining_usd'] += reserved - cost
            call.update(usage, state='settled', cost_usd=cost)
        if cost > reserved + 1e-12:
            raise BudgetCap('Response exceeded conservative reservation; stop and reconcile')
