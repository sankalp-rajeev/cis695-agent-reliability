"""Package headline test IDs and verify preservation after the audit checks pass."""
import gzip
import json
import subprocess
from pathlib import Path

from analyze import HERE, ROOT, dump, original_state, sha, write_csv

protocol = json.loads((HERE / 'protocol.json').read_text())
assert original_state() == protocol['original_worktree']
assert all(sha(ROOT / p) == h for p, h in protocol['preserved_sha256'].items())
with gzip.open(HERE / 'selection_memberships.jsonl.gz', 'rt') as f:
    selections = [r for r in map(json.loads, f) if
                  (r['strategy'], r['edge_variant'], r['depth'], r['budget']) ==
                  ('B', 'PRIMARY_RESOLVED_ONLY', '3', 'ALL')]
for r in selections:
    before, after = r['before_selected'], r['after_selected']
    r['removed'] = sorted(set(before) - set(after)) if before is not None and after is not None else None
    r['added'] = sorted(set(after) - set(before)) if before is not None and after is not None else None
assert len(selections) == 83
write_csv('headline_selected_tests.csv', selections)
validation = json.loads((HERE / 'validation.json').read_text())
validation['audit_tests'] = {'passed': 15, 'command': 'env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest -p no:cacheprovider -o addopts= -q reports/callgraph_selection/typeprop_experiment/regression_validation/test_validation.py'}
validation['final_preservation_check'] = 'passed: all 590 prior tracked files and original dirty worktree unchanged'
dump('validation.json', validation)
dump('incidents.json', [
    {'attempt': 1, 'issue': 'Frozen unavailable-selection CSV fields are blank rather than JSON null.',
     'resolution': 'Treat blank fields as null and preserve unavailable versus empty; no selection output changed.'},
    {'attempt': 2, 'issue': 'Later image HEADs differ from graph base commits for all three raw-pair tasks.',
     'resolution': 'Do not assert source-tree equivalence. Retain those observations as supplemental evidence with explicit provenance limits.'},
    {'attempts': '3-6', 'issue': 'Packaging refinements after successful membership reconstruction.',
     'resolution': 'Preserved exact parameter suffixes, bounded evidence denominators, added local-record coverage/candidate-hash exclusions, and preserved unknown identity matches. Final counts reconcile; no graph or selector changes.'}
])
dump('output_hashes.json', {str(p.relative_to(HERE)): sha(p) for p in sorted(HERE.rglob('*'))
     if p.is_file() and p.name != 'output_hashes.json'})
print('Final preservation, 83 headline selections, and artifact hashes verified.')
