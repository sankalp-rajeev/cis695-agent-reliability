"""Native collection skip receipts; Python 3.6-compatible for task drivers."""

import os
import re


def clean_skip_reason(value):
    value = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', str(value)).strip()
    return '' if value in ('Skipped','SKIPPED') else re.sub(r'^Skipped:\s*', '', value).strip()


def _relative_collection_path(value):
    value = str(value).split('::', 1)[0].replace('\\', '/')
    if os.path.isabs(value):
        value = os.path.relpath(value, os.getcwd())
    return value[2:] if value.startswith('./') else value  # noqa: FURB188 -- task interpreters include Python 3.6


def pytest_module_skip(module, collected, reports, output, returncode, errors=()):
    """Require zero actual items, a native skip with reason, and no import error.

    Exit 5 is acceptable only with this independent native skip evidence.
    A package __init__ skip may cover its descendant requested module.
    """
    if collected or errors or returncode not in (0, 5):
        return None
    module = _relative_collection_path(module)
    text = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', output)
    summaries = []
    for line in text.splitlines():
        match = re.match(r'^\s*SKIPPED\s+(?:\[\d+\]\s+)?(.+?\.py):(\d+):\s*(.+)$', line)
        if match:
            summaries.append({'path': _relative_collection_path(match.group(1)),
                              'line': int(match.group(2)), 'reason': clean_skip_reason(match.group(3))})
    for report in reports:
        if report.get('when') != 'collect':
            continue
        node = _relative_collection_path(report.get('nodeid', ''))
        reason = clean_skip_reason(report.get('reason', ''))
        if reason and node and (node == module or module.startswith(node.rstrip('/')+'/')):
            return {'reason': reason, 'source': 'native pytest collect report',
                    'report': report, 'summary': summaries, 'native_returncode': returncode}
    for summary in summaries:
        path = summary['path']
        package = path[:-12] if path.endswith('/__init__.py') else None
        if summary['reason'] and (path == module or (package and module.startswith(package+'/'))):
            return {'reason': summary['reason'], 'source': 'native pytest -rs SKIPPED line',
                    'report': summary, 'summary': summaries, 'native_returncode': returncode}
    return None
