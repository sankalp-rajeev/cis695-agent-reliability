"""Only actual, hash-frozen runner formats from this audit supply fixtures."""
import importlib.util
import json
import unittest
from pathlib import Path

OUT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('audit_resume', OUT/'resume.py')
RUN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN)
OLD = RUN.OLD
FIXED = RUN.parser_namespace(fixed=True)
FIXTURES = json.loads((OUT/'observed_parser_fixtures.json').read_text())


class ObservedParserTests(unittest.TestCase):
    def fixture(self, kind):
        f = next(row for row in FIXTURES if row['kind']==kind)
        self.assertIn(f['raw_line'], (OUT/f['source']).read_text())
        return f

    def test_exact_observed_id_is_preserved(self):
        f = self.fixture('exact')
        for parser in (OLD, FIXED):
            result = parser['_parse_pytest'](f['raw_line'], (f['selected_id'],))
            self.assertEqual({k:v.value for k,v in result.items()},
                             {f['selected_id']:f['observed_status']})

    def test_observed_parameter_case_maps_to_selected_family(self):
        f = self.fixture('parameter_family')
        self.assertEqual(OLD['_parse_pytest'](f['raw_line'], (f['selected_id'],)), {})
        result = FIXED['_parse_pytest'](f['raw_line'], (f['selected_id'],))
        self.assertEqual({k:v.value for k,v in result.items()},
                         {f['selected_id']:f['observed_status']})

    def test_observed_concrete_parameter_id_stays_concrete_when_selected(self):
        f = self.fixture('parameter_family')
        for parser in (OLD, FIXED):
            result = parser['_parse_pytest'](f['raw_line'], (f['raw_test_id'],))
            self.assertEqual({k:v.value for k,v in result.items()},
                             {f['raw_test_id']:f['observed_status']})

    def test_actual_not_found_output_does_not_become_pass(self):
        folder = OUT/'phase2/pytest-dev__pytest-5809/base/initial'
        events = [json.loads(s) for s in (folder/'batch_events.jsonl').read_text().splitlines()]
        ends = {e['batch']:e for e in events if e['event']=='end'}
        event = next(e for e in events if e['event']=='start' and ends[e['batch']]['returncode']==4)
        raw = (folder/('batch_%04d.raw'%event['batch'])).read_text()
        self.assertIn('not found:', raw)
        for parser in (OLD, FIXED):
            self.assertEqual(parser['_parse_pytest'](raw, tuple(event['ids'])), {})


if __name__=='__main__':
    unittest.main(verbosity=2)
