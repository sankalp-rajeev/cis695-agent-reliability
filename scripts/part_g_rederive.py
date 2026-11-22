#!/usr/bin/env python3
"""Part G step 6 (amendment B9): sealed records under the new classification. Label-free.

    part_g_rederive.py [--workers N]

For each dev gold record (Phase 6, with pytest-7236/7521 from the part F rerun) and each
completed task of the stopped Phase 7 run, recompute V1-V4 outcomes and flags as part G
would record them:
  * step 1: V1 runs the container's own `git apply --check` (in the task's verified
    container: the one check that needs Docker). A rejected patch fails V1, V2/V3 become
    PATCH_DOES_NOT_APPLY (not infrastructure) and V4 has nothing to check;
  * step 2: a stored run-health block gets its attribution from the stored G1 health;
  * step 3: a G1 block that A7 would now exclude means V2 must rerun (outcome unknown).
Gold decisions are recomputed (v1.4.1, v1.5 switches off, all on). Arm B gets outcomes
and flags only. No labels are read, no patch content is printed, sealed runs are only read.
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reliability.verifier.record import SignalAbsence, SignalKind, SignalRecord  # noqa: E402
from reliability.verifier.run_v1_4_1 import g1_attribution, paired_collection_exclusions  # noqa: E402
from reliability.verifier.decision import SignalOutcome  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
KINDS = (('V1', SignalKind.INTEGRITY), ('V2', SignalKind.REGRESSION), ('V3', SignalKind.STATIC),
         ('V4', SignalKind.REPRODUCTION))
GOLD, GOLD_F = ROOT / 'runs/study_dev_gold', ROOT / 'runs/study_dev_gold_f'
GOLD_F_IDS = ('pytest-dev__pytest-7236', 'pytest-dev__pytest-7521')
ARMB = ROOT / 'runs/study_dev_armb'
SPECS = (ROOT / 'configs/e2e/task_specs_83.json', ROOT / 'configs/e2e/task_specs_add9_e2e_v141.json')
WORK = ROOT / 'runs/study_v1_5/part_g_rederive'
OUT = ROOT / 'reports/study_v1_5/build'


def _absent(kind, reason, absence=SignalAbsence.ERROR):
    record = SignalRecord.absent(kind, absence, reason)
    record.findings.update(absence_reason=reason, infrastructure=False)
    return record


def rederive(signals, *, g1, after, applies, selected):
    """New signals for one stored task. `g1`/`after`: stored G1 health rows (scope G1 and
    G1_after_paired_exclusion); `applies`: the container apply check; `selected`: tests."""
    new = {kind: signal.model_copy(deep=True) for kind, signal in signals.items()}
    notes, rerun = [], False
    v1, v2, v3 = new[SignalKind.INTEGRITY], new[SignalKind.REGRESSION], new[SignalKind.STATIC]
    reason = lambda s: s.findings.get('absence_reason') or ''  # noqa: E731
    if applies is False:
        violations = list(v1.findings.get('violations', []))
        if 'does_not_apply' not in violations:
            violations.append('does_not_apply')
        v1.findings.update(violations=violations, patch_applies=False, apply_check='FAIL')
        new[SignalKind.INTEGRITY] = v1.model_copy(update={'outcome': SignalOutcome.FAIL})
        # A selection exists unless V2 was absent for want of one (absence error NO_SELECTION).
        no_selection = v2.absence is SignalAbsence.ERROR and reason(v2) == 'NO_SELECTION'
        if not no_selection and reason(v2) != 'EMPTY_PATCH':
            new[SignalKind.REGRESSION] = _absent(SignalKind.REGRESSION, 'PATCH_DOES_NOT_APPLY')
        if reason(v3) not in ('NO_PARSEABLE_PATCH', 'EMPTY_PATCH'):
            new[SignalKind.STATIC] = _absent(SignalKind.STATIC, 'PATCH_DOES_NOT_APPLY')
        new[SignalKind.REPRODUCTION] = SignalRecord.absent(
            SignalKind.REPRODUCTION, SignalAbsence.NOTHING_TO_CHECK, 'no task spec or patch does not apply')
        return {'signals': new, 'notes': ['patch does not apply in the container'], 'v2_rerun_needed': False}
    if applies is True:
        v1.findings['apply_check'] = 'PASS'
    if reason(v2).startswith('RUN_HEALTH_G1') and g1:
        paired = None if after else paired_collection_exclusions(g1)
        modules = {entry['module'] for entry in paired or ()}
        if paired and any(t.split('::', 1)[0] not in modules for t in selected):
            rerun = True
            notes.append('A7 now excludes ' + ', '.join(sorted(modules)))
        else:
            attribution = g1_attribution(after or g1)
            v2.findings.update(attribution=attribution, infrastructure=attribution == 'infrastructure')
    return {'signals': new, 'notes': notes, 'v2_rerun_needed': rerun}


def _view(signal):
    return {'outcome': signal.outcome.value, 'absence': signal.absence.value if signal.absence else None,
            'reason': signal.findings.get('absence_reason'), 'infrastructure': signal.findings.get('infrastructure')}


def compare(old, new):
    changes = []
    for name, kind in KINDS:
        a, b = _view(old[kind]), _view(new[kind])
        for field in ('outcome', 'absence', 'reason', 'infrastructure'):
            if a[field] != b[field]:
                label = '' if field == 'outcome' else field + ' '
                changes.append(f'{name} {label}{a[field]} -> {b[field]}')
    return changes


def task_infrastructure(signals):
    return any(signals[k].outcome is SignalOutcome.NOT_AVAILABLE and signals[k].findings.get('infrastructure', False)
               for k in (SignalKind.REGRESSION, SignalKind.STATIC))


def apply_job(job):
    """Container apply check for one sealed patch (worker process)."""
    from reliability.verifier.run_v1_4_1 import container_apply_check
    from reliability.verifier.task_specs import load_registries
    group, iid, patch_path = job
    tasks, _ = load_registries(list(SPECS))
    text = Path(patch_path).read_bytes().decode('utf-8')
    if not text.strip():
        return group, iid, None, 'empty patch'
    folder = WORK / group / iid
    folder.mkdir(parents=True, exist_ok=True)
    try:
        applies, _, command = container_apply_check(tasks[iid], text, folder, 'part_g_rederive')
        return group, iid, applies, command
    except Exception as exc:  # noqa: BLE001
        return group, iid, None, type(exc).__name__


def load(run, iid):
    import decide_v1_5 as dv
    from reliability.verifier.run_v1_4_1 import VerificationRecordV141
    files, _ = dv.check_sealed(run, require_complete=False)
    record = VerificationRecordV141.model_validate_json(dv._read(run, files, f'tasks/{iid}/verification_record.full-v1.4.1.json'))
    rows = []
    name = f'tasks/{iid}/verification/health.jsonl'
    if name in files:
        rows = [json.loads(line) for line in dv._read(run, files, name).decode().splitlines() if line.strip()]
    g1 = [r for r in rows if r.get('scope') == 'G1']
    after = [r for r in rows if r.get('scope') == 'G1_after_paired_exclusion']
    return record, g1[-2:] or None, after[-2:] or None, dv.added_paths(run, files, iid)


def decisions(signals, added):
    from reliability.verifier.policy_v1_4 import evidence_from_signals as ev14
    from reliability.verifier.policy_v1_4_1 import FullPolicyV141
    from reliability.verifier.policy_v1_5 import FullPolicyV15, evidence_from_signals as ev15
    off = dict(r2_v3_reject=False, r3_extended_reject=False, r6_accept_v2_not_available=False,
               r6b_accept_one_uncovered=False)
    on = {k: True for k in off}
    out = {'v1.4.1': FullPolicyV141().decide(ev14(signals))}
    for name, switches in (('v1.5 off', off), ('v1.5 all on', on)):
        out[name] = FullPolicyV15(**switches).decide(ev15(signals, added_paths=added))
    return {k: f'{r.decision.value}/{r.rule_id}' if hasattr(r, 'rule_id') else r.decision.value for k, r in out.items()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--workers', type=int, default=6)
    args = parser.parse_args(argv)
    ids = json.loads((ROOT / 'reports/study_v1_5/pilot/dev_reference_ids.json').read_text())
    gold_runs = {iid: (GOLD_F if iid in GOLD_F_IDS else GOLD) for iid in ids}
    armb_done = json.loads((ARMB / 'completion.json').read_text())['completed_tasks']
    jobs = [('gold', iid, str(gold_runs[iid] / 'tasks' / iid / 'patch.diff')) for iid in ids]
    jobs += [('armb', iid, str(ARMB / 'tasks' / iid / 'patch.diff')) for iid in armb_done]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        applied = {(g, i): (a, e) for g, i, a, e in pool.map(apply_job, jobs)}
    result = {'gold': {}, 'armb': {}}
    for group, run_of, group_ids in (('gold', gold_runs, ids), ('armb', {i: ARMB for i in armb_done}, armb_done)):
        for iid in group_ids:
            record, g1, after, added = load(run_of[iid], iid)
            applies, error = applied[(group, iid)]
            out = rederive(record.signals, g1=g1, after=after, applies=applies, selected=record.selected_tests)
            row = {'run': str(run_of[iid].relative_to(ROOT)), 'apply_check': 'PASS' if applies else 'FAIL'
                   if applies is False else 'UNAVAILABLE:' + str(error), 'old': {n: _view(record.signals[k]) for n, k in KINDS},
                   'new': {n: _view(out['signals'][k]) for n, k in KINDS},
                   'old_task_infrastructure': task_infrastructure(record.signals),
                   'new_task_infrastructure': None if out['v2_rerun_needed'] else task_infrastructure(out['signals']),
                   'attribution': out['signals'][SignalKind.REGRESSION].findings.get('attribution'),
                   'changes': compare(record.signals, out['signals']), 'notes': out['notes'],
                   'v2_rerun_needed': out['v2_rerun_needed']}
            if out['v2_rerun_needed']:
                row['changes'].append('V2 must rerun (outcome not derivable from stored signals)')
            if group == 'gold':
                row['old_decisions'] = decisions(record.signals, added)
                row['new_decisions'] = None if out['v2_rerun_needed'] else decisions(out['signals'], added)
            result[group][iid] = row
    (OUT / 'part_g_rederive.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    for group in ('gold', 'armb'):
        changed = {i: r for i, r in result[group].items() if r['changes']
                   or r.get('old_decisions') != r.get('new_decisions')}
        print(json.dumps({'group': group, 'tasks': len(result[group]), 'changed': sorted(changed),
                          'apply_unavailable': sorted(i for i, r in result[group].items()
                                                      if r['apply_check'].startswith('UNAVAILABLE'))}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
