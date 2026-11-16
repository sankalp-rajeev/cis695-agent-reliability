# HARD STOP: independent verification mismatch

Updated: 2026-11-16T19:36:56.004386+00:00. Stage reached: Stage 6. Stages 1-5 were completed and pushed, but their aggregate conclusions are provisional because the required full independent verification did not finish.

Exact failure: verify_all.py raised AssertionError comparing v1_raw_observations.json to independently rerun V1 observations. The independent run successfully compared record_inventory.csv, missing_records.csv, record_inventory_all.csv, and v1_adversarial.csv, then stopped at the detailed raw-observation JSON. It did not reach the V3, V4, recompute, or post-hoc label comparisons. See independent_verification.json.

Concrete audit-runner mistake: run_v1.py supplied allowed_paths=('some_other_package/',) for out_of_scope, but verify_all.py supplied allowed_paths=['some_other_package/']. The unchanged verifier includes that argument's representation in its diagnostic. The stored diagnostic is `path outside allowed scope ('some_other_package/',)`; the independent list invocation predicts `path outside allowed scope ['some_other_package/']`. stage6_mismatch_evidence.json records the raw finding and both source excerpts. The complete comparison stopped at the first failing artifact; this is not a claim that every other field matched.

Applicable hard stop: any verification mismatch in Stage 6; no seal. No script or output was repaired and verification was not rerun after the mismatch.

One decision needed: authorize changing only the independent audit runner to use the original tuple argument, then resume Stage 6 with a fresh full comparison. No verifier, policy, config, frozen input, or sealed Stage 1-4 output needs alteration.

Existing annotated tag: signal-audit-labelfree at d2cc07ab1036bf5a36225fcf8acf2698b5b6e8c4, pushed before Stage 5. signal-audit-sealed does not exist and must not be created while this mismatch remains. No final verified REPORT.md is claimed.

Attempt 1 was aborted after label exposure; this attempt used a fresh session and a file whitelist. Label access began only after the label-free tag was pushed.
