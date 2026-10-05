"""Source-backed dictionary and exercises; no fabricated teaching corpus is bundled."""
from __future__ import annotations

import sqlite3
import unicodedata
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .living import LayerProvenance, ReviewState
from .living_store import RevisionConflict
from .ottoman import OttomanRecord, OttomanStage


class DictionaryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: str(uuid4()), max_length=100)
    entry_id: str = Field(min_length=1, max_length=100)
    spelling: str = Field(min_length=1, max_length=500)
    transliteration: str | None = Field(default=None, max_length=500)
    modern_turkish: str | None = Field(default=None, max_length=2000)
    arabic: str | None = Field(default=None, max_length=2000)
    english: str | None = Field(default=None, max_length=2000)
    grammatical_note: str | None = Field(default=None, max_length=2000)
    historical_meaning: str | None = Field(default=None, max_length=2000)
    linguistic_origin: str | None = Field(default=None, max_length=200)
    related_forms: list[str] = Field(default_factory=list, max_length=100)
    state: ReviewState = ReviewState.DRAFT
    provenance: LayerProvenance
    parent_revision_id: str | None = None

    @model_validator(mode="after")
    def evidence_required(self):
        if self.linguistic_origin and (self.state != ReviewState.VERIFIED or not self.provenance.evidence):
            raise ValueError("Etymology requires human verification and explicit documentary evidence")
        if self.state == ReviewState.VERIFIED and not self.provenance.reviewer:
            raise ValueError("Verified dictionary entry requires a reviewer")
        return self


class ReadingExercise(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: str(uuid4()), max_length=100)
    title: str = Field(min_length=1, max_length=200)
    transcription_revision: str = Field(min_length=1, max_length=100)
    transliteration_revision: str | None = Field(default=None, max_length=100)
    modernization_revision: str | None = Field(default=None, max_length=100)
    arabic_revision: str | None = Field(default=None, max_length=100)
    rights_note: str = Field(min_length=1, max_length=2000)
    source_license: str = Field(min_length=1, max_length=500)


def normalize_answer(text: str) -> str:
    # Whitespace/NFC normalization only; never silently equate different Ottoman letters.
    return " ".join(unicodedata.normalize("NFC", text).split())


def validate_exercise(item: ReadingExercise, records: list[OttomanRecord]) -> list[OttomanRecord]:
    by_id = {r.id: r for r in records}
    chain = []
    fields = [(item.transcription_revision, OttomanStage.TRANSCRIPTION),
              (item.transliteration_revision, OttomanStage.TRANSLITERATION),
              (item.modernization_revision, OttomanStage.MODERNIZATION),
              (item.arabic_revision, OttomanStage.ARABIC)]
    for revision, stage in fields:
        if not revision:
            continue
        record = by_id.get(revision)
        if not record or record.stage != stage or record.state != ReviewState.VERIFIED:
            raise ValueError("Exercises require verified revisions of the specified stage")
        if chain and record.input_revision_id != chain[-1].id:
            raise ValueError("Exercise reveal steps must form one documented derivation chain")
        chain.append(record)
    return chain


class AcademyRepository:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path)) as connection:
            connection.executescript('''
                CREATE TABLE IF NOT EXISTS dictionary_revisions(
                  sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE,
                  entry_id TEXT, payload TEXT);
                CREATE TABLE IF NOT EXISTS academy_exercises(id TEXT PRIMARY KEY,
                  manuscript_id TEXT, page_id TEXT, payload TEXT);
                CREATE TABLE IF NOT EXISTS academy_audit(sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                  object_id TEXT, kind TEXT, actor TEXT, timestamp TEXT);
            ''')
            connection.commit()

    def append_entry(self, item: DictionaryEntry, *, actor: str) -> DictionaryEntry:
        with closing(sqlite3.connect(self.path, timeout=5)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            head = connection.execute("SELECT id FROM dictionary_revisions WHERE entry_id=? ORDER BY sequence DESC LIMIT 1", (item.entry_id,)).fetchone()
            if item.parent_revision_id != (head[0] if head else None):
                raise RevisionConflict("Dictionary parent revision must match current entry")
            try:
                connection.execute("INSERT INTO dictionary_revisions(id,entry_id,payload) VALUES(?,?,?)", (item.id, item.entry_id, item.model_dump_json()))
            except sqlite3.IntegrityError as exc:
                raise RevisionConflict("Dictionary revision IDs cannot be reused") from exc
            self._audit(connection, item.id, "dictionary", actor)
        return item

    def entries(self, query: str, *, limit=30) -> list[DictionaryEntry]:
        with closing(sqlite3.connect(self.path)) as connection:
            rows = connection.execute("SELECT payload FROM dictionary_revisions WHERE sequence IN (SELECT MAX(sequence) FROM dictionary_revisions GROUP BY entry_id) ORDER BY sequence DESC").fetchall()
        words = normalize_answer(query).casefold()
        result = [DictionaryEntry.model_validate_json(r[0]) for r in rows]
        return [r for r in result if any(words in normalize_answer(x).casefold() for x in [r.spelling, r.transliteration or "", r.modern_turkish or "", r.arabic or "", r.english or ""])][:limit]

    def put_exercise(self, item: ReadingExercise, manuscript_id: str, page_id: str, *, actor: str):
        with closing(sqlite3.connect(self.path, timeout=5)) as connection, connection:
            try:
                connection.execute("INSERT INTO academy_exercises VALUES(?,?,?,?)", (item.id, manuscript_id, page_id, item.model_dump_json()))
            except sqlite3.IntegrityError as exc:
                raise RevisionConflict("Exercise identity is immutable; create a new exercise") from exc
            self._audit(connection, item.id, "exercise", actor)
        return item

    def exercises(self, manuscript_id: str, page_id: str) -> list[ReadingExercise]:
        with closing(sqlite3.connect(self.path)) as connection:
            rows = connection.execute("SELECT payload FROM academy_exercises WHERE manuscript_id=? AND page_id=?", (manuscript_id, page_id)).fetchall()
        return [ReadingExercise.model_validate_json(r[0]) for r in rows]

    @staticmethod
    def _audit(connection, object_id, kind, actor):
        connection.execute("INSERT INTO academy_audit(object_id,kind,actor,timestamp) VALUES(?,?,?,?)", (object_id, kind, actor, datetime.now(UTC).isoformat()))
