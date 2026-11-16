# Verification evidence and reproduction

The audit producers and their Stage 1-5 outputs are frozen. Do not regenerate them to verify this report.

- Original failed receipt: independent_verification.json.
- Original failure explanation: stage6_mismatch_evidence.json; resolved blocker: verification_runs/initial_blocked.md.
- Successful full rerun: independent_verification_rerun.json and independent_verification_rerun.stdout.txt.
- Exact runtime image, source mounts, and disabled network: run_audit_container.sh and execution_environment.json.
- Isolated rerun location, command inputs, script digest, timestamps, and exit status: verification_rerun_execution.json.
- All pre/post-fix analysis hashes: pre_fix_analysis_hashes.json and analysis_outputs_unchanged.json.

To reproduce while preserving historical receipts, copy this audit directory into a temporary directory without Python caches. Make a temporary copy of run_audit_container.sh, set audit_out to the copy and audit_root to the original repository, and invoke it with verify_all.py. The script reads original raw inputs through read-only mounts and writes its fixed receipt filename only into the isolated copy. Keep that new receipt under a distinct name; the preserved failed receipt must remain unchanged. No producer or analysis module is imported by verify_all.py.

The first runtime argument correction is the isolated one-line commit cf58a54. Commit 770a717 fixes only the related expected-spec constructor argument and logs the pre-rerun form review. check_csv/check_json remain unchanged; raw diagnostics compare exactly.

From this audit directory, check the final deliverables with:

```sh
sha256sum -c artifact_manifest.sha256
```

The manifest excludes itself and Python cache files. Raw-input digests are chained through input_provenance.csv and posthoc_labels/input_sha256.csv.
