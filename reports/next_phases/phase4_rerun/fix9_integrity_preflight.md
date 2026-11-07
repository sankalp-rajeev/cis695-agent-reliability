# Fix 9: source integrity, generated-input pinning, and pristine-image preflight

Preflight passed on branch `experiment/v2-execution-repair`: clean worktree, local HEAD/upstream/live origin all `52ec6c7adba9779253bab19d5e9d93b282bcdc4c`. No attempt-1 outcomes or correctness labels were decoded or used.

## Plan and quarantine before implementation

`f212342` committed the integrity-stop rule, attempt-1 quarantine, and non-halting generated-input evidence rule before Fix 9 code. Existing hypothesis thresholds, B1/B2, and verdict definitions were not changed. An integrity halt aborts the attempt; a label-free repair requires a new executor version, new freeze tag, and restart from task 1. An old tag is never moved.

Attempt 1 is marked **aborted, not analyzed** in `runs/phase4_v2_serial_20261107T173952Z/QUARANTINE.json`. Its retained files were hashed as opaque byte streams: no JSON/raw-output decoding, outcome aggregation, scoring, or use in this fix. The [committed quarantine manifest](attempt1_quarantine_manifest.json) covers 1,128 original files and identifies the 35 completed task directories by file existence only. The local manifest copy has SHA-256 `c6f0c838bfe5d8a37d7c3ff24712479ae6893a46b7db3360bcf60984dffe7fce`.

The quarantined captures remain in place. `phase4-plan-frozen` remains at `d31f8928d5e2f2a6641183005685b0486c07d41e`; no new freeze tag or controlled attempt was created.

## Fix 9 implementation

The implementation is one commit, `84840b7`, with 22 Fix 9 unit cases. It introduces `BaseSourceSpec` and a source verifier in `src/reliability/verifier/source_integrity.py`:

1. Verify the frozen tar SHA-256 and declared base commit.
2. Read effective `export-subst` attributes from the **base tree only**, using an isolated Git directory and index populated from that commit. Worktree/patch changes, `.git/info/attributes`, global/system attributes, and Git templates cannot grant exceptions. Existing refs are copied only into this temporary metadata repository so Git pretty formats retain their reference context; no user-repository tag is created or moved.
3. For each marked file, require pristine image bytes to equal the base Git blob. Independently require the frozen archive bytes to equal that blob with only its `$Format:...$` expressions expanded. Literal bytes must be identical. A real edit, an unrelated archive change, or an unmarked-file mismatch raises `SourceIntegrityError` and removes the container before runtime.
4. Image Git versions that lack `%(describe:...)` use its equivalent read-only `git describe` operation. Git's automatic abbreviation length can vary with object-database size. Where the archived expansion selects a different **default** length, the verifier independently reproduces the value with `--abbrev=N`; a prefix match alone is never acceptance. Explicit format abbreviations cannot be overridden. The exact commands and computed values are retained as proofs. Unknown/unproved differences remain failures.

There is no blanket `_version.py` exemption, AST-only equivalence test, image-file rewrite, configuration restoration, or policy change.

### Runtime generated-input evidence

`TaskContainer` inventories all untracked version-named Python modules, **including ignored files**, and pins their original hashes for its lifetime. This intentionally conservative inventory can also include handwritten version helpers in untracked submodules; every listed path is explicit. Creation, deletion, and content changes are detected.

The executor records before/after snapshots for patch application, native collection, execution, and each isolated confirmation (including confirmation-level boundary snapshots). Snapshots are retained on exceptional exits too. Execution's after-snapshot follows timeout process cleanup. Audit time consumes the pass deadline; final hashing/cleanup may add wall time after the native execution cap.

Any change adds **`GENERATED_INPUT_CHANGED`** to the pass and task evidence, including changes seen in confirmations or a baseline-abstention path. It does **not** halt, replace a test outcome, or change Policy C/S verdicts. Inventory failures are separately visible as `GENERATED_INPUT_AUDIT_ERROR`. Generated evidence is serialized, hashed, and round-trips through `RunResult`; signal records expose the task flags. Old baseline caches are invalidated by the Fix 9 revision.

Real container execution now requires a pinned `BaseSourceSpec` and a verified pristine-source receipt. A future, separately authorized launcher must supply the frozen base commit/archive/hash and abort the attempt on `SourceIntegrityError`. The old quarantined attempt-1 launcher is not a compatible way to start this executor version. The source-only audit deliberately uses `halt=False` to enumerate all pristine mismatches, not to authorize runtime despite them.

### Preflight method and scope

`scripts/phase4_integrity_preflight.py` reads the independently frozen 83-task metadata and archive source, pins each existing image by its immutable frozen image ID, and uses one container at a time with `--pull=never`, `--network none`, and `--cpu-shares 2048`.

The source comparison covers archived Python files, runner configuration files, `bin/test`, and every base-commit `export-subst` file (including non-Python `.git_archival.txt`). It is not a claim to compare every binary/data file in every image. Generated inventory is taken before and after the source-only probe. No candidate is applied; no selector, native collector, test runner, confirmation, or repository package is invoked. The probes execute only stdlib file hashing and read-only Git metadata/export commands. They do not consult the quarantined run.

Two preliminary source-only audits exposed old-image Git's unsupported describe formatter and automatic abbreviation differences. Their diagnostic records are retained separately under ignored `runs/fix9_source_preflight_native_git_initial` and `runs/fix9_source_preflight_default_describe_abbreviation`. The tables and sealed receipts below use only the final, complete 83-image audit of commit `84840b7`. None of these audits performed collection or test execution.

## Final 83-image findings

All **83** pristine images were audited in **167.86 s**. **76 verified; 7 have unresolved integrity mismatches; zero probe errors.** There were **25 tasks with raw byte differences**: 18 were accepted only after complete export proofs, and 7 remain rejected. Sphinx-7910 has two differing files, giving 26 differing file entries. These are source-integrity statuses, not test outcomes.

**No source was restored or candidate patch applied. No collection, task test, or confirmation ran.** The production guard would stop on each unresolved mismatch; the source-only audit continued expressly to list all 83 images. A new controlled run is not ready to launch under the strict rule while these seven differences remain unresolved.

### Every raw difference and its cause

| Task | File | Decision / cause |
|---|---|---|
| `astropy__astropy-13977` | `pyproject.toml` | Image build-time setuptools==68.0.0 configuration pin; not export-subst; rejected without restoration |
| `astropy__astropy-14365` | `pyproject.toml` | Image build-time setuptools==68.0.0 configuration pin; not export-subst; rejected without restoration |
| `astropy__astropy-14508` | `pyproject.toml` | Image build-time setuptools==68.0.0 configuration pin; not export-subst; rejected without restoration |
| `matplotlib__matplotlib-14623` | `lib/matplotlib/_version.py` | Accepted: image equals base blob; archive equals only proven Format expansion |
| `matplotlib__matplotlib-20488` | `.git_archival.txt` | Accepted: image equals base blob; archive equals only proven Format expansion |
| `matplotlib__matplotlib-20676` | `.git_archival.txt` | Accepted: image equals base blob; archive equals only proven Format expansion |
| `matplotlib__matplotlib-22719` | `.git_archival.txt` | Accepted: image equals base blob; archive equals only proven Format expansion |
| `matplotlib__matplotlib-22871` | `.git_archival.txt` | Accepted: image equals base blob; archive equals only proven Format expansion |
| `matplotlib__matplotlib-23299` | `.git_archival.txt` | Accepted: image equals base blob; archive equals only proven Format expansion |
| `matplotlib__matplotlib-23476` | `.git_archival.txt` | Accepted: image equals base blob; archive equals only proven Format expansion |
| `matplotlib__matplotlib-24026` | `.git_archival.txt` | Accepted: image equals base blob; archive equals only proven Format expansion |
| `matplotlib__matplotlib-24177` | `.git_archival.txt` | Accepted: image equals base blob; archive equals only proven Format expansion |
| `matplotlib__matplotlib-24637` | `.git_archival.txt` | Accepted: image equals base blob; archive equals only proven Format expansion |
| `matplotlib__matplotlib-24970` | `.git_archival.txt` | Accepted: image equals base blob; archive equals only proven Format expansion |
| `matplotlib__matplotlib-25122` | `.git_archival.txt` | Accepted: image equals base blob; archive equals only proven Format expansion |
| `matplotlib__matplotlib-25287` | `.git_archival.txt` | Accepted: image equals base blob; archive equals only proven Format expansion |
| `matplotlib__matplotlib-25479` | `.git_archival.txt` | Accepted: image equals base blob; archive equals only proven Format expansion |
| `matplotlib__matplotlib-26291` | `.git_archival.txt` | Accepted: image equals base blob; archive equals only proven Format expansion |
| `pydata__xarray-4966` | `.git_archival.txt` | Accepted: image equals base blob; archive equals only proven Format expansion |
| `pydata__xarray-6599` | `.git_archival.txt` | Accepted: image equals base blob; archive equals only proven Format expansion |
| `pydata__xarray-6744` | `.git_archival.txt` | Accepted: image equals base blob; archive equals only proven Format expansion |
| `sphinx-doc__sphinx-10323` | `tox.ini` | Image tox.ini adds pytest -rA reporting option; rejected |
| `sphinx-doc__sphinx-10435` | `tox.ini` | Image tox.ini adds pytest -rA reporting option; rejected |
| `sphinx-doc__sphinx-10466` | `tox.ini` | Image tox.ini adds pytest -rA reporting option; rejected |
| `sphinx-doc__sphinx-7910` | `setup.py` | Image setup.py has dependency compatibility ceilings and added markupsafe pin; rejected |
| `sphinx-doc__sphinx-7910` | `tox.ini` | Image tox.ini adds pytest -rA reporting option; rejected |

All expected, observed, and base-blob SHA-256 values are in [difference_causes.csv](fix9_integrity_preflight/difference_causes.csv). The unmodified machine output is [differences.csv](fix9_integrity_preflight/differences.csv). Per-task compressed source receipts retain raw mismatch bytes and exact expansion/describe proofs; non-export source diffs are saved separately.

The seven unresolved tasks are Astropy-13977, -14365, -14508 and Sphinx-10323, -10435, -10466, -7910. Their image files differ from both the archive and the declared base blob. The Astropy differences are setuptools==68.0.0 build-requirement pins. Sphinx tox files add `-rA`; Sphinx-7910 also has dependency compatibility pins in setup.py. No new exception was introduced for these edits.

### Every repository with base-commit export-subst files

| Repository | Tasks | Marked paths |
|---|---:|---|
| `matplotlib/matplotlib` | 15 | `.git_archival.txt`, `lib/matplotlib/_version.py` |
| `pydata/xarray` | 3 | `.git_archival.txt` |

These are the only two repositories with enabled `export-subst` on base-tree files in this cohort. The [complete task/path list](fix9_integrity_preflight/export_subst_files.csv) includes all 18 tasks. Matplotlib-14623 uses the Versioneer Python file; the other Matplotlib and xarray cases use `.git_archival.txt`. Eight newer Matplotlib images required the independently verified describe/abbreviation compatibility proof, rather than trusting their older Git formatter. All 18 cases satisfy the same literal-byte and base-blob conditions.

### Generated-input inventory

The inventory pinned **50 untracked version-named Python inputs across 27 tasks**. The [complete inventory](fix9_integrity_preflight/generated_inventory.csv) gives every path and hash; this conservative set includes ignored build outputs and version helpers in untracked submodules. No generated-input change or audit error was observed during these source-only probes. This does not predict their behavior during future collection/execution; those runtime stages will be audited by the new executor.

## Verification and boundaries

The 22 Fix 9 unit cases cover real source edits (marked and unmarked), altered archive literals, an archive-expanded image that improperly matches the tar instead of the base blob, non-base attribute injection, old-Git describe compatibility, independently verified default abbreviation queries, ignored-file discovery, generated creation/deletion/change flags, exceptional stage exits, confirmation evidence, and unchanged healthy C/S verdicts when only the informational flag is set. The targeted executor/validation suite passed before the final pretty-format extensions; the final Fix 9 suite has 22 passes.

The full unit-suite result will be recorded separately after this audit report is committed. No controlled-run outcome analysis is part of verification. The old freeze tag remains unchanged. No new freeze tag or controlled launch is authorized or performed by this audit. Future runtime requires a new reviewed freeze and starts at task 1; none of attempt 1 may be reused as analyzed evidence.

## Reproduction

```bash
env -u PYTHONPATH .venv/bin/python scripts/phase4_integrity_preflight.py \
  --output /tmp/fresh_fix9_source_preflight
```

[manifest.json](fix9_integrity_preflight/manifest.json) records the final implementation commit, source SHA-256 values, frozen metadata hash, and original audit-receipt hashes. [tasks.csv](fix9_integrity_preflight/tasks.csv) accounts for all 83 images. Human source diagnoses are an added report layer; the underlying source receipts and machine CSVs are unchanged. The prior cost estimates concern the pre-Fix-9 executor; no runtime cost benchmark or task execution was performed here.
