INCONCLUSIVE: file-level selection kept 12/12 reference regressions, with a median per-task reduction of 3.33% and 0 traced/untraced disagreements on Phase-4-stable tests.
DO NOT ADOPT: total execution cost was 1464.838s versus 741.721s baseline; median-task costs were 37.539s versus 16.968s.

All 13 pre-registered tasks completed in eval_set.json order. No task or test was excluded to pass a gate.

| Task | Reference kept | Selected / V2 | Executed | Reduction | Incomplete / executed base | Stable differences | Cost / baseline (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| django__django-10973 | 5/5 | 8/13 | 6 | 53.85% | 0/11 | 0 | 2.470 / 1.865 |
| django__django-12209 | 1/1 | 3319/3319 | 3119 | 6.03% | 0/3161 | 0 | 280.030 / 130.876 |
| django__django-14140 | 2/2 | 2334/2334 | 2033 | 12.90% | 0/2033 | 0 | 96.108 / 45.062 |
| django__django-14631 | 1/1 | 4468/4468 | 4130 | 7.56% | 0/4354 | 0 | 315.188 / 157.136 |
| matplotlib__matplotlib-25479 | 1/1 | 88/88 | 88 | 0.00% | 0/265 | 0 | 21.027 / 8.920 |
| pytest-dev__pytest-5809 | 1/1 | 4/4 | 4 | 0.00% | 0/4 | 0 | 1.254 / 0.667 |
| sphinx-doc__sphinx-10435 | 1/1 | 90/90 | 87 | 3.33% | 0/111 | 0 | 37.539 / 16.968 |
| matplotlib__matplotlib-24637 | 0/0 | 16/16 | 16 | 0.00% | 0/278 | 0 | 16.481 / 6.332 |
| pallets__flask-5014 | 0/0 | 203/203 | 202 | 0.49% | 0/285 | 0 | 8.717 / 5.172 |
| pydata__xarray-6744 | 0/0 | 42/362 | 38 | 89.50% | 0/2443 | 0 | 360.947 / 156.836 |
| pytest-dev__pytest-5787 | 0/0 | 206/206 | 132 | 35.92% | 0/189 | 0 | 41.665 / 20.016 |
| scikit-learn__scikit-learn-12585 | 0/0 | 769/769 | 768 | 0.13% | 0/1394 | 0 | 281.950 / 190.940 |
| sphinx-doc__sphinx-7910 | 0/0 | 16/16 | 16 | 0.00% | 0/16 | 0 | 1.461 / 0.931 |

Pooled selected/executed: 11563/10639 of 11888 V2 IDs. Pooled reduction: 10.51%.
Reusable-history cost: 370.135s versus 360.751s for the sealed full patched passes.
TRACE_INCOMPLETE: 0; without usable traces: 940; patch-only absent definitions/files: 8.

Break-even uses the frozen inequality `(T - 1) * B < r * P`. Both sides and the strict comparison appear per task in per_task.csv. Costs sum all module-process end events, including retries and fallback events; collection and setup costs are excluded.

Limits: these results cover this frozen set and these Phase 4 images. Shared initialization can touch a changed file and retain every test in scope; this is the primary definition. Missing, skipped, errored and unreached traces are retained. Reduction uses actual executed selected IDs over the frozen V2 list size, so retained skipped IDs contribute no execution. The patched baseline is sealed Phase 4 data, not a simultaneous full patched rerun.

Function-level selection, test-window-only selection and all time ratios are exploratory. They do not alter the primary verdict or adoption rule. No patched pass was run for the test-window-only selection; its table reports selection counts only.

Exploratory pooled tracing time ratio T: 2.873. Selected patched/Phase 4 outcome differences: 0; these are reported separately from the preregistered traced/untraced criterion.

Phase 4 FLAKY exclusions from the stable-outcome criterion:
None.

Unspecified cases: none; no incomplete evaluation task was omitted.

Run: `/home/sankalp/projects/cis695-v2-scg-ubuntu-publication/runs/phase6b_eval_20261114`. Frozen harness: `phase6b-harness-frozen` at `92a1e8e04d4cc788322eca3152739504dced2319`. Independent verification is documented in verification.md; this report must not be sealed before that check passes.
