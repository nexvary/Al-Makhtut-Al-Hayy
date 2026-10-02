from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class TextLayerKind(StrEnum):
    HTR_RAW = "htr_raw"
    DIPLOMATIC = "diplomatic_transcription"
    VERIFIED = "verified_transcription"
    NORMALIZED = "normalized_arabic"
    SIMPLIFIED = "simplified_arabic"
    TRANSLATION = "translation"
    AI_EXPLANATION = "ai_explanation"


class Point(BaseModel):
    x: float
    y: float


class TextLayer(BaseModel):
    kind: TextLayerKind
    text: str
    status: Literal["machine", "draft", "verified"]
    confidence: float | None = Field(default=None, ge=0, le=1)
    model: str | None = None
    revision: str | None = None


class Region(BaseModel):
    id: str
    polygon: list[Point]
    layers: list[TextLayer] = []


class Page(BaseModel):
    id: str
    sequence: int = Field(ge=1)
    folio_label: str | None = None
    image: str
    regions: list[Region] = []


class Manuscript(BaseModel):
    id: str
    title: str
    author: str | None = None
    date_label: str | None = None
    source_institution: str | None = None
    source_url: str | None = None
    license: str | None = None
    pages: list[Page] = []
