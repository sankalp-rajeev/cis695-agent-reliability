"""Reproduce the post-hoc Baseline versus Full assessment from frozen study data."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import platform
import subprocess
from dataclasses import asdict
from pathlib import Path

import numpy as np

from reconstruction import ROOT, reconstruct, explicit_high_risks
from statistics_core import (populations, confusion, transitions, paired_bootstrap, paired_exact,
                             BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED)

HERE = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_csv(path, rows, fields=None):
    fields = fields or list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fields, lineterminator="\n")
        writer.writeheader()
        for r in rows:
            writer.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (list, dict, tuple)) else v for k, v in r.items()})


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def load_inputs():
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    input_hashes, discrepancies = {}, []
    def committed(relative):
        payload = subprocess.run(["git", "show", revision + ":" + relative], cwd=ROOT, check=True, capture_output=True).stdout
        input_hashes["git:" + revision + ":" + relative] = digest(payload)
        local = ROOT / relative
        if local.exists() and local.read_bytes() != payload:
            discrepancies.append(relative + " differs locally; committed content used")
        return payload
    raw = list(csv.DictReader(io.StringIO(committed("docs/results_100.csv").decode())))
    if len({r["instance_id"] for r in raw}) != len(raw) or len(raw) != 100:
        raise ValueError("expected 100 unique committed tasks")
    evidence_report = committed("docs/results_100.md").decode()
    for name in ("decision.py", "integrity.py", "evidence.py"):
        relative = "src/reliability/verifier/" + name
        committed_code = committed(relative)
        if (ROOT / relative).read_bytes() != committed_code:
            raise ValueError("implemented policy/adapter differs from committed code: " + relative)
    risk = explicit_high_risks(evidence_report)
    rows = [reconstruct(r, risk) for r in raw]
    target = next(r for r in rows if r["instance_id"] == "pytest-dev__pytest-7432")
    path = ROOT / "runs" / target["source_run"] / "tasks" / target["instance_id"] / "oracle_record.json"
    payload = path.read_bytes()
    input_hashes[str(path.relative_to(ROOT))] = digest(payload)
    local = json.loads(payload)
    if local["instance_id"] != target["instance_id"] or local["experiment_id"] != target["source_run"]:
        raise ValueError("pytest-7432 local-record identity mismatch")
    target.update(pytest_7432_committed_oracle=target["oracle"], pytest_7432_local_oracle=local["outcome"],
        pytest_7432_note="committed resolved is authoritative; local patch_apply_failed is sensitivity only",
        pytest_7432_local_source=str(path.relative_to(ROOT)))
    metadata = dict(revision=revision, input_sha256=input_hashes, local_discrepancies=discrepancies,
        python_version=platform.python_version(), numpy_version=np.__version__,
        oracle_use="POST-HOC ANALYSIS ONLY; oracle labels never enter policy Evidence",
        risk_provenance_counts={status: sum(r["high_severity_risk_status"] == status for r in rows)
                                for status in sorted({r["high_severity_risk_status"] for r in rows})})
    return rows, metadata


def build_bundle(rows, output, metadata=None, seed=BOOTSTRAP_SEED, resamples=BOOTSTRAP_RESAMPLES):
    """Pure derived-artifact build; tests supply synthetic rows and a temp output."""
    metadata = metadata or {}
    output.mkdir(parents=True, exist_ok=True)
    pops = populations(rows)
    sensitivity = [dict(r, oracle="unresolved") if r["instance_id"] == "pytest-dev__pytest-7432" else dict(r) for r in rows]
    hypothetical = populations(sensitivity)
    pops["PYTEST7432_UNRESOLVED_HEADLINE_SENSITIVITY"] = hypothetical["HEADLINE_NONEMPTY_PRIMARY"]
    pops["PYTEST7432_UNRESOLVED_ALL_NONEMPTY_SENSITIVITY"] = hypothetical["ALL_NONEMPTY"]
    primary = pops["HEADLINE_NONEMPTY_PRIMARY"]
    boot, replicates = paired_bootstrap(primary, seed, resamples)
    paired = paired_exact(primary)
    matrices, metrics, transition_rows = [], [], []
    for name, group in pops.items():
        for policy in ("baseline", "full"):
            cm = confusion(group, policy)
            decisions = {d: sum(r[policy + "_decision"] == d for r in group) for d in ("ACCEPT", "FLAG", "REJECT")}
            matrices.append(dict(population=name, policy=policy, n=cm.n, **asdict(cm), **decisions,
                                 empty_patches=sum(r["oracle"] == "empty_patch" for r in group)))
            row = dict(population=name, policy=policy, **cm.metrics())
            interval = boot["policy_f1"][policy] if name == "HEADLINE_NONEMPTY_PRIMARY" else {}
            row.update(f1_bootstrap_low=interval.get("low"), f1_bootstrap_high=interval.get("high"),
                       f1_ci_method="paired_patch_percentile_bootstrap" if interval else "not_estimated")
            metrics.append(row)
        for (before, after, oracle), count in sorted(transitions(group).items()):
            transition_rows.append(dict(population=name, baseline_decision=before, full_decision=after,
                                        oracle=oracle, count=count))
    counts = {name: dict(n=len(group), resolved=sum(r["oracle"] == "resolved" for r in group),
                         unresolved=sum(r["oracle"] == "unresolved" for r in group),
                         empty=sum(r["oracle"] == "empty_patch" for r in group)) for name, group in pops.items()}
    facts = dict(metadata=metadata, populations=counts, bootstrap=boot, paired_tests=paired,
        bootstrap_row_order=[r["instance_id"] for r in primary],
        expectations=[dict(policy=p, expected=expected, actual=asdict(confusion(primary, p)),
                           matches=asdict(confusion(primary, p)) == expected)
            for p, expected in (("baseline", dict(tp=53, fp=11, fn=16, tn=3)),
                                ("full", dict(tp=45, fp=7, fn=24, tn=7)))])
    write_csv(output / "per_task.csv", rows)
    write_csv(output / "confusion_matrices.csv", matrices)
    write_csv(output / "metrics.csv", metrics)
    write_csv(output / "transitions.csv", transition_rows)
    write_csv(output / "bootstrap_replicates.csv", replicates)
    write_csv(output / "bootstrap_differences.csv", [dict(metric=name, **values, seed=seed, resamples=resamples)
                                                      for name, values in boot["differences"].items()])
    write_json(output / "analysis.json", facts)
    from render_report import render
    render(output, rows, matrices, metrics, facts)
    return facts


def finalize_hashes():
    outputs = {p.name: digest(p.read_bytes()) for p in sorted(HERE.iterdir()) if p.is_file()
               and p.name not in {"outputs.sha256.json", "outputs.sha256.json.sha256"}}
    write_json(HERE / "outputs.sha256.json", dict(output_sha256=outputs,
               self_hash="outputs.sha256.json.sha256; self-reference excluded"))
    (HERE / "outputs.sha256.json.sha256").write_text(digest((HERE / "outputs.sha256.json").read_bytes()) + "  outputs.sha256.json\n")


def main():
    rows, metadata = load_inputs()
    code = {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in sorted(HERE.glob("*.py"))}
    facts = build_bundle(rows, HERE, metadata)
    write_json(HERE / "inputs.json", dict(**metadata, code_sha256=code,
        bootstrap_seed=BOOTSTRAP_SEED, bootstrap_resamples=BOOTSTRAP_RESAMPLES,
        command="env -u PYTHONPATH .venv/bin/python -B reports/policy_comparison/compare.py",
        classifications_modified=False, repair_verification_or_oracle_rerun=False,
        pure_policy_reconstruction=True))
    finalize_hashes()
    print(json.dumps(dict(nonempty=facts["populations"]["ALL_NONEMPTY"],
                         primary=facts["populations"]["HEADLINE_NONEMPTY_PRIMARY"], paired_tests=facts["paired_tests"]), indent=2))


if __name__ == "__main__":
    main()
