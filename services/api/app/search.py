from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Protocol

from .arabic import tokenize_arabic
from .citations import CitationTarget


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
                continue
            combined.append(
                SearchHit(
                    document=lexical_hit.document,
                    lexical_score=lexical_hit.lexical_score,
                    vector_score=vector_hits.get(doc_id, 0.0),
                )
            )
        return sorted(combined, key=lambda hit: hit.score, reverse=True)[:limit]
