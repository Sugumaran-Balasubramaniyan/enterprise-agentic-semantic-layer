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


def _term_variants(term: str) -> tuple[str, ...]:
    """Return an exact singular/plural vocabulary variant without fuzzy matching."""

    normalized = normalize(term)
    words = normalized.split()
    if not words:
        return ()
    last = words[-1]
    if last.endswith("y"):
        plural = last[:-1] + "ies"
    elif last.endswith("s"):
        plural = last
    else:
        plural = last + "s"
    pluralized = " ".join([*words[:-1], plural])
    return (normalized,) if pluralized == normalized else (normalized, pluralized)


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
                for normalized_term in _term_variants(term):
                    if re.search(rf"(?<!\w){re.escape(normalized_term)}(?!\w)", normalized_text):
                        matches.setdefault(concept.id, normalized_term)
                        break
                if concept.id in matches:
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
