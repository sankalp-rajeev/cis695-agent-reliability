"""Synthetic Phase 5 checks. Added for review; not executed in Phase 5.

No repository experiment data, benchmark imports, containers or model calls.
"""

import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    'phase5_replay', Path(__file__).resolve().parents[2] / 'scripts/phase5_replay.py')
replay = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(replay)


class TierGateChecks(unittest.TestCase):
    def setUp(self):
        self.record = {
            'before': ['a.py::a', 'b.py::b'],
            'before_by_tier': {'1': ['a.py::a'], '2': ['a.py::a', 'b.py::b']},
            'after': ['a.py::a'], 'after_by_tier': {'1': ['a.py::a'], '2': []},
        }

    def test_exact_match_and_lowest_tier(self):
        result = replay.tier_gate(['a.py::a', 'b.py::b'], self.record)
        self.assertEqual(result['matched'], 'before')
        self.assertEqual(result['tiers'], {'a.py::a': 1, 'b.py::b': 2})
        self.assertEqual(replay.tier_gate(['a.py::a'], self.record)['matched'], 'after')

    def test_reordered_list_is_rejected(self):
        result = replay.tier_gate(['b.py::b', 'a.py::a'], self.record)
        self.assertEqual(result['matched'], 'none')
        self.assertIsNone(result['tiers'])

    def test_one_id_off_is_rejected(self):
        self.assertEqual(replay.tier_gate(['a.py::a', 'c.py::c'], self.record)['matched'], 'none')

    def test_tier_union_missing_or_extra_is_rejected(self):
        for tier2 in ([], ['b.py::b', 'extra.py::x']):
            self.record['before_by_tier']['2'] = tier2
            result = replay.tier_gate(['a.py::a', 'b.py::b'], self.record)
            self.assertEqual(result['matched'], 'none')

    def test_both_exact_matches_use_before(self):
        self.record['after'] = list(self.record['before'])
        self.record['after_by_tier'] = self.record['before_by_tier']
        result = replay.tier_gate(self.record['before'], self.record)
        self.assertEqual(result['matched'], 'before')
        self.assertEqual(result['exact_matches'], ['before', 'after'])


class ReplayChecks(unittest.TestCase):
    def test_rule_tiers_then_changed_name_then_source_order(self):
        modules = ['tests/test_z.py', 'tests/test_target.py', 'tests/test_a.py', 'tests/test_second.py']
        tiers = {m: 1 for m in modules}
        tiers['tests/test_target.py'] = 2
        self.assertEqual(replay.rule_order(modules, tiers, ['src/target.py', 'src/second.py']),
            ['tests/test_second.py', 'tests/test_z.py', 'tests/test_a.py', 'tests/test_target.py'])

    def test_cutoff_and_start_end_bounds(self):
        modules = ['a.py', 'b.py', 'c.py']
        costs = {'a.py': 10., 'b.py': 25., 'c.py': 5.}
        tests = ['a.py::a', 'b.py::b1', 'b.py::b2', 'c.py::c']
        result = replay.replay(modules, costs, tests, ['b.py::b1'], 30)
        self.assertEqual(result['modules_run'], ['a.py', 'b.py'])
        self.assertEqual(result['modules_not_reached'], ['c.py'])
        self.assertEqual(result['modules_in_progress'], ['b.py'])
        self.assertEqual(result['share_not_reached'], .25)
        self.assertEqual(result['first_regression_start_s'], 10.)
        self.assertIsNone(result['first_regression_end_s'])
        self.assertEqual(result['full_first_regression_end_s'], 35.)
        self.assertEqual(result['reference_kept_start'], ['b.py::b1'])
        self.assertEqual(result['reference_kept_end'], [])
        self.assertTrue(result['binds'])
        at_end = replay.replay(modules, costs, tests, ['b.py::b1'], 35)
        self.assertEqual(at_end['first_regression_end_s'], 35.)
        self.assertEqual(at_end['modules_not_reached'], ['c.py'])

    def test_nonbinding_budget_is_noninformative(self):
        result = replay.replay(['a.py'], {'a.py': 10.}, ['a.py::a'], ['a.py::a'], 10)
        self.assertFalse(result['binds'])
        self.assertFalse(result['informative'])
        self.assertEqual(result['first_regression_start_s'], 0.)
        self.assertEqual(result['first_regression_end_s'], 10.)

    def test_outside_reference_never_becomes_kept_or_missed(self):
        result = replay.selector_metrics(['a.py::a', 'b.py::b'],
            ['a.py::a', 'outside.py::x'], ['a.py::a', 'b.py::b'])
        self.assertEqual(result['reference_kept'], ['a.py::a'])
        self.assertEqual(result['reference_missed'], ['b.py::b'])
        self.assertEqual(result['outside_reference_count'], 1)
        self.assertEqual(result['outside_reference_ids'], ['outside.py::x'])
        self.assertEqual(result['share_v2_kept'], .5)
        self.assertIsNone(replay.selector_metrics(['a'], None, ['a'])['reference_missed'])

    def test_retry_and_split_parent_durations_are_summed(self):
        events = [
            {'event': 'start', 'module': 'a.py'},
            {'event': 'end', 'module': 'a.py', 'duration_s': 2., 'split': True},
            {'event': 'end', 'module': 'a.py', 'duration_s': 3., 'retry': True},
            {'event': 'end', 'module': 'a.py', 'duration_s': 5., 'retry': True},
            {'event': 'end', 'module': 'b.py', 'duration_s': 7.},
        ]
        self.assertEqual(replay.module_costs(events), {'a.py': 10., 'b.py': 7.})
        self.assertEqual(replay.collection_costs([
            {'module': 'a.py', 'duration_s': 1.}, {'module': 'a.py', 'duration_s': 2.}]), {'a.py': 3.})

    def test_quantile_right_censoring(self):
        self.assertEqual(replay.quantile([1., 2., 3., None], .25), 1.75)
        self.assertIsNone(replay.quantile([1., 2., 3., None], .75))


if __name__ == '__main__':
    unittest.main()
