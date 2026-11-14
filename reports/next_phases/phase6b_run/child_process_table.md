# Child-process report (before repair)

Source: existing `runs/phase6b_smoke_workers_20261113c` captures. The old journal did not record executable, argv, environment or scope labels. Every exec child without a trace is listed conservatively; environment noninheritance cannot be assigned to individual PIDs from a process-wide flag. No missing field is reconstructed.

| Smoke | Parent / child PID | Executable | argv[0:3] | Python (resolved/shebang) | Spawn scope | Tests receiving old flag |
|---|---|---|---|---|---|---|
| matplotlib__matplotlib-25287 | 1042 / 1059 | not recorded | not recorded | unknown | shared (session/module/class unavailable) | 6 |
| matplotlib__matplotlib-25287 | 1042 / 1062 | not recorded | not recorded | unknown | inside test window | 1 |
| matplotlib__matplotlib-25287 | 1042 / 1063 | not recorded | not recorded | unknown | inside test window | 1 |
| matplotlib__matplotlib-25287 | 1042 / 1064 | not recorded | not recorded | unknown | inside test window | 1 |
| matplotlib__matplotlib-25287 | 1042 / 1065 | not recorded | not recorded | unknown | inside test window | 1 |
| matplotlib__matplotlib-25287 | 1042 / 1074 | not recorded | not recorded | unknown | inside test window | 1 |
| matplotlib__matplotlib-25287 | 1042 / 1075 | not recorded | not recorded | unknown | inside test window | 1 |
| django__django-13033 | 929 / 930 | not recorded | not recorded | unknown | shared (session/module/class unavailable) | 4 |
| django__django-13033 | 929 / 932 | not recorded | not recorded | unknown | shared (session/module/class unavailable) | 4 |
| django__django-12965 | 947 / 948 | not recorded | not recorded | unknown | shared (session/module/class unavailable) | 17 |
| django__django-12965 | 947 / 950 | not recorded | not recorded | unknown | shared (session/module/class unavailable) | 17 |

Matplotlib: the old capture cannot establish whether the flagged test legitimately starts Python; the journal lacks executable/argv evidence. The old loader flags any unfollowed exec, including non-Python programs. A new observation-only smoke is needed before making that determination.
