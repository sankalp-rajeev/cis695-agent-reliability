# Validated V2 discovery baseline and 83-task preparation

Discovery cleanup and the three authorized integration cases passed validation. The updated baseline is ready for protocol review. **A complete 83-task execution remains blocked by 44 unavailable local image tags.** No full evaluation was launched, no missing environment was replaced, and no historical result was overwritten.

## Discovery across all 83 tasks

| Measure | Result |
|---|---:|
| Final-study candidate patches / verified base archives | 83 / 83 |
| Original selected task/test identities | 58,033 |
| Cleaned selected task/test identities | 57,682 |
| Removed / added | **351 / 0** |
| Tasks with removals | 19 |
| Removed string-only identities | 325 |
| Removed function-local helper/local-class identities | 26 |
| Independently verified removal occurrences | 554 string locations + 26 local definitions |
| Valid outer-definition occurrences retained | 57,471 |
| Parametrized outer-definition occurrences retained | 2,324 |
| Uncertain records conservatively retained | 217 |
| Known named historical regression-detecting tests retained | **6 / 6** |
| Previously observed raw concrete-test rows retaining an identity/family | **689 / 689** |

Counts of identities are task-specific; source occurrences and raw concrete observations have separate denominators. A family remains an unparameterized selectable identity and may expand into multiple runner cases. Retention does not establish fresh execution of a test.

The comparison reproduces the original selector from commit `0c0c87f` and invokes both versions on the same candidate patch and base archive. Candidate export/patch hashes, archive hashes and archive PAX base commits were verified. All 83 tasks have a comparison; zero base archives are unavailable. Saved V2-selection variants are audited separately; saved records outside the 83-task cohort are explicitly excluded rather than counted as unavailable experiment tasks.

The independent verifier does not accept the filter's reasons as its proof. It pairs physical definition candidates with the original scanner's IDs, then uses Python token boundaries and AST ancestor scopes to inspect **every occurrence of every removed identity**. All 351 have an independent source proof. It also checks that every original selected outer definition survives and retains all selected candidates when parsing is uncertain. Evidence and numbered contexts are in [audit/removed_ids.json](audit/removed_ids.json); retained outer definitions and parametrize markers are in [audit/valid_outer_definitions.json](audit/valid_outer_definitions.json).

Known historical detecting identities and the 689 previously observed concrete rows were consulted only **after** the comparison had been written and hashed. They were not inputs to selection, ranking or filter design. Their retention is recorded in [audit/known_witnesses_retained.json](audit/known_witnesses_retained.json) and [audit/observed_raw_tests_retained.json](audit/observed_raw_tests_retained.json). Only the pytest detecting test was freshly rerun here; the missing Django/Sphinx environments prevent fresh confirmation of the other five historical identities.

This is deliberately conservative cleanup, not a new collector. Module/class definitions, duplicate identities with a real or uncertain occurrence, possible dynamic namespace construction, exported local functions, parse failures and parametrized families are retained. The original scanner's other limitations, including its async-definition coverage, are not expanded or silently repaired in this change. Source inspection does not prove that every retained ID is runnable under every framework configuration.

## What changed and what did not

`node_ids()` now filters legacy candidates whose source locations can be excluded as string text or non-exported local definitions. Existing identity order and spellings are preserved; no new ID is introduced. The added helper functions retain the original textual scanner as the ordering/identity boundary.

An AST comparison confirms **24 pre-existing selection definitions unchanged**, excluding the deliberately replaced `node_ids`. Both versions produce identical convention scores, runner discovery, symbols and configuration; cleaned tier memberships are ordered subsequences of their originals. **19 protected verifier/configuration files retain their original bytes**, covering execution, regression classification, decision adapters/policy and the frozen shadow-classifier implementations. Ranking, tier caps, seeds, timeouts, confirmation rules and decision policy are unchanged. No SCG-based filtering or SCG selection artifact is used.

The uncommitted experiment script was finalized to exclude saved SCG/import-selector comparisons, distinguish outside-cohort records from unavailable tasks, verify archive commits and tier invariants, and include shadow-only integration checks. The independent audit, integration replay and guarded evaluation runner are new apparatus, not changes to the verdict algorithm. One test helper was rewritten from a lambda to a named function for lint compliance.

## Unit and integration validation

**The full unit suite passed: 922 passed, 1 skipped.** Relevant lint checks passed. [test_results.json](test_results.json), [unit_final_complete.txt](unit_final_complete.txt) and [lint.txt](lint.txt) preserve the commands/results. The initial broad suite encountered 30 read-only cache-lock errors; rerunning offline with a temporary copy of the already resident Hugging Face cache resolved them without a dataset download or production change. Added runner tests verify approval binding, source/manifest drift detection, unavailable-image accounting, incomplete-PASS rejection and post-collection label access.

The live diagnostic used the exact three image IDs from the previous audited local validation. It compared original discovery A with cleaned discovery B in **A/B then B/A order for every task**: 12 fresh arms, not reused historical outcomes. Each arm used a new network-disabled container, no image pulls, no baseline cache, unchanged 300-second pass limits and unchanged regression confirmation. Selected test files and candidate-changed source files matched the verified base archive in every arm.

| Task | Original A | Cleaned B | Missing raw-selected IDs per tree, A → B | Native regressions |
|---|---|---|---:|---|
| pylint-6528 | 218 selected; INCOMPLETE | 217 selected; **PASS, COMPLETE** | 1 → 0 | 0 → 0 |
| pylint-7277 | 70 selected; PASS, COMPLETE | 70 selected; **PASS, COMPLETE** | 0 → 0 | 0 → 0 |
| pytest-5809 | 7 selected; FAIL, incomplete evidence | 4 selected; **FAIL, COMPLETE** | 3 → 0 | Same `TestPaste.test_create_new_paste` |

Both repetitions agree for every arm. The removed pylint ID is the local `test_environ_pythonpath` context manager; the three removed pytest IDs are definitions inside a generated-test source string. **Executed concrete test IDs and base/patched statuses are identical across all four arms of each task.** Cleanup removed invalid requests rather than removing executed tests or changing their outcomes. No initial-pass timeouts occurred. Complete evidence never produced an unexplained PASS, and **incomplete execution produced zero PASS verdicts**.

The pytest regression remains FAIL despite the classifier suggesting `LIKELY_SUPERSEDED_ASSERTION`; the suggestion remains shadow-only. Pylint predictions abstain (`UNCERTAIN`). Replay through unchanged production adapters and record serialization preserves native INCOMPLETE as neutral NOT_AVAILABLE with absence `incomplete`. With other stages explicitly disabled, FullPolicy and BaselinePolicy project FLAG for the pylint cases and REJECT for pytest; the shadow suggestion does not change these decisions. These are **V2-only projections**, not newly executed full-verifier results.

All **128 raw capture files** were hash-verified. [integration_audit/summary.csv](integration_audit/summary.csv) records every arm's missing IDs, timeouts, errors, regression and policy results. [integration_audit/results.json](integration_audit/results.json) retains the raw-ID/status comparisons and [integration_audit/records/](integration_audit/records/) contains the serialized round-trips. Complete stdout/stderr/runner bytes, batch receipts and commands remain under `comparison_final/`. The sum of measured regression wall time across the 12 arms was about 555 seconds; shadow/setup/cleanup costs are recorded separately in the native captures.

Improved pylint-6528 completeness is not evidence that the patch is correct or that wrong-patch detection improved. No new global precision/recall/F1 claim is made from these three familiar cases.

## Frozen 83-task evaluation for review

The prepared [frozen_83/protocol.json](frozen_83/protocol.json) names the validated code commit, exact source/config hashes and effective SelectionConfig/RegressionConfig. [frozen_83/tasks.json](frozen_83/tasks.json) accounts for all 83 tasks, including expected image tags, available image IDs/digests, patch/archive/source hashes and test-manifest locations. Candidate bytes, selected-ID/tier/convention manifests, allowed issue text and host-package versions are sealed transitively by the protocol hash.

The runner is `scripts/v2_evaluation.py`; [README.md](README.md) documents validation and eventual execution commands. Preparation and `validate` start **zero containers**. Execution requires the exact reviewed protocol SHA-256, checks source/config and host-package drift, and refuses existing output directories. It will perform fresh base/patched passes sequentially using unchanged production classification and confirmation. The existing baseline-unreliable guard may stop a task before a patched pass; that exception is explicitly recorded rather than bypassed. The production 600-second pair setting is nominal metadata; no new hard total-time enforcement or altered confirmation/shadow budget is introduced.

Native PASS/FAIL/INCOMPLETE, completeness states, NOT_AVAILABLE and BASELINE_UNRELIABLE are reported separately from environment/runner errors. The ledger retains all 83 task identities. An absent environment has no invented V2 verdict. Runtime, runner/confirmation/shadow costs, raw coverage, missing/timeout IDs, available cgroup lifetime CPU/peak memory and evidence storage are recorded. Docker resource defaults are unchanged; the captured host has 32 CPUs and 10,424,115,200 bytes available to Docker.

Correctness precision/recall/F1 and historical witness detection are separate **post-collection** analyses. Correctness and witness sidecars must match candidate hashes and cannot be opened until collection is complete. Positive prediction is V2 FAIL and target is a wrong patch. Both binary-only and all-labeled-task recall/F1 are defined; abstentions remain explicit and undefined ratios remain null. These metrics are specified now, not measured without a new run.

## Remaining limits and readiness

1. **39 image tags are locally present; 44 are unavailable.** All 83 source archives/manifests exist. Missing images are listed individually in the frozen task manifest. No substitutes, pulls or builds were used. Restoring environments requires a new reviewed freeze because the current manifest explicitly marks those tasks unavailable.
2. Available image metadata alone is not a source-fidelity check. The three validation images match prior audited IDs and selected/changed source hashes. Their original historical full-image equivalence is still unproven; current image Git HEAD and base source are recorded separately. Other available images must pass the same source preflight when execution is eventually approved.
3. Five known historical detecting tests have selection-retention evidence but no fresh execution here. Preserving them is not a claim that fresh environments will reproduce the historical regression outcomes.
4. Local source cleanup does not solve every retained invalid/uncertain identity, the unchanged parser's family-level classification limits, or the inability of existing tests alone to establish issue correctness. These are not addressed by policy changes in this task.

**Ready:** validated discovery/execution-integrity baseline, exact manifests, guarded runner and protocol review. **Not ready:** complete execution of all 83 tasks while 44 environments are absent. **Not authorized or launched:** the full 83-task run.

## Preservation and Git

Work stayed on the original `fix/pkg-cache-mask` branch. Initial fingerprints are in `initial_state.json`; the final preservation check verifies every pre-existing unrelated dirty/untracked file and historical tracked artifact unchanged. The deleted `.env.example`, edits to `docs/checklist.md` and `scripts/verify_model.py`, existing SCG draft/status files, and `reports/ceiling_check/` are unrelated and excluded from these commits. The experimental SCG worktree/branch is not modified.

Validated source, tests, runner, reports and complete new evidence are committed first. The final freeze then records that exact code revision; its manifest/report-only commit leaves executable hashes unchanged. Push/HEAD/upstream verification is reported with the delivered commit hashes, without claiming the original worktree is globally clean while unrelated pre-existing edits remain.
