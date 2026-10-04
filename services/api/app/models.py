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


class RegionType(StrEnum):
    TEXT_LINE = "text_line"
    MARGINALIA = "marginalia"
    ILLUSTRATION = "illustration"
    TABLE = "table"
    DECORATION = "decoration"
    OTHER = "other"


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
    region_type: RegionType = RegionType.TEXT_LINE
    reading_order: int | None = None
    polygon: list[Point] = Field(default_factory=list)
    layers: list[TextLayer] = Field(default_factory=list)


class Page(BaseModel):
    id: str
    sequence: int = Field(ge=1)
    folio_label: str | None = None
    image: str
    canvas_uri: str | None = None
    image_width: int | None = Field(default=None, gt=0)
    image_height: int | None = Field(default=None, gt=0)
    regions: list[Region] = Field(default_factory=list)


class Manuscript(BaseModel):
    id: str
    title: str
    author: str | None = None
    date_label: str | None = None
    source_institution: str | None = None
    source_url: str | None = None
    license: str | None = None
    pages: list[Page] = Field(default_factory=list)
    work_id: str | None = None
    witness_id: str | None = None
