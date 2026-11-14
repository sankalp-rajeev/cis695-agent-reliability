"""Project only original-run identities/admission; never decode verdict fields."""

import hashlib
import json
from pathlib import Path

_ADMITTED = frozenset(('passed', 'failed', 'skipped', 'xfail', 'xpass'))


class JSONProjection:
    """Small structural JSON projection; discarded values are never decoded."""
    def __init__(self, text):
        self.text, self.position = text, 0
        self.decoder = json.JSONDecoder()

    def whitespace(self):
        while self.position < len(self.text) and self.text[self.position].isspace():
            self.position += 1

    def scalar(self):
        self.whitespace()
        value, self.position = self.decoder.raw_decode(self.text, self.position)
        return value

    def skip(self):
        self.whitespace()
        depth, quoted, escaped = 0, False, False
        while self.position < len(self.text):
            char = self.text[self.position]
            if quoted:
                if escaped:
                    escaped = False
                elif char == '\\':
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in '[{':
                depth += 1
            elif char in ']}':
                if depth == 0:
                    return
                depth -= 1
                if depth == 0:
                    self.position += 1
                    return
            elif depth == 0 and char in ',:':
                return
            self.position += 1
            if depth == 0 and not quoted and char == '"':
                return

    def project(self, schema, *, calls=False):
        self.whitespace()
        if schema is True:
            return self.scalar()
        opening = self.text[self.position]
        self.position += 1
        if opening == '{':
            result = {}
            self.whitespace()
            while self.text[self.position] != '}':
                key = self.scalar()
                self.whitespace()
                if self.text[self.position] != ':':
                    raise ValueError('Malformed reference JSON')
                self.position += 1
                if key in schema:
                    result[key] = self.project(schema[key], calls=key == 'calls')
                else:
                    self.skip()
                self.whitespace()
                if self.text[self.position] == ',':
                    self.position += 1
                self.whitespace()
            self.position += 1
            return result
        if opening == '[':
            result = []
            self.whitespace()
            while self.text[self.position] != ']':
                if calls and len(result) >= 2:
                    self.skip()
                else:
                    result.append(self.project(schema['*']))
                self.whitespace()
                if self.text[self.position] == ',':
                    self.position += 1
                self.whitespace()
            self.position += 1
            return result
        raise ValueError('Unexpected reference JSON structure')


def original_admission_evidence(path: Path, expected_sha256: str):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('Original-run input hash mismatch: ' + str(path))
    schema = {'calls': {'*': {'patched': True, 'run': {'results': {
        '*': {'test_id': True, 'status': True}}}}}}
    projection = JSONProjection(raw.decode()).project(schema)
    result = {tree:{'admitted_ids':set(),'skipped_reference_ids':set(),
                    'module_skip_blocked_ids':set()} for tree in ('base','patched')}
    seen = set()
    for call in projection.get('calls', []):
        tree = 'patched' if call['patched'] else 'base'
        if tree in seen:
            raise ValueError('Duplicate initial reference tree')
        seen.add(tree)
        for row in call['run']['results']:
            identity,status=row['test_id'],row['status'].lower()
            if status in _ADMITTED:
                result[tree]['admitted_ids'].add(identity)
            if status == 'skipped':
                result[tree]['skipped_reference_ids'].add(identity)
            elif status in _ADMITTED or status == 'error':
                result[tree]['module_skip_blocked_ids'].add(identity)
    # Empty original selections can legitimately have no native calls.
    return {tree:{kind:sorted(ids) for kind,ids in evidence.items()} for tree,evidence in result.items()}


def original_admitted(path: Path, expected_sha256: str):
    return {tree:values['admitted_ids'] for tree,values in original_admission_evidence(path,expected_sha256).items()}
