"""Deterministic lexical grounding of governed terms and synonyms."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from semantic_layer.models import Resolution

if TYPE_CHECKING:
    from semantic_layer.registry.service import SemanticRegistry


def normalize(text: str) -> str:
    """Normalize human punctuation and spacing without applying fuzzy matching."""

    return " ".join(re.sub(r"[-_/]", " ", text.casefold()).split())


class DeterministicResolver:
    """Exact token and synonym resolver; it has no LLM or SQL capability."""

    def __init__(self, registry: SemanticRegistry) -> None:
        self.registry = registry

    def resolve(self, text: str) -> Resolution:
        normalized_text = normalize(text)
        matches: dict[str, str] = {}
        for concept in self.registry.concepts.values():
            terms = [concept.name, *concept.synonyms]
            for term in terms:
                normalized_term = normalize(term)
                if re.search(rf"(?<!\w){re.escape(normalized_term)}(?!\w)", normalized_text):
                    matches.setdefault(concept.id, normalized_term)
                    break
        for mapping in self.registry.mappings.values():
            for local_value, concept_id in mapping.normalization.get("products", {}).items():
                normalized_value = normalize(local_value)
                if (
                    concept_id in self.registry.concepts
                    and re.search(rf"(?<!\w){re.escape(normalized_value)}(?!\w)", normalized_text)
                ):
                    matches.setdefault(concept_id, normalized_value)
        return Resolution(text=text, concept_ids=sorted(matches), matched_terms=dict(sorted(matches.items())))
