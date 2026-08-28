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


def test_demo_commands_create_and_use_a_local_venv() -> None:
    required = [
        "python3 -m venv .venv",
        ".venv/bin/python -m pip install -e '.[dev]'",
        "make PYTHON=.venv/bin/python validate-semantic",
        "make PYTHON=.venv/bin/python demo",
    ]
    for path in [ROOT / "README.md", ROOT / "docs" / "interview-demo-guide.md"]:
        text = path.read_text()
        for command in required:
            assert command in text, (path, command)
        assert not any(line.strip() == "make demo" for line in text.splitlines())
        assert "make PYTHON=python3" not in text


def test_example_questions_does_not_require_bare_python() -> None:
    text = (ROOT / "examples" / "example_questions.md").read_text()
    assert "python3 -m semantic_layer.demo" in text
    assert "python -m semantic_layer.demo" not in text


def test_each_adr_has_required_decision_sections() -> None:
    adr_paths = sorted((ROOT / "docs" / "decisions").glob("ADR-00[1-8]-*.md"))
    assert len(adr_paths) == 8
    for path in adr_paths:
        text = path.read_text()
        for heading in ["## Context", "## Decision", "## Alternatives", "## Consequences"]:
            assert heading in text, (path, heading)
