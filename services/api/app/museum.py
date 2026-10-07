"""Living Museum records distinguish documentary evidence from interpretation."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from pydantic import ConfigDict, Field, HttpUrl, model_validator

from .heritage_graph import ScientificRecord
from .living_store import RevisionConflict


class EvidenceClass(StrEnum):
    DOCUMENTED = "documented_evidence"
    INTERPRETIVE = "interpretive_reconstruction"


class MuseumAsset(ScientificRecord):
    kind: str = Field(pattern="^(image|audio|video|model_3d)$")
    url: HttpUrl
    license: str = Field(min_length=1, max_length=1000)
    attribution: str = Field(min_length=1, max_length=1000)
    evidence_class: EvidenceClass

    @model_validator(mode="after")
    def reconstruction_label(self):
        if self.kind == "model_3d" and self.evidence_class != EvidenceClass.INTERPRETIVE:
            raise ValueError("Reconstructed 3D geometry is interpretive, not original manuscript evidence")
        return self


class MuseumObject(ScientificRecord):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: str(uuid4()), max_length=100)
    object_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1, max_length=5000)
    evidence_class: EvidenceClass
    original_illustration_region: str = Field(min_length=1, max_length=200)
    historical_entity_ids: list[str] = Field(default_factory=list, max_length=100)
    assets: list[MuseumAsset] = Field(default_factory=list, max_length=30)
    interpretation_notes: str | None = Field(default=None, max_length=5000)
    parent_revision_id: str | None = None

    @model_validator(mode="after")
    def documented_region(self):
        if self.provenance.source.region_id != self.original_illustration_region:
            raise ValueError("Original illustration must match the source region")
        if not self.provenance.evidence:
            raise ValueError("Historical objects require explicit source evidence")
        if self.evidence_class == EvidenceClass.INTERPRETIVE and not self.interpretation_notes:
            raise ValueError("Interpretive reconstruction must disclose assumptions")
        return self


class Exhibition(ScientificRecord):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: str(uuid4()), max_length=100)
    exhibition_id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=500)
    theme: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=5000)
    object_ids: list[str] = Field(min_length=1, max_length=100)
    parent_revision_id: str | None = None


class MuseumRepository:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path)) as connection:
            connection.executescript('''
                CREATE TABLE IF NOT EXISTS museum_revisions(sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                  id TEXT UNIQUE, kind TEXT, object_id TEXT, payload TEXT);
                CREATE TABLE IF NOT EXISTS museum_audit(sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                  revision_id TEXT, parent_revision_id TEXT, actor TEXT, timestamp TEXT);
            ''')
            connection.commit()

    def append(self, item: MuseumObject | Exhibition, *, actor: str):
        kind = "object" if isinstance(item, MuseumObject) else "exhibition"
        object_id = item.object_id if kind == "object" else item.exhibition_id
        with closing(sqlite3.connect(self.path, timeout=5)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            if kind == "exhibition":
                for identifier in item.object_ids:
                    if not connection.execute("SELECT 1 FROM museum_revisions WHERE kind='object' AND object_id=?", (identifier,)).fetchone():
                        raise ValueError("Exhibition references an unknown historical object")
            head = connection.execute("SELECT id FROM museum_revisions WHERE kind=? AND object_id=? ORDER BY sequence DESC LIMIT 1", (kind, object_id)).fetchone()
            if item.parent_revision_id != (head[0] if head else None):
                raise RevisionConflict("Museum parent revision must match current record")
            try:
                connection.execute("INSERT INTO museum_revisions(id,kind,object_id,payload) VALUES(?,?,?,?)", (item.id, kind, object_id, item.model_dump_json()))
            except sqlite3.IntegrityError as exc:
                raise RevisionConflict("Museum revision identity is immutable") from exc
            connection.execute("INSERT INTO museum_audit(revision_id,parent_revision_id,actor,timestamp) VALUES(?,?,?,?)", (item.id,item.parent_revision_id,actor,datetime.now(UTC).isoformat()))
        return item

    def current(self, kind: str):
        model = MuseumObject if kind == "object" else Exhibition
        with closing(sqlite3.connect(self.path)) as connection:
            rows = connection.execute("SELECT payload FROM museum_revisions WHERE sequence IN (SELECT MAX(sequence) FROM museum_revisions WHERE kind=? GROUP BY object_id) ORDER BY sequence", (kind,)).fetchall()
        return [model.model_validate_json(row[0]) for row in rows]
