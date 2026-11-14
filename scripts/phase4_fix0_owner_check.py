#!/usr/bin/env python3
"""Offline AST owner inventory. Never import or execute archived source."""
import ast
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/next_phases/phase4_baselines'
FROZEN = Path('/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/paired_frozen/tasks.json')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_archive(path):
    modules, classes, aliases = {}, {}, {}
    with tarfile.open(path) as archive:
        for member in archive.getmembers():
            if not member.isfile() or not member.name.startswith('testbed/') or not member.name.endswith('.py'):
                continue
            file = member.name[8:]
            module = file[:-3].replace('/', '.')
            if module.endswith('.__init__'):
                module = module[:-9]
            try:
                tree = ast.parse(archive.extractfile(member).read(), filename=file)
            except (SyntaxError, ValueError):
                continue
            modules[module] = (file, tree)
    # Django exposes tests/ as an import root in addition to the repo root.
    test_roots = {m.split('.')[1] for m in modules if m.startswith('tests.')}
    def canonical(name):
        return 'tests.' + name if name.split('.')[0] in test_roots else name
    for module, (file, tree) in modules.items():
        names = aliases.setdefault(module, {})
        package = module if file.endswith('/__init__.py') else module.rpartition('.')[0]
        def import_nodes(node):
            for child in ast.iter_child_nodes(node):
                if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    yield child
                    yield from import_nodes(child)
        for node in import_nodes(tree):
            if isinstance(node, ast.ImportFrom):
                prefix = '.'.join(package.split('.')[:len(package.split('.')) - node.level + 1]) if node.level else ''
                target = '.'.join(x for x in (prefix, node.module) if x)
                for alias in node.names:
                    names[alias.asname or alias.name] = canonical(target + '.' + alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    names[alias.asname or alias.name.split('.')[0]] = canonical(alias.name if alias.asname else alias.name.split('.')[0])
        def visit(body, scope=''):
            for node in body:
                if isinstance(node, ast.ClassDef):
                    key = module + '.' + scope + node.name
                    classes[key] = (module, file, node)
                    visit(node.body, scope + node.name + '.')
        visit(tree.body)
    def resolve(module, node):
        name = ast.unparse(node)
        head, _, tail = name.partition('.')
        name = aliases[module].get(head, module + '.' + head) + ('.' + tail if tail else '')
        seen = set()
        while name not in seen and len(seen) < 30:
            if name in classes or name in ('unittest.TestCase', 'unittest.case.TestCase'):
                break
            seen.add(name)
            parts = name.split('.')
            replacement = None
            for i in range(len(parts) - 1, 0, -1):
                prefix = '.'.join(parts[:i])
                target = aliases.get(prefix, {}).get(parts[i])
                if target:
                    replacement = '.'.join([target] + parts[i + 1:])
                    break
            if replacement is None:
                break
            name = replacement
        return name
    bases = {key: [resolve(module, b) for b in node.bases] for key, (module, _, node) in classes.items()}
    cache = {}
    def mro(key, active=()):
        if key in cache:
            return cache[key]
        if key in active:
            return [key]
        seqs = [mro(b, active + (key,))[:] for b in bases.get(key, [])] + [bases.get(key, [])[:]]
        result = [key]
        while any(seqs):
            seqs = [s for s in seqs if s]
            head = next((s[0] for s in seqs if all(s[0] not in t[1:] for t in seqs)), None)
            if head is None:
                raise ValueError('Unresolved C3 MRO: ' + key)
            result.append(head)
            for seq in seqs:
                if seq[0] == head:
                    seq.pop(0)
        cache[key] = result
        return result
    def testcase(key):
        return any(k in ('unittest.TestCase', 'unittest.case.TestCase') for k in mro(key))
    def method_owner(key, name):
        for parent in mro(key):
            if parent in classes and any(getattr(n, 'name', None) == name for n in classes[parent][2].body):
                return parent
        return None
    return modules, classes, mro, testcase, method_owner


def main():
    rows = [r for r in csv.DictReader((OUT / 'fix0_slots.csv').open()) if 'missing 1 required positional argument:' in r['signature']]
    tasks = {t['instance_id']: t for t in json.loads(FROZEN.read_text())}
    hashes = {str(FROZEN): digest(FROZEN), str(OUT / 'fix0_slots.csv'): digest(OUT / 'fix0_slots.csv')}
    output = []
    for task in sorted({r['instance_id'] for r in rows}):
        path = Path('/home/sankalp/cg_repos/task_archives') / (task + '.tar')
        hashes[str(path)] = digest(path)
        assert hashes[str(path)] == tasks[task]['base_archive_sha256']
        modules, classes, mro, testcase, method_owner = inspect_archive(path)
        selected = sorted({r['selected_test_id'] for r in rows if r['instance_id'] == task})
        for label in selected:
            parts = label.split('::')
            module = parts[0][:-3].replace('/', '.')
            key = '.'.join([module] + parts[1:-1]) if len(parts) > 2 else ''
            owner = method_owner(key, parts[-1]) if key in classes else None
            body = classes[owner][2].body if owner else modules[module][1].body
            node = next((n for n in body if getattr(n, 'name', None) == parts[-1]), None)
            decorated = bool(getattr(node, 'decorator_list', []))
            mixin = bool(owner and not testcase(owner))
            category = ('decorated function or method' if decorated else 'method on non-TestCase class (mixin)' if mixin else 'module-level function' if not owner and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else 'other')
            subclasses = sorted(k for k in classes if mixin and k != owner and owner in mro(k) and testcase(k) and method_owner(k, parts[-1]) == owner)
            relevant = [r for r in rows if r['instance_id'] == task and r['selected_test_id'] == label]
            for signature in sorted({r['signature'] for r in relevant}):
                slots = [r for r in relevant if r['signature'] == signature]
                output.append(dict(instance_id=task, selected_test_id=label, signature=signature, selected_tree_slots=len(slots), trees=';'.join(sorted({r['tree'] for r in slots})), category=category, owner=owner or module, owner_is_TestCase=bool(owner and testcase(owner)), owner_is_mixin=mixin, decorators=';'.join(ast.unparse(d) for d in getattr(node, 'decorator_list', [])), concrete_subclass_count=len(subclasses), concrete_subclasses=';'.join(subclasses), source=f'{path}!testbed/{parts[0]}:{getattr(node, "lineno", 0)}'))
        print(task, len(selected), flush=True)
    with (OUT / 'fix0_owner_check.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(output[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(output)
    summary = dict(selected_tree_slots=sum(r['selected_tree_slots'] for r in output), task_labels=len({(r['instance_id'], r['selected_test_id']) for r in output}), task_label_signature_rows=len(output), category_rows=dict(Counter(r['category'] for r in output)), category_slots=dict(Counter({c: sum(r['selected_tree_slots'] for r in output if r['category'] == c) for c in {r['category'] for r in output}})), mixin_rows=sum(r['owner_is_mixin'] for r in output), mixin_without_concrete_subclass=sum(r['owner_is_mixin'] and not r['concrete_subclass_count'] for r in output), Docker_calls=0, source_execution=False, classification='Decorated takes precedence; owner_is_mixin is independent. Concrete subclass lists use AST-resolved imports, transitive unittest.TestCase ancestry and C3 effective method owner; overridden methods excluded. Other includes ordinary TestCase methods and non-callable attributes. Counts include co-batched collateral labels, not only the callable causing the abort.', input_sha256=hashes, script_sha256=digest(Path(__file__)))
    summary['mixin_expanded_identities_per_task_label'] = sum(r['concrete_subclass_count'] for r in output if r['owner_is_mixin'])
    summary['mixin_expanded_tree_instances'] = 2 * summary['mixin_expanded_identities_per_task_label']
    (OUT / 'fix0_owner_check_summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k:v for k,v in summary.items() if k != 'input_sha256'}, indent=2))


if __name__ == '__main__':
    main()
