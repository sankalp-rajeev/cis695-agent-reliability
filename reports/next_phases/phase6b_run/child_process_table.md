# Child-process report (before repair)

Source: existing `runs/phase6b_smoke_workers_20261113c` captures. The old journal did not record executable, argv, environment or scope labels. Every exec child without a trace is listed conservatively; environment noninheritance cannot be assigned to individual PIDs from a process-wide flag. No missing field is reconstructed.

| Smoke | Parent / child PID | Executable | argv[0:3] | Python (resolved/shebang) | Spawn scope | Per-child flag reach (scope size when unrecorded) |
|---|---|---|---|---|---|---|
| matplotlib__matplotlib-25287 | 1042 / 1059 | not recorded | not recorded | unknown | shared (session/module/class unavailable) | unrecorded; recorded scope 6 |
| matplotlib__matplotlib-25287 | 1042 / 1062 | not recorded | not recorded | unknown | inside test window | 1 |
| matplotlib__matplotlib-25287 | 1042 / 1063 | not recorded | not recorded | unknown | inside test window | 1 |
| matplotlib__matplotlib-25287 | 1042 / 1064 | not recorded | not recorded | unknown | inside test window | 1 |
| matplotlib__matplotlib-25287 | 1042 / 1065 | not recorded | not recorded | unknown | inside test window | 1 |
| matplotlib__matplotlib-25287 | 1042 / 1074 | not recorded | not recorded | unknown | inside test window | 1 |
| matplotlib__matplotlib-25287 | 1042 / 1075 | not recorded | not recorded | unknown | inside test window | 1 |
| django__django-13033 | 929 / 930 | not recorded | not recorded | unknown | shared (session/module/class unavailable) | unrecorded; recorded scope 4 |
| django__django-13033 | 929 / 932 | not recorded | not recorded | unknown | shared (session/module/class unavailable) | unrecorded; recorded scope 4 |
| django__django-12965 | 947 / 948 | not recorded | not recorded | unknown | shared (session/module/class unavailable) | unrecorded; recorded scope 17 |
| django__django-12965 | 947 / 950 | not recorded | not recorded | unknown | shared (session/module/class unavailable) | unrecorded; recorded scope 17 |

Matplotlib: the old capture cannot establish whether the flagged test legitimately starts Python; the journal lacks executable/argv evidence. The old loader flags any unfollowed exec, including non-Python programs. A new observation-only smoke is needed before making that determination.


## Observation-only rerun

Run: `runs/phase6b_smoke_observation_20261114`. Only child metadata was added; old flagging/selection rules and runner commands were retained. These are diagnostic observations, not evaluation results. Shared scope is recorded as session by the draft when no test is active; it cannot distinguish module/class setup.

| Smoke | Parent / child PID | Executable (resolved) | argv[0:3] | Python / shebang | Environment inherited | Spawn scope | Tests receiving old flag |
|---|---|---|---|---|---|---|---|
| matplotlib__matplotlib-25287 | 1038 / 1055 | gs (/usr/bin/gs) | `["gs", "--version"]` | False | True | session/shared (module/class unrecorded) | 0 |
| matplotlib__matplotlib-25287 | 1038 / 1058 | git (/usr/bin/git) | `["git", "help"]` | False | True | inside test window | 1 |
| matplotlib__matplotlib-25287 | 1038 / 1059 | git (/usr/bin/git) | `["git", "--git-dir", "/testbed/.git"]` | False | True | inside test window | 1 |
| matplotlib__matplotlib-25287 | 1038 / 1060 | git (/usr/bin/git) | `["git", "help"]` | False | True | inside test window | 1 |
| matplotlib__matplotlib-25287 | 1038 / 1061 | git (/usr/bin/git) | `["git", "--git-dir", "/testbed/.git"]` | False | True | inside test window | 1 |
| matplotlib__matplotlib-25287 | 1038 / 1070 | git (/usr/bin/git) | `["git", "--git-dir", "/testbed/.git"]` | False | True | inside test window | 1 |
| matplotlib__matplotlib-25287 | 1038 / 1071 | git (/usr/bin/git) | `["git", "--git-dir", "/testbed/.git"]` | False | True | inside test window | 1 |
| django__django-13033 | 928 / 929 | git (/usr/bin/git) | `["git", "log", "--pretty=format:%ct"]` | False | True | session/shared (module/class unrecorded) | 0 |
| django__django-13033 | 928 / 931 | /sbin/ldconfig (/sbin/ldconfig) | `["/sbin/ldconfig", "-p"]` | False / #!/bin/sh | False | session/shared (module/class unrecorded) | 4 |
| django__django-12965 | 947 / 948 | git (/usr/bin/git) | `["git", "log", "--pretty=format:%ct"]` | False | True | session/shared (module/class unrecorded) | 0 |
| django__django-12965 | 947 / 950 | /sbin/ldconfig (/sbin/ldconfig) | `["/sbin/ldconfig", "-p"]` | False / #!/bin/sh | False | session/shared (module/class unrecorded) | 16 |

All observed exec children in these smokes were non-Python. The two environment-stripping children were `/sbin/ldconfig -p`, once in each Django session; the resolved file has `#!/bin/sh`. The other Django child was Git. Matplotlib spawned Ghostscript in shared initialization and Git during `test_set_line_coll_dash_image[png]`; that test did **not** spawn an untraced Python interpreter in the observation capture. The old loader nevertheless flagged it for an unfollowed child.

- matplotlib__matplotlib-25287: old TRACE_INCOMPLETE = 1/4 (25.00%); traced/untraced outcomes match = True; workers with tests = 0.
- django__django-13033: old TRACE_INCOMPLETE = 4/4 (100.00%); traced/untraced outcomes match = True; workers with tests = 0.
- django__django-12965: old TRACE_INCOMPLETE = 16/16 (100.00%); traced/untraced outcomes match = True; workers with tests = 3.

The unmodified smoke gate stopped at parallel Django because the old flags exceeded 5%. No threshold was changed, no repair was attempted, and no evaluation metrics were published. The draft gates enforce 5% only on parallel Django; the authorized repair must extend it to every smoke.

## Repaired smoke gates

Final captures: `runs/phase6b_smoke_final_20261114`. All three have 0% TRACE_INCOMPLETE; traced/untraced outcomes match and repeated selections are identical. Parallel Django has three test-running workers. Independent raw-journal recomputation matches all three primary/exploratory selections and trace accounting. Matplotlib’s previously flagged Git-spawning test is now complete; it did not spawn Python.

Reporting clarification: the old shared rows did not record per-child environment/flag provenance, so their original numbers were scope sizes, not measured flag reach. They are now labeled unrecorded with scope size. In the observation-only rerun, shared Ghostscript and Git inherited activation and propagated no old flag (0); ldconfig stripped it and propagated the old session flag to 4 and 16 executed tests. Each Matplotlib test-window Git child caused the same single old-loader flag. No scope size is substituted for a measured flag count. This table clarification changes no smoke gate, evaluation capture, selection, threshold, or result.
