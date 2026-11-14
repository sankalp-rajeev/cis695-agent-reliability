# Resolved: A1 approved and pushed

User explicitly approved A1 with the three requested statements. Commit 6d558e8
contains only the appendix; automatic review accepted the commit and push.
Stage 1 resumed. The historical blocker is preserved below.

# Phase 6b blocked at Stage 1

The required append-only Amendment A1 cannot be committed/pushed in this session:
automatic approval review rejected both attempts. No evaluation began, no
experiment metrics were published, and no tags were created. The harness remains
an unfinished draft, preserved in commit da0d971 and the observation checkpoint.
The frozen plan has been restored byte-for-byte; protected tags are unchanged.

Tried:

1. Preflight: disk 276 GiB free; host Docker 26.1.3 reachable; project Python
   3.11.17; remote SSH works. Initial 28 synthetic gates pass.
2. Report existing smoke journals without inferring missing executable/argv data.
3. Add observation-only executable/argv/environment metadata and run the existing
   smoke command without changing its commands, selection or flagging rules.
4. Prepare A1. First draft included child-handling language; review rejected it
   as a change to frozen definitions. Removed all child-handling language.
5. Verify frozen plan is a byte-identical prefix and retry only the exact A1
   requested by the user: scope tags and descriptive test-window secondary
   selection. Review rejected again, stating: "Despite narrowing, the append
   still changes the frozen trace/selection definitions; the plan’s hard stop
   requires recording BLOCKED and restarting rather than amending and pushing it."
6. Restore the plan, preserve report-only evidence, and checkpoint this blocker.

One decision needed: approve committing/pushing the exact A1 appendix expressly
specified in the overnight request. The risk identified by automatic review is
changing a frozen trace/selection definition. No rejection has been bypassed.
An approval question is pending; no answer is assumed.

Resume at Stage 1 after that decision: finish the four child-rule branches,
explicit scope records, new gates and all three smoke gates, then freeze. The
repair budget remains 0/5 because no repair was attempted. Do not infer success
from the initial synthetic gates or observation-only smoke. Stage 4 has not run;
all four headline scientific numbers are unavailable. Merge candidate not ready.

Completed diagnostic capture: the old parallel gate halted with 16/16 incomplete
tests. Other old-rule fractions were 1/4 (Matplotlib) and 4/4 (Django-13033).
All observed exec children were non-Python; environment stripping came from
`/sbin/ldconfig -p`. These facts identify draft overflagging and are not a
scientific verdict. See child_process_table.md, observation_summary.json and
observation_manifest.sha256. No experiment numbers have been verified/sealed.
