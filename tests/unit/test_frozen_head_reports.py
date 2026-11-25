"""Audited mode (amendment B10/B11 freeze `v1.5-frozen-2`): HEAD must be the freeze tag's
commit, or a descendant whose every change since the tag is under reports/ (the per-system
report commits of Phase 12). The tree must be clean and the tag annotated."""

import subprocess

import pytest

from reliability import e2e_runner


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                          check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "reports").mkdir()
    (root / "src/code.py").write_text("x = 1\n")
    (root / "reports/a.md").write_text("a\n")
    git(root, "init", "-q")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "frozen")
    git(root, "tag", "-a", "freeze", "-m", "freeze")
    monkeypatch.setattr(e2e_runner, "ROOT", root)
    return root


def commit(repo, path, text):
    (repo / path).parent.mkdir(parents=True, exist_ok=True)
    (repo / path).write_text(text)
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "change " + path)


def test_head_at_the_tag_is_accepted(repo):
    assert e2e_runner.require_frozen_head("freeze") == git(repo, "rev-parse", "HEAD")


def test_report_only_commits_after_the_tag_are_accepted(repo):
    commit(repo, "reports/test_b1/system.md", "report\n")
    commit(repo, "reports/study/STATUS.md", "status\n")
    assert e2e_runner.require_frozen_head("freeze") == git(repo, "rev-parse", "HEAD")


@pytest.mark.parametrize("path", ["src/code.py", "configs/v.yaml", "scripts/run.py", "tests/t.py", "README.md"])
def test_any_other_change_after_the_tag_is_refused(repo, path):
    commit(repo, "reports/ok.md", "fine\n")
    commit(repo, path, "changed\n")
    with pytest.raises(ValueError, match="clean HEAD at the freeze tag"):
        e2e_runner.require_frozen_head("freeze")


def test_a_dirty_tree_is_refused_even_at_the_tag(repo):
    (repo / "reports/a.md").write_text("edited\n")
    with pytest.raises(ValueError, match="clean HEAD"):
        e2e_runner.require_frozen_head("freeze")


def test_head_that_does_not_descend_from_the_tag_is_refused(repo):
    git(repo, "checkout", "-q", "--orphan", "other")
    commit(repo, "reports/x.md", "x\n")
    with pytest.raises(ValueError, match="clean HEAD at the freeze tag"):
        e2e_runner.require_frozen_head("freeze")


def test_a_lightweight_tag_is_refused(repo):
    git(repo, "tag", "light")
    with pytest.raises(ValueError, match="annotated"):
        e2e_runner.require_frozen_head("light")
