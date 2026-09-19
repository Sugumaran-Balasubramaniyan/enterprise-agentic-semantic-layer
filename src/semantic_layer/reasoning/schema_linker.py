"""Finite, ontology-grounded grammar for SAP support requests.

Grounding is deliberately closed: only tokens in the checked-in grammar or a
cued finite entity vocabulary can reach planning. The linker does not infer
synonyms, call a model, or fabricate ontology identifiers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

import yaml


@dataclass
class GroundedEntities:
    """The fail-closed, planner-independent result of grammar grounding."""

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
    normalized_request: str = ""
    failure_class: str = "NONE"


class SchemaLinker:
    """Ground requests against a finite grammar before planning."""

    GRAMMAR_PATH: ClassVar[Path] = (
        Path(__file__).resolve().parents[3] / "tests/research/grounding_grammar.yaml"
    )

    KNOWN_COMPONENTS: ClassVar[list[str]] = [
        "BC-DB-HDB", "BC-DB-ORA", "BC-DB", "BC-CST-MM", "BC-CST-DP", "BC-CST", "BC",
        "FI-GL-GL", "FI-GL", "FI", "MM-PUR-PO", "MM-PUR", "MM", "SD-SLS-SO", "SD-SLS", "SD",
    ]
    KNOWN_ALERTS: ClassVar[list[str]] = [
        "TIME_OUT", "TSV_TNEW_PAGE_ALLOC_FAILED", "DBSQL_NO_MORE_CONNECTION",
        "CX_SY_OPEN_SQL_ERROR", "CALL_FUNCTION_NOT_FOUND", "SYSTEM_TIME_OUT",
    ]
    KNOWN_PRODUCT_VERSIONS: ClassVar[list[tuple[str, str]]] = [
        ("S/4HANA 2023", "S4HANA_2023"), ("S/4HANA 2022", "S4HANA_2022"),
        ("S/4HANA 2021", "S4HANA_2021"), ("NetWeaver 7.50", "NETWEAVER_750"),
    ]
    KNOWN_SOFTWARE_COMPONENTS: ClassVar[list[str]] = ["SAP_BASIS", "S4CORE", "SAP_APPL", "SAP_UI"]
    KNOWN_PRIORITIES: ClassVar[dict[str, str]] = {
        "very high": "Very High", "high": "High", "medium": "Medium", "low": "Low",
    }

    @staticmethod
    def _reason(name: str) -> str:
        """Use Task 2's closed ReasonCode vocabulary when importable."""

        try:
            from semantic_layer.research.contracts import ReasonCode

            return ReasonCode[name].value
        except (ImportError, KeyError):
            # Direct linker imports can occur while optional research exports
            # are still initializing.
            return name

    def __init__(self) -> None:
        grammar = yaml.safe_load(self.GRAMMAR_PATH.read_text(encoding="utf-8"))
        if grammar.get("schema_version") != "1.0":
            raise ValueError("unsupported grounding grammar schema")
        self._fillers = frozenset(grammar["filler_tokens"])
        self._lookup_verbs = frozenset(grammar["lookup_verb"])
        self._question_words = frozenset(grammar["question_word"])
        self._prerequisite_markers = frozenset(grammar["prerequisite_marker"])
        self._unsupported_markers = frozenset(grammar["unsupported_intent_marker"])
        self._component_lookup = {value.casefold(): value for value in self.KNOWN_COMPONENTS}
        self._alert_lookup = {value.casefold(): value for value in self.KNOWN_ALERTS}
        self._product_lookup = {code.casefold(): code for _, code in self.KNOWN_PRODUCT_VERSIONS}
        self._software_lookup = {value.casefold(): value for value in self.KNOWN_SOFTWARE_COMPONENTS}
        self._product_labels = {label.casefold(): code for label, code in self.KNOWN_PRODUCT_VERSIONS}

    @staticmethod
    def _tokens(query_text: str) -> list[str]:
        """Case-fold Unicode whitespace and ignore punctuation at boundaries."""

        folded = query_text.casefold()
        chars: list[str] = []
        boundary = frozenset(",!?;:()[]{}\"'")
        for index, char in enumerate(folded):
            if char.isspace() or char in boundary:
                chars.append(" ")
            elif char == ".":
                next_char = folded[index + 1] if index + 1 < len(folded) else ""
                chars.append("." if next_char and next_char.isdigit() else " ")
            else:
                chars.append(char)
        return "".join(chars).split()

    @staticmethod
    def _numeric_support(token: str) -> int | None:
        if not token.startswith("sp"):
            return None
        digits = token[2:]
        if 1 <= len(digits) <= 2 and digits.isdecimal():
            return int(digits)
        return None

    @staticmethod
    def _add(values: list, value) -> None:
        if value not in values:
            values.append(value)

    def _mark_cued_unknowns(
        self, tokens: list[str], consumed: set[int], failure: str | None
    ) -> str | None:
        """Classify unknown values immediately after an explicit entity cue."""

        for index, token in enumerate(tokens):
            if token == "s/4hana":
                value_index = index + 1
                if value_index < len(tokens):
                    label = f"{token} {tokens[value_index]}"
                    if label in self._product_labels:
                        consumed.update({index, value_index})
                    else:
                        consumed.update({index, value_index})
                        failure = failure or self._reason("UNKNOWN_ENTITY")
                else:
                    consumed.add(index)
                    failure = failure or self._reason("UNKNOWN_ENTITY")
                continue
            if token not in {"alert", "component", "note", "priority"}:
                continue
            value_index = index + 1
            if token == "priority" and value_index < len(tokens):
                value = tokens[value_index]
                if value in self.KNOWN_PRIORITIES:
                    consumed.update({index, value_index})
                else:
                    consumed.add(index)
                    failure = failure or self._reason("UNKNOWN_ENTITY")
                continue
            if value_index >= len(tokens):
                consumed.add(index)
                failure = failure or self._reason("UNKNOWN_ENTITY")
                continue
            value = tokens[value_index]
            # "SAP note resolves ..." uses note as an ordinary filler noun;
            # only a note followed by a number is a cue-selected slot.
            if token == "note" and value in self._fillers:
                continue
            known = (
                (token == "alert" and value in self._alert_lookup)
                or (token == "component" and value in self._component_lookup)
                or (token == "note" and len(value) == 7 and value.isdecimal())
            )
            consumed.update({index, value_index})
            if not known:
                failure = failure or self._reason("UNKNOWN_ENTITY")
        return failure

    def _collect_entities(self, tokens: list[str], entities: GroundedEntities) -> set[int]:
        consumed: set[int] = set()
        for index, token in enumerate(tokens):
            if token in self._alert_lookup:
                self._add(entities.alert_codes, self._alert_lookup[token])
                consumed.add(index)
            if token in self._component_lookup:
                self._add(entities.component_codes, self._component_lookup[token])
                consumed.add(index)
            if token in self._software_lookup:
                self._add(entities.software_components, self._software_lookup[token])
                consumed.add(index)
            if token in self._product_lookup:
                self._add(entities.product_versions, self._product_lookup[token])
                consumed.add(index)
            if len(token) == 7 and token.isdecimal():
                self._add(entities.note_numbers, token)
                consumed.add(index)
            support_package = self._numeric_support(token)
            if support_package is not None:
                self._add(entities.support_packages, support_package)
                consumed.add(index)
            if token == "s/4hana" and index + 1 < len(tokens):
                label = f"{token} {tokens[index + 1]}"
                if label in self._product_labels:
                    self._add(entities.product_versions, self._product_labels[label])
                    consumed.update({index, index + 1})
            if token == "netweaver" and index + 1 < len(tokens):
                label = f"{token} {tokens[index + 1]}"
                if label in self._product_labels:
                    self._add(entities.product_versions, self._product_labels[label])
                    consumed.update({index, index + 1})
            if token == "priority" and index + 1 < len(tokens):
                priority = self.KNOWN_PRIORITIES.get(tokens[index + 1])
                if priority is not None:
                    self._add(entities.priorities, priority)
                    consumed.update({index, index + 1})
        return consumed

    def ground(self, query_text: str) -> GroundedEntities:
        """Return deterministic grounding; never invoke planning or compilation."""

        tokens = self._tokens(query_text)
        entities = GroundedEntities(raw_query=query_text, normalized_request=" ".join(tokens))
        consumed = self._collect_entities(tokens, entities)
        failure: str | None = None

        # Unsupported intent takes precedence over token diagnostics.
        if any(token in self._unsupported_markers for token in tokens):
            failure = self._reason("UNSUPPORTED_INTENT")
        else:
            failure = self._mark_cued_unknowns(tokens, consumed, failure)

        # Numeric SP tokens are valid syntax; malformed/named SP values are
        # unknown entities even when they are not preceded by a cue.
        for index, token in enumerate(tokens):
            if token.startswith("sp") and self._numeric_support(token) is None:
                consumed.add(index)
                failure = failure or self._reason("UNKNOWN_ENTITY")

        for index, token in enumerate(tokens):
            if index in consumed or token in self._fillers:
                continue
            if token in self._lookup_verbs or token in self._question_words:
                consumed.add(index)
                continue
            failure = failure or self._reason("UNKNOWN_TOKEN")

        families = (
            entities.component_codes, entities.alert_codes, entities.product_versions,
            entities.software_components, entities.support_packages, entities.note_numbers,
            entities.priorities,
        )
        if failure is None and any(len(values) > 1 for values in families):
            failure = self._reason("AMBIGUOUS_INPUT")

        prerequisite = any(token in self._prerequisite_markers for token in tokens)
        if failure is None and prerequisite:
            if len(entities.note_numbers) != 1:
                failure = self._reason("MISSING_REQUIRED_ENTITY")
            elif entities.alert_codes or entities.component_codes or entities.product_versions or entities.support_packages:
                failure = self._reason("AMBIGUOUS_INTENT")
            else:
                entities.intent = "PREREQUISITE_CLOSURE"
        elif failure is None:
            has_alert = len(entities.alert_codes) == 1
            has_component = len(entities.component_codes) == 1
            has_version = len(entities.product_versions) == 1
            has_package = len(entities.support_packages) == 1
            has_priority = len(entities.priorities) == 1
            if has_version and has_package:
                failure = self._reason("AMBIGUOUS_INPUT")
            elif (has_version or has_package) and (has_alert or has_component):
                entities.intent = "VERSION_FILTERED_SEARCH"
            elif has_alert and not has_version and not has_package:
                entities.intent = "ALERT_RESOLUTION"
            elif has_component and not has_alert and not has_version and not has_package:
                entities.intent = "COMPONENT_SEARCH"
            elif len(entities.note_numbers) == 1 and any(
                token in self._lookup_verbs for token in tokens
            ):
                entities.intent = "NOTE_LOOKUP"
            elif len(entities.note_numbers) == 1 and not (
                has_alert or has_component or has_version or has_package or has_priority
            ):
                entities.intent = "GENERAL_SEARCH"
            else:
                failure = self._reason("MISSING_REQUIRED_ENTITY")

        if failure is not None:
            entities.failure_class = failure
            entities.intent = "UNSUPPORTED"
        return entities

    def ground_or_abstain(self, query_text: str) -> GroundedEntities:
        """Ground without raising; rejected grammar remains planner-inert."""

        return self.ground(query_text)
