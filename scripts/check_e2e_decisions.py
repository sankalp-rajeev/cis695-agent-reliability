#!/usr/bin/env python3
"""A3: stored V1/V3/V4 evidence plus A2 V2, with explicit v1.4 rule deltas."""

import csv
import argparse
import json
from pathlib import Path
from collections import Counter

from reliability.env import assert_clean_interpreter
from reliability.verifier.archive_tree import ArchiveTree
from reliability.verifier.decision import Evidence, FullPolicy, SignalOutcome
from reliability.verifier.policy_v1_4 import EvidenceV14
from reliability.verifier.policy_v1_4_1 import FullPolicyV141
from reliability.verifier.run_v1_4_1 import integrity_signal
from reliability.verifier.task_specs import ROOT, load_registries, require_hash, write
from check_e2e_offline import FROZEN, frozen_tasks


def main():
    assert_clean_interpreter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', type=Path, default=ROOT / 'reports/next_phases/e2e_v1_4_1')
    parser.add_argument('--output', type=Path, default=ROOT / 'reports/next_phases/e2e_v1_4_1')
    args = parser.parse_args()
    report_dir = args.output
    report_dir.mkdir(parents=True, exist_ok=True)
    a2 = json.loads((args.offline / 'A2.json').read_text())
    if a2['status'] != 'PASS' or a2['matched'] != 83 or a2['health_halts']:
        raise ValueError('A3 requires passing sealed A2')
    inputs = {r['task']: r for r in json.loads((ROOT / 'reports/policy_v1_4/policy_inputs.json').read_text())}
    with (ROOT / 'reports/next_phases/phase7_signal_audit/recompute_sensitivity.csv').open() as stream:
        phase7 = {r['task']: r for r in csv.DictReader(stream) if r['phase4_policy'] == 'S_invalid_excluded'}
    specs, _ = load_registries([ROOT / 'configs/e2e/task_specs_83.json'])
    patches = {r['instance_id']: r for r in frozen_tasks()}
    rows, baseline_totals, totals, unattributed = [], Counter(), Counter(), []
    for task in a2['tasks']:
        iid = task['instance_id']
        stored = inputs[iid]
        values = {k: SignalOutcome(v) if k in ('integrity', 'regression', 'static', 'reproduction') else v
                  for k, v in stored['signals'].items()}
        signal = task['signal']
        values['regression'] = SignalOutcome.PASS if signal == 'PASS' else (
            SignalOutcome.FAIL if signal in ('FAIL', 'REGRESSION_ERROR') else SignalOutcome.NOT_AVAILABLE)
        baseline = FullPolicy().decide(Evidence(**values))
        if baseline.decision.value != phase7[iid]['new_decision']:
            raise ValueError('Phase 7 primary input mismatch: ' + iid)
        baseline_totals[baseline.decision.value] += 1
        path = FROZEN / patches[iid]['patch_path']
        require_hash(path, patches[iid]['patch_sha256'])
        with ArchiveTree(specs[iid].source.archive_path) as tree:
            fresh, v1 = integrity_signal(path.read_text(), tree)
        absolute = any(stored['summary'].get(k) == 'FAIL' for k in ('syntax', 'import'))
        incomplete = any(row['status'] != 'checked' for row in fresh.analysis)
        new_values = dict(values, integrity=v1.outcome,
            prohibited_manipulation=v1.findings['prohibited_manipulation'],
            high_severity_risk=v1.findings['high_severity_risk'])
        result = FullPolicyV141().decide(EvidenceV14(**new_values,
            v3_absolute_failure=absolute, v1_analysis_incomplete=incomplete))
        causes = []
        if result.decision != baseline.decision:
            v3_only = FullPolicyV141().decide(EvidenceV14(**values, v3_absolute_failure=absolute))
            v1_only = FullPolicyV141().decide(EvidenceV14(**new_values, v1_analysis_incomplete=incomplete))
            if v3_only.decision != baseline.decision:
                causes.append('V3_SYNTAX_IMPORT_GATE')
            if v1_only.decision != baseline.decision:
                causes.append('V1_AST_CHECK')
            if not causes:
                unattributed.append(iid)
        totals[result.decision.value] += 1
        rows.append({'instance_id': iid, 'phase7_S_invalid_excluded': baseline.decision.value,
            'v1_4_1': result.decision.value, 'causes': '|'.join(causes), 'V2': signal,
            'v3_absolute_failure': absolute, 'v1_analysis_incomplete': incomplete,
            'v1_stored': values['integrity'].value, 'v1_current': v1.outcome.value,
            'reasons': '|'.join(result.reasons)})
    if dict(baseline_totals) != {'ACCEPT': 14, 'FLAG': 67, 'REJECT': 2}:
        raise ValueError('Phase 7 primary totals differ')
    with (report_dir / 'decisions_83.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    report = {'A3': 'PASS' if not unattributed else 'FAIL', 'tasks': len(rows),
              'phase7_primary': dict(baseline_totals), 'v1_4_1': dict(totals),
              'differences': [r for r in rows if r['causes']], 'unattributed': unattributed,
              'V4': 'stored reproduction inputs reused; no telemetry or cost synthesized'}
    write(report_dir / 'A3.json', report)
    print(json.dumps(report, indent=2))
    if unattributed:
        raise ValueError('A3 has unattributed differences')


if __name__ == '__main__':
    main()
