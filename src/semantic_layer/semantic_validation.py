"""Typed loading and validation helpers for the canonical semantic assets."""

from pathlib import Path
from typing import Annotated

import yaml
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from pyshacl import validate as shacl_validate
from rdflib import Graph

SEMVER_PATTERN = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
SemanticVersion = Annotated[str, StringConstraints(pattern=SEMVER_PATTERN)]


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
    version: SemanticVersion
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


class VocabularyMetadata(BaseModel):
    """Document-level governance metadata for a vocabulary file."""

    model_config = ConfigDict(extra="forbid")

    version: SemanticVersion
    namespace: str = Field(min_length=1)
    owner: str = Field(min_length=1)


class LoadedVocabulary(list[Concept]):
    """List-compatible vocabulary that retains its document metadata."""

    def __init__(self, concepts: list[Concept], metadata: VocabularyMetadata) -> None:
        super().__init__(concepts)
        self.metadata = metadata

    @property
    def version(self) -> str:
        return self.metadata.version

    @property
    def namespace(self) -> str:
        return self.metadata.namespace

    @property
    def owner(self) -> str:
        return self.metadata.owner

    @property
    def document_version(self) -> str:
        return self.metadata.version

    @property
    def document_namespace(self) -> str:
        return self.metadata.namespace

    @property
    def document_owner(self) -> str:
        return self.metadata.owner


class ValidationResult(BaseModel):
    """Result of validating an RDF graph against a SHACL graph."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    conforms: bool
    report_text: str
    data_path: Path
    shapes_path: Path


class VocabularyDocument(BaseModel):
    """Typed YAML document containing metadata and canonical concepts."""

    model_config = ConfigDict(extra="forbid")

    version: SemanticVersion
    namespace: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    concepts: list[Concept] = Field(min_length=1)


def load_vocabulary(path: Path) -> list[Concept]:
    """Load and validate a YAML business vocabulary from ``path``."""

    with path.open(encoding="utf-8") as stream:
        document = yaml.safe_load(stream)
    parsed = VocabularyDocument.model_validate(document)
    metadata = VocabularyMetadata.model_validate(parsed.model_dump(exclude={"concepts"}))
    return LoadedVocabulary(parsed.concepts, metadata)


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
