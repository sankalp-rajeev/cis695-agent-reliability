"""Audit a completed rerun arm; reads trajectories and writes separate audit output.

Oracle access is confined to audit code. No model calls, containers or graders.
"""
import argparse
import json
from pathlib import Path

from reliability.benchmark.image_leakage import ROOT
from reliability.benchmark.rerun_leakage import audit_arm
from reliability.env import assert_clean_interpreter


def main():
    assert_clean_interpreter()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--image-results',type=Path,default=ROOT/'reports/next_phases/leakage_gaps/images')
    args=parser.parse_args()
    output=args.output or args.run/'leakage_audit'
    summary=audit_arm(args.run,output,args.image_results)
    print(json.dumps({k:summary[k] for k in ('rows','T3_tasks','T4_tasks')},sort_keys=True))
    # Evidence changes interpretation; incompleteness raises instead of passing.
    return 0


if __name__=='__main__':
    raise SystemExit(main())
