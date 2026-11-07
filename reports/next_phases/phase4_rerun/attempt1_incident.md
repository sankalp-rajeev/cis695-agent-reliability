# Phase 4 attempt 1: frozen-source mismatch incident

**Finding:** `matplotlib__matplotlib-14623` halted at the initial **base-image source check**, before candidate-patch application or any native collection, execution, or confirmation for this task. The mismatch is a deterministic **Git `export-subst` archive transformation**, not caused by a collection-time file rewrite. The image contains the original Git blob; the frozen tar contains two expanded Versioneer placeholders. A fresh `git archive` of the declared base commit reproduces the frozen entry byte for byte.

The controlled run remains stopped. No executor, launcher, selection, image, plan, or tag was patched, and no controlled task was restarted or resumed. The 35 completed tasks' result/pass/raw outcome contents and correctness labels were not opened or summarized. Their source audit used result-file **existence**, frozen archive source, startup source-check metadata, and separate collection-only diagnostics.

## 1. Tree and stage at failure

- Frozen executor/plan: `phase4-plan-frozen`, commit `d31f8928d5e2f2a6641183005685b0486c07d41e`.
- Incident image: `sha256:30368e1c136e8eded62e7229d134a132cabb4bb47b5a2c56e1d1e0dc5e9752b3`.
- Failure recorded at `2026-11-07T18:41:56.761429+00:00`.
- **Tree:** newly started, unpatched base image. Supplying patch text to `TaskContainer` does not apply it; application happens when the executor later requests the patched tree.
- **Stage:** local launcher's `Controller.task`, startup hash comparison, line 380. The container had started, its image/resources had been inspected, an expected-hash JSON had been uploaded to `/tmp`, and a read-only Python hash command had returned. The assertion fired while comparing those hashes.
- The check precedes construction of `ContainerTestExecutor` and the first `Recorder.run` call. The interrupted receipt has `active_call: null`; this task has no `calls.json`, source-check success receipt, or native pass capture.
- The frozen V2 selection for this task is empty. Attempt 1 still started its container for its all-83/both-trees scope, unlike the original paired harness's empty-selection shortcut. It failed before reaching either tree's executor call.

Receipts: [original incident error](attempt1_incident_receipts/incident_error.json), [container identity/argv](attempt1_incident_receipts/incident_container.json), [interruption metadata](attempt1_incident_receipts/incident_interruption.json), and [hashed launcher excerpt with line numbers](attempt1_incident_receipts/frozen_launcher_source_check_excerpt.txt). The launcher's recorded SHA-256 is verified against the unchanged run protocol in [diagnostic provenance](attempt1_incident_receipts/diagnostic_provenance.json).

The launcher recorded an integrity halt but returned shell exit code 0. That is a separate status-reporting defect, not evidence of successful completion, and was not changed here.

## 2. Archive and observed file: hashes, full contents, and diff

Frozen archive: `/home/sankalp/cg_repos/task_archives/matplotlib__matplotlib-14623.tar`.

Archive **tar SHA-256**:

```text
32d9e0ee89a2638b07416ab4a7cefe86bc9c285bba77849ab6e292bef507e87c
```

Declared base commit: `d65c9ca20ddf81ef91199e6d819f9d3506ef477c`.

| `lib/matplotlib/_version.py` representation | Bytes | SHA-256 |
|---|---:|---|
| Frozen tar entry | 15,799 | `a14e1304d76c35270dfc9f0051b507a81929417c7b79d9f503a6eee3d0e3af3a` |
| Exact pinned image, before container start | 15,781 | `3c7d6f3bcdfd71943afa63cd95a1cb24c8d35d11b7babcbffb36f69c73176269` |
| Git blob at the declared base commit | 15,781 | `3c7d6f3bcdfd71943afa63cd95a1cb24c8d35d11b7babcbffb36f69c73176269` |
| Fresh `git archive` entry for that base commit | 15,799 | `a14e1304d76c35270dfc9f0051b507a81929417c7b79d9f503a6eee3d0e3af3a` |

Full, unabridged file contents: [frozen entry](attempt1_incident_receipts/archive_version.txt), [pristine image entry](attempt1_incident_receipts/image_version.txt), [base Git blob](attempt1_incident_receipts/git_base_blob.txt), and [reproduced archive entry](attempt1_incident_receipts/reproduced_git_archive_version.txt). These are byte-preserving copies, not imported modules.

The entire diff is two string assignments:

```diff
--- frozen archive/lib/matplotlib/_version.py
+++ pristine pinned image/lib/matplotlib/_version.py
@@ -20,8 +20,8 @@
     # setup.py/versioneer.py will grep for the variable names, so they must
     # each be defined on a line of their own. _version.py will just call
     # get_keywords().
-    git_refnames = ""
-    git_full = "d65c9ca20ddf81ef91199e6d819f9d3506ef477c"
+    git_refnames = "$Format:%d$"
+    git_full = "$Format:%H$"
     keywords = {"refnames": git_refnames, "full": git_full}
     return keywords
```

**Evidence limitation:** the failed launcher did not persist the original observed hash dictionary or original container file bytes before removing that container. The assertion retained the mismatching path only. The observed bytes above are reconstructed from the **same immutable image ID**, then checked through the same read-only startup sequence; they are not represented as a saved copy from the removed incident container. That sequence reproduces exactly one mismatch, this file. [Reproduction receipt](attempt1_incident_receipts/throwaway_reproduction.json), [raw diff](attempt1_incident_receipts/archive_vs_image.diff), and [frozen inputs](attempt1_incident_receipts/frozen_inputs.json) preserve the distinction.

## 3. Candidate patch

**It does not touch `_version.py`.** Its only changed path is:

```text
lib/matplotlib/axes/_base.py
```

The approved candidate patch SHA-256 is `90ca07500c28ff5020e5ee77bb1aa6ea61fcf6810bdfef3f43f81d9af384e262`.

Patch headers and the checked hash are in [frozen_inputs.json](attempt1_incident_receipts/frozen_inputs.json). No patch was applied in any diagnostic container.

## 4. File at container start, before executor steps

**It already differs from the archive.** The file was copied out with `docker cp` from a newly **created but not started** container, before any process ran. Its hash was the image/Git-blob hash above. The container's entrypoint is null, and it was configured with `sleep infinity`, network none, and CPU shares 2048.

The same hash remained after each stage:

1. Container created, not started.
2. Container started, before any `docker exec`.
3. Login shell only (`true`).
4. Python startup only (`python -c pass`).
5. The identical read-only startup hash command.
6. Immediately before native collection.
7. Immediately after native collection.

The file was clean in `git status` both before and after collection. The image's synthetic HEAD is recorded separately; the comparison against the declared base **blob**, not an assumption about HEAD equality, proves the source identity. See the staged hashes in [throwaway_reproduction.json](attempt1_incident_receipts/throwaway_reproduction.json).

## 5. What the original paired run checked

**This file was not checked for this task in the original paired V2 run.** Two independent facts establish that:

- Its original frozen source-check manifest contains only `lib/matplotlib/axes/_base.py`; `_version.py` is absent. That manifest covered selected/candidate-related Python source, not every archived Python file.
- Its V2 selection was empty, so the original paired `execute_arm` took the `ZERO_SELECTION` branch, started no task container, and recorded no native calls. It never reached the image source preflight at all.

For a nonempty selection, the original `v2_evaluation.execute_one` placed `preflight(container, task)` after container start and before `ContainerTestExecutor`/`run_regression`, therefore before patch application and native collection/execution. The exact historical source at harness revision `b030e508d849926b9a2260c70e1091adebfee993` was retrieved and verified against the original protocol's source hashes. Only this incident task's original execution metadata was examined, not any completed task's outcomes. [Original guard receipt and source excerpts](attempt1_incident_receipts/original_guard.json).

Thus the earlier paired run cannot establish byte equality for `_version.py`; attempt 1 introduced a broader startup comparison against exported archive bytes.

## 6. Which step wrote the differing bytes?

**The difference is produced when Git serializes the archive, not when pytest imports Matplotlib.** The archived `.gitattributes` contains:

```gitattributes
lib/matplotlib/_version.py export-subst
```

The working-tree/Git-blob Versioneer module retains `$Format:%d$` and `$Format:%H$`. `git archive` expands those placeholders into the reference decoration and commit hash in its tar entry; it does not rewrite the working-tree file. Running the following against the exact pinned image produced an entry identical to the frozen archive:

```bash
git archive --format=tar d65c9ca20ddf81ef91199e6d819f9d3506ef477c lib/matplotlib/_version.py
```

The version file's Git blob and image bytes match exactly. There is no need to posit an image-source change or a setuptools_scm/Versioneer runtime writer to explain the incident.

A separate native-collection experiment used the tagged collector and plugin, with `lib/matplotlib/tests/test_afm.py` chosen solely as a diagnostic module. The incident task itself has no selected collection module; this probe was **not** a resumed controlled selection or a new family in the study. The command was:

```text
/opt/miniconda3/envs/testbed/bin/python -m pytest --collect-only -q \
  -p no:cacheprovider -p verifier_collect_plugin -- lib/matplotlib/tests/test_afm.py
```

Collection completed with return code 0, and no tests were executed. `_version.py` remained unchanged; inventories of **860 tracked Python files** before and after collection had **zero differences**. Full commands and input-code hashes are preserved in [the reproduction receipt](attempt1_incident_receipts/throwaway_reproduction.json); [native collection receipt](attempt1_incident_receipts/native_collection.json) and [source-only reproducer transcript](attempt1_incident_receipts/matplotlib_reproducer.py.txt) permit audit. [The byte-level substitution proof](attempt1_incident_receipts/export_subst_byte_proof.json) confirms there are no other byte differences. Version calculations can occur in memory without rewriting this file; they are distinct from source-byte mutation.

## 7. Version-source coverage among the 35 completed tasks

This audit covers **source provenance only**, not their outcomes. Completion membership came from result-file existence. The 35 comprise four Astropy tasks and 31 Django tasks. No member has an archived `.gitattributes` `export-subst` rule. Their recorded initial full-source comparisons matched the archived files. Therefore this particular Matplotlib archive/working-tree discrepancy was not silently accepted at their startup checks.

**There is nevertheless a concrete unchecked-generated-source gap in all four Astropy images:**

| Task | Build-generated source present in image | In frozen archive/startup guard? | Included by native source snapshot? | Changed in fresh collection-only probe? |
|---|---|---|---|---|
| astropy__astropy-13977 | `astropy/_version.py` | No | No, ignored | No |
| astropy__astropy-14365 | `astropy/_version.py` | No | No, ignored | No |
| astropy__astropy-14508 | `astropy/_version.py` | No | No, ignored | No |
| astropy__astropy-7606 | `astropy/version.py` | No | No, ignored | No |

For the three newer images, archived `pyproject.toml` declares `[tool.setuptools_scm] write_to = "astropy/_version.py"`. The image file identifies itself as generated by `vcs-versioning`. Tracked `astropy/version.py` is a dispatcher, and `_dev/scm_version.py` attempts `setuptools_scm.get_version` without a file-writing argument. The optional setuptools_scm runtime package is absent in these diagnostic images, so the dispatcher can use the existing generated fallback. The older setup.py explicitly calls `astropy_helpers.version_helpers.generate_version_py`; its image `version.py` header identifies setup.py generation. Its `update_git_devstr` computes an in-memory string; it does not rewrite that module.

These ignored files are absent from archive-based expected hashes. The native snapshot uses `git ls-files --cached --others --exclude-standard`, which excludes these untracked ignored files as well. The exact ignore rules, image-start contents/hashes, source-snapshot path lists, and collection receipts are in [generated_version_coverage.csv](attempt1_incident_receipts/generated_version_coverage.csv) and [the four Astropy probes](attempt1_incident_receipts/astropy_generated_source_probes.json). The probes restored only the same archived configuration files recorded by the original startup metadata; no Python source was edited. All four collection commands completed with return code 0 and zero test execution, and the generated files' before/after hashes matched.

The 31 Django archives have a handwritten `django/utils/version.py`, spanning six source variants, all included in the startup guard. Those utilities contain no detected source-write calls; this is not a claim that Django has no generated artifacts of any other kind.

**Answer to the risk question:** yes, the four Astropy generated modules could have been rewritten without this source guard detecting it. But no such rewrite was observed in these collection-only probes, and the actual Matplotlib mechanism is archive export, not runtime mutation. More generally, container repository source is compared with the archive only at startup; there is no post-collection, post-execution, or post-confirmation comparison. The per-pass `Controller.check` guards host executor/plan files, not the container source tree; native AST snapshots likewise do not perform archive-equality checks. The controlled run retained no post-execution copies/hashes of these generated modules. Their exact state after the already-completed task executions therefore **cannot be certified from the retained source receipts**. No conclusion about those tasks' outcomes follows from this audit.

[Per-task source audit](attempt1_incident_receipts/completed_source_audit.json), [source-only CSV](attempt1_incident_receipts/completed_version_sources.csv), and [native snapshot program](attempt1_incident_receipts/native_source_snapshot_program.txt) document this scope and limitation. The audit identifies version-related sources and declared generated targets; it is not an exhaustive inventory of every possible generated artifact.

## Proposed fix — not implemented

1. **Use a representation-aware, proven source identity check.** For an explicitly `export-subst`-marked file, require the pristine image bytes to equal the declared base Git blob, and independently require `git archive` of that base to reproduce the frozen entry exactly. Record both raw hashes and the transformation. For other files retain strict byte equality. Never blanket-ignore `_version.py` or normalize arbitrary differences. If a candidate actually touches such a path, require an explicit patched-source expectation rather than applying this base-only exception.
2. **Preserve runtime bytes.** Do not copy the archive-expanded Versioneer file into the image: that can change its version-resolution branch and runtime behavior. The proven export transformation belongs in source-provenance accounting, not a source rewrite.
3. **Pin declared build-generated Python inputs separately.** Include the Astropy ignored version modules in a per-image generated-source manifest, without claiming they were in the archive. Record/check source hashes around collection and execution/confirmation, distinguishing approved candidate changes from unexpected writes. This would expose later mutation rather than assuming startup equality persists.
4. **Save mismatch evidence before aborting.** Persist expected and observed hashes, file bytes/diff, tree, and exact executor stage. Return a nonzero launcher status on an integrity halt. These would improve diagnosis; neither was changed here.

No fix, threshold, B1/B2 baseline, policy, selection family, source guard, frozen tag, or controlled run was altered. This report is not authorization for another run.

## Diagnostic boundaries and receipt integrity

Six throwaway containers were used: one successful Matplotlib collection probe, four successful Astropy collection probes, and one Astropy precollection package-introspection probe that stopped on the absent optional `setuptools_scm` package. That preliminary probe executed no collection or test bodies, installed nothing, and was removed; its [receipt](attempt1_incident_receipts/astropy_generated/astropy__astropy-13977/precollection_package_probe.json) and [error transcript](attempt1_incident_receipts/astropy_generated/astropy__astropy-13977/precollection_probe_error.txt) are retained. The subsequent probes handled absence without modifying the environment. Every throwaway was removed. The actual controlled attempt remains halted.

The only new repository files are this incident report and its receipts. [diagnostic_provenance.json](attempt1_incident_receipts/diagnostic_provenance.json) verifies every original executor/plan source hash and the unchanged original launcher/protocol; [receipt_manifest.json](attempt1_incident_receipts/receipt_manifest.json) seals the evidence package. No unit suite or task test bodies were executed for this report.
