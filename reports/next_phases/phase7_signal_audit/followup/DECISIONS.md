# Follow-up decisions

- This is a report-only follow-up. Existing sealed artifacts, verifier source, policies, configurations, and frozen data remain unchanged; all follow-up outputs and report/check scripts are confined to followup/.
- Correct the accounting description: reports/next_phases/phase4_plan.md and its phase4-plan-frozen version designate Policy S with INVALID_ID excluded as primary for claims about PASS. The sealed audit headline instead used S_invalid_missing. Preserve the old seal and report both explicit names and all five rows.
- All correctness comparisons here are post-hoc, never used to select a policy or change a decision. Use the original frozen83 cohort, all three audited label columns, and stored agent claims.
- New read-only input: reports/next_phases/phase4_plan.md and its tagged version, a pre-registration policy document; configs/verifier/full.yaml, configs/agent/v4_generator.yaml, configs/model/generator.yaml are setup descriptions and resource caps, not grader outcomes.
- New read-only source: src/reliability/verifier/reproduction_freeze.py, reproduction.py, static_checks.py, patch.py, integrity.py and .venv/lib/python3.11/site-packages/minisweagent/agents/default.py. Read them only as text to explain stored fields and distinguish generic termination from limit subtype; do not instantiate an agent, run tests, make model calls, or access a network service. src/reliability/agent/runner.py was read as source metadata only.
- Candidate sources: the 83 frozen_83/patches/*.patch files and the other 17 selected original run task patch.diff files under /home/sankalp/projects/cis695-agent-reliability/runs/. These are agent output. Verify each digest against its selected verification record before counting file edits.
- Existing-test edits include modifications, deletions, and renames of test paths; additions alone do not modify a pre-existing test. Test paths use the unchanged V1 path conventions; include both old and new names. With no test edits, assertion edits have an empty denominator and cannot affect any existing decision through this gap.
- V3 is record-only: the two named records say import PASS. Do not invent an import failure, a missing baseline result, or a genuine/environmental classification when the detailed output was not retained.
- V4 records have a generic LimitsExceeded exit, n_steps=40, and cost below the recorded $1 cap. Report the reached step cap and conditional guard inference separately from the UNKNOWN explicitly recorded subtype. Per-response output-token caps do not provide total token use or wall-clock elapsed time.

- The first independent-check launch did not start Python: Docker rejected a duplicated frozen-plan mount. Preserve initial_launch.stdout.txt and initial_launch_execution.json. Remove only the duplicate launcher mount, then start the checker; no comparison or analysis data was changed. This was a launch error, not a verification mismatch.

## Verified completion (2026-11-16T20:21:11.335833+00:00)

- Independent standard-library verify.py passed with zero mismatches across all 11 tables, counts.json, 302 raw input digests and all 82 original sealed artifacts. It imports no producer module and parses candidate Git headers independently.
- Confirmed pre-registration in the frozen plan, not merely the current draft heading: S_invalid_excluded is primary and yields 14/67/2. The original sealed headline S_invalid_missing yielded 13/68/2. Report the discrepancy directly; do not change the old report or any old tag.
- Fifteen post-hoc combinations and the corresponding false-accept lists and agent-claim precision are complete; no accounting choice or decision was selected using labels.
- All 100 candidate patches are available and no existing test file is touched. Assertion weakening/removal has an empty affected-file set, so this V1 gap changes no existing decision.
- V3 import is PASS in each named record; actual failures are lint and build respectively. No detailed failure output or baseline import outcome is recorded, so genuine/environmental classification and the base comparison remain UNKNOWN.
- All 14 V4 no-output records reached the recorded step cap and remained below the cost cap. Preserve the generic recorded termination and UNKNOWN explicit subtype; keep the step-limit inference conditional on inspected code. Do not invent token usage or elapsed generation time.
- Frozen policy export: /tmp/signal_followup_frozen_plan.md, read-only Git-exported pre-registration source. Raw input paths and their roles are enumerated in input_hashes.csv. The original source, policies, configurations and sealed files remain unchanged.
- New read-only candidate paths for the other 17 tasks, each agent-authored patch data without grader labels:
  - /home/sankalp/projects/cis695-agent-reliability/runs/main_50_b/tasks/astropy__astropy-13398/patch.diff — agent candidate output.
  - /home/sankalp/projects/cis695-agent-reliability/runs/main_50_a/tasks/django__django-12663/patch.diff — agent candidate output.
  - /home/sankalp/projects/cis695-agent-reliability/runs/main_2_rerun_mpl/tasks/matplotlib__matplotlib-21568/patch.diff — agent candidate output.
  - /home/sankalp/projects/cis695-agent-reliability/runs/main_50_b/tasks/matplotlib__matplotlib-22865/patch.diff — agent candidate output.
  - /home/sankalp/projects/cis695-agent-reliability/runs/main_50_a/tasks/matplotlib__matplotlib-24627/patch.diff — agent candidate output.
  - /home/sankalp/projects/cis695-agent-reliability/runs/main_50_a/tasks/matplotlib__matplotlib-25332/patch.diff — agent candidate output.
  - /home/sankalp/projects/cis695-agent-reliability/runs/main_50_b/tasks/psf__requests-1142/patch.diff — agent candidate output.
  - /home/sankalp/projects/cis695-agent-reliability/runs/main_50_a/tasks/psf__requests-1724/patch.diff — agent candidate output.
  - /home/sankalp/projects/cis695-agent-reliability/runs/main_50_a/tasks/psf__requests-1766/patch.diff — agent candidate output.
  - /home/sankalp/projects/cis695-agent-reliability/runs/main_50_a/tasks/psf__requests-2317/patch.diff — agent candidate output.
  - /home/sankalp/projects/cis695-agent-reliability/runs/main_50_b/tasks/psf__requests-2931/patch.diff — agent candidate output.
  - /home/sankalp/projects/cis695-agent-reliability/runs/main_50_b/tasks/psf__requests-5414/patch.diff — agent candidate output.
  - /home/sankalp/projects/cis695-agent-reliability/runs/main_50_a/tasks/psf__requests-6028/patch.diff — agent candidate output.
  - /home/sankalp/projects/cis695-agent-reliability/runs/main_50_a/tasks/pylint-dev__pylint-4551/patch.diff — agent candidate output.
  - /home/sankalp/projects/cis695-agent-reliability/runs/main_50_b/tasks/pylint-dev__pylint-8898/patch.diff — agent candidate output.
  - /home/sankalp/projects/cis695-agent-reliability/runs/main_50_a/tasks/sphinx-doc__sphinx-10614/patch.diff — agent candidate output.
  - /home/sankalp/projects/cis695-agent-reliability/runs/main_50_a/tasks/sphinx-doc__sphinx-7748/patch.diff — agent candidate output.
