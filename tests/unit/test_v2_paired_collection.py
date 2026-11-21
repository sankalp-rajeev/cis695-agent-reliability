"""Amendment A7: a selected module whose collection fails on both trees with the same
exception type is excluded from V2's selection and recorded; V2 runs the rest.

A collection error on only one tree, or with different exception types, still
blocks (absence error), and so does a selection with no module left.
"""

import json

import pytest

from reliability.verifier import guarded_v2, run_v1_4_1 as runtime
from reliability.verifier.run_health import RunHealthError
from reliability.verifier.run_v1_4_1 import collection_exception_type, paired_collection_exclusions
from reliability.verifier.selection import Selection
from tests.unit import test_e2e_v1_4_3 as fixture

BROKEN = 'tests/broken/tests.py::Example::test_body'
HEALTHY = fixture.HEALTHY
BODY = 'import unittest\nclass Example(unittest.TestCase):\n    def test_body(self):\n        pass\n'
MISSING = 'import missing_dep_for_test\n' + BODY
IMPORT_ERROR = 'raise ImportError("broken on purpose")\n' + BODY


def runtime_with_broken(tmp_path, monkeypatch, base_src, patched_src):
    task, patch, created = fixture.local_runtime(tmp_path, monkeypatch, ('', ''))
    base_class = runtime.FrozenContainer

    class Container(base_class):
        def set_patched(self, patched):
            super().set_patched(patched)
            folder = self.root / 'tests' / 'broken'
            folder.mkdir(parents=True, exist_ok=True)
            (folder / '__init__.py').touch()
            (folder / 'tests.py').write_text((patched_src if patched else base_src) or BODY)

    monkeypatch.setattr(runtime, 'FrozenContainer', Container)
    monkeypatch.setattr(guarded_v2, 'FrozenContainer', Container)
    return task, patch, created


def call(task, patch, folder, tests):
    return runtime.run_v2(task, patch, Selection(tests=tests, runner=task.runner), folder,
                          experiment='unit', drift={}, stamps={'g1_receipt_sha256': {}})


def test_paired_collection_error_is_excluded_and_v2_runs_the_rest(tmp_path, monkeypatch):
    task, patch, _ = runtime_with_broken(tmp_path, monkeypatch, MISSING, MISSING)
    folder = tmp_path / 'verification'
    signal = call(task, patch, folder, (BROKEN, HEALTHY))
    assert signal.outcome.value == 'PASS' and signal.findings['n_executed'] == 1
    assert signal.findings['paired_collection_exclusions'] == [
        {'module': 'tests/broken/tests.py', 'exception_type': 'ModuleNotFoundError',
         'excluded_tests': [BROKEN], 'trees': ['base', 'patched']}]
    health = [json.loads(line) for line in (folder / 'health.jsonl').read_text().splitlines()]
    assert [r['status'] for r in health if r.get('scope') == 'G1'] == ['BLOCKED', 'BLOCKED']
    rerun = [r for r in health if r.get('scope') == 'G1_after_paired_exclusion']
    assert [r['status'] for r in rerun] == ['READY', 'READY']
    policies = json.loads((folder / 'v2_policies.json').read_text())['policies']
    for policy in policies.values():
        assert policy['selection']['tests'] == [HEALTHY]


@pytest.mark.parametrize('base_src,patched_src', [
    (None, MISSING), (MISSING, None), (MISSING, IMPORT_ERROR)],
    ids=['patched-only', 'base-only', 'different-types'])
def test_unpaired_collection_error_still_blocks(tmp_path, monkeypatch, base_src, patched_src):
    task, patch, _ = runtime_with_broken(tmp_path, monkeypatch, base_src, patched_src)
    folder = tmp_path / 'verification'
    with pytest.raises(RunHealthError):
        call(task, patch, folder, (BROKEN, HEALTHY))
    assert not (folder / 'v2_policies.json').exists()
    assert not any(json.loads(line).get('scope') == 'G1_after_paired_exclusion'
                   for line in (folder / 'health.jsonl').read_text().splitlines())


def test_no_module_left_keeps_the_absence_error(tmp_path, monkeypatch):
    task, patch, _ = runtime_with_broken(tmp_path, monkeypatch, MISSING, MISSING)
    folder = tmp_path / 'verification'
    with pytest.raises(RunHealthError) as caught:
        call(task, patch, folder, (BROKEN,))
    assert caught.value.g1_category == 'module_import_dependency_failure'
    assert not (folder / 'v2_policies.json').exists()


@pytest.mark.parametrize('text,expected', [
    ("Traceback:\nmod.py:16: in <module>\n    import hypothesis\n"
     "E   ModuleNotFoundError: No module named 'hypothesis'\n!!!! Interrupted: 1 error\n1 error in 0.5s",
     'ModuleNotFoundError'),
    ("Hint: make sure your test modules/packages have valid Python names.\n"
     "E   _pytest.config.exceptions.UsageError: hello\n", '_pytest.config.exceptions.UsageError'),
    ('Traceback (most recent call last):\n  File "x.py", line 1, in <module>\n    import y\n'
     'ModuleNotFoundError: No module named \'y\'\n', 'ModuleNotFoundError'),
    ('Aborting: A GIS database backend is required to run gis_tests.\n', None),
    ("collection failed for an unknown reason\n", None),
])
def test_collection_exception_type(text, expected):
    assert collection_exception_type(text) == expected


def _health(tree, stages, status='BLOCKED'):
    return {'tree': tree, 'status': status, 'stages': stages}


def _stage(module, exc, status='COLLECTION_ERROR'):
    return {'stage': 'native_collection', 'module': module, 'status': status, 'input_count': 1,
            'output_count': 0, 'messages': [f'E   {exc}: x'] if exc else ['no type here']}


def test_exclusions_need_every_blocking_stage_paired():
    a, b = _stage('a.py', 'ModuleNotFoundError'), _stage('b.py', 'UsageError')
    assert [e['module'] for e in paired_collection_exclusions(
        [_health('base', [a, b]), _health('patched', [a, b])])] == ['a.py', 'b.py']
    assert paired_collection_exclusions([_health('base', [a, b]), _health('patched', [a])]) is None
    assert paired_collection_exclusions([_health('base', [_stage('a.py', None)]),
                                         _health('patched', [_stage('a.py', None)])]) is None
    runner = {'stage': 'runner_startup', 'status': 'RUNNER_UNAVAILABLE', 'input_count': 1, 'output_count': 0}
    assert paired_collection_exclusions([_health('base', [a, runner]), _health('patched', [a])]) is None
    assert paired_collection_exclusions([_health('base', [a], 'READY'), _health('patched', [a])]) is None
