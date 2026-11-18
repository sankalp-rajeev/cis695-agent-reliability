# Rerun protocol v1, amendment A2 (decided 18 November 2026, before any arm is sealed or graded)

**Correction to section 6 (grading).** Section 6 says grading uses "the same oracle step as the main study, unchanged, using the pinned swebench 4.0.4 wheel". Those two parts conflict. The main study graded with `reliability.oracle.runner.run_oracle`, which runs the SWE-bench harness from the project lockfile: swebench 5.0.2, the version `scripts/run_pilot.py` records. The 4.0.4 wheel is only for V2's pre_install environment specs. **The rule is "the same oracle as the main study"**: `run_oracle`, unchanged, at the frozen pipeline tag, with the lockfile's swebench 5.0.2 and the same per-task timeout (1800 s).

**Additions, decided now:**
- Grading never writes into a sealed arm folder. It runs on a byte-identical copy of each task's frozen patch and minimal records, in a separate grading folder.
- Grading never runs at the same time as an arm (Phase 4 showed CPU contention can change harness labels), nor with any other Docker-heavy job.
- The primary label is the harness's resolved / not resolved. Harness infrastructure errors are re-run once alone, and if they persist they are reported as class X. Phase 4's label-audit procedure is a sensitivity analysis, not the primary label.

Nothing else changes.
