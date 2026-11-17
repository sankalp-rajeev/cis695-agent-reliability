# Decisions

- Use Arrow IPC included_fields for the four public columns before row decoding, because the remaining dataset columns are prohibited inputs.
- Use only the hash-verified runs/phase4_fix10_provenance/swebench-4.0.4-py3-none-any.whl through pre_install.load_specs, because the installed 5.0.2 package is not the frozen authority.
- Copy only Verified dataset/hub cache entries to runs/hf_home and set all three HF variables, because the shared cache is read-only; allocated size is 15 MB.
- Reuse the exact frozen four-column projection for the 83 to retain byte-identical resolve() provenance; project new tasks separately.
- Add optional dataset_projection_row, preflight_identity and runner_provenance fields, because the shared required fields cannot express the public row, explicit identity and provenance of command defaults.
- Preserve frozen runner metadata for the 83 after calling discover_runner, because Phase 4 keeps its historical SymPy pytest metadata while the executor selects its native SymPy adapter by repository; record discovered/effective names separately.
- Build archives with git archive --format=tar --prefix=testbed/ at the base commit inside the pinned offline image, because this reproduces order, commit mtimes and pax headers without acquiring repositories.
- Publish registries and archives with atomic no-replace links, because existing artifacts must never be overwritten.
- New Django choices use prepared_default=false, because Fix 17's rule used observed run commands and every frozen Django choice is false.
- Do not push, because the user's current instruction supersedes the pasted push request.
