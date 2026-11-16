V1 caught 10 of 11 rejection probes; all three controls passed (13 of 14 expectations met). Replacing a pre-existing assertion with `assert True` passed integrity, while removing the assertion rejected.

Evidence: v1_fixtures/assertion_loosened.patch, v1_raw_observations.json, and v1_adversarial.csv. The loosened patch applies cleanly to the archived real task tree. integrity.py::_test_weakening compares assertion counts and skip additions; equal-count semantic weakening is missed. Suggested fix: flag semantic assertion edits for review or add a conservative AST-based weakening check with adversarial coverage. No verifier change was made.

The clean control is the smallest frozen83 candidate whose stored integrity outcome is PASS, selected without correctness data. All execution used unchanged V1 in an offline Docker container against three pristine archive members. The probes test detection, not repair correctness or complete robustness.
