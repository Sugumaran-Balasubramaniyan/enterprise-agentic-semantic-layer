"""Claim-surface checks for the non-publication CIFRE prototype boundary."""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).parents[2]

NON_PUBLICATION_SURFACE = (
    "src/semantic_layer/__init__.py",
    "src/semantic_layer/adapters/__init__.py",
    "src/semantic_layer/adapters/cloud.py",
    "src/semantic_layer/adapters/duckdb.py",
    "src/semantic_layer/agents/__init__.py",
    "src/semantic_layer/agents/workflow.py",
    "src/semantic_layer/api/__init__.py",
    "src/semantic_layer/api/app.py",
    "src/semantic_layer/compiler/__init__.py",
    "src/semantic_layer/compiler/base.py",
    "src/semantic_layer/compiler/cloud_examples.py",
    "src/semantic_layer/compiler/duckdb.py",
    "src/semantic_layer/control.py",
    "src/semantic_layer/data_generation.py",
    "src/semantic_layer/demo.py",
    "src/semantic_layer/demo_sap.py",
    "src/semantic_layer/governance/__init__.py",
    "src/semantic_layer/governance/policy.py",
    "src/semantic_layer/kg/__init__.py",
    "src/semantic_layer/lineage/__init__.py",
    "src/semantic_layer/lineage/service.py",
    "src/semantic_layer/models.py",
    "src/semantic_layer/provenance/__init__.py",
    "src/semantic_layer/provenance/store.py",
    "src/semantic_layer/quality/__init__.py",
    "src/semantic_layer/quality/checks.py",
    "src/semantic_layer/query_planner/__init__.py",
    "src/semantic_layer/query_planner/service.py",
    "src/semantic_layer/registry/__init__.py",
    "src/semantic_layer/registry/service.py",
    "src/semantic_layer/research/__init__.py",
    "src/semantic_layer/resolver/__init__.py",
    "src/semantic_layer/resolver/service.py",
    "examples/README.md",
    "examples/example_questions.md",
    "examples/generated_query_plans/primary_erp_plan.json",
    "examples/generated_sql/README.md",
    "examples/generated_sql/databricks.sql",
    "examples/generated_sql/microsoft-fabric.sql",
    "examples/generated_sql/snowflake.sql",
    "mappings/databricks/france.yaml",
    "mappings/fabric/germany.yaml",
    "mappings/snowflake/united_kingdom.yaml",
    "data_products/acdoca_financials.yaml",
    "data_products/billing_analytics.yaml",
    "data_products/business_partners.yaml",
    "data_products/sales_orders.yaml",
)

LEGACY_URI_FAMILIES = (
    "http://" + "data.sap.com/",
    "http://" + "ontology.sap.com/",
    "https://" + "sap.example/erp/",
)
LEGACY_URI_CONTROL_DOCUMENTS = frozenset(
    {
        "docs/superpowers/specs/2026-09-19-cifre-research-prototype-hardening-design.md",
        "docs/superpowers/plans/2026-09-19-cifre-research-prototype-hardening.md",
        "docs/research/cifre-hardening-baseline.md",
    }
)


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _line_is_non_claim(text: str) -> bool:
    """Allow denials, future requirements, and functional gate vocabulary."""

    lowered = text.casefold()
    return bool(
        re.search(
            r"\b(?:not|no|never|without|disabled|unexecuted|unconfigured|future|proposed|"
            r"simulated?|synthetic|illustrative|local|repository-maintained|fail-closed|"
            r"extension seam|incomplete|not equivalent)\b",
            lowered,
        )
    )


def scan_claim_surfaces(paths: Sequence[Path]) -> list[str]:
    """Return unsupported claim findings as ``path:line:category:excerpt`` strings."""

    findings: list[str] = []
    patterns = (
        ("external-ownership", re.compile(r"\bSAP\s+SE\b|\bSAP\s+Labs\b|\bSAP\s+(?:France|Germany|United Kingdom)\s+Data Office\b", re.IGNORECASE)),
        ("external-certification", re.compile(r"certified_by:\s*SAP\b|certified by SAP\b|certification from SAP\b", re.IGNORECASE)),
        ("unsupported-fidelity", re.compile(r"high[- ]fidelity|production[- ](?:grade|ready|tested)|solved\s+(?:the\s+)?PhD", re.IGNORECASE)),
        ("unsupported-evaluation", re.compile(r"(?:100\s*%|0\s*%)[^\n]{0,80}(?:hallucination|grounded)|(?:hallucination|grounded)[^\n]{0,80}(?:100\s*%|0\s*%)|Vector\s+RAG", re.IGNORECASE)),
        ("external-partnership", re.compile(r"\b(?:official|affiliat(?:e|ed|ion)|strategic partnership|in partnership with)\b[^\n]{0,80}\bSAP\b|\bSAP\b[^\n]{0,80}\b(?:official|affiliat(?:e|ed|ion)|strategic partnership)\b", re.IGNORECASE)),
        ("unsupported-production", re.compile(r"\b(?:live|real|connected|connection)\s+(?:cloud|SAP|Databricks|Snowflake|Fabric)|\bcloud\s+(?:connection|integration|execution)\s+(?:is\s+)?(?:enabled|available|active)|\bproduction\s+data\b|\bcloud[- ]connected\b", re.IGNORECASE)),
    )
    for path in paths:
        relative = _relative(path)
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            if relative not in LEGACY_URI_CONTROL_DOCUMENTS:
                for uri in LEGACY_URI_FAMILIES:
                    if uri in line:
                        findings.append(f"{relative}:{number}:legacy-uri:{uri}")
            if _line_is_non_claim(line):
                continue
            for category, pattern in patterns:
                match = pattern.search(line)
                if match:
                    excerpt = " ".join(line.strip().split())[:140]
                    findings.append(f"{relative}:{number}:{category}:{excerpt}")
    return findings


def test_code_examples_mappings_and_data_products_have_supported_claims() -> None:
    findings = scan_claim_surfaces([ROOT / path for path in NON_PUBLICATION_SURFACE])

    assert findings == [], "unsupported claim surfaces:\n" + "\n".join(findings)


def test_claim_scan_preserves_neutral_identifiers_and_runtime_certified_gates(tmp_path: Path) -> None:
    fixture = tmp_path / "neutral.py"
    fixture.write_text(
        """\n"
        "# SAP-inspired synthetic domain identifiers are not an affiliation.\n"
        "CIFERP = 'ciferp:FinancialPosting'\n"
        "STATUS = 'CERTIFIED'\n"
        "# This is not a production-ready integration; the future deployment needs KMS.\n"
        "# A future Vector RAG baseline is proposed, not a current result.\n"
        "# A 0% hallucination guarantee is not claimed.\n"
        """,
        encoding="utf-8",
    )

    assert scan_claim_surfaces([fixture]) == []


def test_claim_scan_reports_forbidden_legacy_uri_outside_control_documents(tmp_path: Path) -> None:
    fixture = tmp_path / "forbidden.txt"
    fixture.write_text("source: " + LEGACY_URI_FAMILIES[0] + "legacy\n", encoding="utf-8")

    findings = scan_claim_surfaces([fixture])

    assert any("legacy-uri" in finding for finding in findings)
