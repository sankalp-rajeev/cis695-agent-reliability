#!/usr/bin/env python3
"""Read-only Fix 0 signature inventory of the 3,683 Phase 2 selected slots."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re

ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
EXCEPTION = re.compile(r'^(?:E\s+)?((?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*(?:Error|Exception):.*)$')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def django_label(test):
    parts = test.split('::')
    module = parts[0][:-3].replace('/', '.')
    if module.startswith('tests.'):
        module = module[6:]
    return '.'.join([module] + parts[1:])


def normalize(signature, section):
    signature = re.sub(r'0x[0-9a-fA-F]+', '<address>', signature)
    signature = re.sub(r'(?<=TypeError: )[\w.]+(?=\(\) missing \d+ required positional argument)', '<callable>', signature)
    if 'unittest/loader.py' in section:
        signature = re.sub(r"AttributeError: type object '[^']+' has no attribute '[^']+'", 'AttributeError: selected class has no such attribute', signature)
    if 'unittest/loader.py' in section:
        signature = re.sub(r"AttributeError: module '[^']+' has no attribute '[^']+'", 'AttributeError: selected module has no such attribute', signature)
    if 'ERROR: not found:' in signature:
        signature = 'pytest usage error: selected ID not found (without a more specific captured exception)'
    return signature


def decision(signature, section):
    if 'missing 1 required positional argument:' in signature or 'property object' in signature or signature.startswith('pytest usage error:'):
        return 'executor-fixable', 'Malformed/non-collectable standalone label or callable invocation; native collection/orchestration must preserve the missing request, not infer PASS.'
    if signature.startswith('AttributeError: selected') and 'unittest/loader.py' in section:
        return 'executor-fixable', 'unittest loader resolves a selected class/module attribute that does not exist at that path.'
    if "FileNotFoundError: [Errno 2] No such file or directory: 'test.txt'" == signature:
        return 'environmental', 'A Pylint functional lint-input module opens test.txt at import; this missing filesystem precondition is not a parser repair. Do not fabricate the file or infer PASS.'
    if 'No module named' in signature or 'FileNotFoundError:' in signature or 'UnicodeEncodeError:' in signature or "unexpected keyword argument 'warn'" in signature or 'URLError:' in signature:
        return 'environmental', 'Captured missing dependency/tool, encoding, network or installed-library API condition; no parser-only repair is asserted.'
    return 'genuine test-module error', 'An exception remains in the actual selected test/module/fixture; preserve ERROR and investigate its captured frame rather than treating it as an admission gap.'


def run(args):
    assert not args.output.exists()
    report = args.report
    manifest = json.loads((report/'input_manifest.json').read_text())['input_sha256']
    hashes = {str(report/'input_manifest.json'):sha((report/'input_manifest.json').read_bytes())}
    path = report/'selected_gap_attribution.csv'
    hashes[str(path)] = sha(path.read_bytes())
    with path.open(newline='') as stream:
        gaps = [r for r in csv.DictReader(stream) if r['scope']=='initial' and r['cause'] in ('collection_or_runner_error','collection_or_test_error')]
    assert len(gaps)==3683
    captures, native_cache = {}, {}
    rows = []
    for gap in gaps:
        capture = Path(gap['evidence_path'])
        if capture not in captures:
            data = capture.read_bytes()
            assert sha(data)==manifest[str(capture)]
            hashes[str(capture)] = sha(data)
            captures[capture] = data
        data = captures[capture]
        native_path = capture.parents[2]/'result.json'
        if native_path not in native_cache:
            raw = native_path.read_bytes()
            assert sha(raw)==manifest[str(native_path)]
            hashes[str(native_path)] = sha(raw)
            native_cache[native_path] = json.loads(raw)
        native = native_cache[native_path]
        call = next(c for c in native['calls'] if c['run']['evidence_files']['runner.raw']==str(capture))
        events = call['run']['events']
        target = django_label(gap['test_id']) if native.get('runner',{}).get('name')=='django' or gap['instance_id'].startswith('django__') else gap['test_id']
        segments = []
        for i,start in enumerate(events):
            if start.get('event')!='start' or target not in start.get('ids',[]):continue
            end = next((e for e in events[i+1:] if e.get('event')=='end' and e.get('batch')==start['batch']),None)
            if end is not None and not end.get('split'):
                begin,finish=start.get('offset',0),end.get('offset',len(data))
                segments.append((data[:begin].count(b'\n')+1,ANSI.sub('',data[begin:finish].decode('utf-8','replace'))))
        assert len(segments)==1,(gap['instance_id'],gap['test_id'],len(segments))
        first, text = segments[0]
        lines = text.splitlines()
        if gap['cause']=='collection_or_test_error':
            sections=[]
            headings=[i for i,line in enumerate(lines) if re.match(r'^(?:ERROR|FAIL): ',line) or re.match(r'^_{3,}.*_{3,}$',line)]
            for j,start in enumerate(headings):
                end=headings[j+1] if j+1<len(headings) else len(lines)
                header=lines[start]
                score=0
                match=re.match(r'ERROR: (\w+) \(([^)]+)\)',header)
                if match:
                    name,label=match.groups()
                    label=label if label.endswith('.'+name) else label+'.'+name
                    if label==target:score=100
                    elif label.rsplit('.',1)[0]==target.rsplit('.',1)[0] and name in ('setUpClass','tearDownClass'):score=90
                    elif 'unittest.loader._FailedTest.' in label and name in gap['test_id'].split('::')[1:]:score=80
                elif gap['test_id'].split('::')[-1].split('[',1)[0] in header:
                    score=70
                if score:sections.append((score,first+start,'\n'.join(lines[start:end])))
            assert sections,(gap['instance_id'],gap['test_id'],'no matching traceback section')
            score,first,text=max(sections,key=lambda s:s[0])
            lines=text.splitlines()
        exceptions=[]
        for offset,line in enumerate(lines):
            match=EXCEPTION.match(line.strip())
            if match:exceptions.append((match.group(1),first+offset))
        if exceptions:
            # The terminal exception is the final cause; chained exceptions
            # and pytest's contextual source display are not separate slots.
            signature,line=exceptions[-1]
        else:
            candidates=[(s,first+i)for i,s in enumerate(lines)if 'ERROR: not found:'in s]
            assert candidates,(gap['instance_id'],gap['test_id'],'no captured exception or usage signature')
            signature,line=candidates[0]
        signature=normalize(signature,text)
        verdict,rationale=decision(signature,text)
        rows.append({'instance_id':gap['instance_id'],'tree':gap['tree'],'selected_test_id':gap['test_id'],
            'signature':signature,'decision':verdict,'rationale':rationale,
            'evidence_path':str(capture),'line':line,'evidence_path:line':str(capture)+':'+str(line)})
    groups=[]
    for signature in sorted({r['signature']for r in rows}):
        relevant=[r for r in rows if r['signature']==signature]
        assert len({r['decision']for r in relevant})==1,signature
        groups.append({'signature':signature,'tasks':len({r['instance_id']for r in relevant}),
            'slots':len(relevant),'decision':relevant[0]['decision'],'rationale':relevant[0]['rationale'],
            'example_capture_path:line':relevant[0]['evidence_path:line']})
    groups.sort(key=lambda r:(-r['slots'],r['signature']))
    args.output.mkdir(parents=True)
    for name,values in [('fix0_slots.csv',rows),('fix0_all_signatures.csv',groups),('fix0_top10.csv',groups[:10])]:
        with (args.output/name).open('x',newline='')as stream:
            writer=csv.DictWriter(stream,fieldnames=list(values[0]),lineterminator='\n')
            writer.writeheader();writer.writerows(values)
    (args.output/'fix0_manifest.json').write_text(json.dumps({'script_sha256':sha(Path(__file__).read_bytes()),
        'input_sha256':hashes,'selected_slots':len(rows),'tasks':len({r['instance_id']for r in rows}),
        'signature_count':len(groups),'normalization':'callable names in missing-argument TypeError, memory addresses and selected missing attributes; dependency and argument names retained',
        'decision_slots':dict(Counter(r['decision']for r in rows)),'Docker_calls':0},indent=2,sort_keys=True)+'\n')
    print(json.dumps(groups[:10],indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args())
