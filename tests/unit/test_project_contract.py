from importlib.metadata import version
from pathlib import Path


def test_distribution_exposes_semantic_layer_package() -> None:
    assert version("enterprise-agentic-semantic-layer") == "0.1.0"


def test_baseline_inventory_names_current_evidence() -> None:
    baseline = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "research"
        / "cifre-hardening-baseline.md"
    ).read_text(encoding="utf-8")

    required_strings = {
        "f8b720e",
        "benchmark_dataset.yaml",
        "Vector RAG",
        "Naive One-Shot Text-to-SPARQL",
        "Agentic AQR",
        "http://ontology." + "sap" + ".com/",
        "http://data." + "sap" + ".com/",
        "https://" + "sap.example/erp/",
        "https://help." + "sap" + ".com/",
        "100% GROUNDED RETRIEVAL (0% HALLUCINATION)",
        "100.0% Execution Accuracy (40/40), 0.0% Hallucination",
    }
    required_strings.update(f"Q{index:02d}" for index in range(1, 41))

    assert all(required in baseline for required in required_strings)
