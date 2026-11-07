"""Primary slot accounting and the explicitly secondary INVALID_ID sensitivity."""

from reliability.verifier.regression import TestStatus

ADMITTED_STATUSES = frozenset(
    {TestStatus.PASSED, TestStatus.FAILED, TestStatus.SKIPPED, TestStatus.XFAIL, TestStatus.XPASS}
)


def h1_accounting(b1_slots, admitted_slots, invalid_slots):
    """Count original selected tree slots once; INVALID_ID can never be admitted."""
    b1 = set(b1_slots)
    invalid = b1 & set(invalid_slots)
    admitted = (b1 & set(admitted_slots)) - invalid
    secondary = len(b1 - invalid)
    return {
        "primary_B1": len(b1),
        "admitted_original_slots": len(admitted),
        "INVALID_ID_in_B1": len(invalid),
        "primary_H1_fraction": len(admitted) / len(b1) if b1 else None,
        "secondary_label": "INFORMATIONAL SECONDARY: INVALID_ID removed from B1",
        "secondary_denominator": secondary,
        "secondary_H1_fraction": len(admitted) / secondary if secondary else None,
    }
