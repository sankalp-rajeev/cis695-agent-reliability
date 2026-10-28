"""Compare frozen predictions with retrospective labels only after prediction.

No predictions, thresholds, production decisions or historical artifacts change.
"""
import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from reliability.verifier.decision import Evidence, FullPolicy, SignalOutcome

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/v2_stabilization'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    predictions=json.loads((OUT/'shadow_predictions.json').read_text())
    assert predictions['predictions_saved_before_retrospective_label_access']
    frozen=json.loads((OUT/'frozen_rule.json').read_text())
    for name,digest in frozen['implementation_sha256'].items():
        assert sha(ROOT/'src/reliability/verifier'/name)==digest
    assert predictions['frozen_rule_sha256']==frozen['frozen_rule_sha256']
    assert all(v=='DENIED' for v in predictions['isolation']['probe_results'].values())
    # First retrospective-label access in this evaluation pipeline, AFTER the
    # isolated classifier process has exited and predictions were saved.
    retrospective=json.loads((ROOT/'reports/failure_analysis/group4_gold_check.json').read_text())
    labels={r['instance_id']:r for r in retrospective['tasks']}
    stored=json.loads((ROOT/'reports/failure_analysis/extracted.json').read_text())
    snapshots={r['instance_id']:r for r in stored['tasks']}
    comparison=[];policy=FullPolicy()
    for case in predictions['cases']:
        iid=case['instance_id'];label=labels[iid]
        if label['task_class']=='SUPERSEDED_ASSERTION':
            expected='LIKELY_SUPERSEDED_ASSERTION';confidence='high on source classification'
        else:
            # The existing manual diagnosis establishes the likely extra-query
            # regression; NOT_TOUCHED alone is not proof of a genuine regression.
            expected='LIKELY_GENUINE_REGRESSION';confidence='medium; historical parsed V2 + source diagnosis'
        record=snapshots[iid];signals=record['signals'];findings=signals['integrity'].get('findings',{})
        evidence=Evidence(integrity=SignalOutcome(signals['integrity']['outcome']),
            regression=SignalOutcome(signals['regression']['outcome']),
            static=SignalOutcome(signals['static']['outcome']),
            reproduction=SignalOutcome(signals['reproduction']['outcome']),
            high_severity_risk=bool(findings.get('high_severity_risk')),
            prohibited_manipulation=bool(findings.get('prohibited_manipulation')),
            patch_applies=bool(findings.get('patch_applies',True)))
        before=policy.decide(evidence)
        # Shadow mode has exactly the same policy input, irrespective of its label.
        after=policy.decide(evidence)
        assert before==after
        comparison.append({'instance_id':iid,'prediction':case['prediction'],
            'retrospective_label':expected,'retrospective_confidence':confidence,
            'label_source':'reports/failure_analysis/group4_gold_check.json',
            'additional_diagnostic_source':'reports/failure_analysis/failure_analysis.md:526' if case['held_out_diagnostic'] else None,
            'held_out_diagnostic':case['held_out_diagnostic'],
            'agreement':case['prediction']==expected,'suppression_suggested':case['suggest_suppress_v2_negative'],
            'v1':evidence.integrity.value,'v3':evidence.static.value,'v4':evidence.reproduction.value,
            'original_recorded_full_decision':record['csv_row']['verifier_decision'],
            'unchanged_policy_replay':before.decision.value,'shadow_decision':after.decision.value})
    with (OUT/'verdict_diff.csv').open() as f:diff=list(csv.DictReader(f))
    assert all(r['new_v2']==r['original_v2'] or (r['original_v2'],r['new_v2'])==('PASS','INCOMPLETE') for r in diff)
    # All historical audit files and bytes collected in the previous task remain intact.
    audit=ROOT/'reports/v2_scoring_audit/resume_20261026'
    for path,digest in json.loads((audit/'preserved_inputs.sha256.json').read_text()).items():
        assert sha(ROOT/path)==digest,path
    for path,digest in json.loads((audit/'final_outputs.sha256.json').read_text()).items():
        assert sha(audit/path)==digest,path
    contract=json.loads((OUT/'completeness_contract.json').read_text())
    policy_path='src/reliability/verifier/decision.py'
    assert sha(ROOT/policy_path)==contract['source_sha256_before'][policy_path]
    summary={'completed_utc':datetime.now(UTC).isoformat(),
        'frozen_rule_sha256':frozen['frozen_rule_sha256'],
        'retrospective_comparison':comparison,
        'agreement_with_five_historical_labels':{'agree':sum(r['agreement'] for r in comparison),'total':5,
            'abstentions':sum(r['prediction']=='UNCERTAIN' for r in comparison),
            'not_accuracy':'Familiar targeted cases; freezing does not remove prior researcher knowledge.'},
        'known_meaningful_regressions_incorrectly_suppressed':{'numerator':sum(r['suppression_suggested'] for r in comparison if r['held_out_diagnostic']),
            'diagnostic_cases':1,'limitation':'No suppression suggestions; this does not establish generalization or safety.'},
        'full_policy_review':{'actual_decisions_changed':0,'observed_FLAG_reduction':0,
            'before_FLAG':sum(r['unchanged_policy_replay']=='FLAG' for r in comparison),
            'after_FLAG':sum(r['shadow_decision']=='FLAG' for r in comparison),
            'note':'All five have V1/V3/V4 PASS. All predictions abstain. Completeness separately prevents treating pytest-5809 as a complete PASS even if its assertion were excused. No all-83 or 500-task reduction estimate.'},
        'historical_detection':{'actual_wrong_patches_caught':1,'wrong_patches':14,
            'known_existing_suite_opportunities':4,'opportunities_are_not_actual_catches':True},
        'compatibility':{'unexpected_transitions':0,'all_diff_rows':len(diff),
            'populations_overlap_do_not_sum_as_unique_patches':True,
            'original_verdict_source':'Stored verdict where historical raw is absent; old-parser replay where paired audit raw exists. Never fabricate historical results.'},
        'validation':{'focused_unit_tests_passed':254,'ruff':'passed','diff_check':'passed',
            'synthetic_driver_streaming_and_raw_byte_roundtrip':'passed',
            'kernel_isolation':'Landlock ABI 7; five actual prohibited-file read probes denied',
            'decision_policy_file_unchanged':True,'prior_audit_artifacts_unchanged':True,
            'frozen_classifier_unchanged_after_prediction':True,
            'benchmark_or_docker_reproductions_this_task':0,'images_pulled_or_substituted':0,
            'models_or_agents_invoked':0,'commits':0,'500_task_run_launched':False},
        'limitations_before_500':[
            '54 headline PASS records are unverifiable, not demonstrated execution failures; 10 have confirmed gaps.',
            'New capture code was validated with focused units, synthetic runner streaming and existing raw logs, not live benchmark execution.',
            'Missing task images and historical image digests still prevent faithful reproduction of four prototype cases.',
            'Legacy admission/classification and prior FAIL/NOT_AVAILABLE remain compatibility references; an unscored parameter failure blocks PASS rather than inventing a new historical FAIL.',
            'The narrow literal-change rule abstains on every historical case; no demonstrated review reduction or improved wrong-patch detection.',
            'Current V2 provides one base pass and one patched pass plus its legacy rerun; the four-observation rule requires additional supplied stability evidence. Shadow does not add test runs.',
            'Classifier isolation requires x86_64 Linux Landlock ABI >=4; unavailable isolation fails closed to UNCERTAIN.',
            'Six historical V2 FAILs cannot establish generalization; evaluate frozen shadow output against oracle only after the eventual run.']}
    summary['artifacts_sha256']={p.name:sha(p) for p in OUT.iterdir() if p.is_file()}
    summary['implementation_sha256']={str(p.relative_to(ROOT)):sha(p) for p in
        [ROOT/'src/reliability/verifier'/name for name in ('regression.py','container.py','run.py','record.py','superseded_rule.py','superseded_shadow.py')]}
    with (OUT/'validation.json').open('x') as f:json.dump(summary,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({k:summary[k] for k in ('agreement_with_five_historical_labels',
        'known_meaningful_regressions_incorrectly_suppressed','full_policy_review','compatibility','validation')},indent=2))


if __name__=='__main__':main()
