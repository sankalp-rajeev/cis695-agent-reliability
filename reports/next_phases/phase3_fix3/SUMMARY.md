# Phase 3 Fix 3 — runner-aware static and native ID validation

The runner-aware rule was committed and pushed first in `55a5fd6`; the local
worktree environment and full-suite baseline are separate in `2e57d56`.
The earlier 476 non-TestCase-owner labels are all Django: 476 Django, 0 pytest,
0 SymPy. Their owner inventory, 2,347 inherited identities and 10 labels without
a runnable owner are unchanged. B1/B2, thresholds and selected families are unchanged.

## Implementation

`id_validation.py` parses source without importing it. It resolves imports,
relative re-exports, unittest ancestry and C3 effective method owners. Django
requires a TestCase owner. Pytest accepts TestCase subclasses and ordinary
classes under the effective pytest.ini / pyproject.toml / tox.ini / setup.cfg
class patterns, with no custom inherited initializer and no inherited false
`__test__`. Properties, plain Django functions, helpers and missing objects
have explicit reasons. Decorated callables retain their decorations and owner
classification. Non-runnable owners expand only to runnable subclasses of the
selected class that inherit the same effective method without overriding it.

Before execution, `ContainerTestExecutor` switches to the requested tree, takes
its source/config snapshot, runs the static layer and obtains native receipts.
Pytest uses `--collect-only -q` with a collection-receipt plugin, so verbosity,
ANSI and nested config root directories cannot corrupt IDs. Django sets up its
runner and dry-loads each label with `loadTestsFromName`; an owner check keeps
unittest from invoking helper factories. Collection is isolated by module and
per-label loader errors are captured; execution batching is unchanged (Fix 4
is still pending). Native results override static predictions and disagreements
are retained. Static and native INVALID_ID reasons, messages, owner-instance
counts and task/tree context are written to hashed validation evidence.

`INVALID_ID` is distinct from NOT_RUN and excluded from scoring. If every
selected slot is invalid, the result is NOT_AVAILABLE. Collection timeouts stay
missing evidence. Concrete identities map back to the original selected slots;
no returned identity outside a selected instance/parameter family is accepted.
All expanded instances must validate and be admitted before the original slot
is admitted. Shared concrete instances are deduplicated without losing their
original slot ownership. Concrete Django regression keys remain runnable IDs.
The baseline cache revision changes so old unvalidated captures cannot mix with
validated live results. XFAIL/XPASS and REGRESSION_ERROR behavior is retained.

## Offline acceptance (no Docker or repository source execution)

All 83 frozen selections were checked against verified base archives and the
candidate-patched source trees: **115,364 selected tree slots**. Candidate patch
hashes and patch contexts were checked; no correctness sidecar was opened or joined.

| Recorded abort class | Batches with a structural offender flagged | Identified candidate labels flagged |
|---|---:|---:|
| Property | 8 / 8 | 8 / 8 |
| Module-level helper | 4 / 4 | 4 / 4 |
| Non-test function / non-runnable owner | 98 / 98 | 102 / 116 |

The remaining 14 candidates in the function-error rows are runnable TestCase
methods sharing an ambiguous callable name. They are correctly retained. All
**796/796 TestCase-owned collateral task/labels remain runnable on base and on
the candidate-patched tree**. This counts labels, not doubled tree slots.

Not-found coverage is separate: **504/714 explicit not-found batches** receive
a structural flag, including **282 literal AST not-found labels**. The other
flags are non-runnable owners/helpers/attributes. The 130 xmlschema dependency
batches have structurally present source and need native diagnostics; they are
not fabricated as AST not-found cases. Across all 942 aborts, 616 have at least
one flagged candidate (620/2,614 candidate occurrences). Two of those batches
are GIS guard batches containing an additional invalid candidate; this does not
claim that the guard itself was repaired. No prevented-abort or executed-test
recovery rate is inferred from this offline check.

`abort_acceptance.csv` and `abort_classes.csv` preserve every occurrence and the
candidate ambiguity. `static_ids.csv.gz` is the full per-label ledger;
`task_tree_counts.csv` provides per-task/tree INVALID_ID and instance counts.
Its `expanded_slots` counts static owner-expansion candidates, including zero-owner
candidates; `owner_expanded_instances` counts the actual predicted identities.
`collateral_acceptance.csv` and `collateral_patched_acceptance.csv` audit the 796.

## Collection-only Docker smoke (base trees only)

Tasks were fixed by runner/repository identity, without outcomes or correctness
labels: the supplied Django and Astropy tasks and the first sorted SymPy task.
The table reports the final implementation pass. No test executor or scorer
was invoked; **zero test bodies executed and zero test outcomes recorded**.

| Task | AST + native validation (s) | Native collection (s) | INVALID_ID | Owner slots expanded | Owner instances |
|---|---:|---:|---:|---:|---:|
| django__django-11820 | 46.93 | 38.18 | 42 | 21 | 63 |
| astropy__astropy-13977 | 136.85 | 114.25 | 121 | 65 | 330 |
| sympy__sympy-13480 | 29.92 | 0.45 | 781 | 0 | 0 |

Django and Astropy have 3,167 and 11,525 runnable concrete collection identities,
respectively (including parameters), mapped to unchanged selections of 3,167
and 3,080 slots. The frozen SymPy runner is pytest, absent in that image; all
781 IDs receive native load errors containing that diagnostic. No bin/test
adapter was added: that is Fix 5. An explicit unsupported runner fails closed
with missing validation evidence and never falls through to test execution.

The images use synthetic Git HEADs. All archived Python/config files were
hash-verified before collection: 2,574 Django, 934 Astropy, 1,181 SymPy. Astropy's
image had a build-time setuptools version pin in pyproject.toml; the archived
base config was restored inside the disposable container and reverified before
collection. No Python test/source file was changed. Containers had network none
and were removed afterward. Static/native disagreements are reported explicitly:
26 Django, 107 Astropy, 781 SymPy. Optional imports/collection skips and missing
runners are native information, not facts an AST-only check can establish.

`collection_only_summary.csv` gives timings and counts. Each task directory has
collection receipts, source identity, implementation hashes and captured messages
keyed by SHA-256. `static_native_disagreements.csv` is the per-label disagreement
ledger. The collection receipts contain IDs and diagnostics, not test outcomes.

## Full unit suite and environment

The worktree has its own pinned `.venv`, CPython 3.11.17, with an editable import
from this worktree's src. The interpreter-path guard passes. No lockfile or
project config change was needed.

| Full unit run | Passed | Failed | Skipped | Setup errors |
|---|---:|---:|---:|---:|
| Before Fix 3 | 1,023 | 6 | 6 | 17 |
| Final Fix 3 | 1,074 | 6 | 6 | 17 |

All **51 new Fix 3 tests pass**. The exact failure/error set is unchanged; see
`unit_summary.json` and `preexisting_unit_failures.csv`. One test needs an absent
ignored patch fixture; three need unavailable Landlock isolation; one expects
pre-Fix-2 config fields; one failure plus 17 setup errors reject historical
frozen source hashes after the prior repairs. Those unrelated tests/seals were
not changed. Ruff passes for all changed source/test files and new scripts.

## Reproduction and artifacts

Use the local environment with PYTHONPATH cleared:

```bash
env -u PYTHONPATH .venv/bin/python scripts/phase3_fix3_offline.py --output /tmp/fix3_fresh
# Full ledger is stored compactly; gzip -n preserves deterministic output.
gzip -n -c /tmp/fix3_fresh/static_ids.csv > /tmp/fix3_static_ids.csv.gz
env -u PYTHONPATH .venv/bin/python scripts/phase3_fix3_smoke.py \
  --task django__django-11820 --output /tmp/fix3_django_collection
# Repeat collection only for astropy__astropy-13977 and sympy__sympy-13480.
env -u PYTHONPATH HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 \
  .venv/bin/python -m pytest tests/unit -q -o addopts=''
```

`manifest.json` hashes offline inputs and the static implementation. The artifact
manifest hashes packaged results and records the uncompressed ledger digest.
Result commit: resolve `git log -1 --format=%h -- reports/next_phases/phase3_fix3/SUMMARY.md`.
Stop point: Fix 3 only. No Fix 4, Fix 5 adapter, controlled rerun or correctness-label
analysis has started.
