from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock

from .models import Manuscript


class ManuscriptRepository:
    """Source metadata repository; SQLite light profile and an in-memory test adapter."""

    def __init__(self, path: Path | None = None) -> None:
        self._lock = RLock()
        self._items: dict[str, Manuscript] = {}
        self.path = path
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            with self.connection() as connection:
                connection.execute("CREATE TABLE IF NOT EXISTS manuscripts(id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
                connection.execute("CREATE TABLE IF NOT EXISTS source_audit(sequence INTEGER PRIMARY KEY AUTOINCREMENT, "
                                   "manuscript_id TEXT, actor TEXT, old_payload TEXT, new_payload TEXT, timestamp TEXT)")

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=5)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def list(self) -> list[Manuscript]:
        with self._lock:
            if self.path is None:
                return list(self._items.values())
            with self.connection() as connection:
                rows = connection.execute("SELECT payload FROM manuscripts ORDER BY id").fetchall()
            return [Manuscript.model_validate_json(row[0]) for row in rows]

    def get(self, manuscript_id: str) -> Manuscript | None:
        with self._lock:
            if self.path is None:
                return self._items.get(manuscript_id)
            with self.connection() as connection:
                row = connection.execute("SELECT payload FROM manuscripts WHERE id=?", (manuscript_id,)).fetchone()
            return Manuscript.model_validate_json(row[0]) if row else None

    def put(self, manuscript: Manuscript, *, actor: str = "internal") -> Manuscript:
        with self._lock:
            previous = self.get(manuscript.id)
            images = {page.id: page.image for page in manuscript.pages}
            if previous and any(images.get(page.id) != page.image for page in previous.pages):
                raise ValueError("Original page images cannot be replaced or removed; create a new witness")
            if self.path is None:
                self._items[manuscript.id] = manuscript
            else:
                with self.connection() as connection:
                    connection.execute("BEGIN IMMEDIATE")
                    connection.execute(
                        "INSERT INTO manuscripts(id,payload) VALUES(?,?) "
                        "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
                        (manuscript.id, manuscript.model_dump_json()),
                    )
                    connection.execute("INSERT INTO source_audit(manuscript_id,actor,old_payload,new_payload,timestamp) VALUES(?,?,?,?,?)",
                                       (manuscript.id, actor, previous.model_dump_json() if previous else None,
                                        manuscript.model_dump_json(), datetime.now(UTC).isoformat()))
            return manuscript


repository = ManuscriptRepository(Path(os.getenv("MANUSCRIPT_METADATA_PATH", "./data/manuscripts.sqlite3")))
