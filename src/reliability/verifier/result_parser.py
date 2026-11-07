"""Terminal result parsing shared by live execution and stored-capture scoring.

XFAIL/XPASS retain distinct statuses as well as their original runner flavor.
"""

import re
from collections import defaultdict

from reliability.verifier.selection import django_label

ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
PYTEST = re.compile(
    r"^(?P<id>\S.*?::\S.*?)\s+(?P<status>PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b(?P<tail>.*)",
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


def mapping_for(selected, runner):
    wanted = set(selected)
    labels = defaultdict(list)
    if runner == "django":
        for test in selected:
            labels[django_label(test)].append(test)

    def map_id(rid):
        if runner != "django":
            candidates = [rid, rid.split("[", 1)[0]] if "[" in rid else [rid]
            return list(dict.fromkeys(t for t in candidates if t in wanted))
        if rid in labels:
            return labels[rid]
        # Only a unique shortened framework label is admitted; ambiguity stays visible.
        candidates = [
            test for label, ids in labels.items() if label.endswith("." + rid) for test in ids
        ]
        return candidates if len(candidates) == 1 else []

    return map_id
