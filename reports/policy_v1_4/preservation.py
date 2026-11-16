"""Prove original source/config/test bytes and old policy document are preserved."""

import hashlib
import json
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
BASE = "a34f6ed"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


paths = git("ls-tree", "-r", "--name-only", BASE, "src", "configs", "tests").decode().splitlines()
checked = {}
for name in paths:
    before = git("show", BASE + ":" + name)
    assert (ROOT / name).read_bytes() == before, name
    checked[name] = hashlib.sha256(before).hexdigest()
name = "docs/VERIFIER_POLICY.md"
before = git("show", BASE + ":" + name)
assert (ROOT / name).read_bytes().startswith(before)
assert b"## 10. Policy v1.4.0" in (ROOT / name).read_bytes()[len(before) :]
assert not git("diff", BASE, "--", "reports/next_phases/phase7_signal_audit")
assert git("diff", BASE, "--name-only", "--diff-filter=M").decode().splitlines() == [name]
assert git("rev-parse", "main").strip() == git("rev-parse", BASE).strip()
result = {
    "base_commit": git("rev-parse", BASE).decode().strip(),
    "original_files_preserved": len(paths),
    "sha256": checked,
    "policy_document": "old bytes preserved; new version section appended",
    "sealed_audit": "unchanged",
    "main": "unchanged",
}
(OUT / "preservation.json").write_text(json.dumps(result, indent=2) + "\n")
print("PASS:", len(paths), "original source/config/test files preserved; audit and main unchanged")
