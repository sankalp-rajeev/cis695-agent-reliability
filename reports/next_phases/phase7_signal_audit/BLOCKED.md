# HARD STOP: required stored records unavailable

Stage reached: Step 0 completed; pre-Stage-1 input availability check blocked.

Exact state: the frozen task list has 83 distinct IDs, all represented in the two main manifest ID sets. None of the four directory-rule run roots exists in this workspace:

- runs/main_2_rerun_mpl/
- runs/main_3_rerun_infra/
- runs/main_50_a/
- runs/main_50_b/

Consequently all 83 required verification records are missing. This triggers the explicit hard stop: more than 17 of the 83 records missing. missing_records.csv lists every affected task and its reason. record_inventory.py and the separate standard-library-only verify_preflight.py reproduce and independently verify this blocker from approved raw IDs and filesystem entries.

One decision needed: make the original stored run trees available at the four permitted locations, preserving their contents, before restarting the audit. No other run or analysis output has been substituted.

Stages 1-6 are NOT_RUN. V1 caught/total, V3 effects, V4 classes, ACCEPT/FLAG/REJECT counts, and surviving false accepts are NOT_AVAILABLE. No audit seal or tag has been created.

Attempt 1 was aborted after label exposure; this attempt used a fresh session and a file whitelist. No prior attempt file contents or task-label sources were opened in this session.

The Step 0 checkpoint c00779d was pushed successfully. This blocker and its evidence are to be explicitly staged, secret-scanned, committed, and pushed on analysis/signal-audit; final publication is verified from Git after that operation.
