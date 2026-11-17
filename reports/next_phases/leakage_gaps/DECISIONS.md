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
