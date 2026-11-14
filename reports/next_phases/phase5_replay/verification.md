# Phase 5 replay verification

The final replay script completed both commands successfully:

```text
python3 scripts/phase5_replay.py --output /tmp/phase5-replay-final-a1-1
python3 scripts/phase5_replay.py --output /tmp/phase5-replay-final-a1-2
```

All six output files were compared as bytes across both invocations and the published report directory. Every file was identical. Each invocation verified all 1,799 manifested run files before and after computation, checked the frozen selection protocol hashes, and rechecked its other input hashes before writing outputs.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| tier_match.csv | 5030 | `70eadbfe2f0b6d11a051ee103a7fd19523996b1c1883a08e5621c54080c85c4c` |
| selector_replay.csv | 20239 | `e73fd55802560a9293f904aa28e4b7dc4dc4b2c0f18bcf3f68496e1d794ddd00` |
| ordering_replay.csv | 18360358 | `356c5f6cc22e81f8e4a7f8a744d6e872ddd18eed4efce575a9447399d78da40d` |
| per_task_costs.csv | 20361 | `86c97ee2e0c64aebd10629e58c8bce3d739a803350768f8573245c8bd9f7ca97` |
| results.json | 1081863 | `8dd782e2e005e9e767baccb438b8391e02d6daca34f601254f162a301cd1ff8a` |
| results.md | 20615 | `995cff4e0574b9eebe276bad0420b738e4da24f8d58faa0df1cc640aca1c4efd` |

Final source hashes:

- `scripts/phase5_replay.py`: `312ceeab0204aafe296c20fd694f38cc54450f91b3ee64b14b1d9207f732f03a`
- `tests/unit/test_phase5_replay.py`: `9051213eea8cb753aee065c8acc93f9df745029fc88399cbcb85507c4f14a65c`

Static validation passed: Python AST parsing and `ruff check --no-cache scripts/phase5_replay.py tests/unit/test_phase5_replay.py`. Synthetic unit checks were added but not executed. No Docker, benchmark or unit-test execution, model calls, correctness labels, oracle inputs, existing tag updates, or changes to pre-existing sealed artifacts. Phase 6b was not started.

The original annotated plan tag remains `d4af4b870dd6f24b3fac61233b04c0c12b39f24a`. The new annotated Amendment A1 tag is `97969395d0992959e6c0096fc6967babf0b17fdd`.
