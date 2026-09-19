"""Ontology-grounded Schema Linker for SAP Enterprise Support.

Maps unstructured terms and identifiers from natural language queries
to formal URIs in the SAP PPMS and Support Ontologies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class GroundedEntities:
    """Entities grounded in SAP ontology namespaces."""

    raw_query: str
    component_codes: list[str] = field(default_factory=list)
    alert_codes: list[str] = field(default_factory=list)
    product_versions: list[str] = field(default_factory=list)
    software_components: list[str] = field(default_factory=list)
    support_packages: list[int] = field(default_factory=list)
    note_numbers: list[str] = field(default_factory=list)
    priorities: list[str] = field(default_factory=list)
    intent: str = "GENERAL_SEARCH"
    confidence: float = 1.0


class SchemaLinker:
    """Extracts and grounds domain entities against the SAP Support and PPMS ontologies."""

    KNOWN_COMPONENTS: ClassVar[list[str]] = [
        "BC-DB-HDB",
        "BC-DB-ORA",
        "BC-DB",
        "BC-CST-MM",
        "BC-CST-DP",
        "BC-CST",
        "BC",
        "FI-GL-GL",
        "FI-GL",
        "FI",
        "MM-PUR-PO",
        "MM-PUR",
        "MM",
        "SD-SLS-SO",
        "SD-SLS",
        "SD",
    ]

    KNOWN_ALERTS: ClassVar[list[str]] = [
        "TIME_OUT",
        "TSV_TNEW_PAGE_ALLOC_FAILED",
        "DBSQL_NO_MORE_CONNECTION",
        "CX_SY_OPEN_SQL_ERROR",
        "CALL_FUNCTION_NOT_FOUND",
        "SYSTEM_TIME_OUT",
    ]

    KNOWN_PRODUCT_VERSIONS: ClassVar[list[tuple[str, str]]] = [
        ("S/4HANA 2023", "S4HANA_2023"),
        ("S/4HANA 2022", "S4HANA_2022"),
        ("S/4HANA 2021", "S4HANA_2021"),
        ("NetWeaver 7.50", "NETWEAVER_750"),
    ]

    KNOWN_SOFTWARE_COMPONENTS: ClassVar[list[str]] = [
        "SAP_BASIS",
        "S4CORE",
        "SAP_APPL",
        "SAP_UI",
    ]

    def ground(self, query_text: str) -> GroundedEntities:
        """Analyze natural language query and extract formal ontology symbols."""
        entities = GroundedEntities(raw_query=query_text)
        normalized = query_text.upper()

        # 1. Extract Application Components (longest first to avoid prefix collisions)
        sorted_components = sorted(self.KNOWN_COMPONENTS, key=len, reverse=True)
        found_spans: list[tuple[int, int]] = []

        for comp in sorted_components:
            # Match component ensuring it's not immediately preceded/followed by hyphen or alphanum
            pattern = rf"(?<![\w\-]){re.escape(comp)}(?![\w\-])"
            for m in re.finditer(pattern, normalized):
                start, end = m.span()
                # Check overlap with already matched longer component
                if not any(s <= start and end <= e for s, e in found_spans):
                    found_spans.append((start, end))
                    if comp not in entities.component_codes:
                        entities.component_codes.append(comp)

        # 2. Extract Alert / Dump Codes
        for alert in self.KNOWN_ALERTS:
            pattern = rf"\b{re.escape(alert)}\b"
            if re.search(pattern, normalized):
                std_alert = "TIME_OUT" if alert == "SYSTEM_TIME_OUT" else alert
                if std_alert not in entities.alert_codes:
                    entities.alert_codes.append(std_alert)

        # 3. Extract Product Versions
        for label, code in self.KNOWN_PRODUCT_VERSIONS:
            if (label.upper() in normalized or code in normalized) and code not in entities.product_versions:
                entities.product_versions.append(code)

        # 4. Extract Software Components
        for sc in self.KNOWN_SOFTWARE_COMPONENTS:
            if re.search(rf"\b{re.escape(sc)}\b", normalized) and sc not in entities.software_components:
                entities.software_components.append(sc)

        # 5. Extract Support Package levels (e.g., SP01, SP02, SP 01, Support Package 02)
        sp_matches = re.findall(r"\b(?:SP|SUPPORT\s*PACKAGE)\s*(\d{1,2})\b", normalized)
        for sp_str in sp_matches:
            val = int(sp_str)
            if val not in entities.support_packages:
                entities.support_packages.append(val)

        # 6. Extract SAP Note numbers (7 digits or explicit 'NOTE <digits>')
        note_matches = re.findall(r"\b(?:NOTE\s*)?(\d{7})\b", normalized)
        for n in note_matches:
            if n not in entities.note_numbers:
                entities.note_numbers.append(n)

        # 7. Extract Priority
        for prio in ["VERY HIGH", "HIGH", "MEDIUM", "LOW"]:
            if prio in normalized:
                title_prio = prio.title()
                if title_prio not in entities.priorities:
                    entities.priorities.append(title_prio)

        # 8. Infer Intent
        if "PREREQUISITE" in normalized or "PREREQ" in normalized or "DEPEND" in normalized:
            entities.intent = "PREREQUISITE_CHAIN"
        elif entities.alert_codes or "RESOLVE" in normalized or "DUMP" in normalized or "CRASH" in normalized:
            entities.intent = "RESOLVE_ALERT"
        elif entities.support_packages or entities.product_versions:
            entities.intent = "VERSION_FILTER"
        elif entities.component_codes:
            entities.intent = "COMPONENT_SEARCH"
        else:
            entities.intent = "GENERAL_SEARCH"

        return entities
