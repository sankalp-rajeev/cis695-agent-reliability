# Pylint-6528 CPU environment check

No tests, patch application, collection or launcher changes. Three disposable containers used the pinned launcher flags, including `--pull=never`, `-w /testbed`, `--network none` and `sleep infinity`; only the requested CPU override differs between variants. Each command uses the launcher’s `docker exec -w /testbed NAME bash -lc ...` boundary. Unique names/diagnostic labels are used.

UTC timestamp: `2026-11-06T21:05:08.683475+00:00`.

Pinned image tag: `swebench/sweb.eval.x86_64.pylint-dev_1776_pylint-6528:latest`.

Verified local image ID: `sha256:9ba92d212c060748bacf6410d82d24322460bf950db75b511a3eac41bd3f0720`.

This is a fresh environment probe, not proof of historical cgroup values in the sealed full-83 run.

## pinned_default

Launch:

```bash
/usr/bin/docker run --pull=never -d --name verify_phase1_cpu_80acc865e2d7 --label experiment_id=phase1_cpu_check -w /testbed --network none swebench/sweb.eval.x86_64.pylint-dev_1776_pylint-6528:latest sleep infinity
```

Launch exit: `0`.

Launch stdout:
```text
046596dd0a7daf9223e1e3b0dff634ca73f78c00af872c912d090eb6203a636e
```
Launch stderr:
```text
(empty)
```

Command:

```bash
python -c "from pylint.lint.run import _cpu_count, _query_cpu; print(_cpu_count(), _query_cpu())"
```

Exit: `0`.

stdout:
```text
1 1
```
stderr:
```text
(empty)
```

Command:

```bash
cat /sys/fs/cgroup/cpu/cpu.shares /sys/fs/cgroup/cpu/cpu.cfs_quota_us /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>&1
```

Exit: `0`.

stdout:
```text
1024
-1
100000
```
stderr:
```text
(empty)
```

Command:

```bash
stat -fc %T /sys/fs/cgroup
```

Exit: `0`.

stdout:
```text
tmpfs
```
stderr:
```text
(empty)
```

Cleanup exit: `0`; stdout:
```text
verify_phase1_cpu_80acc865e2d7
```
Cleanup stderr:
```text
(empty)
```

## cpu_shares_2048

Launch:

```bash
/usr/bin/docker run --pull=never -d --name verify_phase1_cpu_ccff7c4a1227 --label experiment_id=phase1_cpu_check -w /testbed --network none --cpu-shares 2048 swebench/sweb.eval.x86_64.pylint-dev_1776_pylint-6528:latest sleep infinity
```

Launch exit: `0`.

Launch stdout:
```text
97ea4b13f93caaadf117e90af5fc27b1bee73e2688ee8f596d24893413d19b05
```
Launch stderr:
```text
(empty)
```

Command:

```bash
python -c "from pylint.lint.run import _cpu_count, _query_cpu; print(_cpu_count(), _query_cpu())"
```

Exit: `0`.

stdout:
```text
2 2
```
stderr:
```text
(empty)
```

Command:

```bash
cat /sys/fs/cgroup/cpu/cpu.shares /sys/fs/cgroup/cpu/cpu.cfs_quota_us /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>&1
```

Exit: `0`.

stdout:
```text
2048
-1
100000
```
stderr:
```text
(empty)
```

Command:

```bash
stat -fc %T /sys/fs/cgroup
```

Exit: `0`.

stdout:
```text
tmpfs
```
stderr:
```text
(empty)
```

Cleanup exit: `0`; stdout:
```text
verify_phase1_cpu_ccff7c4a1227
```
Cleanup stderr:
```text
(empty)
```

## cpus_2

Launch:

```bash
/usr/bin/docker run --pull=never -d --name verify_phase1_cpu_4b7d26f9edd0 --label experiment_id=phase1_cpu_check -w /testbed --network none --cpus 2 swebench/sweb.eval.x86_64.pylint-dev_1776_pylint-6528:latest sleep infinity
```

Launch exit: `0`.

Launch stdout:
```text
1488d549c395f8d3ea805b889fbfe6b0bee8feaaf94835080cfc12d831830792
```
Launch stderr:
```text
(empty)
```

Command:

```bash
python -c "from pylint.lint.run import _cpu_count, _query_cpu; print(_cpu_count(), _query_cpu())"
```

Exit: `0`.

stdout:
```text
2 2
```
stderr:
```text
(empty)
```

Command:

```bash
cat /sys/fs/cgroup/cpu/cpu.shares /sys/fs/cgroup/cpu/cpu.cfs_quota_us /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>&1
```

Exit: `0`.

stdout:
```text
1024
200000
100000
```
stderr:
```text
(empty)
```

Command:

```bash
stat -fc %T /sys/fs/cgroup
```

Exit: `0`.

stdout:
```text
tmpfs
```
stderr:
```text
(empty)
```

Cleanup exit: `0`; stdout:
```text
verify_phase1_cpu_4b7d26f9edd0
```
Cleanup stderr:
```text
(empty)
```


## Interpretation of this fresh environment check

| Variant | `_cpu_count()` | `_query_cpu()` | shares | quota | period | mount type |
|---|---:|---:|---:|---:|---:|---|
| pinned_default | 1 | 1 | 1024 | -1 | 100000 | tmpfs |
| cpu_shares_2048 | 2 | 2 | 2048 | -1 | 100000 | tmpfs |
| cpus_2 | 2 | 2 | 1024 | 200000 | 100000 | tmpfs |

The default has no quota and shares=1024; Pylint’s shares/1024 heuristic reports 1. Doubling shares or imposing a two-CPU quota makes both helpers report 2. This demonstrates the present image/host behavior, not historical resource values. All three disposable containers were removed; the launcher is unchanged.
