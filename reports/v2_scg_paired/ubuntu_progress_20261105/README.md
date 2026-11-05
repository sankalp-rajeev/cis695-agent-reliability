# Ubuntu paired experiment progress — 2026-11-05

The updated-V2 versus corrected-SCG integration, immutable 83-task static
preparation, authorized three-task pilot and final diagnostic review are complete.
The latest recommendation is **GO for a separately authorized comparison of the
unchanged frozen pipelines under their shared native execution/verdict policy**.
This publication does not authorize execution. No full-cohort experiment or new
execution plan was created during publication.

## Execution identity

The execution worktree remains detached at
`b030e508d849926b9a2260c70e1091adebfee993`:
`/home/sankalp/projects/cis695-v2-scg-paired-review-b030e50`.
Corrected SCG is pinned to `e1a3ed1c74fd304493c3fe3811de755af77e306c`.

The original harness and unit tests are already committed in `b5f0e33` and
`b030e50`; this progress commit only publishes documentation, evidence summaries
and archived diagnostic-script snapshots. It changes no selector, runner,
parameter-ID parser, verdict, patch, image binding, frozen input or execution
policy. The publication worktree is separate from execution:
`/home/sankalp/projects/cis695-v2-scg-ubuntu-publication`.

| Artifact | SHA-256 |
|---|---|
| Ubuntu frozen protocol | `2eaf8341274099cf4210674e6418a4b1e44ea2d0babb09a1c2243f77258c5153` |
| Completed pilot results | `1c38559c76a0f62f37bd7f301c988ceb02c6f2ab186b0680670e750cba03a8da` |
| Final diagnostic evidence manifest | `7b8258f89a1302040601eb446f46ff566660bbe0cff77cd976f3c965cc613b84` |
| Existing three-task pilot plan | `57c84e2ceb615ebe7df43a5a26cf140b300b5a838f706ce6f7f7a5d2b9a77f1d` |

These identify existing local artifacts, not a new freeze or new plan.

## Published milestones

All linked milestone reports and diagnostic scripts are byte-identical copies
of their local originals. Their historical GO/NO-GO recommendations record the
state at that milestone; the final review supersedes earlier readiness findings.
References to bulk evidence in those reports resolve in the original local
evidence tree, which is intentionally not reproduced in Git.

1. [Ubuntu static integration](../../v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/GO_NO_GO.md):
   83/83 images, 83/83 archives and frozen inputs verified; V2 lists exactly
   reproduced. Historical image differences were 39 non-null ID mismatches and
   44 previously null IDs, with zero missing Ubuntu images or inspection errors.
   The documented unit suite passed 234 tests and the documented Ruff checks
   passed. These are earlier integration checks, not checks rerun for publication.
2. [Scientific audit](../../v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/scientific_audit_20261105T180428_197888Z/SCIENTIFIC_AUDIT_AND_PILOT_REVIEW.md):
   all 83 SCG graph/selection replays and independent membership/order checks
   matched. SCG retains 13 nonempty, 68 empty and two unavailable selections;
   graphs are 56 complete and 27 partial. Resolved-only strategy B, depth 3, ALL
   is unchanged. Zero and unavailable selections are preserved.
3. [Authorized pilot](../../v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/pilot_20261105T183041_929325Z/PILOT_GO_NO_GO.md):
   3/3 tasks and 6/6 arm records completed, with 40 raw capture hashes verified.
   Four native PASS records, Matplotlib V2 native NOT_AVAILABLE and Matplotlib
   SCG ZERO_SELECTION/NOT_AVAILABLE remain unchanged. No crash, timeout,
   source mismatch or evidence-integrity failure was found.
4. [Final post-pilot review](../../v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/post_pilot_review_20261105T185712_250018Z/FINAL_POST_PILOT_REVIEW.md):
   import-only diagnostics for the three exact pilot images found 15 sampled
   project modules resolving to archive-matching source bytes, with no sampled
   target-package site-packages shadowing. All original evidence was preserved.

## Interpretation and remaining limitations

Matplotlib's two bare family IDs expanded to six concrete cases per phase:
four passes and two skips. The unchanged exact-membership parser admitted none
of the suffixed IDs. Both requested IDs stayed NOT_RUN, giving native
NOT_AVAILABLE. Independent raw-family accounting established COMPLETE evidence;
it did not promote the native verdict.

Static declaration exposure was found in 36 tasks, including Matplotlib and
Xarray from the pilot: 35 tasks besides Matplotlib, or 34 beyond both pilot tasks.
Eleven additional nonempty pytest tasks remain uncertain. The structural exposure
envelope is 47 tasks. These are potential exposure counts, not predicted native
abstentions. Both arms share the parser, but differing selected family mixes can
produce asymmetric admission losses. Report raw-versus-native coverage, all
abstentions and incomplete states alongside results.

Archive/source-file equivalence, current diagnostic import resolution and proof
of imports during earlier test execution remain distinct. Separate probes cannot
retroactively establish earlier pytest module origins. Earlier provenance was
complete for Django, partial for Xarray and insufficient for Matplotlib. Full
transitive/patched-state provenance, compiled-extension build provenance and
runtime import evidence for the remaining 80 tasks remain limited or unknown.
The mandatory shared source checks still apply to future execution.

A partial static graph or a selected-list PASS does not establish complete
reachability or patch correctness. The comparison measures the frozen pipelines
including native parser limitations; it does not isolate selector quality from
execution admission. A parser repair would require a separately reviewed
experimental protocol. No correctness labels or historical witnesses were used
to alter selection or pilot execution.

## Local evidence and reproducibility

The original evidence root is:

`/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z`

- [local_artifacts.json](local_artifacts.json) records absolute paths, sizes and
  SHA-256 references for the local protocol, seals, native results and detailed
  per-ID evidence. Frozen payloads, full raw captures, graph replays and container
  file snapshots intentionally remain local.
- [archive_references.json](archive_references.json) records all 83 archive paths,
  frozen hashes and base commits. Archives remain in
  `/home/sankalp/cg_repos/task_archives`; this catalog reads frozen metadata and
  does not represent a fresh archive validation.
- [published_files.json](published_files.json) records the original locations and
  exact hashes of the copied reports, scripts and compact summaries.
- Docker layers, source archives, virtual environments, credentials, `.env`,
  `runs/`, `logs/`, immutable freezes and the patch export are not staged.

Diagnostic Python files are archived as-used provenance, not installed tools or
changes to the harness. Some have top-level side effects, fixed local paths and
exclusive output creation; do not run them against sealed directories. The pilot
script's initial derived import-path extraction had a regex ambiguity; the
published `import_evidence_extraction_correction.json` documents its correction.
The final post-pilot review and corrected source/import evidence are authoritative;
raw captures and native verdicts were never changed.

Publication checks are limited to Python syntax parsing without imports or
execution, JSON/CSV structure, byte/hash identity of copies, staged-path and
credential-pattern review, and Git whitespace/diff review. Publication does not
rerun the scientific audit, validate or recreate a plan, start Docker containers
or run benchmark tests. Future full execution requires separate authorization and
an explicit reviewed plan hash; the existing pilot plan has only three tasks.
