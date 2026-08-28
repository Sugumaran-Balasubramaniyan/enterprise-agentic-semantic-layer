from importlib.metadata import version


def test_distribution_exposes_semantic_layer_package() -> None:
    assert version("enterprise-agentic-semantic-layer") == "0.1.0"
