# Task-spec registry, version 1

The shared schema is `task_spec_registry/1`. A registry contains only patch-independent preparation data. `cohort` is a nonempty descriptive string, never a runner allowlist; `built_by_commit` is a 40-character lowercase Git SHA. `tasks` is an array with unique `instance_id` values across every registry passed to a run. Unknown task fields, patches, selections, outcomes and correctness metadata are refused.

```json
{"schema":"task_spec_registry/1","cohort":"<name>","built_by_commit":"<40 hex>","tasks":[{
  "instance_id":"owner__repo-number","repo":"owner/repo","version":"<version>","base_commit":"<40 hex>",
  "image":{"tag":"<metadata tag>","id":"sha256:<64 hex>"},
  "archive":{"path":"<absolute>","sha256":"<64 hex>","pax_comment":"<base_commit>"},
  "pre_install":{"wheel_sha256":"<64 hex>","dataset_projection_sha256":"<64 hex>","spec":{},
    "wheel_path":"<optional absolute>","dataset_projection_path":"<optional absolute>"},
  "integrity_preflight":{"status":"VERIFIED","receipt_path":"<absolute>","receipt_sha256":"<64 hex>"},
  "runner":{"name":"pytest|django|sympy|unknown","evidence":"<text>","django_parallel_one":null},
  "origin":"phase4_freeze|prepared"
}]}
```

`pre_install.spec` is exactly `PreInstallSpec.resolve()` from the pinned SWE-bench 4.0.4 wheel and the four-column dataset projection, including commands, source identities and provenance. The validator re-resolves and compares it. `wheel_path` and `dataset_projection_path` are optional additions needed to reconstruct `PreInstallSpec` and `BaseSourceSpec` for other cohorts. If omitted, the wheel defaults to `runs/phase4_fix10_provenance/swebench-4.0.4-py3-none-any.whl` and the projection to `reports/next_phases/phase4_rerun/fix10_provenance/dataset_projection.json` in the runner checkout. New registries should supply explicit absolute paths when their projection differs. All hashes must match local artifacts; no network retrieval occurs.

Archive PAX commit, full archive hash, pinned wheel, dataset projection, resolved pre-install specification, and the preflight receipt's hash/status/base identity are validated. The compressed receipt's stored bytes are hashed before decompression. The preflight authorizes identity only; a fresh VERIFIED pristine receipt is still required before runtime. Image tags are metadata; runtime uses only the immutable image ID with `--pull=never`.

`django_parallel_one` is an explicit boolean for Django and null for other runners. The Phase 4 builder derives it solely from hash-verified argv projection, exactly as `frozen_django_command_choice` does. Registry origin is one of `phase4_freeze` or `prepared`; both use the same validator and produce the same task/source objects for identical input data. The runner never loads new instances from a dataset in lieu of a registry. A manifest ID absent from all registries becomes a task-level `NO_TASK_SPEC` absence.
