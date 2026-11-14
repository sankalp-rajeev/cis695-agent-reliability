"""Persistent, fail-closed UM estimates; independent of DeepSeek billing."""

from __future__ import annotations

import fcntl
import json
import math
import os
import uuid
from contextlib import contextmanager
from pathlib import Path


class BudgetCap(RuntimeError):
    """Infrastructure termination, never a model failure."""

    termination = "BUDGET_CAP"


class SpendLedger:
    def __init__(self, path: Path, *, job: str, total_usd=20.0, job_usd=3.0):
        self.path = Path(path)
        self.job = job
        self.total_usd = float(total_usd)
        self.job_usd = float(job_usd)

    @contextmanager
    def locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.with_suffix(".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            data = json.loads(self.path.read_text()) if self.path.exists() else {
                "version": 1, "calls": []}
            if data.get("version") != 1 or not isinstance(data.get("calls"), list):
                raise ValueError("Invalid spend ledger; manual reconciliation required")
            yield data
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2) + "\n")
            os.replace(tmp, self.path)

    @staticmethod
    def spend(data, *, job=None, task=None):
        return sum(float(c["cost_usd"]) for c in data["calls"]
                   if (job is None or c["job"] == job)
                   and (task is None or c["task"] == task))

    def _check(self, data, amount, task=None, task_cap=None):
        if not math.isfinite(amount) or amount < 0:
            raise ValueError("Cost must be finite and nonnegative")
        if self.spend(data) + amount > self.total_usd + 1e-12:
            raise BudgetCap("account ledger budget would be exceeded")
        if self.spend(data, job=self.job) + amount > self.job_usd + 1e-12:
            raise BudgetCap("$3.00 job cap would be exceeded")
        if task_cap is not None and self.spend(data, job=self.job, task=task) + amount > task_cap + 1e-12:
            raise BudgetCap("per-task cost cap would be exceeded")

    def before_task(self, task, cap):
        with self.locked() as data:
            # Resume reserves only the unspent part of this task's cap.
            remaining = max(0.0, cap - self.spend(data, job=self.job, task=task))
            self._check(data, remaining, task, cap)
            if any(c["state"] == "reserved" for c in data["calls"]):
                raise BudgetCap("unsettled request; reconcile the ledger before resuming")

    def reserve(self, amount, *, task, task_cap, stage, model_id):
        with self.locked() as data:
            if any(c["state"] == "reserved" for c in data["calls"]):
                raise BudgetCap("unsettled request; reconcile the ledger before resuming")
            self._check(data, amount, task, task_cap)
            call_id = uuid.uuid4().hex
            data["calls"].append({"id": call_id, "job": self.job, "task": task,
                                  "stage": stage, "model_id": model_id,
                                  "state": "reserved", "cost_usd": amount})
            return call_id

    def settle(self, call_id, cost, **usage):
        if not math.isfinite(cost) or cost < 0:
            raise ValueError("Invalid response cost")
        with self.locked() as data:
            call = next(c for c in data["calls"] if c["id"] == call_id)
            if call["state"] != "reserved":
                raise ValueError("Request already settled")
            reserved = call["cost_usd"]
            call.update(usage, state="settled", cost_usd=cost)
        if cost > reserved + 1e-12:
            raise BudgetCap("response exceeded conservative reservation; stop and reconcile")

    def snapshot(self):
        with self.locked() as data:
            return json.loads(json.dumps(data))
