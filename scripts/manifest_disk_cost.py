"""Compute the exact image-store cost of a task manifest, by build cohort.

Usage: manifest_disk_cost.py manifests/pilot.csv

Multiplying a per-instance average is wrong: SWE-bench evaluation images share
layers according to the batch they were built in, so the cost of a set of images
depends on which layers they hold in common, not on how many images there are.
This script resolves each image's actual layer list from the registry and takes
the union.

No image is pulled. `docker manifest inspect` returns the OCI index, from which
the amd64 sub-manifest gives every layer digest and its *compressed* size. The
union of distinct digests is therefore an exact answer to "how many distinct
layers will this manifest download", in compressed bytes.

On-disk size is larger, since layers are stored extracted. The ratio is
calibrated against the nine images already local, where both quantities are
known: their compressed union is computed the same way and their true
deduplicated on-disk size is read from `docker system df`.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


NAMESPACE = "swebench/sweb.eval.x86_64"


def image_for(instance_id: str) -> str:
    return f"{NAMESPACE}.{instance_id.replace('__', '_1776_').lower()}:latest"


def sh(*args: str) -> str:
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def layers_for(image: str) -> list[tuple[str, int]]:
    """Return (digest, compressed_size) for the amd64 manifest's layers."""
    index = json.loads(sh("docker", "manifest", "inspect", image))

    if "manifests" in index:
        digest = next(
            m["digest"] for m in index["manifests"]
            if m.get("platform", {}).get("architecture") == "amd64"
        )
        repo = image.split(":")[0]
        index = json.loads(sh("docker", "manifest", "inspect", f"{repo}@{digest}"))

    return [(layer["digest"], layer["size"]) for layer in index["layers"]]


def gb(n: float) -> float:
    return round(n / 1e9, 3)


def union_bytes(per_image: dict[str, list[tuple[str, int]]]) -> int:
    seen: dict[str, int] = {}
    for layers in per_image.values():
        for digest, size in layers:
            seen[digest] = size
    return sum(seen.values())


def local_store_gb() -> float:
    for line in sh("docker", "system", "df", "--format", "{{json .}}").splitlines():
        row = json.loads(line)
        if row["Type"] == "Images":
            raw = row["Size"]
            for unit, mult in (("TB", 1e12), ("GB", 1e9), ("MB", 1e6), ("kB", 1e3)):
                if raw.endswith(unit):
                    return float(raw[: -len(unit)]) * mult / 1e9
    return 0.0


manifest_path = Path(sys.argv[1] if len(sys.argv) > 1 else "manifests/pilot.csv")
rows = list(csv.DictReader(manifest_path.open(newline="")))
instances = [r["instance_id"] for r in rows]

print(f"manifest: {manifest_path}  instances: {len(instances)}")
print("resolving layers from the registry (no pull)...\n")

per_image = {}
for instance_id in instances:
    image = image_for(instance_id)
    per_image[instance_id] = layers_for(image)
    total = sum(s for _, s in per_image[instance_id])
    print(f"  {instance_id:34s} layers={len(per_image[instance_id]):3d} compressed={gb(total):6.3f}GB")

# Group instances by the set of layers they share with others: the build cohort.
cohorts: dict[frozenset[str], list[str]] = defaultdict(list)
digest_owners: dict[str, list[str]] = defaultdict(list)
for instance_id, layers in per_image.items():
    for digest, _ in layers:
        digest_owners[digest].append(instance_id)

shared_digests = {d for d, owners in digest_owners.items() if len(owners) > 1}
for instance_id, layers in per_image.items():
    key = frozenset(d for d, _ in layers if d in shared_digests)
    cohorts[key].append(instance_id)

naive = sum(sum(s for _, s in layers) for layers in per_image.values())
exact = union_bytes(per_image)

layer_size = {d: s for layers in per_image.values() for d, s in layers}

print(f"\n=== build cohorts: {len(cohorts)} ===")
for i, (key, members) in enumerate(sorted(cohorts.items(), key=lambda kv: -len(kv[1])), 1):
    shared_gb = gb(sum(layer_size[d] for d in key))
    print(f"  cohort {i}: n={len(members)} shared_layers={len(key)} shared={shared_gb}GB")
    for m in sorted(members):
        print(f"      {m}")

print()
print(f"naive sum (per-image, counts shared layers repeatedly): {gb(naive)} GB compressed")
print(f"exact union (distinct layers only):                     {gb(exact)} GB compressed")
print(f"saved by sharing:                                       {gb(naive - exact)} GB")

# Calibrate compressed -> on-disk against the nine images already local.
local = sh("docker", "images", "--format", "{{.Repository}}:{{.Tag}}").split()
local_swebench = sorted(i for i in local if i.startswith(NAMESPACE))
if local_swebench:
    local_layers = {img: layers_for(img) for img in local_swebench}
    local_compressed = union_bytes(local_layers) / 1e9
    local_disk = local_store_gb()
    ratio = local_disk / local_compressed if local_compressed else 0
    print()
    print(f"calibration on {len(local_swebench)} local images:")
    print(f"  compressed union : {round(local_compressed, 3)} GB")
    print(f"  actual on disk   : {round(local_disk, 3)} GB")
    print(f"  expansion ratio  : {round(ratio, 3)}x")
    print()
    print(f"PILOT ON-DISK ESTIMATE: {round(gb(exact) * ratio, 1)} GB")
