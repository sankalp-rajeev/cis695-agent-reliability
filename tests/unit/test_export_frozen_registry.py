"""Ordered batch exports and the original no-argument exporter entry point."""

import hashlib
import json
import sys

import pytest
from scripts import export_frozen_registry as exporter

FIRST = "demo__repo-1"
SECOND = "demo__repo-2"
FROZEN = "demo__repo-3"


@pytest.fixture
def batch(tmp_path, monkeypatch):
    adapter = exporter.adapter
    frozen_input = f"{FROZEN}\n".encode()
    monkeypatch.setattr(adapter, "assert_clean_interpreter", lambda: None)
    monkeypatch.setattr(adapter, "git", lambda command, *args: "tag" if command == "cat-file" else adapter.COMMIT)
    monkeypatch.setattr(exporter.subprocess, "check_output", lambda *args, **kwargs: frozen_input)
    monkeypatch.setattr(adapter, "FROZEN_HASHES", {
        "configs/e2e/tasks_83.txt": hashlib.sha256(frozen_input).hexdigest(),
    })
    wheel = tmp_path / "test.whl"
    wheel.write_bytes(b"offline fixture wheel")
    monkeypatch.setattr(adapter, "WHEEL", wheel)
    monkeypatch.setattr(adapter, "WHEEL_SHA256", hashlib.sha256(wheel.read_bytes()).hexdigest())
    inputs = tmp_path / "stable"
    inputs.mkdir()
    monkeypatch.setattr(adapter, "INPUTS", inputs)

    def copy_verified(source, destination, sha256):
        raw = source.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == sha256
        destination.write_bytes(raw)

    monkeypatch.setattr(adapter, "copy_verified", copy_verified)

    def registry(iid):
        evidence = tmp_path / iid
        evidence.mkdir()
        projection = evidence / "dataset_projection.json"
        projection.write_text(json.dumps({"instance_id": iid}))
        row = dict.fromkeys(adapter.TASK_FIELDS | adapter.SIDECAR_FIELDS)
        row.update(
            instance_id=iid,
            origin="prepared",
            pre_install={
                "wheel_sha256": adapter.WHEEL_SHA256,
                "dataset_projection_sha256": hashlib.sha256(projection.read_bytes()).hexdigest(),
                "spec": {},
            },
            integrity_preflight={"status": "VERIFIED", "receipt_path": str(evidence / "receipt.json")},
        )
        path = tmp_path / f"{iid}.json"
        path.write_text(json.dumps({"schema": "task_spec_registry/1", "cohort": "study_test1",
                                    "built_by_commit": "a" * 40, "tasks": [row]}))
        return path

    order = tmp_path / "order.json"
    order.write_text(json.dumps([{"instance_id": SECOND}, {"instance_id": FIRST}]))
    return [registry(FIRST), registry(SECOND)], order, tmp_path / "output.json", registry


def test_ordered_mode_preserves_slots_and_binds_sidecar(batch, monkeypatch):
    sources, order, output, _ = batch
    monkeypatch.setattr(sys, "argv", ["export_frozen_registry.py", "--registries", *map(str, sources),
                                    "--order", str(order), "--out", str(output)])
    exporter.main()
    raw = output.read_bytes()
    assert [row["instance_id"] for row in json.loads(raw)["tasks"]] == [SECOND, FIRST]
    sidecar = json.loads(output.with_suffix(".provenance.json").read_text())
    assert sidecar["registry_sha256"] == hashlib.sha256(raw).hexdigest()
    assert [source["path"] for source in sidecar["source_registries"]] == list(map(str, sources))


@pytest.mark.parametrize("suffix", [".json", ".provenance.json"])
def test_ordered_mode_refuses_existing_output(batch, suffix):
    sources, order, output, _ = batch
    existing = output.with_suffix(suffix)
    existing.write_text("original")
    with pytest.raises(FileExistsError, match="Output already exists"):
        exporter.export_ordered_registries(sources, order, output)
    assert existing.read_text() == "original"
    other = output.with_suffix(".provenance.json" if suffix == ".json" else ".json")
    assert not other.exists()


@pytest.mark.parametrize("overlaps", [False, True], ids=["missing-registry-id", "frozen-id"])
def test_ordered_mode_refuses_invalid_ids(batch, overlaps):
    sources, order, output, registry = batch
    if overlaps:
        sources = [sources[0], registry(FROZEN)]
        order.write_text(json.dumps([{"instance_id": FIRST}, {"instance_id": FROZEN}]))
    else:
        sources = sources[:1]
    with pytest.raises(ValueError, match="match the prepared registries and be disjoint"):
        exporter.export_ordered_registries(sources, order, output)
    assert not output.exists() and not output.with_suffix(".provenance.json").exists()


def test_no_argument_calls_original_export(monkeypatch):
    calls = []
    monkeypatch.setattr(sys, "argv", ["export_frozen_registry.py"])
    monkeypatch.setattr(exporter.adapter, "export", lambda: calls.append("export"))
    exporter.main()
    assert calls == ["export"]
