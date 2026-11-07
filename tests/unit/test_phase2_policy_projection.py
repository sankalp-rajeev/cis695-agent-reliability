"""Synthetic checks for Phase 2 aggregation semantics; no benchmark execution."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[2] / 'scripts/phase2_policy_projection.py'
if not MODULE.exists():
    MODULE = Path(__file__).with_name('phase2_policy_projection.py')
SPEC = importlib.util.spec_from_file_location('phase2_policy_projection', MODULE)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class PolicyProjectionTests(unittest.TestCase):
    def test_strict_missing_evidence_does_not_erase_confirmed_FAIL(self):
        row = {'native_signal': 'FAIL', 'parser_only_complete_skip_strict': 'False',
               'parser_only_complete_skip_compatible': 'False'}
        self.assertEqual(audit.projected_verdict(row, True), 'RETAINED_NATIVE_FAIL')
        row['native_signal'] = 'PASS'
        self.assertEqual(audit.projected_verdict(row, True), 'NO_PROJECTED_BINARY_VERDICT')

    def test_CPU_only_ordinary_skips_are_distinct_from_normalized_XFAIL(self):
        rows = [{'skip_flavor': 'SKIPPED', 'reason_group': 'cores_CPU'},
                {'skip_flavor': 'XFAIL', 'reason_group': 'other'}]
        self.assertTrue(audit.cpu_only(rows, False))
        self.assertFalse(audit.cpu_only(rows, True))

    def test_not_found_is_not_proof_of_non_test_function_or_missing_module(self):
        row = {'base_object_kinds': 'function', 'diagnostic': 'ERROR: not found: test_a',
               'offending_selected_ids': '["tests/a.py::test_a"]'}
        self.assertEqual(audit.batch_class(row), 'other')
        row['diagnostic'] += " | ModuleNotFoundError: No module named 'xmlschema'"
        self.assertEqual(audit.batch_class(row), 'missing_module')
        row['base_object_kinds'] = 'helper_callable_for_unittest_loader'
        self.assertEqual(audit.batch_class(row), 'module_level_helper')
        row['offending_selected_ids'] = '["tests/a.py::Helper::test_a"]'
        self.assertEqual(audit.batch_class(row), 'non_test_function')


if __name__ == '__main__':
    unittest.main()
