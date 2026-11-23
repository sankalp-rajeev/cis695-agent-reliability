"""scripts/analyze_v1_5.py: metric functions, policy variants S1-S3, scope and label handling."""

import importlib.util
import json
import math
import pathlib
import sys

import pytest

from reliability.verifier.decision import Decision, SignalOutcome
from reliability.verifier.policy_v1_5 import EvidenceV15

ROOT = pathlib.Path(__file__).resolve().parents[2]
P, F, NA = SignalOutcome.PASS, SignalOutcome.FAIL, SignalOutcome.NOT_AVAILABLE


def _mod():
    spec = importlib.util.spec_from_file_location("analyze_v1_5", ROOT / "scripts" / "analyze_v1_5.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["analyze_v1_5"] = mod  # dataclasses resolve annotations through sys.modules
    spec.loader.exec_module(mod)
    return mod


A = _mod()


# Statistics.

def test_wilson_known_values():
    lo, hi = A.wilson(8, 10)
    assert math.isclose(lo, 0.4902, abs_tol=1e-4) and math.isclose(hi, 0.9433, abs_tol=1e-4)
    assert A.wilson(0, 0) == (None, None)
    lo, hi = A.wilson(0, 60)
    assert lo == 0.0 and math.isclose(hi, 0.0602, abs_tol=1e-4)


def test_newcombe_difference():
    lo, hi = A.newcombe(56, 70, 48, 80)
    # Newcombe (1998) method 10 example: 0.2 difference, CI (0.0524, 0.3339).
    assert math.isclose(lo, 0.0524, abs_tol=1e-3) and math.isclose(hi, 0.3339, abs_tol=1e-3)
    assert A.newcombe(1, 0, 1, 2) == (None, None)


def test_fisher_two_sided():
    assert math.isclose(A.fisher_two_sided(3, 1, 1, 3), 0.4857, abs_tol=1e-4)
    assert math.isclose(A.fisher_two_sided(10, 0, 0, 10), 1.0825e-05, rel_tol=1e-3)
    assert A.fisher_two_sided(0, 0, 0, 0) == 1.0


def row(system, iid, correct, decision, empty=False, labelled=True):
    return A.Row(system=system, instance_id=iid, empty=empty, labelled=labelled, correct=correct,
                 decisions={"frozen": decision}, v4_full_pass=False, recall=False)


def test_metrics_counts_rates_and_lift():
    rows = [row("s", f"t{i}", c, d) for i, (c, d) in enumerate([
        (True, "ACCEPT"), (True, "ACCEPT"), (True, "FLAG"), (True, "REJECT"),
        (False, "ACCEPT"), (False, "FLAG"), (False, "REJECT"), (False, "REJECT")])]
    rows.append(row("s", "e1", None, "REJECT", empty=True))
    rows.append(row("s", "u1", None, "ACCEPT", labelled=False))
    m = A.metrics(rows, "frozen")
    assert (m["n"], m["correct"], m["wrong"], m["empty"], m["unlabelled"]) == (8, 4, 4, 1, 1)
    assert m["base_rate"]["value"] == 0.5
    assert m["accept_precision"]["value"] == pytest.approx(2 / 3)
    assert m["lift"] == pytest.approx((2 / 3) / 0.5)
    assert m["coverage"]["value"] == 0.5 and m["false_accept_rate"]["value"] == 0.25
    assert m["wrong_rejected"]["value"] == 0.5 and m["correct_rejected"]["value"] == 0.25
    assert m["flag_rate"]["value"] == 0.25
    assert m["held_back_difference"]["value"] == pytest.approx(0.75 - 0.5)


def test_accept_weighted_base_rate_weights_systems_by_their_accepts():
    rows = ([row("a", f"a{i}", i < 9, "ACCEPT" if i < 3 else "FLAG") for i in range(10)]
            + [row("b", f"b{i}", i < 1, "ACCEPT" if i < 1 else "FLAG") for i in range(10)])
    pooled = A.metrics(rows, "frozen", systems=("a", "b"))
    # accepts: a 3 (base rate 0.9), b 1 (base rate 0.1) -> (3*0.9 + 1*0.1) / 4 = 0.7
    assert pooled["accept_weighted_base_rate"] == pytest.approx(0.7)
    assert pooled["lift_accept_weighted"] == pytest.approx(1.0 / 0.7)


def test_bootstrap_is_task_clustered_and_seeded():
    rows = [row(s, f"t{i}", (i + k) % 2 == 0, "ACCEPT" if (i + k) % 3 else "FLAG")
            for i in range(30) for k, s in enumerate(("a", "b"))]
    one = A.bootstrap(rows, "frozen", resamples=200, seed=20261126)
    two = A.bootstrap(rows, "frozen", resamples=200, seed=20261126)
    assert one == two and one["resamples_used"] <= 200
    assert one["h1_ci"][0] <= one["h1_ci"][1] and one["h2_ci"][0] <= one["h2_ci"][1]


# Policy variants.

def ev(**kw):
    base = dict(integrity=P, regression=P, reproduction=P, v4_design="per_requirement",
                v4_full_pass=True, v4_pass_units=2)
    base.update(kw)
    return EvidenceV15(**base)


def test_s1_ignores_high_severity_risk():
    e = ev(high_severity_risk=True)
    assert A.decide_variant(e, (), "frozen", A.FROZEN_FOR_TESTS)[0] == "FLAG"
    assert A.decide_variant(e, (), "s1", A.FROZEN_FOR_TESTS) == ("ACCEPT", "R6")


@pytest.mark.parametrize("violations,expected", [
    (("unexpected_config_edit",), "ACCEPT"), (("harness_file_edit",), "ACCEPT"),
    (("conflict_markers", "binary_blob"), "ACCEPT"), (("does_not_apply",), "REJECT"),
    (("unparseable",), "REJECT"), (("conflict_markers", "test_deleted"), "REJECT"),
])
def test_s2_drops_only_the_four_manipulation_findings(violations, expected):
    manipulation = bool(set(violations) & {"unexpected_config_edit", "harness_file_edit", "test_deleted"})
    e = ev(integrity=F, prohibited_manipulation=manipulation, patch_applies="does_not_apply" not in violations)
    assert A.decide_variant(e, violations, "frozen", A.FROZEN_FOR_TESTS)[0] == "REJECT"
    assert A.decide_variant(e, violations, "s2", A.FROZEN_FOR_TESTS)[0] == expected


def test_s3_is_s1_and_s2():
    e = ev(integrity=F, prohibited_manipulation=True, high_severity_risk=True)
    assert A.decide_variant(e, ("harness_file_edit",), "s1", A.FROZEN_FOR_TESTS)[0] == "REJECT"
    assert A.decide_variant(e, ("harness_file_edit",), "s2", A.FROZEN_FOR_TESTS)[0] == "FLAG"
    assert A.decide_variant(e, ("harness_file_edit",), "s3", A.FROZEN_FOR_TESTS) == ("ACCEPT", "R6")


@pytest.mark.parametrize("kw,expected", [
    ({}, "ACCEPT"), ({"regression": F}, "REJECT"), ({"regression": NA}, "FLAG"),
    ({"reproduction": F, "v4_full_pass": False}, "ACCEPT"), ({"v3_absolute_failure": True}, "ACCEPT"),
    ({"integrity": F}, "REJECT"), ({"high_severity_risk": True}, "FLAG"),
])
def test_v1_v2_only_baseline(kw, expected):
    assert A.decide_variant(ev(**kw), (), "v1v2", A.FROZEN_FOR_TESTS)[0] == expected


def test_v1_4_1_variant_uses_v1_4_1():
    assert A.decide_variant(ev(regression=F, reproduction=NA, v4_full_pass=False, v4_pass_units=1),
                            (), "v141", A.FROZEN_FOR_TESTS)[0] == "REJECT"
    assert A.decide_variant(ev(regression=F, reproduction=NA, v4_full_pass=False, v4_pass_units=1),
                            (), "frozen", A.FROZEN_FOR_TESTS)[0] == "FLAG"


# Conflict markers fired only on "=======" lines.

@pytest.mark.parametrize("detail,expected", [
    ("[conflict_markers] a.py: unresolved merge marker: '======='", True),
    ("[conflict_markers] a.py: unresolved merge marker: '=======x'; [conflict_markers] b.py: unresolved merge marker: '=======y'", True),
    ("[conflict_markers] a.py: unresolved merge marker: '<<<<<<< HEAD'", False),
    ("[conflict_markers] a.py: unresolved merge marker: '======='; [conflict_markers] b.py: unresolved merge marker: '>>>>>>> x'", False),
    ("nothing here", False),
])
def test_equals_only_conflict_markers(detail, expected):
    assert A.only_equals_markers(detail) is expected


# Scope and labels.

def test_scope_drops_task_and_pair_exclusions(tmp_path):
    task_ex = tmp_path / "t.json"
    task_ex.write_text(json.dumps({"excluded": [{"instance_id": "x__x-1", "batch": 1}]}))
    pair_ex = tmp_path / "p.json"
    pair_ex.write_text(json.dumps({"excluded": [{"system": "b", "instance_id": "y__y-2", "batch": 1}]}))
    scope = A.Scope.load(["x__x-1", "y__y-2", "z__z-3"], task_ex, [pair_ex])
    assert not scope.keeps("a", "x__x-1") and scope.keeps("a", "y__y-2") and not scope.keeps("b", "y__y-2")
    assert scope.keeps("b", "z__z-3") and not scope.keeps("a", "w__w-4")
    everything = A.Scope.load(["x__x-1", "y__y-2"], None, [])
    assert everything.keeps("b", "y__y-2") and everything.keeps("a", "x__x-1")


def test_labels_drop_on_official_patch_hash_mismatch(tmp_path):
    path = tmp_path / "labels.json"
    path.write_text(json.dumps({"system": "s", "labels": {
        "a__a-1": {"resolved": True, "official_patch_sha256": "11"},
        "a__a-2": {"resolved": False, "official_patch_sha256": "99"},
        "a__a-3": {"resolved": None},
        "a__a-4": {"resolved": True}}}))
    labels, problems = A.load_labels(path, {"a__a-1": "11", "a__a-2": "22", "a__a-3": "33", "a__a-4": "44"})
    assert labels == {"a__a-1": True, "a__a-4": True}
    assert problems["patch_sha256_mismatch"] == ["a__a-2"] and problems["no_label"] == ["a__a-3"]
