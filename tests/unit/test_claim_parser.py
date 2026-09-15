"""Phase 3.2 gate: claims parse, or fail explicitly.

Fixtures cover well-formed, malformed, missing, and adversarial outputs. The
adversarial set is the important one: an agent that *sounds* confident has not
made a claim, and treating prose as agreement would manufacture agent assertions
that were never made - biasing the exact quantity the study measures.
"""

from __future__ import annotations

import dataclasses

import pytest

from reliability.agent.claim_parser import (
    ClaimStatus,
    UnparseableReason,
    parse_claim,
)

# --- well-formed -----------------------------------------------------------

WELL_FORMED = [
    ("FINAL_STATUS: RESOLVED\nVALIDATION_EVIDENCE: ran pytest, 12 passed",
     ClaimStatus.RESOLVED),
    ("FINAL_STATUS: UNRESOLVED\nVALIDATION_EVIDENCE: could not reproduce",
     ClaimStatus.UNRESOLVED),
    ("**FINAL_STATUS:** RESOLVED\n**VALIDATION_EVIDENCE:** suite green",
     ClaimStatus.RESOLVED),
    ("`FINAL_STATUS`: RESOLVED\n`VALIDATION_EVIDENCE`: ok", ClaimStatus.RESOLVED),
    ("FINAL_STATUS:RESOLVED\nVALIDATION_EVIDENCE:tight spacing",
     ClaimStatus.RESOLVED),
    ("final_status: resolved\nvalidation_evidence: lowercase",
     ClaimStatus.RESOLVED),
    ("Work summary here.\n\nFINAL_STATUS: UNRESOLVED\nVALIDATION_EVIDENCE: n/a",
     ClaimStatus.UNRESOLVED),
]


@pytest.mark.parametrize("text,expected", WELL_FORMED)
def test_well_formed_claims_parse(text, expected):
    claim = parse_claim(text)
    assert claim.status is expected
    assert claim.is_parseable
    assert claim.reason is None


def test_evidence_is_captured():
    claim = parse_claim(
        "FINAL_STATUS: RESOLVED\nVALIDATION_EVIDENCE: ran pytest -k enums, 17 passed"
    )
    assert claim.has_evidence
    assert "17 passed" in claim.evidence


def test_multiline_evidence_is_captured():
    claim = parse_claim(
        "FINAL_STATUS: RESOLVED\n"
        "VALIDATION_EVIDENCE: ran the suite\nthen re-ran the failing test\nboth green"
    )
    assert "both green" in claim.evidence


def test_repeated_agreeing_markers_are_accepted():
    """Models often restate their answer; agreement is not ambiguity."""
    claim = parse_claim("FINAL_STATUS: RESOLVED\n...\nFINAL_STATUS: RESOLVED")
    assert claim.status is ClaimStatus.RESOLVED


# --- missing ---------------------------------------------------------------


@pytest.mark.parametrize("text", ["", "   \n\t ", None])
def test_empty_output_is_unparseable(text):
    claim = parse_claim(text)
    assert claim.status is ClaimStatus.UNPARSEABLE
    assert claim.reason is UnparseableReason.EMPTY_OUTPUT


def test_no_marker_is_unparseable():
    claim = parse_claim("I fixed the bug and ran the tests. Everything works now.")
    assert claim.status is ClaimStatus.UNPARSEABLE
    assert claim.reason is UnparseableReason.MISSING


def test_evidence_without_status_is_unparseable():
    claim = parse_claim("VALIDATION_EVIDENCE: ran the suite, all green")
    assert claim.status is ClaimStatus.UNPARSEABLE
    assert claim.reason is UnparseableReason.MISSING
    # The evidence is still captured, so the failure can be triaged.
    assert claim.has_evidence


# --- malformed -------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "FINAL_STATUS: MAYBE",
        "FINAL_STATUS: DONE",
        "FINAL_STATUS: SUCCESS",
        "FINAL_STATUS: PARTIALLY_RESOLVED",
        "FINAL_STATUS: TRUE",
    ],
)
def test_invalid_status_value_is_unparseable(text):
    claim = parse_claim(text)
    assert claim.status is ClaimStatus.UNPARSEABLE
    assert claim.reason is UnparseableReason.INVALID_VALUE


def test_conflicting_statuses_are_unparseable():
    """Ambiguity must not be resolved by taking the last marker."""
    claim = parse_claim(
        "FINAL_STATUS: RESOLVED\nOn reflection...\nFINAL_STATUS: UNRESOLVED"
    )
    assert claim.status is ClaimStatus.UNPARSEABLE
    assert claim.reason is UnparseableReason.AMBIGUOUS
    assert claim.raw_status_tokens == ("RESOLVED", "UNRESOLVED")


def test_status_missing_entirely_from_a_long_trajectory():
    claim = parse_claim("step 1\n" * 500)
    assert claim.status is ClaimStatus.UNPARSEABLE
    assert claim.reason is UnparseableReason.MISSING


# --- adversarial -----------------------------------------------------------

ADVERSARIAL = [
    "I think it's resolved.",
    "The issue appears to be resolved now.",
    "RESOLVED",
    "Status: resolved",
    "final status: resolved",           # missing the underscore in the key
    "I would say FINAL STATUS is RESOLVED",  # marker not in required form
    "The task is complete. Resolved!",
    "My final status? Resolved, I believe.",
]


@pytest.mark.parametrize("text", ADVERSARIAL)
def test_prose_agreement_is_not_a_claim(text):
    claim = parse_claim(text)
    assert claim.status is ClaimStatus.UNPARSEABLE, f"prose accepted as a claim: {text!r}"


def test_never_silently_defaults_to_unresolved():
    """The failure mode this guards against, stated as a test."""
    for text in ADVERSARIAL + ["", "no claim here"]:
        assert parse_claim(text).status is not ClaimStatus.UNRESOLVED


def test_discussing_the_format_without_claiming_is_still_read_as_a_claim():
    """A known limitation, pinned so a future change is a deliberate one.

    An agent that writes out the required format while explaining itself does
    emit the marker, and the parser takes it at face value. Distinguishing
    mention from use would need the agent's final message only, which is what
    the runner passes; this test documents the boundary.
    """
    claim = parse_claim("I should end with FINAL_STATUS: RESOLVED when I am done.")
    assert claim.status is ClaimStatus.RESOLVED


# --- structural ------------------------------------------------------------


def test_parse_claim_never_raises():
    for text in ["", None, "\x00\x01", "FINAL_STATUS:", "FINAL_STATUS: " * 1000]:
        assert parse_claim(text) is not None


def test_claim_is_immutable():
    claim = parse_claim("FINAL_STATUS: RESOLVED")
    with pytest.raises(dataclasses.FrozenInstanceError):
        claim.status = ClaimStatus.UNRESOLVED  # type: ignore[misc]


def test_status_serialises_as_its_name():
    assert ClaimStatus.RESOLVED.value == "RESOLVED"
    assert ClaimStatus.UNPARSEABLE.value == "UNPARSEABLE"
