"""Experimental provider contract. Scores indicate similarity, never attribution certainty."""
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, Field

from .living import LayerProvenance, SourceAnchor


class VisualQueryKind(StrEnum):
    FRAGMENT = "fragment"
    ILLUSTRATION = "illustration"
    HANDWRITING = "handwriting"
    LAYOUT = "layout"


class VisualQuery(BaseModel):
    source: SourceAnchor
    kind: VisualQueryKind
    limit: int = Field(default=10, ge=1, le=30)


class VisualMatch(BaseModel):
    provenance: LayerProvenance
    similarity: float = Field(ge=0, le=1)
    model: str = Field(min_length=1, max_length=200)
    relation: str = "candidate_similarity"


class VisualSimilarityProvider(Protocol):
    def search(self, query: VisualQuery) -> list[VisualMatch]: ...


class ProviderUnavailable(RuntimeError):
    pass


class DisabledVisualProvider:
    def search(self, query: VisualQuery) -> list[VisualMatch]:
        raise ProviderUnavailable("No visual similarity model/index is configured")
