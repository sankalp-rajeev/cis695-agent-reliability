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
        "r2_v3_reject": False, "r3_extended_reject": True, "r6_accept_v2_not_available": False,
        "r6b_accept_one_uncovered": False}
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
        "r2_v3_reject": False, "r3_extended_reject": False, "r6_accept_v2_not_available": False,
        "r6b_accept_one_uncovered": False}


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


FROZEN_CONFIG = ("v1_5:\n  decision_policy: full-v1.5\n  r2_v3_reject: true\n"
                 "  r3_extended_reject: false\n  r6_accept_v2_not_available: true\n")


def _git(repo, *args):
    import subprocess
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t",
                    *args], check=True, capture_output=True)


def make_repo(tmp_path, *, tag=None):
    repo = tmp_path / "repo"
    (repo / "configs" / "verifier").mkdir(parents=True)
    (repo / "configs" / "verifier" / "v1_5.yaml").write_text(FROZEN_CONFIG)
    _git(repo, "init", "-q")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "c")
    if tag == "annotated":
        _git(repo, "tag", "-a", "v1.5-frozen", "-m", "freeze")
    elif tag == "lightweight":
        _git(repo, "tag", "v1.5-frozen")
    # A later edit must not leak into the frozen switches.
    (repo / "configs" / "verifier" / "v1_5.yaml").write_text(FROZEN_CONFIG.replace("true", "false"))
    return repo


def test_frozen_reads_switches_at_the_annotated_tag(tmp_path):
    import subprocess
    mod = _script()
    repo = make_repo(tmp_path, tag="annotated")
    switches, frozen = mod.frozen_switches(repo)
    assert switches == {"r2_v3_reject": True, "r3_extended_reject": False,
                        "r6_accept_v2_not_available": True, "r6b_accept_one_uncovered": False}
    commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    assert frozen == {"tag": "v1.5-frozen", "tag_commit": commit,
                      "config_path": "configs/verifier/v1_5.yaml",
                      "config_sha256": hashlib.sha256(FROZEN_CONFIG.encode()).hexdigest()}


def test_frozen_refuses_a_missing_tag(tmp_path):
    mod = _script()
    with pytest.raises(ValueError, match="missing"):
        mod.frozen_switches(make_repo(tmp_path))


def test_frozen_refuses_a_lightweight_tag(tmp_path):
    mod = _script()
    with pytest.raises(ValueError, match="annotated"):
        mod.frozen_switches(make_repo(tmp_path, tag="lightweight"))


def test_frozen_summary_records_the_tag(tmp_path, monkeypatch):
    mod = _script()
    repo = make_repo(tmp_path, tag="annotated")
    monkeypatch.setattr(mod, "ROOT", repo)
    run = make_run(tmp_path / "run")
    assert mod.main([str(run), "--frozen", "--output", str(tmp_path / "o")]) == 0
    summary = json.loads((tmp_path / "o" / "summary_v1_5_r2-1_r3-0_r6-1.json").read_text())
    assert summary["frozen"]["tag"] == "v1.5-frozen"
    assert summary["frozen"]["config_sha256"] == hashlib.sha256(FROZEN_CONFIG.encode()).hexdigest()
    assert summary["switches"]["r2_v3_reject"] is True


def test_frozen_and_switches_are_mutually_exclusive(tmp_path, capsys):
    mod = _script()
    run = make_run(tmp_path / "run")
    with pytest.raises(SystemExit):
        mod.main([str(run), "--frozen", "--switches", "r2=0,r3=0,r6=0", "--output", str(tmp_path / "o")])
    with pytest.raises(SystemExit):
        mod.main([str(run), "--output", str(tmp_path / "o")])
    assert not (tmp_path / "o").exists()


def test_help_names_frozen_for_headline_results(capsys):
    mod = _script()
    with pytest.raises(SystemExit):
        mod.main(["--help"])
    text = " ".join(capsys.readouterr().out.split())
    assert ("Headline results use --frozen only; --switches is for Phase 7 calibration "
            "and Phase 16 ablations.") in text


# Amendment A4 (v): --no-v2-fallback, V2 recomputed without fallback-selected tests.

def _selection(tests, fallback):
    return {"tests": tests, "by_tier": {}, "fallback_used": bool(fallback),
            "fallback_tests": fallback, "fallback_candidates_total": len(fallback)}


def make_fallback_run(root, selections, *, v2="FAIL", record_overrides=None):
    """One task per entry of `selections` (None: no selection.json), V4 full pass."""
    root.mkdir(parents=True)
    for iid, selection in selections.items():
        record = _record(iid, v2=v2, v4="PASS", decision="FLAG",
                         v4_findings=_per_requirement({"PASS": 1}, full_pass=True))
        record.update((record_overrides or {}).get(iid, {}))
        folder = root / "tasks" / iid
        (folder / "verification").mkdir(parents=True)
        if selection is not None:
            raw = json.dumps(selection).encode()
            (folder / "verification" / "selection.json").write_bytes(raw)
            record["selection_sha256"] = hashlib.sha256(raw).hexdigest()
        (folder / RECORD).write_text(json.dumps(record))
    (root / "header.json").write_text(json.dumps({"policy_version": "v1.4.1-full"}))
    (root / "completion.json").write_text(json.dumps({
        "status": "COMPLETE", "completed_tasks": sorted(selections), "no_patch_tasks": []}))
    files = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in root.rglob("*") if p.is_file()}
    (root / "seal.json").write_text(json.dumps({"status": "COMPLETE", "files_sha256": files}))
    return root


def test_no_v2_fallback_makes_fallback_only_v2_nothing_to_check(tmp_path):
    mod = _script()
    run = make_fallback_run(tmp_path / "run", {
        "b__b-1": _selection(["t.py::a", "t.py::b"], ["t.py::a", "t.py::b"]),
        "b__b-2": _selection(["u.py::a"], []),
    })
    off = mod.parse_switches("r2=0,r3=0,r6=0")
    with_fallback = rows(mod.decide_run(run, off, tmp_path / "with")["csv"])
    assert (with_fallback["b__b-1"]["v2"], with_fallback["b__b-1"]["rule_id"]) == ("FAIL", "R5")
    summary = mod.decide_run(run, off, tmp_path / "without", v2_fallback=False)
    table = rows(summary["csv"])
    assert (table["b__b-1"]["v2"], table["b__b-1"]["v2_absence"]) == ("NOT_AVAILABLE",
                                                                      "nothing_to_check")
    assert table["b__b-1"]["v2_fallback_removed"] == "True"
    assert (table["b__b-1"]["decision"], table["b__b-1"]["rule_id"]) == ("FLAG", "R8")
    assert (table["b__b-2"]["v2"], table["b__b-2"]["rule_id"]) == ("FAIL", "R5")
    assert table["b__b-2"]["v2_fallback_removed"] == "False"
    assert summary["v2_fallback"] is False
    assert summary["summary_name"] == "summary_v1_5_r2-0_r3-0_r6-0_v2-nofallback.json"
    assert pathlib.Path(summary["csv"]).name == "decisions_v1_5_r2-0_r3-0_r6-0_v2-nofallback.csv"
    on = mod.decide_run(run, mod.parse_switches("r2=0,r3=0,r6=1"), tmp_path / "on", v2_fallback=False)
    assert rows(on["csv"])["b__b-1"]["rule_id"] == "R6"


def test_no_v2_fallback_without_selection_keeps_an_absent_v2(tmp_path):
    mod = _script()
    run = make_fallback_run(tmp_path / "run", {"b__b-1": None}, v2="NOT_AVAILABLE")
    table = rows(mod.decide_run(run, mod.parse_switches("r2=0,r3=0,r6=0"), tmp_path / "o",
                                v2_fallback=False)["csv"])
    assert (table["b__b-1"]["v2"], table["b__b-1"]["v2_fallback_removed"]) == ("NOT_AVAILABLE", "False")


@pytest.mark.parametrize("selection,match", [
    (None, "cannot tell"),
    ({"tests": ["t.py::a"], "by_tier": {}}, "cannot tell"),
    (_selection(["t.py::a", "u.py::b"], ["t.py::a"]), "mixes"),
    (_selection(["t.py::a"], ["u.py::b"]), "mixes"),
], ids=["no-selection-but-v2-ran", "no-fallback-fields", "mixed", "fallback-not-selected"])
def test_no_v2_fallback_refuses_instead_of_guessing(tmp_path, selection, match):
    mod = _script()
    run = make_fallback_run(tmp_path / "run", {"b__b-1": selection})
    with pytest.raises(ValueError, match=match):
        mod.decide_run(run, mod.parse_switches("r2=0,r3=0,r6=0"), tmp_path / "o", v2_fallback=False)
    assert not (tmp_path / "o").exists()


def test_no_v2_fallback_checks_the_selection_hash(tmp_path):
    mod = _script()
    run = make_fallback_run(tmp_path / "run", {"b__b-1": _selection(["t.py::a"], ["t.py::a"])},
                            record_overrides={"b__b-1": {}})
    record_path = run / "tasks" / "b__b-1" / RECORD
    record = json.loads(record_path.read_text())
    record["selection_sha256"] = "0" * 64
    record_path.write_text(json.dumps(record))
    seal = json.loads((run / "seal.json").read_text())
    seal["files_sha256"][f"tasks/b__b-1/{RECORD}"] = hashlib.sha256(record_path.read_bytes()).hexdigest()
    (run / "seal.json").write_text(json.dumps(seal))
    with pytest.raises(ValueError, match="selection"):
        mod.decide_run(run, mod.parse_switches("r2=0,r3=0,r6=0"), tmp_path / "o", v2_fallback=False)


def test_main_accepts_no_v2_fallback(tmp_path):
    mod = _script()
    run = make_fallback_run(tmp_path / "run", {"b__b-1": _selection(["t.py::a"], ["t.py::a"])})
    assert mod.main([str(run), "--switches", "r2=0,r3=0,r6=0", "--no-v2-fallback",
                     "--output", str(tmp_path / "o")]) == 0
    summary = json.loads((tmp_path / "o" / "summary_v1_5_r2-0_r3-0_r6-0_v2-nofallback.json").read_text())
    assert summary["v2_fallback"] is False
    assert mod.main([str(run), "--switches", "r2=0,r3=0,r6=0", "--output", str(tmp_path / "p")]) == 0
    assert json.loads((tmp_path / "p" / "summary_v1_5_r2-0_r3-0_r6-0.json").read_text())["v2_fallback"]


# Amendment A6: V3 recomputed from stored base and patched checks.

def _v3_findings(path, base_status, exc="TypeError"):
    tb = (f'Traceback (most recent call last):\n  File "<string>", line 1, in <module>\n'
          f'  File "/testbed/{path}", line 3, in <module>\n    x()\n{exc}: boom\n')
    module = path[:-3].replace("/", ".")
    imp = {"kind": "import", "status": "FAIL", "command": ["python", "-c", "import " + module],
           "exit_code": 1, "stdout": "", "stderr": tb,
           "base_result": {"status": base_status, "exit_code": int(base_status == "FAIL"), "stdout": "",
                           "stderr": tb if base_status == "FAIL" else ""}}
    return {"summary": {"syntax": "PASS", "import": "FAIL"}, "v3_absolute_failure": True,
            "checks": [imp]}


@pytest.mark.parametrize("base_status,added,expected", [
    ("FAIL", False, ("False", "import", "")),
    ("PASS", False, ("True", "", "")),
    ("FAIL", True, ("False", "", "import")),
], ids=["pre-existing", "real", "patch-added-module"])
def test_v3_is_recomputed_with_added_files_from_the_sealed_patch(tmp_path, base_status, added, expected):
    mod = _script()
    root = tmp_path / "run"
    root.mkdir()
    record = _record("c__c-1", v2="PASS", v4="PASS", decision="FLAG",
                     v4_findings=_per_requirement({"PASS": 1}, full_pass=True))
    record["static"]["outcome"] = "FAIL"
    record["static"]["findings"] = _v3_findings("pkg/mod.py", base_status)
    folder = root / "tasks" / "c__c-1"
    folder.mkdir(parents=True)
    (folder / RECORD).write_text(json.dumps(record))
    header = "new file mode 100644\n--- /dev/null\n" if added else "--- a/pkg/mod.py\n"
    (folder / "patch.diff").write_text("diff --git a/pkg/mod.py b/pkg/mod.py\n" + header +
                                       "+++ b/pkg/mod.py\n@@ -0,0 +1 @@\n+x = 1\n")
    (root / "header.json").write_text(json.dumps({"policy_version": "v1.4.1-full"}))
    (root / "completion.json").write_text(json.dumps({
        "status": "COMPLETE", "completed_tasks": ["c__c-1"], "no_patch_tasks": []}))
    files = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in root.rglob("*") if p.is_file()}
    (root / "seal.json").write_text(json.dumps({"status": "COMPLETE", "files_sha256": files}))
    row = rows(mod.decide_run(root, mod.parse_switches("r2=1,r3=0,r6=0"), tmp_path / "o")["csv"])["c__c-1"]
    assert (row["v3_absolute_failure"], row["v3_pre_existing"], row["v3_base_unknown"]) == expected
    assert (row["rule_id"] == "R2") is (expected[0] == "True")


# Amendment A8: r6b is an optional fourth switch.

def test_r6b_switch_parses_and_names_files(tmp_path):
    mod = _script()
    assert mod.parse_switches("r2=0,r3=0,r6=0")["r6b_accept_one_uncovered"] is False
    assert mod.parse_switches("r2=1,r3=0,r6=1,r6b=1")["r6b_accept_one_uncovered"] is True
    for bad in ("r2=0,r3=0,r6=0,r6b=2", "r2=0,r3=0,r6=0,r6b=1,r6b=0", "r2=0,r3=0,r6b=1"):
        with pytest.raises(ValueError):
            mod.parse_switches(bad)
    assert mod.tag(mod.parse_switches("r2=1,r3=0,r6=1,r6b=1")) == "r2-1_r3-0_r6-1_r6b-1"
    assert mod.tag(mod.parse_switches("r2=1,r3=0,r6=1")) == "r2-1_r3-0_r6-1"
    root = tmp_path / "run"
    root.mkdir()
    record = _record("d__d-1", v2="PASS", v4="NOT_AVAILABLE", decision="FLAG",
                     v4_findings=_per_requirement({"PASS": 2, "UNCOVERED": 1}, passes=1))
    (root / "tasks" / "d__d-1").mkdir(parents=True)
    (root / "tasks" / "d__d-1" / RECORD).write_text(json.dumps(record))
    (root / "header.json").write_text(json.dumps({"policy_version": "v1.4.1-full"}))
    (root / "completion.json").write_text(json.dumps({
        "status": "COMPLETE", "completed_tasks": ["d__d-1"], "no_patch_tasks": []}))
    files = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in root.rglob("*") if p.is_file()}
    (root / "seal.json").write_text(json.dumps({"status": "COMPLETE", "files_sha256": files}))
    off = rows(mod.decide_run(root, mod.parse_switches("r2=0,r3=0,r6=0"), tmp_path / "a")["csv"])["d__d-1"]
    on = rows(mod.decide_run(root, mod.parse_switches("r2=0,r3=0,r6=0,r6b=1"), tmp_path / "b")["csv"])["d__d-1"]
    assert (off["rule_id"], on["rule_id"], on["decision"]) == ("R7", "R6b", "ACCEPT")
    assert on["v4_uncovered_units"] == "1"


def test_added_paths_tolerates_a_patch_v1_could_not_parse(tmp_path):
    # V1 already fails an unparseable patch (R1); A6 then has no added files to use.
    mod = _script()
    root = tmp_path / "run"
    (root / "tasks" / "e__e-1").mkdir(parents=True)
    (root / "tasks" / "e__e-1" / "patch.diff").write_text("--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-a\n+b\n")
    files = {"tasks/e__e-1/patch.diff": hashlib.sha256(
        (root / "tasks" / "e__e-1" / "patch.diff").read_bytes()).hexdigest()}
    assert mod.added_paths(root, files, "e__e-1") == ()
