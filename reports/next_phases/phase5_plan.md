# Phase 5 frozen offline replay plan

a. Reference regressions (label-free, from the sealed run only): a test that is PASS on base and FAIL on patched with stable 3/3 confirmation, or REGRESSION_ERROR. Report case by case (the six original native FAIL tasks plus django-10973). No rates over this set.

b. Selectors: V2 Tier 1; V2 Tier 1 + Tier 2 (the V2 list that ran in Phase 4); the corrected static call-graph selector (the frozen paired-harness selections for the same 83 tasks). Each selector is replayed as a subset of the V2 list that ran. A selected test that is not in the V2 list has no reference outcome: count it as "outside reference", never as kept or missed. If per-test tier membership is not recorded in the frozen V2 selection, stop and report that. Do not infer it.

c. Selector metrics per task and selector: reference regressions kept and missed (named), share of the V2 list kept, outside-reference count.

d. Cost model: Phase 4 recorded durations per module process, not per test. Module cost = sum of all end-event durations for that module on the PATCHED tree, including retry and fallback processes. Invent no per-test time. Collection time is reported separately and as a second variant that adds each module's collection-group time. Execution-only is primary.

e. Ordering rule (unchanged from the roadmap): Tier 1 modules before Tier 2; within a tier, modules whose name matches a changed module first; then source order. Compare with 20 random module orderings, seeds 0..19, recorded here: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19. Budgets: 30, 60, 120, 300 s.

f. Time to first regression is two bounds: cumulative time when its module starts (optimistic) and when it ends (conservative). Per budget record modules run, modules not reached, and the share of the V2 list not reached. State per task whether each budget binds (whole patched pass longer than the budget). A budget that does not bind is non-informative and is reported as such.

g. Pre-registered reading: useful if at 120 s the rule keeps at least 90% of reference regressions AND its median time to first regression beats the 25th percentile of the random orderings, on the conservative bound. If the optimistic and conservative bounds disagree, the verdict is "inconclusive". With seven regression tasks, report each case and do not extrapolate.

## Amendment A1

a. Source of tier membership: `reports/v2_discovery_cleanup/comparison_final/offline.json` before_by_tier / after_by_tier. A task's tiers are accepted only if the Phase 4 frozen V2 list (the frozen selection file, verified against the protocol hash as in step 0) equals `before` or `after` for that task EXACTLY in content and order, and the tier sets then union to that list with no ID missing or extra. Record which of before/after matched, per task.

b. A task that matches neither is excluded from the tier-based ordering analysis and reported by name with the reason. Never infer or reconstruct tiers for it. Its selector-replay metrics that don't need tiers (c) are still computed.

c. A test's tier is the lowest tier containing it. A module's tier is the lowest tier among its selected tests. Report any module that mixes tiers.

d. Rules, thresholds, seeds 0..19, budgets 30/60/120/300 s, the bounds, the cost model and the pre-registered reading are unchanged.
