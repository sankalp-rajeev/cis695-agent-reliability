# Decisions

- 2026-11-17: The latest instruction overrides the pasted request to push. Commit
  locally on `analysis/leakage-gaps`; do not push.
- Audit only the four named historical run roots, including their V4 generator
  caches. Never access `wt-e2e`, active containers, or correctness/grader labels.
- Docker operations are image listing and our own `--rm --network none`
  containers, with a read-only root filesystem and read-only probe mount.
  Do not pull images or alter their refs, objects, or source.
- Preserve legacy findings as a multiset; changes must be additions or explicit
  rule-3 downgrades. Record hashes rather than oracle lines or test names.
- Verify pinned source archive digests through `SourceArchive` before using base
  source to classify test names. Missing evidence makes the audit incomplete.
- Existing tests and the reference failure list remain unchanged. New tests use
  invented data and temporary Git repositories or mocked Docker calls.
- Source archive inventory: 83 historical pins, 10 existing archives newly pinned
  by this audit, and 7 missing requests archives exported with read-only
  `git archive` at the manifest base commit into ignored `runs/`. All are verified
  with `SourceArchive`; the latter two groups are never represented as old pins.
- Post-image reconstruction accepts exact context and unique exact hunk offsets
  only. A missing final newline is preserved. Always reconstruct from read-only
  `git show BASE:path`, since archive export transforms can change bytes outside
  a patch hunk. An independent exact-Git-base check of all 120 blobs in all 100
  images matched the initial hash inventory and found zero present blobs.
- Enumerate all Git objects and all refs. Count both newer timestamps and base
  descendants; separately compare future commit trees and exact gold blobs.
  An image exposure is not evidence that a stored agent read it.
- Keep legacy REVIEW occurrences when the stronger ordered test-name rule adds a
  CONFIRMED finding. This preserves the original multiset without hiding new
  evidence. Record explicit rule-3 downgrades if any occur.
- No cache/theme directory is a package copy merely because its basename matches.
  Require source files, then report version metadata and match counts.
- Git refs containing slashes must not be mistaken for paths. Exclude verified
  base source paths/directories and explicit HEAD/base file selections; retain
  searches of other refs, including revision:path expressions. Synthetic tests
  cover this distinction. Version-success checks use image metadata as a fallback
  when source versions are dynamic; the stored install attempt was rechecked and
  its findings were unchanged.
- Final golden: 912 preserved legacy occurrences, zero downgrades, zero losses or
  severity violations. The report's confirmed categories remain separate from
  the question of whether a model actually used an answer. No correctness labels
  or grader outputs were consulted.
