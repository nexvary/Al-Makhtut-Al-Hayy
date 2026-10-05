"""Sourced historical entities, temporal intervals and geographic relationships."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .living import LayerProvenance, ReviewState
from .living_store import RevisionConflict


class EntityKind(StrEnum):
    PERSON = "person"
    AUTHOR = "author"
    SCHOLAR = "scholar"
    BOOK = "book"
    MANUSCRIPT = "manuscript"
    WORK = "work"
    CITY = "city"
    COUNTRY = "country"
    PLACE = "historical_place"
    EVENT = "event"
    INSTRUMENT = "instrument"
    MEDICINE = "medicine"
    PLANT = "plant"
    CONCEPT = "scientific_concept"
    INSTITUTION = "institution"


class HistoricalInterval(BaseModel):
    start_year: int = Field(ge=-10000, le=3000)
    end_year: int = Field(ge=-10000, le=3000)
    circa: bool = False
    calendar: str = "proleptic-gregorian"

    @model_validator(mode="after")
    def interval(self):
        if self.end_year < self.start_year:
            raise ValueError("Historical interval end precedes start")
        if self.calendar != "proleptic-gregorian":
            raise ValueError("Convert dates explicitly before comparison; source date stays in provenance")
        return self


class HistoricalLocation(BaseModel):
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    approximate: bool = True
    label: str = Field(min_length=1, max_length=200)


class ScientificRecord(BaseModel):
    state: ReviewState = ReviewState.DRAFT
    provenance: LayerProvenance

    @model_validator(mode="after")
    def review_integrity(self):
        if self.state == ReviewState.VERIFIED and not self.provenance.reviewer:
            raise ValueError("Verified scientific record requires a human reviewer")
        if self.state == ReviewState.MACHINE and not self.provenance.model:
            raise ValueError("Machine scientific record requires model identity")
        return self


class HistoricalEntity(ScientificRecord):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: str(uuid4()), max_length=100)
    entity_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=500)
    kind: EntityKind
    alternate_names: list[str] = Field(default_factory=list, max_length=100)
    interval: HistoricalInterval | None = None
    location: HistoricalLocation | None = None
    description: str | None = Field(default=None, max_length=5000)
    state: ReviewState = ReviewState.DRAFT
    provenance: LayerProvenance
    parent_revision_id: str | None = None


class HistoricalRelation(ScientificRecord):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: str(uuid4()), max_length=100)
    relation_id: str = Field(min_length=1, max_length=100)
    subject: str = Field(min_length=1, max_length=100)
    predicate: str = Field(min_length=1, max_length=100)
    object: str = Field(min_length=1, max_length=100)
    interval: HistoricalInterval | None = None
    state: ReviewState = ReviewState.DRAFT
    provenance: LayerProvenance
    parent_revision_id: str | None = None


class GraphRepository:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path)) as connection:
            connection.executescript('''
                CREATE TABLE IF NOT EXISTS heritage_revisions(sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                  id TEXT UNIQUE, kind TEXT, object_id TEXT, payload TEXT);
                CREATE INDEX IF NOT EXISTS heritage_head ON heritage_revisions(kind,object_id,sequence);
                CREATE TABLE IF NOT EXISTS heritage_audit(sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                  revision_id TEXT, parent_revision_id TEXT, actor TEXT, timestamp TEXT);
            ''')
            connection.commit()

    def append(self, item: HistoricalEntity | HistoricalRelation, *, actor: str):
        kind = "entity" if isinstance(item, HistoricalEntity) else "relation"
        object_id = item.entity_id if kind == "entity" else item.relation_id
        with closing(sqlite3.connect(self.path, timeout=5)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            if kind == "relation":
                for entity_id in {item.subject, item.object}:
                    if not connection.execute("SELECT 1 FROM heritage_revisions WHERE kind='entity' AND object_id=?", (entity_id,)).fetchone():
                        raise ValueError("Graph relation requires known source and target entities")
            head = connection.execute("SELECT id FROM heritage_revisions WHERE kind=? AND object_id=? ORDER BY sequence DESC LIMIT 1", (kind, object_id)).fetchone()
            if item.parent_revision_id != (head[0] if head else None):
                raise RevisionConflict("Graph parent revision must match current object head")
            try:
                connection.execute("INSERT INTO heritage_revisions(id,kind,object_id,payload) VALUES(?,?,?,?)", (item.id, kind, object_id, item.model_dump_json()))
            except sqlite3.IntegrityError as exc:
                raise RevisionConflict("Graph revision identity is immutable") from exc
            connection.execute("INSERT INTO heritage_audit(revision_id,parent_revision_id,actor,timestamp) VALUES(?,?,?,?)", (item.id, item.parent_revision_id, actor, datetime.now(UTC).isoformat()))
        return item

    def current(self, kind: str):
        model = HistoricalEntity if kind == "entity" else HistoricalRelation
        with closing(sqlite3.connect(self.path)) as connection:
            rows = connection.execute("SELECT payload FROM heritage_revisions WHERE sequence IN (SELECT MAX(sequence) FROM heritage_revisions WHERE kind=? GROUP BY object_id) ORDER BY sequence", (kind,)).fetchall()
        return [model.model_validate_json(row[0]) for row in rows]

    def time_slice(self, start: int, end: int) -> list[HistoricalEntity]:
        if end < start:
            raise ValueError("Requested time interval is reversed")
        return [item for item in self.current("entity") if item.interval and item.interval.start_year <= end and item.interval.end_year >= start]

    def neighbors(self, entity_id: str) -> dict:
        relations = [r for r in self.current("relation") if entity_id in {r.subject, r.object}]
        ids = {entity_id} | {r.subject for r in relations} | {r.object for r in relations}
        return {"entities": [e for e in self.current("entity") if e.entity_id in ids], "relations": relations}

    def geojson(self, start: int | None = None, end: int | None = None) -> dict:
        entities = self.current("entity") if start is None else self.time_slice(start, end if end is not None else start)
        features = []
        for entity in entities:
            if not entity.location:
                continue
            features.append({"type": "Feature", "id": entity.entity_id,
                             "geometry": {"type": "Point", "coordinates": [entity.location.longitude, entity.location.latitude]},
                             "properties": {"name": entity.name, "kind": entity.kind, "approximate": entity.location.approximate,
                                            "interval": entity.interval, "state": entity.state, "provenance": entity.provenance}})
        return {"type": "FeatureCollection", "features": features}
