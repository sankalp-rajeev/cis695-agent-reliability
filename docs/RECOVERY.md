# Recovery

A half is one process. If the machine sleeps, the SSH session drops, or the process is killed, the task directories already written stay. Resume continues from those directories. It does not start a second experiment id.

## Launch

From a clean tree, at the commit you intend to cite:

```bash
scripts/launch_tmux.sh configs/experiments/main_50_a.yaml
```

That opens tmux session `main_50_a` with two windows. The first runs:

```bash
env -u PYTHONPATH .venv/bin/python scripts/run_pilot.py --experiment configs/experiments/main_50_a.yaml
```

The second runs `scripts/notify.sh`, which posts counts to ntfy.sh when `NTFY_TOPIC` is set in the environment or in `.env`. The runner starts even if that topic is unset; the notify window then exits without posting.

`main_50_b` is the same command with `configs/experiments/main_50_b.yaml`, and only after `main_50_a` has met the interim thresholds in `docs/VERIFIER_POLICY.md` §8.5. Do not launch `configs/experiments/main_100.yaml`.

Attach with `tmux attach -t main_50_a`. Detach with `Ctrl-b` then `d`. The session keeps running.

## Resume

```bash
env -u PYTHONPATH .venv/bin/python scripts/run_pilot.py --resume main_50_a
```

`--resume` takes an experiment id or a config path. It refuses, and does not start a task, unless all three of these hold:

- `git status` is clean. `--allow-dirty` is not accepted on a resume.
- `HEAD` equals `git_commit` in `runs/<experiment>/meta.yaml`.
- The config hash equals `config_hash` in that file. The hash covers the experiment file, the model, agent, and verifier configs it names, and the manifest.

Each accepted resume is appended to `resumes` in `meta.yaml` (timestamp, commit, config hash). The original block is not replaced.

Completed tasks are not redone. A task with `repair_record.json` skips the agent. A task with `verification_record.full.json` skips the verifier. A task with `oracle_record.json` skips the oracle.

## Containers

Agent containers are started with Docker label `experiment_id=<id>`. Verifier containers are named `verify_<id>_<instance>_<suffix>` and carry the same label. List them with:

```bash
docker ps -a --filter label=experiment_id=main_50_a
```

## First-10 halt

On `main_50_a` and `main_50_b` the process exits after ten tasks if there are more than 2 infrastructure failures, mean cost per task is above $0.15, the leakage audit fails, or any task ended `insufficient_balance` or `rate_limited`. The reason is in `runs/<experiment>/checkpoint.json`. Do not resume past that halt by editing the records. Fix the cause, or stop the half.

## What resume will not do

It will not ignore a dirty tree, a moved `HEAD`, or an edited config. It will not merge two experiment ids. It will not rerun a finished task in order to pick up a policy change — a policy change is a new experiment id.
