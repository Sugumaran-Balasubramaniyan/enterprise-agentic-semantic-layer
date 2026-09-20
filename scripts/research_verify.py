#!/usr/bin/env python3
"""Run the local CIFRE asset or final reproducibility boundary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from semantic_layer.validation import run_asset_worker, run_research_verify


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--assets-only",
        action="store_true",
        help="run generation/parity and validation assets without benchmark output",
    )
    parser.add_argument("--asset-worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--root", type=Path, help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.asset_worker:
        root = args.root or Path(__file__).resolve().parents[1]
        payload = run_asset_worker(root)
        print(json.dumps(payload, sort_keys=True, default=str))
        return int(payload["returncode"])
    root = Path(__file__).resolve().parents[1]
    mode = "assets" if args.assets_only else "final"
    report = run_research_verify(root, sys.executable, mode=mode)
    print(json.dumps(report.to_dict(), sort_keys=True, indent=2, default=str))
    return report.returncode


if __name__ == "__main__":
    raise SystemExit(main())
