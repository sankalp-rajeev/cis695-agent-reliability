"""Read only cost, token, step and elapsed fields from authorized old runs."""
import json
from pathlib import Path

IDS = ('django__django-14373', 'scikit-learn__scikit-learn-12973', 'django__django-16899')
OLD = Path.home() / 'projects/cis695-agent-reliability/runs'
FORBIDDEN = ('oracle', 'grade', 'grader', 'label', 'gold', 'FAIL_TO_PASS', 'PASS_TO_PASS')
REPAIR_KEYS = ('steps', 'n_steps', 'steps_used', 'duration_s')
USAGE_KEYS = ('tokens_in', 'tokens_out', 'cached_input_tokens', 'api_cost_usd', 'steps', 'n_steps')
V4_KEYS = ('steps_used', 'cost_usd', 'elapsed_seconds', 'total_input_tokens', 'total_output_tokens',
           'cached_input_tokens')


def numeric_keys(data, keys):
    return {k: data.get(k) if isinstance(data.get(k), (int, float)) else None for k in keys}


def extract():
    output = {}
    for run in ('main_50_a', 'main_50_b'):
        root = OLD / run / 'tasks'
        matched = [root / i / 'repair_record.json' for i in IDS
                   if (root / i / 'repair_record.json').is_file()]
        same_three = len(matched) == 3
        paths = matched if same_three else sorted(root.glob('*/repair_record.json'))
        rows = []
        for path in paths:
            if any(word.lower() in str(path).lower() for word in FORBIDDEN):
                raise RuntimeError('Forbidden input path')
            data = json.loads(path.read_text())
            row = {'instance_id': path.parent.name, **numeric_keys(data, REPAIR_KEYS),
                   'usage': numeric_keys(data.get('usage', {}), USAGE_KEYS)}
            v4 = []
            for vp in sorted(path.parent.glob('verification_record.*.json')):
                if any(word.lower() in str(vp).lower() for word in FORBIDDEN):
                    raise RuntimeError('Forbidden input path')
                verification = json.loads(vp.read_text())
                findings = verification.get('reproduction', {}).get('findings', {})
                evidence = findings.get('generation_evidence', {})
                # Older V4 records place generator counters directly in findings.
                values = {**numeric_keys(findings, ('n_steps', 'cost_usd')),
                          **numeric_keys(evidence, V4_KEYS)}
                if values['cost_usd'] is None:
                    values['cost_usd'] = numeric_keys(findings, ('cost_usd',))['cost_usd']
                v4.append({'source': str(vp), **values})
            row['v4_numeric'] = v4
            row['source'] = str(path)
            rows.append(row)
        output[run] = {'selection': 'same three tasks' if same_three else 'whole set (three tasks absent)',
                       'rows': rows, 'count': len(rows)}
    return output


if __name__ == '__main__':
    dest = Path(__file__).resolve().parents[1] / 'reports/umgpt_probe/deepseek_numeric.json'
    result = extract()
    dest.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: {'selection': v['selection'], 'count': v['count']} for k, v in result.items()}))
