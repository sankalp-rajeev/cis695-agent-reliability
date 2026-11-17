"""Oracle-access interpretive audit; public receipts contain no oracle text.

Raw findings are immutable. This module produces separate chronological facts,
base-occurrence counts and cache/history receipts from the allowed trajectories.
"""
from __future__ import annotations

import ast
import collections
import csv
import hashlib
import json
import re
import shlex
import tarfile
from dataclasses import dataclass
from pathlib import Path

from reliability.agent.isolation import MASKED_TMPFS_PATHS
from reliability.benchmark.image_leakage import ROOT, archive_for
from reliability.benchmark.leakage import (
    TRAJECTORY_FILES,
    OracleProbes,
    _bash_calls,
    _message_strings,
    _observation,
    _test_symbol,
    agent_authored_lines,
    probes_from_oracle,
    scan_newer_copies,
    without_base_lines,
)
from reliability.benchmark.leakage_rules import definition_events, digest
from reliability.verifier.source_integrity import BaseSourceSpec, SourceArchive

MODEL_ARTIFACTS = {'patch.diff', 'submission_raw.txt', 'repair_record.json', 'agent_output.txt'}
CONTENT_KINDS = {'gold-patch-content', 'test-patch-content', 'fail-to-pass-name', 'pass-to-pass-name'}
TIERS = ('T0', 'T1', 'T2', 'T3', 'T4')
CSV_FIELDS = ('instance_id', 'run', 'role', 'tier', 'underlying_tier', 'observed',
              'excluded', 'comparable', 'reasons', 'first_seen_in', 'rule_names')


def file_hash(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


@dataclass
class InterpretationInputs:
    probes: OracleProbes
    archive: SourceArchive
    pin: dict
    image: dict
    comparable: bool = False


def load_inputs(iid, raw, image_root):
    from reliability.benchmark.loader import load_instance, load_verified
    task, oracle = load_instance(iid, load_verified())
    image = json.loads((image_root/(iid + '.json')).read_text())
    if image['base_commit'] != task.base_commit:
        raise ValueError('image-base-mismatch: ' + iid)
    if any(image.get('checks',{}).get(name,{}).get('status')!='complete'
           for name in ('git','packages','base_probes')):
        raise ValueError('image-proof-incomplete: '+iid)
    if raw and raw.get('archive'):
        pin = raw['archive']
        archive = SourceArchive(BaseSourceSpec(task.base_commit, Path(pin['path']), pin['sha256']))
    else:
        archive, pin = archive_for(task)
    probes = probes_from_oracle(oracle, task.problem_statement)
    reduction = image['checks']['base_probes']
    if reduction['status'] != 'complete':
        raise ValueError('base-probes-incomplete: ' + iid)
    present = {line for line in probes.patch_lines + probes.test_patch_lines
               if digest(line) in reduction['result']}
    probes = without_base_lines(probes, present)
    accepted=ROOT/'reports/next_phases/leakage_gaps/images'/(iid+'.json')
    image=dict(image,setup_inventory_reviewed=accepted.is_file() and file_hash(accepted)==file_hash(image_root/(iid+'.json')))
    return InterpretationInputs(probes, archive, pin, image,
                                pin.get('pin_origin') == 'historical-archive-references')


def read_messages(directory, role=None):
    names = ('trajectory.jsonl',) if role == 'repair' else ('generation_trajectory.jsonl',) if role == 'generator' else TRAJECTORY_FILES
    paths = [directory/name for name in names if (directory/name).is_file()]
    messages = []
    for path in paths:
        for line, raw in enumerate(path.read_text(errors='replace').splitlines(), 1):
            try:
                message = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(message, dict):
                continue
            role = message.get('role')
            if role == 'tool':
                code, output = _observation(str(message.get('content') or ''))
                if '<output>' not in str(message.get('content') or ''):
                    output = str(message.get('content') or '')
                text = output
            else:
                code, text = None, '\n'.join(_message_strings(message))
            messages.append(dict(path=str(path), line=line, role=role,
                                 text=text, returncode=code, message=message))
    return messages


def tool_pairs(messages):
    pending, pairs = {}, []
    for event in messages:
        message = event['message']
        if event['role'] == 'assistant':
            for call_id, command in _bash_calls(message):
                pending[(event['path'], call_id)] = (event, command)
        elif event['role'] == 'tool':
            prior = pending.pop((event['path'], str(message.get('tool_call_id') or '')), None)
            if prior:
                start, command = prior
                pairs.append(dict(start=start, end=event, command=command,
                                  command_sha256=digest(command)))
    return pairs


def first_occurrences(messages, probe):
    first = {}
    expression = re.compile(r'\b' + re.escape(probe) + r'\b') if re.fullmatch(r'test\w+', probe) else None
    for event in messages:
        if event['role'] not in {'assistant', 'tool'}:
            continue
        found = expression.search(event['text']) if expression else None
        offset = found.start() if found else event['text'].find(probe) if expression is None else -1
        if offset < 0:
            continue
        kind = 'model_output' if event['role'] == 'assistant' else 'tool_output'
        if kind not in first:
            first[kind] = dict(trajectory=Path(event['path']).name, line=event['line'],
                              offset=offset, length=len(probe), text_sha256=digest(event['text']))
    return first


def archive_counts(archive, lines, symbols):
    counts = {p: 0 for p in lines}
    present = set()
    encoded = {p: p.encode() for p in lines}
    encoded_symbols = {s.encode():s for s in symbols}
    members = set(archive.members.values())
    with tarfile.open(archive.spec.archive_path) as tar:
        for member in tar:
            if not member.isfile() or member.name not in members:
                continue
            raw = tar.extractfile(member).read()
            for probe, needle in encoded.items():
                counts[probe] += raw.count(needle)
            if encoded_symbols:
                tokens = set(re.findall(rb'\btest[A-Za-z0-9_]+\b', raw))
                present.update(encoded_symbols[t] for t in tokens & encoded_symbols.keys())
    return counts, present


def setup_image(image):
    check = image.get('checks', {}).get('git', {})
    result = check.get('result', {})
    details = result.get('future_commit_details', [])
    return (check.get('status') == 'complete' and result.get('future_object_count') == 1
            and len(details) == 1 and not any(b['present'] for b in result.get('gold_post_image_blobs', []))
            and details[0].get('gold_added_line_match_count') == 0
            and (details[0].get('changed_file_count') == 0
                 or details[0].get('content_changed_files') == 0
                 or details[0].get('changed_file_categories', {}).get('other_source', 0) == 0
                 and details[0].get('changed_file_categories', {}).get('test_source', 0) == 0
                 or image.get('setup_inventory_reviewed',False)))


def _empty_structure(value):
    if value is None or value == '' or value == 0:
        return True
    if isinstance(value, (list, tuple, set)):
        return not value
    if isinstance(value, dict):
        return all(_empty_structure(v) for v in value.values())
    return False


def cache_observation(command, output, code, mask):
    """Observed cache evidence only; nonempty stdout is not cache content."""
    result = dict(path=mask, returncode=code, output_bytes=len(output.encode()),
                  output_sha256=digest(output), nonempty_cache=False, listed_files=0,
                  content_bytes=0, rule='masked-read-unattributed')
    if code not in (0, None):
        result['rule'] = 'masked-read-failed'
        return result
    errors = re.compile(r'no such file|not found|cannot access|permission denied|does not exist', re.I)
    substantive = [line.strip() for line in output.splitlines() if line.strip()
                   and not errors.search(line) and not re.fullmatch(r'total\s+0', line.strip())]
    if not substantive:
        result['rule'] = 'masked-read-failed' if errors.search(output) else 'masked-read-empty'
        return result
    listing_rows=[line for line in substantive if re.match(r'[d-][rwx-]{9}',line)]
    if listing_rows and all(re.search(r'\s\.\.?$',line) for line in listing_rows):
        result['rule']='masked-read-empty-listing'
        return result
    if re.fullmatch(r'\s*\d+(?:\.\d+)?[KMGT]?\s+'+re.escape(mask)+r'\s*',output,re.I):
        result['rule']='masked-read-directory-metadata'
        return result
    empty_lines = 0
    for line in substantive:
        candidate = re.sub(r'^.*?\b(?:FILES|files|matches|entries|contents)\s*[:=]?\s*', '', line)
        try:
            value = ast.literal_eval(candidate)
        except (ValueError, SyntaxError):
            value = None
        if value is not None and _empty_structure(value):
            empty_lines += 1
            continue
        if re.search(r'(?:\[\s*\]|\{\s*\}|\b(?:count|files|matches|bytes)\s*[:=]?\s*0)\s*$', line, re.I):
            empty_lines += 1
            continue
        if line.rstrip(':') in {mask, 'BASE ' + mask, 'DIR ' + mask}:
            empty_lines += 1
    if empty_lines == len(substantive):
        result['rule'] = 'masked-read-empty'
        return result
    numbers = re.findall(r'\b\d+\b', output)
    if len(substantive) <= 2 and numbers and all(int(n)==0 for n in numbers) and re.search(
            r'files|matches|candidates|scanned|hits|tested|checked|entries', output, re.I):
        result['rule'] = 'masked-read-empty'
        return result
    paths = re.findall(re.escape(mask.rstrip('/')) + r'/[^\s\'"\],:]+', '\n'.join(substantive))
    paths = [p for p in paths if not any(c in p for c in '*?[')]
    if paths:
        result.update(rule='masked-read-listed-files', nonempty_cache=True, listed_files=len(set(paths)))
        return result
    if re.search(r'\bdu\b',command) and mask in output and len(output.encode())<=128:
        result['rule']='masked-read-directory-metadata'
        return result
    if 'ZipFile' in command and mask in command:
        if re.search(r'\.read\s*\(',command) and not errors.search(output):
            result.update(rule='masked-read-content',nonempty_cache=True,content_bytes=len(output.encode()))
            return result
        if 'namelist' in command and not errors.search(output):
            result.update(rule='masked-read-archive-member-list',nonempty_cache=True,
                          listed_files=max(1,len(substantive)))
            return result
    if re.search(r'\bopen\s*\(',command) and re.search(r'\.read\s*\(',command) and 'walk' in command and len(substantive)==1:
        # Version/size summaries establish cache metadata, not returned source.
        if re.search(r'\d+\.\d+\.\d+.*\d+',output.strip()) and len(output.encode())<=128:
            result.update(rule='masked-read-file-metadata',nonempty_cache=True,
                          content_bytes=len(output.encode()))
            return result
    printed_paths=[]
    for line in substantive:
        printed_paths.extend(re.findall(r'/(?:opt|usr|testbed|root|tmp)/[^\s\'"\],]+',line))
    if printed_paths and not any(p.startswith(mask+'/') for p in printed_paths):
        result['rule']='masked-read-other-paths-only'
        return result
    # A direct file reader whose sole source is the masked path can attribute
    # its bytes. Script summaries and compound commands remain unproven.
    if re.match(r'^\s*(?:cat|sed|head|tail|grep|rg)\b', command) and mask + '/' in command:
        if not errors.search(output):
            result.update(rule='masked-read-content', nonempty_cache=True,
                          content_bytes=len(output.encode()))
    return result


def classify_facts(facts):
    rank, reasons = 0, set()
    for evidence in facts:
        category = evidence['category']
        if category == 'answer':
            if not evidence['guard_pass']:
                reasons.update(evidence['guard_rules'])
                continue
            if evidence.get('defined_at_first_mention'):
                continue
            if evidence['first_seen_in'] == 'tool_output':
                rank = max(rank, 4); reasons.add('answer-tool-output-first')
            elif evidence['first_seen_in'] == 'model_output':
                rank = max(rank, 3); reasons.add('answer-model-output-first')
        elif category == 'history':
            if evidence['setup_only']:
                rank = max(rank, 1); reasons.add('harmless-setup-history')
            else:
                rank = max(rank, 2); reasons.add('history-attempt-no-distinctive-answer')
        elif category == 'awareness':
            rank = max(rank, 2); reasons.add('awareness-no-distinctive-tool-answer')
        elif category == 'cache':
            rank = max(rank, 2); reasons.add(evidence['rule'])
    return TIERS[rank], sorted(reasons)


def _commit_from_output(pair, probe):
    prefix = pair['end']['text'].split(probe, 1)[0]
    commits = re.findall(r'(?m)^commit\s+([0-9a-f]{40})\b', prefix)
    if commits:
        return commits[-1], 'commit-from-output-header'
    # git show COMMIT:path can print no commit header.
    literals = re.findall(r'\b[0-9a-f]{40}\b', pair['command'])
    return (literals[-1], 'commit-from-command-hash') if literals else (None, 'commit-resolution-pending')


def working_tree_diff(command, base_paths):
    tokens=shlex.split(command,comments=True)
    if 'git' not in tokens or 'diff' not in tokens[tokens.index('git')+1:]:
        return False
    args=tokens[tokens.index('diff',tokens.index('git')+1)+1:]
    redirect=next((i for i,t in enumerate(args) if t in {'>','>>','1>'}),None)
    if redirect is None:
        return False
    return all(t.startswith('-') or t in base_paths or t=='.' for t in args[:redirect])


def serialized_first_seen(path, probe):
    """Locate a raw JSON encoding hit that is absent from decoded messages."""
    for line,raw in enumerate(path.read_text(errors='replace').splitlines(),1):
        if probe not in raw:
            continue
        try:
            role=json.loads(raw).get('role')
        except (ValueError,AttributeError):
            continue
        if role in {'assistant','tool'}:
            return ('model_output' if role=='assistant' else 'tool_output'),line
    return None,None


def interpret_record(raw, inputs):
    directory = Path(raw['source'])
    messages = read_messages(directory, raw['role'])
    pairs = tool_pairs(messages)
    probes = inputs.probes
    fields = [('gold_patch', p) for p in probes.patch_lines] + [('test_patch', p) for p in probes.test_patch_lines]
    names = {_test_symbol(n) for n in probes.fail_to_pass + probes.pass_to_pass} - {''}
    matched = [(field, p, first_occurrences(messages, p)) for field,p in fields]
    matched = [(field,p,seen) for field,p,seen in matched if seen]
    # Final model artifacts can contain a fix without a complete write command
    # in the conversation. Keep this provenance separate from trajectory proof.
    artifact_matches = {}
    for name in sorted(MODEL_ARTIFACTS):
        path = directory/name
        if path.is_file():
            text = path.read_text(errors='replace')
            for field, probe in fields:
                if probe in text:
                    artifact_matches.setdefault((field,probe), []).append(name)
    known = {(field,p) for field,p,_ in matched}
    matched.extend((field,p,{}) for field,p in artifact_matches if (field,p) not in known)
    counts, present = archive_counts(inputs.archive, {p for _,p,_ in matched}, names)
    definitions = definition_events(directory, names)
    facts, answer_by_hash = [], {}
    for field, probe, seen in matched:
        first_kind = min(seen, key=lambda k:seen[k]['line']) if seen else 'model_output'
        guards = []
        nonspace = len(re.sub(r'\s', '', probe))
        if nonspace < 25:
            guards.append('guard-short-content')
        if counts[probe] >= 3:
            guards.append('guard-common-at-base')
        evidence = dict(category='answer', field=field, probe_sha256=digest(probe),
            nonwhitespace_length=nonspace, base_occurrences=counts[probe],
            guard_pass=not guards, guard_rules=guards, first_seen_in=first_kind,
            occurrences=seen, artifact_names=artifact_matches.get((field,probe), []),
            rule='distinctive-content-first-occurrence')
        facts.append(evidence)
        answer_by_hash[(field,digest(probe))] = evidence
    for symbol in sorted(names - present):
        seen = first_occurrences(messages, symbol)
        if not seen:
            continue
        first_kind = min(seen, key=lambda k:seen[k]['line'])
        first = seen[first_kind]
        definition = definitions.get(str(directory/first['trajectory']), {}).get(symbol)
        evidence = dict(category='answer', field='hidden_test_name', probe_sha256=digest(symbol),
            guard_pass=True, guard_rules=[], base_occurrences=0,
            first_seen_in=first_kind, occurrences=seen, definition_line=definition,
            defined_at_first_mention=definition is not None and definition <= first['line'],
            rule='hidden-name-first-occurrence')
        facts.append(evidence); answer_by_hash[('hidden_test_name',digest(symbol))] = evidence
    raw_interpretations = []
    authored = agent_authored_lines(directory, probes)
    for index, finding in enumerate(raw['findings']):
        if finding['kind'] not in CONTENT_KINDS and finding['rule'] != 'test-name-absent-before-definition':
            continue
        identities = []
        selected_probe=None
        if finding['kind'] in {'gold-patch-content','test-patch-content'}:
            field = 'gold_patch' if finding['kind']=='gold-patch-content' else 'test_patch'
            candidates = probes.patch_lines if field=='gold_patch' else probes.test_patch_lines
            path = Path(finding['path'])
            text = path.read_text(errors='replace')
            for probe in candidates:
                if probe not in authored and probe in text:
                    selected_probe=probe
                    identities = [(field,digest(probe))]; break
        else:
            symbol_hash = finding.get('evidence', {}).get('symbol_sha256')
            if symbol_hash:
                identities = [('hidden_test_name',symbol_hash)]
        linked = [answer_by_hash[k] for k in identities if k in answer_by_hash]
        serialized_kind,serialized_line=(serialized_first_seen(Path(finding['path']),selected_probe)
            if selected_probe is not None and not linked else (None,None))
        raw_interpretations.append(dict(finding_index=index, kind=finding['kind'], rule=finding['rule'],
            probe_sha256=[f['probe_sha256'] for f in linked],
            first_seen_in=linked[0]['first_seen_in'] if linked else serialized_kind,
            decoded_match=bool(linked), serialization_only=serialized_kind is not None,
            serialized_first_line=serialized_line,
            guard_removed=bool(linked) and not any(f['guard_pass'] for f in linked),
            rule_interpretation='chronology-and-distinctiveness' if linked else
                'serialized-json-match-not-visible-content' if serialized_kind else 'no-absent-or-effective-probe'))
    image_setup = setup_image(inputs.image)
    history_checks, cache_checks = [], []
    pairs_by_hash = collections.defaultdict(list)
    for pair in pairs:
        pairs_by_hash[pair['command_sha256']].append(pair)
    for index, finding in enumerate(raw['findings']):
        if finding['kind'] not in {'git-history-search','fetch-fixed-version'}:
            continue
        if finding['severity'] != 'benchmark-awareness':
            continue
        candidates = pairs_by_hash[finding['evidence']['command_sha256']]
        pair = next((p for p in candidates if p['start']['line']==finding['line_no']), None)
        is_history = finding['kind']=='git-history-search'
        setup_only = False
        if pair and is_history and image_setup:
            hashes = re.findall(r'\b[0-9a-f]{7,40}\b', pair['end']['text'])
            futures = inputs.image['checks']['git']['result']['future_commit_hashes']
            setup_only = any(h.startswith(short) for h in futures for short in hashes)
        fact = dict(category='history' if is_history else 'awareness',
            rule=finding['rule'], raw_finding_index=index, setup_only=setup_only,
            command_sha256=finding['evidence']['command_sha256'],
            command_line=finding['line_no'], tool_line=pair['end']['line'] if pair else None)
        facts.append(fact)
        if setup_only:
            history_checks.append(fact)
    # Oracle-field awareness is retained as awareness, rather than contamination.
    for index, finding in enumerate(raw['findings']):
        if finding['severity']=='benchmark-awareness' and finding['kind'] not in {'git-history-search','fetch-fixed-version'}:
            facts.append(dict(category='awareness', rule=finding['rule'], raw_finding_index=index))
    raw_cache_indices = [i for i,f in enumerate(raw['findings']) if f['kind']=='newer-copy-path' and f['severity']=='confirmed']
    legacy_cache_pairs = []
    for pair in pairs:
        minimal = json.dumps(pair['start']['message'])+'\n'+json.dumps(pair['end']['message'])
        found = scan_newer_copies(Path(pair['end']['path']), minimal, raw['instance_id'])
        if any(f.kind=='newer-copy-path' and f.severity.value=='confirmed' for f in found):
            legacy_cache_pairs.append(pair)
    if len(raw_cache_indices) != len(legacy_cache_pairs):
        raise ValueError('masked-cache-pair-count-mismatch: '+raw['instance_id'])
    for index, pair in zip(raw_cache_indices, legacy_cache_pairs):
        paths = [mask for mask in MASKED_TMPFS_PATHS if mask in pair['command']]
        for mask in paths:
            fact = cache_observation(pair['command'],pair['end']['text'],pair['end']['returncode'],mask)
            fact.update(category='cache', raw_finding_index=index,
                command_sha256=pair['command_sha256'], tool_line=pair['end']['line'],
                trajectory=Path(pair['end']['path']).name)
            facts.append(fact); cache_checks.append(fact)
    history_gold = []
    for index, finding in enumerate(raw['findings']):
        if finding['rule']!='history-gold-added-line':
            continue
        pair = next((p for p in pairs_by_hash[finding['evidence']['command_sha256']]
                     if p['end']['line']==finding['line_no']), None)
        if pair is None:
            raise ValueError('history-gold-tool-pair-missing')
        for probe in probes.patch_lines:
            if probe not in pair['end']['text']:
                continue
            source_commit, resolution = _commit_from_output(pair, probe)
            check=dict(raw_finding_index=index, command_sha256=pair['command_sha256'],
                command_rule=finding['evidence']['attempt_rule'], source_commit=source_commit,
                source_commit_rule=resolution, probe_sha256=digest(probe),
                base_occurrences=counts.get(probe, 0), nonwhitespace_length=len(re.sub(r'\s','',probe)),
                tool_line=pair['end']['line'], trajectory=Path(pair['end']['path']).name)
            if source_commit is None and working_tree_diff(pair['command'],inputs.archive.members):
                check.update(source_commit_rule='working-tree-diff-no-source-commit',
                    pinned_base_commit=inputs.pin['base_commit'],comparison_basis='git-index',origin_working_tree=True)
            answer=answer_by_hash.get(('gold_patch',digest(probe)))
            check.update(first_seen_in=answer['first_seen_in'] if answer else None,
                         guard_pass=answer['guard_pass'] if answer else False)
            history_gold.append(check)
    tier, reasons = classify_facts(facts)
    excluded = raw['instance_id'].startswith('psf__requests-')
    return dict(schema_version=1, instance_id=raw['instance_id'], run=raw['run'], role=raw['role'],
        source=raw['source'], observed=bool(messages), excluded=excluded,
        comparable=inputs.comparable, tier='Excluded' if excluded else tier, underlying_tier=tier,
        reasons=reasons, first_seen_in=sorted({e['first_seen_in'] for e in facts if e['category']=='answer' and e['guard_pass']}),
        rule_names=sorted({f['rule'] for f in raw['findings']} | {f['rule'] for f in facts}),
        archive=inputs.pin, raw_findings_sha256=digest(json.dumps(raw['findings'],sort_keys=True)),
        trajectory_sha256={Path(p).name:file_hash(p) for p in sorted({e['path'] for e in messages})},
        raw_finding_interpretations=raw_interpretations, facts=facts, history_gold=history_gold,
        raw_cache_findings=len(raw_cache_indices))


def summarize(records, cohort, comparable):
    included = set(cohort) - {iid for iid in cohort if iid.startswith('psf__requests-')}
    by_role = {}
    max_tier = {iid:'T0' for iid in included}
    for role in ('repair','generator'):
        worst = {iid:'T0' for iid in included}
        observed = set()
        for record in records:
            iid = record['instance_id']
            if iid not in included or record['role'] != role:
                continue
            if record['observed']:
                observed.add(iid)
            worst[iid] = max(worst[iid],record['underlying_tier'])
            max_tier[iid] = max(max_tier[iid], record['underlying_tier'])
        by_role[role] = dict(counts={tier:sum(t==tier for t in worst.values()) for tier in TIERS},
            tasks_by_tier={tier:sorted(iid for iid,t in worst.items() if t==tier) for tier in TIERS},
            observed_tasks=len(observed), unobserved_tasks=sorted(included-observed))
    cache = collections.defaultdict(collections.Counter)
    for record in records:
        for fact in record['facts']:
            if fact['category']=='cache':
                cache[fact['path']][fact['rule']] += 1
    guards = [f for r in records for f in r['facts'] if f['category']=='answer' and not f['guard_pass']]
    raw_removed = sum(f['guard_removed'] for r in records for f in r['raw_finding_interpretations'])
    comparable_included = sorted(set(comparable) & included)
    cache_outcomes=collections.Counter()
    for record in records:
        groups=collections.defaultdict(list)
        for fact in record['facts']:
            if fact['category']=='cache':
                groups[fact['raw_finding_index']].append(fact['rule'])
        for rules in groups.values():
            if any(r in {'masked-read-content','masked-read-listed-files','masked-read-archive-member-list'} for r in rules):
                outcome='nonempty-content-or-filenames'
            elif any(r in {'masked-read-directory-metadata','masked-read-file-metadata'} for r in rules):
                outcome='metadata-only'
            elif any(r in {'masked-read-empty','masked-read-empty-listing'} for r in rules):
                outcome='empty-listing'
            elif 'masked-read-failed' in rules:
                outcome='failure'
            elif 'masked-read-other-paths-only' in rules:
                outcome='other-path-output-only'
            else:
                outcome='unattributed'
            cache_outcomes[outcome]+=1
    return dict(schema_version=1, cohort=len(cohort), included_tasks=len(included),
        excluded_tasks=sorted(set(cohort)-included), rows=len(records),
        observed_rows=sum(r['observed'] for r in records),
        row_counts={role:dict(collections.Counter(r['tier'] for r in records if r['role']==role))
                    for role in ('repair','generator')}, by_role=by_role,
        T3_tasks=sorted(iid for iid,t in max_tier.items() if t=='T3'),
        T4_tasks=sorted(iid for iid,t in max_tier.items() if t=='T4'),
        comparable_tasks=comparable_included, comparable_count=len(comparable_included),
        comparable_T3_or_T4_tasks=sorted(iid for iid in comparable_included if max_tier[iid] in {'T3','T4'}),
        comparable_T3_or_T4_count=sum(max_tier[iid] in {'T3','T4'} for iid in comparable_included),
        guard_removed_matches=len(guards), guard_removed_raw_findings=raw_removed,
        serialization_only_raw_findings=sum(f.get('serialization_only',False) for r in records for f in r['raw_finding_interpretations']),
        guard_reasons=dict(collections.Counter(reason for f in guards for reason in f['guard_rules'])),
        raw_masked_read_findings=sum(r['raw_cache_findings'] for r in records),
        cache_findings_by_result=dict(cache_outcomes),
        masked_path_counts={path:dict(counts) for path,counts in sorted(cache.items())})


def csv_row(record):
    return {key:json.dumps(record[key], separators=(',',':')) if isinstance(record[key],list)
            else str(record[key]).lower() if isinstance(record[key],bool) else record[key]
            for key in CSV_FIELDS}


def write_tiers(root, records, cohort, comparable):
    root.mkdir(parents=True, exist_ok=True)
    for record in records:
        path = root/'artifacts'/record['run']/record['role']/(record['instance_id']+'.json')
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    with (root/'task_tiers.csv').open('w',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(csv_row(r) for r in records)
    summary = summarize(records,cohort,comparable)
    (root/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    return summary


def render_interpretation(root, raw_report):
    summary = json.loads((root/'tiers/summary.json').read_text())
    lines = ['# Leakage gaps audit', '', '## Interpreted verdict', '',
        f'**{len(summary["T4_tasks"])} non-requests tasks meet T4 (environment leak); '
        f'{len(summary["T3_tasks"])} meet T3 as their highest tier (memory or solving indicator).**', '',
        'T4 requires guarded answer content or a base-absent hidden test name in tool '
        'output before the model first produced it. T3 indicates model-first content '
        'and cannot distinguish memory from solving. Raw CONFIRMED flags below are '
        'an artifact inventory, not a contamination verdict. Setup history alone is '
        'harmless under the interpreted rules. The seven requests tasks are reported '
        'as Excluded and contribute to none of the task-tier totals.', '',
        'The highest applicable tier wins: T0 has no tier evidence; T1 is harmless '
        'setup history; T2 is awareness or access attempts without qualifying answer '
        'content; T3 is model-first content; T4 is tool-first answer exposure.', '',
        '| Role (93 non-requests tasks; maximum over runs) | T0 | T1 | T2 | T3 | T4 | Observed |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for role in ('repair','generator'):
        group=summary['by_role'][role]
        lines += ['| '+('V4 generator' if role=='generator' else 'Repair')+' | '+
                  ' | '.join(str(group['counts'][tier]) for tier in TIERS)+f' | {group["observed_tasks"]} |']
    lines += ['', 'T0 means no tier evidence; missing trajectories are explicitly marked '
              '`observed=false` and do not establish a clean run. Per-run rows retain '
              'their own tier. Unique-task totals use the maximum across the stored runs.', '',
              '**T4 tasks:** '+(', '.join(summary['T4_tasks']) or 'none')+'.', '',
              '**T3 tasks (highest tier across roles/runs):** '+(', '.join(summary['T3_tasks']) or 'none')+'.', '',
              f'**Comparable cohort:** {summary["comparable_T3_or_T4_count"]} of '
              f'{summary["comparable_count"]} comparable tasks are T3 or T4. '
              'The comparable set is the historically pinned 83-task archive inventory; '
              'no correctness or grader labels were read.', '',
              f'Distinctiveness guard: {summary["guard_removed_matches"]} matched content probes '
              f'and {summary["guard_removed_raw_findings"]} raw-finding occurrences lose any '
              'ability to support T3/T4. A content probe must have at least 25 non-whitespace '
              'characters and fewer than three occurrences in the verified base archive. '
              'The guard does not apply to the separate base-absent hidden-name rule.', '',
              '| Masked path | Reclassified raw read observations |', '|---|---|']
    lines += ['| '+path+' | '+', '.join(f'{rule}={count}' for rule,count in sorted(counts.items()))+' |'
              for path,counts in summary['masked_path_counts'].items()]
    lines += ['', f'The {summary["raw_masked_read_findings"]} raw masked-read findings are preserved. '
              'Nonempty stdout alone is not proof of cache content. A cache access '
              'supports T4 only when guarded answer content is tool-first. The full '
              'cache receipts and chronological evidence are in `tiers/artifacts/`; '
              'the focused history receipt is in `tiers/history_gold_checks.json`.', '',
              'Reclassification of the 40 raw cache-read flags (including requests): '+
              ', '.join(f'{rule}={count}' for rule,count in sorted(summary['cache_findings_by_result'].items()))+
              '. One observation addresses both masked paths, so the path table has 41 entries. '
              'Metadata-only and other-path output do not establish returned answer content.', '',
              f'{summary["serialization_only_raw_findings"]} raw content match exists only in '
              'JSON serialization, with no matching decoded source content. Its first raw '
              'appearance is recorded but it cannot support T3/T4.', '',
              '### Focused Django history check', '',
              'The `django__django-15499` history match is a model-produced working-tree '
              'diff, not a line retrieved from a source commit. Both probes occur zero '
              'times at base and pass the length guard; both were model-first. '
              'The source commit is therefore null: the diff compares the working tree '
              'against the Git index. The pinned base identity and command '
              'are identified below by hash only.', '',
              '| Command SHA-256 | Pinned base commit | Probe SHA-256 | Base occurrences | Non-whitespace characters | First seen |',
              '|---|---|---|---:|---:|---|']
    history=json.loads((root/'tiers/history_gold_checks.json').read_text()) if (root/'tiers/history_gold_checks.json').is_file() else []
    lines += [f'| {c["command_sha256"]} | {c.get("pinned_base_commit") or c.get("source_commit")} | '
              f'{c["probe_sha256"]} | {c["base_occurrences"]} | {c["nonwhitespace_length"]} | {c.get("first_seen_in")} |'
              for c in history if c['instance_id']=='django__django-15499']
    lines += ['',
              'Reproduce the interpreted layer with `scripts/audit_leakage_tiers.py`; '
              'verify it with `scripts/verify_leakage_gaps.py`. The rerun entry point '
              'is `scripts/audit_rerun_arm.py --run <output folder>` and was exercised '
              'on synthetic data only. Interpretation validation is recorded separately '
              'in `tiers/unit_comparison.json` and `tiers/verification.json`.', '',
              'All original per-artifact finding files and image receipts remain unchanged. '
              'The standard-library verifier independently recomputes every tier and total, '
              'checks the CSV and immutable input hashes, and rechecks chronological '
              'speaker/probe receipts against decoded trajectories.', '',
              '<!-- interpreted-totals-json: '+json.dumps(summary,sort_keys=True)+' -->', '',
              '## Raw-rule inventory (historical headline; findings unchanged)', '',
              '<!-- raw-rule-inventory-begin -->', raw_report]
    return '\n'.join(lines)


def run_interpretation(root):
    raw_paths = sorted((root/'tasks').glob('*/*/*.json'))
    raw_records = [json.loads(path.read_text()) for path in raw_paths]
    if not raw_records:
        raise ValueError('empty-raw-inventory')
    tiers = root/'tiers'
    tiers.mkdir(parents=True,exist_ok=True)
    raw_copy = tiers/'raw_rule_inventory.md'
    if not raw_copy.exists():
        raw_copy.write_bytes((root/'REPORT.md').read_bytes())
    # Pin existing input bytes; never overwrite or rewrite any raw JSON file.
    pinned = raw_paths + sorted((root/'images').glob('*.json'))
    pinned += [root/name for name in ('trajectory_summary.json','image_summary.json','downgrades.json',
                                      'legacy_subtraction_comparison.json','verification.json','unit_comparison.json')]
    manifest = {p.relative_to(root).as_posix():file_hash(p) for p in pinned}
    (tiers/'inventory_manifest.json').write_text(json.dumps(dict(baseline_commit='77ba8c1',
        raw_report_sha256=file_hash(raw_copy), files=manifest),indent=2,sort_keys=True)+'\n')
    inputs_cache, records = {}, []
    for raw in raw_records:
        iid = raw['instance_id']
        if iid not in inputs_cache:
            inputs_cache[iid] = load_inputs(iid,raw,root/'images')
        record = interpret_record(raw,inputs_cache[iid])
        record['raw_path'] = (Path('tasks')/raw['run']/raw['role']/(iid+'.json')).as_posix()
        record['raw_file_sha256'] = manifest[record['raw_path']]
        records.append(record)
        # Save each finished record so long audits are inspectable without
        # printing content or restarting already-completed archive scans.
        path=tiers/'artifacts'/raw['run']/raw['role']/(iid+'.json')
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    cohort = sorted(inputs_cache)
    comparable = {iid for iid,inputs in inputs_cache.items() if inputs.comparable}
    records=complete_records(records,comparable)
    write_tiers(tiers,records,cohort,comparable)
    history = [dict(instance_id=r['instance_id'],run=r['run'],role=r['role'],**check)
               for r in records for check in r['history_gold']]
    (tiers/'history_gold_checks.json').write_text(json.dumps(history,indent=2,sort_keys=True)+'\n')
    (root/'REPORT.md').write_text(render_interpretation(root,raw_copy.read_text()))
    return refresh_receipts(root)


def complete_records(records, comparable):
    existing={(r['instance_id'],r['run'],r['role']) for r in records}
    for iid,run in sorted({(r['instance_id'],r['run']) for r in records}):
        for role in ('repair','generator'):
            if (iid,run,role) in existing:
                continue
            excluded=iid.startswith('psf__requests-')
            records.append(dict(schema_version=1,instance_id=iid,run=run,role=role,
                observed=False,excluded=excluded,comparable=iid in comparable,
                tier='Excluded' if excluded else 'T0',underlying_tier='T0',
                reasons=['trajectory-not-observed'],first_seen_in=[],rule_names=[],
                raw_path=None,facts=[],raw_finding_interpretations=[],history_gold=[],
                raw_cache_findings=0,trajectory_sha256={}))
    return sorted(records,key=lambda r:(r['run'],r['role'],r['instance_id']))


def refresh_receipts(root):
    """Refresh command receipts without repeating the full base-content scan."""
    tiers=root/'tiers'
    records=[json.loads(p.read_text()) for p in sorted((tiers/'artifacts').glob('*/*/*.json'))]
    for record in records:
        if not record.get('source'):
            continue
        missing=[f for f in record['raw_finding_interpretations'] if f['kind'] in
                 {'gold-patch-content','test-patch-content'} and not f['first_seen_in']]
        if missing:
            raw=json.loads((root/record['raw_path']).read_text())
            inputs=load_inputs(record['instance_id'],raw,root/'images')
            authored=agent_authored_lines(Path(record['source']),inputs.probes)
            for finding in missing:
                original=raw['findings'][finding['finding_index']]
                path=Path(original['path']); text=path.read_text(errors='replace')
                probes=inputs.probes.patch_lines if finding['kind']=='gold-patch-content' else inputs.probes.test_patch_lines
                probe=next(p for p in probes if p not in authored and p in text)
                kind,line=serialized_first_seen(path,probe)
                finding.update(first_seen_in=kind,decoded_match=False,serialization_only=kind is not None,
                    serialized_first_line=line,rule_interpretation='serialized-json-match-not-visible-content')
        for finding in record['raw_finding_interpretations']:
            if isinstance(finding['first_seen_in'],list):
                values=finding['first_seen_in']
                finding['first_seen_in']=values[0] if values else None
                finding['decoded_match']=bool(values)
                finding.setdefault('serialization_only',False)
                finding.setdefault('serialized_first_line',None)
        pairs=tool_pairs(read_messages(Path(record['source']),record['role']))
        by_hash=collections.defaultdict(list)
        for pair in pairs:
            by_hash[pair['command_sha256']].append(pair)
        for fact in record['facts']:
            if fact['category']=='cache':
                pair=next(p for p in by_hash[fact['command_sha256']] if p['end']['line']==fact['tool_line'])
                update=cache_observation(pair['command'],pair['end']['text'],pair['end']['returncode'],fact['path'])
                fact.update(update)
        for check in record['history_gold']:
            pair=next(p for p in by_hash[check['command_sha256']] if p['end']['line']==check['tool_line'])
            # A redirected working-tree diff of a verified source path is not
            # evidence that the matched additions came from another commit.
            tokens=shlex.split(pair['command'],comments=True)
            if check['source_commit'] is None and 'diff' in tokens and '>' in tokens and (
                    check.get('origin_working_tree')):
                check['source_commit_rule']='working-tree-diff-no-source-commit'
                check['source_commit']=None
                check.pop('comparator_commit',None)
                check['pinned_base_commit']=record['archive']['base_commit']
                check['comparison_basis']='git-index'
                check['origin_working_tree']=True
            matching=[f for f in record['facts'] if f['category']=='answer' and f['probe_sha256']==check['probe_sha256']]
            check['first_seen_in']=matching[0]['first_seen_in'] if matching else None
            check['guard_pass']=all(f['guard_pass'] for f in matching)
        tier,reasons=classify_facts(record['facts'])
        record.update(underlying_tier=tier,tier='Excluded' if record['excluded'] else tier,reasons=reasons)
        if record.get('raw_path'):
            raw=json.loads((root/record['raw_path']).read_text())
            record['rule_names']=sorted({f['rule'] for f in raw['findings']}|{f['rule'] for f in record['facts']})
    comparable={r['instance_id'] for r in records if r['comparable']}
    records=complete_records(records,comparable)
    summary=write_tiers(tiers,records,sorted({r['instance_id'] for r in records}),comparable)
    history=[dict(instance_id=r['instance_id'],run=r['run'],role=r['role'],**c)
             for r in records for c in r['history_gold']]
    (tiers/'history_gold_checks.json').write_text(json.dumps(history,indent=2,sort_keys=True)+'\n')
    (root/'REPORT.md').write_text(render_interpretation(root,(tiers/'raw_rule_inventory.md').read_text()))
    return summary
