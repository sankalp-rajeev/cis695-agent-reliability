"""Narrow deterministic shadow prototype. No filesystem, model or oracle inputs.

Deliberately recognizes only a single string-valued configuration-field change.
Other behavior changes abstain; this is not a general assertion interpreter.
"""
import ast
import re

ALLOWLIST = frozenset({'issue', 'candidate_patch', 'test_source', 'base_output', 'patched_output'})
RESULT = re.compile(r'^(\S.*?::\S.*?) (PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b')


def classify(packet, config):
    checks = {key: False for key in ('stable_transition','plain_assertion','explicit_issue_change',
                                    'candidate_changes_behavior','no_conflicts')}
    def answer(reason, prediction='UNCERTAIN', evidence=()):
        return {'prediction':prediction,'shadow_mode':True,
                'suggest_suppress_v2_negative':prediction=='LIKELY_SUPERSEDED_ASSERTION',
                'checks':checks,'reason':reason,'evidence':list(evidence)}
    if set(packet) != ALLOWLIST:
        return answer('Input schema is not the exact allowlist')
    if not all(isinstance(packet[k],str) for k in ('issue','candidate_patch','test_source')):
        return answer('Non-text source input')
    for key in ('base_output','patched_output'):
        if not isinstance(packet[key],list):return answer('Run-output list missing')
        for run in packet[key]:
            if not isinstance(run,dict) or set(run)!={'stdout','stderr','returncode','timed_out'}:
                return answer('Run-output schema mismatch')
            if not isinstance(run['stdout'],str) or not isinstance(run['stderr'],str):
                return answer('Raw runner output is not text')
    minimum = config['minimum_observations_per_tree']
    if any(len(packet[k])<minimum for k in ('base_output','patched_output')):
        return answer('Insufficient paired stability observations; need initial plus three per tree')
    def statuses(run):
        values={}
        for line in (run['stdout']+'\n'+run['stderr']).splitlines():
            match=RESULT.match(line.strip())
            if match:values.setdefault(match[1],set()).add(match[2])
        return values
    all_runs=packet['base_output']+packet['patched_output']
    parsed=[statuses(run) for run in all_runs]
    failed={tid for values in parsed for tid,states in values.items() if 'FAILED' in states}
    if len(failed)!=1:return answer('No unique failing concrete test, or unrelated failures')
    tid=next(iter(failed))
    bases=[statuses(r) for r in packet['base_output']]
    patches=[statuses(r) for r in packet['patched_output']]
    checks['stable_transition']=(all(v.get(tid)=={'PASSED'} for v in bases)
        and all(v.get(tid)=={'FAILED'} for v in patches)
        and all(not r['timed_out'] and r['returncode']==0 for r in packet['base_output'])
        and all(not r['timed_out'] and r['returncode']==1 for r in packet['patched_output']))
    if not checks['stable_transition']:return answer('Stable base PASS -> patched FAIL not established')
    text='\n'.join(r['stdout']+'\n'+r['stderr'] for r in all_runs)
    patch_text='\n'.join(r['stdout']+'\n'+r['stderr'] for r in packet['patched_output'])
    exception_lines=re.findall(r'^E\s+(\w+(?:Error|Exception)):',text,re.MULTILINE)
    checks['plain_assertion']=('AssertionError:' in patch_text
        and bool(re.search(r'^>\s*assert\b',patch_text,re.MULTILINE))
        and all(e=='AssertionError' for e in exception_lines)
        and not re.search(r'Traceback \(most recent|ERROR collecting|Fatal Python|Segmentation fault',text))
    checks['no_conflicts']=(not any('ERROR' in s or (other!=tid and 'FAILED' in s)
        for values in parsed for other,s in values.items())
        and all(not r['stderr'].strip() for r in all_runs)
        and not re.search(r'(?m)^.*\bERROR(?:S|:| collecting| at setup| at teardown)',text))
    if not checks['plain_assertion'] or not checks['no_conflicts']:
        return answer('Non-assertion, conflicting or unrelated failure evidence')
    removed=[];added=[];paths=[]
    for line in packet['candidate_patch'].splitlines():
        if line.startswith('+++ b/'):paths.append(line[6:])
        elif line.startswith('-') and not line.startswith('---') and line[1:].strip():removed.append(line[1:].strip())
        elif line.startswith('+') and not line.startswith('+++') and line[1:].strip():added.append(line[1:].strip())
    if len(removed)!=1 or len(added)!=1 or len(paths)!=1:
        return answer('Outside frozen single-literal-change rule')
    try:
        old=ast.parse('{'+removed[0].rstrip(',')+'}',mode='eval').body
        new=ast.parse('{'+added[0].rstrip(',')+'}',mode='eval').body
        tree=ast.parse(packet['test_source'])
    except (SyntaxError,ValueError,RecursionError):
        return answer('Unsupported source syntax')
    if not (isinstance(old,ast.Dict) and isinstance(new,ast.Dict) and len(old.keys)==len(new.keys)==1
            and isinstance(old.keys[0],ast.Constant) and isinstance(old.keys[0].value,str)
            and isinstance(new.keys[0],ast.Constant) and new.keys[0].value==old.keys[0].value
            and isinstance(new.values[0],ast.Constant) and isinstance(new.values[0].value,str)):
        return answer('Not a unique string configuration-field change')
    field=old.keys[0].value;new_value=new.values[0].value
    old_values={n.value for n in ast.walk(old.values[0]) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
    method=tid.split('::')[-1].split('[',1)[0]
    funcs=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==method]
    if len(funcs)!=1:return answer('Failing test source identity is not unique')
    func=funcs[0]
    expectations=[n for n in ast.walk(func) if isinstance(n,ast.Assert)
        and any(isinstance(c,ast.Constant) and c.value==field+'=%s' for c in ast.walk(n))
        and any(isinstance(c,ast.Name) and c.id==field for c in ast.walk(n))]
    assignments=[n for n in ast.walk(func) if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id==field for t in n.targets)]
    expected_old={n.value for assignment in assignments for n in ast.walk(assignment.value)
                  if isinstance(n,ast.Constant) and isinstance(n.value,str)}
    issue=re.sub(r'\s+',' ',re.sub(r'[`\"\']','',packet['issue']))
    matching=[]
    for old_value in sorted(old_values & expected_old):
        pattern=(r'\b'+re.escape(field)+r'\b.{0,40}\bchang(?:e|ed)\s+from\s+'
                 +re.escape(old_value)+r'\s+to\s+'+re.escape(new_value)+r'\b')
        if re.search(pattern,issue,re.IGNORECASE):matching.append(old_value)
    checks['explicit_issue_change']=bool(matching and len(expectations)==1)
    module=paths[0].rsplit('/',1)[-1].removesuffix('.py')
    calls_module=any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
        and isinstance(n.func.value,ast.Name) and n.func.value.id==module for n in ast.walk(func))
    checks['candidate_changes_behavior']=(calls_module and field+'='+new_value in patch_text
        and all(old_value!=new_value for old_value in matching) and bool(matching))
    if not all(checks.values()):return answer('Exact issue/patch/test/output relationship not established')
    return answer('All five frozen conditions satisfied','LIKELY_SUPERSEDED_ASSERTION',
                  (tid,'field='+field,'old='+','.join(matching),'new='+new_value,
                   str(len(bases))+' base PASS; '+str(len(patches))+' patched assertion FAIL'))
