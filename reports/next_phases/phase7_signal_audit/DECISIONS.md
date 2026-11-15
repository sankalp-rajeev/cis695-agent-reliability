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
