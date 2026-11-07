"""Map collected instances back to the unchanged selected-family slots."""

from dataclasses import replace

from reliability.verifier.regression import RunResult, TestResult, TestStatus

# Missing one expansion member must dominate healthy members in its original slot.
_SEVERITY = {
    TestStatus.SKIPPED: 0,
    TestStatus.XFAIL: 1,
    TestStatus.PASSED: 2,
    TestStatus.XPASS: 3,
    TestStatus.FAILED: 4,
    TestStatus.ERROR: 5,
    TestStatus.NOT_RUN: 6,
    TestStatus.TIMEOUT: 7,
}


def apply_validation(run: RunResult, validation):
    owners = {}
    for record in validation.records:
        if record.valid:
            for identity in record.runnable_ids:
                owners.setdefault(identity, []).append(record.selected_id)
    by_id = run.by_id()
    results, receipts = [], []
    for record in validation.records:
        receipt = record.to_dict()
        receipts.append(receipt)
        receipt["admitted"] = False
        receipt["admitted_instances"] = 0
        if record.reason:
            results.append(
                TestResult(
                    record.selected_id,
                    TestStatus.NOT_RUN if record.unavailable else TestStatus.INVALID_ID,
                    message=record.reason + ": " + record.message,
                )
            )
            continue
        statuses = [
            by_id.get(tid, TestResult(tid, TestStatus.NOT_RUN)).status
            for tid in record.runnable_ids
        ]
        gaps = (TestStatus.NOT_RUN, TestStatus.TIMEOUT, TestStatus.ERROR, TestStatus.INVALID_ID)
        receipt["admitted_instances"] = sum(s not in gaps for s in statuses)
        receipt["admitted"] = bool(statuses) and all(s not in gaps for s in statuses)
        status = max(statuses, key=_SEVERITY.get) if statuses else TestStatus.NOT_RUN
        results.append(TestResult(record.selected_id, status))
    mappings = {}
    for raw, identities in run.raw_id_map.items():
        mappings[raw] = tuple(
            dict.fromkeys(owner for tid in identities for owner in owners.get(tid, ()))
        )
    summary = validation.to_dict()
    summary.pop('records')
    return replace(
        run,
        raw_execution_map={raw: ids[0] for raw, ids in run.raw_id_map.items() if len(ids) == 1},
        validation_summary=summary,
        evidence_files={**run.evidence_files, **validation.evidence_files},
        evidence_sha256={**run.evidence_sha256, **validation.evidence_sha256},
        results=tuple(results),
        raw_id_map=mappings,
        requested_tests=tuple(r.selected_id for r in validation.records),
        validation=tuple(receipts),
        execution_results=run.results,
        execution_id_map={k: tuple(v) for k, v in owners.items()},
    )
