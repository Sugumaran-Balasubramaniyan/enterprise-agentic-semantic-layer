import re
import subprocess
from pathlib import Path

from semantic_layer.api.app import create_app

ROOT = Path(__file__).parents[2]
MARKDOWN_LINK_RE = re.compile(r"\[[^]]+\]\(([^)]+)\)")
MERMAID_BLOCK_RE = re.compile(
    r"^ {0,3}```mermaid[ \t]*\n(.*?)^ {0,3}```[ \t]*$", re.MULTILINE | re.DOTALL
)
MARKDOWN_FENCE_RE = re.compile(r"^ {0,3}`{3,}[^`]*$", re.MULTILINE)
MERMAID_START_RE = re.compile(r"^ {0,3}```mermaid[ \t]*$", re.MULTILINE)


def _tracked_markdown_paths() -> list[Path]:
    completed = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "*.md"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [
        ROOT / line
        for line in completed.stdout.splitlines()
        if line and (ROOT / line).exists()
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
        slug = re.sub(r"-+", "-", slug).strip("-")
        anchors.add(slug)
    return anchors


def test_readme_contains_required_system_sections() -> None:
    readme = (ROOT / "README.md").read_text()
    for heading in ["System walkthrough", "Architecture", "How to run", "Provenance"]:
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
    ] + [f"ADR-{number:03d}-" for number in range(1, 9)]
    docs = ROOT / "docs"
    for path in required[:4]:
        assert (docs / path).is_file()
    adr_names = {path.name for path in (docs / "decisions").glob("ADR-*.md")}
    for prefix in required[5:]:
        assert any(name.startswith(prefix) for name in adr_names)


def test_mermaid_fences_are_balanced() -> None:
    for path in _tracked_markdown_paths():
        text = path.read_text()
        assert len(MARKDOWN_FENCE_RE.findall(text)) % 2 == 0, path


def test_mermaid_fences_close_and_use_github_safe_labels() -> None:
    """Keep every README/docs diagram renderable by GitHub's Mermaid renderer."""

    for path in [ROOT / "README.md", *(ROOT / "docs").rglob("*.md")]:
        text = path.read_text()
        blocks = MERMAID_BLOCK_RE.findall(text)
        assert len(MERMAID_START_RE.findall(text)) == len(blocks), path
        for block in blocks:
            assert "\\n" not in block, path
            assert "<br>" not in block, path


def test_system_walkthrough_commands_create_and_use_a_local_venv() -> None:
    required = [
        "python3 -m venv .venv",
        ".venv/bin/python -m pip install -e '.[dev]'",
        "make PYTHON=.venv/bin/python validate-semantic",
        "make PYTHON=.venv/bin/python demo",
    ]
    text = (ROOT / "README.md").read_text()
    for command in required:
        assert command in text, command
    assert not any(line.strip() == "make demo" for line in text.splitlines())
    assert "make PYTHON=python3" not in text


def test_repository_markdown_excludes_legacy_demo_script_language() -> None:
    """Keep tracked Markdown free of stale demo-script residue."""

    forbidden_fragments = (
        ("inter" "view"),
        ("recruit" "er"),
        ("inter" "view-demo-guide.md"),
        ("presentation-" "preparation"),
        ("presentation " "preparation"),
    )
    matches = [
        f"{path.relative_to(ROOT)}: {fragment}"
        for path in _tracked_markdown_paths()
        for fragment in forbidden_fragments
        if fragment in path.read_text().lower()
    ]
    assert not matches, "\n".join(matches)


def test_markdown_relative_links_resolve() -> None:
    broken: list[str] = []
    for path in _tracked_markdown_paths():
        text = path.read_text()
        anchors = _github_anchor_candidates(text)
        for target in MARKDOWN_LINK_RE.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if target.startswith("#"):
                if target[1:] not in anchors:
                    broken.append(f"{path.relative_to(ROOT)} -> {target}")
                continue
            relative_target, _, anchor = target.partition("#")
            resolved = (path.parent / relative_target).resolve()
            if not resolved.exists():
                broken.append(f"{path.relative_to(ROOT)} -> {target}")
                continue
            if anchor and resolved.suffix == ".md":
                target_anchors = _github_anchor_candidates(resolved.read_text())
                if anchor not in target_anchors:
                    broken.append(f"{path.relative_to(ROOT)} -> {target}")
    assert not broken, "\n".join(broken)


def test_mermaid_blocks_use_github_safe_line_breaks() -> None:
    offenders: list[str] = []
    for path in [ROOT / "README.md", *(ROOT / "docs").rglob("*.md")]:
        text = path.read_text()
        for block in MERMAID_BLOCK_RE.findall(text):
            if "\\n" in block:
                offenders.append(str(path.relative_to(ROOT)))
                break
    assert not offenders, "\n".join(offenders)


def test_example_questions_does_not_require_bare_python() -> None:
    text = (ROOT / "examples" / "example_questions.md").read_text()
    assert ".venv/bin/python -m semantic_layer.demo" in text
    assert "\npython -m semantic_layer.demo" not in text


def test_each_adr_has_required_decision_sections() -> None:
    adr_paths = sorted((ROOT / "docs" / "decisions").glob("ADR-00[1-8]-*.md"))
    assert len(adr_paths) == 8
    for path in adr_paths:
        text = path.read_text()
        for heading in ["## Context", "## Decision", "## Alternatives", "## Consequences"]:
            assert heading in text, (path, heading)


def test_readme_api_table_matches_registered_fastapi_routes() -> None:
    readme = (ROOT / "README.md").read_text()
    routes = {
        (route.path, method)
        for route in create_app().routes
        if route.path in create_app().openapi()["paths"]
        for method in route.methods or set()
    }
    assert "GET /health" in readme
    for route, method in routes:
        assert f"{method.upper()} {route}" in readme, (method, route)
    for unsupported in [
        "/concepts/{id}/relationships",
        "/metrics/{id}",
        "/data-products/{id}",
        "/mappings/{concept}",
    ]:
        assert unsupported not in readme


def test_readme_verification_section_identifies_latest_evidence() -> None:
    readme = (ROOT / "README.md").read_text()
    assert "2026-08-29 UTC" in readme
    assert "docs/verification-report.md" in readme
    assert "205 passed" in readme
    assert "195 passed" not in readme


def test_readme_documents_local_prerequisites_and_reproducibility_contract() -> None:
    readme = (ROOT / "README.md").read_text()
    required_fragments = [
        "Python 3.12",
        "No cloud credentials",
        "No LLM API key",
        "SEMANTIC_LAYER_ENV",
        "SEMANTIC_LAYER_SIGNING_KEY",
        "raw/",
        "curated/",
        "generate_demo_data.py",
        "seed",
        "as-of",
        "lockfile",
        "customer_id",
        "policy_id",
        "claim_id",
        "premium_id",
    ]
    for fragment in required_fragments:
        assert fragment in readme, fragment


def test_readme_documents_data_contract_and_clean_install() -> None:
    readme = (ROOT / "README.md").read_text()
    for fragment in [
        "git clone",
        "make setup",
        "schemas",
        "grain",
        "join keys",
        "curated fixtures",
        "configuration matrix",
    ]:
        assert fragment in readme, fragment
    assert "make PYTHON=.venv/bin/python setup" not in readme


def test_readme_documents_production_operations_and_security_boundary() -> None:
    """Keep local-demo limits and production operating requirements explicit."""

    readme = (ROOT / "README.md").read_text()
    required_fragments = [
        "## Production deployment and operating model",
        "### Local reference versus production service",
        "liveness-only",
        "request-body role is spoofable demo context",
        "development-only convenience",
        "### Environment separation and promotion",
        "### Identity, authorization, and privacy controls",
        "### Provenance retention, signing, and backup",
        "### Observability and CI coverage boundary",
        "No telemetry, tracing, metrics export, alerting, or security scanning is implemented",
        "### Operational failure and action matrix",
        "### Upgrade and rollback guidance",
        "fail closed",
    ]
    for fragment in required_fragments:
        assert fragment in readme, fragment


def test_readme_is_a_complete_repository_handbook_for_extension_and_release() -> None:
    """Keep the public handbook navigable and anchored to executable assets."""

    readme = (ROOT / "README.md").read_text()
    required_fragments = [
        "## Table of contents",
        "## Reader paths",
        "## Ownership, contribution, and review workflow",
        "## Semantic versioning, compatibility, and deprecation",
        "## Release process",
        "## Onboarding a country or domain",
        "## Capability-to-example traceability",
        "## Pilot implementation plan",
        "## Scale-out plan and promotion gates",
        "## Production extension matrix",
        "## Support and escalation",
        "[Business vocabulary](semantic/vocabulary/insurance.yaml)",
        "[Product taxonomy](semantic/taxonomy/insurance-products.ttl)",
        "[Insurance ontology](semantic/ontology/insurance.ttl)",
        "[SHACL shapes](semantic/shapes/insurance-shapes.ttl)",
        "[Metric definitions](semantic/metrics/metrics.yaml)",
        "[Business rules](semantic/rules/claims.yaml)",
        "[Certified data-product contracts](data_products/)",
        "[Federated mappings](mappings/)",
        "[Golden evaluation corpus](tests/golden/questions.yaml)",
        "[CI workflow](.github/workflows/ci.yml)",
        "breaking change",
        "deprecation window",
        "baseline and target-state assessment",
        "promotion gate",
        "semantic owner",
        "data-product owner",
        "platform owner",
        "security and privacy",
    ]
    for fragment in required_fragments:
        assert fragment in readme, fragment
