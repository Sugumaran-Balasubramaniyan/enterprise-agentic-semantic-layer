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

from semantic_layer.research.contracts import ReasonCode


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
    failure_class: ReasonCode = ReasonCode.NONE


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

    def __init__(self) -> None:
        grammar = yaml.safe_load(self.GRAMMAR_PATH.read_text(encoding="utf-8"))
        if grammar.get("schema_version") != "1.0":
            raise ValueError("unsupported grounding grammar schema")
        self._fillers = frozenset(grammar["filler_tokens"])
        self._lookup_verbs = frozenset(grammar["lookup_verb"])
        self._question_words = frozenset(grammar["question_word"])
        self._alert_context_tokens = frozenset(grammar["alert_context_tokens"])
        self._prerequisite_markers = frozenset(grammar["prerequisite_marker"])
        self._unsupported_markers = frozenset(grammar["unsupported_intent_marker"])
        self._templates = tuple(grammar["templates"])
        self._template_intents = frozenset(template["intent"] for template in self._templates)
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

    @classmethod
    def _priority_value(cls, tokens: list[str], index: int) -> tuple[str | None, int]:
        """Return a cued priority and the number of value tokens it consumes."""

        value_index = index + 1
        if value_index >= len(tokens):
            return None, 0
        first = tokens[value_index]
        if first == "very" and value_index + 1 < len(tokens):
            value = cls.KNOWN_PRIORITIES.get(f"{first} {tokens[value_index + 1]}")
            return value, 2
        return cls.KNOWN_PRIORITIES.get(first), 1

    @staticmethod
    def _add(values: list, value) -> None:
        if value not in values:
            values.append(value)

    def _mark_cued_unknowns(
        self, tokens: list[str], consumed: set[int], failure: ReasonCode | None
    ) -> ReasonCode | None:
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
                        failure = failure or ReasonCode.UNKNOWN_ENTITY
                else:
                    consumed.add(index)
                    failure = failure or ReasonCode.UNKNOWN_ENTITY
                continue
            if token not in {"alert", "component", "note", "priority"}:
                continue
            value_index = index + 1
            if token == "priority":
                priority, width = self._priority_value(tokens, index)
                consumed.update(range(index, index + width + 1))
                if priority is None:
                    failure = failure or ReasonCode.UNKNOWN_ENTITY
                continue
            if value_index >= len(tokens):
                consumed.add(index)
                failure = failure or ReasonCode.UNKNOWN_ENTITY
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
                failure = failure or ReasonCode.UNKNOWN_ENTITY
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
            if token == "priority":
                priority, width = self._priority_value(tokens, index)
                if priority is not None:
                    self._add(entities.priorities, priority)
                    consumed.update(range(index, index + width + 1))
        return consumed

    def _recognized_entities(self, tokens: list[str]) -> list[tuple[str, int, bool]]:
        """Return recognized slots with their token positions and cue state."""

        records: list[tuple[str, int, bool]] = []
        for index, token in enumerate(tokens):
            previous = tokens[index - 1] if index else ""
            if token in self._alert_lookup:
                following = tokens[index + 1] if index + 1 < len(tokens) else ""
                records.append(
                    (
                        "alert_code",
                        index,
                        previous in self._alert_context_tokens
                        or following in self._alert_context_tokens,
                    )
                )
            if token in self._component_lookup:
                records.append(("component_code", index, previous == "component"))
            if token in self._software_lookup:
                records.append(("software_component", index, False))
            if token in self._product_lookup:
                records.append(("product_version", index, False))
            if (
                token == "s/4hana"
                and index + 1 < len(tokens)
                and f"{token} {tokens[index + 1]}" in self._product_labels
            ):
                records.append(("product_version", index, True))
            if (
                token == "netweaver"
                and index + 1 < len(tokens)
                and f"{token} {tokens[index + 1]}" in self._product_labels
            ):
                records.append(("product_version", index, True))
            if len(token) == 7 and token.isdecimal():
                records.append(("note_number", index, previous == "note"))
            if self._numeric_support(token) is not None:
                records.append(("support_package", index, True))
            if token == "priority":
                priority, _width = self._priority_value(tokens, index)
                if priority is not None:
                    records.append(("priority", index, True))
        return records

    def _match_declared_template(
        self, tokens: list[str], entities: GroundedEntities
    ) -> tuple[str | None, ReasonCode | None]:
        """Select one declared template and reject extra or uncued slots."""

        records = self._recognized_entities(tokens)
        families = {family for family, _, _ in records}
        lookup = any(token in self._lookup_verbs for token in tokens)
        question = any(token in self._question_words for token in tokens)
        prerequisite = any(token in self._prerequisite_markers for token in tokens)
        has_alert = len(entities.alert_codes) == 1
        has_component = len(entities.component_codes) == 1
        has_version = len(entities.product_versions) == 1
        has_package = len(entities.support_packages) == 1
        has_note = len(entities.note_numbers) == 1

        if prerequisite:
            candidate = "PREREQUISITE_CLOSURE"
        elif has_version or has_package:
            candidate = "VERSION_FILTERED_SEARCH"
        elif has_alert:
            candidate = "ALERT_RESOLUTION"
        elif has_component:
            candidate = "COMPONENT_SEARCH"
        elif has_note and lookup:
            candidate = "NOTE_LOOKUP"
        elif has_note and len(tokens) == 1:
            candidate = "GENERAL_SEARCH"
        else:
            return None, ReasonCode.MISSING_REQUIRED_ENTITY

        if candidate not in self._template_intents:
            return None, ReasonCode.UNSUPPORTED_INTENT

        if candidate == "VERSION_FILTERED_SEARCH" and not (has_alert or has_component):
            return None, ReasonCode.UNKNOWN_TOKEN

        allowed = {
            "PREREQUISITE_CLOSURE": {"note_number"},
            "NOTE_LOOKUP": {"note_number"},
            "GENERAL_SEARCH": {"note_number"},
            "ALERT_RESOLUTION": {"alert_code", "component_code", "priority"},
            "COMPONENT_SEARCH": {"component_code", "priority"},
            "VERSION_FILTERED_SEARCH": {
                "alert_code", "component_code", "product_version", "support_package", "priority"
            },
        }[candidate]
        if families - allowed:
            return None, ReasonCode.UNSUPPORTED_INTENT

        ordered: list[str] = []
        for family, _, _ in records:
            if family not in ordered:
                ordered.append(family)
        if "priority" in ordered and ordered[-1] != "priority":
            return None, ReasonCode.UNSUPPORTED_INTENT
        if candidate == "ALERT_RESOLUTION":
            valid_orders = {
                ("alert_code",),
                ("alert_code", "component_code"),
                ("component_code", "alert_code"),
            }
        elif candidate == "COMPONENT_SEARCH":
            valid_orders = {("component_code",)}
        elif candidate == "VERSION_FILTERED_SEARCH":
            valid_orders = {
                ("alert_code", "product_version"),
                ("alert_code", "support_package"),
                ("component_code", "product_version"),
                ("component_code", "support_package"),
                ("product_version", "alert_code"),
                ("support_package", "alert_code"),
                ("product_version", "component_code"),
                ("support_package", "component_code"),
                ("alert_code", "component_code", "product_version"),
                ("alert_code", "component_code", "support_package"),
                ("alert_code", "product_version", "component_code"),
                ("alert_code", "support_package", "component_code"),
                ("product_version", "alert_code", "component_code"),
                ("support_package", "alert_code", "component_code"),
                ("component_code", "alert_code", "product_version"),
                ("component_code", "alert_code", "support_package"),
                ("alert_code", "product_version", "support_package"),
                ("alert_code", "product_version", "component_code", "support_package"),
            }
        else:
            valid_orders = {("note_number",)}
        if tuple(item for item in ordered if item not in {"priority"}) not in valid_orders:
            return None, ReasonCode.UNSUPPORTED_INTENT

        for family, _, cued in records:
            if family in {"alert_code", "component_code", "product_version", "software_component"} and not cued:
                return None, ReasonCode.UNKNOWN_TOKEN
            if family == "note_number" and not cued:
                bare_lookup = candidate == "NOTE_LOOKUP" and lookup and families == {"note_number"}
                bare_prerequisite = candidate == "PREREQUISITE_CLOSURE" and families == {"note_number"}
                if not (bare_lookup or bare_prerequisite or candidate == "GENERAL_SEARCH"):
                    return None, ReasonCode.UNSUPPORTED_INTENT

        if candidate in {"PREREQUISITE_CLOSURE", "NOTE_LOOKUP", "GENERAL_SEARCH"}:
            if candidate == "PREREQUISITE_CLOSURE" and (not question or not has_note):
                return None, ReasonCode.UNSUPPORTED_INTENT
            if candidate == "NOTE_LOOKUP" and (not lookup or not has_note):
                return None, ReasonCode.UNSUPPORTED_INTENT
            if candidate == "GENERAL_SEARCH" and (not has_note or len(tokens) != 1):
                return None, ReasonCode.UNSUPPORTED_INTENT
        elif not question:
            return None, ReasonCode.UNSUPPORTED_INTENT

        if candidate == "PREREQUISITE_CLOSURE" and (has_alert or has_component or has_version or has_package):
            return None, ReasonCode.AMBIGUOUS_INTENT
        if candidate == "VERSION_FILTERED_SEARCH" and not (
            (has_alert or has_component) and (has_version or has_package)
        ):
            return None, (
                ReasonCode.UNKNOWN_TOKEN
                if not (has_alert or has_component)
                else ReasonCode.MISSING_REQUIRED_ENTITY
            )
        return candidate, None

    def ground(self, query_text: str) -> GroundedEntities:
        """Return deterministic grounding; never invoke planning or compilation."""

        tokens = self._tokens(query_text)
        entities = GroundedEntities(raw_query=query_text, normalized_request=" ".join(tokens))
        consumed = self._collect_entities(tokens, entities)
        failure: ReasonCode | None = None

        # Unsupported intent takes precedence over token diagnostics.
        if any(token in self._unsupported_markers for token in tokens):
            failure = ReasonCode.UNSUPPORTED_INTENT
        else:
            failure = self._mark_cued_unknowns(tokens, consumed, failure)

        # Numeric SP tokens are valid syntax; malformed/named SP values are
        # unknown entities even when they are not preceded by a cue.
        for index, token in enumerate(tokens):
            if token.startswith("sp") and self._numeric_support(token) is None:
                consumed.add(index)
                failure = failure or ReasonCode.UNKNOWN_ENTITY

        for index, token in enumerate(tokens):
            if index in consumed or token in self._fillers:
                continue
            if token in self._lookup_verbs or token in self._question_words:
                consumed.add(index)
                continue
            failure = failure or ReasonCode.UNKNOWN_TOKEN

        families = (
            entities.component_codes, entities.alert_codes, entities.product_versions,
            entities.software_components, entities.support_packages, entities.note_numbers,
            entities.priorities,
        )
        if failure is None and any(len(values) > 1 for values in families):
            failure = ReasonCode.AMBIGUOUS_INPUT
        if failure is None:
            entities.intent, template_failure = self._match_declared_template(tokens, entities)
            failure = template_failure

        if failure is not None:
            entities.failure_class = failure
            entities.intent = "UNSUPPORTED"
        return entities

    def ground_or_abstain(self, query_text: str) -> GroundedEntities:
        """Ground without raising; rejected grammar remains planner-inert."""

        return self.ground(query_text)
