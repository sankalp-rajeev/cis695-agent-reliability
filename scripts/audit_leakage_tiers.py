"""Interpret immutable stored audit findings; oracle-access audit boundary."""
import argparse
import json
from pathlib import Path

from reliability.benchmark.image_leakage import ROOT
from reliability.benchmark.leakage_interpretation import refresh_receipts, run_interpretation
from reliability.env import assert_clean_interpreter


def main():
    assert_clean_interpreter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-dir',type=Path,default=ROOT/'reports/next_phases/leakage_gaps')
    parser.add_argument('--refresh-receipts',action='store_true')
    args=parser.parse_args()
    summary=refresh_receipts(args.report_dir) if args.refresh_receipts else run_interpretation(args.report_dir)
    print(json.dumps({k:summary[k] for k in ['rows','T3_tasks','T4_tasks','comparable_T3_or_T4_count',
                                            'guard_removed_matches','masked_path_counts']},sort_keys=True))


if __name__=='__main__':
    main()
