# Fix 10: pristine integrity preflight

**83/83 VERIFIED; no remaining mismatch.** The source-only audit ran serially in **171.257 s**, using frozen immutable image IDs, `--pull=never`, `--network none`, and `--cpu-shares 2048`. No candidate patch, native collection, test execution, confirmation, correctness label, or attempt-1 outcome was used. Attempt 1 remains quarantined, aborted and not analyzed.

The audit found raw image/archive byte differences in 25 tasks (26 files). Eighteen tasks have exact export-subst proofs (15 Matplotlib, three xarray); seven tasks have exact pre_install proofs (eight files). No blanket file exemption or source restoration is used. The export-subst repositories remain `matplotlib/matplotlib` and `pydata/xarray`.

## Pre_install proofs

| Task | Spec repo/version | Files | Image build script corroboration |
|---|---|---|---|
| astropy__astropy-13977 | astropy/astropy / 5.1 | pyproject.toml | no image script |
| astropy__astropy-14365 | astropy/astropy / 5.1 | pyproject.toml | no image script |
| astropy__astropy-14508 | astropy/astropy / 5.1 | pyproject.toml | no image script |
| sphinx-doc__sphinx-10323 | sphinx-doc/sphinx / 5.0 | tox.ini | no image script |
| sphinx-doc__sphinx-10435 | sphinx-doc/sphinx / 5.0 | tox.ini | no image script |
| sphinx-doc__sphinx-10466 | sphinx-doc/sphinx / 5.0 | tox.ini | no image script |
| sphinx-doc__sphinx-7910 | sphinx-doc/sphinx / 3.2 | setup.py, tox.ini | no image script |

For each file above, frozen archive bytes equal the base Git blob. Replaying every command from the selected spec, in order, on copies of all target base blobs in an isolated host temporary directory yields exactly the image bytes. This independently proves the Astropy setuptools pin, Sphinx pytest `-rA` change, and Sphinx-7910 dependency pins. The image is never rewritten by the proof.

Every affected image returned **"no image script"** at the six checked setup paths: `/root/setup_repo.sh`, `/root/setup_env.sh`, `/setup_repo.sh`, `/setup_env.sh`, `/tmp/setup_repo.sh`, `/tmp/setup_env.sh`. The snapshot alone is accepted under the amended rule. The script reader rejects a present script unless its complete ordered source-edit command subsequence equals the spec; unit tests exercise matching, extra, missing, and reordered commands. Receipts retain the exact paths checked.

## Provenance

The project still uses **swebench 5.0.2**, which has no pre_install specifications. The separate **4.0.4 wheel** was downloaded from the [PyPI wheel URL](https://files.pythonhosted.org/packages/e4/65/bf9f45764317150c92fe9a0c37a0c4556c13eecc8878d4f92ffb3d31c861/swebench-4.0.4-py3-none-any.whl), SHA-256 `4e315ac60ff7b5b7186592b84d22df9befd898bba296a6b9665fdb3487fcd8f7`. It is stored in ignored `runs/phase4_fix10_provenance/`, outside the project environment. It was neither installed nor imported. Only pre_install fields of the Python constituent `MAP_REPO_VERSION_TO_SPECS_PY` were read through the restricted AST interpreter. All 83 required repo/version specs exist.

[Provenance](fix10_provenance/provenance.json) and the [four-column projection](fix10_provenance/dataset_projection.json) record the existing pinned Verified snapshot, original Arrow SHA-256, projection SHA-256, wheel URL and hash, and all 83 metadata identities. Arrow IPC included_fields was restricted to instance_id, repo, base_commit, version before decoding any batches. The whole original file was hashed opaquely; no other column values were decoded. Every task source receipt independently records wheel/source hashes, package version, spec key, exact commands, dataset identity and corroboration.

## Generated inputs and receipts

The pristine inventory contains **50 untracked version-named Python inputs across 27 tasks**, including ignored modules. No input changed across the source-guard probes and no generated audit error occurred. This is a pristine inventory, not a test outcome. The executor retains non-halting GENERATED_INPUT_CHANGED evidence for runtime stages.

[summary.json](fix10_integrity_preflight/summary.json), [tasks.csv](fix10_integrity_preflight/tasks.csv), [differences.csv](fix10_integrity_preflight/differences.csv), and [generated_inventory.csv](fix10_integrity_preflight/generated_inventory.csv) contain the machine accounting. Per-task compressed source receipts include hashes and byte proofs. [manifest.json](fix10_integrity_preflight/manifest.json) seals the audit source, frozen metadata, wheel/projection identity and receipts at Fix 10 implementation commit `39a8d54`.

The launcher is documented in [phase4_launcher.md](phase4_launcher.md). Full-suite verification is in [fix10_unit_summary.json](fix10_unit_summary.json): **1,192 passed, 6 failed, 6 skipped, 17 errors (18.92 s)**, with exactly the existing 23 failure/error identities. All 17 new Fix 10 and 12 launcher cases passed. Existing reasons are the missing ignored Django patch fixture, unavailable Landlock ABI >=4, a stale historical config assertion, and historical frozen source/evidence seals; [baseline failure list](../worktree_environment/baseline_failures.csv). No unrelated test, fixture or historical seal was changed.

No new tag or controlled attempt was created. The original freeze tag remains unchanged. This report prepares the next approval point; it does not authorize or start a run.
