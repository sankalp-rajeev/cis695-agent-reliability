#!/usr/bin/env python3
"""Fallback projection from Docker Hub tag metadata; never downloads layers.

OCI exact unions are rate-limited. Report a no-sharing estimate and a calibrated
store-average estimate distinctly, with their assumptions and limitations.
"""

import json
import statistics
import threading
import time
import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from reliability.env import assert_clean_interpreter
from reliability.task_prep.core import ROOT, dataset_rows, inspect_image, run, sha, write_new
from reliability.verifier.container import image_for

_request_lock = threading.Lock()
_last_request = 0.0


def tag_metadata(iid):
    path = ROOT / "runs/task_prep_tag_sizes" / (iid + ".json")
    if path.exists():
        return json.loads(path.read_text())
    repository = image_for(iid).split(":")[0]
    url = "https://hub.docker.com/v2/repositories/" + repository + "/tags/latest"
    for attempt in range(8):
        try:
            global _last_request
            with _request_lock:
                time.sleep(max(0.0, 1.0 - (time.monotonic() - _last_request)))
                _last_request = time.monotonic()
            with urllib.request.urlopen(url, timeout=45) as response:
                value = json.load(response)
            image = next(
                i for i in value["images"] if i["architecture"] == "amd64" and i["os"] == "linux"
            )
            result = {
                "instance_id": iid,
                "url": url,
                "compressed_size": image["size"],
                "manifest_digest": image["digest"],
            }
            write_new(path, result)
            return result
        except (OSError, ValueError, StopIteration):
            if attempt == 7:
                raise
            time.sleep(30)


def main():
    assert_clean_interpreter()
    rows, _ = dataset_rows()
    by_id = {r["instance_id"]: r for r in rows}
    cohorts = {
        name: json.loads((ROOT / "configs/e2e/cohorts" / (name + ".json")).read_text())[
            "instance_ids"
        ]
        for name in ("main100", "verified200", "verified500")
    }
    local = {iid: info for iid in by_id if (info := inspect_image(image_for(iid))) is not None}
    with ThreadPoolExecutor(max_workers=2) as pool:
        sizes = {
            r["instance_id"]: r
            for r in pool.map(tag_metadata, sorted(set(cohorts["verified500"]) | set(local)))
        }
    ratios = [info["Size"] / sizes[iid]["compressed_size"] for iid, info in local.items()]
    expansion_by_repo = defaultdict(list)
    for iid, info in local.items():
        expansion_by_repo[by_id[iid]["repo"]].append(info["Size"] / sizes[iid]["compressed_size"])
    summary = [
        json.loads(s)
        for s in run(
            ["docker", "system", "df", "--format", "{{json .}}"], text=True
        ).stdout.splitlines()
    ]
    raw = next(s["Size"] for s in summary if s["Type"] == "Images")
    units = {"TB": 1e12, "GB": 1e9, "MB": 1e6, "kB": 1e3, "B": 1}
    disk_bytes = next(
        float(raw[: -len(unit)]) * factor for unit, factor in units.items() if raw.endswith(unit)
    )
    store_ratio = disk_bytes / sum(sizes[i]["compressed_size"] for i in local)
    archive_sizes = defaultdict(list)
    existing = set()
    for p in Path("/home/sankalp/cg_repos/task_archives").glob("*.tar"):
        iid = p.name.split(".", 1)[0]
        if iid in by_id:
            existing.add(iid)
            if p.name == iid + ".tar":
                archive_sizes[by_id[iid]["repo"]].append(p.stat().st_size)
    initial = json.loads(
        (ROOT / "configs/e2e/task_specs_main100_rest10_evidence/timing.json").read_text()
    )
    retry = []
    for suffix in ("retry1", "retry2"):
        retry.extend(
            json.loads(
                (
                    ROOT / f"configs/e2e/task_specs_main100_rest10_{suffix}_evidence/timing.json"
                ).read_text()
            )
        )
    times = {r["instance_id"]: r["seconds"] for r in initial}
    for r in retry:
        times[r["instance_id"]] += r["seconds"]
    per_task = statistics.mean(times.values())
    import shutil

    free = shutil.disk_usage(ROOT).free
    results = {}
    for name, ids in cohorts.items():
        missing = [iid for iid in ids if iid not in local]
        compressed_sum = sum(sizes[i]["compressed_size"] for i in missing)
        archives = sum(
            statistics.mean(archive_sizes[by_id[i]["repo"]]) for i in ids if i not in existing
        )
        point = compressed_sum * store_ratio
        conservative = sum(
            sizes[i]["compressed_size"] * max(expansion_by_repo[by_id[i]["repo"]]) for i in missing
        )
        results[name] = {
            "tasks": len(ids),
            "images_already_present": len(ids) - len(missing),
            "images_missing": len(missing),
            "compressed_missing_image_sum_bytes_no_sharing": compressed_sum,
            "image_disk_bytes_store_average_estimate": round(point),
            "image_disk_bytes_no_sharing_conservative_estimate": round(conservative),
            "archive_disk_bytes_estimate": round(archives),
            "free_disk_bytes_now": free,
            "free_disk_bytes_after_store_average_estimate": round(free - point - archives),
            "free_disk_bytes_after_conservative_estimate": round(free - conservative - archives),
            "fits_50GB_reserve_store_average_estimate": free - point - archives >= 50_000_000_000,
            "fits_50GB_reserve_conservative_estimate": free - conservative - archives
            >= 50_000_000_000,
            "serial_prepare_seconds_images_present": round(per_task * len(ids), 3),
            "remaining_prepare_seconds_images_present": round(per_task * (len(ids) - 93), 3),
        }
    value = {
        "method": "Docker Hub amd64 tag compressed sizes; exact OCI union unavailable due unauthenticated pull rate limit",
        "cohorts": results,
        "pulls": 0,
        "local_verified_images": len(local),
        "local_image_store_reported_bytes": disk_bytes,
        "local_virtual_to_compressed_min": min(ratios),
        "local_virtual_to_compressed_max": max(ratios),
        "store_average_ratio": store_ratio,
        "assumptions": [
            "Store-average point estimate assumes the current deduplication ratio carries to the new repo/build mix.",
            "Conservative estimate sums each missing full compressed image times the maximum observed extracted/compressed ratio for its repo, with no sharing credit; it is an estimate, not a mathematical bound.",
            "Archives use existing per-repo mean tar size; no new archives are built for projection.",
            "Time includes all observed initial/retry attempts on ten tasks with local images. Pull/network time is unmeasured and excluded.",
            "The 500-named manifest is the entire non-excluded Verified population, not 500 eligible tasks.",
        ],
        "archive_mean_bytes_by_repo": {
            k: statistics.mean(v) for k, v in sorted(archive_sizes.items())
        },
        "measured_ten_seconds_including_retries": times,
        "mean_seconds": per_task,
        "metadata_records": len(sizes),
        "tag_size_metadata_sha256": {
            iid: sha(ROOT / "runs/task_prep_tag_sizes" / (iid + ".json")) for iid in sorted(sizes)
        },
    }
    write_new(ROOT / "reports/next_phases/task_prep/projection.json", value)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
