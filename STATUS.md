# Leakage gaps audit

2026-11-17: Implementing the four audit extensions on `analysis/leakage-gaps`.
Stored main-study artifacts are read in place. No correctness labels or grader
results are inputs. The running `wt-e2e` experiment is out of scope and untouched.

Offline dataset cache: only SWE-bench Verified, copied to `runs/hf_home`,
15,484,578 bytes initially (15 MB). All Python commands use this worktree's
`.venv`, `PYTHONPATH=src`, and both Hugging Face offline flags.

Pending: implementation, synthetic tests, stored-run golden comparison,
image inventory and checks, full unit suite comparison by id, independent verifier.
No push is authorized.
