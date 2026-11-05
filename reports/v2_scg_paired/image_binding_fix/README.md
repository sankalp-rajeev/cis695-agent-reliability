# Ubuntu image-binding fix

Reviewed base: `b5f0e33`, branch `experiment/v2-scg-paired-harness`.

The original adapter supplied historical V2 image IDs directly to execution.
Its 44 null IDs therefore caused skips even if Ubuntu had the exact image tags.
The fix records a separate read-only host inventory and supplies its sealed
`host_image_id` to both arms. Original V2 files, hashes and historical task
metadata remain unchanged.

`bind-images` checks the Docker daemon and all 83 exact frozen tags. It records
historical/actual IDs, availability, differences and available repository digests.
Missing images remain MISSING; Docker errors remain INSPECTION_ERROR and block
preparation. Tags, historical IDs, registry lookups and replacement images are
never used as fallbacks. There are no pull, build or container-launch commands.

The version-2 paired protocol seals the inventory bytes/hash and each task's
binding. Preparation, validation, plan creation and launch recheck the inventory.
Each arm checks its tag and daemon again before execution. Changed tags/IDs,
deleted images, newly present formerly missing images or daemon changes require
a new reviewed inventory/freeze/plan. The native archive/source check remains
mandatory after container startup and before tests; matching image IDs or tags
never establish source fidelity.

Validation: **234 tests passed**, including 66 paired-harness cases and 19 image
inspection/binding cases. Lint and whitespace checks passed. Coverage includes
historical null, matching and different IDs; missing images; inspection errors;
all-83 binding/cohort preservation; both arms receiving the same host ID;
binding/protocol seal tampering; tag and daemon drift; per-arm rechecks; and
source mismatches blocking the executor. Docker inspection and containers are
mocked in these tests. See `unit.xml`, `unit.txt`, `lint.txt` and `validation.json`.

No benchmark tests or experiment launch occurred. No real Ubuntu Docker
inventory was collected in this session. The remaining host validation is to
run the updated [Ubuntu commands](../README.md#exact-ubuntu-commands-offline-review-and-preflight-only),
review all binding differences/availability, and create a new paired freeze.
Actual source fidelity remains unknown until the unchanged source preflight
runs during a separately authorized pilot. There are no implementation blockers.
