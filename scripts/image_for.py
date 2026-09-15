"""Print the prebuilt evaluation image name for one SWE-bench Verified instance.

SWE-bench derives the image tag from the instance id by replacing the `__`
separator with `_1776_` (Docker tags cannot contain `__`) and lowercasing, so the
name is computable without loading the dataset. An earlier version of this script
scanned all 500 rows through the `datasets` API, which materialises every column
including the multi-kilobyte `problem_statement`, `patch`, and `test_patch` fields
on each row; that took minutes per lookup.

Pass --verify to check the computed name against the dataset's own `image` field.

Usage: image_for.py <instance_id> [--verify]
"""

import sys

NAMESPACE = "swebench/sweb.eval.x86_64"


def image_for(instance_id: str) -> str:
    return f"{NAMESPACE}.{instance_id.replace('__', '_1776_').lower()}:latest"


instance_id = sys.argv[1]
name = image_for(instance_id)

if "--verify" in sys.argv:
    import warnings

    warnings.filterwarnings("ignore")
    from datasets import load_dataset

    ds = load_dataset("SWE-bench/SWE-bench_Verified", split="test")
    expected = next(
        r["image"] for r in ds.select_columns(["instance_id", "image"])
        if r["instance_id"] == instance_id
    )
    if expected != name:
        sys.exit(f"MISMATCH: computed {name!r} != dataset {expected!r}")
    print(f"verified: {name}", file=sys.stderr)

print(name)
