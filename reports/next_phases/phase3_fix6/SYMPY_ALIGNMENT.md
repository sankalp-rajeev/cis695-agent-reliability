# SymPy command alignment before Fix 6

Reference: [SWE-bench v4.1.0 TEST_SYMPY and SPECS_SYMPY](https://github.com/SWE-bench/SWE-bench/blob/v4.1.0/swebench/harness/constants/python.py), inspected 2026-11-07. The pinned installed SWE-bench 5.0.2 wheel no longer contains the older repository command constants; the published harness source supplies the comparison without opening task labels.

Harness: `PYTHONWARNINGS='ignore::UserWarning,ignore::SyntaxWarning' bin/test -C --verbose <module>`.

Previously the adapter omitted PYTHONWARNINGS. It now sets exactly those two filters before importing SymPy, for both collection and execution, including the current interpreter as well as child processes. It does not suppress DeprecationWarning. Cache disabling already matched `-C` and is applied before the initial import. The adapter uses the task's Python interpreter, executes `bin/test` via runpy, adds `--no-subprocess` to retain the exact selected-name guard, and restricts the native collector to the containing module. Those intentional differences prevent native substring matching or re-execution from adding families; native execution and reporting remain in use.

Only the base quantum printing module was checked: `sympy__sympy-13480`, `sympy/physics/quantum/tests/test_printing.py`. All 16 selected IDs validated, zero INVALID_ID or collection errors, zero test bodies executed, 26.47 s including container/source verification. All archived Python source files and bin/test matched their frozen hashes. This is a load check, not a claim that the former execution-time warning/Reporter failure has disappeared. Receipt: quantum_load_receipt.json. No patched run or correctness comparison.

Adapter tests: 18 passed, including exact warning environment and effective UserWarning/SyntaxWarning suppression, native collection without test-body execution, exact family selection, and Python 3.6 syntax.
