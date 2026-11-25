"""OCI metadata-only disk estimates; never pulls image layers."""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from reliability.task_prep.core import ROOT, dataset_rows, inspect_image, run, sha, write_new
from reliability.verifier.container import _docker_bin, image_for


def layers_for(image):
    # Same OCI index/amd64 layer resolution and union as manifest_disk_cost.py.
    index = json.loads(
        run([_docker_bin(), "manifest", "inspect", image], text=True, timeout=90).stdout
    )
    if "manifests" in index:
        digest = next(
            m["digest"]
            for m in index["manifests"]
            if m.get("platform", {}).get("architecture") == "amd64"
        )
        index = json.loads(
            run(
                [_docker_bin(), "manifest", "inspect", image.split(":")[0] + "@" + digest],
                text=True,
                timeout=90,
            ).stdout
        )
    return [(layer["digest"], layer["size"]) for layer in index["layers"]]


def union(layers):
    return {digest: size for entries in layers for digest, size in entries}


def project(cohort_dir, cache_dir, out):
    import shutil

    rows, _ = dataset_rows()
    by_id = {r["instance_id"]: r for r in rows}
    cohorts = {
        name: json.loads((cohort_dir / (name + ".json")).read_text())["instance_ids"]
        for name in ("main100", "verified200", "verified500")
    }
    # Include every locally present Verified image, including excluded requests,
    # because its layers are already on disk and can be shared by future pulls.
    local = {iid: info for iid in by_id if (info := inspect_image(image_for(iid))) is not None}
    all_ids = sorted(set(cohorts["verified500"]) | set(local))
    cache_dir.mkdir(parents=True, exist_ok=True)

    def resolve(iid):
        path = cache_dir / (iid + ".json")
        if path.exists():
            return iid, json.loads(path.read_text())
        layers = layers_for(image_for(iid))
        write_new(path, layers)
        return iid, layers

    with ThreadPoolExecutor(max_workers=8) as pool:
        layers = dict(pool.map(resolve, all_ids))
    local_layers = union(layers[iid] for iid in local)
    summary = [
        json.loads(line)
        for line in run(
            [_docker_bin(), "system", "df", "--format", "{{json .}}"], text=True
        ).stdout.splitlines()
    ]
    raw = next(s["Size"] for s in summary if s["Type"] == "Images")
    units = {"TB": 1e12, "GB": 1e9, "MB": 1e6, "kB": 1e3, "B": 1}
    disk_bytes = next(
        float(raw[: -len(unit)]) * factor for unit, factor in units.items() if raw.endswith(unit)
    )
    expansion = disk_bytes / sum(local_layers.values())
    archive_sizes = defaultdict(list)
    existing = {}
    for directory in [Path("/home/sankalp/cg_repos/task_archives")]:
        for path in directory.glob("*.tar"):
            iid = path.stem
            if iid in by_id:
                existing[iid] = path.stat().st_size
                archive_sizes[by_id[iid]["repo"]].append(path.stat().st_size)
    timings = json.loads(
        (ROOT / "configs/e2e/task_specs_main100_rest10_evidence/timing.json").read_text()
    )
    seconds = [r["seconds"] for r in timings]
    free = shutil.disk_usage(ROOT).free
    results = {}
    for name, ids in cohorts.items():
        missing = [iid for iid in ids if iid not in local]
        needed_layers = union(layers[iid] for iid in missing)
        compressed = sum(
            size for digest, size in needed_layers.items() if digest not in local_layers
        )
        archive_cost = sum(
            statistics.mean(archive_sizes[by_id[iid]["repo"]]) for iid in ids if iid not in existing
        )
        image_disk = compressed * expansion
        results[name] = {
            "tasks": len(ids),
            "images_already_present": len(ids) - len(missing),
            "images_missing": len(missing),
            "marginal_compressed_image_bytes": compressed,
            "projected_image_disk_bytes": round(image_disk),
            "projected_new_archive_bytes": round(archive_cost),
            "free_disk_bytes_now": free,
            "projected_free_disk_bytes": round(free - image_disk - archive_cost),
            "fits_with_50GB_reserve": free - image_disk - archive_cost >= 50_000_000_000,
            "prepare_seconds_images_present": round(statistics.mean(seconds) * len(ids), 3),
            "prepare_seconds_remaining_images_present": round(
                statistics.mean(seconds) * (len(ids) - 93), 3
            ),
            "missing_compressed_download_bytes": compressed,
        }
    value = {
        "cohorts": results,
        "local_verified_images": len(local),
        "local_compressed_layer_union_bytes": sum(local_layers.values()),
        "docker_image_store_reported_bytes": disk_bytes,
        "compressed_to_disk_ratio": expansion,
        "archive_mean_bytes_by_repo": {
            repo: statistics.mean(sizes) for repo, sizes in sorted(archive_sizes.items())
        },
        "measured_ten_seconds": seconds,
        "mean_seconds": statistics.mean(seconds),
        "median_seconds": statistics.median(seconds),
        "time_scope": "serial preparation stages with local images; excludes pull/network time and model/test execution",
        "time_projection_caveat": "Ten-task timings include failures and omit unknown pull latency; no claim that ten tasks all VERIFIED.",
        "disk_method": "OCI amd64 distinct compressed layer union minus all locally present Verified layers, using manifest_disk_cost.py algorithm; extracted bytes calibrated by local docker system df image store / compressed union.",
        "disk_caveat": "Calibrated estimate, not a hard upper bound. Archive cost uses observed per-repo means. No image layers pulled.",
        "metadata_sha256": {p.name: sha(p) for p in sorted(cache_dir.glob("*.json"))},
        "pulls": 0,
    }
    write_new(out, value)
    print(json.dumps(value["cohorts"], indent=2))
    return value
