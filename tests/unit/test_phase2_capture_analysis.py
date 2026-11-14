"""Small fixtures for observed parser failures; no harness or benchmark imports."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[2] / 'scripts/phase2_capture_analysis.py'
if not MODULE.exists():
    MODULE = Path(__file__).with_name('phase2_capture_analysis.py')
SPEC = importlib.util.spec_from_file_location('phase2_capture_analysis', MODULE)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class CaptureReplayTests(unittest.TestCase):
    def test_django_warning_separated_status_and_summary_rejection(self):
        text = ('test_a (sample.tests.Case)\nA warning from a dependency\n'
                ' ... ok\nOK (skipped=2)\n'
                'test_b (sample.tests.Case) ... warning\nok\n')
        outcomes = audit.parse_capture(text, 'django')
        self.assertEqual(set(outcomes), {'sample.tests.Case.test_a', 'sample.tests.Case.test_b'})
        self.assertEqual([v['status'] for v in outcomes.values()], ['passed', 'passed'])

    def test_loader_placeholder_remains_an_error_without_a_test_body(self):
        text = 'missing (unittest.loader._FailedTest) ... ERROR\n'
        outcome = audit.parse_capture(text, 'django')['unittest.loader._FailedTest.missing']
        self.assertEqual((outcome['kind'], outcome['status']), ('loader_placeholder', 'error'))

    def test_ansi_parameter_id_is_retained_and_teardown_error_wins(self):
        text = ('\x1b[32mtests/a.py::test_a[value with spaces]\x1b[0m '
                '\x1b[32mPASSED\x1b[0m [100%]\n'
                'tests/a.py::test_a[value with spaces] ERROR [100%]\n')
        outcome = audit.parse_capture(text, 'pytest')['tests/a.py::test_a[value with spaces]']
        self.assertEqual(outcome['status'], 'error')

    def test_ambiguous_exact_and_family_mapping_is_not_silently_resolved(self):
        mapper = audit.mapping_for(['tests/a.py::test_a', 'tests/a.py::test_a[1]'], 'pytest')
        self.assertEqual(len(mapper('tests/a.py::test_a[1]')), 2)

    def test_skip_reason_and_xfail_are_not_reported_as_test_passes(self):
        outcomes = audit.parse_capture('tests/a.py::test_a SKIPPED (Need 2...) [50%]\n'
                                       'tests/a.py::test_b XFAIL [100%]\n', 'pytest')
        self.assertEqual(outcomes['tests/a.py::test_a']['reason'], 'Need 2...')
        self.assertEqual(outcomes['tests/a.py::test_b']['flavor'], 'XFAIL')
        self.assertTrue(all(v['status'] == 'skipped' for v in outcomes.values()))

    def test_old_lowercase_xfail_and_unittest_expected_failure(self):
        pytest = audit.parse_capture('tests/a.py::test_a xfail [100%]\n', 'pytest')
        self.assertEqual(pytest['tests/a.py::test_a']['flavor'], 'XFAIL')
        django = audit.parse_capture('test_a (sample.Case) ... expected failure\n'
                                     'test_b (sample.Case) ... unexpected success\n', 'django')
        self.assertEqual(django['sample.Case.test_a']['status'], 'skipped')
        self.assertEqual(django['sample.Case.test_b']['status'], 'passed')

    def test_parenthesized_docstring_does_not_replace_pending_test_identity(self):
        text = ('test_lookup (admin_filters.tests.ListFiltersTests)\n'
                "Ensure ('fieldpath', ClassName ) lookups pass checks ... ok\n")
        parsed = audit.parse_capture(text, 'django')
        self.assertEqual(set(parsed), {'admin_filters.tests.ListFiltersTests.test_lookup'})
        self.assertEqual(parsed['admin_filters.tests.ListFiltersTests.test_lookup']['status'], 'passed')

    def test_unnamed_class_setup_skip_requires_exact_source_reason_match(self):
        cls = audit.ast.parse('class Example:\n def setUpClass(cls):\n  raise SkipTest("database feature unavailable")\n').body[0]
        sources = audit.Sources({}, audit.Inputs())
        sources.object = lambda task, test: {'class_node': cls, 'source': 'stored.tar!testbed/tests.py'}
        batch = {'text': 'header\nskipped "database feature unavailable"\n', 'line': 10}
        result = sources.class_setup_skip('task', 'tests.py::Example::test_a', batch)
        self.assertEqual(result['line'], 11)
        self.assertEqual(result['reason'], 'database feature unavailable')
        batch['text'] = 'skipped "different reason"\n'
        self.assertIsNone(sources.class_setup_skip('task', 'tests.py::Example::test_a', batch))

    def test_unique_property_abort_counts_only_other_requests_as_collateral(self):
        class StoredSourceFixture:
            def object(self, task, test):
                prop = test.endswith('::test_index')
                return {'kind': 'property' if prop else 'function', 'non_test': prop,
                        'source': 'stored_source.py', 'line': 4}
        selected = ['tests/a.py::Case::test_a', 'django/test/runner.py::Remote::test_index', 'tests/b.py::Case::test_b']
        text = b"TypeError: don't know how to make test from: <property object at 0x123>\n"
        call = {'run': {'results': [{'test_id': test, 'status': 'not_run'} for test in selected],
                       'events': [{'event': 'start', 'batch': 3, 'ids': [audit.django_label(t) for t in selected], 'offset': 0},
                                  {'event': 'end', 'batch': 3, 'returncode': 1, 'split': False, 'offset': len(text)}],
                       'evidence_files': {'runner.raw': 'stored_capture.raw'}, 'timed_out': False}}
        rows, _ = audit.batch_details('task', 0, call, selected, 'django', text, {}, StoredSourceFixture(), 'base')
        self.assertEqual((rows[0]['not_run_count'], rows[0]['collateral_not_run_count']), (3, 2))
        self.assertEqual(rows[0]['base_object_kinds'], 'property')


if __name__ == '__main__':
    unittest.main()
