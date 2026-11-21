# V4 freeze (tag `study-v4-frozen`)

V4 is frozen at the Phase 4b prompts with one pass (commit `fa1b016`, re-pilot `6cf1c2b`, all five gates passed). After this tag there are no generator, prompt or V4 code changes. The rule changes that come with the freeze are in [AMENDMENT_2026-11-21.md](AMENDMENT_2026-11-21.md).

## File hashes (sha256)

| Role | File | sha256 |
|---|---|---|
| Generator model pin | `configs/model/generator.yaml` | `26083476ea0ac96095fb56054ec25d7cf445b34ff5eb26ee1eee40512a8ba10c` |
| Requirements prompt | `configs/agent/v4_requirements.yaml` | `43d6432d33dc80424f14b66ff671b08b7130f395ab35f4b92b34bbcfe2614ceb` |
| Per-requirement tests prompt | `configs/agent/v4_tests_per_requirement.yaml` | `c0a034f7f471b36c0fd8d7dc20387056bf866883e7dffcca1390b596185e0916` |
| Legacy V4 prompt (old V4, amendment A4 (vi)) | `configs/agent/v4_generator.yaml` | `78f69e8df13e0e9ca03c24f89aa83755c400e0058052b8a3d9e6f7fcc0b5e4cb` |
| Verifier config (`v4_design: per_requirement`, `v4_passes: 1`) | `configs/verifier/v1_5.yaml` | `c29740699cf3fdc94342adc04735de709922e648ee973596051250151b0b95b5` |
| V4 source | `src/reliability/verifier/reproduction.py` | `e24c7a0f1f835f6dd6193a0208554ecb9bcd891d80e57f85ca564a05c42e4fed` |
| V4 source | `src/reliability/verifier/reproduction_freeze.py` | `4185fcfcbf8dfd5d371016a8cac6abd7ec41593916022c6f0ccffcf69cdf0c93` |
| V4 source | `src/reliability/verifier/reproduction_reuse.py` | `2c02ba4aad3a598764062fce8fac6a7f2574824adef164a99c60da08f0c4b0bd` |
| V4 source | `src/reliability/verifier/reproduction_v1_4.py` | `67a9744b0e802df4a042448779d9b91f6dc5f988f7eaa9489a0588f461ab3f73` |

The three prompt hashes equal the ones the re-pilot recorded in every task's `verification/v4/frozen.json` identity. The in-container test runner hash recorded there is `sha256:30ca495a5ff49b8e4206b32b67800468ffe9ef5d9d60e0939dc9ee2ea6c93898`. It is built from `RUNNER_SOURCE` in `reproduction_freeze.py`.

`generator.yaml` changed only in its `verified:` block (date and fingerprint), which `scripts/verify_model.py --update` wrote. The model, provider and sampling settings are unchanged.

## Generator fingerprint

| | Value |
|---|---|
| Old pin (checked 2026-09-30) | `aeb56401ca74e127821c4f9126dcb669` |
| New pin (checked 2026-11-21) | `bc19ba97cbe016479903222bb1578db6` |
| Model / served model | `deepseek/deepseek-v4-flash` / `deepseek-flash` |
| Re-pilot responses | 858 of 858 report `bc19ba97cbe016479903222bb1578db6` (`extra.response.system_fingerprint` in the generator trajectories) |
| Verification request | PASS, 1 tool call, 308 in / 48 out tokens, $0.00011237 |

Per-response fingerprints are already in every generator trajectory, so no recording code was added. If the fingerprint changes, it is logged as a deviation, not a stop (amendment A2).

## DeepSeek balance

$8.64, read from the provider balance API on 2026-11-21 16:05 UTC, after the verification request. The previous reading was $9.03, before the first pilot. The ledger cost of the two pilots is $1.00 ($0.670 + $0.331), but the reported balance fell by $0.39. This gap has not been explained. The figure above is the provider's own reading.
