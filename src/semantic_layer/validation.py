"""Command-line semantic asset validation."""

from pathlib import Path

from .semantic_validation import ValidationResult, load_vocabulary, validate_graph

__all__ = ["ValidationResult", "load_vocabulary", "main", "validate_graph"]


def main(root: Path | None = None) -> int:
    root = root or Path(__file__).resolve().parents[2]
    shapes = root / "semantic" / "shapes" / "insurance-shapes.ttl"
    valid = root / "semantic" / "ontology" / "sample-graph-valid.ttl"
    invalid = root / "semantic" / "ontology" / "sample-graph-invalid.ttl"

    vocabulary = load_vocabulary(root / "semantic" / "vocabulary" / "insurance.yaml")
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
