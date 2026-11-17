# Rerun protocol v1, amendment A1 (decided 17 November 2026, while blinded)

**Trigger (label-free):** during arm B (gpt-4.1-mini on the U-M Toolkit), the repair of `django__django-13569` ended after 4 successful calls. The 5th response came back with `finish_reason: content_filter` and `filtered: true` in the ledger (the Azure content filter on the U-M gateway). The agent recorded termination `error`, and the task froze an empty patch. The runner counts it as an ordinary no-patch task, as if the model had failed. The UM probe saw 0 filtered responses in 265 calls; this is the first in arm B, after 17 tasks.

**Amendment:** a task whose repair stage contains any ledger call with `finish_reason` `content_filter` or `any_filtered: true`, and whose repair did not complete with a non-empty patch, is classed as **provider-blocked**.
- Provider-blocked tasks are reported separately, together with their count. Like agent-infrastructure tasks, they are excluded from the precision metrics in section 8.
- Sensitivity analysis: they are counted as no-patch tasks instead.
- A filtered call in a task that still produced a non-empty patch does not change that task's class; it is only reported.
- The same rule applies to arm A, where it is expected to be inert because the DeepSeek route has no content filter.

**What does not change:** the pipeline, the run, the decision rule and every other part of the protocol. No retry of filtered calls is added, because that would change agent behaviour relative to the main study. Classification uses only ledger fields recorded during the run; no labels, grader output or task outcomes are used.

**Status:** made before any arm was sealed or graded. It is recorded as a protocol amendment, not as a post-hoc deviation.
