# Signal audit decisions

This is a blocked checkpoint, not an analysis result.

- D001: Apply the explicit label-exposure hard stop immediately. The initial inspection mistakenly displayed label-bearing portions of docs/results_100.md and docs/results_100.csv before Stage 5. Do not continue Stages 1–4 in this exposed context or reinterpret the exposure as an authorized Stage 5 read. No label values are reproduced in this checkpoint.
- D002: Use only the already-present local origin/main ref to create the requested new branch; do not fetch. The initial worktree was clean. Leave main and existing tags untouched.
- D003: Request a filesystem sandbox exception only for local Git metadata updates required by the authorized branch/checkpoint operations. This grants no network authorization.
- D004: The instruction to push a hard-stop checkpoint conflicts with the explicit no-network rule. Conservatively honor no network: make a local commit, leave the tree clean, and report the unperformed push. Do not attempt remote access.
- D005: Record every audit result as NOT_RUN. Preliminary path/source inspection is not independent verification and supports no claims about V1, V3, V4, repaired V2, or labels. Do not create signal-audit-sealed.
- D006: STATUS.md and this file describe the checkpoint commit itself, with Git recording its identity. Do not create an unbounded sequence of commits solely to insert the previous commit hash into status files.
- D007: The one decision needed for audit resumption is authorization to restart in a fresh, label-isolated context. Restart must enforce field allowlists before reading mixed CSV/JSON sources and restrict documentation reads to label-free reconciliation material. This checkpoint does not itself authorize restart.
