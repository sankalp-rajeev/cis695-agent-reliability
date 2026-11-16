# Survivor diagnosis (report-only, post-hoc)

**Verdict.** Both patches are wrong, and both are accepted because every execution signal checked something the patch really does satisfy, not the contract the hidden test checks: pylint-4661 picked a different directory than the gold (`~/.local/share/pylint` via `platformdirs` instead of `appdirs.user_cache_dir`) while the issue text allows it, and sympy-17318 stopped the `IndexError` inside `split_surds` instead of making `_sqrt_match` return `[]`. In both tasks the V2 PASS says nothing about correctness for this patch, and the sympy FLAG-to-ACCEPT change is the V2 repair turning an infrastructure NOT_AVAILABLE (no `pytest` in a `bin/test` repository) into a real but non-discriminating PASS.

Labels, the gold patch and the gold tests were read for this report; nothing here changes a decision. No code, policy or config was changed, no model was called, nothing was executed from the stored artifacts.

## Provenance and limits

- Stored artifacts (not copied into git; cited by path):
  - pylint: `~/survivor_data/runs/main_50_b/tasks/pylint-dev__pylint-4661/` (`verification_record.full.json`, `patch.diff`, `oracle_record.json`, `trajectory.jsonl`).
  - sympy: `~/survivor_data/runs/main_3_rerun_infra/tasks/sympy__sympy-17318/` (same files).
  - Original V2 raw output: `~/survivor_data/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results/tasks/<task>/v2/`.
- The sympy survivor is the `main_3_rerun_infra` record. In `main_50_b` the same task has an empty patch (`patch.diff` is 0 bytes, decision REJECT, "integrity check failed"), so it is not the survivor there.
- Gold data: public SWE-bench Verified loaded (the parquet from `princeton-nlp/SWE-bench_Verified`). The gold-comparison parts are therefore included.
- To reason statically about imports and call paths I shallow-fetched the two base commits (`sympy` d4e0231b, `pylint` 1d1619ef) over git into the session scratchpad. Nothing was run and nothing from those trees is committed.
- The V4 test sources are not in `~/survivor_data` (the verification records keep only hashes and run tails). I quote them from `cis695-agent-reliability/reports/failure_analysis/v4_sources.txt` (lines 983-1166 and 1167-1420), which holds the same frozen files. I did not re-hash them against the recorded `sha256`, so treat them as the same files by name only.
- The repaired V2 raw capture is not in `~/survivor_data`. The repaired sympy outcome comes from the sealed Phase 4 summary `reports/next_phases/phase4_rerun/attempt4_seal/results.json`.

Evidence = read from a file. Inference = my reasoning; marked **[inference]**.

## How the decision is formed (evidence)

`src/reliability/verifier/decision.py`, `FullPolicy.decide`: ACCEPT requires integrity PASS, regression (V2) PASS, reproduction (V4) PASS and no high-severity risk flag. V3 (static) is not an input. Reasons stored for both survivors: "all accept conditions met".

---

# 1. pylint-dev__pylint-4661

### 1.1 Agent patch vs gold

Evidence: `patch.diff`, dataset gold.

| | Agent | Gold |
|---|---|---|
| Files | `pylint/config/__init__.py`, `doc/faq.rst` | `pylint/config/__init__.py`, `setup.cfg` (+ test patch) |
| Default location | `PYLINT_HOME = os.environ.get("PYLINTHOME", user_data_dir("pylint", "pylint"))` → `~/.local/share/pylint` | `PYLINT_HOME = appdirs.user_cache_dir("pylint")` → `~/.cache/pylint` |
| Library | `platformdirs` (not declared in the patch) | `appdirs`, added to `install_requires` in `setup.cfg` |
| Other | removes `USER_HOME` logic; `os.mkdir`→`os.makedirs`; rewrites FAQ and `ENV_HELP` | keeps `USER_HOME` and the `~` branches; prints a notice when the old `~/.pylint.d` exists |

Behavioural gap in plain words: the issue asks to stop using `~/.pylint.d` and says data belongs in `$HOME/.local/share/<PROGRAM_NAME>`. The agent followed that sentence. The gold moved the directory to the *cache* location (`~/.cache/pylint`) through a specific library. The hidden test pins that exact value.

The oracle record says the F2P test `tests/lint/unittest_lint.py::test_pylint_home` failed (`oracle_record.json`, `outcome: unresolved`, `pass_to_pass` empty). Gold test change:

```
-        expected = os.path.join(uhome, ".pylint.d")
+        expected = appdirs.user_cache_dir("pylint")
     assert config.PYLINT_HOME == expected
```

Open detail: the oracle record does not say whether the failure is an assertion mismatch or an `import appdirs` error. The agent's own trajectory shows `ModuleNotFoundError: No module named 'appdirs'` in its container (trajectory line 12), and the test file imports `appdirs` at module top. Either way the cause traces to the spec gap, not to a bug in what the agent tried to do.

### 1.2 V4

Evidence (`v4_sources.txt`, `verification_record.full.json`): three tests, all failing on base with `assertion_failure`, all passing twice on the patched tree (`3/3 stable generated tests pass`).

- `test_repro_1`: with `HOME` and `XDG_DATA_HOME` set to temp dirs, `pylint.config.PYLINT_HOME` must be in `{$XDG_DATA_HOME/pylint, $HOME/.local/share/pylint}` and not `~/.pylint.d`.
- `test_repro_2`: with `XDG_DATA_HOME` unset, `PYLINT_HOME == $HOME/.local/share/pylint`.
- `test_repro_3`: same location check, then `save_results`/`load_results` round-trip lands inside it.

Why they pass on the wrong patch: `platformdirs.user_data_dir("pylint")` on Linux returns exactly the paths the tests accept. The tests were derived from the issue text, which names that directory, and the patch implements the same reading.

Versus gold F2P: the gold asserts equality with `appdirs.user_cache_dir("pylint")`, a different directory. No generated test could pass base-fails/patched-passes and also separate the data dir from the cache dir without knowing the gold choice.

Classification: **other: the issue is under-specified and the hidden test encodes one implementation choice** (the generated tests are not weak; they test the issue's stated core faithfully). Secondary: the tests check the location only.

### 1.3 V2

Evidence: `offline.json` (tier membership), `v2/result.json`, `v2/raw/*/stdout.raw`.

- Selected (4), all Tier 1, Tier 2 empty: `tests/test_config.py::test_can_read_ini`, `test_can_read_setup_cfg`, `test_can_read_toml`, `test_can_read_toml_rich_types`. Convention `tests_tree`, hit rate 0.127.
- Executed and passed on both trees: 4/4, "4 passed" (`stdout.raw`), no regressions, `execution_status: EXECUTED`, `completeness: COMPLETE`.
- Exercise of changed code (static, from `tests/test_config.py` and `pylint/config/__init__.py` at base):
  - The tests call `pylint.lint.Run(["--rcfile", ..., __file__])` with `check_parallel` and `sys.exit` mocked and assert on disabled messages, `jobs`, `reports` and the exit call. Nothing reads `PYLINT_HOME`.
  - `import pylint.config` executes the changed module-level lines, so an import error in the patch would fail these tests.
  - `save_results` and `load_results` are the only other users of `PYLINT_HOME`; they are reached from `PyLinter.generate_reports` only when `file_state.base_name` is not None. **[inference]** with `jobs=10` and `check_parallel` mocked that path is not taken, but I did not verify the `Run` control flow.

Verdict on V2: **vacuous for the behaviour the patch changes.** At most a weak import smoke test.

### 1.4 V1 and V3 evidence

- V1 (`integrity`): PASS, no violations; the patch applies; `risk_features`: 2 files, 8 added / 16 removed lines, `unrelated_dirs_touched: 1` (the `doc/` edit). Nothing relevant to the defect.
- V3 (`static`): syntax, import, lint and typecheck PASS; build NOT_AVAILABLE (`No module named build`). Not a decision input.
- Possibly relevant: the diff adds `from platformdirs import user_data_dir` and does not touch `setup.cfg` or any requirement file. In the agent's container `platformdirs 4.3.6` is present only as a dependency of `black` and `virtualenv` (trajectory line 15), so the V3 `import` PASS is environment luck, not declared support. That is an undeclared dependency, a defect independent of the directory choice. I found no stored check that looks for this.

---

# 2. sympy__sympy-17318

### 2.1 Agent patch vs gold

Evidence: `patch.diff`, dataset gold.

Agent (`sympy/simplify/radsimp.py`, function `split_surds`):

```
+    if not surds:
+        return S.One, S.Zero, expr
```

Gold: leaves `split_surds` code unchanged (docstring wording only) and changes `_sqrt_match` in `sqrtdenest.py` so the "all addends square to rationals" branch also requires positivity:

```
-        if all((x**2).is_Rational for x in pargs):
+        sqargs = [x**2 for x in pargs]
+        if all(sq.is_Rational and sq.is_positive for sq in sqargs):
```

Gold F2P `test_issue_12420`:

```
assert _sqrt_match(4 + I) == []
assert sqrtdenest((3 - sqrt(2)*sqrt(4 + 3*I) + 3*I)/2) == I
e = 3 - sqrt(2)*sqrt(4 + I) + 3*I
assert sqrtdenest(e) == e
```

Behavioural gap: for a radicand like `4 + I` (addends square to `16` and `-1`, no `Pow` surds), gold treats it as "not a surd sum", so `_sqrt_match` says "no match" (`[]`). The agent lets it enter the surd path and returns a dummy split `(1, 0, expr)`, so `_sqrt_match(4 + I)` returns `[4 + I, 0, 1]` (traced from the base source: `r, b, a = split_surds(p); res = a, b, r`). The crash is gone but the helper's contract is wrong.

Oracle (`oracle_record.json`): F2P `test_issue_12420` fails; the 10 P2P tests (all in `test_sqrtdenest.py`) pass.

### 2.2 V4

Evidence (`v4_sources.txt`, record): three tests, all `assertion_failure` on base, all `pass` x2 on the patched tree.

- `test_repro_1`: `(3 - sqrt(2)*sqrt(1 + 2*I) + 3*I)/2` must come back unchanged from `sqrtdenest`, no exception.
- `test_repro_2`: five non-denestable radicands (`sqrt(1+2I)`, `sqrt(2+2I)`, `sqrt(1+I)`, `sqrt(-1+2I)`, `sqrt(2+3I)`) return unchanged; a control `sqrtdenest(sqrt(5+2*sqrt(6))) == sqrt(2)+sqrt(3)`.
- `test_repro_3`: composite expressions with `sqrt(1+2I)`, unchanged and idempotent.

Why they pass on the wrong patch: they assert only "no exception, output unchanged" through the public `sqrtdenest`. The agent's guard produces that. They never call `_sqrt_match`, the layer where the gold puts the fix, and they replace the issue's literal expression with `1+2I` because the generator observed the literal one is auto-simplified (docstring in test 1).

Versus gold F2P: assertions 2 and 3 are the same family as V4's inputs, so they very likely pass for the agent too. The agent's own validation says the original expression "evaluates to `I`". **[inference]** the failing assertion is therefore the first one, `_sqrt_match(4 + I) == []`, which is an internal-contract check. The stored oracle record names only the test, not the assertion.

Classification: **tests check the public symptom, the gold test pins an internal contract** (patch fixes only the symptom the test checks). Not "too weak" in the usual sense: the V4 tests catch the original crash.

### 2.3 V2 (repaired run)

Evidence: `offline.json` and `v2/result.json`; sealed Phase 4 summary.

- Selected (21), all Tier 1, Tier 2 empty: every listed test is in `sympy/simplify/tests/test_radsimp.py` (`test_radsimp`, `test_collect_1`..., `test_issue_14608`). Convention `sibling_tests`, score 0.515.
- Executed and passed: 21/21 on base and 21/21 on patched, per `attempt4_seal/results.json` and `results.md` line 133.
- Exercise of changed code (static, base sources):
  - The test file never mentions `split_surds`, `_sqrt_match` or `sqrtdenest` directly.
  - `radsimp.py` line 815 does call `sqrtdenest(sqrt(d.base))`, and `rad_rationalize` calls `split_surds`, so the function is reachable from the selected tests.
  - The patch changes behaviour only when `surds` is empty, which is exactly the input that raised `IndexError` at base. Base ran 21/21 PASS, so no selected test reached that branch (barring a swallowed exception). **[inference]** the patched run takes the same paths as base, so the new line was never executed.
  - The module that observes this defect, `test_sqrtdenest.py`, was not selected: selection follows the edited file (`radsimp.py`), not the place where the bug shows up. Even if it were selected, the 10 P2P tests there pass on this patch (oracle), so only the new F2P test discriminates.

Verdict on V2: **vacuous for this patch** (a pass is guaranteed by construction).

### 2.4 Old V2 vs repaired V2

- Old (`main_3_rerun_infra/.../verification_record.full.json`): regression `NOT_AVAILABLE`, `absence: error`, "tests were selected but none executed ... `/opt/miniconda3/envs/testbed/bin/python: No module named pytest`" for both baseline and patched; summary `NOT_RUN: 21`. Decision FLAG, reason "regression is NOT_AVAILABLE, not PASS". Raw capture (`v2/raw/*/stdout.raw`): the single line `No module named pytest`. Cause: the frozen selection metadata said runner `pytest` (`selection_runner: "pytest: pytest.ini or conftest.py"`) but this sympy tree is run with `bin/test`; Phase 2 classifies the gap as `sympy_runner_mismatch` (`phase2_incomplete_causes/native_gap_ledger.csv`).
- Repaired (`attempt4_seal/results.json`): all four accounting policies PASS, `INVALID_ID: 0`, base 21 admitted/21 passed, patched 21/21. Phase 7 recompute (`phase7_signal_audit/recompute_decisions.csv`, row for 17318): FLAG → ACCEPT, V2 `NOT_AVAILABLE` → `PASS`, policy S_invalid_missing.
- Repair responsible: Phase 3 Fix 5 (commit `ae9e4a7`, `reports/next_phases/phase3_fix5/SUMMARY.md`): SymPy is discovered from `bin/test` and `sympy/__init__.py`, the frozen `pytest` runner label is repaired at run time, and the native invocation is `bin/test -C --verbose --no-subprocess <module>`. Later fixes (14: skips and native flags; 18/18b: identity accounting) shaped accounting; Fix 18b shows `sympy__sympy-17318` base at 21/21 identities recorded. **[inference]** Fix 5 is the change that turned the outcome; I did not bisect.
- Is the new PASS real? Yes as execution (21 real native results on each tree, nothing missing). No as evidence about this patch (2.3). The repair removed a false negative-looking gap and exposed that the gap was masking a signal that could not have helped.

### 2.5 V1 and V3 evidence

- V1: PASS; 1 file, +2 lines, no risk flags.
- V3: syntax and import PASS; lint and typecheck NOT_AVAILABLE (no configuration), build NOT_AVAILABLE. Nothing relevant. Not a decision input.

---

# 3. Cross-task

### What they have in common (evidence unless marked)

1. Both patches are wrong, both pass all four verifier gates (V1 PASS, V2 PASS, V4 PASS, no high-severity risk) under every accounting variant.
2. For both, the only test that discriminates is the F2P test. Pylint's P2P is empty; sympy's P2P all pass on the wrong patch (oracle records).
3. In both, the V2 selection executes real tests that pass but never assert on the changed behaviour (2.3 and 1.3).
4. In both, V4 tests are faithful to the issue and pass because the patch satisfies the issue's visible wording. The hidden test pins something the issue does not state: a specific directory and library (pylint), an internal helper's return value (sympy).
5. **[inference]** Both are "plausible reading of the issue" failures, not careless ones; their agent-side validation was reasonable and self-consistent.

### Which verifier signal would have needed to differ

- V2: it would have had to include a test that observes the changed behaviour. For sympy that means the sqrtdenest module and still not P2P; for pylint there is no such existing test (P2P empty). So V2 alone could not catch either, no matter the selection quality. A V2 *vacuity* signal (below) could have refused a PASS as evidence.
- V4: it would have had to assert on the contract the gold chose. This is not recoverable from the issue text in pylint's case; in sympy's case it requires testing the helper rather than the public entry point.
- V3: possibly relevant only for the pylint undeclared dependency.

### Candidate remedies (listed, not applied)

| # | Remedy | What would confirm it |
|---|---|---|
| R1 | Treat a V2 PASS as informative only if at least one selected test executes a changed line of the patch (coverage or trace of the patched hunks); otherwise report V2 as non-discriminating and do not let it satisfy ACCEPT. | Across all 83 stored/frozen tasks, compute changed-line hit by selected tests on the patched tree (Phase 6a runtime trace machinery may already provide it). Confirm sympy-17318 has 0 hits. For pylint the module-level lines hit on import, so a line criterion would need to be "hit by an assertion path" or a statement-level criterion with some form of behaviour check; check on labelled data whether vacuous-V2 ACCEPTs are enriched for wrong patches and how many right patches would be demoted. |
| R2 | In V4, also test the changed function's contract: have the generator run its assertions on the helper that the traceback or patch points at, plus the issue's literal example, not only a substitute input. | Re-run V4 generation on sympy-17318 with that instruction (needs a model call, so not here); confirm a test of `_sqrt_match` fails on this patch; measure effect on right-patch false rejects. |
| R3 | In V4, detect under-specification: when several implementations satisfy the issue (data vs cache dir; chosen library), mark V4 PASS as "ambiguous" and do not count it as support for ACCEPT. | Have the generator list alternative locations or libraries and see whether the passing tests discriminate them; for pylint-4661 the check on the patched tree should accept both data and cache dirs. Measure how often this fires on right patches. |
| R4 | Mutation sensitivity of V4: apply simple alternative edits to the candidate (e.g. move the sympy guard, change the pylint path) and check whether V4 can tell right from wrong; a suite that passes everything is not evidence. | Offline experiment on stored V4 suites: count how many mutations each suite distinguishes. Predicted from this report: zero for pylint-4661, partial for sympy-17318. |
| R5 | V3 / V1 dependency check: flag imports of third-party modules that the patch does not add to packaging metadata (pylint `platformdirs`). | Run on all 83 frozen patches: how many add a new third-party import without a metadata change, and whether those are wrong more often. Likely rare; useful mainly as a secondary risk flag. |
| R6 | Policy: when V2 is vacuous (R1) and V4 is a single-source signal, downgrade ACCEPT to FLAG. | Re-run `FullPolicy` offline on stored records with R1 applied; check precision gain against label counts and the number of right patches lost. |

Not a remedy for these two: broadening V2 selection (more P2P tests). The oracle shows the extra P2P tests that exist already pass on the sympy patch, and pylint has none.

### Caveats

- Which assertion fails in the sympy F2P test, and whether the pylint failure is an assertion or an import error, are not in the stored records (marked above).
- The V4 sources were taken from the sibling checkout's `v4_sources.txt`, not hash-verified here.
- Two survivors are an anecdote, not a rate; none of the remedies has been measured.
