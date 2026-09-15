"""List SWE-bench Verified instances for one repo, grouped by environment setup commit.

Evaluation images are layered base -> env -> instance, and the env layer is keyed
by (repo, environment_setup_commit). Instances sharing an env commit therefore
share that layer on disk, which is what separates per-repo from per-instance cost.
"""

import sys
import warnings
from collections import defaultdict

warnings.filterwarnings("ignore")

from datasets import load_dataset

repo = sys.argv[1]
ds = load_dataset("SWE-bench/SWE-bench_Verified", split="test")

groups = defaultdict(list)
for r in ds:
    if r["repo"] == repo:
        groups[r["environment_setup_commit"]].append(r["instance_id"])

for env_commit, instances in sorted(groups.items(), key=lambda kv: -len(kv[1])):
    print(f"{env_commit}  n={len(instances)}")
    for i in sorted(instances):
        print(f"    {i}")
