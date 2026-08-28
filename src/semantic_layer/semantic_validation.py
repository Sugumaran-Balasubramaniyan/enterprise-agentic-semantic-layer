"""Typed loading and validation helpers for the canonical semantic assets."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field
from pyshacl import validate as shacl_validate
from rdflib import Graph


class Sensitivity(BaseModel):
    """Classification metadata for a canonical concept."""

    model_config = ConfigDict(extra="forbid")

    classification: str
    rationale: str | None = None


class Relationship(BaseModel):
    """A governed relationship from one canonical concept to another."""

    model_config = ConfigDict(extra="forbid")

    predicate: str
    target: str
    description: str | None = None


class Concept(BaseModel):
    """One versioned, governed business concept from the vocabulary."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    version: str
    definition: str
    description: str
    synonyms: list[str] = Field(default_factory=list)
    domain: str
    owner: str
    classification: str
    sensitivity: Sensitivity
    relationships: list[Relationship] = Field(default_factory=list)
    allowed_values: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Result of validating an RDF graph against a SHACL graph."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    conforms: bool
    report_text: str
    data_path: Path
    shapes_path: Path


def _concept_payloads(document: Any) -> list[dict[str, Any]]:
    if isinstance(document, dict):
        concepts = document.get("concepts")
    else:
        concepts = document
    if not isinstance(concepts, list):
        raise TypeError("Vocabulary must contain a 'concepts' list")
    return concepts


def load_vocabulary(path: Path) -> list[Concept]:
    """Load and validate a YAML business vocabulary from ``path``."""

    with path.open(encoding="utf-8") as stream:
        document = yaml.safe_load(stream)
    return [Concept.model_validate(item) for item in _concept_payloads(document)]


def validate_graph(data_path: Path, shapes_path: Path) -> ValidationResult:
    """Validate a Turtle instance graph with its Turtle SHACL shapes."""

    data_graph = Graph().parse(data_path, format="turtle")
    shapes_graph = Graph().parse(shapes_path, format="turtle")
    conforms, _, report_text = shacl_validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        abort_on_first=False,
        advanced=False,
    )
    return ValidationResult(
        conforms=bool(conforms),
        report_text=str(report_text),
        data_path=data_path,
        shapes_path=shapes_path,
    )
