"""Measure true layer sharing between local SWE-bench evaluation images.

`docker system df -v` attributes SharedSize/UniqueSize per image, but that
accounting is unreliable here: summing per-image UniqueSize exceeded the
reported store total, implying a negative shared remainder. This script works
from the layer graph instead, which is ground truth.

Each image's RootFS.Layers is its ordered list of diff IDs. Two images share a
layer when they share a diff ID. Layer byte sizes come from `docker history`,
whose size-bearing entries correspond in order to the diff IDs.

Usage: layer_overlap.py
"""

import json
import subprocess
from itertools import combinations


def sh(*args: str) -> str:
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def images() -> list[str]:
    out = sh("docker", "images", "--format", "{{.Repository}}:{{.Tag}}")
    return sorted(i for i in out.split() if i.startswith("swebench/"))


def diff_ids(image: str) -> list[str]:
    return json.loads(sh("docker", "image", "inspect", "--format", "{{json .RootFS.Layers}}", image))


def layer_sizes(image: str) -> list[int]:
    """Sizes of the size-bearing history entries, oldest first."""
    out = sh("docker", "history", "--no-trunc", "--format", "{{.Size}}", image)
    # docker history prints newest first; reverse to match diff-id order.
    raw = [line.strip() for line in out.splitlines() if line.strip()][::-1]
    sizes = []
    for r in raw:
        units = {"TB": 1e12, "GB": 1e9, "MB": 1e6, "kB": 1e3, "KB": 1e3, "B": 1}
        for u, m in units.items():
            if r.endswith(u):
                sizes.append(int(float(r[: -len(u)]) * m))
                break
    return [s for s in sizes if s > 0]


imgs = images()
layer_bytes: dict[str, int] = {}
image_layers: dict[str, list[str]] = {}

for img in imgs:
    ids = diff_ids(img)
    sizes = layer_sizes(img)
    image_layers[img] = ids
    # Align from the front; non-empty layers map to the earliest diff ids.
    for lid, size in zip(ids, sizes):
        layer_bytes[lid] = max(layer_bytes.get(lid, 0), size)

short = {img: img.split(".")[-1].replace(":latest", "") for img in imgs}

print("=== layer counts ===")
for img in imgs:
    total = sum(layer_bytes.get(l, 0) for l in image_layers[img])
    print(f"{short[img]:28s} layers={len(image_layers[img]):3d} sum_layer_gb={total / 1e9:7.3f}")

print()
print("=== pairwise shared layers ===")
for a, b in combinations(imgs, 2):
    sa, sb = set(image_layers[a]), set(image_layers[b])
    shared = sa & sb
    shared_gb = sum(layer_bytes.get(l, 0) for l in shared) / 1e9
    print(f"{short[a]:28s} {short[b]:28s} shared_layers={len(shared):3d} shared_gb={shared_gb:7.3f}")

print()
all_layers = {l for ls in image_layers.values() for l in ls}
union_gb = sum(layer_bytes.get(l, 0) for l in all_layers) / 1e9
naive_gb = sum(sum(layer_bytes.get(l, 0) for l in ls) for ls in image_layers.values()) / 1e9
print(f"images={len(imgs)}")
print(f"naive_sum_gb={naive_gb:.3f}   (counts shared layers once per image)")
print(f"dedup_union_gb={union_gb:.3f} (true on-disk, uncompressed)")
print(f"sharing_saving_gb={naive_gb - union_gb:.3f}")
