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

## Interpretive follow-up

- Preserve every raw finding, severity and image receipt byte for byte. A new
  `tiers/inventory_manifest.json` pins them; the old report text is preserved
  verbatim under the raw-rule inventory heading and in `tiers/raw_rule_inventory.md`.
- T4 requires eligible tool-output-first content or an absent hidden test name.
  T3 is model-first evidence and cannot distinguish memory from solving. Own
  writes and later tool echoes do not turn a model-produced fix into T4.
- Accept the user's reviewed setup-commit facts for the existing 100-image
  inventory. Setup commits alone do not demonstrate answer access.
- Count content occurrences in verified pinned base archives. Require 25
  non-whitespace characters and fewer than three base occurrences; keep the
  hidden-name rule separate. Also distinguish raw JSON escaping from content
  actually present in decoded messages.
- Per-run CSV rows include explicitly unobserved missing role trajectories.
  Unique-task role totals cover 93 non-requests tasks and use the maximum over
  runs. T3/T4 task lists use the maximum over both roles; requests are excluded.
  The 83 comparable tasks come from the historical archive pin inventory.
- Reinspect stored cache command results; never execute those agent commands.
  Separate returned source, filenames, member listings, metadata and empty
  listings. A cache access alone does not establish T4 without answer content.
- The initial parent-directory guidance search was broader than permitted and
  returned no paths or contents. No blinded run payload was opened; all later
  access is restricted to explicit allowed paths.
- The reusable arm audit has no model or Docker calls. Only synthetic folders
  are used for its validation in this session. No push is authorized.
- Final interpretation: highest-tier lists have 62 T3 and two T4 tasks; 60/83
  comparable tasks are T3/T4. The T4 tasks are the two historical Matplotlib
  cache-read cases. The Django history match is model-first working-tree content;
  source commit is null, with the pinned base hash recorded only as identity.
- Content guard removes 24 probe matches and three raw occurrences. A fourth
  raw content occurrence is a match to JSON escaping rather than decoded text.
  Cache reclassification covers all 40 raw flags and never upgrades an access
  to T4 without qualifying tool-first answer content.
- Validation: 24 new synthetic tests, 167 focused audit passes, full-suite
  1,566 passed / 7 skipped / 6 failed / 17 errors. Exact failed/error IDs match
  the reference. Independent tier recomputation and chronological receipts pass.
