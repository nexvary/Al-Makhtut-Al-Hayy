"""Ottoman stages are separate scholarly records, never a single translation field."""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .living import LayerProvenance, ReviewState
from .living_store import RevisionConflict


class OttomanStage(StrEnum):
    LAYOUT = "layout"
    HTR = "htr"
    TRANSCRIPTION = "transcription"
    TRANSLITERATION = "transliteration"
    MODERNIZATION = "modernization"
    ARABIC = "translation_ar"
    ENGLISH = "translation_en"


PREDECESSORS = {
    OttomanStage.LAYOUT: set(),
    OttomanStage.HTR: {OttomanStage.LAYOUT},
    OttomanStage.TRANSCRIPTION: {OttomanStage.HTR},
    OttomanStage.TRANSLITERATION: {OttomanStage.TRANSCRIPTION},
    OttomanStage.MODERNIZATION: {OttomanStage.TRANSLITERATION},
    OttomanStage.ARABIC: {OttomanStage.MODERNIZATION},
    OttomanStage.ENGLISH: {OttomanStage.MODERNIZATION},
}
LANGUAGES = {OttomanStage.LAYOUT: None, OttomanStage.HTR: "ota-Arab",
             OttomanStage.TRANSCRIPTION: "ota-Arab", OttomanStage.TRANSLITERATION: "ota-Latn",
             OttomanStage.MODERNIZATION: "tr", OttomanStage.ARABIC: "ar", OttomanStage.ENGLISH: "en"}


class OttomanRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    stage: OttomanStage
    state: ReviewState = ReviewState.DRAFT
    text: str | None = Field(default=None, max_length=100_000)
    layout: dict | None = None
    provenance: LayerProvenance
    input_revision_id: str | None = Field(default=None, max_length=100)
    parent_revision_id: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def integrity(self) -> OttomanRecord:
        if self.stage == OttomanStage.LAYOUT:
            if not self.layout or self.text:
                raise ValueError("Layout stores regions, not translated or transcribed text")
        elif not self.text or not self.text.strip() or self.layout is not None:
            raise ValueError("Text stages require text and cannot contain layout")
        if self.stage == OttomanStage.HTR and self.state != ReviewState.MACHINE:
            raise ValueError("HTR remains machine; review creates a transcription record")
        if self.state == ReviewState.MACHINE and not self.provenance.model:
            raise ValueError("Machine output requires its model identity")
        if self.state == ReviewState.VERIFIED and not self.provenance.reviewer:
            raise ValueError("Verified output requires a human reviewer")
        if self.stage not in {OttomanStage.LAYOUT, OttomanStage.TRANSCRIPTION} and not self.input_revision_id:
            raise ValueError("This stage requires an explicit upstream revision")
        return self


class OttomanRepository:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as connection:
            connection.executescript('''
                CREATE TABLE IF NOT EXISTS ottoman_schema(version INTEGER PRIMARY KEY);
                INSERT OR IGNORE INTO ottoman_schema VALUES(1);
                CREATE TABLE IF NOT EXISTS ottoman_revisions(
                  sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE,
                  manuscript_id TEXT, page_id TEXT, scope TEXT, payload TEXT);
                CREATE INDEX IF NOT EXISTS ottoman_page ON ottoman_revisions(manuscript_id,page_id);
                CREATE TABLE IF NOT EXISTS ottoman_audit(
                  sequence INTEGER PRIMARY KEY AUTOINCREMENT, revision_id TEXT, actor TEXT,
                  input_revision_id TEXT, parent_revision_id TEXT, timestamp TEXT);
            ''')
            connection.commit()

    def connect(self):
        # A connection is opened per operation. Caller closes it after commit/rollback.
        return sqlite3.connect(self.path, timeout=5)

    def append(self, item: OttomanRecord, *, actor: str) -> OttomanRecord:
        source = item.provenance.source
        scope = json.dumps([source.witness_id, source.region_id, item.stage])
        connection = self.connect()
        try:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                head = connection.execute("SELECT id FROM ottoman_revisions WHERE manuscript_id=? AND page_id=? AND scope=? ORDER BY sequence DESC LIMIT 1",
                                          (source.manuscript_id, source.page_id, scope)).fetchone()
                if item.parent_revision_id != (head[0] if head else None):
                    raise RevisionConflict("Ottoman parent revision must match current stage head")
                if item.input_revision_id:
                    row = connection.execute("SELECT payload FROM ottoman_revisions WHERE id=?", (item.input_revision_id,)).fetchone()
                    upstream = OttomanRecord.model_validate_json(row[0]) if row else None
                    if not upstream or upstream.stage not in PREDECESSORS[item.stage]:
                        raise ValueError("Input revision is missing or belongs to a different stage")
                    anchor = upstream.provenance.source
                    if (anchor.manuscript_id, anchor.page_id, anchor.witness_id, anchor.region_id) != (source.manuscript_id, source.page_id, source.witness_id, source.region_id):
                        raise ValueError("Input revision must refer to the same source region and witness")
                    # Verified downstream output must not conceal unreviewed dependencies.
                    if (item.state == ReviewState.VERIFIED and item.stage != OttomanStage.TRANSCRIPTION
                            and upstream.state != ReviewState.VERIFIED):
                        raise ValueError("Verified downstream output requires verified upstream text")
                if item.stage == OttomanStage.LAYOUT and item.input_revision_id:
                    raise ValueError("Layout is anchored to the original image, not generated text")
                try:
                    connection.execute("INSERT INTO ottoman_revisions(id,manuscript_id,page_id,scope,payload) VALUES(?,?,?,?,?)",
                                       (item.id, source.manuscript_id, source.page_id, scope, item.model_dump_json()))
                except sqlite3.IntegrityError as exc:
                    raise RevisionConflict("Revision identity is immutable") from exc
                connection.execute("INSERT INTO ottoman_audit(revision_id,actor,input_revision_id,parent_revision_id,timestamp) VALUES(?,?,?,?,?)",
                                   (item.id, actor, item.input_revision_id, item.parent_revision_id, datetime.now(UTC).isoformat()))
        finally:
            connection.close()
        return item

    def history(self, manuscript_id: str, page_id: str) -> list[OttomanRecord]:
        connection = self.connect()
        try:
            rows = connection.execute("SELECT payload FROM ottoman_revisions WHERE manuscript_id=? AND page_id=? ORDER BY sequence",
                                      (manuscript_id, page_id)).fetchall()
            return [OttomanRecord.model_validate_json(row[0]) for row in rows]
        finally:
            connection.close()
