"""Command-line entry point for the local golden evaluation."""

from pathlib import Path

from semantic_layer.evaluation import run_evaluation
from semantic_layer.registry import SemanticRegistry


def main() -> int:
    report = run_evaluation(SemanticRegistry.from_repository(Path.cwd()))
    print(report.summary())
    if report.failed_cases:
        print("Failed cases: " + ", ".join(report.failed_cases))
    return 1 if report.failed_cases else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
