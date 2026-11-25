"""Amendment B12: V1's apply check and the container's patch application are exactly the
SWE-bench 5.0.2 grader's sequence (harness/run_evaluation.py, GIT_APPLY_CMDS), on the patch
bytes as stored: each command in order on the patch file, the tree reset between attempts,
then `git apply --check --reverse`. A patch applies iff one exits 0; the command is recorded.
Reverting to base restores the pristine tree exactly, whichever command applied the patch."""

import subprocess

import pytest

from reliability.verifier import container as C

BASE = "".join(f"l{i}\n" for i in range(1, 10))
GOOD = ("diff --git a/m.py b/m.py\n--- a/m.py\n+++ b/m.py\n@@ -2,7 +2,7 @@\n l2\n l3\n l4\n-l5\n+L5\n l6\n l7\n l8\n")
NO_FINAL_NEWLINE = GOOD[:-1]
PREAMBLE = "Here is the fix I made:\n\n" + GOOD
FUZZ = GOOD.replace(" l8\n", " CHANGED\n")
NEVER = GOOD.replace(" l2\n l3\n l4\n-l5\n", " x2\n x3\n x4\n-x5\n").replace(" l6\n l7\n l8\n", " x6\n x7\n x8\n")


class LocalContainer(C.TaskContainer):
    """The real TaskContainer logic, run with bash in a local git repo instead of docker exec."""

    def __init__(self, root, patch_text):
        super().__init__("demo__repo-1", patch_text, image="img", name="local")
        self.root, self._started = root, True
        self.harness_patch_file = str(root.parent / "patch.diff")
        self.scratch_prefix = str(root.parent / "verifier_")

    def exec(self, command, timeout_s=120):
        script = command if isinstance(command, str) else " ".join(command)
        proc = subprocess.run(["bash", "-c", script], cwd=self.root, capture_output=True, text=True,
                              errors="replace", timeout=timeout_s, check=False)
        return proc.returncode, proc.stdout + proc.stderr

    def put_file(self, path, data):
        with open(path, "wb") as stream:
            stream.write(data)


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "testbed"
    root.mkdir()
    (root / "m.py").write_text(BASE)
    (root / ".gitignore").write_text("*.pyc\n")
    for args in (["init", "-q"], ["add", "."], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base"]):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
    (root / "untracked_base_file.txt").write_text("present in the pristine image\n")
    (root / "cached.pyc").write_bytes(b"ignored in base\n")
    return root


def tree(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*"))
            if p.is_file() and ".git" not in p.relative_to(root).parts}


@pytest.mark.parametrize("patch,command", [
    (GOOD, "git apply --verbose"),
    (NO_FINAL_NEWLINE, "patch --batch --forward --fuzz=5 -p1 -i"),
    (PREAMBLE, "git apply --verbose"),
    (FUZZ, "patch --batch --forward --fuzz=5 -p1 -i"),
], ids=["clean", "no-final-newline", "text-before-diff", "needs-fuzz"])
def test_patch_applies_by_the_first_grader_command_that_exits_0(repo, patch, command):
    container = LocalContainer(repo, patch)
    pristine = tree(repo)
    assert container.apply_check()[0] is True and container.apply_check()[2] == command
    assert tree(repo) == pristine  # the check leaves the tree as it found it
    container.set_patched(True)
    assert container.apply_command == command
    assert "L5" in (repo / "m.py").read_text()
    container.set_patched(False)
    assert tree(repo) == pristine
    container.set_patched(True)
    assert "L5" in (repo / "m.py").read_text()


def test_a_patch_that_fails_every_command_does_not_apply(repo):
    container = LocalContainer(repo, NEVER)
    pristine = tree(repo)
    applies, detail, command = container.apply_check()
    assert applies is False and command is None and detail
    with pytest.raises(C.PatchApplyError):
        container.set_patched(True)
    assert tree(repo) == pristine


def test_the_patch_file_holds_the_stored_bytes_unchanged(repo):
    container = LocalContainer(repo, NO_FINAL_NEWLINE)
    container.apply_check()
    assert open(container.harness_patch_file, "rb").read() == NO_FINAL_NEWLINE.encode("utf-8")


def test_an_already_applied_patch_counts_as_applied(repo):
    # Real git: --3way recognises the change already in the tree before the reverse check is reached.
    (repo / "m.py").write_text(BASE.replace("l5", "L5"))
    container = LocalContainer(repo, GOOD)
    applies, _, command = container.apply_check()
    assert applies is True and command == "git apply --verbose --3way"


def test_the_sequence_and_reset_are_the_grader_constants():
    from swebench.harness import run_evaluation
    from swebench.harness.constants import CONTAINER_PATCH_FILE
    assert tuple(run_evaluation.GIT_APPLY_CMDS) == C.HARNESS_APPLY_COMMANDS
    assert C.HARNESS_PATCH_FILE == CONTAINER_PATCH_FILE
    assert C.HARNESS_RESET == "git checkout -- . ; git clean -fd"


# -- V1 (verify_task) ----------------------------------------------------------------

from reliability.agent.freeze import freeze_patch  # noqa: E402
from reliability.verifier.decision import SignalOutcome  # noqa: E402
from reliability.verifier.record import SignalKind  # noqa: E402
from reliability.verifier.run_v1_4_1 import verify_task  # noqa: E402
from tests.unit.test_e2e_runtime import PATCH, good, task  # noqa: E402,F401  (fixture)


def v1(directory, task, patch, result):
    freeze_patch(directory / "patch.diff", patch)
    return verify_task(directory, instance_id=task.instance_id, task_spec=task, experiment_id="unit",
                       v2_runner=lambda *a, **k: good(SignalKind.REGRESSION),
                       v3_runner=lambda *a, **k: good(SignalKind.STATIC),
                       v4_runner=lambda *a: good(SignalKind.REPRODUCTION), drift={},
                       apply_check=lambda *a: result)


def test_v1_records_the_grader_command_that_applied_the_patch(tmp_path, task):
    record = v1(tmp_path, task, PATCH[:-1], (True, "", "patch --batch --forward --fuzz=5 -p1 -i"))
    assert record.integrity.outcome is SignalOutcome.PASS
    assert record.integrity.findings["apply_check"] == "PASS"
    assert record.integrity.findings["apply_command"] == "patch --batch --forward --fuzz=5 -p1 -i"


def test_v1_accepts_text_before_the_first_diff(tmp_path, task):
    record = v1(tmp_path, task, "Here is my fix:\n\n" + PATCH, (True, "", "git apply --verbose"))
    assert record.integrity.outcome is SignalOutcome.PASS, record.integrity.detail
    assert record.selected_tests is not None


def test_v1_fails_a_patch_no_grader_command_applies(tmp_path, task):
    record = v1(tmp_path, task, PATCH, (False, "error: patch failed: foo.py:1", None))
    assert record.integrity.outcome is SignalOutcome.FAIL
    assert record.integrity.findings["apply_check"] == "FAIL"
    assert record.integrity.findings["apply_command"] is None
