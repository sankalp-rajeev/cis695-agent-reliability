import importlib.util
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _script():
    spec = importlib.util.spec_from_file_location(
        "audit_leakage_script", ROOT / "scripts" / "audit_leakage.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fake_docker(monkeypatch, *, git, site):
    """git and site are (returncode, stdout, stderr) for the two searches."""
    monkeypatch.setattr("reliability.agent.isolation.docker_bin", lambda: "docker")
    monkeypatch.setattr("reliability.verifier.container.image_for", lambda _id: "img")

    def fake_run(cmd, **kwargs):
        rc, out, err = git if cmd[cmd.index("--entrypoint") + 1] == "git" else site
        return subprocess.CompletedProcess(cmd, rc, out, err)

    monkeypatch.setattr(subprocess, "run", fake_run)


LINE = "return type(self)(result)"
OTHER = "this_line_exists_nowhere_in_the_image()"


def test_a_line_found_only_in_site_packages_is_dropped(monkeypatch):
    _fake_docker(monkeypatch, git=(1, "", ""), site=(0, f"            {LINE}\n", ""))
    found = _script().lines_present_at_base("x__x-1", (LINE, OTHER))
    assert found == {LINE}


def test_a_line_found_by_neither_search_is_kept_as_a_probe(monkeypatch):
    _fake_docker(monkeypatch, git=(1, "", ""), site=(1, "", ""))
    assert _script().lines_present_at_base("x__x-1", (LINE,)) == set()


def test_a_failed_site_packages_search_drops_nothing(monkeypatch):
    _fake_docker(monkeypatch, git=(1, "", ""), site=(2, "", "bash: boom"))
    assert _script().lines_present_at_base("x__x-1", (LINE,)) == set()


def test_a_line_found_in_the_repo_tree_is_still_dropped(monkeypatch):
    _fake_docker(monkeypatch, git=(0, f"a.py:    {LINE}\n", ""), site=(1, "", ""))
    assert _script().lines_present_at_base("x__x-1", (LINE,)) == {LINE}
