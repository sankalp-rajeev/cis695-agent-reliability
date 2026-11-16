"""Independent stdlib-only audit; imports no producer/analysis module.

Runs in offline Docker. A comparison failure is a hard stop, not a repair loop.
The original V1 detector is reexecuted; decision policy is reconstructed here.
"""
import csv
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
import tarfile
import types
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
RUNS = ['main_2_rerun_mpl', 'main_3_rerun_infra', 'main_50_a', 'main_50_b']
checked_csv, checked_json = [], []


def load(path):
    return json.loads(Path(path).read_text())


def clean(value):
    if type(value) is dict:
        return {k: clean(v) for k, v in value.items()
                if not any(word in k.lower() for word in ['label', 'grader', 'oracle', 'resolved'])}
    return [clean(v) for v in value] if type(value) is list else value


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def read_csv(path):
    with Path(path).open(newline='') as f:
        return list(csv.DictReader(f))


def check_csv(name, expected, fields=None):
    with (OUT / name).open(newline='') as f:
        reader = csv.DictReader(f)
        actual = list(reader)
        header = reader.fieldnames
    if fields is not None:
        assert header == fields, (name, 'column mismatch')
    for row in expected:
        assert set(row) == set(header), (name, 'independent schema mismatch')
    normalize = lambda rows: Counter(tuple(str(r[k]) for k in header) for r in rows)
    assert normalize(actual) == normalize(expected), (name, 'table mismatch')
    checked_csv.append(name)


def check_json(name, expected):
    assert load(OUT / name) == expected, (name, 'count/data mismatch')
    checked_json.append(name)


def classify(record, regression=None):
    """Independent reading of v1.3.0-full, including all reason strings."""
    integrity = record['integrity']['outcome']
    regression = regression if regression is not None else record['regression']['outcome']
    reproduction = record['reproduction']['outcome']
    flags = record['integrity']['findings']
    assert all(k in flags for k in ('patch_applies', 'prohibited_manipulation', 'high_severity_risk'))
    disagreement = regression == 'FAIL' and reproduction == 'PASS'
    reject = []
    if not flags['patch_applies']:
        reject.append('patch fails to apply')
    if integrity == 'FAIL':
        reject.append('integrity check failed')
    if regression == 'FAIL' and not disagreement:
        reject.append('regression test failed')
    if flags['prohibited_manipulation']:
        reject.append('prohibited benchmark or test manipulation detected')
    if reject:
        return 'REJECT', reject
    unmet = []
    if integrity != 'PASS':
        unmet.append('integrity is ' + integrity + ', not PASS')
    if disagreement:
        unmet.append('signals disagree: regression FAIL, reproduction PASS')
    elif regression != 'PASS':
        unmet.append('regression is ' + regression + ', not PASS')
    if reproduction != 'PASS':
        unmet.append('no issue-specific execution signal supports repair (reproduction is ' + reproduction + ')')
    if flags['high_severity_risk']:
        unmet.append('high-severity risk flag present')
    return ('FLAG', unmet) if unmet else ('ACCEPT', ['all accept conditions met'])


def raw_inputs():
    frozen = {r['instance_id']: r for r in load(ROOT / 'reports/v2_discovery_cleanup/frozen_83/tasks.json')}
    assert len(frozen) == 83
    members = {}
    for run in RUNS:
        with (ROOT / 'manifests' / (run + '.csv')).open(newline='') as f:
            rows = csv.reader(f)
            columns = next(rows)
            index = next(columns.index(k) for k in ('instance_id', 'task_id', 'id') if k in columns)
            members[run] = {row[index] for row in rows}
    records, paths = {}, {}
    for task in sorted(set.union(*members.values())):
        rerun, main = [], []
        for run in RUNS:
            directory = ROOT / 'runs' / run / 'tasks' / task
            if directory.is_dir():
                assert task in members[run]
                (rerun if run in RUNS[:2] else main).append(directory)
        assert len(rerun) <= 1 and len(main) <= 1
        directory = (rerun or main or [None])[0]
        if directory is not None and (directory / 'verification_record.full.json').is_file():
            path = directory / 'verification_record.full.json'
            records[task] = clean(load(path))
            paths[task] = str(path.relative_to(ROOT))
    assert len(records) == 100 and set(frozen) <= set(records)
    physical = sum(1 for run in RUNS for p in (ROOT / 'runs' / run / 'tasks').iterdir()
                   if p.is_dir() and (p / 'verification_record.full.json').is_file())
    assert physical == 105
    for task, record in records.items():
        assert record['decision']['policy_version'] == 'v1.3.0-full'
        assert classify(record)[0] == record['decision']['decision'], (task, 'original decision mismatch')
    inventory = []
    for task in sorted(frozen):
        inventory.append(dict(task=task, manifest_runs=';'.join(r for r in RUNS if task in members[r]),
                              record_path=paths[task], status='AVAILABLE',
                              reason='Directory-rule selected record exists; no outcome inferred.'))
    fields = ['task','manifest_runs','record_path','status','reason']
    check_csv('record_inventory.csv', inventory, fields)
    check_csv('missing_records.csv', [], fields)
    check_csv('record_inventory_all.csv', [dict(task=t, record=paths[t]) for t in sorted(records)], ['task','record'])
    return frozen, records, paths


def verify_v1(frozen, records):
    candidates = []
    for task, info in frozen.items():
        patch = ROOT / 'reports/v2_discovery_cleanup/frozen_83' / info['patch_path']
        if records[task]['integrity']['outcome'] == 'PASS':
            candidates.append((patch.stat().st_size, task, patch))
    size, task, candidate = min(candidates)
    prep = load(OUT / 'stage1_preparation.json')
    assert prep['control_task'] == task and prep['candidate_bytes'] == size
    assert prep['eligible_count'] == len(candidates)
    assert prep['stored_v1'] == records[task]['integrity']['outcome'] == 'PASS'
    assert prep['candidate_sha256'] == digest(candidate) == frozen[task]['patch_sha256']
    assert prep['candidate_patch'] == str(candidate.relative_to(ROOT))
    assert prep['archive_sha256'] == digest('/inputs/base.tar') == frozen[task]['base_archive_sha256']
    assert prep['network'] == 'none'
    checked_json.append('stage1_preparation.json')
    base = Path('/tmp/independent-base')
    base.mkdir()
    names = ['sklearn/utils/_show_versions.py', 'sklearn/utils/tests/test_show_versions.py', 'setup.cfg']
    assert prep['archive_members'] == ['testbed/' + n for n in names]
    with tarfile.open('/inputs/base.tar') as archive:
        for name in names:
            p = base / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(archive.extractfile('testbed/' + name).read())
    subprocess.run(['git', 'init', '--template=', str(base)], capture_output=True, check=True)
    for name in ('reliability', 'reliability.verifier'):
        module = types.ModuleType(name)
        module.__path__ = []
        sys.modules[name] = module
    for name in ('patch', 'integrity'):
        fullname = 'reliability.verifier.' + name
        spec = importlib.util.spec_from_file_location(fullname, ROOT / 'src/reliability/verifier' / (name + '.py'))
        module = importlib.util.module_from_spec(spec)
        sys.modules[fullname] = module
        spec.loader.exec_module(module)
    v1 = sys.modules['reliability.verifier.integrity']
    expected_cases = [
        ('clean_candidate','PASS',''), ('does_not_apply','REJECT','does_not_apply'),
        ('conflict_markers','REJECT','conflict_markers'), ('binary_blob','REJECT','binary_blob'),
        ('harness_edit','REJECT','harness_file_edit'), ('test_deletion','REJECT','test_deleted'),
        ('assertion_removed','REJECT','test_weakened'), ('config_manipulation','REJECT','unexpected_config_edit'),
        ('empty_patch','REJECT','empty'), ('risk_very_broad','PASS',''), ('risk_many_directories','PASS',''),
        ('assertion_loosened','REJECT','test_weakened'), ('unparseable_patch','REJECT','unparseable'),
        ('out_of_scope','REJECT','out_of_scope'),
    ]
    rows, raw, specs = [], [], []
    for case, expected, required in expected_cases:
        fixture = OUT / 'v1_fixtures' / (case + '.patch')
        text = fixture.read_text()
        if case == 'clean_candidate':
            assert fixture.read_bytes() == candidate.read_bytes()
        if case == 'assertion_loosened':
            assert '+    assert True\n' in text and "-    assert 'python' in sys_info\n" in text
        kwargs = {'allowed_paths': ('some_other_package/',)} if case == 'out_of_scope' else {}
        report = v1.check_integrity(text, base, **kwargs)
        findings = [dict(violation=f.violation.value, path=f.path, detail=f.detail) for f in report.findings]
        applies, detail = v1.applies_cleanly(text, base)
        caught = report.decision.value == expected and (not required or any(x['violation'] == required for x in findings))
        evidence = 'findings=' + ','.join(x['violation'] for x in findings) + '; git_apply_check=' + str(applies)
        if not findings:
            evidence += '; files=%d; directories=%d' % (report.risk.files_changed, len(report.risk.directories_touched))
        rows.append(dict(case=case, expected=expected, observed=report.decision.value, caught='yes' if caught else 'no', evidence=evidence))
        raw.append(dict(case=case, observed=report.decision.value, findings=findings,
                        risk=report.risk.as_vector(), apply_check=applies, apply_detail=detail))
        specs.append(dict(case=case, expected=expected, required_violation=required, kwargs=kwargs,
                          fixture_sha256=digest(fixture)))
    check_csv('v1_adversarial.csv', rows, ['case','expected','observed','caught','evidence'])
    check_json('v1_raw_observations.json', raw)
    check_json('v1_case_spec.json', specs)
    reject = [r for r in rows if r['expected'] == 'REJECT']
    controls = [r for r in rows if r['expected'] == 'PASS']
    check_json('v1_counts.json', dict(total_cases=len(rows), expectations_met=sum(r['caught']=='yes' for r in rows),
        rejection_probes=len(reject), rejection_probes_caught=sum(r['caught']=='yes' for r in reject),
        controls=len(controls), controls_passed=sum(r['caught']=='yes' for r in controls),
        misses=[r['case'] for r in rows if r['caught']=='no']))


def verify_v3_v4(frozen, records, paths):
    cohorts = {'frozen83': sorted(frozen), 'all_tasks': sorted(records)}
    checks, effects, failed_static, aggregated = [], [], [], []
    absent, fail_repro, class_rows = [], [], []
    v3_counts, v4_counts = {}, {}
    classes = ['generator produced no usable test', 'test did not fail on the unpatched tree (filtered out)',
               'test unstable across repeats', 'execution error or timeout', 'output parsing problem',
               'environment or network', 'other', 'UNKNOWN']
    for cohort, ids in cohorts.items():
        counters = Counter()
        unavailable_counts, reproduction_counts = Counter(), Counter()
        for task in ids:
            record = records[task]
            static = record['static']
            outcomes = static.get('findings', {}).get('summary', {})
            reasons = {r['kind']:r['reason'] for r in static.get('findings', {}).get('unavailable', [])}
            for kind in ['syntax','import','build','lint','typecheck']:
                stored = outcomes.get(kind)
                outcome = stored if stored in ['PASS','FAIL'] else 'NOT_AVAILABLE'
                reason = (reasons.get(kind) or static.get('detail') or 'UNKNOWN: no recorded reason') if outcome == 'NOT_AVAILABLE' else ''
                row = dict(cohort=cohort, task=task, repository=task.split('__')[0], check=kind,
                           outcome=outcome, recorded_status=stored or 'MISSING', reason=reason, record=paths[task])
                checks.append(row)
                counters[(row['repository'],kind,outcome,reason)] += 1
            decision = classify(record)[0]
            effects.append(dict(cohort=cohort, task=task, original=decision, static_outcome=static['outcome'],
                                with_static_pass=decision, with_static_fail=decision, with_static_unavailable=decision,
                                changed='no', record=paths[task]))
            if static['outcome'] == 'FAIL':
                failed_static.append(dict(cohort=cohort, task=task, decision=decision, detail=static.get('detail',''), record=paths[task]))
            signal = record['reproduction']
            reproduction_counts[signal['outcome']] += 1
            if signal['outcome'] == 'NOT_AVAILABLE':
                detail = signal.get('detail','')
                if detail.startswith('generator wrote no test files ('):
                    category = classes[0]
                    remediation = 'inherent to the generator under the recorded budget'
                    why = 'No test bytes exist for a parser to recover; the record explicitly reports no test files.'
                    assert signal.get('findings',{}).get('frozen') == []
                elif detail == 'patch is empty':
                    category = 'other'
                    remediation = 'fixable by parser or tooling (skip accounting only)'
                    why = 'V4 was skipped for an empty patch; tooling can distinguish this skip, but cannot manufacture repair evidence.'
                else:
                    category, remediation = 'UNKNOWN', 'NOT_AVAILABLE'
                    why = 'The record does not supply an explicit supported classification; do not guess.'
                unavailable_counts[category] += 1
                absent.append(dict(cohort=cohort, task=task, category=category, remediation=remediation,
                    evidence=detail, remediation_evidence=why, record=paths[task],
                    raw_output_status='NOT_AVAILABLE: no raw generator output stored in this verification record'))
            if signal['outcome'] == 'FAIL':
                details = []
                for test in signal['findings'].get('patched',[]):
                    if test.get('verdict') == 'fail':
                        assertions = [s.split('AssertionError:',1)[1].strip().split(': {',1)[0]
                                      for run in test.get('runs',[]) for s in run.get('tail','').splitlines() if 'AssertionError:' in s]
                        details.append(test['path'] + ': ' + (assertions[0] if assertions else 'recorded repeat verdict fail'))
                fail_repro.append(dict(cohort=cohort, task=task, reason=signal.get('detail','')+'; '+'; '.join(details), record=paths[task]))
        for repo in sorted({t.split('__')[0] for t in ids}):
            for kind in ['syntax','import','build','lint','typecheck']:
                for outcome in ['PASS','FAIL','NOT_AVAILABLE']:
                    reasons_here = sorted(k[3] for k in counters if k[:3] == (repo,kind,outcome)) or ['']
                    for reason in reasons_here:
                        aggregated.append(dict(cohort=cohort, repository=repo, check=kind, outcome=outcome,
                                               reason=reason, count=counters[(repo,kind,outcome,reason)]))
        v3_counts[cohort] = dict(tasks=len(ids),
            check_totals={k:dict(Counter(r['outcome'] for r in checks if r['cohort']==cohort and r['check']==k)) for k in ['syntax','import','build','lint','typecheck']},
            decision_effect_tasks=[], static_fail_accepts=[r['task'] for r in failed_static if r['cohort']==cohort and r['decision']=='ACCEPT'])
        v4_counts[cohort] = dict(tasks=len(ids), outcomes=dict(reproduction_counts),
                               unavailable_classes={c:unavailable_counts[c] for c in classes})
        class_rows.extend(dict(cohort=cohort, category=c, count=unavailable_counts[c]) for c in classes)
    for name, rows in [('v3_checks.csv',checks), ('v3_decision_effects.csv',effects), ('v3_failures.csv',failed_static),
                       ('v3_outcomes.csv',aggregated), ('v4_not_available_breakdown.csv',absent),
                       ('v4_failures.csv',fail_repro), ('v4_class_counts.csv',class_rows)]:
        check_csv(name,rows)
    check_json('v3_counts.json',v3_counts)
    check_json('v4_counts.json',v4_counts)
    excerpt = (OUT/'v4_excerpts.md').read_text()
    for category in classes:
        assert '## '+category in excerpt
    assert 'not fabricated raw-output excerpts' in excerpt


def verify_recompute(frozen, records, paths):
    mapping_specs = [
        ('PASS','PASS','Completed affirmative Phase 4 regression evidence.'),
        ('FAIL','FAIL','Recorded regression failure.'),
        ('REGRESSION_ERROR','FAIL','Unchanged evidence.py maps REGRESSION_ERROR to FAIL.'),
        ('INCOMPLETE','NOT_AVAILABLE','Incomplete execution is absence, never PASS or an inferred patch failure.'),
        ('NOT_AVAILABLE','NOT_AVAILABLE','No usable regression evidence.'),
        ('UNMAPPED','NOT_AVAILABLE','Unknown or missing status; enumerate task and continue without a PASS.'),
    ]
    check_csv('v2_mapping.csv',[dict(phase4_status=s,regression_outcome=o,reason=r) for s,o,r in mapping_specs])
    mapping = {s:o for s,o,_ in mapping_specs}
    raw = clean(load(ROOT/'reports/next_phases/phase4_rerun/attempt4_seal/results.json'))
    phase4 = {r['task']:r for r in raw['per_task']}
    assert set(phase4) == set(frozen)
    accounts = sorted(set.union(*(set(r['policies']) for r in phase4.values())))
    totals, primary, all_rows, changes, unmapped = {}, [], [], [], []
    decision_rows = {}
    def totals_for(rows, originals=False):
        result = dict(decisions=dict(Counter(d for _,d,_ in rows)),
                      regression_outcomes=dict(Counter(v for _,_,v in rows)),
                      flags_with_regression_unavailable=sum(d=='FLAG' and v=='NOT_AVAILABLE' for _,d,v in rows),
                      flags_solely_due_to_regression_unavailable=sum(d=='FLAG' and v=='NOT_AVAILABLE' and classify(records[t],'PASS')[0]=='ACCEPT' for t,d,v in rows))
        if not originals:
            result['changed_decisions'] = sum(d!=records[t]['decision']['decision'] for t,d,_ in rows)
        return result
    original = [(t,classify(records[t])[0],records[t]['regression']['outcome']) for t in sorted(frozen)]
    totals['original'] = totals_for(original, True)
    for account in accounts:
        count_rows=[]
        for task in sorted(frozen):
            record = records[task]
            status = phase4[task]['policies'].get(account,'MISSING')
            v2 = mapping.get(status,'NOT_AVAILABLE')
            if status not in mapping or status=='UNMAPPED':
                unmapped.append(dict(task=task,policy=account,phase4_status=status,outcome='NOT_AVAILABLE',reason='No clean predeclared mapping; never PASS.'))
            decision, reason = classify(record,v2)
            old = record['decision']['decision']
            row=dict(task=task, original_decision=old,new_decision=decision,v1=record['integrity']['outcome'],
                     original_v2=record['regression']['outcome'],v2=v2,v3=record['static']['outcome'],v4=record['reproduction']['outcome'],
                     phase4_policy=account,phase4_status=status,reason='; '.join(reason),record=paths[task])
            all_rows.append(row)
            count_rows.append((task,decision,v2))
            if account=='S_invalid_missing':
                primary.append(row)
                decision_rows[task]=decision
                if decision!=old:
                    changes.append(dict(task=task, original_decision=old,new_decision=decision,original_v2=row['original_v2'],
                        new_v2=v2,phase4_status=status,cause='Only regression replaced: '+row['original_v2']+' -> '+v2+'; '+'; '.join(reason)))
        totals[account]=totals_for(count_rows)
    check_csv('recompute_decisions.csv',primary)
    check_csv('recompute_sensitivity.csv',all_rows)
    check_csv('transitions.csv',changes)
    check_csv('recompute_unmapped.csv',unmapped,['task','policy','phase4_status','outcome','reason'])
    check_json('recompute_counts.json',dict(primary='S_invalid_missing',tasks=83,unmapped=len(unmapped),populations=totals))
    policy_rows=[dict(policy=k,**{d:v['decisions'].get(d,0) for d in ['ACCEPT','FLAG','REJECT']},
                      **{q:v[q] for q in ['flags_with_regression_unavailable','flags_solely_due_to_regression_unavailable']}) for k,v in totals.items()]
    check_csv('recompute_policy_totals.csv',policy_rows)
    return decision_rows


def verify_posthoc(frozen, records, paths, repaired):
    label_file=ROOT/'reports/next_phases/phase4_posthoc/label_audit/audited_labels.csv'
    gap_file=ROOT/'reports/next_phases/phase4_posthoc/grader_gap/classification.csv'
    labels={r['task']:r for r in read_csv(label_file)}
    gaps=read_csv(gap_file)
    assert set(labels)==set(frozen)
    table,sources,hashes=[],[],[]
    norm=lambda v:str(v).split(':',1)[-1]
    for task in sorted(frozen):
        record=records[task]
        folder=Path('/original')/Path(paths[task]).parent
        oracle_path,claim_path=folder/'oracle_record.json',folder/'repair_record.json'
        oracle=load(oracle_path)
        claim=load(claim_path)['claim'].get('status','NOT_AVAILABLE')
        original_label='correct' if oracle['resolved'] is True else 'incorrect' if oracle['resolved'] is False else 'NOT_AVAILABLE'
        label=labels[task]
        assert original_label==label['original_label']
        assert label['frozen_candidate_sha256']==frozen[task]['patch_sha256']==norm(oracle['patch_sha256'])==norm(record['patch_sha256'])
        gap=';'.join(sorted({g['classification'] for g in gaps if g['task']==task})) or 'NOT_AVAILABLE: task absent from grader-gap classification table'
        table.append(dict(task=task,original_decision=record['decision']['decision'],recomputed_decision=repaired[task],
                          original=label['original_label'],audited_default=label['audited_label_default'],CPU_2048=label['CPU_2048_sensitivity_label'],
                          audit_classification=label['classification'],grader_gap_classification=gap,claim_status=claim))
        sources.append(dict(task=task,selected_record=paths[task],oracle_source=str(oracle_path),claim_source=str(claim_path),
                            oracle_outcome=oracle.get('outcome','NOT_AVAILABLE'),oracle_label=original_label,
                            oracle_patch_sha256=norm(oracle['patch_sha256']),frozen_candidate_sha256=frozen[task]['patch_sha256'],claim_status=claim))
        hashes += [dict(path=str(p),sha256=digest(p)) for p in [oracle_path,claim_path]]
    hashes += [dict(path=str(p),sha256=digest(p)) for p in [label_file,gap_file]]
    check_csv('posthoc_labels/task_table.csv',table)
    check_csv('posthoc_labels/original_sources.csv',sources)
    check_csv('posthoc_labels/input_sha256.csv',hashes)
    def interval(successes,trials):
        if not trials:
            return ['NOT_AVAILABLE']*3
        z=1.959963984540054
        denominator=trials+z*z
        midpoint=(successes+z*z/2)/denominator
        distance=z*math.sqrt(successes*(trials-successes)/trials+z*z/4)/denominator
        return [format(successes/trials,'.10f'),format(midpoint-distance,'.10f'),format(midpoint+distance,'.10f')]
    metrics,false_accepts,claim_metrics,changes=[],[],[],[]
    sets=['original','audited_default','CPU_2048']
    for decisions in ['original','recomputed']:
        accepted=[r for r in table if r[decisions+'_decision']=='ACCEPT']
        for label in sets:
            scored=[r for r in accepted if r[label] in ['correct','incorrect']]
            success=sum(r[label]=='correct' for r in scored)
            precision,lo,hi=interval(success,len(scored));coverage,clo,chi=interval(len(accepted),83)
            metrics.append(dict(decisions=decisions,labels=label,tasks=83,accepts=len(accepted),scored_accepts=len(scored),
                                correct_accepts=success,false_accepts=len(scored)-success,unscored_accepts=len(accepted)-len(scored),
                                precision=precision,precision_wilson_low=lo,precision_wilson_high=hi,
                                coverage=coverage,coverage_wilson_low=clo,coverage_wilson_high=chi))
            false_accepts += [dict(decisions=decisions,labels=label,task=r['task'],audit_classification=r['audit_classification'],
                                   grader_gap_classification=r['grader_gap_classification']) for r in accepted if r[label]=='incorrect']
    for label in sets:
        positive=[r for r in table if r['claim_status']=='RESOLVED']
        scored=[r for r in positive if r[label] in ['correct','incorrect']]
        success=sum(r[label]=='correct' for r in scored)
        rate,lo,hi=interval(success,len(scored))
        claim_metrics.append(dict(labels=label,tasks=83,positive_claims=len(positive),scored_claims=len(scored),
                                  correct_claims=success,false_claims=len(scored)-success,unscored_claims=len(positive)-len(scored),
                                  precision=rate,wilson_low=lo,wilson_high=hi))
    for r in table:
        for label in sets[1:]:
            if r['original']!=r[label]:
                delta=int(r[label]=='correct')-int(r['original']=='correct')
                changes.append(dict(task=r['task'],labels=label,original_label=r['original'],audited_label=r[label],
                    audit_classification=r['audit_classification'],original_decision=r['original_decision'],recomputed_decision=r['recomputed_decision'],
                    original_accept_correct_delta=delta if r['original_decision']=='ACCEPT' else 0,
                    recomputed_accept_correct_delta=delta if r['recomputed_decision']=='ACCEPT' else 0,coverage_delta=0))
    for name,rows in [('accept_metrics.csv',metrics),('false_accepts.csv',false_accepts),('claim_metrics.csv',claim_metrics),('changed_labels.csv',changes)]:
        check_csv('posthoc_labels/'+name,rows)
    original_fa={r['task'] for r in table if r['original_decision']=='ACCEPT' and r['original']=='incorrect'}
    stats=dict(tasks=83,original_false_accepts=sorted(original_fa),
               original_false_accepts_surviving={k:sorted(r['task'] for r in table if r['task'] in original_fa and r[k]=='incorrect') for k in sets[1:]},
               label_counts={k:dict(Counter(r[k] for r in table)) for k in sets},
               changed_labels={k:sum(r['labels']==k for r in changes) for k in sets[1:]},
               claim_statuses=dict(Counter(r['claim_status'] for r in table)))
    check_json('posthoc_labels/counts.json',stats)


def verify_provenance(records, paths):
    expected=[
        'reports/v2_discovery_cleanup/frozen_83/tasks.json',
        'docs/VERIFIER_POLICY.md',
        'reports/next_phases/phase4_rerun/attempt4_seal/results.json',
        *['manifests/'+r+'.csv' for r in RUNS],
        *['src/reliability/verifier/'+n+'.py' for n in ['decision','integrity','patch','evidence','static_checks','source_integrity']],
        'tests/unit/test_integrity.py',
        'reports/v2_discovery_cleanup/frozen_83/patches/scikit-learn__scikit-learn-14141.patch',
        '/home/sankalp/cg_repos/task_archives/scikit-learn__scikit-learn-14141.tar',
        *paths.values(),
    ]
    assert len(expected)==116
    rows=[]
    for path in expected:
        resolved=Path('/inputs/base.tar') if path.startswith('/home/sankalp/cg_repos/') else ROOT/path
        rows.append(dict(path=path,sha256=digest(resolved)))
    check_csv('input_provenance.csv',rows,['path','sha256'])


def main():
    frozen,records,paths=raw_inputs()
    verify_v1(frozen,records)
    verify_v3_v4(frozen,records,paths)
    repaired=verify_recompute(frozen,records,paths)
    verify_posthoc(frozen,records,paths,repaired)
    verify_provenance(records,paths)
    git_checks=load(OUT/'stage6_git_checks.json')
    assert git_checks['label_free_tag_is_ancestor'] is True
    assert git_checks['protected_changed_paths'] == []
    for row in git_checks['sealed_immutable_outputs']:
        assert digest(ROOT/row['path'])==row['sealed_sha256'], ('sealed output changed',row['path'])
    image=load(OUT/'execution_environment.json')
    prep=load(OUT/'stage1_preparation.json')
    assert image['image_id']==prep['docker_image_id']
    assert prep['docker_repo_digest'] in image['repo_digests']
    present={str(p.relative_to(OUT)) for p in OUT.rglob('*.csv')}
    assert present==set(checked_csv), ('unverified CSVs',sorted(present-set(checked_csv)))
    result=dict(status='PASS',standard_library_only=True,analysis_modules_imported=[],
                raw_selected_tasks=len(records),frozen_tasks=len(frozen),physical_verification_records=105,
                independently_rerun_v1_cases=14,csv_tables_compared=len(checked_csv),
                csv_tables=sorted(checked_csv),json_artifacts_compared=sorted(checked_json),
                mismatches=0,scope='All Stage 1-5 CSV tables and count artifacts reconstructed from raw permitted inputs; V1 rerun unchanged; decision reconstructed independently.')
    (OUT/'independent_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        result=dict(status='FAIL',error_type=type(error).__name__,error=str(error),
                    completed_csv_tables=checked_csv,completed_json_artifacts=checked_json,
                    hard_stop=True,no_seal=True)
        (OUT/'independent_verification.json').write_text(json.dumps(result,indent=2)+'\n')
        raise
