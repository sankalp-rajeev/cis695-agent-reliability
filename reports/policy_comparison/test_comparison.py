"""Synthetic hand-computed fixtures only; no runs, verifier or oracle is rerun."""
import csv
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from statistics_core import (Confusion, confusion, wilson, populations, transitions,
    exact_mcnemar, enrichment_exact, paired_bootstrap, paired_exact)
from reconstruction import policy_results, reconstruct, explicit_high_risks
from compare import build_bundle


def make_rows():
    """45/7 concordant ACCEPTs; 8 right + 4 wrong stopped; 19 jointly withheld."""
    rows = []
    def add(n, oracle, baseline, full, stratum='headline', **signals):
        for _ in range(n):
            rows.append(dict(instance_id=f'synthetic-{len(rows)}', source_run='fixture', repo='synthetic/repo',
                stratum=stratum, oracle=oracle, baseline_decision=baseline, full_decision=full,
                V1='PASS', V2='PASS', V3='PASS', V4='PASS', high_severity_risk=None, **signals))
    add(45, 'resolved', 'ACCEPT', 'ACCEPT')
    rows[0]['instance_id'] = 'pytest-dev__pytest-7432'
    add(7, 'unresolved', 'ACCEPT', 'ACCEPT')
    add(8, 'resolved', 'ACCEPT', 'FLAG')
    add(4, 'unresolved', 'ACCEPT', 'FLAG')
    for row in rows[52:64]:
        row['V4'] = 'NOT_AVAILABLE'
    add(5, 'resolved', 'REJECT', 'FLAG')
    for row in rows[64:69]:
        row['V2'] = 'FAIL'
    add(11, 'resolved', 'FLAG', 'FLAG')
    add(2, 'unresolved', 'FLAG', 'FLAG')
    add(1, 'unresolved', 'REJECT', 'REJECT')
    add(2, 'resolved', 'ACCEPT', 'ACCEPT', 'requests')
    add(4, 'resolved', 'FLAG', 'FLAG', 'requests')
    add(10, 'empty_patch', 'REJECT', 'REJECT')
    add(1, 'empty_patch', 'REJECT', 'REJECT', 'requests')
    return rows


def test_requested_confusion_matrices_from_synthetic_pairs():
    primary = populations(make_rows())['HEADLINE_NONEMPTY_PRIMARY']
    assert len(primary) == 83
    assert confusion(primary, 'baseline') == Confusion(53, 11, 16, 3)
    assert confusion(primary, 'full') == Confusion(45, 7, 24, 7)


@pytest.mark.parametrize('cm,p,r,f1,acc,specificity,npv,balance,coverage,safety', [
    (Confusion(53,11,16,3),53/64,53/69,106/133,56/83,3/14,3/19,(53/69+3/14)/2,64/83,(3/19,3/14,6/33)),
    (Confusion(45,7,24,7),45/52,45/69,90/121,52/83,7/14,7/31,(45/69+7/14)/2,52/83,(7/31,7/14,14/45)),
])
def test_hand_computed_metrics(cm,p,r,f1,acc,specificity,npv,balance,coverage,safety):
    metrics = cm.metrics()
    expected = dict(precision=p,recall=r,f1=f1,accuracy=acc,specificity=specificity,
                    negative_predictive_value=npv,balanced_accuracy=balance,coverage=coverage)
    for name,value in expected.items():
        assert metrics[name] == pytest.approx(value, abs=1e-14)
    assert metrics['false_acceptance_proportion'] == pytest.approx(1-p)
    assert tuple(metrics['unsafe_detection_'+k] for k in ('precision','recall','f1')) == pytest.approx(safety)


def test_zero_denominators_are_missing_but_defined_zero_remains_zero():
    empty = Confusion(0,0,0,0).metrics()
    assert all(empty[k] is None for k in ('precision','recall','f1','accuracy','specificity','coverage','balanced_accuracy'))
    withheld = Confusion(0,0,2,0).metrics()
    assert withheld['precision'] is None and withheld['specificity'] is None
    assert withheld['recall'] == withheld['f1'] == withheld['accuracy'] == 0
    assert withheld['balanced_accuracy'] is None


def test_reference_wilson_interval_five_of_ten():
    # Reference values from the closed-form Wilson score formula with z=.975
    # standard-normal quantile (1.959963984540054), p=.5, n=10.
    assert wilson(5,10) == pytest.approx((0.236593090512564,0.763406909487436),abs=1e-12)
    assert wilson(0,0) == (None,None)
    low,high = wilson(0,1)
    assert low == pytest.approx(0,abs=1e-15) and high == pytest.approx(0.793450685622763,abs=1e-12)


@pytest.mark.parametrize('successes,trials', [(-1,2),(3,2),(0,-1)])
def test_wilson_rejects_invalid_counts(successes,trials):
    with pytest.raises(ValueError): wilson(successes,trials)


@pytest.mark.parametrize('v1,v2,v3,v4,risk,baseline,full', [
    ('PASS','PASS','FAIL','PASS',False,'ACCEPT','ACCEPT'),
    ('PASS','PASS','PASS','NOT_AVAILABLE',False,'ACCEPT','FLAG'),
    ('PASS','PASS','PASS','FAIL',False,'ACCEPT','FLAG'),
    ('PASS','PASS','PASS','PASS',True,'ACCEPT','FLAG'),
    ('PASS','FAIL','PASS','PASS',False,'REJECT','FLAG'),
    ('PASS','FAIL','PASS','FAIL',False,'REJECT','REJECT'),
    ('FAIL','FAIL','PASS','PASS',False,'REJECT','REJECT'),
    ('PASS','NOT_AVAILABLE','PASS','PASS',False,'FLAG','FLAG'),
])
def test_implemented_policy_reconstruction_known_examples(v1,v2,v3,v4,risk,baseline,full):
    result = policy_results(v1,v2,v3,v4,risk)
    assert result['baseline_decision'] == baseline
    assert result['full_possible_decisions'] == [full]


def test_risk_missing_is_not_false_and_accept_implication_is_not_independent():
    base = dict(instance_id='i',source_run='s',repo='r',stratum='headline',oracle='resolved',
                integrity='PASS',regression='PASS',static='FAIL',reproduction='PASS',verifier_decision='ACCEPT')
    row = reconstruct(base,{})
    assert row['high_severity_risk'] is False
    assert row['high_severity_risk_status'] == 'inferred_policy_implication_not_independent'
    assert row['full_code_check'] == 'matches_conditional_on_inferred_risk_not_independent'
    # Flipping the oracle cannot change either reconstructed policy result.
    other = reconstruct(dict(base,oracle='unresolved'),{})
    assert row['baseline_decision'] == other['baseline_decision'] and row['full_decision'] == other['full_decision']
    missing = reconstruct(dict(base,regression='NOT_AVAILABLE',verifier_decision='FLAG'),{})
    assert missing['high_severity_risk'] is None and missing['high_severity_risk_status'] == 'missing'
    explicit = explicit_high_risks('| i__i-1 | A | run | FLAG | high-severity risk flag present |')
    assert explicit == {'i__i-1':True}


def test_population_filters_separate_requests_and_structural_empties():
    groups = populations(make_rows())
    assert len(groups['HEADLINE_NONEMPTY_PRIMARY']) == 83
    assert len(groups['REQUESTS_NONEMPTY']) == 6
    assert len(groups['ALL_NONEMPTY']) == 89
    assert len(groups['HEADLINE_INCLUDING_EMPTY_SENSITIVITY']) == 93
    assert len(groups['ALL_100_INCLUDING_EMPTY_SENSITIVITY']) == 100
    assert len(groups['HEADLINE_EMPTY_STRUCTURAL']) == 10 and len(groups['ALL_EMPTY_STRUCTURAL']) == 11
    assert {r['stratum'] for r in groups['HEADLINE_NONEMPTY_PRIMARY']} == {'headline'}


def test_paired_transitions_and_correctness_mcnemar_known_counts():
    rows = populations(make_rows())['HEADLINE_NONEMPTY_PRIMARY']
    t = transitions(rows)
    assert t['ACCEPT','FLAG','resolved'] == 8 and t['ACCEPT','FLAG','unresolved'] == 4
    assert t['REJECT','FLAG','resolved'] == 5
    tests = paired_exact(rows)
    assert tests['stopped_wrong'] == 4 and tests['stopped_right'] == 8
    assert tests['accept_disagreement_table'] == dict(both_accept=52,baseline_only_accept=12,full_only_accept=0,neither_accept=19)
    assert tests['correctness_disagreement_table'] == dict(both_correct=48,baseline_only_correct=8,full_only_correct=4,neither_correct=23)
    # 2*(C(12,0)+...+C(12,4))/2**12 = 1588/4096.
    assert tests['correctness_mcnemar_exact_two_sided_p'] == 1588/4096
    assert exact_mcnemar(0,0) == 1 and exact_mcnemar(0,5) == 1/16


def test_finite_population_exact_test_hand_computed():
    # Two wrong among four accepted; a two-patch stopped set contains both wrong:
    # one favorable subset among C(4,2)=6.
    assert enrichment_exact(4,2,2,2) == 1/6
    assert enrichment_exact(4,2,4,2) == 1
    with pytest.raises(ValueError): enrichment_exact(4,2,2,3)


def test_paired_bootstrap_known_equal_policy_answer_and_repeatability():
    rows = [dict(oracle=label,baseline_decision='ACCEPT',full_decision='ACCEPT') for label in ('resolved','unresolved','resolved')]
    first, draws = paired_bootstrap(rows,seed=13,resamples=100)
    second, repeat = paired_bootstrap(rows,seed=13,resamples=100)
    assert first == second and draws == repeat
    for values in first['differences'].values():
        assert values['point'] == values['low'] == values['high'] == 0


def test_bootstrap_known_all_correct_accept_vs_withhold_and_undefined_precision():
    rows = [dict(oracle='resolved',baseline_decision='ACCEPT',full_decision='FLAG') for _ in range(3)]
    result,_ = paired_bootstrap(rows,seed=1,resamples=30)
    for name in ('recall','f1','accuracy','coverage'):
        assert result['differences'][name]['point'] == result['differences'][name]['low'] == result['differences'][name]['high'] == -1
    p = result['differences']['precision']
    assert p['point'] is p['low'] is p['high'] is None
    assert p['valid_resamples'] == 0 and p['undefined_resamples'] == 30


def test_csv_report_consistency_and_pytest_sensitivity_on_synthetic_fixture(tmp_path):
    facts = build_bundle(make_rows(),tmp_path,seed=7,resamples=100)
    with (tmp_path/'metrics.csv').open() as stream:
        metrics = {(r['population'],r['policy']):r for r in csv.DictReader(stream)}
    with (tmp_path/'confusion_matrices.csv').open() as stream:
        matrices = {(r['population'],r['policy']):r for r in csv.DictReader(stream)}
    assert float(metrics['HEADLINE_NONEMPTY_PRIMARY','baseline']['precision']) == 53/64
    assert float(metrics['HEADLINE_NONEMPTY_PRIMARY','full']['f1']) == 90/121
    assert tuple(int(matrices['PYTEST7432_UNRESOLVED_HEADLINE_SENSITIVITY','baseline'][k]) for k in ('tp','fp','fn','tn')) == (52,12,16,3)
    assert tuple(int(matrices['PYTEST7432_UNRESOLVED_HEADLINE_SENSITIVITY','full'][k]) for k in ('tp','fp','fn','tn')) == (44,8,24,7)
    report = (tmp_path/'report.md').read_text()
    assert '**89 non-empty**' in report and '| Baseline ACCEPT | 53 TP | 11 FP |' in report
    assert '| Full ACCEPT | 45 TP | 7 FP |' in report
    assert '| TP / FP / FN / TN | 52 / 12 / 16 / 3 | 44 / 8 / 24 / 7 |' in report
    assert 'Statistical significance of a reliability improvement is not established' in report
    assert all(r['matches'] for r in facts['expectations'])
    assert json.loads((tmp_path/'analysis.json').read_text())['populations']['HEADLINE_NONEMPTY_PRIMARY']['resolved'] == 69
