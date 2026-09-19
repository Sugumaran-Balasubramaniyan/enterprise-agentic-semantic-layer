"""Command-line entry point for the SAP-KGBench research evaluation."""

from __future__ import annotations

from semantic_layer.kg.loader import SAPKnowledgeGraph
from semantic_layer.research.benchmark_runner import BenchmarkRunner


def main() -> int:
    kg = SAPKnowledgeGraph()
    kg.load_ontologies([
        "semantic/ontology/sap_ppms.ttl",
        "semantic/ontology/sap_support.ttl",
        "semantic/data/sap_support_graph.ttl",
    ])
    runner = BenchmarkRunner(kg)
    report = runner.run_evaluation()
    print("\n=======================================================")
    print("           SAP-KGBench Evaluation Results")
    print("=======================================================\n")
    print(report.to_markdown_table())
    print("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
