"""Independent, source-anchored representations; originals remain on Manuscript.Page."""
from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import AwareDatetime, BaseModel, Field, model_validator

from .citations import CitationTarget
from .models import Point


class LayerKind(StrEnum):
    ORIGINAL = "original_image"
    MACHINE = "machine_reading"
    DRAFT = "draft_transcription"
    VERIFIED = "verified_transcription"
    CRITICAL = "critical_text"
    MODERN = "modernized_text"
    EXPLANATION = "simplified_explanation"
    TRANSLATION = "translation"
    AUDIO = "audio"
    ENTITIES = "named_entities"
    OBJECTS = "historical_objects"
    ILLUSTRATIONS = "illustrations"
    REFERENCES = "references"
    ANNOTATIONS = "annotations"
    PROVENANCE = "provenance"


class ReviewState(StrEnum):
    MACHINE = "machine"
    DRAFT = "draft"
    VERIFIED = "verified"


class SourceAnchor(CitationTarget):
    witness_id: str | None = None
    coordinates: list[Point] = Field(default_factory=list, max_length=1000)
    source_uri: str | None = None


class LayerProvenance(BaseModel):
    source: SourceAnchor
    extraction_method: str = Field(min_length=1, max_length=100)
    source_text: str | None = Field(default=None, max_length=100_000)
    model: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    reviewer: str | None = None
    revision: str | None = None
    timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    evidence: list[CitationTarget] = Field(default_factory=list, max_length=100)


class LivingLayer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    kind: LayerKind
    state: ReviewState = ReviewState.DRAFT
    language: str | None = Field(default=None, max_length=35)
    text: str | None = Field(default=None, max_length=100_000)
    asset_uri: str | None = Field(default=None, max_length=2000)
    data: dict[str, Any] = Field(default_factory=dict)
    provenance: LayerProvenance
    parent_revision_id: str | None = None

    @model_validator(mode="after")
    def review_integrity(self) -> LivingLayer:
        if self.kind == LayerKind.MACHINE and self.state != ReviewState.MACHINE:
            raise ValueError("Machine reading stays machine; human review creates a separate layer")
        if self.state == ReviewState.VERIFIED and not self.provenance.reviewer:
            raise ValueError("Verified layers require an identified human reviewer")
        if self.state == ReviewState.MACHINE and not self.provenance.model:
            raise ValueError("Machine output must identify its model")
        if self.kind == LayerKind.VERIFIED and self.state != ReviewState.VERIFIED:
            raise ValueError("Verified transcription cannot contain an unverified draft")
        if not self.text and not self.asset_uri and not self.data:
            raise ValueError("A layer requires text, an asset or structured data")
        return self
