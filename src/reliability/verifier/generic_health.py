"""Pre-registered environment exceptions, authorized only by a paired gate.

Within the scope, individual collectors produce provisional exception records
using the existing per-task accounting. The caller must check both trees before
opening G1 or evaluating V2 policies. No other executor enables these rules.
"""

from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


RULES_PATH = Path(__file__).resolve().parents[3] / 'configs/verifier/run_health_generic_exceptions.json'
_scope = ContextVar('paired_generic_health', default=None)


def rules_manifest():
    raw = RULES_PATH.read_bytes()
    return {'path': str(RULES_PATH.relative_to(RULES_PATH.parents[2])),
            'sha256': hashlib.sha256(raw).hexdigest(),
            'rules': json.loads(raw)['rules']}


def rules_stamp():
    active = _scope.get()
    manifest = active['manifest'] if active else rules_manifest()
    return {k: manifest[k] for k in ('path', 'sha256')}


@contextmanager
def paired_exception_scope(task, repo):
    token = _scope.set({'task': task, 'repo': repo, 'manifest': rules_manifest()})
    try:
        yield
    finally:
        _scope.reset(token)


def guard_message(message, required):
    """The literal guard may be wrapped in a collector's SystemExit traceback.

    An additional exception, chained traceback, or changed guard text is not the
    same environment failure, even if it repeats the required words.
    """
    if not re.search(r'(?:^|: )(?:Aborting: )?' + re.escape(required) + r'\.?[ \t]*$', message, re.MULTILINE):
        return False
    if 'During handling of the above exception' in message or 'direct cause' in message:
        return False
    exceptions = re.findall(r'^([\w.]+):[^\n]*$', message, re.MULTILINE)
    return all(name in ('Aborting', 'SystemExit') for name in exceptions) and all(
        line.strip() == 'SystemExit: 1' for line in message.splitlines() if line.startswith('SystemExit:'))


def generic_match(task, module, stage, message, tree):
    active = _scope.get()
    if not active or task != active['task']:
        return None
    path = PurePosixPath(module)
    if path.is_absolute() or '..' in path.parts or str(path) != module:
        return None
    for rule in active['manifest']['rules']:
        if (active['repo'] == rule['repo'] and module.startswith(rule['module_prefix'])
                and stage in rule['stages'] and tree in rule['trees']
                and guard_message(message, rule['required_message'])):
            return {**rule, 'exception_source': 'generic_rule', 'rule_id': rule['id'],
                    'rules_file_sha256': active['manifest']['sha256']}
    return None


def exception_metadata(matches):
    generic = [m for m in matches if m and m.get('exception_source') == 'generic_rule']
    if not generic:
        return {}
    return {k: generic[0][k] for k in ('exception_source', 'rule_id', 'rules_file_sha256')}


def check_generic_pair(stages_by_tree):
    """Return halt reasons and revoke every application lacking paired proof."""
    applications = {}
    for tree, stages in stages_by_tree.items():
        for stage in stages:
            if stage.get('exception_source') == 'generic_rule':
                key = (stage['module'], stage['stage'], stage['rule_id'])
                applications.setdefault(key, {})[tree] = stage
    reasons = []
    for (module, name, rule_id), pair in applications.items():
        complete = set(pair) == {'base', 'patched'}
        complete &= all(s.get('allowed_exception') and s.get('output_count') == 0
                        and s.get('status') in ('COLLECTION_ERROR', 'NOT_RUN') for s in pair.values())
        # A second failure in the same module cannot be hidden by the GIS text.
        complete &= not any(s.get('module') == module and not s.get('allowed_exception')
                            and s.get('status') in ('COLLECTION_ERROR', 'RUNNER_UNAVAILABLE', 'NOT_REACHED', 'ERROR', 'NOT_RUN')
                            for stages in stages_by_tree.values() for s in stages)
        if complete:
            for stage in pair.values():
                stage['both_trees_confirmed'] = True
        else:
            reasons.append('Generic rule ' + rule_id + ': missing identical both-tree failure at ' + name + '/' + module)
            for stage in pair.values():
                stage['allowed_exception'] = []
                stage['generic_rule_rejected'] = rule_id
                for key in ('exception_source', 'rule_id', 'rules_file_sha256', 'both_trees_confirmed'):
                    stage.pop(key, None)
    return reasons
