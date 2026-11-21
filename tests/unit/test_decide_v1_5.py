"""scripts/decide_v1_5.py: offline, label-free v1.5 decisions from a sealed run."""

import csv
import hashlib
import importlib.util
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
RECORD = "verification_record.full-v1.4.1.json"


def _script():
    spec = importlib.util.spec_from_file_location("decide_v1_5", ROOT / "scripts" / "decide_v1_5.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _signal(kind, outcome, findings=None):
    data = {"kind": kind, "outcome": outcome, "detail": "x", "findings": findings or {}}
    if outcome == "NOT_AVAILABLE":
        data["absence"] = "nothing_to_check"
    return data


def _record(iid, *, v2, v4, v3="PASS", v4_findings=None, decision="FLAG"):
    return {
        "instance_id": iid, "experiment_id": "exp", "verifier_config": "full-v1.5",
        "patch_sha256": "sha256:" + "0" * 64,
        "integrity": _signal("integrity", "PASS", {"ast_analysis": []}),
        "regression": _signal("regression", v2),
        "static": _signal("static", "PASS", {"summary": {"syntax": v3}}),
        "reproduction": _signal("reproduction", v4, v4_findings),
        "decision": {"decision": decision, "policy_name": "full-v1.4",
                     "policy_version": "v1.4.1-full", "reasons": ["r"]},
        "reproduction_generator": {"generator": {"model_id": "m"}},
        "verified_at": "2026-11-20T00:00:00+00:00",
    }


def _per_requirement(counts, *, passes=2, full_pass=False):
    return {"setup": {"design": "per_requirement", "passes": passes}, "full_pass": full_pass,
            "verdict_counts": {k: counts.get(k, 0) for k in (
                "UNCOVERED", "NO_RESULT", "PASS", "FAIL_CONFIRMED", "FAIL_SINGLE")}}


def make_run(root, *, seal=True, header=None):
    root.mkdir(parents=True)
    records = {
        "a__a-1": _record("a__a-1", v2="PASS", v4="PASS", decision="ACCEPT",
                          v4_findings=_per_requirement({"PASS": 2}, full_pass=True)),
        "a__a-2": _record("a__a-2", v2="NOT_AVAILABLE", v4="FAIL",
                          v4_findings=_per_requirement({"FAIL_CONFIRMED": 1})),
        "a__a-3": _record("a__a-3", v2="PASS", v4="NOT_AVAILABLE", v3="FAIL",
                          v4_findings=_per_requirement({"PASS": 1, "UNCOVERED": 1})),
        "a__a-4": _record("a__a-4", v2="NOT_AVAILABLE", v4="PASS",
                          v4_findings=_per_requirement({"PASS": 1}, full_pass=True)),
    }
    for iid, record in records.items():
        (root / "tasks" / iid).mkdir(parents=True)
        (root / "tasks" / iid / RECORD).write_text(json.dumps(record))
    (root / "header.json").write_text(json.dumps(header or {"policy_version": "v1.4.1-full"}))
    (root / "completion.json").write_text(json.dumps({
        "status": "COMPLETE", "completed_tasks": sorted(records), "no_patch_tasks": ["a__a-4"]}))
    if seal:
        files = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in root.rglob("*") if p.is_file()}
        (root / "seal.json").write_text(json.dumps({"status": "COMPLETE", "files_sha256": files}))
    return root


def rows(path):
    with open(path, newline="") as stream:
        return {row["instance_id"]: row for row in csv.DictReader(stream)}


def test_switches_parse_and_name():
    mod = _script()
    assert mod.parse_switches("r2=0,r3=1,r6=0") == {
        "r2_v3_reject": False, "r3_extended_reject": True, "r6_accept_v2_not_available": False}
    for bad in ("r2=0,r3=1", "r2=0,r3=1,r6=2", "r2=0,r3=1,r6=0,r6=1", "x=0,r3=1,r6=0"):
        with pytest.raises(ValueError):
            mod.parse_switches(bad)


def test_switches_off_recomputes_every_task(tmp_path):
    mod = _script()
    run = make_run(tmp_path / "runs" / "study_dev_armB")
    summary = mod.decide_run(run, mod.parse_switches("r2=0,r3=0,r6=0"), tmp_path / "out")
    table = rows(summary["csv"])
    assert {k: (r["decision"], r["rule_id"], r["review_label"]) for k, r in table.items()} == {
        "a__a-1": ("ACCEPT", "R6", "none"),
        "a__a-2": ("FLAG", "R4", "likely_wrong"),
        "a__a-3": ("FLAG", "R8", "none"),
        "a__a-4": ("FLAG", "R8", "none"),
    }
    assert table["a__a-4"]["has_patch"] == "False"
    assert summary["counts"]["patch"]["decision"] == {"ACCEPT": 1, "FLAG": 2, "REJECT": 0}
    assert summary["tasks"] == 4 and summary["patch_tasks"] == 3
    assert json.loads((tmp_path / "out" / summary["summary_name"]).read_text())["switches"] == {
        "r2_v3_reject": False, "r3_extended_reject": False, "r6_accept_v2_not_available": False}


def test_switches_on_change_only_their_rules(tmp_path):
    mod = _script()
    run = make_run(tmp_path / "runs" / "study_dev_armB")
    summary = mod.decide_run(run, mod.parse_switches("r2=1,r3=1,r6=1"), tmp_path / "out")
    table = rows(summary["csv"])
    assert (table["a__a-2"]["decision"], table["a__a-2"]["rule_id"]) == ("REJECT", "R3")
    assert (table["a__a-3"]["decision"], table["a__a-3"]["rule_id"]) == ("REJECT", "R2")
    assert (table["a__a-4"]["decision"], table["a__a-4"]["rule_id"]) == ("ACCEPT", "R6")


@pytest.mark.parametrize("name", ["labels", "grading_armB", "official_label_join", "posthoc"])
def test_refuses_a_label_path(tmp_path, name):
    mod = _script()
    run = make_run(tmp_path / name / "run")
    with pytest.raises(ValueError, match="forbidden"):
        mod.decide_run(run, mod.parse_switches("r2=0,r3=0,r6=0"), tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_refuses_an_unsealed_run(tmp_path):
    mod = _script()
    run = make_run(tmp_path / "run", seal=False)
    with pytest.raises(ValueError, match="seal"):
        mod.decide_run(run, mod.parse_switches("r2=0,r3=0,r6=0"), tmp_path / "out")


def test_refuses_a_run_changed_after_its_seal(tmp_path):
    mod = _script()
    run = make_run(tmp_path / "run")
    (run / "tasks" / "a__a-1" / "extra.json").write_text("{}")
    with pytest.raises(ValueError, match="seal"):
        mod.decide_run(run, mod.parse_switches("r2=0,r3=0,r6=0"), tmp_path / "out")


def test_refuses_output_inside_the_run(tmp_path):
    mod = _script()
    run = make_run(tmp_path / "run")
    with pytest.raises(ValueError, match="inside"):
        mod.decide_run(run, mod.parse_switches("r2=0,r3=0,r6=0"), run / "out")


def test_gold_run_needs_reference_header(tmp_path):
    mod = _script()
    switches = mod.parse_switches("r2=0,r3=0,r6=0")
    plain = make_run(tmp_path / "runs" / "study_dev_gold")
    with pytest.raises(ValueError, match="forbidden"):
        mod.decide_run(plain, switches, tmp_path / "out")
    gold = make_run(tmp_path / "runs2" / "study_dev_gold",
                    header={"policy_version": "v1.4.1-full", "reference_patches": True})
    assert mod.decide_run(gold, switches, tmp_path / "out")["tasks"] == 4


def test_main_writes_csv_and_summary(tmp_path, capsys):
    mod = _script()
    run = make_run(tmp_path / "run")
    assert mod.main([str(run), "--switches", "r2=0,r3=1,r6=0", "--output", str(tmp_path / "o")]) == 0
    assert (tmp_path / "o" / "decisions_v1_5_r2-0_r3-1_r6-0.csv").is_file()
    assert (tmp_path / "o" / "summary_v1_5_r2-0_r3-1_r6-0.json").is_file()
    assert "R3" in capsys.readouterr().out
