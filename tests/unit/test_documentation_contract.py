from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_readme_contains_required_interview_sections() -> None:
    readme = (ROOT / "README.md").read_text()
    for heading in ["5-minute interview demo", "Architecture", "How to run", "Provenance"]:
        assert heading in readme


def test_documentation_contains_six_mermaid_diagrams() -> None:
    diagrams = sum(
        path.read_text().count("```mermaid")
        for path in (ROOT / "docs").rglob("*.md")
    )
    assert diagrams >= 6


def test_required_documentation_and_adrs_exist() -> None:
    required = [
        "architecture.md",
        "agent-architecture.md",
        "governance.md",
        "implementation-plan.md",
        "interview-demo-guide.md",
    ] + [f"ADR-{number:03d}-" for number in range(1, 9)]
    docs = ROOT / "docs"
    for path in required[:5]:
        assert (docs / path).is_file()
    adr_names = {path.name for path in (docs / "decisions").glob("ADR-*.md")}
    for prefix in required[5:]:
        assert any(name.startswith(prefix) for name in adr_names)


def test_mermaid_fences_are_balanced() -> None:
    # Planning/spec documents contain illustrative nested code blocks; the
    # published documentation surface is the README plus docs outside the
    # internal superpowers working area.
    paths = [ROOT / "README.md", *(ROOT / "docs").glob("*.md")]
    paths.extend((ROOT / "docs" / "decisions").glob("*.md"))
    for path in paths:
        text = path.read_text()
        assert text.count("```") % 2 == 0, path


def test_demo_guide_has_all_interview_timeboxes_and_cloud_boundary() -> None:
    guide = (ROOT / "docs" / "interview-demo-guide.md").read_text()
    for heading in ["30-second", "2-minute", "5-minute", "10-minute"]:
        assert heading in guide
    assert "not executed" in guide
    assert "curl" in guide
