"""Run the extended audit and immutable legacy golden on the stored main study."""
import argparse
import json
from pathlib import Path

from reliability.benchmark.image_leakage import ROOT
from reliability.benchmark.leakage_study import run_study
from reliability.env import assert_clean_interpreter


def main():
    assert_clean_interpreter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'reports/next_phases/leakage_gaps')
    parser.add_argument('--image-results', type=Path, default=ROOT/'reports/next_phases/leakage_gaps/images')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = run_study(args.output, image_root=args.image_results)
    print(json.dumps(result, sort_keys=True))
    return int(bool(result['golden_violations'] or result['confirmed_tasks']))


if __name__ == '__main__':
    raise SystemExit(main())
