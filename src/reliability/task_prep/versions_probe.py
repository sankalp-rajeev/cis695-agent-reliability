"""Standalone Python 3.6-compatible probe; emits names and versions only.

Never imports repository code. Only version assignments and distribution metadata
are read. The caller supplies the public import name and base commit on stdin.
"""
import ast
import json
import os
import re
import subprocess
import sys

BLOCKED = ('oracle', 'grade', 'label', 'gold', 'posthoc', 'fail_to_pass', 'pass_to_pass')
VERSION_FILES = ('__init__.py', '__version__.py', 'version.py', '_version.py', '_version_info.py', 'release.py')
VERSION_NAMES = ('__version__', 'version', 'VERSION', 'version_info', '__version_info__', 'short_version')


def allowed(path):
    return not any(word in path.lower() for word in BLOCKED)


def versions(raw):
    try:
        tree = ast.parse(raw)
    except (SyntaxError, ValueError):
        return []
    result = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id in VERSION_NAMES for t in node.targets):
            continue
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, TypeError):
            continue
        if isinstance(value, (tuple, list)):
            value = '.'.join(str(x) for x in value)
        if isinstance(value, str) and re.match(r'^\d+\.\d+', value):
            result.append(value)
    return sorted(set(result))


def probe(request):
    name, commit = request['import_name'], request['base_commit']
    masks = tuple(request['masked_paths'])
    aliases = (name, '_pytest') if name == 'pytest' else (name,)
    files = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', commit], cwd='/testbed').decode().splitlines()
    base = []
    for path in files:
        if not allowed(path) or os.path.basename(path) not in VERSION_FILES:
            continue
        parts = path.split('/')
        if not any(part in aliases for part in parts[:-1]) or len(parts) > 4:
            continue
        raw = subprocess.check_output(['git', 'show', commit + ':' + path], cwd='/testbed').decode('utf-8', 'replace')
        for version in versions(raw):
            base.append({'path': path, 'version': version})
    copies, errors = [], []
    roots = ('/opt', '/usr/local/lib', '/usr/lib', '/root', '/tmp')
    def onerror(exc):
        errors.append({'path': exc.filename, 'error': type(exc).__name__})
    for root in roots:
        if not os.path.isdir(root):
            continue
        for directory, dirs, names in os.walk(root, followlinks=False, onerror=onerror):
            dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', 'node_modules')
                       and allowed(os.path.join(directory, d))
                       and not any(os.path.join(directory, d) == m or os.path.join(directory, d).startswith(m + '/') for m in masks)]
            if os.path.basename(directory) not in aliases:
                continue
            if os.path.islink(directory) and os.path.realpath(directory).startswith('/testbed/'):
                continue
            found = []
            for filename in VERSION_FILES:
                path = os.path.join(directory, filename)
                if os.path.isfile(path) and allowed(path):
                    with open(path, 'r', errors='replace') as stream:
                        found.extend({'path': path, 'version': v} for v in versions(stream.read()))
            # A distribution can store its version only in dist-info METADATA.
            if not found:
                parent = os.path.dirname(directory)
                for entry in os.listdir(parent):
                    if entry.lower().replace('-', '_').startswith(name.lower().replace('-', '_') + '_') and entry.endswith(('.dist-info', '.egg-info')):
                        path = os.path.join(parent, entry, 'METADATA' if entry.endswith('.dist-info') else 'PKG-INFO')
                        if os.path.isfile(path) and allowed(path):
                            with open(path, 'r', errors='replace') as stream:
                                for line in stream:
                                    if line.startswith('Version: '):
                                        found.append({'path': path, 'version': line[9:].strip()})
                                        break
            # Namespace directories with no Python code are not package copies.
            if found:
                copies.extend(found)
            elif '__init__.py' in names:
                copies.append({'path': directory, 'version': None})
            dirs[:] = []
    return {'base_versions': base, 'copies': sorted(copies, key=lambda x: x['path']), 'scan_errors': errors,
            'roots': list(roots), 'masked_paths': list(masks), 'repository_code_imported': False}


if __name__ == '__main__':
    print(json.dumps(probe(json.load(sys.stdin)), sort_keys=True))
