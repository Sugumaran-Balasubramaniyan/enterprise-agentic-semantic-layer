import os
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_source_layout_and_build_configuration_are_declared() -> None:
    """Pin the source-only CI contract; wheel packaging is a separate concern."""
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    source_root = ROOT / "src"
    package_init = source_root / "semantic_layer" / "__init__.py"

    assert pyproject["project"]["name"] == "enterprise-agentic-semantic-layer"
    assert pyproject["project"]["version"] == "0.1.0"
    assert pyproject["build-system"]["build-backend"] == "setuptools.build_meta"
    assert pyproject["tool"]["setuptools"]["packages"]["find"]["where"] == ["src"]
    assert package_init.is_file()

    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(source_root)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import semantic_layer; print(semantic_layer.__file__)",
        ],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    assert Path(result.stdout.strip()).resolve() == package_init.resolve()


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
