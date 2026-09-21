"""Typed loading and validation helpers for the canonical semantic assets."""

import hashlib
from pathlib import Path
from typing import Annotated

import yaml
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from pyshacl import validate as shacl_validate
from rdflib import RDF, Graph, Namespace

_CIFMETA = Namespace("https://example.org/cifre-kg/meta#")
_SH = Namespace("http://www.w3.org/ns/shacl#")

_SEMVER_NUMERIC = r"(?:0|[1-9]\d*)"
_SEMVER_NON_NUMERIC = r"(?:[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
_SEMVER_IDENTIFIER = rf"(?:{_SEMVER_NUMERIC}|{_SEMVER_NON_NUMERIC})"
SEMVER_PATTERN = (
    rf"^{_SEMVER_NUMERIC}\.{_SEMVER_NUMERIC}\.{_SEMVER_NUMERIC}"
    rf"(?:-{_SEMVER_IDENTIFIER}(?:\.{_SEMVER_IDENTIFIER})*)?"
    rf"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
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
    scope: str = "unspecified"
    inference: str = "rdfs"
    violation_count: int = 0
    data_sha256: str = ""
    shapes_sha256: str = ""
    provenance_dataset_id: str | None = None

    @property
    def graph_scope(self) -> str:
        """Return the explicit graph selection used for this report."""

        return self.scope


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


def _default_scope(shapes_path: Path) -> str:
    name = shapes_path.name.casefold()
    if "support" in name:
        return "support"
    if "erp" in name:
        return "erp"
    return "unspecified"


def _dataset_id(graph: Graph) -> str | None:
    values = sorted({str(value) for value in graph.objects(None, _CIFMETA.datasetId)})
    return "+".join(values) if values else None


def validate_graph(
    data_path: Path,
    shapes_path: Path,
    *,
    scope: str | None = None,
) -> ValidationResult:
    """Validate a Turtle instance graph with its Turtle SHACL shapes.

    ``scope`` is report metadata, not a second graph loader.  Omitting it
    selects a deterministic scope from the shape filename so legacy callers
    receive an explicit report without changing their validation behavior.
    """

    data_graph = Graph().parse(data_path, format="turtle")
    shapes_graph = Graph().parse(shapes_path, format="turtle")
    conforms, report_graph, report_text = shacl_validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        abort_on_first=False,
        advanced=False,
        js=False,
        meta_shacl=False,
    )
    selected_scope = scope or _default_scope(shapes_path)
    if selected_scope not in {"support", "erp", "combined", "unspecified"}:
        raise ValueError("scope must be one of: support, erp, combined, unspecified")
    return ValidationResult(
        conforms=bool(conforms),
        report_text=str(report_text),
        data_path=data_path,
        shapes_path=shapes_path,
        scope=selected_scope,
        violation_count=len(set(report_graph.subjects(RDF.type, _SH.ValidationResult))),
        data_sha256=hashlib.sha256(data_path.read_bytes()).hexdigest(),
        shapes_sha256=hashlib.sha256(shapes_path.read_bytes()).hexdigest(),
        provenance_dataset_id=_dataset_id(data_graph),
    )
