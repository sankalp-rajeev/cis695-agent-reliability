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

Completed the stored audit: 196 directories (105 repair, 91 V4), 1,141 files,
32,567 findings. There are 458 CONFIRMED flags (including content, cache-read,
history-output and absent-test-name rules), and 1,437 benchmark-awareness flags
across 96 unique tasks. The report distinguishes answer content from post-base
preparation history. All 912 legacy findings survive with their severity; zero
downgrades and zero golden violations. Exact original base-probe subtraction was
rechecked in all 100 images with no differences.

Image audit: 100/100 present, no incomplete checks; 0/120 exact gold post-image
blobs, independently reconstructed from `git show` of the pinned base. Seven
requests images hold 28 different-version unmasked copies in total; no other
cohort task meets that condition. The report lists all future commits and tree
change categories, including permission-only changes, without publishing content.

Final full suite: 1,542 passed, 7 skipped, 6 failed, 17 errors. The failed/error
IDs exactly match the reference, with no newly passing reference failures.
All 71 new audit tests pass; focused audit validation has 143 passing tests.
The standard-library independent verifier passes. Cache size remains 15,484,578
bytes. Existing tests, reference files, stored runs and `wt-e2e` are unchanged.
Only the proposed fresh single-commit agent repository remains a user decision;
it is documented and not implemented. Commits are local; no push is authorized.
