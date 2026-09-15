"""Report the Docker image store with shared vs unique size per image.

`docker images` reports each image's full virtual size, which counts shared base
layers once per image and so overstates disk use. `docker system df -v` reports
SharedSize and UniqueSize per image; UniqueSize is the marginal cost of adding
that image to a store that already holds its shared layers. The deduplicated
store total is `sum(UniqueSize) + shared_layers_counted_once`, which is what
`docker system df` prints as the Images size.

Usage: image_store.py [--tsv]
"""

import json
import subprocess
import sys

UNITS = {"B": 1, "kB": 1e3, "KB": 1e3, "MB": 1e6, "GB": 1e9, "TB": 1e12}


def to_bytes(s: str) -> float:
    s = s.strip()
    for unit, mult in sorted(UNITS.items(), key=lambda kv: -len(kv[0])):
        if s.endswith(unit):
            return float(s[: -len(unit)]) * mult
    return float(s)


def gb(n: float) -> float:
    return round(n / 1e9, 3)


verbose = json.loads(
    subprocess.run(
        ["docker", "system", "df", "-v", "--format", "{{json .}}"],
        capture_output=True, text=True, check=True,
    ).stdout
)
summary = [
    json.loads(line)
    for line in subprocess.run(
        ["docker", "system", "df", "--format", "{{json .}}"],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    if line.strip()
]

images = [i for i in verbose["Images"] if i["Repository"] != "hello-world"]
store_total = next(to_bytes(s["Size"]) for s in summary if s["Type"] == "Images")
unique_sum = sum(to_bytes(i["UniqueSize"]) for i in images)

if "--tsv" in sys.argv:
    print("repository\ttag\tunique_gb\tshared_gb\tvirtual_gb")
    for i in sorted(images, key=lambda i: i["Repository"]):
        print(
            f"{i['Repository']}\t{i['Tag']}\t{gb(to_bytes(i['UniqueSize']))}\t"
            f"{gb(to_bytes(i['SharedSize']))}\t{gb(to_bytes(i['VirtualSize']))}"
        )
else:
    for i in sorted(images, key=lambda i: i["Repository"]):
        print(
            f"{i['Repository']:62s} unique={gb(to_bytes(i['UniqueSize'])):7.3f}GB "
            f"shared={gb(to_bytes(i['SharedSize'])):7.3f}GB "
            f"virtual={gb(to_bytes(i['VirtualSize'])):7.3f}GB"
        )

print()
print(f"images={len(images)}")
print(f"sum_unique_gb={gb(unique_sum)}")
print(f"store_total_gb={gb(store_total)}")
print(f"shared_overhead_gb={gb(store_total - unique_sum)}")
