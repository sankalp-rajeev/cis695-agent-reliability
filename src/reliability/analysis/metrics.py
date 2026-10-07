"""Study metrics from records already on disk. No model calls.

Denominators follow docs/VERIFIER_POLICY.md §8 and the formulas in the
technical design §15. Infrastructure exclusions and empty patches leave
FAR_verifier and Coverage. A V4 signal of NOT_AVAILABLE does not: it stays
in the coverage denominator.
"""

from __future__ import annotations

from pathlib import Path

from reliability.agent.claim_parser import ClaimStatus
from reliability.agent.records import RepairRecord, load_records
from reliability.oracle.records import OracleOutcome, load_records as load_oracle
from reliability.verifier.decision import SignalOutcome
from reliability.verifier.record import load_records as load_verification


def _index(records):
    return {record.instance_id: record for record in records}


def is_empty_patch(repair: RepairRecord | None, oracle) -> bool:
    if oracle is not None and oracle.outcome is OracleOutcome.EMPTY_PATCH:
        return True
    return repair is not None and repair.patch.size_bytes == 0


def is_infra(oracle) -> bool:
    return oracle is not None and (
        oracle.infrastructure_error or oracle.outcome is OracleOutcome.INFRA_ERROR
    )


def compute_metrics(run_root: Path) -> dict:
    """FSR_agent, FAR_verifier, and coverage for one run directory."""
    run_root = Path(run_root)
    repairs = _index(load_records(run_root))
    verifications = _index(load_verification(run_root, config="full"))
    oracles = _index(load_oracle(run_root))
    ids = sorted(set(repairs) | set(verifications) | set(oracles))

    rows = []
    for instance_id in ids:
        repair = repairs.get(instance_id)
        verification = verifications.get(instance_id)
        oracle = oracles.get(instance_id)
        reproduction = None
        decision = None
        if verification is not None:
            decision = verification.decision.decision.value
            reproduction = verification.reproduction.outcome.value
        empty = is_empty_patch(repair, oracle)
        infra = is_infra(oracle)
        # Valid for FAR and coverage: a real patch with an oracle verdict
        # that is about the patch. V4 NOT_AVAILABLE stays in.
        valid = (
            not empty
            and not infra
            and oracle is not None
            and oracle.outcome in {OracleOutcome.RESOLVED, OracleOutcome.UNRESOLVED}
            and decision is not None
        )
        claim = repair.claim.status.value if repair is not None else None
        rows.append({
            "instance_id": instance_id,
            "claim": claim,
            "decision": decision,
            "reproduction": reproduction,
            "oracle": oracle.outcome.value if oracle is not None else None,
            "empty": empty,
            "infra": infra,
            "valid": valid,
            "resolved_claim": claim == ClaimStatus.RESOLVED.value,
            "accept": decision == "ACCEPT",
            "oracle_unresolved": (
                oracle is not None and oracle.outcome is OracleOutcome.UNRESOLVED
            ),
        })

    valid_rows = [row for row in rows if row["valid"]]
    accepts = [row for row in valid_rows if row["accept"]]
    false_accepts = [row for row in accepts if row["oracle_unresolved"]]
    # FSR uses claims of RESOLVED that have a patch-level oracle verdict.
    claimed = [
        row for row in rows
        if row["resolved_claim"] and not row["empty"] and not row["infra"]
        and row["oracle"] in {OracleOutcome.RESOLVED.value, OracleOutcome.UNRESOLVED.value}
    ]
    false_claims = [row for row in claimed if row["oracle_unresolved"]]
    v4_na = [
        row for row in valid_rows
        if row["reproduction"] == SignalOutcome.NOT_AVAILABLE.value
    ]

    def rate(num: int, den: int):
        return None if den == 0 else round(num / den, 4)

    return {
        "n": len(rows),
        "n_valid": len(valid_rows),
        "n_empty": sum(1 for row in rows if row["empty"]),
        "n_infra": sum(1 for row in rows if row["infra"]),
        "n_v4_not_available_in_coverage": len(v4_na),
        "fsr_agent": {
            "numerator": len(false_claims),
            "denominator": len(claimed),
            "rate": rate(len(false_claims), len(claimed)),
        },
        "far_verifier": {
            "numerator": len(false_accepts),
            "denominator": len(accepts),
            "rate": rate(len(false_accepts), len(accepts)),
        },
        "coverage": {
            "numerator": len(accepts),
            "denominator": len(valid_rows),
            "rate": rate(len(accepts), len(valid_rows)),
        },
        "rows": rows,
    }
