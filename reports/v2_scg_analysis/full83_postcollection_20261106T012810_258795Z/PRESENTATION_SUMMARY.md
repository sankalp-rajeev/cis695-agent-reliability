# CIS 695: what the paired experiment establishes

**Question:** Can corrected, resolved-only, depth-3 SCG select fewer tests without
sacrificing regression detection compared with updated V2?

**Answer for this configuration and cohort:** fewer tests and lower measured cost
were achieved; preservation of observed regression-detection coverage was not.
The experiment does not establish the same conclusion for all static call graphs.

| Result | Updated V2 | Corrected SCG |
|---|---:|---:|
| PASS / FAIL | 25 / 6 | 8 / 0 |
| INCOMPLETE / NOT_AVAILABLE / no verdict | 39 / 13 / 0 | 2 / 71 / 2 |
| Incorrect patches flagged | 1/14 | 0/14 |
| Correct-labelled patches flagged | 5/69 | 0/69 |
| Binary outcome coverage | 37.35% | 9.64% |
| Historical named witnesses selected and confirmed | 6/6 | 0/6 |
| Selection-worker + execution wall seconds | 7,805 | 1,499 |

- On the same 81 tasks with available lists, SCG selected **131 versus 57,159
  IDs (99.77% fewer)**. Its two unavailable lists remain null. Most of its cost
  reduction accompanies empty selections and abstention, not matched detection.
- V2 confirmed seven base-pass/patched-fail transitions across six tasks. SCG
  selected none of those tests. Only Matplotlib-25479 is an incorrect-labelled
  patch; the six historical witnesses belong to five correct-labelled patches.
  A reproducible old-test failure is not automatically a defective patch.
- Only four tasks have binary outcomes in both arms, all PASS/PASS; one is
  labelled incorrect. This cannot support a noninferiority claim. SCG's zero
  false alarms also cannot establish better specificity at equal coverage.
- SCG produces complete selected-list PASS evidence on four tasks where V2 is
  INCOMPLETE. This is useful narrow evidence; one of the four patches is wrong.
- All 39 V2 INCOMPLETE verdicts preserve a recorded original PASS with evidence
  gaps. Timeouts, NOT_RUN IDs, collection/runner errors, malformed raw-ID mapping
  and parameter-family admission loss overlap. Raw observations are never
  silently promoted to native outcomes.
- Additional recorded limitations: pytest absent in all five SymPy images;
  ANSI-colour admission loss in Astropy; unavailable Landlock isolation for the
  shadow classifier; incomplete actual-run import provenance. Relevant source
  hashes and all 780 raw capture hashes still verify.

The earlier graph-feasibility, static-selection, import/SCG side study,
type-propagation and corrected-mapping studies provide progressively more precise
source/graph evidence. They reuse the cohort and are not independent replications.
More resolved edges and correct edited-symbol identities did not establish
detecting-test reachability. This live run adds measured execution evidence.

**Recommendation:** do not replace V2 or use this SCG configuration as its test
exclusion gate on this evidence. V2 also needs stronger evidence coverage and
label-relative interpretation. Alternative graph models, ranking/hybrid uses or
parser/environment repairs require separate prospective evaluation; no such
benefit is claimed from this run.

All 83 pairs/166 arms were verified, original files remain unchanged, and all
analysis was post-collection without new benchmark execution. Full evidence,
scope, historical-study interpretation and uncertainties are in
[FINAL_SCIENTIFIC_REPORT.md](FINAL_SCIENTIFIC_REPORT.md).
