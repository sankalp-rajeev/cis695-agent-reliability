# V2 discovery cleanup and 83-task review package

This directory preserves a new validation baseline. Historical study results are not rewritten, and no full 83-task evaluation has been launched.

The discovery comparison uses only the final 83 candidate patches and verified base archives. Known historical detecting tests and observed raw IDs are consulted afterward to audit retention, never to construct or tune selection. SCG and import-closure selector outputs are excluded.

Primary artifacts:

- `report.md`: findings, integration results and limitations.
- `comparison_final/offline.json`: original/improved discovery for every task, tier memberships, identities and hashes.
- `audit/summary.json`, `audit/removed_ids.json`: independent tokenizer/scope proofs for all 351 removed IDs.
- `audit/valid_outer_definitions.json`, `audit/known_witnesses_retained.json`, `audit/observed_raw_tests_retained.json`: retention evidence.
- `comparison_final/docker_protocol.json`: the original/cleaned A/B, B/A schedule for the three authorized integration tasks.
- `comparison_final/docker/`: fresh environment observations, native results and byte-exact raw captures for all 12 arms. `commands.jsonl` preserves command provenance.
- `integration_audit/`: frozen-capture replay through unchanged adapters, record serialization, FullPolicy and BaselinePolicy. Other verifier stages are explicitly disabled; these are V2-only policy projections.
- `inputs/`: a four-column allowlisted task projection, local-image inventory and Docker resource provenance.
- `frozen_83/`: the final protocol, 83 task/test manifests, candidate patch bytes, issue text, host package inventory and hashes. Added after the validated code commit, whose exact hash is `protocol.json:code_revision`.

## Review without execution

From the original repository, with its existing environment:

```bash
env -u PYTHONPATH .venv/bin/python scripts/v2_evaluation.py validate \
  --frozen reports/v2_discovery_cleanup/frozen_83
```

This verifies frozen inputs and execution-source/configuration hashes. It starts no container. The prepared cohort includes 39 locally available images and 44 unavailable image tags; the complete experiment cannot execute all 83 tasks until the missing environments are restored and a new manifest is reviewed. Existing images are never substituted or pulled automatically.

The protocol binds its task/test/patch/issue manifests transitively by SHA-256. The runner also checks current interpreter/package versions and selected-test/candidate-changed source hashes inside each container. It records a differing image Git HEAD rather than silently claiming historical full-image identity.

## Execution only after user review and approval

The following is documentation, not authorization to launch. Use a new output directory and the exact hash of the approved `protocol.json`:

```bash
env -u PYTHONPATH .venv/bin/python scripts/v2_evaluation.py run \
  --frozen reports/v2_discovery_cleanup/frozen_83 \
  --out runs/v2_83_<new_run_id> \
  --approved-protocol-sha256 <reviewed_protocol_sha256>
```

The runner refuses a mismatched approval hash, changed source/configuration, changed manifests and an existing output directory. It runs tasks sequentially, disables networking and baseline-cache reuse, preserves the existing regression confirmation and baseline-unreliable rules, and keeps the superseded-assertion classifier shadow-only. It creates a ledger and one outcome for every task, including environment/runner errors. It does not retry a failed task or resume over existing evidence; a process interruption requires review and a separately named continuation design.

No model, agent, gold test, oracle evaluation or V1/V3/V4 execution is part of this V2-only experiment. A complete PASS requires complete evidence; FAIL retains precedence when an actual regression was found despite other execution gaps.

## Metrics after collection

```bash
env -u PYTHONPATH .venv/bin/python scripts/v2_evaluation.py summarize \
  --out runs/v2_83_<new_run_id>
```

The summary includes native signals, execution/completeness states, missing and timed-out IDs, raw concrete-case coverage, runtime, confirmation/shadow costs, evidence size and available cgroup lifetime CPU/peak-memory measurements. Unsupported resource measurements remain unavailable. Legacy parser gaps are reported separately from raw-ID accounting.

Correctness precision/recall/F1 and historical-witness detection require separate, post-collection JSON sidecars. They are never accepted by `prepare` or `run`. A correctness sidecar maps every task ID to `{"patch_sha256": "<64 hex>", "correctness": "right"}` or `wrong`. A witness sidecar maps each relevant task ID to `{"patch_sha256": "<64 hex>", "test_ids": ["path::test"]}`. Both must match the exact candidate hashes; historical observations are not assumed to reproduce in a fresh environment.

Pass them with `summarize --labels <correctness.json> --witnesses <witnesses.json>` only after all 83 tasks are accounted for. Positive prediction is native V2 FAIL and positive target is a wrong patch. Report binary-only and all-labeled-task recall/F1 separately; INCOMPLETE and unavailable executions are abstentions, not inferred PASS. Undefined ratios remain null. No updated accuracy, precision, recall or F1 is claimed before this fresh execution.

## Reproduction of validation

`scripts/v2_discovery_experiment.py offline` writes a new comparison directory. Its parent must contain `inputs/tasks.json`; it requires the pinned local candidate export and 83 base archives. The `docker` mode additionally requires the exact three prior-audit image IDs and writes a new AB/BA validation protocol, never an 83-task run. `scripts/v2_discovery_validate.py` independently audits discovery, and `scripts/v2_discovery_integration_audit.py` replays saved captures without executing tests. All output helpers refuse to overwrite existing artifacts.

The full host unit suite was run offline against a temporary copy of the existing Hugging Face cache because the original cache is read-only in the session sandbox. No dataset download, dependency installation, image pull or replacement environment was used.
