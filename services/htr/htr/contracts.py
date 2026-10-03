from __future__ import annotations

from pydantic import BaseModel, Field


class Point(BaseModel):
    x: float
    y: float


class SourceImage(BaseModel):
    manuscript_id: str
    page_id: str
    image_uri: str
    iiif_canvas_uri: str | None = None


class RecognizedLine(BaseModel):
    id: str
    polygon: list[Point]
    text: str
    confidence: float | None = Field(default=None, ge=0, le=1)


class HtrRequest(BaseModel):
    source: SourceImage
    model_id: str | None = None
    segment: bool = True


class HtrResult(BaseModel):
    engine: str
    engine_version: str | None = None
    model_id: str | None = None
    lines: list[RecognizedLine]
    raw_artifact_uri: str | None = None
