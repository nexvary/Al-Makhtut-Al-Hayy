from __future__ import annotations

from pydantic import BaseModel


class CitationTarget(BaseModel):
    manuscript_id: str
    page_id: str
    region_id: str | None = None
    canvas_uri: str | None = None
    label: str | None = None


def citation_key(target: CitationTarget) -> str:
    parts = [target.manuscript_id, target.page_id]
    if target.region_id:
        parts.append(target.region_id)
    return ":".join(parts)
