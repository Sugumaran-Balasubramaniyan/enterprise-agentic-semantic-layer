"""CLI for writing a caller-selected temporary CIFRE result artifact."""

from __future__ import annotations

import argparse
from pathlib import Path

from semantic_layer.kg.loader import SAPKnowledgeGraph
from semantic_layer.research.benchmark_runner import BenchmarkRunner

ROOT = Path(__file__).resolve().parents[3]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="caller-supplied temporary JSON output path",
    )
    parser.add_argument(
        "--dataset",
        dest="dataset_paths",
        action="append",
        type=Path,
        help="benchmark dataset path (repeat exactly twice for v1 and v2)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    dataset_paths = args.dataset_paths or (
        ROOT / "tests/research/benchmark_dataset_v1.yaml",
        ROOT / "tests/research/benchmark_dataset_v2.yaml",
    )
    if len(dataset_paths) != 2:
        raise SystemExit("--dataset must be supplied exactly twice")
    graph = SAPKnowledgeGraph()
    graph.load_ontologies(
        [
            ROOT / "semantic/ontology/sap_ppms.ttl",
            ROOT / "semantic/ontology/sap_support.ttl",
            ROOT / "semantic/data/sap_support_graph.ttl",
        ]
    )
    result = BenchmarkRunner(
        graph,
        dataset_paths=dataset_paths,
        result_path=args.output,
    ).run()
    print(
        f"schema-valid temporary artifact: {args.output} "
        f"corpora={len(result['corpus_runs'])} per_query={len(result['per_query'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
