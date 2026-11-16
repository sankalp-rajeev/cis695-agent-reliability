# Decisions

- Attempt 1 was aborted after label exposure; this attempt uses a fresh session and a file whitelist.
- The archive destination already existed. The exact requested git mv command preserved the prior current directory at reports/next_phases/phase7_signal_audit_attempt1_aborted/phase7_signal_audit/, retaining the existing archive. Neither prior directory was opened.
- Secret scanning inspects newly staged content blobs only. Pure renames are verified using identical Git blob IDs without opening their prohibited historical contents; they introduce no content.
- No model calls or non-Git network operations are authorized. Host Python may inspect permitted data and prepare reports; task-tree/verifier execution must occur in Docker, using local images and stored archives without networking.
- Missing evidence remains NOT_AVAILABLE or NOT_RUN and is never a PASS.

## Record availability hard stop (2026-11-15T01:06:10.650554+00:00)

- Before task execution, check whether the directory-rule input roots exist. None of runs/main_2_rerun_mpl, runs/main_3_rerun_infra, runs/main_50_a, or runs/main_50_b exists, including as a symlink entry. Therefore no approved record path under any of those roots is available.
- Manifest ID overlaps with the 83 frozen tasks: main_2_rerun_mpl = 1; main_3_rerun_infra = 3; main_50_a = 39; main_50_b = 44. The two main manifests cover all 83 IDs. No manifest fields other than task IDs were used or emitted.
- Apply the explicit greater-than-17-missing-records hard stop immediately: all 83 are missing. Do not substitute Phase 4 results, similarly named runs, prior analysis, or post-hoc material for the required original records. Do not infer any original signal or decision from absence.
- Independent verification here covers only the missing-input inventory, not audit Stages 1-5, and is not Stage 6. No scientific audit finding or sealed report is claimed.
- The initial Docker image-list attempt could not connect to the daemon because of socket permissions. No container ran; no escalation is needed because the missing-record hard stop already requires stopping.
- One decision needed: restore or mount the original stored run trees at the four permitted paths, without changing their frozen contents, before resuming a label-isolated audit. No permission to broaden the whitelist or invent outcomes is assumed.

## Resume and successful preflight (2026-11-16T19:07:59.058528+00:00)

- The user confirmed restoration of the four allowed run trees and explicitly resumed attempt 2. Do not repeat Step 0 or read either archived prior directory.
- Regenerate record_inventory.csv (83 rows) and missing_records.csv (zero rows), retaining the historical missing-record evidence in Git history. Select reruns by directory existence before the corresponding original main run; verify manifest ID membership. There are zero missing required records.
- A separate standard-library verifier independently recomputes membership and selection from approved raw task/manifest IDs and filesystem existence, and compares every output row. This is a preflight check, not Stage 6 or a verifier outcome.
- The renewed preflight clears only the old missing-record blocker. The user's instruction explicitly retains the whitelist and stage order; it does not authorize reading referenced files automatically.

## Stage 1 whitelist hard stop (2026-11-16T19:07:59.058528+00:00)

- Conservative reading of "a real clean candidate patch": use an actual frozen submitted candidate for the passing control, rather than silently replacing it with an invented source edit. Frozen task metadata identifies reports/v2_discovery_cleanup/frozen_83/patches/astropy__astropy-13977.patch. That file exists; its contents were not opened, hashed, copied, imported, or executed. The expected patch digest comes only from permitted tasks.json.
- The corresponding stored source archive at /home/sankalp/cg_repos/task_archives/astropy__astropy-13977.tar is explicitly allowed. Its SHA-256 matches frozen metadata; no archive restoration or network access is needed. This does not make the separate candidate patch an allowed input.
- The exact whitelist allows tasks.json, manifest IDs, selected verification records, stored source archives, the specified Phase 4 results, verifier Python sources, the specified policy document, and unit tests. It does not include frozen_83/patches/*.patch or extend to files merely referenced in tasks.json. The sanitized selected record provides a patch SHA-256, not candidate patch text.
- Apply the explicit hard stop: "Any file outside the whitelist being needed before Stage 5. If so, stop and say which file and why; do not open it." Do not skip Stage 1 to perform later stages, fabricate a control result, or treat this absence of execution as PASS.
- One decision needed: add read-only access to reports/v2_discovery_cleanup/frozen_83/patches/astropy__astropy-13977.patch to the pre-Stage-5 whitelist for the V1 control. Keep the patch and every other frozen artifact unchanged.
- Attempt 1 was aborted after label exposure; this attempt used a fresh session and a file whitelist.
