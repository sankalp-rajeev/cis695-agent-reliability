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
    TestStatus.CRASH: 5.5,
    TestStatus.NOT_RUN: 6,
    TestStatus.NOT_REACHED: 6.5,
    TestStatus.TIMEOUT: 7,
    TestStatus.COLLECTION_ERROR: 8,
    TestStatus.RUNNER_UNAVAILABLE: 9,
}


def apply_validation(run: RunResult, validation):
    owners = {}
    for record in validation.records:
        if record.valid:
            for identity in record.runnable_ids:
                owners.setdefault(identity, []).append(record.selected_id)
    by_id = run.by_id()
    module_skips = {tid: reason for record in validation.records if record.valid
                    for tid,reason in record.module_skip_instances}
    skip_results = tuple(TestResult(tid,TestStatus.SKIPPED,message='module_skip: '+reason)
                         for tid,reason in module_skips.items())
    by_id.update({r.test_id:r for r in skip_results})
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
                    TestStatus(record.failure_status.lower())
                    if record.unavailable and record.failure_status
                    else TestStatus.COLLECTION_ERROR
                    if record.unavailable
                    else TestStatus.INVALID_ID,
                    message=record.reason + ": " + record.message,
                    elapsed_s=record.elapsed_s,
                )
            )
            continue
        statuses = [
            by_id.get(tid, TestResult(tid, TestStatus.NOT_RUN)).status
            for tid in record.runnable_ids
        ]
        gaps = (
            TestStatus.NOT_RUN,
            TestStatus.NOT_REACHED,
            TestStatus.TIMEOUT,
            TestStatus.ERROR,
            TestStatus.CRASH,
            TestStatus.INVALID_ID,
            TestStatus.COLLECTION_ERROR,
            TestStatus.RUNNER_UNAVAILABLE,
        )
        terminal_instances = sum(s not in gaps for s in statuses)
        receipt['fallback_terminal_instances'] = terminal_instances if record.collector_fallback else 0
        receipt["admitted_instances"] = terminal_instances if not record.collector_fallback else 0
        receipt["admitted"] = not record.collector_fallback and bool(statuses) and all(s not in gaps for s in statuses)
        status = max(statuses, key=_SEVERITY.get) if statuses else TestStatus.NOT_RUN
        results.append(TestResult(record.selected_id, status,
                                  message='module_skip: '+record.module_skip_reason if record.module_skip_reason else '',
                                  elapsed_s=max((by_id[t].elapsed_s for t in record.runnable_ids if t in by_id), default=0.0)))
    mappings = {}
    for raw, identities in run.raw_id_map.items():
        mappings[raw] = tuple(
            dict.fromkeys(owner for tid in identities for owner in owners.get(tid, ()))
        )
    mappings.update({tid:tuple(dict.fromkeys(owners.get(tid, ()))) for tid in module_skips})
    summary = validation.to_dict()
    summary.pop("records")
    return replace(
        run,
        raw_execution_map={raw: ids[0] for raw, ids in run.raw_id_map.items() if len(ids) == 1},
        validation_summary=summary,
        evidence_files={**run.evidence_files, **validation.evidence_files},
        evidence_sha256={**run.evidence_sha256, **validation.evidence_sha256},
        results=tuple(results),
        raw_results=run.raw_results+skip_results,
        raw_id_map=mappings,
        requested_tests=tuple(r.selected_id for r in validation.records),
        validation=tuple(receipts),
        execution_results=run.results+skip_results,
        execution_id_map={k: tuple(v) for k, v in owners.items()},
    )
