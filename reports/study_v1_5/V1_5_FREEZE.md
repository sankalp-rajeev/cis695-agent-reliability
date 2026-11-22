# v1.5 freeze (tag `v1.5-frozen`)

Phase 8 set the decision switches in `configs/verifier/v1_5.yaml` to the set Phase 7 adopted ([ADOPTION.md](ADOPTION.md)) and changed nothing else in that file. After this tag there are no changes to `src/` or `configs/`. Headline decisions come only from `scripts/decide_v1_5.py --frozen`, which reads the switches at this tag.

## Switches

| switch | key | value |
|---|---|---|
| r2 | `r2_v3_reject` | on |
| r3 | `r3_extended_reject` | off |
| r6 | `r6_accept_v2_not_available` | on |
| r6b | `r6b_accept_one_uncovered` | on |

Adopted in Phase 7: r2, r6, r6b. ADOPTION.md gates: all pass. Late (A5): no.

The V4 keys of `v1_5.yaml` (`reproduction` and every `v1_5.v4_*`) equal their values at `study-v4-frozen`, and the other eight sha256 values in [V4_FREEZE.md](V4_FREEZE.md) still match. `v1_5.yaml` differs from `study-v4-frozen` only in its switch lines.

## File hashes (sha256)

| Role | File | sha256 |
|---|---|---|
| config | `configs/verifier/v1_5.yaml` | `be997bc6c48d9108b0f3b0e411603677639e55b5c2d57b991b0394a6792d15cb` |
| config | `configs/verifier/run_health_generic_exceptions.json` | `133b1718eeb53df319c53042a3a37ffd59f2f97b2955d9871e51543a79928f13` |
| policy | `src/reliability/verifier/decision.py` | `bcc404845a2c270f26885268e64b475aa50f4f9426cdaa3447a6fcbfa7d000f2` |
| policy | `src/reliability/verifier/evidence.py` | `11397764d5da1a18ab1b71fc53f4c56ee76dcfa9c0ed035d4002d0633e266f37` |
| policy | `src/reliability/verifier/policy_v1_4.py` | `7ea72dfaf7eeb885072938025f40457588a8df67e6bf0b2fe8f90d97da3b9876` |
| policy | `src/reliability/verifier/policy_v1_4_1.py` | `70cc9b343c00c59686c04d1f71a2e21431488c3a32d110f19959c5745d5acfbc` |
| policy | `src/reliability/verifier/policy_v1_5.py` | `ab7f24dc50ebc67872979392f28581dc89c0a8f58e78a4587b6108026c9a3cb4` |
| V1 | `src/reliability/verifier/integrity.py` | `c25ab4334c51835c2f6c977193b3f7d947a62fed5d1249814ffbebfd3249c73c` |
| V1 | `src/reliability/verifier/integrity_v1_4.py` | `25bcc111cfa3f64520267ef6d96f3a7b8c094e0630f8009491f50fc3452864c0` |
| V1 | `src/reliability/verifier/patch.py` | `ccbbbabbcecec46bae2498c4c4853eb15f8666eeac83200011ae547a976655a7` |
| V3 | `src/reliability/verifier/static_v1_4.py` | `ada8d8d85ffafb74e958a354dfd212c21a0e9ee5332ff801b8319d5478d9ca6f` |
| V3 | `src/reliability/verifier/static_checks.py` | `48a7fbb6ad3aaaeac894dfdd639a0172e7ed2a21f450b3ac618d7bdf76efa88a` |
| V2 and run health | `src/reliability/verifier/accounting.py` | `06052e03368d0b038aa84a37ee53bcb70fe3f332766667aaf5f51072c1855f9b` |
| V2 and run health | `src/reliability/verifier/admission_reference.py` | `f712cf7cb04045d49f789751d01feb1a4389062595f9cdb2ca58bf26af57c2fe` |
| V2 and run health | `src/reliability/verifier/archive_tree.py` | `985c3a60e363f3e9d6834d4843944a27c43f1cc9e03c263f88a67e944405857e` |
| V2 and run health | `src/reliability/verifier/collection.py` | `930eb0f10cdc88e5c035bbf522fe47c8b1df9b4c4397bb0755f5808a78865ee4` |
| V2 and run health | `src/reliability/verifier/container.py` | `65f712aac5a43ce64b97ed208296adc3147ab1bb8b2a1d43f26d857421aef85e` |
| V2 and run health | `src/reliability/verifier/drift_reference.py` | `a931fd4496d29fb9f6f87fb8178cc79e9d1b13a16af33a999d4f90e6631ad6a1` |
| V2 and run health | `src/reliability/verifier/g1_reference.py` | `4da9b80ffc8ac304f591ad5536dc82fad49897fb5bcd239d99d331de8e9eb209` |
| V2 and run health | `src/reliability/verifier/generic_health.py` | `e8682c8b0c71a2d3db46a527a458fd474b64e3cf908721b0022a6bca2dbb049b` |
| V2 and run health | `src/reliability/verifier/guarded_v2.py` | `72698fe170ce90f633311d4ae0096c67a702c292f719056140cd0acbc9ce8d34` |
| V2 and run health | `src/reliability/verifier/id_validation.py` | `e8d3b674aecd0c258a8066124476393f2ef0238b88df81b5c672335807a292fa` |
| V2 and run health | `src/reliability/verifier/inline_g1.py` | `955e106dad690d00d9c10ae65ac27535ab1f8872001d642bfbea2d8a3fbb69b0` |
| V2 and run health | `src/reliability/verifier/module_skips.py` | `7a5da3a8109ad3f9a2251829516d9f160e319e6e0842578c030ac8f11d6caaf9` |
| V2 and run health | `src/reliability/verifier/native_reference.py` | `5b5eac00f0e7366bec2b4a0a8abd446f44dc9bbc81c2aa15a61524e6489159ad` |
| V2 and run health | `src/reliability/verifier/node_ids.py` | `26cc7638b2c01149a652bfdaec7175e2a765510fad30970b0fd67af1a1fbd2fd` |
| V2 and run health | `src/reliability/verifier/pre_install.py` | `da2e424e890befaca3970749bf9ea7dd6af16e903ab7054b791c26b8a68652dc` |
| V2 and run health | `src/reliability/verifier/record.py` | `5bd77c62138d0dbbb099112ba78a4667ecf12a8c7f314f77a0920505e4c3baa8` |
| V2 and run health | `src/reliability/verifier/regression.py` | `f0275408d2674c02bfd6dc46c19c50fa1178cf1978efcc5e22eac2aa18f62a99` |
| V2 and run health | `src/reliability/verifier/result_parser.py` | `3e8171018764380a62a0720be101ebd7069470869d214cf117b4075037e7ce8c` |
| V2 and run health | `src/reliability/verifier/run.py` | `ef24e6ad9c95add1b81958ad141f40abcd3549c9aba30b3e517797dfa5f0c7a0` |
| V2 and run health | `src/reliability/verifier/run_health.py` | `ae433133ff3863034829402035df68da321a156bd23b9cd21d10540f0530a2e6` |
| V2 and run health | `src/reliability/verifier/run_v1_4.py` | `396e5acb4c968477030853046d6ca1eecb2219e0581338362dc840f4b6942430` |
| V2 and run health | `src/reliability/verifier/run_v1_4_1.py` | `7b01141dd5a73f6fc425bb8f2807f72b9dce9ee173c88dbfc659f80e62e745c5` |
| V2 and run health | `src/reliability/verifier/selection.py` | `fc0080021e9760f2f1e2a0fe76b5c4ec6c02b2f59e45bd2de13d702264f76654` |
| V2 and run health | `src/reliability/verifier/source_integrity.py` | `9e8ba6c5897bf6920f4fbbc00baac4d6f4a94cdb09627fae7086a6b3bf10796b` |
| V2 and run health | `src/reliability/verifier/superseded_rule.py` | `4c3150eb15af25c7f1914e88abbe3eece28ae306aac1f367c23f0540d85594f4` |
| V2 and run health | `src/reliability/verifier/superseded_rule_v2.py` | `dc3d9c5206f75c73f1b9783e89b0940936992e0a41a1b4a12c103e8598eef90a` |
| V2 and run health | `src/reliability/verifier/superseded_shadow.py` | `76a88c0abb4dbf5e2f0dc7231c0e4d97e9cdc84d91b6580f65abec363e1b5f62` |
| V2 and run health | `src/reliability/verifier/superseded_shadow_v2.py` | `3dc70ba25c9e3f7ddc739873f0043e803d2c0548a54bb64c87abcbd7b241d6eb` |
| V2 and run health | `src/reliability/verifier/sympy_adapter.py` | `370e4840b4d5302c34ebf418b82121fe8f7d29495074c0d395f864c613e2d4ae` |
| V2 and run health | `src/reliability/verifier/task_specs.py` | `f20461bc970ae7a3bf09802802e3b4c6ae496f4132cb129e0732eb642c4dbbf5` |
| V2 and run health | `src/reliability/verifier/validated_run.py` | `18840fa7f83804fcd71b983251524375d0a4ec02d0f0b4b0897e376de33f58b0` |
| runner | `src/reliability/e2e_runner.py` | `4c41e215e06a4f9f48a0b74248078c28abf4913597a5630c636fd7c75418401d` |
| runner | `src/reliability/e2e_models.py` | `00efc0fd0cffe40bbb6c7738d60bf67b5b185e2484439b8c33744a5cd3d2eb76` |
| runner | `scripts/run_e2e.py` | `33cc44bb775167fb51dc9b50c2eba29634156e82727ce32cf7ba9f49e6eeada4` |
| runner | `scripts/decide_v1_5.py` | `aca6638114519889a031d9bf4aad8bd4d8023cf9b4c319cc065f6cd8a856f5cc` |

V4's own files are pinned in [V4_FREEZE.md](V4_FREEZE.md).
