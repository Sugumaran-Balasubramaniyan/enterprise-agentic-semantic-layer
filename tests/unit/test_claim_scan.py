"""Claim-surface checks for the non-publication CIFRE prototype boundary."""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

import pytest

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
_NEGATION_PREFIX = re.compile(
    r"\b(?:not|no|never|without|isn't|aren't|wasn't|weren't|doesn't|don't|didn't|"
    r"cannot|can't|won't|wouldn't|couldn't)\b",
    re.IGNORECASE,
)
_FUTURE_PREFIX = re.compile(
    r"\b(?:future|proposed|planned|hypothetical)\b(?:\s+\w+){0,4}\s*$|"
    r"\b(?:would|could|may|might|should)\s+(?:be\s+)?$",
    re.IGNORECASE,
)
_NEGATION_SUFFIX = re.compile(
    r"\b(?:is|are|was|were|be|been|being|does|do|did|will|would|could|may|might|"
    r"should|can|has|have|had)\s+(?:not|never)\b|"
    r"\b(?:isn't|aren't|wasn't|weren't|doesn't|don't|didn't|won't|wouldn't|"
    r"couldn't|can't|cannot)\b|\b(?:not|never)\s+(?:be\s+)?\w+\b",
    re.IGNORECASE,
)
_FUTURE_SUFFIX = re.compile(
    r"\b(?:future|proposed|planned|hypothetical)\b(?:\s+\w+){0,4}\b|"
    r"\b(?:will|would|could|may|might|should)\s+(?:be\s+)?"
    r"(?:future|proposed|planned|hypothetical)\b|"
    r"\b(?:is|are|was|were)\s+(?:a\s+)?(?:future|proposed|planned|hypothetical)\b",
    re.IGNORECASE,
)


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _claim_is_non_claim(text: str, start: int, end: int) -> bool:
    """Allow only the specific denied/future claim span, not its whole line."""

    prefix = text[:start]
    clause_start = max(prefix.rfind(";"), prefix.rfind("."), prefix.rfind("\n")) + 1
    clause_prefix = prefix[clause_start:]
    if _NEGATION_PREFIX.search(clause_prefix) or _FUTURE_PREFIX.search(clause_prefix):
        return True

    clause_ends = [position for delimiter in ";.\n" if (position := text.find(delimiter, end)) >= 0]
    clause_end = min(clause_ends, default=len(text))
    suffix = text[end:clause_end]
    return bool(_NEGATION_SUFFIX.search(suffix) or _FUTURE_SUFFIX.search(suffix))


def scan_claim_surfaces(paths: Sequence[Path]) -> list[str]:
    """Return unsupported claim findings as ``path:line:category:excerpt`` strings."""

    findings: list[str] = []
    patterns = (
        (
            "external-ownership",
            re.compile(
                r"\bSAP\s+SE\b|\bSAP\s+Labs\b|\bSAP\s+(?:France|Germany|United Kingdom)\s+Data Office\b",
                re.IGNORECASE,
            ),
        ),
        (
            "external-publication",
            re.compile(
                r"\b(?:publisher|publication)\s*:\s*SAP\b|\bSAP\s+publication\b|"
                r"\b(?:published|publication|endorsed|sponsored|officially supported)\s+(?:by|from)?\s*SAP\b|"
                r"\bSAP[- ]?(?:endorsed|sponsored|official|partnership)\b|"
                r"\bSAP\s+(?:sponsorship|partnership)\b|"
                r"\b(?:sponsorship|partnership)\s+(?:with|from|by)\s+SAP\b|"
                r"\bin partnership with SAP\b|\bofficial(?:ly)?\s+(?:sponsored|endorsed|supported)\s+by SAP\b|"
                r"\bofficial SAP\b",
                re.IGNORECASE,
            ),
        ),
        (
            "external-certification",
            re.compile(
                r"certified_by:\s*SAP\b|certified by SAP\b|certification from SAP\b",
                re.IGNORECASE,
            ),
        ),
        (
            "unsupported-fidelity",
            re.compile(r"high[- ]fidelity|production[- ](?:grade|ready|tested)", re.IGNORECASE),
        ),
        (
            "unsupported-production",
            re.compile(
                r"\b(?:deployed|hosted|production[- ](?:deployment|service|system)|live\s+(?:service|cloud|connection)|"
                r"real\s+(?:cloud|service)|connected\s+(?:cloud|service)|cloud[- ]connected)\b|"
                r"\bcloud\s+(?:connection|integration|execution)\s+(?:is\s+)?(?:enabled|available|active)\b|"
                r"\bproduction\s+data\b",
                re.IGNORECASE,
            ),
        ),
        (
            "unsupported-evaluation",
            re.compile(
                r"(?:100\s*%|0\s*%)[^\n]{0,80}(?:hallucination|grounded)|"
                r"(?:hallucination|grounded)[^\n]{0,80}(?:100\s*%|0\s*%)|"
                r"\bzero[- ]hallucination(?:\s+guarantee)?\b|\bhallucination\s+guarantee\b",
                re.IGNORECASE,
            ),
        ),
        ("fake-vector-rag", re.compile(r"\bVector\s+RAG\b", re.IGNORECASE)),
        (
            "unsupported-superiority",
            re.compile(
                r"\b(?:superior(?:ity)?|outperform(?:s|ed|ing)?|outperformance|better than|state[- ]of[- ]the[- ]art)\b",
                re.IGNORECASE,
            ),
        ),
        ("solved-phd", re.compile(r"\bsolved\s+(?:the\s+)?PhD\b", re.IGNORECASE)),
    )
    for path in paths:
        relative = _relative(path)
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            if relative not in LEGACY_URI_CONTROL_DOCUMENTS:
                for uri in LEGACY_URI_FAMILIES:
                    if uri in line:
                        findings.append(f"{relative}:{number}:legacy-uri:{uri}")
            for category, pattern in patterns:
                for match in pattern.finditer(line):
                    if _claim_is_non_claim(line, match.start(), match.end()):
                        continue
                    excerpt = " ".join(line.strip().split())[:140]
                    findings.append(f"{relative}:{number}:{category}:{excerpt}")
    return findings


def test_code_examples_mappings_and_data_products_have_supported_claims() -> None:
    findings = scan_claim_surfaces([ROOT / path for path in NON_PUBLICATION_SURFACE])

    assert findings == [], "unsupported claim surfaces:\n" + "\n".join(findings)


def test_claim_scan_preserves_neutral_identifiers_and_runtime_certified_gates(tmp_path: Path) -> None:
    fixture = tmp_path / "neutral.py"
    fixture.write_text(
        """\
# SAP-inspired synthetic domain identifiers are not an affiliation.
CIFERP = 'ciferp:FinancialPosting'
STATUS = 'CERTIFIED'
# This is not a production-ready integration; the future deployment needs KMS.
# A future Vector RAG baseline is proposed, not a current result.
# A 0% hallucination guarantee is not claimed.
""",
        encoding="utf-8",
    )

    assert scan_claim_surfaces([fixture]) == []


def test_claim_scan_reports_each_forbidden_claim_category(tmp_path: Path) -> None:
    fixture = tmp_path / "claims.txt"
    fixture.write_text(
        """\
SAP SE affiliation and SAP Labs ownership.
Published by SAP; SAP-endorsed, officially sponsored by SAP, and in partnership with SAP.
An official SAP sponsorship is asserted.
This production-ready service is deployed and hosted as a live cloud connection.
certified_by: SAP Enterprise Governance Board.
100% grounded retrieval and 0% hallucination; zero-hallucination guarantee.
Vector RAG superiority over the baseline solved the PhD problem.
source: http://data.sap.com/legacy
""",
        encoding="utf-8",
    )

    findings = scan_claim_surfaces([fixture])
    categories = {finding.split(":", 3)[2] for finding in findings}

    assert categories >= {
        "external-ownership",
        "external-publication",
        "unsupported-production",
        "external-certification",
        "unsupported-evaluation",
        "fake-vector-rag",
        "unsupported-superiority",
        "solved-phd",
        "legacy-uri",
    }


def test_claim_scan_checks_claim_context_without_skipping_mixed_lines(tmp_path: Path) -> None:
    fixture = tmp_path / "mixed.txt"
    fixture.write_text(
        """\
owner: SAP SE; future synthetic contract wording does not change ownership.
A future production deployment is proposed, not implemented.
This is not a high-fidelity production-ready service.
""",
        encoding="utf-8",
    )

    findings = scan_claim_surfaces([fixture])

    assert any("external-ownership" in finding for finding in findings)
    assert not any("unsupported-production" in finding for finding in findings)
    assert not any("unsupported-fidelity" in finding for finding in findings)


def test_claim_scan_suppresses_only_same_clause_future_or_negative_wording(tmp_path: Path) -> None:
    fixture = tmp_path / "clause_context.txt"
    fixture.write_text(
        """\
This production-ready service is future work.
This Vector RAG baseline is proposed future work.
SAP-endorsed claim is not made.
owner: SAP SE; future synthetic contract.
""",
        encoding="utf-8",
    )

    findings = scan_claim_surfaces([fixture])

    assert len(findings) == 1
    assert "external-ownership" in findings[0]


@pytest.mark.parametrize(
    "text",
    (
        "SAP publication is not asserted.",
        "SAP publication isn't real.",
        "SAP publication will be proposed.",
        "SAP SE is not affiliated.",
        "no sponsorship by SAP is claimed.",
        "SAP-endorsed is never endorsed.",
        "SAP publication is a proposed future comparison.",
        "SAP publication would be future work.",
    ),
)
def test_claim_scan_accepts_general_same_clause_nonclaims(tmp_path: Path, text: str) -> None:
    fixture = tmp_path / "general_nonclaim.txt"
    fixture.write_text(text + "\n", encoding="utf-8")

    assert scan_claim_surfaces([fixture]) == []


@pytest.mark.parametrize(
    "text",
    (
        "publisher: SAP",
        "SAP publication",
        "SAP-endorsed",
        "sponsored by SAP",
        "in partnership with SAP",
    ),
)
def test_claim_scan_reports_present_publication_forms(tmp_path: Path, text: str) -> None:
    fixture = tmp_path / "present_publication.txt"
    fixture.write_text(text + "\n", encoding="utf-8")

    findings = scan_claim_surfaces([fixture])

    assert len(findings) == 1
    assert "external-publication" in findings[0]


@pytest.mark.parametrize(
    "text",
    (
        "SAP publication; future comparison.",
        "future comparison; SAP publication.",
        "SAP SE. future synthetic contract.",
        "future work\nSAP-endorsed.",
    ),
)
def test_claim_scan_keeps_positive_claims_in_other_clauses(tmp_path: Path, text: str) -> None:
    fixture = tmp_path / "mixed_clauses.txt"
    fixture.write_text(text + "\n", encoding="utf-8")

    findings = scan_claim_surfaces([fixture])

    assert findings


def test_claim_scan_detects_publication_field_and_phrase_forms_but_not_nonclaims(tmp_path: Path) -> None:
    positive = tmp_path / "publication_positive.txt"
    positive.write_text(
        """\
publisher: SAP
SAP publication
published by SAP
SAP-endorsed
sponsored by SAP
SAP sponsorship
partnership with SAP
SAP partnership
""",
        encoding="utf-8",
    )
    negative = tmp_path / "publication_negative.txt"
    negative.write_text(
        """\
publisher: repository-maintained synthetic contract
No SAP publication is made.
A future SAP publication is proposed.
SAP-endorsed claim is not made.
A future partnership with SAP is proposed.
Sponsorship by SAP is not claimed.
""",
        encoding="utf-8",
    )

    positive_findings = scan_claim_surfaces([positive])
    negative_findings = scan_claim_surfaces([negative])

    assert len(positive_findings) == 8
    assert all("external-publication" in finding for finding in positive_findings)
    assert negative_findings == []


def test_claim_scan_reports_forbidden_legacy_uri_outside_control_documents(tmp_path: Path) -> None:
    fixture = tmp_path / "forbidden.txt"
    fixture.write_text("source: " + LEGACY_URI_FAMILIES[0] + "legacy\n", encoding="utf-8")

    findings = scan_claim_surfaces([fixture])

    assert any("legacy-uri" in finding for finding in findings)
