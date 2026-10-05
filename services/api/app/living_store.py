"""Append-only SQLite profile; the domain contract is independent of this adapter."""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from .living import LivingLayer


class RevisionConflict(ValueError):
    pass


class LayerRepository(Protocol):
    def append(self, item: LivingLayer, *, actor: str) -> LivingLayer: ...
    def history(self, manuscript_id: str, page_id: str) -> list[LivingLayer]: ...


class SqliteLayerRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS living_schema(version INTEGER PRIMARY KEY);
                INSERT OR IGNORE INTO living_schema VALUES(1);
                CREATE TABLE IF NOT EXISTS living_revisions(
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    id TEXT UNIQUE NOT NULL,
                    manuscript_id TEXT NOT NULL,
                    page_id TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS living_page
                    ON living_revisions(manuscript_id, page_id);
                CREATE TABLE IF NOT EXISTS living_audit(
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor TEXT NOT NULL,
                    revision_id TEXT NOT NULL,
                    previous_revision_id TEXT,
                    timestamp TEXT NOT NULL
                );
            """)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA cache_size=-2048")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def append(self, item: LivingLayer, *, actor: str) -> LivingLayer:
        source = item.provenance.source
        scope = json.dumps([source.witness_id, source.region_id, item.kind, item.language])
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT id FROM living_revisions WHERE manuscript_id=? AND page_id=? "
                "AND scope=? ORDER BY sequence DESC LIMIT 1",
                (source.manuscript_id, source.page_id, scope),
            ).fetchone()
            current = row[0] if row else None
            if item.parent_revision_id != current:
                raise RevisionConflict("Parent revision must match the current layer head")
            try:
                connection.execute(
                    "INSERT INTO living_revisions(id,manuscript_id,page_id,scope,payload) "
                    "VALUES(?,?,?,?,?)",
                    (item.id, source.manuscript_id, source.page_id, scope, item.model_dump_json()),
                )
            except sqlite3.IntegrityError as exc:
                raise RevisionConflict("Revision IDs are immutable and cannot be reused") from exc
            connection.execute(
                "INSERT INTO living_audit(actor,revision_id,previous_revision_id,timestamp) "
                "VALUES(?,?,?,?)",
                (actor, item.id, current, datetime.now(UTC).isoformat()),
            )
        return item

    def history(self, manuscript_id: str, page_id: str) -> list[LivingLayer]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM living_revisions WHERE manuscript_id=? AND page_id=? "
                "ORDER BY sequence", (manuscript_id, page_id),
            ).fetchall()
        return [LivingLayer.model_validate_json(row[0]) for row in rows]

    def audit(self) -> list[dict]:
        with self.connect() as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute("SELECT * FROM living_audit")]

    def verified_candidates(self, manuscript_ids: list[str] | None = None, *, limit: int = 2000) -> list[LivingLayer]:
        """Current reviewed representations only; later adapters can provide indexed retrieval."""
        sql = ("SELECT payload FROM living_revisions WHERE sequence IN "
               "(SELECT MAX(sequence) FROM living_revisions GROUP BY manuscript_id,page_id,scope) "
               "AND json_extract(payload,'$.state')='verified'")
        values: list = []
        if manuscript_ids is not None:
            if not manuscript_ids:
                return []
            sql += " AND manuscript_id IN (" + ",".join("?" for _ in manuscript_ids) + ")"
            values.extend(manuscript_ids)
        sql += " ORDER BY sequence DESC LIMIT ?"
        values.append(limit)
        with self.connect() as connection:
            rows = connection.execute(sql, values).fetchall()
        return [LivingLayer.model_validate_json(row[0]) for row in rows]
