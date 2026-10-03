from __future__ import annotations

from enum import StrEnum
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

    def witnesses(self, work_id: str) -> list[Witness]:
        with self._lock:
            return [item for item in self._witnesses.values() if item.work_id == work_id]

    def variants(self, work_id: str) -> list[VariantReading]:
        with self._lock:
            return [item for item in self._variants.values() if item.work_id == work_id]


scholarship_store = ScholarshipStore()
