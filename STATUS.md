# UM cost probe status

Done: all three model verifications and all three authorized task attempts on gpt-4.1-mini. Total estimated spend $0.65728395 including $0.00031875 verification; no cost cap fired and no filtering event occurred in 265 new calls. django-14373 cost $0.05068680; scikit-learn-12973 cost $0.26790480 (V4 RepeatedFormatError); django-16899 cost $0.33837360 (100-step repair limit, no patch, V4 empty-patch skip).

Done: cost-only report and measured/repriced 10/83-task projections; numeric-only DeepSeek whole-set comparison; 75 focused tests; independent ledger/report reconciliation; all 38 frozen files match origin/main. No correctness grading, V1–V3, or oracle run.

Running: none; paid work and report validation are finished.

Next: review reports/umgpt_probe/REPORT.md to choose a rerun model; observed skips/errors limit the 83-task budget estimate. No further paid calls planned. Publication branch: feature/umgpt-routing.
