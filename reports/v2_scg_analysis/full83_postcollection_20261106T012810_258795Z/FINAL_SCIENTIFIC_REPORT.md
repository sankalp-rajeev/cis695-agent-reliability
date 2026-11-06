# Updated V2 versus corrected SCG: completed paired evaluation

**Conclusion:** This corrected, resolved-only, depth-3, ALL-budget SCG configuration selects far fewer tests and uses substantially less total measured time, but **does not demonstrate preservation of regression detection**. It omits every test responsible for V2's seven freshly confirmed base-pass/patched-fail transitions across six tasks, including the one incorrect patch V2 flags. V2 is also a weak patch-correctness discriminator here: one incorrect patch flagged, five correct-labelled patches flagged, and extensive incomplete evidence. Neither result supports a broad claim about all static call graphs or proves patch correctness from PASS.

This report separates **observations**, **supported explanations** and **unknowns**. Native signals, abstentions and incomplete states are unchanged. No benchmark, selector, graph build, Docker experiment or previous scientific audit was rerun during this evaluation.

## 1. Integrity and reproducibility

The collector completed normally on **2026-11-05, 18:24:55 America/Phoenix**, after 7,906.84 seconds including command startup. All **83 unique paired records and 166 arm records** reconcile with `results.json`, the approved schedule and individual native results. Alternating arm order, candidate hashes, images, archives, runners and exact frozen selections match. The unlabeled summary ran first and exactly reproduced the saved metrics; the unchanged harness then ran its label/witness summary.

| Identity | SHA-256 / revision |
|---|---|
| Execution worktree commit | `b030e508d849926b9a2260c70e1091adebfee993` |
| Corrected SCG commit | `e1a3ed1c74fd304493c3fe3811de755af77e306c` |
| Original Ubuntu protocol | `2eaf8341274099cf4210674e6418a4b1e44ea2d0babb09a1c2243f77258c5153` |
| Approved full plan | `12ccff62b99c493dba1eab49ccc53de5ad6da7638ef8529b881c4a472d8f2160` |
| Completed results | `d290159d5ab466c5089dafbafc47332bb122b4f04584f991ca23fec0abcee941` |
| Pinned correctness-label source | `89192cb27935c33b62204dbbc5ac9090e8577407e367ec347542ca7c9155cb66` |

All **765 sealed frozen artifacts**, **780 raw capture files** from **195 recorded runner calls**, and **91 recorded runtime source checks** verify. Those source checks cover 1,781 task-arm/file entries. There are zero recorded top-level EXECUTION_ERROR or ENVIRONMENT_MISMATCH arm records. Matching file hashes establish integrity of retained bytes; they do not make a timed-out/incomplete capture complete.

The two missing SCG verdicts are expected frozen abstentions: `django__django-13569` introduces a method absent at base, while `django__django-16082` changes module-level data without a mapped named-definition seed. Both have null selections, no resolved seeds, `UNAVAILABLE_NO_RESOLVED_SEEDS`, zero calls and zero execution time. The latter graph is partial, but the recorded no-seed condition is distinct from its syntax diagnostic. Neither is a lost arm record or execution crash.

Labels are the committed final-study oracle projection, restricted to the exact 83 candidate hashes: **69 resolved/right and 14 unresolved/wrong**. The working CSV differs from pinned Git only by CRLF. Four frozen source-run names are generic `rerun` aliases; final-study provenance and exact patch hashes reconcile them to the labelled reruns, without substituting the alternate patches mentioned in the export manifest. Labels were attached only after completion; collection manifests record `labels_read: false`. These are the study's correctness labels, not a new independent semantic proof of correctness.

See [integrity verification](integrity_verification.json), [label provenance](sidecar_provenance.json), [candidate bindings](label_candidate_bindings.json), and the exact [unlabeled](unlabeled_summary.command.json) and [labelled](labeled_summary.command.json) commands. Full protected-file snapshots and analysis-code hashes are retained separately.

## 2. Overall results and paired comparisons

| Final native outcome | V2 | SCG |
|---|---:|---:|
| PASS | 25 | 8 |
| FAIL | 6 | 0 |
| NOT_AVAILABLE | 13 | 71 |
| INCOMPLETE | 39 | 2 |
| No verdict: unavailable selection | 0 | 2 |
| Binary coverage: PASS or FAIL | 31/83, 37.35% | 8/83, 9.64% |
| Abstention: all other dispositions | 52/83, 62.65% | 75/83, 90.36% |

Only **four tasks have binary outcomes in both arms**, all PASS/PASS: Django-15103, Xarray-4629, Pylint-7277 and scikit-learn-14141. Pylint-7277 is labelled wrong. Thus the common binary subset provides no positive-regression comparison and cannot establish noninferiority. There are 65 differing disposition pairs, mostly involving abstention rather than competing completed classifications. At least one arm is binary on 35 tasks; neither is binary on 48.

| V2 / SCG disposition | Tasks |
|---|---:|
| PASS / PASS | 4 |
| PASS / NOT_AVAILABLE | 20 |
| PASS / INCOMPLETE | 1 |
| FAIL / NOT_AVAILABLE | 6 |
| INCOMPLETE / PASS | 4 |
| INCOMPLETE / INCOMPLETE | 1 |
| INCOMPLETE / NOT_AVAILABLE | 32 |
| INCOMPLETE / no verdict | 2 |
| NOT_AVAILABLE / NOT_AVAILABLE | 13 |

All 13 nonempty SCG lists executed: eight PASS, three NOT_AVAILABLE, two INCOMPLETE. Eight lists have complete graphs and five partial graphs. Four SCG PASS records occur in each graph stratum; both SCG INCOMPLETE records have complete graphs. Static graph completeness therefore does not establish runtime completeness.

## 3. Detection, false alarms and what a regression means

| Correctness-label analysis | V2 | SCG |
|---|---:|---:|
| Incorrect patches flagged FAIL | 1/14, 7.14% | 0/14 |
| Incorrect patches receiving PASS | 5 | 2 |
| Incorrect patches with abstention | 8 | 12 |
| Correct-labelled patches flagged FAIL | 5/69, 7.25% | 0/69 |
| Correct-labelled patches receiving PASS | 20 | 6 |
| Correct-labelled patches with abstention | 44 | 63 |
| Precision of FAIL against wrong-patch label | 1/6, 16.67% | Undefined: no FAIL |
| Binary-only recall, different covered subsets | 1/6, 16.67% | 0/2 |

The all-labelled recall denominator counts an abstaining wrong patch as **not detected**, without converting its verdict to PASS. SCG's zero false alarms accompany only six completed binary outcomes on the 69 correct-labelled patches; they are not evidence of universally better specificity. Existing protocol F1 values are preserved in [labelled summary](labeled_summary.json), including all-labelled F1 0.10 versus 0.00 and binary-only F1 0.167 versus 0.00; the different coverage denominators must accompany them.

**Observed transition evidence:** all seven V2 regression IDs passed on base, failed on patched, failed again in production patched confirmation and passed in an additional base observation. Three FAIL tasks also contain other incomplete evidence; the native FAIL precedence remains unchanged. The sole wrong-labelled detection is **Matplotlib-25479**, `test_register_cmap`, with COMPLETE evidence. SCG selects zero tests on all six V2 FAIL tasks, so the observed detection difference on these tests is a selection omission, not a SCG parameter-parser failure.

**Historical 0/6 check:** V2 selects and freshly confirms all six named historical witnesses across Django-12209/14140/14631, pytest-5809 and Sphinx-10435. SCG selects 0/6, observes none and confirms none. All five patches are labelled correct. The six witness transitions plus Matplotlib's additional transition explain the seven regression IDs across six FAIL tasks; do not count the six historical witnesses as six incorrect-patch detections.

**Interpretation:** the five correct-labelled FAIL tasks are false alarms for the wrong-patch classification target, while simultaneously containing reproducible changes against pre-existing tests. Their assertions concern query count, Q serialization, datetime precision, pastebin lexer and LaTeX formatting. This supports a patch-associated behavioral difference under the bound environments. It does not alone establish that each old expectation remains the intended specification or that the correct-labelled patch is defective. The auxiliary shadow classifier could not adjudicate: its Landlock ABI >=4 isolation requirement was unavailable, leaving **all seven predictions UNCERTAIN**. It was not bypassed and native signals were not suppressed. See [per-test confirmation evidence](regression_evidence.json), [failure excerpts](failure_diagnostic_excerpts.json), and [witness observations](historical_witness_execution.json).

## 4. Selection, execution coverage and computational cost

V2 has 83 available lists, including five empty, totalling **57,682 task-local selected IDs**. SCG has 81 available lists, including 68 empty, totalling **131 IDs**; two lists remain null. On the same 81 available tasks, V2 selects **57,159** versus SCG's **131**, a 99.77% reduction. Of SCG's 131 task-local IDs, 120 overlap V2 and 11 do not. These counts describe functions/families, not distinct concrete parameter invocations or unrelated independent tests across repository snapshots.

| Initial-pass coverage | V2 base / patched | SCG base / patched |
|---|---:|---:|
| Requested selected-ID slots | 57,682 / 57,682 | 131 / 131 |
| Adapter-recorded raw outcome IDs | 68,281 / 68,286 | 800 / 800 |
| Raw outcome IDs with a unique selected mapping | 68,065 / 68,068 | 800 / 800 |
| Selected families represented by raw mappings | 49,608 / 49,608 | 129 / 129 |
| Admitted selected statuses, excluding NOT_RUN/TIMEOUT | 37,767 / 37,766 | 103 / 103 |

Raw and admitted counts measure different units. V2 has 216/218 unaccounted or ambiguous raw entries, including malformed Django summary-derived IDs; raw totals cannot be advertised as an unqualified exact count of actual tests. Skips/expected failures and ERROR states also differ from passed tests. The unchanged adapter represents XFAIL as skipped, and the native counted-outcome definition includes ERROR. Aggregate native counted outcomes are 37,766 versus 103. V2 adds six production confirmation calls and seven base shadow observations; SCG adds none. Full per-phase statuses are in [analysis metrics](analysis_metrics.json), rather than silently treating unadmitted raw cases as native PASS.

| Measured cost, seconds | V2 | SCG |
|---|---:|---:|
| Selection worker wall total | 54.41 | 1,360.44 |
| Graph construction, included above | — | 924.37 |
| Archive/input extraction, included above | — | 41.35 |
| Selection/mapping/ranking, included above | 33.64 | 343.45 |
| Execution arm wall total | 7,750.68 | 138.25 |
| Selection worker + execution wall | 7,805.09 | 1,498.69 |
| Selection worker CPU | 48.68 | 1,353.53 |
| Recorded container lifetime CPU | 14,858.54, 78 arms | 264.52, 13 arms |

SCG's combined measured arm cost is about **80.8% lower**, but most SCG arms execute nothing and its binary coverage is much lower. This is not a saving at matched detection quality. Whole collection wall time is 7,905.03 seconds; the command wrapper measured 7,906.84. Original static preparation command wall time was 1,433.36 seconds, giving approximately **9,340.19 seconds (2 h 35 m 40 s)** for preparation plus collection commands, excluding integration tests, audits and pilot. Per-arm cost sums use worker totals and differ from whole-command wall accounting; do not add graph construction twice. Container CPU is lifetime CPU, not wall time or whole-host energy. Resource snapshots report execution peaks of approximately 2.47 GiB for V2 and 0.27 GiB for SCG; SCG static preparation had a separate approximately 2.39 GiB worker peak.

These are descriptive measurements from one host/run, without independent timing repetitions. Counterbalanced arm order and fresh containers do not establish a general cross-machine speedup distribution.

## 5. Why evidence is incomplete or unavailable

All **39 V2 INCOMPLETE** records preserve original PASS -> final INCOMPLETE. The following task counts overlap and are supported by retained diagnostics, not exclusive causal allocations:

| Co-occurring evidence condition among those 39 | Tasks |
|---|---:|
| Selected NOT_RUN entries | 38 |
| Selected IDs without mapped raw evidence | 32 |
| Runner errors / incomplete-capture flags | 28 |
| Raw ID mapping gaps or ambiguity | 20 |
| Directly observed bracket-family admission gaps | 16 |
| Explicit pytest “not found” diagnostics | 14 |
| Raw ERROR outcomes | 9 |
| Pass timeout | 1 |

There are two timeout tasks overall, **Astropy-13977** and **scikit-learn-14629**, each timing out on base and patched. Astropy's native result is NOT_AVAILABLE rather than INCOMPLETE, so it is outside the 39 denominator. Source existence and file equivalence do not guarantee runtime collectability of every requested ID.

The 13 V2 NOT_AVAILABLE records partition into five empty lists and eight nonempty requests: Astropy-13977 times out; **all five SymPy images report “No module named pytest”**; Astropy-14365 loses native admission to ANSI-coloured outcome text; Matplotlib-25287 loses admission to parameter-family IDs. The latter two have COMPLETE raw accounting. Five missing-pytest environments are actual recorded runtime dependency failures, despite healthy host dependencies and available image tags.

Across the entire cohort, bracketed concrete raw IDs map to selected NOT_RUN families on **34 V2 tasks and four SCG tasks**. This establishes an admission limitation in those captures, not a count of verdicts that a parser repair would change. The unchanged parser also rejects Astropy's colour-wrapped status tokens: diagnostic replay after stripping ANSI admits the exact IDs in Astropy-14365, without changing any stored result. Astropy-13977 also contains ANSI-sensitive output, but its timeouts remain an independent limitation. No parser repair or counterfactual verdict replacement was applied.

SCG's **71 NOT_AVAILABLE** split into **68 empty lists** and **three nonempty arms with no native admissions**: Astropy-14365 (ANSI text), Matplotlib-25122 (396 passing concrete cases per phase behind three families), and Pylint-6528 (four passing concrete cases per phase behind two families). These three have COMPLETE raw accounting. Its two INCOMPLETE arms are Matplotlib-23299 and scikit-learn-12585: both have a requested ID absent from raw coverage and recorded runner errors; the latter also has parameter-family gaps. These are distinct from the two null no-seed selections.

The 68 SCG empty lists comprise 47 complete and 21 partial graphs. Existing independent static audit evidence found no eligible retained resolved path within the frozen depth, with exact reproduction of every list. This is a statement about the retained graph/configuration, not absence of a runtime call or proof that dynamic Python makes recovery impossible. Prior path diagnosis supplies case-specific dispatch/import/framework explanations for the six witnesses; this evaluation did not rebuild those graphs or extrapolate an exact mechanism to every empty task.

## 6. Representative cases and useful SCG evidence

| Task / label | V2 | SCG | What is supported |
|---|---|---|---|
| Matplotlib-25479 / wrong | 88 IDs; FAIL, COMPLETE | 0; NOT_AVAILABLE | One wrong-patch flag with repeated colormap assertion failure is lost by the empty selection. |
| Django-14140 / right | 2,334; FAIL, other evidence incomplete | 0; NOT_AVAILABLE | Two stable Q-serialization transitions; false alarm against the label, not proof of a bad patch. |
| Matplotlib-25287 / right | 2; NOT_AVAILABLE, COMPLETE raw accounting | 0; NOT_AVAILABLE | Six concrete cases per phase coexist with zero legacy family admissions. |
| Matplotlib-25122 / right | 54; PASS | 3; NOT_AVAILABLE, COMPLETE raw accounting | A large parameter expansion does not produce a native completed verdict for the narrow list. |
| Django-13820 / right | 262; INCOMPLETE | 8; PASS, complete graph | SCG supplies complete evidence for its narrower selected list where V2 has gaps. |
| Django-16631 / wrong | 478; INCOMPLETE | 5; PASS, partial graph | Narrow complete execution is useful evidence but misses the wrong-patch label. |
| SymPy-17318 / wrong | 21; NOT_AVAILABLE, pytest missing | 0; NOT_AVAILABLE | Neither arm establishes correct-patch acceptance or a completed negative test result. |

SCG has PASS where V2 is INCOMPLETE in **four tasks**: Django-13820, Django-16631, Pylint-4970 and scikit-learn-14629. Three are correct-labelled; Django-16631 is wrong-labelled. These are real execution-completeness/cost benefits for selected lists, rather than superior patch validation. Two graphs are complete and two partial. Conversely, Matplotlib-23299 is V2 PASS / SCG INCOMPLETE. All task-level cases, including the 14 wrong patches, remain in the inventory.

## 7. What the earlier SCG studies establish

Historical reports describe overlapping phases and follow-ups rather than five independent replications. For presentation, the five research stages below include Amendment 2 within graph feasibility and the witness/path audits within corrected mapping. They reuse this cohort and must not be pooled as independent statistical evidence.

| Earlier stage | Supported result and implication |
|---|---|
| Graph feasibility and Amendment 2 | Original 56 complete / 23 partial / four resource-limited graphs became 56 complete / 27 partial after explicit SymPy omissions. Graph construction became feasible under retained-source limits; dynamic completeness and test relevance were not established. |
| Registered Phase 2 static selectors | Primary C1/C2 achieved 2/6 each and C3 3/7, below the registered thresholds. Fewer candidates and ranking changes were static evidence, not measured detection or runtime savings. |
| Nine-case static import/SCG side experiment | Broader import closure retained some opportunities but often thousands of tests; resolved-only graph exclusions missed important existing identities. Its proportional runtime estimates were explicitly not measurements. |
| Lightweight receiver type propagation | Added 25,875 resolved callsites, predominantly local constructors, but no resolved-only changed-seed selection benefit. Matched sample graph build was about 1.43x baseline. More resolved edges did not establish better relevant-test reachability or regression recall. |
| Qualified mapping, witness validation and path diagnosis | Corrected 106 existing edited definitions, separated 21 new definitions and removed broad context seeds; paired depth-3 lists fell 715 -> 131. Historical six-witness retention stayed 0/6. Correct mapping eliminated false identities without repairing missing runtime/framework paths; it did not establish preserved test recall. |

Sources are hash-catalogued in `historical_report_inputs.json`: graph report/amendment, Phase 2 report, `next_steps/report.md`, type-propagation report, qualified-mapping report, regression-validation report and regression-path diagnosis. Existing path diagnosis found the six witness misses were not recovered even by uncapped queries over its stored edges; that supports specific stored-model limitations, not a universal impossibility theorem. No broader/ambiguous-edge configuration, alternative depth, dynamic selector or new hybrid was executed in this paired experiment.

## 8. Limits and presentation conclusions

**Observed:** the configuration gives dramatically smaller selections and lower measured cost, 90.36% abstention, zero wrong-patch flags, zero of six historical witnesses retained, and no native FAIL. V2 produces more completed outcomes and one wrong-patch flag, alongside five label-relative false alarms and 62.65% abstention.

**Supported explanation:** strict resolved-only paths and exact edited-definition seeds form an aggressive exclusion boundary. Missing dispatch/framework paths and source/collection/admission limitations can leave useful tests out or their outcomes unscored. The seven V2-confirmed failing identities are all excluded by SCG; a parser repair alone could not recover those omitted requests.

**Unresolved:** precise false-negative rates for all latent regressions, complete semantic validity of old assertions, verdicts under repaired parsers/environments, and full runtime import provenance. All 91 image HEADs differ from the dataset base commits; the relevant-file equivalence checks passed, but neither those checks nor three earlier import-only probes prove every import in the actual full executions. No host-wide isolation/classifier workaround was attempted. The 14 incorrect patches, repository clustering, many abstentions and four common binary tasks cannot support a powered noninferiority claim or establish an optimal cost/coverage tradeoff.

Presentation-ready conclusions:

1. **Selecting fewer tests was achieved; preserving observed regression-detection coverage was not.**
2. **Correcting source identity and adding resolved edges are insufficient proxies for detecting-test reachability.**
3. **V2's six FAIL tasks mean seven reproducible old-test transitions, but only one wrong-patch flag under the study labels.**
4. **SCG's zero false alarms mainly coexist with very low coverage; PASS and empty selection must not become correctness guarantees.**
5. **Do not adopt this resolved-only depth-3 SCG configuration as a replacement or exclusion gate for V2 on this evidence.** Auxiliary ranking or framework modelling remain future hypotheses requiring separate, prospectively frozen evaluation; this study does not establish their benefit.
6. **V2 also needs evidence/admission and environment limitations addressed in a separately reviewed protocol before stronger claims.** This report preserves the current results rather than repairing or rerunning them.

All new analysis lives outside the freeze and results. [Task-arm inventory](task_arm_inventory.csv), [diagnostics](arm_diagnostics.json), [metrics](analysis_metrics.json), [parser/environment evidence](parser_and_environment_diagnostics.json) and exact commands retain the basis for these claims. `analysis_artifact_sha256.json` seals the new evidence; it does not reseal or replace original experiment artifacts.
