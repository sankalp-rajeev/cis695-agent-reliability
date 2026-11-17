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

Interpretive follow-up (2026-11-17): adding a separate T0–T4 layer without
rewriting any original finding or image receipt. It distinguishes tool-first
answer content from model-produced fixes, applies the length/base-occurrence
guard, and treats accepted setup history as harmless. The rerun CLI is exercised
only on invented temporary folders. Full-suite comparison is in progress.

Interpretation completed: 210 task/run/role rows (196 observed; 14 explicitly
unobserved). Over 93 non-requests tasks, repair T0/T1/T2/T3/T4 counts are
3/0/28/60/2; V4 counts are 22/2/22/45/2, with 84 observed V4 tasks. Highest-tier
task lists contain 62 T3 and two T4 tasks. T4 is limited to
`matplotlib__matplotlib-20676` and `matplotlib__matplotlib-21568`, with guarded
tool-first cached-wheel content. Of the 83 comparable tasks, 60 are T3 or T4.
T3 explicitly includes legitimate solving; it does not establish an environment
leak. All original raw findings, totals and image receipts remain unchanged.

The guard removes 24 matched probes (three raw finding occurrences); one further
raw content match is JSON-serialization-only. The Django history hit is
model-first working-tree content, with no source commit supplying the additions.
The 40 raw cache flags resolve to 36 nonempty source/filename observations, two
metadata-only observations, one empty listing and one other-path output. One
flag addresses both masks, so the path table has 41 observations.

Validation: all 24 new interpretation tests pass; the focused audit suite has
167 passes. Full suite: 1,566 passed, 7 skipped, 6 failed, 17 errors; the exact
failed/error IDs equal the reference, with zero new IDs and zero newly passing
reference failures. The standalone standard-library verifier independently
recomputes tiers, CSV and totals, checks original inventory hashes, and validates
chronological probe/speaker receipts. The reusable rerun entry point was tested
only on synthetic folders. No real rerun was audited. No push is authorized.

Scope incident: the first guidance-file search in this follow-up included the
parent projects directory. It returned no paths or contents. Subsequent searches
use explicit allowed paths; no blinded run payload has been opened or audited.
