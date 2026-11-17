# Interpretation layer

This layer supplements the raw audit at `77ba8c1`; it does not rewrite any raw
finding, severity, image receipt or raw total. `inventory_manifest.json` pins all
original inputs. `raw_rule_inventory.md` is the original report verbatim, also
preserved under the raw-rule inventory section of the main report.

`task_tiers.csv` contains one row per task/run/role, including explicit unobserved
rows for missing role trajectories: 210 rows, 196 observed. The 100 tasks include
seven requests tasks, marked `Excluded`. Unique-task role totals use the maximum
over stored runs and contain 93 tasks each. Unobserved T0 rows mean no evidence,
not a clean audited trajectory. T3 and T4 task lists use the maximum over both
roles/runs; the comparable cohort is the 83 historically pinned source archives.

The highest applicable tier wins:

| Tier | Required evidence |
|---|---|
| T0 | No evidence for a higher tier; observation coverage is separate. |
| T1 | A history command showed only the accepted setup commit. |
| T2 | Fetch/history/oracle-field awareness, or cache probes, without qualifying tool-first answer content. |
| T3 | A base-absent hidden name occurs model-first before a successful defining write; or distinctive content is model-first, including own writes. This cannot distinguish memory from solving. |
| T4 | Guarded gold/test-patch content or a base-absent hidden name is tool-first, before model production. |
| Excluded | The seven requests tasks retain an underlying tier but contribute to no contamination-tier totals. |

## Facts and chronology

`artifacts/<run>/<role>/<iid>.json` records separate interpretive facts and links
raw findings by their original index. Individual answer facts have a single
`first_seen_in` value. The CSV field aggregates these labels as a JSON list.
Gold content and hidden names are represented only by hashes. Trajectory receipts
record message line, speaker, offset/length and text hash; they do not contain
source strings. The independent verifier checks the slices and first speaker
against decoded trajectories, without importing `reliability`.

Content probes are the existing problem-subtracted/base-reduced audit probes,
including supplemental model-first matches that the raw audit intentionally
suppressed as agent-authored. Every match counts occurrences in the verified base
archive. A content probe requires at least 25 non-whitespace characters and fewer
than three base occurrences to support T3/T4. Hidden names use a separate
base-absence rule. Successful defining writes are checked in trajectory order.
A raw match that exists only because of JSON escaping is recorded separately and
cannot support T3/T4.

T1 relies on the user's accepted main-study image inventory: the only post-base
commit is setup, with no gold added-line matches or exact gold post-image blobs.
For reusable entry points, image identity must match the existing reviewed
inventory or the tree/mode/metadata checks must establish setup-only exposure.

## Focused checks

`history_gold_checks.json` links the Django history finding to its command hash,
two probe hashes, base counts, lengths, and first speaker. The matched additions
were model-produced working-tree content, not content obtained from a source
commit. `source_commit` is null; the recorded pinned base hash is an identity
reference. A default working-tree diff compares against the Git index.

All 40 raw masked-read findings survive. Cache receipts distinguish source,
filenames, archive members, file/directory metadata, empty directory listings and
output from other paths. The path table has 41 entries because one raw command
addressed both masks. The raw cache diagnostic includes requests, as requested;
contamination-tier totals exclude those tasks. Cache presence alone never gives
T4; eligible answer content must be tool-first.

## Reproduction

Run from this worktree, using only its environment:

```sh
export HF_HOME=/home/sankalp/projects/wt-leakage/runs/hf_home
export HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1
env -u PYTHONPATH PYTHONPATH=src .venv/bin/python scripts/audit_leakage_tiers.py
env -u PYTHONPATH PYTHONPATH=src .venv/bin/python scripts/verify_leakage_gaps.py
env -u PYTHONPATH PYTHONPATH=src .venv/bin/python -m pytest -p no:cacheprovider -rfE
```

`--refresh-receipts` regenerates command attributions, tiers, CSV, summary and the
report from existing interpreted facts. Use the full command when trajectories,
probes or base source change. The offline dataset cache remains 15,484,578 bytes.

The reusable entry point for a future completed rerun is:

```sh
env -u PYTHONPATH PYTHONPATH=src .venv/bin/python scripts/audit_rerun_arm.py --run <output-folder>
```

It recognizes repair trajectories under `tasks/<iid>/`, V4 trajectories under
`_reproduction_cache/<iid>/`, and co-located generation trajectories under task
directories. It writes raw findings and tiers into `<output-folder>/leakage_audit`
unless `--output` is supplied. It reads the pinned dataset, archives and image
proofs; it does not launch models, Docker, tests in task images, or graders. It
never runs stored agent commands. Original trajectories are read only.

This entry point was exercised on invented temporary folders only, including its
CLI argument handling, separate role chronology and source-hash preservation.
The full suite has 1,566 passed, 7 skipped, and exactly the reference's six failed
and seventeen error IDs. All 24 new interpretation tests pass; no reference
failure changed to passing. See `unit_comparison.json` and `verification.json`.
