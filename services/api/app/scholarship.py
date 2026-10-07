from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from threading import RLock

from pydantic import BaseModel, Field

from .citations import CitationTarget


class WitnessKind(StrEnum):
    MANUSCRIPT = "manuscript"
    PRINT = "print"
    EDITION = "edition"
    TRANSLATION = "translation"


class BibliographicMetadata(BaseModel):
    title: str
    author: str | None = None
    date_label: str | None = None
    language: str = "ar"
    repository: str | None = None
    shelfmark: str | None = None
    place: str | None = None
    identifier: str | None = None
    source_url: str | None = None
    rights: str | None = None


class Work(BaseModel):
    id: str
    title: str
    author: str | None = None
    description: str | None = None


class Witness(BaseModel):
    id: str
    work_id: str
    manuscript_id: str | None = None
    kind: WitnessKind
    label: str
    bibliography: BibliographicMetadata


class VariantReading(BaseModel):
    id: str
    work_id: str
    locus: str
    readings: dict[str, str]
    note: str | None = None
    sources: list[CitationTarget] = Field(default_factory=list)


class WitnessAlignment(BaseModel):
    id: str
    work_id: str
    witness_a: str
    witness_b: str
    pairs: list[tuple[str, str]] = Field(default_factory=list)
    method: str = "manual"


class ScholarshipStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._works: dict[str, Work] = {}
        self._witnesses: dict[str, Witness] = {}
        self._variants: dict[str, VariantReading] = {}
        self._alignments: dict[str, WitnessAlignment] = {}

    def put_work(self, item: Work) -> Work:
        with self._lock:
            self._works[item.id] = item
        return item

    def put_witness(self, item: Witness) -> Witness:
        with self._lock:
            self._witnesses[item.id] = item
        return item

    def put_variant(self, item: VariantReading) -> VariantReading:
        with self._lock:
            self._variants[item.id] = item
        return item

    def put_alignment(self, item: WitnessAlignment) -> WitnessAlignment:
        with self._lock:
            self._alignments[item.id] = item
        return item

    def get_witness(self, witness_id: str) -> Witness | None:
        with self._lock:
            return self._witnesses.get(witness_id)

    def witnesses(self, work_id: str) -> list[Witness]:
        with self._lock:
            return [item for item in self._witnesses.values() if item.work_id == work_id]

    def variants(self, work_id: str) -> list[VariantReading]:
        with self._lock:
            return [item for item in self._variants.values() if item.work_id == work_id]




class SqliteScholarshipStore(ScholarshipStore):
    """Light deployment adapter retaining works, witnesses and scholarly links."""

    def __init__(self, path) -> None:
        super().__init__()
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS scholarly_items("
                               "kind TEXT, id TEXT, work_id TEXT, payload TEXT, PRIMARY KEY(kind,id))")
            connection.execute("CREATE TABLE IF NOT EXISTS scholarly_audit(sequence INTEGER PRIMARY KEY AUTOINCREMENT, "
                               "kind TEXT,id TEXT,actor TEXT,old_payload TEXT,new_payload TEXT,timestamp TEXT)")

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.path, timeout=5)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _save(self, kind, item, *, actor="internal"):
        work_id = item.id if kind == "work" else item.work_id
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            previous = connection.execute("SELECT payload FROM scholarly_items WHERE kind=? AND id=?", (kind, item.id)).fetchone()
            connection.execute("INSERT INTO scholarly_items VALUES(?,?,?,?) "
                               "ON CONFLICT(kind,id) DO UPDATE SET work_id=excluded.work_id,payload=excluded.payload",
                               (kind, item.id, work_id, item.model_dump_json()))
            connection.execute("INSERT INTO scholarly_audit(kind,id,actor,old_payload,new_payload,timestamp) VALUES(?,?,?,?,?,?)",
                               (kind, item.id, actor, previous[0] if previous else None,
                                item.model_dump_json(), datetime.now(UTC).isoformat()))
        return item

    def _list(self, kind, model, work_id=None):
        with self.connection() as connection:
            if work_id is None:
                rows = connection.execute("SELECT payload FROM scholarly_items WHERE kind=?", (kind,)).fetchall()
            else:
                rows = connection.execute("SELECT payload FROM scholarly_items WHERE kind=? AND work_id=?", (kind, work_id)).fetchall()
        return [model.model_validate_json(row[0]) for row in rows]

    def put_work(self, item: Work, *, actor: str = "internal") -> Work:
        return self._save("work", item, actor=actor)

    def get_work(self, work_id: str) -> Work | None:
        return next((item for item in self._list("work", Work) if item.id == work_id), None)

    def put_witness(self, item: Witness, *, actor: str = "internal") -> Witness:
        if self.get_work(item.work_id) is None:
            raise ValueError("Witness requires an existing work")
        return self._save("witness", item, actor=actor)

    def get_witness(self, witness_id: str) -> Witness | None:
        return next((item for item in self._list("witness", Witness) if item.id == witness_id), None)

    def put_variant(self, item: VariantReading, *, actor: str = "internal") -> VariantReading:
        known = {w.id for w in self.witnesses(item.work_id)}
        if len(item.readings) < 2 or not set(item.readings).issubset(known):
            raise ValueError("Variants require at least two witnesses of the same work")
        return self._save("variant", item, actor=actor)

    def put_alignment(self, item: WitnessAlignment, *, actor: str = "internal") -> WitnessAlignment:
        known = {w.id for w in self.witnesses(item.work_id)}
        if item.witness_a == item.witness_b or not {item.witness_a, item.witness_b}.issubset(known):
            raise ValueError("Alignments require different witnesses of the same work")
        return self._save("alignment", item, actor=actor)

    def witnesses(self, work_id: str) -> list[Witness]:
        return self._list("witness", Witness, work_id)

    def variants(self, work_id: str) -> list[VariantReading]:
        return self._list("variant", VariantReading, work_id)


scholarship_store = SqliteScholarshipStore(Path(os.getenv("SCHOLARSHIP_METADATA_PATH", "./data/scholarship.sqlite3")))
