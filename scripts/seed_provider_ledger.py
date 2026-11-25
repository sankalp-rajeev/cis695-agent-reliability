#!/usr/bin/env python3
"""Byte-copy a probe ledger once, preserving legacy UM/default-account spend."""

import argparse
import json
from pathlib import Path

from reliability.env import assert_clean_interpreter
from reliability.provider_spend import seed_provider_ledger


def main(argv=None):
    assert_clean_interpreter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from', dest='source', type=Path, required=True)
    parser.add_argument('--to', dest='destination', type=Path,
                        default=Path(__file__).resolve().parents[1] / 'runs/provider_spend_ledger.json')
    args = parser.parse_args(argv)
    print(json.dumps(seed_provider_ledger(args.source, args.destination), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
