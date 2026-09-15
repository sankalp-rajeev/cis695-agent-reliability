"""Print one oracle field for one SWE-bench Verified instance.

ORACLE ACCESS. This script reads gold-patch / test fields and exists only to
build harness feasibility controls (Phase 1.2 and 1.3b). Nothing under
src/reliability/agent may call it, and its output must never reach an agent
prompt. See Phase 2.2 (oracle quarantine) and Phase 8.3 (leakage audit).

Column selection happens before iteration: scanning rows while every column is
materialised pulls the multi-kilobyte problem_statement/patch/test_patch text
for all 500 rows and takes minutes.

Usage: oracle_field.py <instance_id> <field>
"""

import sys
import warnings

warnings.filterwarnings("ignore")

from datasets import load_dataset

instance_id, field = sys.argv[1], sys.argv[2]

ds = load_dataset("SWE-bench/SWE-bench_Verified", split="test")
ds = ds.select_columns(["instance_id", field])

row = next((r for r in ds if r["instance_id"] == instance_id), None)
if row is None:
    sys.exit(f"no such instance: {instance_id}")

value = row[field]
sys.stdout.write(value if isinstance(value, str) else repr(value))
