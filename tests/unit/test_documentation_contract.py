"""Artifact-independent publication contracts for the Task 11 document set."""

from __future__ import annotations

import re
import subprocess
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
DEFERRED_ARTIFACT_LINK = "results/latest_benchmark.json"
RESEARCH_HANDOFF_DOCS = (
    ROOT / "docs" / "research" / "cifre_phd_proposal.md",
    ROOT / "docs" / "research" / "technical_design_and_research_questions.md",
    ROOT / "docs" / "research" / "cifre-interview-brief.md",
    ROOT / "docs" / "verification-report.md",
)
RESEARCH_SOURCE_LINKS = (
    "../../src/semantic_layer/reasoning/schema_linker.py",
    "../../src/semantic_layer/reasoning/query_planner.py",
    "../../src/semantic_layer/reasoning/text_to_sparql.py",
    "../../src/semantic_layer/reasoning/reflective_agent.py",
    "../../src/semantic_layer/kg/loader.py",
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


def _tracked_markdown_paths() -> list[Path]:
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "*.md",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return [
        ROOT / line
        for line in completed.stdout.splitlines()
        if line and (ROOT / line).is_file()
    ]


def _github_anchor_candidates(text: str) -> set[str]:
    anchors: set[str] = set()
    for line in text.splitlines():
        if not line.startswith("#"):
            continue
        heading = line.lstrip("#").strip().lower()
        if not heading:
            continue
        slug = re.sub(r"[^\w\- ]+", "", heading)
        slug = slug.replace(" ", "-")
        anchors.add(re.sub(r"-+", "-", slug).strip("-"))
    return anchors


def _is_mermaid_info_string(info_string: str) -> bool:
    return info_string.split(maxsplit=1)[0].lower() == "mermaid" if info_string else False


def _mermaid_blocks(text: str) -> list[str]:
    blocks, _ = _fenced_markdown_blocks(text)
    return [block.content for block in blocks if _is_mermaid_info_string(block.info_string)]


def _count_mermaid_openers(text: str) -> int:
    return sum(
        1
        for line in text.splitlines()
        if (parsed := _parse_markdown_fence(line)) is not None
        and _is_mermaid_info_string(parsed[2])
    )


def test_publication_claim_contract_and_links() -> None:
    """Pin public wording while allowing the final artifact to be absent."""

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    compact_readme = _compact_markdown(readme)
    assert DISCLAIMER in compact_readme

    first_research_heading = readme.index("## Synthetic KG and AQR research prototype")
    first_reproducibility_command = readme.index(
        "make PYTHON=.venv/bin/python research-verify"
    )
    assert DISCLAIMER in _compact_markdown(readme[:first_research_heading])
    assert DISCLAIMER in _compact_markdown(readme[:first_reproducibility_command])

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
    assert first_screen.index("research-verify") < first_screen.index(secondary_heading)
    assert "research-benchmark" not in readme
    assert "Task 13" in readme
    assert "will wire" in readme
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


def test_research_handoff_contract_and_links() -> None:
    """Keep the research handoff source-verifiable and explicit about evidence."""

    for path in RESEARCH_HANDOFF_DOCS:
        assert path.is_file(), path

    proposal = (ROOT / "docs" / "research" / "cifre_phd_proposal.md").read_text(
        encoding="utf-8"
    )
    for section in (
        "Knowledge-Grounded Autonomous Query Reasoning for Enterprise Agentic AI",
        "Context and motivation",
        "Research gap",
        "Central research question",
        "Research questions and hypotheses",
        "Current deterministic baseline",
        "Controlled v1/v2 protocol",
        "Methodology",
        "Baselines and metrics",
        "Expected contributions",
        "Risks",
        "Falsifiable outcomes",
        "Three-year roadmap",
        "Non-goals",
    ):
        assert section in proposal, section
    for research_id in ("RQ1", "RQ2", "RQ3", "RQ4", "RQ5", "RQ6", "H1", "H2", "H3", "H4"):
        assert research_id in proposal, research_id
    assert DISCLAIMER in _compact_markdown(proposal)
    assert "SAP Labs France" not in proposal
    assert "100.0%" not in proposal
    assert "0% hallucination" not in proposal.lower()

    technical = (
        ROOT / "docs" / "research" / "technical_design_and_research_questions.md"
    ).read_text(encoding="utf-8")
    for topic in (
        "RDF vs property graph",
        "OWL",
        "SHACL",
        "OWL vs SHACL",
        "SPARQL",
        "property paths",
        "multi-hop",
        "bounded query repair",
        "unknown entities",
        "ambiguous entities",
        "constraining LLM-generated SPARQL",
        "execution vs exact-match accuracy",
        "vector RAG",
        "millions of documents",
        "ontology evolution",
        "research contribution vs software engineering",
    ):
        assert topic.lower() in technical.lower(), topic
    for research_id in ("RQ1", "RQ2", "RQ3", "RQ4", "RQ5"):
        assert research_id in technical, research_id
    assert "Implemented" in technical
    assert "Proposed" in technical

    brief = (ROOT / "docs" / "research" / "cifre-interview-brief.md").read_text(
        encoding="utf-8"
    )
    for required in (
        "cifre-synthetic-aqr-v1",
        "results/latest_benchmark.json",
        "make PYTHON=.venv/bin/python research-verify",
        "independent",
        "no affiliation",
        "Task 13",
    ):
        assert required.lower() in brief.lower(), required
    for link in RESEARCH_SOURCE_LINKS:
        assert f"]({link})" in brief, link

    verification = (ROOT / "docs" / "verification-report.md").read_text(
        encoding="utf-8"
    )
    for field in (
        "Commit",
        "SHA-256",
        "Commands",
        "lock",
        "Environment",
        "Known limitations",
        "Task 13",
    ):
        assert field.lower() in verification.lower(), field
    assert re.search(r"(?i)not yet (?:created|available|final)", verification)

    baseline = (ROOT / "docs" / "research" / "cifre-hardening-baseline.md").read_text(
        encoding="utf-8"
    )
    assert "final handoff" in baseline.lower()


def test_owned_markdown_fences_are_balanced() -> None:
    for path in _tracked_markdown_paths():
        _, balanced = _fenced_markdown_blocks(path.read_text(encoding="utf-8"))
        assert balanced, path


def test_documentation_contains_six_mermaid_diagrams() -> None:
    diagrams = sum(
        len(_mermaid_blocks(path.read_text(encoding="utf-8")))
        for path in (ROOT / "docs").rglob("*.md")
    )
    assert diagrams >= 6


def test_mermaid_fences_close_and_use_github_safe_labels() -> None:
    for path in [ROOT / "README.md", *(ROOT / "docs").rglob("*.md")]:
        text = path.read_text(encoding="utf-8")
        blocks = _mermaid_blocks(text)
        assert _count_mermaid_openers(text) == len(blocks), path
        for block in blocks:
            assert "\\n" not in block, path
            assert "<br>" not in block, path


def test_owned_markdown_links_have_syntax_without_resolving_artifacts() -> None:
    for path in PUBLICATION_DOCS:
        text = path.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK_RE.findall(text):
            assert target.strip() == target
            assert "\n" not in target
            assert target


def test_markdown_relative_links_and_anchors_resolve_except_deferred_artifact() -> None:
    broken: list[str] = []
    for path in _tracked_markdown_paths():
        text = path.read_text(encoding="utf-8")
        anchors = _github_anchor_candidates(text)
        for target in MARKDOWN_LINK_RE.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if target.startswith("#"):
                if target[1:] not in anchors:
                    broken.append(f"{path.relative_to(ROOT)} -> {target}")
                continue
            relative_target, _, anchor = target.partition("#")
            if relative_target == DEFERRED_ARTIFACT_LINK:
                continue
            resolved = (path.parent / relative_target).resolve()
            if not resolved.exists():
                broken.append(f"{path.relative_to(ROOT)} -> {target}")
                continue
            if anchor and resolved.suffix == ".md":
                target_anchors = _github_anchor_candidates(resolved.read_text(encoding="utf-8"))
                if anchor not in target_anchors:
                    broken.append(f"{path.relative_to(ROOT)} -> {target}")
    assert not broken, "\n".join(broken)


def test_mermaid_blocks_use_github_safe_line_breaks() -> None:
    offenders: list[str] = []
    for path in [ROOT / "README.md", *(ROOT / "docs").rglob("*.md")]:
        if any("\\n" in block for block in _mermaid_blocks(path.read_text(encoding="utf-8"))):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, "\n".join(offenders)


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
        "make PYTHON=.venv/bin/python research-verify",
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
