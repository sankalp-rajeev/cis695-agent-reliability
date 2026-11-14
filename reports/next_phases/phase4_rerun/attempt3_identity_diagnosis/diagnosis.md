# Attempt 3 identity-only diagnosis

Category **C**: the native SymPy reporter terminates with an unhandled `AttributeError` for missing `_active_file` while reporting an import-time `DeprecationWarning`. No selected name appears in any raw stream. The runner exits with code 1, without a signal. This is neither a format-only gap nor a cap hit.

The original attempt directory remains unchanged. Its 852 files are quarantined by an external hash manifest. No correctness labels, oracle data or test outcome fields were decoded. Raw excerpts are restricted to masked import/runner traceback metadata.

All 16 IDs share module `sympy/physics/quantum/tests/test_printing.py` on both trees:

| ID suffix (append to module with `::`) | Name in runner/stdout/stderr | Line format | Covering batches on each tree |
|---|---|---|---|
| `test_anticommutator` | 0 / 0 / 0 | Absent | 8, 9 |
| `test_big_expr` | 0 / 0 / 0 | Absent | 8, 24 |
| `test_cg` | 0 / 0 / 0 | Absent | 8, 10 |
| `test_commutator` | 0 / 0 / 0 | Absent | 8, 11 |
| `test_constants` | 0 / 0 / 0 | Absent | 8, 12 |
| `test_dagger` | 0 / 0 / 0 | Absent | 8, 13 |
| `test_gate` | 0 / 0 / 0 | Absent | 8, 15 |
| `test_gate_failing` | 0 / 0 / 0 | Absent | 8, 14 |
| `test_hilbert` | 0 / 0 / 0 | Absent | 8, 16 |
| `test_innerproduct` | 0 / 0 / 0 | Absent | 8, 17 |
| `test_operator` | 0 / 0 / 0 | Absent | 8, 18 |
| `test_qexpr` | 0 / 0 / 0 | Absent | 8, 19 |
| `test_qubit` | 0 / 0 / 0 | Absent | 8, 20 |
| `test_spin` | 0 / 0 / 0 | Absent | 8, 21 |
| `test_state` | 0 / 0 / 0 | Absent | 8, 22 |
| `test_tensorproduct` | 0 / 0 / 0 | Absent | 8, 23 |

The initial batch covers all 16 IDs; each retry covers one ID. Every invocation has an end receipt, and each tree has a final driver-completion receipt. Process exit was recorded normally by the OS, but runner execution did not finish normally because of the unhandled reporter exception.

| Tree | Pass elapsed / cap (s) | Module invocation range (s) | Cap hit | Driver completed |
|---|---|---|---|---|
| base | 1115.309 / 1800 | 0.626765–0.701554 | No | Yes |
| patched | 1097.947 / 1800 | 0.638751–0.716540 | No | Yes |

| Tree | Batch | Retry of | Selected IDs covered | Exit code | Duration (s) | Runner completed normally | End receipt |
|---|---|---|---|---|---|---|---|
| base | 8 | — | All 16 | 1 | 0.701554 | No | Yes |
| base | 9 | 8 | test_anticommutator | 1 | 0.687027 | No | Yes |
| base | 10 | 8 | test_cg | 1 | 0.640095 | No | Yes |
| base | 11 | 8 | test_commutator | 1 | 0.677021 | No | Yes |
| base | 12 | 8 | test_constants | 1 | 0.640035 | No | Yes |
| base | 13 | 8 | test_dagger | 1 | 0.682599 | No | Yes |
| base | 14 | 8 | test_gate_failing | 1 | 0.630691 | No | Yes |
| base | 15 | 8 | test_gate | 1 | 0.678248 | No | Yes |
| base | 16 | 8 | test_hilbert | 1 | 0.687341 | No | Yes |
| base | 17 | 8 | test_innerproduct | 1 | 0.631493 | No | Yes |
| base | 18 | 8 | test_operator | 1 | 0.700736 | No | Yes |
| base | 19 | 8 | test_qexpr | 1 | 0.641822 | No | Yes |
| base | 20 | 8 | test_qubit | 1 | 0.678217 | No | Yes |
| base | 21 | 8 | test_spin | 1 | 0.633022 | No | Yes |
| base | 22 | 8 | test_state | 1 | 0.660820 | No | Yes |
| base | 23 | 8 | test_tensorproduct | 1 | 0.626765 | No | Yes |
| base | 24 | 8 | test_big_expr | 1 | 0.637313 | No | Yes |
| patched | 8 | — | All 16 | 1 | 0.675874 | No | Yes |
| patched | 9 | 8 | test_anticommutator | 1 | 0.716540 | No | Yes |
| patched | 10 | 8 | test_cg | 1 | 0.643342 | No | Yes |
| patched | 11 | 8 | test_commutator | 1 | 0.640725 | No | Yes |
| patched | 12 | 8 | test_constants | 1 | 0.638751 | No | Yes |
| patched | 13 | 8 | test_dagger | 1 | 0.697870 | No | Yes |
| patched | 14 | 8 | test_gate_failing | 1 | 0.675641 | No | Yes |
| patched | 15 | 8 | test_gate | 1 | 0.647193 | No | Yes |
| patched | 16 | 8 | test_hilbert | 1 | 0.669593 | No | Yes |
| patched | 17 | 8 | test_innerproduct | 1 | 0.674747 | No | Yes |
| patched | 18 | 8 | test_operator | 1 | 0.706385 | No | Yes |
| patched | 19 | 8 | test_qexpr | 1 | 0.671936 | No | Yes |
| patched | 20 | 8 | test_qubit | 1 | 0.669678 | No | Yes |
| patched | 21 | 8 | test_spin | 1 | 0.644957 | No | Yes |
| patched | 22 | 8 | test_state | 1 | 0.664775 | No | Yes |
| patched | 23 | 8 | test_tensorproduct | 1 | 0.710103 | No | Yes |
| patched | 24 | 8 | test_big_expr | 1 | 0.646520 | No | Yes |

Full identity-to-invocation mapping, exact argv, byte offsets, raw-source hashes, pass caps and per-invocation durations are in `diagnosis.json`. Each interval is measured against the existing 1,800-second per-pass cap; no per-invocation cap was reached. Start/end events do not record absolute per-batch elapsed time within the pass, so no finer cap-remaining value is inferred.

Per the category-C stop instruction: no plan/code amendment, G1 rerun, runtime smoke, unit-suite rerun, freeze tag or new experiment was performed. The requested smoke scope is retained below for any separately authorized follow-up.

Tasks 34–37: `sympy__sympy-13480`, `sympy__sympy-17318`, `sympy__sympy-19783`, `sympy__sympy-24562`.

All SymPy-runner tasks: `sympy__sympy-13480`, `sympy__sympy-14711`, `sympy__sympy-17318`, `sympy__sympy-19783`, `sympy__sympy-24562`.
