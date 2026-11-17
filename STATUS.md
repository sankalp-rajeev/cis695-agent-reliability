# Leakage gaps audit

2026-11-17: Implementing the four audit extensions on `analysis/leakage-gaps`.
Stored main-study artifacts are read in place. No correctness labels or grader
results are inputs. The running `wt-e2e` experiment is out of scope and untouched.

Offline dataset cache: only SWE-bench Verified, copied to `runs/hf_home`,
15,484,578 bytes initially (15 MB). All Python commands use this worktree's
`.venv`, `PYTHONPATH=src`, and both Hugging Face offline flags.

Implemented command-attempt/success rules, verified-base test-name classification,
per-image cache/copy/Git probes, historical golden comparison, and a standard-library
independent verifier. New synthetic tests pass, including verifier tamper checks.

All 100 images are local. Their object inventories contain a reachable post-base
commit in every image; none of 120 exact gold post-image blobs is present.
The seven requests tasks lacked supplied source archives: read-only exports of
their pinned image base commits are hashed and verified locally; provenance is
explicit in the report inputs. Existing archives are never changed.

The first full unit suite matched the reference's six failed and seventeen error
IDs exactly, with no newly passing reference failures. Final validation and the
stored-run audit are running. Commits are local; no push is authorized.
