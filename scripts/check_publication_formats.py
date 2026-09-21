#!/usr/bin/env python3
"""Parse every tracked JSON, YAML, and Turtle publication input."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml
from rdflib import Graph


def _tracked(root: Path) -> list[Path]:
    output = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"])
    return [
        root / relative
        for relative in output.decode("utf-8").split("\0")
        if relative and (root / relative).is_file()
    ]


def _parse(root: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    counts = {".json": 0, ".yaml": 0, ".yml": 0, ".ttl": 0}
    for path in _tracked(root):
        suffix = path.suffix.lower()
        if suffix not in counts:
            continue
        try:
            if suffix == ".json":
                json.loads(path.read_bytes())
            elif suffix in {".yaml", ".yml"}:
                yaml.safe_load(path.read_text(encoding="utf-8"))
            else:
                Graph().parse(path, format="turtle")
            counts[suffix] += 1
        except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
            errors.append(f"{path.relative_to(root)}: {type(error).__name__}: {error}")
    if errors:
        return 1, errors
    print(
        "formats: "
        + ", ".join(f"{suffix}={counts[suffix]}" for suffix in (".json", ".yaml", ".yml", ".ttl"))
    )
    return 0, []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        returncode, errors = _parse(args.root.resolve())
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"format inventory failed: {error}", file=sys.stderr)
        return 1
    if errors:
        print("format parse failures:", file=sys.stderr)
        print("\n".join(errors), file=sys.stderr)
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
