"""Amendment B11: a gold line first seen in a tool output that only read git objects which
are verified ancestors of the task's base commit is BASE_HISTORY (recorded, not failing).
Anything else that is not model-written stays GOLD_LINE_LEAK."""

import json

import pytest

from reliability.benchmark import leakage
from reliability.verifier.task_specs import sha, write
from tests.unit.test_reference_leakage import (
    DIGEST, EXCLUSIVE, IID, assistant, prompt, reference_run, run_audit, tool,
)

BASE_COMMIT = "a" * 40
OLD = "4855071" + "0" * 33
NEWER = "9" * 40


def with_base(run, *, base_commit=BASE_COMMIT, image="sha256:" + "b" * 64):
    header = json.loads((run / "header.json").read_text())
    (registry,) = header["registry_sha256"]
    data = json.loads(open(registry).read())
    data["tasks"][0].update(base_commit=base_commit, image={"id": image})
    write(registry, data)
    header["registry_sha256"] = {registry: sha(registry)}
    write(run / "header.json", header)
    return run


def shell(command):
    return assistant(tool_calls=[{"id": "c1", "type": "function", "function": {
        "name": "bash", "arguments": json.dumps({"command": command})}}])


def history_run(tmp_path, monkeypatch, command, output, ancestors, *, seen=None, **base):
    def check(task, revisions):
        if seen is not None:
            seen.append((task.base_commit, task.image_id, sorted(revisions)))
        if isinstance(ancestors, Exception):
            raise ancestors
        return {rev: rev in ancestors for rev in revisions}
    monkeypatch.setattr(leakage, "verify_ancestors", check)
    run = reference_run(tmp_path, monkeypatch, {
        "requirements": prompt() + [shell(command), tool(output), assistant(content="done")],
    })
    return with_base(run, **base)


def diff(sha_, sign="-"):
    return (f"commit {sha_}\nAuthor: someone\nDate:   2018\n\n    Remove a work-around.\n\n"
            "diff --git a/m.py b/m.py\n@@ -1,3 +1,2 @@\n" f"{sign}    {EXCLUSIVE}\n")


def test_ancestor_commit_history_is_base_history_not_a_leak(tmp_path, monkeypatch, capsys):
    seen = []
    run = history_run(tmp_path, monkeypatch, f"cd /testbed && git show {OLD[:9]} -- m.py",
                      "<returncode>0</returncode>\n" + diff(OLD), {OLD}, seen=seen)
    code, out, summary = run_audit(run, tmp_path, capsys)
    assert code == 0
    assert "[recorded] BASE_HISTORY" in out and "GOLD_LINE_LEAK" not in out
    assert f"task={IID} conversation=requirements message_index=4 sha256={DIGEST}" in out
    task = summary["tasks"][0]
    assert task["base_history_lines"] == [DIGEST] and task["leak_lines"] == []
    assert seen == [(BASE_COMMIT, "sha256:" + "b" * 64, [OLD])]
    assert EXCLUSIVE not in out and EXCLUSIVE not in json.dumps(summary)


def test_a_commit_that_is_not_an_ancestor_stays_a_leak(tmp_path, monkeypatch, capsys):
    run = history_run(tmp_path, monkeypatch, f"git show {NEWER[:9]}", diff(NEWER, "+"), set())
    code, out, summary = run_audit(run, tmp_path, capsys)
    assert code == 1 and "[confirmed] GOLD_LINE_LEAK" in out and "BASE_HISTORY" not in out
    assert summary["tasks"][0]["leak_lines"] == [DIGEST]


def test_file_at_an_ancestor_revision_without_a_header_uses_the_named_revision(tmp_path, monkeypatch, capsys):
    seen = []
    run = history_run(tmp_path, monkeypatch, f"cd /testbed && git show {OLD[:9]}^:m.py | sed -n '1,170p'",
                      "def f():\n    " + EXCLUSIVE + "\n", {OLD[:9] + "^"}, seen=seen)
    code, out, _ = run_audit(run, tmp_path, capsys)
    assert code == 0 and "BASE_HISTORY" in out
    assert seen[0][2] == [OLD[:9] + "^"]


def test_the_nearest_commit_header_decides_in_a_compound_history_command(tmp_path, monkeypatch, capsys):
    # The line sits under the second commit's header; only that commit must be an ancestor.
    output = (f"commit {NEWER}\n\n    unrelated\n\ndiff --git a/n.py b/n.py\n+x = 1\n" + diff(OLD))
    seen = []
    run = history_run(tmp_path, monkeypatch, f"git show {NEWER[:9]} && git show {OLD[:9]}", output, {OLD}, seen=seen)
    code, out, _ = run_audit(run, tmp_path, capsys)
    assert code == 0 and "BASE_HISTORY" in out
    assert seen[0][2] == [OLD]


@pytest.mark.parametrize("command", [
    f"cat m.py && git show {'4855071' + '0' * 33}",
    "cat /opt/miniconda3/pkgs/astropy-3.1/lib/astropy/utils/introspection.py",
    f"git show {'4855071' + '0' * 33} | sed 's/x/y/'",
    "git log --all -p -- m.py | python -c 'import sys; print(sys.stdin.read())'",
], ids=["non-git-segment", "package-cache", "editing-filter", "python-filter"])
def test_output_that_is_not_only_git_history_stays_a_leak(tmp_path, monkeypatch, capsys, command):
    run = history_run(tmp_path, monkeypatch, command, diff(OLD), {OLD})
    code, out, _ = run_audit(run, tmp_path, capsys)
    assert code == 1 and "GOLD_LINE_LEAK" in out and "BASE_HISTORY" not in out


@pytest.mark.parametrize("failure", ["checker-error", "no-base-commit"])
def test_unverifiable_ancestry_stays_a_leak(tmp_path, monkeypatch, capsys, failure):
    ancestors = RuntimeError("docker unavailable") if failure == "checker-error" else {OLD}
    base = {"base_commit": None} if failure == "no-base-commit" else {}
    run = history_run(tmp_path, monkeypatch, f"git show {OLD[:9]}", diff(OLD), ancestors, **base)
    code, out, _ = run_audit(run, tmp_path, capsys)
    assert code == 1 and "GOLD_LINE_LEAK" in out


def test_model_written_first_appearance_is_still_recall(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(leakage, "verify_ancestors", lambda task, revisions: {r: True for r in revisions})
    run = with_base(reference_run(tmp_path, monkeypatch, {
        "requirements": prompt() + [assistant(content=EXCLUSIVE), shell(f"git show {OLD[:9]}"), tool(diff(OLD))],
    }))
    code, out, summary = run_audit(run, tmp_path, capsys)
    assert code == 0 and "GENERATOR_RECALL" in out and "BASE_HISTORY" not in out
    assert summary["tasks"][0]["base_history_lines"] == []


def test_history_revisions_parser():
    revisions = leakage.history_revisions
    assert revisions(f"cd /testbed && git show {OLD[:9]} -- a.py", diff(OLD), EXCLUSIVE) == {OLD}
    assert revisions(f"git show {OLD[:9]}^:a.py | head -50", "    " + EXCLUSIVE, EXCLUSIVE) == {OLD[:9] + "^"}
    assert revisions("git log -p -- a.py | grep -n minversion", diff(OLD), EXCLUSIVE) == {OLD}
    assert revisions("grep -R minversion .", diff(OLD), EXCLUSIVE) is None
    assert revisions("git show HEAD:a.py", "    " + EXCLUSIVE, EXCLUSIVE) == {"HEAD"}
