"""Terminal result parsing shared by live execution and stored-capture scoring.

XFAIL/XPASS retain distinct statuses as well as their original runner flavor.
"""

import re
from collections import defaultdict

from reliability.verifier.node_ids import normalize_pytest_id
from reliability.verifier.selection import django_label

ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
PYTEST = re.compile(
    r"^(?P<id>\S.*?::\S.*?)\s+(?P<status>PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)(?=$|\s|\[)(?P<tail>.*)",
    re.IGNORECASE,
)
DJANGO = re.compile(r"^(?P<name>\w+) \((?P<label>[^)]+)\)(?P<tail>.*)$")
DJ_STATUS = re.compile(
    r"\.\.\.\s*(ok|FAIL|ERROR|skipped|expected failure|unexpected success)\b(.*)", re.IGNORECASE
)
STATUSES = {
    "PASSED": "passed",
    "FAILED": "failed",
    "ERROR": "error",
    "SKIPPED": "skipped",
    "XFAIL": "xfail",
    "XPASS": "xpass",
    "ok": "passed",
    "fail": "failed",
    "error": "error",
    "skipped": "skipped",
    "expected failure": "xfail",
    "unexpected success": "xpass",
}
SEVERITY = {"skipped": 0, "xfail": 1, "passed": 2, "xpass": 3, "failed": 4, "error": 5}


def parse_capture(text, runner):
    """Parse observed terminal outcomes; reject Django summary-derived fake IDs."""
    if runner == "sympy":
        return parse_sympy_capture(text)
    result, pending = {}, None
    for number, physical in enumerate(text.split("\n"), 1):
        for line in ANSI.sub("", physical).split("\r"):
            line = line.strip()
            if runner == "django":
                header = DJANGO.match(line)
                if header:
                    name, label, tail = header.group("name", "label", "tail")
                    if name in ("OK", "FAILED", "FAIL", "ERROR", "Ran"):
                        pending = None
                        continue
                    if re.fullmatch(
                        r"(?:[A-Za-z_]\w*|<locals>)(?:\.(?:[A-Za-z_]\w*|<locals>))*", label
                    ):
                        pending = (
                            label if label.endswith("." + name) else label + "." + name,
                            number,
                        )
                    else:
                        # A docstring such as "Ensure ('fieldpath', ClassName)"
                        # is not a new unittest header; retain the real pending ID.
                        tail = line
                else:
                    tail = line
                match = DJ_STATUS.search(tail)
                if match is None and pending is not None:
                    # Verbose unittest output can put a docstring/warning between
                    # the test header and a bare terminal status on a later line.
                    match = re.match(
                        r"^(ok|FAIL|ERROR|skipped|expected failure|unexpected success)\b(.*)$", tail
                    )
                if pending is None or match is None:
                    continue
                rid, header_line = pending
                word = match.group(1).lower()
                status = STATUSES[word]
                reason = match.group(2).strip().strip("\"'") if status == "skipped" else ""
                if word == "expected failure":
                    reason = "expected failure"
                pending = None
                kind = (
                    "loader_placeholder"
                    if "unittest.loader._FailedTest." in rid
                    else "fixture"
                    if rid.endswith(
                        (".setUpClass", ".tearDownClass", ".setUpModule", ".tearDownModule")
                    )
                    else "case"
                )
            else:
                match = PYTEST.match(line)
                if match is None:
                    continue
                rid, word, tail = match.group("id", "status", "tail")
                word = word.upper()
                status = STATUSES[word]
                skip = re.search(r"^\s*\((.*?)\)", tail)
                reason = skip.group(1) if skip and status == "skipped" else ""
                kind, header_line = "case", number
            observation = {
                "status": status,
                "line": number,
                "header_line": header_line,
                "reason": reason,
                "flavor": word,
                "kind": kind,
            }
            if rid not in result or SEVERITY[status] >= SEVERITY[result[rid]["status"]]:
                result[rid] = observation
    return result


# SymPy's native verbose reporter identifies the file once, then emits a test
# name and a token (sometimes on a later line after warnings/debug output).
_SYMPY_FILE = re.compile(r"^(?P<path>[^\s\[]+\.py)\[(?:\d+|\?)\]")
_SYMPY_TEST = re.compile(r"^(?P<name>test_\w+|<lambda>)(?:\s+(?P<tail>.*))?$")
_SYMPY_TOKEN = re.compile(r"(?:^|\s)(ok|[fXFEsKwT])\s*(?:\[(?:OK|FAIL)\])?\s*$")
_SYMPY_STATUS = {
    "ok": "passed",
    "f": "xfail",
    "X": "xpass",
    "F": "failed",
    "E": "error",
    "s": "skipped",
    "K": "skipped",
    "w": "skipped",
    "T": "timeout",
}


def parse_sympy_capture(text):
    result, module, pending = {}, None, None
    severity = dict(SEVERITY, timeout=6)
    for number, physical in enumerate(text.split("\n"), 1):
        for line in ANSI.sub("", physical).split("\r"):
            line = line.strip()
            header = _SYMPY_FILE.match(line)
            if header:
                module = header.group("path")
                module = re.sub(r"^/testbed/", "", module)
                pending = None
                continue
            if line.startswith(("===", "___", "DO *NOT* COMMIT")):
                module, pending = None, None
                continue
            test = _SYMPY_TEST.match(line)
            if test and module:
                pending = (module + "::" + test.group("name"), number)
                tail = test.group("tail") or ""
            else:
                tail = line
            token = _SYMPY_TOKEN.search(tail)
            if not pending or not token:
                continue
            word = token.group(1)
            status = _SYMPY_STATUS[word]
            rid, header_line = pending
            flavor = "XFAIL" if word == "f" else "XPASS" if word == "X" else status.upper()
            observed = {
                "status": status,
                "line": number,
                "header_line": header_line,
                "reason": tail[: token.start()].strip() if status in ("skipped", "timeout") else "",
                "flavor": flavor,
                "kind": "case",
            }
            if rid not in result or severity[status] >= severity[result[rid]["status"]]:
                result[rid] = observed
    return result


def mapping_for(selected, runner):
    normalized = defaultdict(list)
    for test in selected:
        normalized[normalize_pytest_id(test) if runner == "pytest" else test].append(test)
    labels = defaultdict(list)
    if runner == "django":
        for test in selected:
            labels[django_label(test)].append(test)

    def map_id(rid):
        if runner != "django":
            rid = normalize_pytest_id(rid) if runner == "pytest" else rid
            candidates = [rid, rid.split("[", 1)[0]] if "[" in rid else [rid]
            return list(dict.fromkeys(t for candidate in candidates for t in normalized.get(candidate, ())))
        if rid in labels:
            return labels[rid]
        # Only a unique shortened framework label is admitted; ambiguity stays visible.
        candidates = [
            test for label, ids in labels.items() if label.endswith("." + rid) for test in ids
        ]
        return candidates if len(candidates) == 1 else []

    return map_id


def active_test(kind, missing_ids, output):
    """Recognize an unfinished verbose test start, never a terminal outcome."""
    import re

    pending = []
    for identity in missing_ids:
        if kind == "django":
            owner, method = identity.rsplit(".", 1)
            prefixes = (method + " (" + owner + ")", method + " (" + identity + ")")
        elif kind == "sympy":
            prefixes = (identity.rsplit("::", 1)[-1],)
        else:
            # Pytest may omit a configured root prefix in its displayed ID.
            canonical = normalize_pytest_id(identity)
            prefixes = tuple(canonical[i:] for i in [0] +
                             [m.end() for m in re.finditer("/", canonical.split("::", 1)[0])])
        for line_number, line in enumerate(output.splitlines()):
            clean = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", line).strip()
            if kind == 'pytest':
                clean = normalize_pytest_id(clean)
            if any(clean == prefix or clean.startswith(prefix + " ") for prefix in prefixes):
                # Completed cases are excluded by the event's missing_ids.
                pending.append((line_number, identity))
    return max(pending)[1] if pending else None


def module_identity_failures(events):
    """Only a first attempt AND its retry with no per-test progress prove loss."""
    ends = {e.get('batch'): e for e in events if e.get('event') == 'end'}
    def silent(e):
        return bool(e and e.get('load_failure') and not e.get('timed_out')
                    and not e.get('observed_ids') and not e.get('test_started')
                    and not e.get('active_id') and not e.get('per_test_output'))
    return [e for e in ends.values() if e.get('retry') and silent(e)
            and silent(ends.get(e.get('parent')))]


def sympy_import_signature(module, stderr):
    """Require a real module-import traceback, never an outcome or summary."""
    text = ANSI.sub('', stderr)
    frame = r'File [\"\'](?:/testbed/)?' + re.escape(module) + r'[\"\'], line \d+, in <module>'
    if not module or 'Traceback (most recent call last):' not in text or not re.search(frame, text):
        return ''
    exceptions = re.findall(r'^([A-Za-z_]\w*(?:Error|Exception|Warning)): (.+)$', text, re.MULTILINE)
    if not exceptions:
        return ''
    # A reporter exception qualifies only while handling the module import.
    terminal, message = exceptions[-1]
    if "'PyTestReporter' object has no attribute '_active_file'" in message:
        if 'in test_exception' not in text or len(exceptions) < 2:
            return ''
        return exceptions[0][0] + ' -> PyTestReporter._active_file during import of ' + module
    return terminal + ': ' + re.sub(r'0x[0-9a-fA-F]+', '<address>', message)[:1000]


def sympy_silent_nonzero(event):
    return (event.get('event') == 'end' and isinstance(event.get('returncode'), int)
            and event['returncode'] != 0 and not event.get('timed_out')
            and not any(event.get(k) for k in ('observed_ids', 'test_started', 'active_id', 'per_test_output')))


def sympy_import_batches(events):
    """A different, normally completed invocation must prove this tree's runner."""
    import base64
    import binascii

    starts = {e.get('batch'): e for e in events if e.get('event') == 'start'}
    healthy = [e for e in events if e.get('event') == 'end'
               and e.get('returncode') in (0, 1) and e.get('observed_ids')
               and not e.get('timed_out') and not e.get('load_failure')
               and not e.get('missing_ids')
               and starts.get(e.get('batch'), {}).get('ids')
               and set(starts.get(e.get('batch'), {}).get('ids', ())) <= set(e['observed_ids'])]
    matched = {}
    for event in events:
        if not sympy_silent_nonzero(event) or event['returncode'] < 0:
            continue
        start = starts.get(event.get('batch'), {})
        module = event.get('module', start.get('module', ''))
        if not any(e.get('batch') != event.get('batch') for e in healthy):
            continue
        try:
            stderr = base64.b64decode(event.get('stderr_b64', ''), validate=True).decode('utf-8', 'replace')
        except (ValueError, binascii.Error):
            continue
        signature = sympy_import_signature(module, stderr)
        if signature:
            matched[event['batch']] = signature
    return matched
