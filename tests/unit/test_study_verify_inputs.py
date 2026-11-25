import hashlib
import json

import pytest
from scripts import run_e2e
from scripts.make_verify_inputs import build_verify_inputs

from reliability.verifier.task_specs import ROOT, sha, write

FIRST = "demo__repo-1"
SECOND = "demo__repo-2"


def inputs(tmp_path, folder="reference"):
    manifest = tmp_path / "runs/study_v1_5/patches" / folder / "tasks.json"
    manifest.parent.mkdir(parents=True)
    rows = []
    for iid, raw in ((FIRST, b"synthetic patch\n"), (SECOND, b"")):
        path = manifest.with_name(iid + ".patch")
        path.write_bytes(raw)
        rows.append({
            "instance_id": iid, "patch_path": str(path.relative_to(tmp_path)),
            "patch_sha256": hashlib.sha256(raw).hexdigest(),
        })
    write(manifest, {"tasks": rows})
    ids = tmp_path / "ids.json"
    write(ids, [SECOND, FIRST])
    return manifest, ids


def test_converter_accepts_ordered_and_empty_inputs(tmp_path):
    manifest, ids = inputs(tmp_path)
    output = tmp_path / "verify_inputs"
    assert build_verify_inputs(manifest, ids, output, repo_root=tmp_path) == {"patches": 2, "empty": 1}
    assert [item["instance_id"] for item in json.loads((output / "tasks.json").read_text())] == [SECOND, FIRST]
    assert list(run_e2e.frozen_inputs(output, [SECOND, FIRST])) == [SECOND, FIRST]
    assert (output / f"{SECOND}.patch").read_bytes() == b""
    assert (output / f"{SECOND}.patch").stat().st_mode & 0o222 == 0
    assert json.loads((output / "source.json").read_text()) == {
        "source_manifest": str(manifest.relative_to(tmp_path)),
        "source_manifest_sha256": sha(manifest), "id_list": str(ids), "id_list_sha256": sha(ids),
        "counts": {"patches": 2, "empty": 1},
    }
    with pytest.raises(FileExistsError):
        build_verify_inputs(manifest, ids, output, repo_root=tmp_path)
    assert (output / f"{FIRST}.patch").read_bytes() == b"synthetic patch\n"


def test_converter_refuses_bad_hash_and_removes_incomplete_output(tmp_path):
    manifest, ids = inputs(tmp_path)
    manifest.with_name(f"{FIRST}.patch").write_bytes(b"changed")
    output = tmp_path / "verify_inputs"
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        build_verify_inputs(manifest, ids, output, repo_root=tmp_path)
    assert not output.exists()


@pytest.fixture
def cli(tmp_path, monkeypatch):
    monkeypatch.setattr(run_e2e, "ROOT", tmp_path)
    monkeypatch.setattr(run_e2e, "assert_clean_interpreter", lambda: None)
    monkeypatch.setattr(run_e2e, "git", lambda *args: "")
    monkeypatch.setattr(run_e2e, "load_registries", lambda paths: ({}, {}))
    return [
        "--manifest", str(tmp_path / "ids.json"), "--task-specs", str(tmp_path / "registry.json"),
        "--output", str(tmp_path / "runs/output"), "--mode", "pilot", "--skip-v4",
        "--primary-config", str(ROOT / "configs/model/primary.yaml"),
        "--generator-config", str(ROOT / "configs/model/generator.yaml"),
    ]


def test_reference_flag_requires_verify_only(cli):
    with pytest.raises(ValueError, match="requires --verify-only-from"):
        run_e2e.main([*cli, "--reference-patches"])


@pytest.mark.parametrize("folder, flag", [("reference", []), ("public", ["--reference-patches"])])
def test_reference_flag_requires_matching_provenance(tmp_path, cli, folder, flag):
    manifest, ids = inputs(tmp_path, folder)
    output = tmp_path / "verify_inputs"
    build_verify_inputs(manifest, ids, output, repo_root=tmp_path)
    with pytest.raises(ValueError, match="must match the reference manifest"):
        run_e2e.main([*cli, "--verify-only-from", str(output), *flag])


@pytest.mark.parametrize("reference", [True, False])
def test_reference_opt_in_is_recorded_in_header(tmp_path, cli, monkeypatch, reference):
    manifest, ids = inputs(tmp_path, "reference" if reference else "public")
    output = tmp_path / "verify_inputs"
    build_verify_inputs(manifest, ids, output, repo_root=tmp_path)

    def record_header(ids, directory, header, agent_stage, verify_stage, **options):
        assert header["reference_patches"] is reference
        assert header["verify_only_input_folder"] == str(output)
        assert header["verify_only_source_sha256"] == sha(output / "source.json")
        return "COMPLETE"

    monkeypatch.setattr(run_e2e, "run_batch", record_header)
    flag = ["--reference-patches"] if reference else []
    assert run_e2e.main([*cli, "--verify-only-from", str(output), *flag]) == 0
