from __future__ import annotations

from threading import RLock

from pydantic import BaseModel, Field


class GlossaryTerm(BaseModel):
    id: str
    term: str
    definition: str
    manuscript_id: str | None = None
    page_id: str | None = None
    region_ids: list[str] = Field(default_factory=list)
    historical_note: str | None = None


class GlossaryStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._items: dict[str, GlossaryTerm] = {}

    def put(self, item: GlossaryTerm) -> GlossaryTerm:
        with self._lock:
            self._items[item.id] = item
        return item

    def list(self, manuscript_id: str | None = None) -> list[GlossaryTerm]:
        with self._lock:
            values = list(self._items.values())
        if manuscript_id is None:
            return values
        return [item for item in values if item.manuscript_id in {None, manuscript_id}]


glossary_store = GlossaryStore()
