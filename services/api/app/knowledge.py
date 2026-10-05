from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from .legacy_store import LegacyRecordStore


class GlossaryTerm(BaseModel):
    id: str
    term: str
    definition: str
    manuscript_id: str | None = None
    page_id: str | None = None
    region_ids: list[str] = Field(default_factory=list)
    historical_note: str | None = None


class GlossaryStore:
    def __init__(self, path: Path | None = None):
        self.store = LegacyRecordStore(path)

    def put(self, item: GlossaryTerm, *, actor: str = "legacy-adapter") -> GlossaryTerm:
        self.store.put("glossary",item.id,item.model_dump(mode="json"),actor=actor)
        return item

    def list(self, manuscript_id: str | None = None) -> list[GlossaryTerm]:
        values = [GlossaryTerm.model_validate(row) for row in self.store.rows("glossary")]
        return values if manuscript_id is None else [item for item in values if item.manuscript_id in {None,manuscript_id}]


glossary_store = GlossaryStore()
