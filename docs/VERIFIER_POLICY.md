# Regression Test Selection Policy

**Component:** Verifier V2 (existing regression tests)
**Status:** Draft for advisor review — 2026-09-15
**Checklist gate:** Phase 5.1

---

## 1. Purpose and constraint

The verifier runs a subset of the repository's pre-existing tests to determine whether a candidate patch broke previously working behaviour. The subset must be chosen using only information a developer would have with the issue still open: the candidate patch and the repository at the base commit.

The selection must never consult `PASS_TO_PASS`, `FAIL_TO_PASS`, the gold patch, or the gold test patch. This is the property that makes the verifier's decision meaningful; a verifier that selected tests using the benchmark's own relevance list would be answering a question no deployed system can ask.

One structural protection already holds: the gold test patch is not applied at the base commit, so tests introduced by the human fix do not exist in the working tree the verifier reads. Selection cannot reach them even by accident.

---

## 2. Permitted and forbidden inputs

**Permitted**

- the candidate patch (file paths, hunks, changed symbol names)
- the repository tree at the base commit, including all pre-existing test files
- the repository's own test configuration (`pytest.ini`, `setup.cfg`, `tox.ini`, `conftest.py`)
- the issue description

**Forbidden**

- `PASS_TO_PASS`, `FAIL_TO_PASS`
- the gold patch, the gold test patch
- the oracle verdict
- test files created or modified by the *candidate* patch (see §5.3)

---

## 3. Procedure

### 3.1 Convention discovery

Test layout varies by project, so the mapping from source file to test file is derived per repository rather than hardcoded. For each repository, the verifier samples source files and checks which of the following layouts locates a matching test file most often:

- sibling test package — `pkg/module.py` → `pkg/tests/test_module.py`
- mirrored tree — `src/pkg/module.py` → `tests/pkg/test_module.py`
- suffix convention — `module.py` → `module_test.py`
- flat test directory — `tests/test_module.py`

The winning layout and its hit rate are written to the verification record, so the mapping used for any instance is auditable after the fact. If no layout matches on more than a small fraction of sampled files, the repository is marked `CONVENTION_UNKNOWN` and selection falls through to Tier 2 only.

### 3.2 Baseline pass

The selected tests are run **twice**: once against the unpatched base commit, once against the patched tree. Only tests that pass on the base and fail on the patch count as regressions.

This matters because repositories carry pre-existing failures — environment-dependent tests, skips that resolve differently, genuinely broken tests at that commit. Without a baseline, every such failure would be attributed to the candidate patch, inflating the rejection rate with noise and making the verifier look more discriminating than it is.

The baseline result is cached per instance. The base commit never changes, so the baseline is computed once and reused across verifier configurations and ablations.

### 3.3 Selection tiers

Tiers are evaluated in order and unioned. Selection stops when the time budget is projected to be exhausted.

**Tier 0 — whole suite, if it fits.** If the repository's full test suite completes within budget on the baseline pass, run the full suite. More evidence is strictly better, and a suite that runs in two minutes should not be artificially narrowed. Observed oracle runs suggest this is feasible for several repositories in the pilot manifest.

**Tier 1 — direct correspondence.** For each non-test source file the patch modifies, locate its corresponding test file via the discovered convention.

**Tier 2 — symbol reference.** Extract the names of functions, classes, and methods whose definitions the patch touches. Include any test file in the repository that references one of those names. Resolution is by import graph where the module can be parsed, falling back to textual match where it cannot.

Tier 2 exists because Tier 1 misses the common case where behaviour lives in one module and is exercised from another — an ORM compiler change tested through a queryset test, for example. Naming convention alone would not find it.

**Tier 3 — containing package.** Run the full test package containing any Tier 1 or Tier 2 hit, if budget remains.

### 3.4 Budget

Five minutes wall-clock per pass, ten minutes per instance including baseline. Tests are ordered Tier 1 → 2 → 3 so that the highest-relevance tests run first and a budget cut removes the weakest evidence rather than an arbitrary slice.

Five minutes is chosen against the observed oracle evaluation times of 30–120 seconds per instance: generous enough to admit a full suite on most repositories in the manifest, bounded enough that verification cost stays well below repair cost and the whole study remains re-runnable.

---

## 4. Outcome classification

Every selected test resolves to exactly one of:

| Outcome | Meaning |
|---|---|
| `PASS` | passed on base and on patch |
| `REGRESSION` | passed on base, failed on patch |
| `PRE_EXISTING_FAIL` | failed on base — excluded from the regression signal, recorded |
| `NEWLY_PASSING` | failed on base, passes on patch — recorded, not treated as proof of repair |
| `ERROR` | collection or import error, not a test failure |
| `TIMEOUT` | budget exhausted before completion |
| `NOT_RUN` | selected but never reached |

`NOT_RUN` and `TIMEOUT` are never counted as passes. A verifier that treats unexecuted tests as evidence of correctness would accept patches on the strength of work it did not do.

The regression signal passes only if the `REGRESSION` count is zero **and** at least one test actually executed. Zero tests run is `NOT_AVAILABLE`, which cannot produce `ACCEPT`.

### 4.1 Flake handling

Any test classified `REGRESSION` is re-run once in isolation. A test that passes on re-run is marked `FLAKY` and excluded from the regression signal, with the disagreement recorded. Rejecting a correct patch because of a nondeterministic test would land in the false-rejection rate and directly distort the risk–coverage curve.

---

## 5. Edge cases

**5.1 No tests discovered.** Recorded as `NOT_AVAILABLE`, never as a pass. Routes to `FLAG` rather than `ACCEPT`.

**5.2 Patch touches only non-source files.** Documentation or configuration changes yield no Tier 1 or Tier 2 hits. Tier 3 does not apply. Result is `NOT_AVAILABLE`.

**5.3 Patch adds or modifies test files.** Tests authored or edited by the repair agent are excluded from the regression set entirely. They are the agent's own claim about correctness, not independent evidence, and admitting them would let the agent write its own acceptance criteria. Their existence is recorded as a risk feature for V1 and V5; deletion or weakening of pre-existing tests is an integrity failure, not a selection question.

**5.4 Patch fails to apply.** Selection does not run. The integrity check has already rejected.

**5.5 Baseline is catastrophically broken.** If more than half the selected tests fail on the base commit, the environment is suspect rather than the repository. Recorded as `BASELINE_UNRELIABLE` and routed to `FLAG`.

---

## 6. What this deliberately does not do

**It does not select tests by what the patch is trying to fix.** Reasoning about which behaviour the issue describes, and choosing tests accordingly, would make the selection an inference about correctness rather than a mechanical function of the patch. Issue-derived evidence belongs to V4, which is generated independently and measured separately, and keeping the two apart is what allows the ablation to attribute value to one or the other.

**It does not run the agent's own tests.** See §5.3.

**It does not adapt the selection based on results.** Widening the net after a failure, or narrowing it after a pass, would make the test set a function of the patch's behaviour and destroy the comparability of the signal across instances.

---

## 7. On overlap with `PASS_TO_PASS`

Any sufficiently broad selection will overlap the benchmark's `PASS_TO_PASS` set, and Tier 0 may overlap it substantially. This is worth stating plainly rather than leaving for a reader to notice.

The overlap is not leakage. Leakage is a question of information flow, not of set intersection: the policy above never reads the benchmark's test lists, and would produce the same selection if they did not exist. `PASS_TO_PASS` is itself derived from the repository's pre-existing tests, so a policy that runs pre-existing tests is expected to intersect it — that is the point of both.

What the overlap does affect is interpretation. SWE-bench resolution requires both `FAIL_TO_PASS` and `PASS_TO_PASS` to pass, so a verifier running a broad slice of the existing suite is approximating one half of the oracle's criterion while remaining genuinely blind to the other. Reported false-acceptance therefore reflects mostly the `FAIL_TO_PASS` dimension.

Checklist item 5.3 measures this overlap per instance and reports it. The measurement is made after the fact, from the oracle record, and is never fed back into selection.

---

## 8. Open questions for advisor

1. **Is Tier 0 the right default?** Running the whole suite where it fits maximises evidence and simplifies the policy, but makes the overlap with `PASS_TO_PASS` largest, and makes the verifier's regression signal least distinguishable from half the oracle. The alternative — capping at Tier 2 even when budget allows more — yields a weaker but more clearly independent signal. This trades evidential strength against interpretive cleanliness.

2. **Is ten minutes per instance defensible**, or should verification cost be held to a fixed fraction of repair cost so that the ratio, rather than an absolute number, is what stays constant as models change?

3. **Is the single flake re-run sufficient**, given that flakiness enters the false-rejection rate directly? A best-of-three would be more robust and roughly doubles the cost of the failure path only.

4. **Should `NEWLY_PASSING` feed the accept decision at all?** It is currently recorded but unused. A pre-existing test that starts passing after the patch is weak evidence of repair, and admitting it would blur the boundary with V4's issue-derived signal — but discarding it may waste real information.
