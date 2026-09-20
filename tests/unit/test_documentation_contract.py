"""Artifact-independent publication contracts for the Task 11 document set."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from semantic_layer.api.app import create_app

ROOT = Path(__file__).parents[2]
PUBLICATION_DOCS = (
    ROOT / "README.md",
    ROOT / "docs" / "agent-architecture.md",
    ROOT / "docs" / "architecture.md",
    ROOT / "docs" / "data-products.md",
    ROOT / "docs" / "evaluation.md",
    ROOT / "docs" / "federated-semantics.md",
    ROOT / "docs" / "governance.md",
    ROOT / "docs" / "implementation-plan.md",
    ROOT / "docs" / "ontology.md",
    ROOT / "docs" / "semantic-layer.md",
    *(ROOT / "docs" / "decisions").glob("ADR-00[1-8]-*.md"),
)
MARKDOWN_LINK_RE = re.compile(r"\[[^]]+\]\(([^)]+)\)")
MARKDOWN_FENCE_RE = re.compile(
    r"^(?P<indent> {0,3})(?P<fence>`{3,}|~{3,})(?P<suffix>[^\r\n]*)$"
)
DISCLAIMER = (
    "This is an independent, unaffiliated candidate prototype using synthetic "
    "support and product-lifecycle fixtures. It is not an SAP product, SAP "
    "publication, SAP-endorsed benchmark, or report of access to SAP internal "
    "data. The repository demonstrates a deterministic symbolic baseline and "
    "proposes future LLM/retrieval experiments; it does not claim completed PhD "
    "research or production readiness."
)


@dataclass(frozen=True)
class MarkdownFenceBlock:
    fence_char: str
    fence_length: int
    info_string: str
    content: str


def _parse_markdown_fence(line: str) -> tuple[str, int, str] | None:
    match = MARKDOWN_FENCE_RE.match(line)
    if match is None:
        return None
    fence = match.group("fence")
    return fence[0], len(fence), match.group("suffix").strip()


def _fenced_markdown_blocks(text: str) -> tuple[list[MarkdownFenceBlock], bool]:
    blocks: list[MarkdownFenceBlock] = []
    opening: tuple[str, int, str] | None = None
    block_lines: list[str] = []

    for line in text.splitlines():
        parsed = _parse_markdown_fence(line)
        if opening is None:
            if parsed is not None:
                opening = parsed
                block_lines = []
            continue

        if parsed is not None:
            fence_char, fence_length, suffix = parsed
            if suffix == "" and fence_char == opening[0] and fence_length >= opening[1]:
                blocks.append(
                    MarkdownFenceBlock(
                        fence_char=opening[0],
                        fence_length=opening[1],
                        info_string=opening[2],
                        content="\n".join(block_lines),
                    )
                )
                opening = None
                block_lines = []
                continue
        block_lines.append(line)

    return blocks, opening is None


def _compact_markdown(text: str) -> str:
    without_quote_markers = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    return " ".join(without_quote_markers.split())


def test_publication_claim_contract_and_links() -> None:
    """Pin public wording while allowing the final artifact to be absent."""

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    compact_readme = _compact_markdown(readme)
    assert DISCLAIMER in compact_readme

    first_research_heading = readme.index("## Synthetic KG and AQR research prototype")
    first_benchmark_command = readme.index("research-benchmark")
    assert DISCLAIMER in _compact_markdown(readme[:first_research_heading])
    assert DISCLAIMER in _compact_markdown(readme[:first_benchmark_command])

    first_screen = readme[:readme.index("## Local setup")]
    for label in (
        "Implemented locally",
        "Synthetic/simulated",
        "Proposed future work",
        "Not implemented",
    ):
        assert label in first_screen
    assert "KG/AQR" in first_screen
    secondary_heading = "## Secondary reference: federated ERP semantic layer"
    assert secondary_heading in first_screen
    assert first_screen.index("research-benchmark") < first_screen.index(secondary_heading)
    assert "[preliminary benchmark artifact](results/latest_benchmark.json)" in readme

    package_metadata = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert (
        'description = "Independent synthetic semantic-layer and knowledge-graph research prototype"'
        in package_metadata
    )
    assert "production-grade" not in package_metadata.lower()
    assert "sap labs" not in package_metadata.lower()

    for path in PUBLICATION_DOCS:
        assert path.is_file(), path
        text = path.read_text(encoding="utf-8")
        assert "synthetic" in text.lower(), path
        assert "proposed" in text.lower() or "not implemented" in text.lower(), path


def test_owned_markdown_fences_are_balanced() -> None:
    for path in PUBLICATION_DOCS:
        _, balanced = _fenced_markdown_blocks(path.read_text(encoding="utf-8"))
        assert balanced, path


def test_owned_markdown_links_have_syntax_without_resolving_artifacts() -> None:
    for path in PUBLICATION_DOCS:
        text = path.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK_RE.findall(text):
            assert target.strip() == target
            assert "\n" not in target
            assert target


def test_readme_contains_primary_system_sections() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in [
        "Synthetic KG and AQR research prototype",
        "Preliminary controlled synthetic benchmark",
        "Limitations and future research",
        "Secondary reference: federated ERP semantic layer",
        "System walkthrough",
        "Architecture and semantic contract",
        "Local setup",
    ]:
        assert heading in readme


def test_readme_documents_executable_local_commands() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for command in [
        "python3 -m venv .venv",
        ".venv/bin/python -m pip install -e '.[dev]'",
        "make PYTHON=.venv/bin/python validate-semantic",
        "make PYTHON=.venv/bin/python kg-validate",
        "make PYTHON=.venv/bin/python research-benchmark",
        "make PYTHON=.venv/bin/python research-demo",
        "make PYTHON=.venv/bin/python test",
        ".venv/bin/python data/generate_demo_data.py",
    ]:
        assert command in readme, command


def test_readme_api_table_matches_registered_fastapi_routes() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    application = create_app()
    for route in application.routes:
        if route.path not in application.openapi()["paths"]:
            continue
        for method in route.methods or set():
            assert f"{method.upper()} {route.path}" in readme, (method, route.path)
    for unsupported in ["/concepts/{id}/relationships", "/metrics/{id}"]:
        assert unsupported not in readme


def test_required_documentation_and_adrs_exist() -> None:
    for relative in [
        "docs/architecture.md",
        "docs/agent-architecture.md",
        "docs/data-products.md",
        "docs/evaluation.md",
        "docs/federated-semantics.md",
        "docs/governance.md",
        "docs/implementation-plan.md",
        "docs/ontology.md",
        "docs/semantic-layer.md",
    ]:
        assert (ROOT / relative).is_file()
    adr_paths = sorted((ROOT / "docs" / "decisions").glob("ADR-00[1-8]-*.md"))
    assert len(adr_paths) == 8
    for path in adr_paths:
        text = path.read_text(encoding="utf-8")
        for heading in ["## Context", "## Decision", "## Alternatives", "## Consequences"]:
            assert heading in text, (path, heading)


def test_owned_docs_use_neutral_namespace_examples() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in PUBLICATION_DOCS)
    assert "cifsup" in combined
    assert "cifppms" in combined
    assert "ciferp" in combined
    assert "cifskos" in combined
    assert not re.search(r"\bsap:", combined, flags=re.IGNORECASE)


def test_readme_states_mandatory_limitations_and_future_boundaries() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for fragment in [
        "synthetic",
        "no proprietary",
        "ontology is simplified",
        "small, controlled corpora",
        "deterministic and controlled",
        "no llm",
        "no production-scale graph or performance validation",
        "security, privacy, authentication, and governance controls are incomplete",
        "findings are preliminary",
        "no affiliation",
        "learned schema linking",
        "text-to-sparql",
        "learned repair",
        "hybrid graph/vector retrieval",
    ]:
        assert fragment in readme, fragment
