from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from .citations import CitationTarget
from .legacy_store import LegacyRecordStore


class MediaKind(StrEnum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    MODEL_3D = "model_3d"
    ANIMATION = "animation"


class MediaAsset(BaseModel):
    id: str
    kind: MediaKind
    url: str
    label: str | None = None
    license: str | None = None
    attribution: str | None = None
    mime_type: str | None = None


class HistoricalWarning(BaseModel):
    code: str
    text: str
    severity: str = "info"


class PlaceReference(BaseModel):
    id: str
    name: str
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    source: CitationTarget | None = None


class HistoricalObject(BaseModel):
    id: str
    manuscript_id: str
    name: str
    category: str
    alternate_names: list[str] = Field(default_factory=list)
    description: str | None = None
    region_ids: list[str] = Field(default_factory=list)
    sources: list[CitationTarget] = Field(default_factory=list)
    media: list[MediaAsset] = Field(default_factory=list)
    warnings: list[HistoricalWarning] = Field(default_factory=list)
    places: list[PlaceReference] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    id: str
    title: str
    start_year: int
    end_year: int | None = None
    circa: bool = False
    description: str | None = None
    sources: list[CitationTarget] = Field(default_factory=list)
    object_ids: list[str] = Field(default_factory=list)


class StoryCard(BaseModel):
    id: str
    title: str
    body: str
    source_ids: list[str] = Field(default_factory=list)
    media_ids: list[str] = Field(default_factory=list)


class RelatedPassage(BaseModel):
    source_region_id: str
    target_region_id: str
    relation: str
    note: str | None = None


class Exhibit(BaseModel):
    id: str
    title: str
    description: str | None = None
    object_ids: list[str] = Field(default_factory=list)
    story_cards: list[StoryCard] = Field(default_factory=list)


def historical_context_warning(category: str) -> HistoricalWarning | None:
    if category.lower() in {"medicine", "medical", "surgery", "surgical", "pharmacy"}:
        return HistoricalWarning(
            code="historical-medical-context",
            text=(
                "هذا المحتوى يصف معرفة وممارسات تاريخية، ولا يُستخدم كإرشاد طبي حديث "
                "أو كبديل عن المراجع الطبية المعاصرة."
            ),
            severity="important",
        )
    return None


class VisualKnowledgeStore:
    def __init__(self, path: Path | None = None):
        self.store = LegacyRecordStore(path)

    def put_object(self, item: HistoricalObject, *, actor: str = "legacy-adapter") -> HistoricalObject:
        warning = historical_context_warning(item.category)
        if warning and all(existing.code != warning.code for existing in item.warnings):
            item = item.model_copy(update={"warnings":[*item.warnings,warning]})
        self.store.put("visual-object",item.id,item.model_dump(mode="json"),actor=actor)
        return item

    def list_objects(self, manuscript_id: str | None = None) -> list[HistoricalObject]:
        values = [HistoricalObject.model_validate(row) for row in self.store.rows("visual-object")]
        return values if manuscript_id is None else [x for x in values if x.manuscript_id == manuscript_id]

    def put_event(self, item: TimelineEvent, *, actor: str = "legacy-adapter") -> TimelineEvent:
        self.store.put("visual-event",item.id,item.model_dump(mode="json"),actor=actor)
        return item

    def list_events(self) -> list[TimelineEvent]:
        return sorted([TimelineEvent.model_validate(row) for row in self.store.rows("visual-event")],key=lambda item:item.start_year)

    def put_exhibit(self, item: Exhibit, *, actor: str = "legacy-adapter") -> Exhibit:
        self.store.put("visual-exhibit",item.id,item.model_dump(mode="json"),actor=actor)
        return item

    def list_exhibits(self) -> list[Exhibit]:
        return [Exhibit.model_validate(row) for row in self.store.rows("visual-exhibit")]

    def add_relation(self, item: RelatedPassage, *, actor: str = "legacy-adapter") -> RelatedPassage:
        identifier = json.dumps([item.source_region_id,item.target_region_id,item.relation])
        self.store.put("visual-relation",identifier,item.model_dump(mode="json"),actor=actor)
        return item

    def relations(self) -> list[RelatedPassage]:
        return [RelatedPassage.model_validate(row) for row in self.store.rows("visual-relation")]


visual_store = VisualKnowledgeStore()
