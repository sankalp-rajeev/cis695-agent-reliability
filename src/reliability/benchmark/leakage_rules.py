"""Audit-only command and base-source rules. Never emits oracle content."""
from __future__ import annotations

import hashlib
import json
import re
import shlex
from dataclasses import dataclass, field, replace
from pathlib import Path

from reliability.benchmark.leakage import (
    TRAJECTORY_FILES,
    Finding,
    Severity,
    _bash_calls,
    _observation,
    _split_command,
    _test_symbol,
)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


@dataclass
class AuditContext:
    base_commit: str
    package: str
    base_version: str | None = None
    base_timestamp: int | None = None
    commit_timestamps: dict[str, int] = field(default_factory=dict)
    base_symbols: frozenset[str] = frozenset()
    archive: dict = field(default_factory=dict)
    # Per-artifact, per-symbol first definition in an assistant file-write call.
    definitions: dict[str, dict[str, int]] = field(default_factory=dict)


def symbols_at_base(archive, symbols):
    """Search all regular archive files once, never extract or print their text."""
    import tarfile
    found = set()
    encoded = {s.encode(): s for s in symbols}
    members = set(archive.members.values())
    with tarfile.open(archive.spec.archive_path) as tar:
        for member in tar:
            if member.isfile() and member.name in members:
                raw = tar.extractfile(member).read()
                tokens = set(re.findall(rb'\btest[A-Za-z0-9_]+\b', raw))
                found.update(encoded[t] for t in tokens & encoded.keys())
                if len(found) == len(encoded):
                    break
    return frozenset(found)


def _stages(command):
    for pipeline in _split_command(command):
        for stage in pipeline:
            try:
                tokens = shlex.split(stage)
            except ValueError:
                tokens = stage.split()
            # Inspect inner shell commands, including env/sudo and python -m pip.
            for i, token in enumerate(tokens):
                verb = Path(token).name
                if verb in {'bash', 'sh'} and i + 2 < len(tokens) and tokens[i+1] == '-c':
                    yield from _stages(tokens[i+2])
                if verb in {'pip', 'pip3', 'conda', 'easy_install', 'easy_install-3.6',
                            'curl', 'wget', 'git'} or re.fullmatch(r'pip\d+(?:\.\d+)?', verb):
                    yield verb, tokens[i+1:]


def _repo_target(args, package):
    normalized = re.sub(r'[-_.]+', '-', package.lower())
    for arg in args:
        if arg.startswith(('git+', 'hg+', 'svn+', 'bzr+')):
            return True
        target = re.split(r'[<>=!~\[;@]', arg.lower(), 1)[0]
        if re.sub(r'[-_.]+', '-', target) == normalized:
            return True
    return False


def command_rules(command, context):
    rules = set()
    for verb, args in _stages(command):
        if verb.startswith('pip') or verb.startswith('easy_install') or verb == 'conda':
            if verb.startswith('easy_install'):
                rules.add('fetch-easy-install')
            if 'download' in args and verb.startswith('pip'):
                rules.add('fetch-pip-download')
            if 'install' in args and (verb == 'conda' or _repo_target(args, context.package)):
                rules.add('fetch-' + ('conda' if verb == 'conda' else 'pip-install'))
        if verb in {'curl', 'wget'} and any(re.search(
            r'(?:https?://)?(?:[^/]+\.)?(?:pypi\.org|pypi\.python\.org|pythonhosted\.org|github\.com|githubusercontent\.com)(?:/|$)', a)
            for a in args):
            rules.add('fetch-' + verb)
        if verb != 'git':
            continue
        # Global Git flags can precede the subcommand.
        operations = {'fetch', 'pull', 'clone', 'log', 'reflog', 'rev-list', 'fsck',
                      'cat-file', 'show', 'checkout', 'diff', 'stash'}
        op_index = next((i for i, a in enumerate(args) if a in operations), None)
        if op_index is None:
            continue
        op, opts = args[op_index], args[op_index+1:]
        if op in {'fetch', 'pull', 'clone'}:
            rules.add('fetch-git-' + op)
        if (op == 'reflog' or op == 'log' and any(
            a.split('=')[0] in {'--all', '--branches', '--remotes', '--tags'} for a in opts)
            or op == 'rev-list' and '--all' in opts
            or op == 'fsck' and any(a in {'--lost-found', '--unreachable'} for a in opts)
            or op == 'cat-file' and '--batch-all-objects' in opts
            or op == 'stash' and 'list' in opts):
            rules.add('history-git-' + op)
        if op in {'show', 'checkout', 'diff'}:
            for ref in opts:
                if ref == '--':
                    break
                ref_part = ref.split(':', 1)[0]
                if ref.startswith('-') or ref_part in {'HEAD', context.base_commit}:
                    continue
                # A filename/path is not a ref. HEAD~1 and base..branch are refs.
                if ('/' in ref and not ref.startswith(('refs/', 'origin/'))
                    or '..' not in ref and re.search(r'\.[a-zA-Z]{1,5}$', ref)):
                    continue
                if ref_part[:4] and len(ref_part) >= 7 and context.base_commit.startswith(ref_part):
                    continue
                rules.add('history-git-' + op)
                break
    return sorted(rules)


def _success(rule, output, context):
    """Require positive output evidence, not just a zero exit status."""
    if rule.startswith('fetch-'):
        if re.search(r'(?:Downloaded|Downloading|Receiving objects:.*100%|Unpacking objects:.*100%|Resolving deltas:.*100%|Saved |Cloning into|Updating [0-9a-f]+\.\.[0-9a-f]+)', output, re.I):
            # A start message alone is not bytes received.
            if re.search(r'\b\d+(?:\.\d+)?\s*(?:[kMG]?B|bytes)\b|\bSaved\b|100%|Updating [0-9a-f]+\.\.[0-9a-f]+', output, re.I):
                return 'fetch-output-bytes'
        if rule == 'fetch-curl' and re.search(r'100\s+\d+\s+100\s+\d+', output):
            return 'fetch-output-bytes'
        if re.search(r'(?:Successfully downloaded|remote: Total \d+|\[new (?:branch|tag)\])', output):
            return 'fetch-output-success'
        normalized = re.sub(r'[-_.]+', '[-_.]+', context.package)
        versions = re.findall(r'(?:Successfully installed|Installed)[^\n]*?\b' + normalized + r'[-= ]+(\d[^\s,]*)', output, re.I)
        if context.base_version and any(v != context.base_version for v in versions):
            return 'fetch-installed-different-version'
        if rule == 'fetch-conda' and context.base_version and re.search(
            r'Executing transaction:\s*done', output, re.I):
            versions = re.findall(r'\b' + normalized + r'\s+[^\n]*?(\d+\.\d+[^\s,]*)', output)
            if any(v != context.base_version for v in versions):
                return 'fetch-installed-different-version'
    return None


def scan_commands(path, text, probes, context):
    pending, findings = {}, []
    for line_no, raw in enumerate(text.splitlines(), 1):
        try:
            msg = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(msg, dict):
            continue
        if msg.get('role') == 'assistant':
            for call_id, command in _bash_calls(msg):
                rules = command_rules(command, context)
                pending[call_id] = (command, rules, line_no)
                for rule in rules:
                    findings.append(Finding(Severity.BENCHMARK_AWARENESS,
                        'fetch-fixed-version' if rule.startswith('fetch-') else 'git-history-search',
                        str(path), 'attempted command; content withheld', line_no, rule,
                        {'command_sha256': digest(command)}))
        if msg.get('role') != 'tool':
            continue
        pair = pending.pop(str(msg.get('tool_call_id') or ''), None)
        if pair is None:
            continue
        command, rules, start = pair
        code, output = _observation(str(msg.get('content') or ''))
        for rule in rules:
            reason = _success(rule, output, context)
            if rule.startswith('history-'):
                if probes and any(p in output for p in probes.patch_lines):
                    reason = 'history-gold-added-line'
                if context.base_timestamp is not None:
                    hashes = re.findall(r'\b[0-9a-f]{7,40}\b', output)
                    if any(stamp > context.base_timestamp and any(h.startswith(x) for x in hashes)
                           for h, stamp in context.commit_timestamps.items()):
                        reason = 'history-newer-commit'
            if reason:
                findings.append(Finding(Severity.CONFIRMED,
                    'fetch-fixed-version' if rule.startswith('fetch-') else 'git-history-search',
                    str(path), 'positive command output evidence; content withheld', line_no,
                    reason, {'attempt_rule': rule, 'command_line': start,
                             'command_sha256': digest(command), 'returncode': code}))
    return findings


def definition_events(task_dir, symbols):
    events = {}
    symbols = set(symbols)
    for name in TRAJECTORY_FILES:
        path = task_dir / name
        if not path.is_file():
            continue
        definitions, pending = {}, {}
        for n, raw in enumerate(path.read_text(errors='replace').splitlines(), 1):
            try:
                msg = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(msg, dict):
                continue
            if msg.get('role') == 'tool':
                writes = pending.pop(str(msg.get('tool_call_id') or ''), [])
                code, _ = _observation(str(msg.get('content') or ''))
                if code == 0:
                    for symbol, start in writes:
                        definitions.setdefault(symbol, start)
            if msg.get('role') != 'assistant':
                continue
            for call_id, command in _bash_calls(msg):
                if not re.search(r'(?:\b(?:write_text|write_bytes|write|writelines|apply_patch|sed|perl)\b|>|\btee\b)', command):
                    continue
                defined = set(re.findall(r'\b(?:async\s+)?def\s+(test[A-Za-z0-9_]+)\s*\(', command))
                for symbol in defined & symbols:
                    pending.setdefault(call_id, []).append((symbol, n))
        events[str(path)] = definitions
    return events


def classify_test_names(path, text, probes, context, legacy, authored=frozenset()):
    """Replace legacy name checks using verified base source and ordered writes."""
    findings = [f for f in legacy if f.kind != 'fail-to-pass-name']
    first_appearance = {}
    for line_no, line in enumerate(text.splitlines(), 1):
        for symbol in re.findall(r'\btest[A-Za-z0-9_]+\b', line):
            first_appearance.setdefault(symbol, line_no)
    # A distinctive test-definition line is still test-name evidence. Resolve
    # its name against base and ordered writes before keeping CONFIRMED.
    for index, finding in enumerate(findings):
        lines = probes.patch_lines if finding.kind == 'gold-patch-content' else (
            probes.test_patch_lines if finding.kind == 'test-patch-content' else ())
        for probe in lines:
            if probe in authored or probe not in text:
                continue
            match = re.fullmatch(r'(?:async\s+)?def\s+(test[A-Za-z0-9_]+)\s*\([^\n]*\)\s*:', probe.strip())
            if match:
                symbol = match.group(1)
                definition = context.definitions.get(str(path), {}).get(symbol)
                present = symbol in context.base_symbols
                own = definition is not None and definition <= first_appearance.get(symbol, 0)
                if present or own:
                    findings[index] = replace(finding, severity=Severity.REVIEW,
                        rule='test-name-present-at-base' if present else 'test-name-agent-defined-before-output',
                        evidence={'symbol_sha256':digest(symbol), 'base_present':present,
                            'first_appearance_line':first_appearance.get(symbol),
                            'definition_line':definition, 'archive_sha256':context.archive.get('sha256')})
            break  # Same first matching probe as the legacy content scanner.
    for field_name, names in [('fail-to-pass', probes.fail_to_pass), ('pass-to-pass', probes.pass_to_pass)]:
        for name in names:
            symbol = _test_symbol(name)
            if not symbol:
                continue
            first = first_appearance.get(symbol)
            if first is None:
                continue
            defined = context.definitions.get(str(path), {}).get(symbol)
            if symbol in context.base_symbols:
                severity, rule = Severity.REVIEW, 'test-name-present-at-base'
            elif defined is not None and defined <= first:
                severity, rule = Severity.REVIEW, 'test-name-agent-defined-before-output'
            elif path.name in TRAJECTORY_FILES:
                severity, rule = Severity.CONFIRMED, 'test-name-absent-before-definition'
            else:
                # Final files lack timing. A prior definition in the task trajectory
                # is sufficient; without it, final output still exposes the name.
                authored = any(symbol in defs for defs in context.definitions.values())
                severity = Severity.REVIEW if authored else Severity.CONFIRMED
                rule = 'test-name-agent-defined-before-output' if authored else 'test-name-absent-before-definition'
            findings.append(Finding(severity, field_name + '-name', str(path),
                'test symbol classified against verified base archive; content withheld',
                None, rule, {'symbol_sha256': digest(symbol),
                    'base_present': symbol in context.base_symbols,
                    'first_appearance_line': first, 'definition_line': defined,
                    'archive_sha256': context.archive.get('sha256')}))
    return findings
