"""decide_v1_5.py (amendment B9): report instead of crashing, and decide a merged set of
tasks kept from a stopped run plus a rerun."""

import hashlib
import json

import pytest

from tests.unit.test_decide_v1_5 import RECORD, _per_requirement, _record, _script, rows

SWITCHES = "r2=0,r3=0,r6=0"


def build(root, ids, *, status="COMPLETE", completions=None, seal=True):
    root.mkdir(parents=True)
    for iid in ids:
        (root / "tasks" / iid).mkdir(parents=True)
        record = _record(iid, v2="PASS", v4="PASS", decision="ACCEPT",
                         v4_findings=_per_requirement({"PASS": 2}, full_pass=True))
        (root / "tasks" / iid / RECORD).write_text(json.dumps(record))
    for iid, complete in (completions or {}).items():
        (root / "tasks" / iid / "task_completion.json").write_text(json.dumps({"complete": complete}))
    (root / "header.json").write_text(json.dumps({"policy_version": "v1.4.1-full"}))
    (root / "completion.json").write_text(json.dumps({
        "status": status, "completed_tasks": list(ids), "no_patch_tasks": []}))
    if seal:
        files = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in root.rglob("*") if p.is_file()}
        (root / "seal.json").write_text(json.dumps({"status": status, "files_sha256": files}))
    return root


def runs(tmp_path, *, kept_ids=("a__a-1", "a__a-2"), completions=None):
    kept = build(tmp_path / "stopped", ("a__a-1", "a__a-2", "a__a-3"), status="STOPPED_SYSTEMIC",
                 completions=completions if completions is not None
                 else {"a__a-1": True, "a__a-2": True, "a__a-3": True})
    rerun = build(tmp_path / "rerun", ("a__a-3", "a__a-4"))
    return kept, rerun, list(kept_ids)


def test_merged_decisions_cover_kept_and_rerun_tasks_and_name_their_source(tmp_path):
    mod = _script()
    kept, rerun, kept_ids = runs(tmp_path)
    expected = ["a__a-1", "a__a-2", "a__a-3", "a__a-4"]
    summary = mod.decide_run(rerun, mod.parse_switches(SWITCHES), tmp_path / "out",
                             kept=(kept, kept_ids), expected_ids=expected)
    assert summary["tasks"] == 4
    assert summary["sources"] == {"a__a-1": str(kept), "a__a-2": str(kept),
                                  "a__a-3": str(rerun), "a__a-4": str(rerun)}
    table = rows(summary["csv"])
    assert {i: r["source_run"] for i, r in table.items()} == summary["sources"]


def test_merge_refuses_a_task_from_both_runs(tmp_path):
    mod = _script()
    kept, rerun, _ = runs(tmp_path)
    with pytest.raises(ValueError, match="duplicate"):
        mod.decide_run(rerun, mod.parse_switches(SWITCHES), tmp_path / "out",
                       kept=(kept, ["a__a-1", "a__a-3"]), expected_ids=["a__a-1", "a__a-3", "a__a-4"])


def test_merge_requires_exactly_the_expected_ids(tmp_path):
    mod = _script()
    kept, rerun, kept_ids = runs(tmp_path)
    with pytest.raises(ValueError, match="exactly"):
        mod.decide_run(rerun, mod.parse_switches(SWITCHES), tmp_path / "out",
                       kept=(kept, kept_ids), expected_ids=["a__a-1", "a__a-2", "a__a-3", "a__a-4", "a__a-5"])


@pytest.mark.parametrize("completions", [{"a__a-1": True}, {"a__a-1": True, "a__a-2": False}],
                         ids=["missing", "incomplete"])
def test_merge_refuses_a_kept_task_without_a_complete_completion_file(tmp_path, completions):
    mod = _script()
    kept, rerun, kept_ids = runs(tmp_path, completions=completions)
    with pytest.raises(ValueError, match="completion"):
        mod.decide_run(rerun, mod.parse_switches(SWITCHES), tmp_path / "out",
                       kept=(kept, kept_ids), expected_ids=["a__a-1", "a__a-2", "a__a-3", "a__a-4"])


def test_main_reports_instead_of_crashing_on_an_unsealed_run(tmp_path, capsys):
    mod = _script()
    run = build(tmp_path / "run", ("a__a-1",), seal=False)
    assert mod.main([str(run), "--switches", SWITCHES, "--output", str(tmp_path / "o")]) == 2
    err = capsys.readouterr().err
    assert "cannot decide" in err and "seal" in err and "Traceback" not in err


def test_main_reports_instead_of_crashing_on_a_missing_completion_file(tmp_path, capsys):
    mod = _script()
    kept, rerun, kept_ids = runs(tmp_path, completions={"a__a-1": True})
    (tmp_path / "kept.json").write_text(json.dumps(kept_ids))
    (tmp_path / "all.json").write_text(json.dumps(["a__a-1", "a__a-2", "a__a-3", "a__a-4"]))
    code = mod.main([str(rerun), "--switches", SWITCHES, "--output", str(tmp_path / "o"),
                     "--kept-run", str(kept), "--kept-ids", str(tmp_path / "kept.json"),
                     "--expect-ids", str(tmp_path / "all.json")])
    assert code == 2
    assert "completion" in capsys.readouterr().err


def test_main_merges_from_the_command_line(tmp_path, capsys):
    mod = _script()
    kept, rerun, kept_ids = runs(tmp_path)
    (tmp_path / "kept.json").write_text(json.dumps(kept_ids))
    (tmp_path / "all.json").write_text(json.dumps(["a__a-1", "a__a-2", "a__a-3", "a__a-4"]))
    assert mod.main([str(rerun), "--switches", SWITCHES, "--output", str(tmp_path / "o"),
                     "--kept-run", str(kept), "--kept-ids", str(tmp_path / "kept.json"),
                     "--expect-ids", str(tmp_path / "all.json")]) == 0
    assert "4 tasks" in capsys.readouterr().out
