from pathlib import Path

from semantic_layer.semantic_validation import validate_graph

ROOT = Path(__file__).parents[2]
SHAPES = ROOT / "semantic" / "shapes" / "insurance-shapes.ttl"
VALID_GRAPH = ROOT / "semantic" / "ontology" / "sample-graph-valid.ttl"
INVALID_GRAPH = ROOT / "semantic" / "ontology" / "sample-graph-invalid.ttl"


def test_invalid_claim_graph_fails_shacl_validation() -> None:
    result = validate_graph(INVALID_GRAPH, SHAPES)
    assert result.conforms is False
    assert "claimDate" in result.report_text


def test_valid_claim_graph_conforms_to_shacl_shapes() -> None:
    result = validate_graph(VALID_GRAPH, SHAPES)
    assert result.conforms is True


def test_shacl_validation_reports_fixture_paths() -> None:
    result = validate_graph(INVALID_GRAPH, SHAPES)
    assert result.data_path == INVALID_GRAPH
    assert result.shapes_path == SHAPES
