"""Command-line semantic asset and reproducibility validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Literal

from .semantic_validation import ValidationResult, load_vocabulary, validate_graph

from rdflib import Graph
from rdflib.compare import isomorphic

__all__ = [
    "ValidationResult",
    "VerificationReport",
    "assert_graph_isomorphic",
    "load_vocabulary",
    "main",
    "run_asset_verification",
    "run_research_verify",
    "validate_graph",
]


@dataclass(frozen=True)
class VerificationReport:
    """Machine-readable result of the local research verification boundary."""

    mode: Literal["assets", "final"]
    returncode: int
    validation: dict[str, Any] | None = None
    parity: dict[str, Any] | None = None
    benchmark: dict[str, Any] | None = None
    errors: tuple[str, ...] = field(default_factory=tuple)

    @property
    def return_code(self) -> int:
        """Compatibility spelling for callers that use snake case."""

        return self.returncode

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "returncode": self.returncode,
            "validation": self.validation,
            "parity": self.parity,
            "benchmark": self.benchmark,
            "errors": list(self.errors),
        }


def assert_graph_isomorphic(generated: Graph, checked_in: Graph) -> None:
    """Fail when two RDF graphs differ semantically, independent of serialization."""

    if not isomorphic(generated, checked_in):
        raise AssertionError(
            "generated and checked-in RDF graphs are not isomorphic "
            f"(generated={len(generated)} triples, checked_in={len(checked_in)} triples)"
        )


def _asset_verification(
    root: Path, python: str, mode: Literal["assets", "final"]
) -> VerificationReport:
    parity: dict[str, Any] | None = None
    validation: dict[str, Any] | None = None
    benchmark: dict[str, Any] | None = None
    errors: list[str] = []
    try:
        from semantic_layer.kg.sap_dataset_generator import build_sap_support_graph
        from semantic_layer.research.benchmark_runner import build_validation_metadata

        checked_in_path = root / "semantic/data/sap_support_graph.ttl"
        with TemporaryDirectory(prefix="cifre-asset-") as temporary:
            generated_path = Path(temporary) / "sap_support_graph.ttl"
            generated_graph = build_sap_support_graph()
            generated_graph.serialize(destination=generated_path, format="turtle")
            checked_in_graph = Graph().parse(checked_in_path, format="turtle")
            assert_graph_isomorphic(generated_graph, checked_in_graph)
            parity = {
                "generated_path": str(generated_path),
                "checked_in_path": checked_in_path.relative_to(root).as_posix(),
                "generated_triples": len(generated_graph),
                "checked_in_triples": len(checked_in_graph),
                "isomorphic": True,
            }
            validation = build_validation_metadata(root)

            if mode == "final":
                # Final mode remains caller-owned: the artifact is temporary and
                # never writes results/latest_benchmark.json.
                import json
                import os
                import subprocess

                result_path = Path(temporary) / "cifre-benchmark-result.json"
                env = os.environ.copy()
                env["PYTHONPATH"] = str(root / "src") + os.pathsep + env.get("PYTHONPATH", "")
                command = [
                    python,
                    "-m",
                    "semantic_layer.research",
                    "--output",
                    str(result_path),
                ]
                completed = subprocess.run(
                    command,
                    cwd=root,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if completed.returncode:
                    raise RuntimeError(
                        f"benchmark command failed ({completed.returncode}): "
                        f"{completed.stderr.strip() or completed.stdout.strip()}"
                    )
                benchmark = {
                    "command": command,
                    "artifact": json.loads(result_path.read_text(encoding="utf-8")),
                }
    except Exception as error:  # verification must report drift, not mutate or raise
        errors.append(f"{type(error).__name__}: {error}")

    return VerificationReport(
        mode=mode,
        returncode=0 if not errors else 1,
        validation=validation,
        parity=parity,
        benchmark=benchmark,
        errors=tuple(errors),
    )


def run_research_verify(
    root: Path,
    python: str,
    *,
    mode: Literal["assets", "final"],
) -> VerificationReport:
    """Run the reusable asset boundary, optionally followed by final checks."""

    if mode not in {"assets", "final"}:
        raise ValueError("mode must be 'assets' or 'final'")
    return _asset_verification(Path(root).resolve(), python, mode)


def run_asset_verification(root: Path, python: str) -> VerificationReport:
    """Run only generation/parity, SHACL matrix, and prerequisite evidence."""

    return run_research_verify(root, python, mode="assets")


def main(root: Path | None = None) -> int:
    root = root or Path(__file__).resolve().parents[2]
    shapes = root / "semantic" / "shapes" / "sap_erp_shapes.ttl"
    valid = root / "semantic" / "ontology" / "sample-graph-valid.ttl"
    invalid = root / "semantic" / "ontology" / "sample-graph-invalid.ttl"

    vocabulary = load_vocabulary(root / "semantic" / "vocabulary" / "sap_erp.yaml")
    print(f"Vocabulary: {len(vocabulary)} concepts loaded")
    results = []
    for path in (valid, invalid):
        result = validate_graph(path, shapes)
        results.append(result)
        expected = "conforms" if path == valid else "fails as expected"
        outcome = "CONFORMS" if result.conforms else "DOES NOT CONFORM"
        print(f"{path.name}: {outcome} ({expected})")
        if not result.conforms:
            print(result.report_text)
    valid_result, invalid_result = results
    return 0 if valid_result.conforms and not invalid_result.conforms else 1


if __name__ == "__main__":
    raise SystemExit(main())
