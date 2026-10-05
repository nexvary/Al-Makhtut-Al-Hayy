import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from .auth import Role, require_roles
from .living import LayerKind, LivingLayer
from .living_routes import check_anchor
from .repository import repository
from .visual_index import ImageIndexRequest, ImageQuery, ThumbnailVisualProvider

router = APIRouter(prefix="/api/v1/visual-search", tags=["visual-discovery"])


@lru_cache(maxsize=1)
def visual_index():
    return ThumbnailVisualProvider(Path(os.getenv("VISUAL_INDEX_PATH", "./data/visual-index.sqlite3")))


Store = Annotated[ThumbnailVisualProvider, Depends(visual_index)]


@router.get("/capabilities")
def capabilities():
    return {"provider": "dhash-64-thumbnail-v1", "kinds": ["fragment", "illustration"],
            "maximum_pixels": 1048576, "maximum_image_bytes": 1048576,
            "notice": "Visual resemblance only; not semantic, handwriting or historical attribution."}


@router.post("/index")
def publish(item: ImageIndexRequest, store: Store,
            actor: Annotated[dict, Depends(require_roles(Role.REVIEWER, Role.ADMIN))]):
    check_anchor(LivingLayer(kind=LayerKind.ANNOTATIONS, data={"visual-index": True}, provenance=item.provenance))
    manuscript = repository.get(item.provenance.source.manuscript_id)
    if not manuscript.license or item.source_license != manuscript.license:
        raise HTTPException(422, "Curated thumbnails require the recorded manuscript license")
    page = next(p for p in manuscript.pages if p.id == item.provenance.source.page_id)
    if item.provenance.source.source_uri != page.image:
        raise HTTPException(422, "Original image URI must match the source page")
    item.provenance.reviewer = actor["sub"]
    item.provenance.evidence = []  # Index attestation is not an additional scholarly text citation.
    try:
        return store.publish(item, actor=actor["sub"])
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/query")
def query(item: ImageQuery, store: Store):
    try:
        return {"matches": store.search_image(item),
                "notice": "Candidates require human comparison with the original. Similarity is not confidence."}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
