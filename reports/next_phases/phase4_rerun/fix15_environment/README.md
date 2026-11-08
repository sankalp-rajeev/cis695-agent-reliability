The worktree `.venv` was recreated with `uv sync --frozen --python 3.11
--link-mode copy --cache-dir /tmp/fix15_uv_cache`. The unchanged lockfile SHA-256
is recorded in before.json and after.json. A fresh cache and copied package
files avoid sharing broken package inodes with the earlier environment.

The already cached 500-row SWE-bench Verified dataset was copied byte for byte
into `/tmp/fix15_hf_datasets` because the original home cache is read-only in
the tool sandbox. dataset_cache.json records the source/target and hashes.
Test invocation uses HF_DATASETS_CACHE=/tmp/fix15_hf_datasets,
HF_HUB_OFFLINE=1 and HF_DATASETS_OFFLINE=1; it never downloads a replacement.
No attempt-2 outcomes, verdicts or labels were accessed.

The focused environment/guard suite passes all 101 tests, including test_loader,
test_no_leakage and test_sampler. test_v2_scg_paired now imports and runs; its
historical integrity barriers still reject the newer verifier source/config.
The remaining pre-existing failures are enumerated with reasons in
remaining_before_final_unit.json. The final unit-suite report follows G1.

Known isolation limitation: Linux 5.15.0-139-generic exposes Landlock ABI 1;
the isolated shadow worker requires ABI 4. It abstains without running the
classifier. No isolation fallback or integrity guard was weakened.
