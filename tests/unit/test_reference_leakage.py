import hashlib
import io
import json
import tarfile
from types import SimpleNamespace

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
    assert "GOLD_LINE_IN_GENERATOR" in result
    assert f"task={IID} conversation=pass_2 message_index=2 sha256={digest}" in result
    assert f"task={IID} count=1" in result
    assert all(line not in result for line in (EXCLUSIVE, ISSUE_LINE, REMOVED, BASE, SHORT))
