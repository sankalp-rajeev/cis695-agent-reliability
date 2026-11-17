# E2E v1.4.1 decisions

- 2026-11-16: Add new modules beside frozen modules; the v1.4.0 and UM manifests prohibit modifying the existing verifier implementation.
- 2026-11-16: Run registry, selection, and sealed V2 checks before live execution; the requested stop rule requires stopping on any A2 difference or halt.
- 2026-11-16: Use a temporary UV cache with the worktree's own environment; the default cache directory is outside the writable roots.
- 2026-11-16: Do not substitute sealed attempt-4 Django commands for the D1 source; D1 explicitly requires the fix13 projection used by frozen_django_command_choice.
- 2026-11-16: Stop implementation at the input-access preflight; 31 required Django sources are outside the allowlist and the required frozen-artifact hash for golden.csv has an expressly forbidden path name.
- 2026-11-16: Report blocked checks as incomplete and create no frozen tag; neither an input-access audit nor an unchanged existing unit suite demonstrates A1–A7 acceptance.
