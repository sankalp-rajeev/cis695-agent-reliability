# Fix 18: SymPy module-import identity accounting

Fresh, source-verified base containers reproduced the same import warning and reporter exception with the exact harness command and the unchanged executor command. See `invocation_comparison.md` for the environment, flags and Python-path differences. The plan was committed first as `de906a3`.

A nonzero SymPy invocation with no reported selected IDs or observed test start is classified as module-import evidence only with a matching stderr traceback and another normally completed invocation on the same tree that reported IDs. Both-tree import gaps remain COLLECTION_ERROR (missing evidence); patched-only gaps retain Fix 17 accounting after base-module progress. Unexplained identities halt even on small SymPy trees. Raw per-invocation stderr attribution and signatures are retained.

## Base-only identity smoke

| Task | G1 identities recorded exactly once | COLLECTION_ERROR | TIMEOUT | NOT_REACHED | Health trip |
|---|---:|---:|---:|---:|---|
| `sympy__sympy-13480` | 763/763 | 16 | 0 | 0 | No |
| `sympy__sympy-17318` | 21/21 | 0 | 0 | 0 | No |
| `sympy__sympy-19783` | 729/729 | 0 | 0 | 0 | No |
| `sympy__sympy-24562` | 662/662 | 0 | 1 | 463 | No |
| `sympy__sympy-14711` | 429/429 | 0 | 0 | 0 | No |

The capped tree was `sympy__sympy-24562`; its recorded budget gaps caused no identity halt. All five tasks have zero missing or duplicate G1 identities and no unexplained non-run identities. Any other allowed non-run categories are recorded in `base_smoke.json`. The old sealed G1 sets used by the smoke match the new exhaustive G1 sets exactly. Frozen reference coverage and drift-reference counts are documented in `reference_coverage.json`.

Import signatures:

- `DeprecationWarning -> PyTestReporter._active_file during import of sympy/physics/quantum/tests/test_printing.py`

## Validation and preservation

- Fourteen new unit checks succeeded; the full suite has 1,362 successful checks with the same six pre-existing check issues and 17 pre-existing setup issues. Only masked unit summaries and issue names are reported.
- Exhaustive G1: 166/166 ready, zero projected halts, zero test bodies. Manifest SHA-256: `946873c02a84475f6e42a99cef824adfcac8e7391a01b6d7b797f33d6410723a`.
- All 852 quarantined attempt-3 files were verified byte-for-byte unchanged; no files were added or removed there.
- Raw smoke/comparison captures remain in ignored run directories, with public hash manifests. No correctness labels, oracle data, benchmark test outcomes or verdicts were inspected for analysis.
- No new freeze tag or full experiment was launched.
