"""Print the prebuilt evaluation image name for one SWE-bench Verified instance."""

import sys
import warnings

warnings.filterwarnings("ignore")

from datasets import load_dataset  # noqa: E402

instance_id = sys.argv[1]
ds = load_dataset("SWE-bench/SWE-bench_Verified", split="test")
print(next(r["image"] for r in ds if r["instance_id"] == instance_id))
