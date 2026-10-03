from __future__ import annotations

from threading import RLock

from .models import Manuscript


class ManuscriptRepository:
    """Small deterministic repository used until PostgreSQL migrations land."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._items: dict[str, Manuscript] = {}

    def list(self) -> list[Manuscript]:
        with self._lock:
            return list(self._items.values())

    def get(self, manuscript_id: str) -> Manuscript | None:
        with self._lock:
            return self._items.get(manuscript_id)

    def put(self, manuscript: Manuscript) -> Manuscript:
        with self._lock:
            self._items[manuscript.id] = manuscript
            return manuscript


repository = ManuscriptRepository()
