from __future__ import annotations

import heapq
import json
import sqlite3
from collections import Counter
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .arabic import tokenize_arabic
from .citations import CitationTarget
from .legacy_store import LegacyRecordStore


@dataclass(frozen=True)
class SearchDocument:
    id: str
    text: str
    citation: CitationTarget
    verified: bool = False


@dataclass(frozen=True)
class SearchHit:
    document: SearchDocument
    lexical_score: float
    vector_score: float = 0.0

    @property
    def score(self) -> float:
        verification_boost = 0.15 if self.document.verified else 0.0
        return (0.65 * self.lexical_score) + (0.35 * self.vector_score) + verification_boost


class VectorSearch(Protocol):
    def search(self, query: str, *, limit: int) -> list[tuple[str, float]]: ...


class NullVectorSearch:
    def search(self, query: str, *, limit: int) -> list[tuple[str, float]]:
        return []


class InMemorySearchIndex:
    def __init__(self) -> None:
        self._documents: dict[str, SearchDocument] = {}
        self._terms: dict[str, Counter[str]] = {}

    def upsert(self, document: SearchDocument) -> None:
        self._documents[document.id] = document
        self._terms[document.id] = Counter(tokenize_arabic(document.text))

    def get_document(self, identifier: str) -> SearchDocument | None:
        return self._documents.get(identifier)

    def search(self, query: str, *, limit: int = 10) -> list[SearchHit]:
        query_terms = Counter(tokenize_arabic(query))
        if not query_terms:
            return []
        hits: list[SearchHit] = []
        for doc_id, terms in self._terms.items():
            overlap = sum(min(count, terms.get(term, 0)) for term, count in query_terms.items())
            if overlap:
                lexical = overlap / max(sum(query_terms.values()), 1)
                hits.append(SearchHit(self._documents[doc_id], lexical_score=lexical))
        return sorted(hits, key=lambda hit: hit.score, reverse=True)[:limit]


class SqliteSearchIndex(InMemorySearchIndex):
    def __init__(self, path: Path | None = None):
        self.store = LegacyRecordStore(path)

    def upsert(self, document: SearchDocument) -> None:
        self.store.put("search-document",document.id,{"id":document.id,"text":document.text,
            "citation":document.citation.model_dump(mode="json"),"verified":document.verified},actor="search-indexer")

    def get_document(self, identifier: str) -> SearchDocument | None:
        with closing(sqlite3.connect(self.store.path)) as connection:
            row = connection.execute("SELECT payload FROM legacy_records WHERE kind='search-document' AND id=?",(identifier,)).fetchone()
        if row is None:
            return None
        item = json.loads(row[0])
        return SearchDocument(id=item["id"],text=item["text"],citation=CitationTarget.model_validate(item["citation"]),verified=item["verified"])

    def search(self, query: str, *, limit: int = 10) -> list[SearchHit]:
        query_terms = Counter(tokenize_arabic(query))
        if not query_terms:
            return []
        def candidates():
            for item in self.store.iter_rows("search-document",2000):
                terms = Counter(tokenize_arabic(item["text"]))
                overlap = sum(min(count,terms.get(term,0)) for term,count in query_terms.items())
                if overlap:
                    document = SearchDocument(id=item["id"],text=item["text"],citation=CitationTarget.model_validate(item["citation"]),verified=item["verified"])
                    yield SearchHit(document,lexical_score=overlap/max(sum(query_terms.values()),1))
        return heapq.nlargest(limit,candidates(),key=lambda hit:hit.score)


class HybridRetriever:
    def __init__(self, lexical: InMemorySearchIndex, vector: VectorSearch | None = None) -> None:
        self.lexical = lexical
        self.vector = vector or NullVectorSearch()

    def search(self, query: str, *, limit: int = 10) -> list[SearchHit]:
        lexical_hits = {hit.document.id: hit for hit in self.lexical.search(query, limit=limit * 2)}
        vector_hits = dict(self.vector.search(query, limit=limit * 2))
        ids = set(lexical_hits) | set(vector_hits)
        combined: list[SearchHit] = []
        for doc_id in ids:
            lexical_hit = lexical_hits.get(doc_id)
            if lexical_hit is None:
                document = self.lexical.get_document(doc_id)
                if document is None:
                    continue
                lexical_hit = SearchHit(document,lexical_score=0.0)
            combined.append(
                SearchHit(
                    document=lexical_hit.document,
                    lexical_score=lexical_hit.lexical_score,
                    vector_score=vector_hits.get(doc_id, 0.0),
                )
            )
        return sorted(combined, key=lambda hit: hit.score, reverse=True)[:limit]
