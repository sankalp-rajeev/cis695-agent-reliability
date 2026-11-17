"""Safety and determinism boundaries of task preparation."""

import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pyarrow as pa
import pytest
from pyarrow import ipc

from reliability.task_prep import core
from reliability.task_prep.cohorts import sample_additions
from reliability.task_prep.versions_probe import versions
from reliability.verifier.pre_install import load_specs


def test_dataset_projection_precedes_row_materialization(tmp_path, monkeypatch):
    arrow = tmp_path / "metadata.arrow"
    table = pa.table(
        {
            "instance_id": ["org__repo-1"],
            "repo": ["org/repo"],
            "base_commit": ["a" * 40],
            "version": ["1.0"],
            "patch": ["must never materialize"],
            "test_patch": ["must never materialize"],
        }
    )
    with pa.OSFile(str(arrow), "wb") as sink, ipc.new_stream(sink, table.schema) as writer:
        writer.write_table(table)
    original = ipc.open_stream
    projected = []

    def checked(stream, **kwargs):
        reader = original(stream, **kwargs)
        if "options" in kwargs:
            projected.append(reader.schema.names)
        return reader

    monkeypatch.setattr(ipc, "open_stream", checked)
    rows, _ = core.dataset_rows(arrow)
    assert rows == [
        {
            "instance_id": "org__repo-1",
            "repo": "org/repo",
            "base_commit": "a" * 40,
            "version": "1.0",
        }
    ]
    assert projected == [list(core.COLUMNS)]


def test_wrong_wheel_is_rejected_before_projection_is_opened(tmp_path):
    wheel = tmp_path / "snapshot.whl"
    wheel.write_bytes(b"wrong wheel")
    with pytest.raises(ValueError, match="wheel SHA-256 mismatch"):
        load_specs(wheel, tmp_path / "missing.json")


def test_atomic_publication_never_replaces_concurrent_winner(tmp_path):
    path = tmp_path / "registry.json"

    def publish(index):
        try:
            core.write_new(path, {"writer": index})
            return index
        except FileExistsError:
            return None

    with ThreadPoolExecutor(max_workers=4) as pool:
        winners = [v for v in pool.map(publish, range(4)) if v is not None]
    assert len(winners) == 1
    assert json.loads(path.read_text()) == {"writer": winners[0]}
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize(
    "base,copies,expected",
    [
        (["1.0"], [{"path": "/opt/lib/pip/_vendor/repo/__init__.py", "version": "2.0"}], core.RULE),
        (["1.0"], [{"path": "/opt/lib/repo/__init__.py", "version": "1.0"}], "ELIGIBLE"),
        ([], [{"path": "/root/repo", "version": "1.0"}], "UNCHECKED"),
        (["1.0"], [{"path": "/tmp/repo", "version": None}], "UNCHECKED"),
    ],
)
def test_eligibility_requires_resolved_versions(base, copies, expected):
    class Container:
        image = "sha256:" + "a" * 64

        def exec_input(self, command, data, timeout_s):
            assert command.startswith("/opt/miniconda3/bin/python -c ")
            request = json.loads(data)
            assert request["import_name"] == "repo"
            assert request["masked_paths"] == list(core.MASKED_TMPFS_PATHS)
            return 0, json.dumps(
                {
                    "base_versions": [{"version": v} for v in base],
                    "copies": copies,
                    "scan_errors": [],
                }
            )

    assert (
        core.eligibility(Container(), {"instance_id": "org__repo-1", "base_commit": "a" * 40})[
            "status"
        ]
        == expected
    )


def test_version_parser_cannot_execute_package_code(tmp_path):
    marker = tmp_path / "executed"
    code = f"__version__ = '2.0.1'\nopen({str(marker)!r}, 'w').write('bad')\n"
    assert versions(code) == ["2.0.1"]
    assert not marker.exists()
    assert versions("__version__ = __import__('sys').version") == []


def test_cohort_sampling_respects_capacity_pilot_and_fixed_membership():
    rows = [
        {"instance_id": f"{repo}__pkg-{i}", "repo": repo}
        for repo in ("a", "b", "c")
        for i in range(20)
    ]
    fixed = {"a__pkg-0", "a__pkg-1", "b__pkg-0"}
    pilot = {"b__pkg-1", "c__pkg-1"}
    excluded = {f"c__pkg-{i}" for i in range(2, 20)}
    selected, quotas = sample_additions(rows, fixed, pilot, excluded, n=30)
    assert len(selected) == len(set(selected)) == 30
    assert fixed <= set(selected)
    assert not set(selected) & (pilot | excluded)
    assert selected == sample_additions(list(reversed(rows)), fixed, pilot, excluded, n=30)[0]
    assert sum(quotas.values()) == 27
    assert quotas["c"] <= 1


def test_daemon_error_is_not_treated_as_a_missing_image(monkeypatch):
    monkeypatch.setattr(
        core.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=1, stderr="permission denied", stdout=""),
    )
    with pytest.raises(RuntimeError, match="Image inspection failed"):
        core.ensure_image("org__repo-1", allow_pull=True)


def test_preparation_preserves_json_stdout_and_retains_diagnostics(monkeypatch):
    container = core.PreparationContainer("org__repo-1", "")
    monkeypatch.setattr(
        core.PreparationContainer,
        "exec_raw",
        lambda *a: (0, b'{"status":"VERIFIED"}\n', b"dependency warning\n", False),
    )
    rc, raw = container.exec("probe")
    assert rc == 0 and json.loads(raw) == {"status": "VERIFIED"}
    assert container.command_diagnostics == ["dependency warning\n"]


def test_export_expansion_is_deterministic_and_preserves_original(tmp_path):
    import base64
    import io
    import tarfile

    raw = tmp_path / "source.tar"
    with tarfile.open(
        raw, "w", format=tarfile.PAX_FORMAT, pax_headers={"comment": "a" * 40}
    ) as archive:
        member = tarfile.TarInfo("testbed/.git_archival.txt")
        member.mtime = 1234
        member.size = 3
        archive.addfile(member, io.BytesIO(b"old"))
    initial_hash = core.sha(raw)
    receipt = {
        "mismatches": [
            {
                "path": ".git_archival.txt",
                "reason": "archive_differs_from_base_git_archive",
                "describe_fallback_proofs": [{"command": ["describe", "--tags", "a" * 40]}],
                "git_archive_b64": base64.b64encode(b"proven expansion").decode(),
            }
        ]
    }
    spec = {"path": str(raw), "sha256": initial_hash, "pax_comment": "a" * 40}
    first = core.expand_proven_exports(spec, receipt)
    second = core.expand_proven_exports(spec, receipt)
    assert first == second
    assert core.sha(raw) == initial_hash
    with tarfile.open(first["path"]) as archive:
        assert archive.pax_headers["comment"] == "a" * 40
        assert archive.extractfile("testbed/.git_archival.txt").read() == b"proven expansion"
        assert archive.getmember("testbed/.git_archival.txt").mtime == 1234


def test_export_expansion_refuses_unproven_source_difference():
    from reliability.verifier.source_integrity import SourceIntegrityError

    receipt = {"mismatches": [{"path": "tox.ini", "reason": "non_export_subst_source_mismatch"}]}
    with pytest.raises(SourceIntegrityError):
        core.expand_proven_exports({}, receipt)
