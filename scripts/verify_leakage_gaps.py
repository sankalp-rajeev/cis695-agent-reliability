"""Independent stdlib-only recount and rule-3 verification; no reliability imports.

Never opens a dataset, gold patch, correctness label or grader result. Symbol
hashes are checked against tokens read directly from the verified base tar.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
import tarfile
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def fail(message):
    raise ValueError(message)


def symbol_hashes(pin):
    path = Path(pin['path'])
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != pin['sha256']:
        fail('archive digest mismatch')
    symbols = set()
    with tarfile.open(path) as tar:
        for member in tar:
            if member.isfile() and member.name.startswith('testbed/'):
                if '..' in Path(member.name).parts:
                    fail('unsafe archive path')
                raw = tar.extractfile(member).read()
                symbols.update(hashlib.sha256(s).hexdigest() for s in
                               re.findall(rb'\btest[A-Za-z0-9_]+\b', raw))
    return symbols


def finding_key(f):
    return f['path'], f['kind'], f['line_no'], f['severity']


def definition_evidence(path, symbol_hash):
    """Independently decode commands and require a successful ordered write."""
    first, definitions, pending = None, [], {}
    for number, raw in enumerate(path.read_text().splitlines(), 1):
        try:
            message = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(message, dict):
            continue
        if any(hashlib.sha256(token.encode()).hexdigest() == symbol_hash
               for token in re.findall(r'\btest[A-Za-z0-9_]+\b', raw)):
            first = number if first is None else first
        if message.get('role') == 'assistant':
            for index, call in enumerate(message.get('tool_calls') or []):
                function = call.get('function') or {}
                if function.get('name') != 'bash':
                    continue
                args = function.get('arguments') or {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except ValueError:
                        continue
                command = args.get('command', '') if isinstance(args, dict) else ''
                if not re.search(r'(?:>|\b(?:write_text|write_bytes|write|writelines|apply_patch|sed|perl|tee)\b)', command):
                    continue
                symbols = re.findall(r'\b(?:async\s+)?def\s+(test[A-Za-z0-9_]+)\s*\(', command)
                if any(hashlib.sha256(s.encode()).hexdigest() == symbol_hash for s in symbols):
                    pending[str(call.get('id') or f'call-{index}')] = number
        elif message.get('role') == 'tool':
            definition = pending.pop(str(message.get('tool_call_id') or ''), None)
            if definition is not None and re.search(r'<returncode>\s*0\s*</returncode>', str(message.get('content') or '')):
                definitions.append(definition)
    return first, min(definitions) if definitions else None


def verify(root):
    tasks = [read(p) for p in sorted((root/'tasks').glob('*/*/*.json'))]
    if not tasks:
        fail('empty trajectory results')
    findings = [f for task in tasks for f in task['findings']]
    summary = read(root/'trajectory_summary.json')
    expected = dict(task_directories=len(tasks), unique_tasks=len({r['instance_id'] for r in tasks}),
        repair_directories=sum(r['role']=='repair' for r in tasks),
        generator_directories=sum(r['role']=='generator' for r in tasks),
        scanned_files=sum(r['scanned_files'] for r in tasks), findings=len(findings),
        severity=dict(collections.Counter(f['severity'] for f in findings)),
        rules=dict(collections.Counter(f['rule'] for f in findings)),
        legacy_findings=sum(len(r['legacy_findings']) for r in tasks),
        downgrades=sum(len(r['golden']['downgrades']) for r in tasks),
        golden_violations=sum(len(r['golden']['violations']) for r in tasks),
        awareness_tasks=len({r['instance_id'] for r in tasks if any(f['severity']=='benchmark-awareness' for f in r['findings'])}),
        confirmed_tasks=sorted({r['instance_id'] for r in tasks if any(f['severity']=='confirmed' for f in r['findings'])}))
    if expected != summary:
        fail('trajectory totals mismatch')
    pins, checked = {}, 0
    for task in tasks:
        before = collections.Counter(finding_key(f) for f in task['legacy_findings'])
        after = collections.Counter(finding_key(f) for f in task['findings'])
        for downgrade in task['golden']['downgrades']:
            old, new = downgrade['before'], downgrade['after']
            if old['severity'] != 'confirmed' or new['severity'] != 'review':
                fail('invalid downgrade severity')
            if (old['path'],old['kind'],old['line_no']) != (new['path'],new['kind'],new['line_no']):
                fail('downgrade identity changed')
            rule = new['rule']
            pin = task['archive']
            if pin['sha256'] not in pins:
                pins[pin['sha256']] = symbol_hashes(pin)
            symbol_hash = new['evidence']['symbol_sha256']
            present = symbol_hash in pins[pin['sha256']]
            if rule == 'test-name-present-at-base':
                if not present or not new['evidence']['base_present']:
                    fail('base-present downgrade disproved')
            elif rule == 'test-name-agent-defined-before-output':
                if present or new['evidence']['base_present']:
                    fail('agent-definition downgrade unexpectedly at base')
                # Find a definition of this hashed symbol in a file-write call
                # before the first output containing the symbol. No gold names.
                first, definition = definition_evidence(Path(new['path']), symbol_hash)
                if first is None or definition is None or definition > first:
                    fail('ordered-definition downgrade disproved')
            else:
                fail('unsupported downgrade rule')
            before[finding_key(old)] -= 1
            checked += 1
        if any(count > after[key] for key, count in before.items()):
            fail('legacy golden finding lost')
    if read(root/'downgrades.json') != [d for t in tasks for d in t['golden']['downgrades']]:
        fail('downgrade inventory mismatch')
    images = [read(p) for p in sorted((root/'images').glob('*.json'))]
    image_summary = read(root/'image_summary.json')
    if len(images) != image_summary['cohort']:
        fail('image cohort total mismatch')
    missing = sorted(r['instance_id'] for r in images if r.get('status') == 'missing')
    if missing != sorted(image_summary['missing']):
        fail('missing image inventory mismatch')
    git_results = [r.get('checks', {}).get('git', {}).get('result', {}) for r in images]
    copies = [(r['instance_id'], c) for r in images for c in
              r.get('checks', {}).get('packages', {}).get('result', {}).get('copies', [])]
    image_recount = dict(cohort=len(images), present=sum(r.get('status') != 'missing' for r in images),
        missing=missing,
        incomplete=sorted(r['instance_id'] for r in images if r.get('status') == 'incomplete' or
            any(c['status'] != 'complete' for c in r.get('checks', {}).values())),
        future_history_images=sum(g.get('future_object_count', 0) > 0 for g in git_results),
        future_reachable_images=sum(g.get('future_reachable_count', 0) > 0 for g in git_results),
        gold_blob_images=sum(any(b['present'] for b in g.get('gold_post_image_blobs', [])) for g in git_results),
        gold_blobs_probed=sum(len(g.get('gold_post_image_blobs', [])) for g in git_results),
        different_version_copies=sum(c.get('different_from_base') is True for _, c in copies),
        different_version_tasks=sorted({iid for iid,c in copies if c.get('different_from_base')}),
        unresolved_copy_versions=sum(c.get('different_from_base') is None for _, c in copies))
    if image_recount != image_summary:
        fail('image totals mismatch')
    subtraction = root/'legacy_subtraction_comparison.json'
    if subtraction.is_file():
        proof = read(subtraction)
        by_id = {row['instance_id']:row for row in proof['tasks']}
        if proof['checked'] != len(images) or proof['mismatches'] or len(by_id) != len(images):
            fail('legacy subtraction coverage mismatch')
        for image in images:
            row = by_id[image['instance_id']]
            hashes = sorted(set(image['checks']['base_probes']['result']))
            observed = hashlib.sha256(json.dumps(hashes).encode()).hexdigest()
            if not row['equal'] or row['baseline_sha256'] != observed or row['extended_sha256'] != observed:
                fail('legacy subtraction proof mismatch')
    report = (root/'REPORT.md').read_text()
    marker = re.search(r'<!-- totals-json: (.+?) -->', report)
    if not marker or json.loads(marker.group(1)) != dict(trajectory=expected, images=image_summary):
        fail('report totals mismatch')
    human_totals = {
        r'Confirmed findings: (\d+)': expected['severity'].get('confirmed', 0),
        r'Benchmark-awareness findings: (\d+)': expected['severity'].get('benchmark-awareness', 0),
        r'(\d+) images contain commits after base': image_summary['future_history_images'],
        r'(\d+) images contain at least one exact gold': image_summary['gold_blob_images'],
        r'(\d+) unmasked package copies have': image_summary['different_version_copies'],
        r'(\d+) copy versions remain unresolved': image_summary['unresolved_copy_versions'],
    }
    for pattern, expected_value in human_totals.items():
        found = re.search(pattern, report)
        if not found or int(found.group(1)) != expected_value:
            fail('human-readable report total mismatch')
    result = dict(status='pass', task_directories=len(tasks), findings=len(findings),
                  image_tasks=len(images), downgrades_rechecked=checked,
                  golden_violations=expected['golden_violations'])
    if expected['golden_violations'] or image_summary['incomplete']:
        fail('audit incomplete or golden violated')
    return result


def interpreted_tier(facts):
    """Independent interpretation of sanitized facts; no package imports."""
    rank = 0
    reasons = set()
    for fact in facts:
        category = fact['category']
        if category == 'answer':
            if fact['field'] == 'hidden_test_name':
                eligible = fact['base_occurrences'] == 0
                expected_guards = []
            else:
                expected_guards = []
                if fact['nonwhitespace_length'] < 25:
                    expected_guards.append('guard-short-content')
                if fact['base_occurrences'] >= 3:
                    expected_guards.append('guard-common-at-base')
                eligible = not expected_guards
            if fact['guard_pass'] != eligible or fact['guard_rules'] != expected_guards:
                fail('interpretive distinctiveness guard mismatch')
            if not eligible:
                reasons.update(expected_guards)
                continue
            if fact.get('defined_at_first_mention'):
                continue
            observed = fact.get('occurrences', {})
            if observed:
                first = min(observed, key=lambda k:observed[k]['line'])
                if fact['first_seen_in'] != first:
                    fail('first occurrence order mismatch')
            if fact['first_seen_in'] == 'tool_output':
                rank = max(rank,4); reasons.add('answer-tool-output-first')
            elif fact['first_seen_in'] == 'model_output':
                rank = max(rank,3); reasons.add('answer-model-output-first')
            else:
                fail('unsupported first occurrence role')
        elif category == 'history':
            if fact['setup_only']:
                rank=max(rank,1); reasons.add('harmless-setup-history')
            else:
                rank=max(rank,2); reasons.add('history-attempt-no-distinctive-answer')
        elif category == 'awareness':
            rank=max(rank,2); reasons.add('awareness-no-distinctive-tool-answer')
        elif category == 'cache':
            actual = fact['listed_files'] > 0 or fact['content_bytes'] > 0
            if actual != fact['nonempty_cache']:
                fail('masked cache nonempty evidence mismatch')
            if fact['rule']=='masked-read-failed' and fact['nonempty_cache']:
                fail('failed read cannot establish cache content')
            rank=max(rank,2); reasons.add(fact['rule'])
        else:
            fail('unknown interpretation evidence category')
    return 'T'+str(rank), sorted(reasons)


def interpreted_summary(records, cohort, comparable):
    levels=('T0','T1','T2','T3','T4')
    excluded={iid for iid in cohort if iid.startswith('psf__requests-')}
    included=set(cohort)-excluded
    combined=dict.fromkeys(included,'T0')
    by_role={}
    for role in ('repair','generator'):
        worst=dict.fromkeys(included,'T0'); observed=set()
        for record in records:
            iid=record['instance_id']
            if iid not in included or record['role']!=role:
                continue
            if record['observed']:
                observed.add(iid)
            worst[iid]=max(worst[iid],record['underlying_tier'])
            combined[iid]=max(combined[iid],record['underlying_tier'])
        by_role[role]={'counts':{t:sum(v==t for v in worst.values()) for t in levels},
            'tasks_by_tier':{t:sorted(iid for iid,v in worst.items() if v==t) for t in levels},
            'observed_tasks':len(observed),'unobserved_tasks':sorted(included-observed)}
    cache=collections.defaultdict(collections.Counter)
    guards=[]
    for record in records:
        for fact in record['facts']:
            if fact['category']=='cache':
                cache[fact['path']][fact['rule']]+=1
            if fact['category']=='answer' and not fact['guard_pass']:
                guards.append(fact)
    comparable_included=sorted(set(comparable)&included)
    cache_outcomes=collections.Counter()
    for record in records:
        by_index=collections.defaultdict(set)
        for fact in record['facts']:
            if fact['category']=='cache':
                by_index[fact['raw_finding_index']].add(fact['rule'])
        for rules in by_index.values():
            if rules & {'masked-read-content','masked-read-listed-files','masked-read-archive-member-list'}:
                label='nonempty-content-or-filenames'
            elif rules & {'masked-read-directory-metadata','masked-read-file-metadata'}:
                label='metadata-only'
            elif rules & {'masked-read-empty','masked-read-empty-listing'}:
                label='empty-listing'
            elif 'masked-read-failed' in rules:
                label='failure'
            elif 'masked-read-other-paths-only' in rules:
                label='other-path-output-only'
            else:
                label='unattributed'
            cache_outcomes[label]+=1
    return {'schema_version':1,'cohort':len(cohort),'included_tasks':len(included),
        'excluded_tasks':sorted(excluded),'rows':len(records),
        'observed_rows':sum(r['observed'] for r in records),
        'row_counts':{role:dict(collections.Counter(r['tier'] for r in records if r['role']==role))
                     for role in ('repair','generator')},'by_role':by_role,
        'T3_tasks':sorted(iid for iid,t in combined.items() if t=='T3'),
        'T4_tasks':sorted(iid for iid,t in combined.items() if t=='T4'),
        'comparable_tasks':comparable_included,'comparable_count':len(comparable_included),
        'comparable_T3_or_T4_tasks':sorted(iid for iid in comparable_included if combined[iid] in {'T3','T4'}),
        'comparable_T3_or_T4_count':sum(combined[iid] in {'T3','T4'} for iid in comparable_included),
        'guard_removed_matches':len(guards),
        'guard_removed_raw_findings':sum(f['guard_removed'] for r in records for f in r['raw_finding_interpretations']),
        'serialization_only_raw_findings':sum(f.get('serialization_only',False) for r in records for f in r['raw_finding_interpretations']),
        'guard_reasons':dict(collections.Counter(reason for f in guards for reason in f['guard_rules'])),
        'raw_masked_read_findings':sum(r['raw_cache_findings'] for r in records),
        'cache_findings_by_result':dict(cache_outcomes),
        'masked_path_counts':{p:dict(c) for p,c in sorted(cache.items())}}


def verify_tiers(root):
    tiers=root/'tiers'
    records=[read(p) for p in sorted((tiers/'artifacts').glob('*/*/*.json'))]
    if not records:
        fail('empty interpretation inventory')
    identities={(r['instance_id'],r['run'],r['role']) for r in records}
    if len(identities)!=len(records):
        fail('duplicate interpretation row')
    raw_files=sorted((root/'tasks').glob('*/*/*.json'))
    raw_records=[read(path) for path in raw_files]
    expected={(r['instance_id'],r['run'],role) for r in raw_records for role in ('repair','generator')}
    if identities!=expected:
        fail('interpretation role coverage mismatch')
    referenced={r['raw_path'] for r in records if r.get('raw_path')}
    if referenced!={p.relative_to(root).as_posix() for p in raw_files}:
        fail('raw inventory interpretation coverage mismatch')
    for record in records:
        verify_chronological_receipts(record)
        tier,reasons=interpreted_tier(record['facts'])
        excluded=record['instance_id'].startswith('psf__requests-')
        if record['underlying_tier']!=tier or record['tier']!=('Excluded' if excluded else tier):
            fail('per-task contamination tier mismatch')
        if record['excluded']!=excluded:
            fail('requests exclusion mismatch')
        if not record['observed'] and not record['facts']:
            reasons=['trajectory-not-observed']
        if record['reasons']!=reasons:
            fail('tier reasons mismatch')
        first=sorted({f['first_seen_in'] for f in record['facts'] if f['category']=='answer' and f['guard_pass']})
        if record['first_seen_in']!=first:
            fail('row first-seen roles mismatch')
        raw_path=record.get('raw_path')
        if raw_path:
            path=root/raw_path
            if '..' in Path(raw_path).parts or Path(raw_path).is_absolute():
                fail('unsafe raw inventory reference')
            with path.open('rb') as stream:
                if hashlib.file_digest(stream,'sha256').hexdigest()!=record['raw_file_sha256']:
                    fail('raw inventory changed')
            raw=read(path)
            expected_hash=hashlib.sha256(json.dumps(raw['findings'],sort_keys=True).encode()).hexdigest()
            if expected_hash!=record['raw_findings_sha256']:
                fail('raw finding list changed')
            for finding in record['raw_finding_interpretations']:
                prior=raw['findings'][finding['finding_index']]
                if (prior['kind'],prior['rule'])!=(finding['kind'],finding['rule']):
                    fail('raw finding interpretation reference mismatch')
                if (prior['kind'] in {'gold-patch-content','test-patch-content'} or
                        prior['rule']=='test-name-absent-before-definition') and finding['first_seen_in'] not in {'tool_output','model_output'}:
                    fail('raw answer finding lacks first speaker classification')
    cohort=sorted({r['instance_id'] for r in records})
    comparable={r['instance_id'] for r in records if r['comparable']}
    expected=interpreted_summary(records,cohort,comparable)
    if expected!=read(tiers/'summary.json'):
        fail('interpretive summary mismatch')
    history_file=tiers/'history_gold_checks.json'
    if history_file.is_file():
        history=[dict(instance_id=r['instance_id'],run=r['run'],role=r['role'],**h)
                 for r in sorted(records,key=lambda r:(r['run'],r['role'],r['instance_id'])) for h in r['history_gold']]
        if read(history_file)!=history:
            fail('focused history receipt inventory mismatch')
    with (tiers/'task_tiers.csv').open(newline='') as stream:
        reader=csv.DictReader(stream); fields=reader.fieldnames; actual=list(reader)
    canonical=[]
    for record in sorted(records,key=lambda r:(r['run'],r['role'],r['instance_id'])):
        canonical.append({key:json.dumps(record[key],separators=(',',':')) if isinstance(record[key],list)
            else str(record[key]).lower() if isinstance(record[key],bool) else record[key] for key in fields})
    if actual!=canonical:
        fail('tier CSV mismatch')
    manifest=tiers/'inventory_manifest.json'
    if manifest.is_file():
        pin=read(manifest)
        historical={r['instance_id'] for r in raw_records if
                    r.get('archive',{}).get('pin_origin')=='historical-archive-references'}
        if historical!=comparable:
            fail('comparable cohort differs from pinned historical inventory')
        for name,expected_hash in pin['files'].items():
            path=root/name
            if Path(name).is_absolute() or '..' in Path(name).parts:
                fail('unsafe inventory manifest path')
            with path.open('rb') as stream:
                if hashlib.file_digest(stream,'sha256').hexdigest()!=expected_hash:
                    fail('immutable raw inventory changed')
        with (tiers/'raw_rule_inventory.md').open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=pin['raw_report_sha256']:
                fail('raw report inventory changed')
        report=(root/'REPORT.md').read_text()
        if not report.endswith((tiers/'raw_rule_inventory.md').read_text()):
            fail('old report inventory not preserved')
        marker=re.search(r'<!-- interpreted-totals-json: (.+?) -->',report)
        if not marker or json.loads(marker.group(1))!=expected:
            fail('interpreted report totals mismatch')
    return {'status':'pass','rows':len(records),'T3_tasks':len(expected['T3_tasks']),
            'T4_tasks':len(expected['T4_tasks']),'comparable_T3_or_T4_count':expected['comparable_T3_or_T4_count']}


def verify_chronological_receipts(record):
    """Check hashed probe slices and first speaker against decoded source messages."""
    def strings(value):
        if isinstance(value,str):
            result=[value]
            if value.lstrip()[:1] in ('{','['):
                try:
                    result.extend(strings(json.loads(value)))
                except ValueError:
                    pass
            return result
        if isinstance(value,dict):
            return [s for v in value.values() for s in strings(v)]
        if isinstance(value,list):
            return [s for v in value for s in strings(v)]
        return []
    trajectories={}
    for name,expected_hash in record.get('trajectory_sha256',{}).items():
        if name not in {'trajectory.jsonl','generation_trajectory.jsonl'}:
            fail('unsupported chronology source path')
        path=Path(record['source'])/name
        with path.open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=expected_hash:
                fail('chronology source changed')
        messages={}
        for number,raw in enumerate(path.read_text(errors='replace').splitlines(),1):
            try:
                message=json.loads(raw)
            except ValueError:
                continue
            if not isinstance(message,dict):
                continue
            role=message.get('role')
            if role=='tool':
                content=str(message.get('content') or '')
                match=re.search(r'<output>(.*?)</output>',content,re.S)
                text=match.group(1).strip() if match else content
            else:
                text='\n'.join(strings(message))
            messages[number]=(role,text)
        trajectories[name]=messages
    for fact in record['facts']:
        if fact['category']!='answer':
            continue
        if fact['field']=='hidden_test_name' and fact.get('occurrences'):
            first=min(fact['occurrences'].values(),key=lambda p:p['line'])
            _,defined=definition_evidence(Path(record['source'])/first['trajectory'],fact['probe_sha256'])
            if fact.get('definition_line')!=defined:
                fail('hidden name definition receipt mismatch')
            if fact.get('defined_at_first_mention')!=(defined is not None and defined<=first['line']):
                fail('hidden name first-write ordering mismatch')
        for first_kind,proof in fact.get('occurrences',{}).items():
            messages=trajectories.get(proof['trajectory'],{})
            role,text=messages.get(proof['line'],(None,''))
            if role!=('tool' if first_kind=='tool_output' else 'assistant'):
                fail('chronological first speaker mismatch')
            if hashlib.sha256(text.encode()).hexdigest()!=proof['text_sha256']:
                fail('chronological text hash mismatch')
            probe=text[proof['offset']:proof['offset']+proof['length']]
            if hashlib.sha256(probe.encode()).hexdigest()!=fact['probe_sha256']:
                fail('chronological probe hash mismatch')
            if fact['field']!='hidden_test_name' and len(re.sub(r'\s','',probe))!=fact['nonwhitespace_length']:
                fail('content length guard receipt mismatch')
            for number,(earlier_role,earlier_text) in messages.items():
                if earlier_role not in {'assistant','tool'}:
                    continue
                present=(bool(re.search(r'\b'+re.escape(probe)+r'\b',earlier_text))
                         if fact['field']=='hidden_test_name' else probe in earlier_text)
                kind='tool_output' if earlier_role=='tool' else 'model_output'
                if present and kind not in fact['occurrences']:
                    fail('first speaker omitted from chronology')
                if present and earlier_role==role and number<proof['line']:
                    fail('earlier occurrence omitted from chronology')


FOLLOWUP_TIERS = ('T0', 'T1', 'T2', 'T3-content', 'T3-name', 'T4')
USED_COLUMNS = ('instance_id', 'repair_run', 'repair_tier', 'repair_rule', 'patch_sha256',
                'v4_run', 'v4_tier', 'v4_rule', 'v4_suite_sha256')
SUPERSEDED_COLUMNS = ('instance_id', 'role', 'run', 'tier', 'used_run')
CACHE_CONTENT_RULES = {
    'masked-read-content', 'masked-read-listed-files', 'masked-read-archive-member-list',
}


def resolve_repair_run(source_run, frozen_sha256, candidate_hashes):
    """Honor exact provenance, otherwise require a unique byte-for-byte match."""
    matches = sorted(run for run, sha in candidate_hashes.items() if sha == frozen_sha256)
    if source_run in candidate_hashes:
        if source_run not in matches:
            fail('explicit repair provenance conflicts with frozen patch hash')
        return source_run, 'explicit-run-and-patch-sha256'
    if source_run not in (None, '', 'rerun'):
        fail('unknown explicit repair provenance')
    if len(matches) != 1:
        fail('frozen patch lacks a unique stored run hash match')
    return matches[0], 'unique-patch-sha256'


def split_t3(record):
    tier, _ = interpreted_tier(record['facts'])
    if tier != 'T3':
        return tier
    has_name = any(
        fact['category'] == 'answer' and fact['field'] == 'hidden_test_name'
        and fact['guard_pass'] and fact['first_seen_in'] == 'model_output'
        and not fact.get('defined_at_first_mention') for fact in record['facts']
    )
    return 'T3-name' if has_name else 'T3-content'


def used_run_tables(records, provenance):
    """Recompute rows and both table scopes from accepted role-specific facts."""
    observed = {
        (r['instance_id'], r['role'], r['run']): split_t3(r)
        for r in records if r['observed'] and not r['excluded']
    }
    comparable = {r['instance_id'] for r in records if r['comparable'] and not r['excluded']}
    cohort = {r['instance_id'] for r in records if not r['excluded']}
    if set(provenance) != comparable:
        fail('frozen phase 4 cohort differs from comparable task set')

    used, selections = [], {}
    for iid, proof in sorted(provenance.items()):
        repair, rule = resolve_repair_run(
            proof['source_run'], proof['patch_sha256'], proof['repair_patch_sha256s'],
        )
        if set(proof['repair_patch_sha256s']) != {
            run for task, role, run in observed if task == iid and role == 'repair'
        }:
            fail('repair candidate provenance coverage mismatch')
        sources = proof['reproduction_record_provenance']
        if not sources or any(p['patch_sha256'] != proof['patch_sha256'] for p in sources.values()):
            fail('V4 signal is not bound to frozen patch')
        suites = {p['suite_sha256'] for p in sources.values()}
        if len(suites) != 1:
            fail('V4 signal records disagree on suite hash')
        suite = suites.pop()
        candidates = proof['v4_suite_sha256s']
        matches = sorted(run for run, sha in candidates.items() if suite and sha == suite)
        if len(matches) > 1:
            fail('V4 suite has ambiguous stored run provenance')
        v4 = matches[0] if matches else ''
        v4_key = iid, 'generator', v4
        repair_key = iid, 'repair', repair
        if repair_key not in observed or (v4 and v4_key not in observed):
            fail('used-run trajectory lacks accepted tier evidence')
        selections[iid, 'repair'] = repair
        if v4:
            selections[iid, 'generator'] = v4
        used.append(dict(instance_id=iid, repair_run=repair, repair_tier=observed[repair_key],
                         repair_rule=rule, patch_sha256=proof['patch_sha256'], v4_run=v4,
                         v4_tier=observed.get(v4_key, 'Unobserved'),
                         v4_rule='unique-frozen-suite-sha256' if v4 else 'v4-provenance-unresolved',
                         v4_suite_sha256=suite or ''))

    superseded = [
        dict(instance_id=iid, role=role, run=run, tier=tier, used_run=selections[iid, role])
        for (iid, role, run), tier in sorted(observed.items())
        if (iid, role) in selections and run != selections[iid, role]
    ]

    def count(tiers):
        return {tier: tiers.count(tier) for tier in FOLLOWUP_TIERS}

    def scope(task_ids, selected):
        result = {}
        by_task = collections.defaultdict(list)
        for role in ('repair', 'generator'):
            grouped = collections.defaultdict(list)
            for (iid, kind, run), tier in observed.items():
                if iid in task_ids and kind == role and (not selected or selections.get((iid, kind)) == run):
                    grouped[iid].append(tier)
                    by_task[iid].append(tier)
            worst = [max(tiers, key=FOLLOWUP_TIERS.index) for tiers in grouped.values()]
            result[role] = dict(counts=count(worst), observed_tasks=len(worst),
                                unobserved_tasks=len(task_ids) - len(worst))
        result['any_role'] = {
            tier: sorted(iid for iid, tiers in by_task.items() if tier in tiers)
            for tier in ('T3-content', 'T3-name', 'T4')
        }
        result['highest_tier'] = count([max(tiers, key=FOLLOWUP_TIERS.index) for tiers in by_task.values()])
        return result

    cache = {}
    for run in sorted({r['run'] for r in records}):
        evidence = [(r['instance_id'], f) for r in records if r['run'] == run
                    for f in r['facts'] if f['category'] == 'cache']
        cache[run] = {
            'nonempty_return_observations': sum(f['rule'] in CACHE_CONTENT_RULES for _, f in evidence),
            'returned_source_tasks': sorted({iid for iid, f in evidence if f['rule'] == 'masked-read-content'}),
            'nonempty_return_tasks': sorted({iid for iid, f in evidence if f['rule'] in CACHE_CONTENT_RULES}),
            'paths': {path: dict(collections.Counter(f['rule'] for _, f in evidence if f['path'] == path))
                      for path in sorted({f['path'] for _, f in evidence})},
        }
    summary = dict(
        used_comparable=scope(comparable, True), all_runs_comparable=scope(comparable, False),
        all_runs_non_requests=scope(cohort, False), comparable_count=len(comparable),
        non_requests_count=len(cohort), superseded_rows=len(superseded), cache_observations=cache,
    )
    return used, superseded, summary


def verify_used_run_tiers(root):
    tiers = root / 'tiers'
    records = [read(p) for p in sorted((tiers / 'artifacts').glob('*/*/*.json'))]
    receipt = read(tiers / 'used_run_provenance.json')
    # Reproject only provenance fields from the named frozen inputs and stored runs.
    from audit_used_run_tiers import collect_provenance, collect_timeline, report_section

    if collect_provenance(Path(receipt['frozen_manifest']), records) != receipt:
        fail('used-run provenance does not match the stored sources')
    used, superseded, summary = used_run_tables(records, receipt['tasks'])
    for name, rows, columns in (
        ('used_run_tiers.csv', used, USED_COLUMNS),
        ('superseded_run_tiers.csv', superseded, SUPERSEDED_COLUMNS),
    ):
        with (tiers / name).open(newline='') as stream:
            table = csv.DictReader(stream)
            if tuple(table.fieldnames or ()) != columns or list(table) != rows:
                fail('used-run CSV mismatch: ' + name)
    if summary != read(tiers / 'used_run_summary.json'):
        fail('used-run tier table mismatch')
    timeline = collect_timeline(summary['cache_observations'])
    if timeline != read(tiers / 'cache_mask_timeline.json'):
        fail('cache mask timeline mismatch')
    report = (root / 'REPORT.md').read_text()
    if not report.startswith('# Leakage gaps audit\n\n' + report_section(summary, timeline)):
        fail('used-run report totals mismatch')
    return {'status': 'pass', 'comparable_tasks': len(used), 'superseded_rows': len(superseded)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-dir', type=Path, default=Path('reports/next_phases/leakage_gaps'))
    parser.add_argument('--tiers-only', action='store_true')
    args = parser.parse_args()
    result = {} if args.tiers_only else verify(args.report_dir)
    if (args.report_dir/'tiers/summary.json').is_file():
        result['interpretation'] = verify_tiers(args.report_dir)
    elif args.tiers_only:
        fail('interpretation results missing')
    if (args.report_dir / 'tiers' / 'used_run_provenance.json').is_file():
        result['used_runs'] = verify_used_run_tiers(args.report_dir)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
