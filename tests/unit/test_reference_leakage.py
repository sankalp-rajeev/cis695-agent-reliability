import hashlib
import io
import json
import tarfile
from types import SimpleNamespace

import pytest

from scripts import audit_leakage

from reliability.benchmark import loader
from reliability.verifier.task_specs import sha, write

IID = "demo__repo-1"
EXCLUSIVE = "retry_policy accepts recovery from an expired cursor"
ISSUE_LINE = "the documented cursor parameter is allowed to be missing"
REMOVED = "the old behavior returned an empty page every time"
BASE = "def process_the_existing_cursor_with_default_timeout():"
SHORT = "return False"


def test_reference_audit_scans_generator_calls_and_redacts_hits(tmp_path, monkeypatch, capsys):
    run = tmp_path / "reference_run"
    task = run / "tasks" / IID
    archive = tmp_path / "canonical.tar"
    with tarfile.open(archive, "w") as stream:
        data = ("    " + BASE + "\n").encode()
        member = tarfile.TarInfo("src/module.py")
        member.size = len(data)
        stream.addfile(member, io.BytesIO(data))

    phase = task / "verification/v4"
    patch = task / "patch.diff"
    patch.parent.mkdir(parents=True)
    patch.write_text("\n".join([
        "--- a/original_module.py", "+++ b/newly_created_source_file.py", "@@ -1 +1,5 @@",
        "- " + REMOVED, "+  " + REMOVED, "+  " + ISSUE_LINE, "+\t" + BASE,
        "+" + SHORT, "+" + EXCLUSIVE.replace(" ", "   ", 1),
    ]))
    registry = tmp_path / "registry.json"
    write(registry, {"tasks": [{"instance_id": IID, "archive": {"path": str(archive), "sha256": sha(archive)}}]})
    write(run / "header.json", {
        "reference_patches": True, "registry_sha256": {str(registry): sha(registry)},
        "verify_only_inputs": {IID: {"sha256": sha(patch)}},
    })
    monkeypatch.setattr(loader, "load_agent_tasks", lambda: (
        SimpleNamespace(instance_id=IID, problem_statement="Issue details: " + ISSUE_LINE.replace(" ", "\t")),
    ))

    def trajectory(name, rows):
        path = phase / name / "generator/generation_trajectory.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))

    trajectory("requirements", [
        {"role": "system", "content": ISSUE_LINE},
        {"role": "user", "content": REMOVED},
    ])
    trajectory("pass_1", [{"role": "assistant", "content": BASE + "\n" + SHORT}])
    trajectory("pass_2", [{"role": "system", "content": "Test instructions"}])
    assert audit_leakage.main(["--runs", str(run)]) == 0
    result = capsys.readouterr().out
    assert f"task={IID} count=1" in result
    assert "GOLD_LINE_IN_GENERATOR" not in result

    trajectory("pass_2", [
        {"role": "system", "content": "Test instructions"},
        {"role": "tool", "content": json.dumps({"stdout": EXCLUSIVE.replace(" ", "\t")})},
    ])
    assert audit_leakage.main(["--runs", str(run)]) == 1
    result = capsys.readouterr().out
    digest = hashlib.sha256(EXCLUSIVE.encode()).hexdigest()
    assert "[confirmed] GOLD_LINE_LEAK" in result
    assert f"task={IID} conversation=pass_2 message_index=2 sha256={digest}" in result
    assert f"task={IID} count=1" in result
    assert all(line not in result for line in (EXCLUSIVE, ISSUE_LINE, REMOVED, BASE, SHORT))


# Amendment A3: first-appearance classification for reference runs.

DIGEST = hashlib.sha256(EXCLUSIVE.encode()).hexdigest()


def reference_run(tmp_path, monkeypatch, conversations, *, requirements_json=None, tests=None):
    """A sealed-layout reference run with one task. `conversations` maps a
    conversation name to its messages; `tests` maps a kept test file name to
    (content, kept)."""
    run = tmp_path / "reference_run"
    task = run / "tasks" / IID
    archive = tmp_path / "canonical.tar"
    with tarfile.open(archive, "w") as stream:
        data = b"unrelated = 1\n"
        member = tarfile.TarInfo("src/module.py")
        member.size = len(data)
        stream.addfile(member, io.BytesIO(data))
    v4 = task / "verification/v4"
    patch = task / "patch.diff"
    patch.parent.mkdir(parents=True)
    patch.write_text("--- a/m.py\n+++ b/m.py\n@@ -1 +1 @@\n+" + EXCLUSIVE + "\n")
    registry = tmp_path / "registry.json"
    write(registry, {"tasks": [{"instance_id": IID, "archive": {"path": str(archive), "sha256": sha(archive)}}]})
    write(run / "header.json", {
        "reference_patches": True, "registry_sha256": {str(registry): sha(registry)},
        "verify_only_inputs": {IID: {"sha256": sha(patch)}},
    })
    monkeypatch.setattr(loader, "load_agent_tasks", lambda: (
        SimpleNamespace(instance_id=IID, problem_statement="An unrelated issue text."),))
    for name, rows in conversations.items():
        path = v4 / name / "generator/generation_trajectory.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    if requirements_json is not None:
        (v4 / "requirements.json").write_text(requirements_json)
    frozen_tests = []
    for name, (content, kept) in (tests or {}).items():
        if kept:
            (v4 / "tests").mkdir(parents=True, exist_ok=True)
            (v4 / "tests" / name).write_text(content)
        frozen_tests.append({"path": "v4_repro/" + name, "kept": kept, "sha256": "sha256:" + hashlib.sha256(
            content.encode()).hexdigest()})
    write(v4 / "frozen.json", {"generation_calls": [{"call": n} for n in conversations],
                               "tests": frozen_tests})
    return run


def prompt(text="Write tests."):
    return [{"role": "system", "content": "You write tests."}, {"role": "user", "content": text}]


def assistant(**fields):
    return {"role": "assistant", "content": "", **fields}


def tool(text):
    return {"role": "tool", "tool_call_id": "c1", "content": text}


def run_audit(run, tmp_path, capsys):
    summary = tmp_path / "summary.json"
    code = audit_leakage.main(["--runs", str(run), "--reference-summary", str(summary)])
    return code, capsys.readouterr().out, json.loads(summary.read_text())


@pytest.mark.parametrize("message", [
    assistant(content="I will add " + EXCLUSIVE),
    assistant(reasoning_content="Maybe the fix is " + EXCLUSIVE),
    assistant(tool_calls=[{"id": "c1", "type": "function", "function": {
        "name": "bash", "arguments": json.dumps({"command": "echo '" + EXCLUSIVE + "' > /tmp/x"})}}]),
], ids=["content", "reasoning", "tool-call-args"])
def test_model_written_first_appearance_is_recall_not_failure(tmp_path, monkeypatch, capsys, message):
    run = reference_run(tmp_path, monkeypatch, {
        "requirements": prompt(),
        # The model's own text first, then a tool output echoing it back.
        "pass_1": prompt() + [message, tool("0\n" + EXCLUSIVE)],
    })
    code, out, summary = run_audit(run, tmp_path, capsys)
    assert code == 0
    assert "[recorded] GENERATOR_RECALL" in out and "GOLD_LINE_LEAK" not in out
    assert f"task={IID} conversation=pass_1 message_index=3 sha256={DIGEST}" in out
    task = summary["tasks"][0]
    assert task["instance_id"] == IID and task["recall_lines"] == [DIGEST]
    assert task["recall_messages"] == [{"conversation": "pass_1", "message_index": 3},
                                       {"conversation": "pass_1", "message_index": 4}]
    assert task["leak_lines"] == [] and task["frozen_test_lines"] == []
    assert EXCLUSIVE not in out and EXCLUSIVE not in json.dumps(summary)


@pytest.mark.parametrize("first", [
    tool("0\n" + EXCLUSIVE),
    {"role": "user", "content": "Format error. " + EXCLUSIVE},
    assistant(content="ok", extra={"response": EXCLUSIVE}),
], ids=["tool-output", "later-user-message", "assistant-extra-only"])
def test_first_appearance_outside_model_text_is_a_confirmed_leak(tmp_path, monkeypatch, capsys, first):
    run = reference_run(tmp_path, monkeypatch, {
        "requirements": prompt(),
        "pass_1": prompt() + [assistant(content="looking"), first, assistant(content=EXCLUSIVE)],
    })
    code, out, summary = run_audit(run, tmp_path, capsys)
    assert code == 1
    assert "[confirmed] GOLD_LINE_LEAK" in out
    assert f"task={IID} conversation=pass_1 message_index=4 sha256={DIGEST}" in out
    assert summary["tasks"][0]["leak_lines"] == [DIGEST]
    assert summary["tasks"][0]["recall_lines"] == []


def test_first_appearance_is_judged_per_conversation(tmp_path, monkeypatch, capsys):
    # The model wrote it in the requirements conversation, but pass_1 first
    # sees it in a tool output: that conversation was handed the line.
    run = reference_run(tmp_path, monkeypatch, {
        "requirements": prompt() + [assistant(content=EXCLUSIVE)],
        "pass_1": prompt() + [assistant(content="x"), tool("0\n" + EXCLUSIVE)],
    })
    code, out, summary = run_audit(run, tmp_path, capsys)
    assert code == 1
    assert "conversation=requirements message_index=3" in out
    assert "GOLD_LINE_LEAK" in out and "conversation=pass_1 message_index=4" in out
    assert summary["tasks"][0]["recall_lines"] == [DIGEST]
    assert summary["tasks"][0]["leak_lines"] == [DIGEST]


def test_pass_prompt_line_is_recall_only_if_the_model_wrote_it_into_requirements(
        tmp_path, monkeypatch, capsys):
    requirements = json.dumps({"requirements": [{"id": "R1", "text": EXCLUSIVE}]})
    conversations = {
        "requirements": prompt() + [assistant(content="R1: " + EXCLUSIVE)],
        "pass_1": prompt("Requirements:\nR1: " + EXCLUSIVE),
    }
    run = reference_run(tmp_path, monkeypatch, conversations, requirements_json=requirements)
    code, out, summary = run_audit(run, tmp_path, capsys)
    assert code == 0 and "GOLD_LINE_LEAK" not in out
    assert "conversation=pass_1 message_index=2" in out
    assert summary["tasks"][0]["recall_messages"] == [
        {"conversation": "requirements", "message_index": 3},
        {"conversation": "pass_1", "message_index": 2}]


@pytest.mark.parametrize("case", ["not-in-requirements-json", "not-model-written"])
def test_pass_prompt_line_otherwise_is_a_leak(tmp_path, monkeypatch, capsys, case):
    if case == "not-in-requirements-json":
        requirements_conversation = prompt() + [assistant(content=EXCLUSIVE)]
        requirements = json.dumps({"requirements": [{"id": "R1", "text": "something else"}]})
    else:
        requirements_conversation = prompt()
        requirements = json.dumps({"requirements": [{"id": "R1", "text": EXCLUSIVE}]})
    run = reference_run(tmp_path, monkeypatch, {
        "requirements": requirements_conversation,
        "pass_1": prompt("Requirements:\nR1: " + EXCLUSIVE),
    }, requirements_json=requirements)
    code, out, summary = run_audit(run, tmp_path, capsys)
    assert code == 1
    assert "GOLD_LINE_LEAK" in out and "conversation=pass_1 message_index=2" in out


def test_gold_line_in_a_kept_frozen_test_is_recorded(tmp_path, monkeypatch, capsys):
    run = reference_run(tmp_path, monkeypatch, {
        "requirements": prompt(),
        "pass_1": prompt() + [assistant(content=EXCLUSIVE)],
    }, tests={"test_repro_R1_p1.py": ("def test():\n    " + EXCLUSIVE + "\n", True),
              "test_repro_R2_p1.py": ("def test():\n    " + EXCLUSIVE + "\n", False)})
    code, out, summary = run_audit(run, tmp_path, capsys)
    assert code == 0
    assert out.count("[recorded] GOLD_LINE_IN_FROZEN_TEST") == 1
    assert "test_repro_R1_p1.py" in out and "test_repro_R2_p1.py" not in out
    assert summary["tasks"][0]["frozen_test_lines"] == [DIGEST]


def test_a_kept_frozen_test_that_differs_from_its_hash_fails_closed(tmp_path, monkeypatch, capsys):
    run = reference_run(tmp_path, monkeypatch, {"requirements": prompt(), "pass_1": prompt()},
                        tests={"test_repro_R1_p1.py": ("def test():\n    pass\n", True)})
    (run / "tasks" / IID / "verification/v4/tests/test_repro_R1_p1.py").write_text("changed\n")
    code, out, _ = run_audit(run, tmp_path, capsys)
    assert code == 1 and "reference-audit-incomplete" in out


def test_reference_generator_trajectories_get_newer_copy_checks(tmp_path, monkeypatch, capsys):
    read = assistant(tool_calls=[{"id": "c1", "type": "function", "function": {
        "name": "bash", "arguments": json.dumps({"command": "cat /opt/miniconda3/pkgs/demo/x.py"})}}])
    run = reference_run(tmp_path, monkeypatch, {
        "requirements": prompt(),
        "pass_1": prompt() + [read, tool("<returncode>0</returncode>\n<output>\nsource text\n</output>")],
    })
    code, out, _ = run_audit(run, tmp_path, capsys)
    assert code == 1 and "[confirmed] newer-copy-path" in out
    listing = assistant(tool_calls=[{"id": "c1", "type": "function", "function": {
        "name": "bash", "arguments": json.dumps({"command": "ls /opt/miniconda3/pkgs"})}}])
    (tmp_path / "second").mkdir()
    run2 = reference_run(tmp_path / "second", monkeypatch, {
        "requirements": prompt(),
        "pass_1": prompt() + [listing, tool("<returncode>0</returncode>\n<output>\ndemo\n</output>")],
    })
    code, out, _ = run_audit(run2, tmp_path / "second", capsys)
    assert code == 0 and "newer-copy-listing" in out
