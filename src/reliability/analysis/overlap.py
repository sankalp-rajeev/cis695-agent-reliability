"""Phase 5.3: overlap between the verifier's selected tests and PASS_TO_PASS.

Computed after the fact from stored records. Selection never saw these names;
this module is the only point at which the two sets are allowed to meet, and
only once both are already fixed on disk.
"""

from __future__ import annotations

from reliability.oracle.records import OracleRecord
from reliability.verifier.record import VerificationRecord


def names_match(selected: str, oracle_name: str) -> bool:
    """A selected test and a PASS_TO_PASS entry refer to the same test.

    SWE-bench stores short names (`test_foo`) in some repos and node ids
    (`tests/test_mod.py::test_foo`) in others. Selection produces node ids.
    Equality is exact; failing that, either string ending with the other after
    stripping a `::` suffix is accepted so `test_foo` matches
    `tests/test_mod.py::test_foo` without matching `test_foobar`.
    """
    if selected == oracle_name:
        return True
    sel_tail = selected.rsplit("::", 1)[-1]
    ora_tail = oracle_name.rsplit("::", 1)[-1]
    return bool(sel_tail) and sel_tail == ora_tail


def overlap(
    selected: tuple[str, ...],
    pass_to_pass: tuple[str, ...],
) -> dict:
    """Set comparison, plus the fraction of each side that the other covers."""
    matched_selected = tuple(
        s for s in selected if any(names_match(s, p) for p in pass_to_pass)
    )
    matched_p2p = tuple(
        p for p in pass_to_pass if any(names_match(s, p) for s in selected)
    )
    n_sel, n_p2p = len(selected), len(pass_to_pass)
    return {
        "n_selected": n_sel,
        "n_pass_to_pass": n_p2p,
        "n_overlap_selected": len(matched_selected),
        "n_overlap_pass_to_pass": len(matched_p2p),
        "fraction_of_selected": (
            round(len(matched_selected) / n_sel, 4) if n_sel else None),
        "fraction_of_pass_to_pass": (
            round(len(matched_p2p) / n_p2p, 4) if n_p2p else None),
        "matched_selected": list(matched_selected),
        "unmatched_selected": [s for s in selected if s not in matched_selected],
    }


def overlap_from_records(
    verification: VerificationRecord, oracle: OracleRecord
) -> dict:
    p2p = oracle.pass_to_pass.success + oracle.pass_to_pass.failure
    result = overlap(verification.selected_tests, p2p)
    result["instance_id"] = verification.instance_id
    return result
