# Decisions

- Attempt 1 was aborted after label exposure; this attempt uses a fresh session and a file whitelist.
- The archive destination already existed. The exact requested git mv command preserved the prior current directory at reports/next_phases/phase7_signal_audit_attempt1_aborted/phase7_signal_audit/, retaining the existing archive. Neither prior directory was opened.
- Secret scanning inspects newly staged content blobs only. Pure renames are verified using identical Git blob IDs without opening their prohibited historical contents; they introduce no content.
- No model calls or non-Git network operations are authorized. Host Python may inspect permitted data and prepare reports; task-tree/verifier execution must occur in Docker, using local images and stored archives without networking.
- Missing evidence remains NOT_AVAILABLE or NOT_RUN and is never a PASS.
