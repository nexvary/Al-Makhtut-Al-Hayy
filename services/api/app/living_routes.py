from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from .auth import Role, require_roles
from .living import LayerKind, LivingLayer, ReviewState
from .living_store import RevisionConflict, SqliteLayerRepository
from .repository import repository
from .scholarship import scholarship_store

router = APIRouter(prefix="/api/v1/living", tags=["living-layers"])


@lru_cache(maxsize=1)
def layer_repository() -> SqliteLayerRepository:
    return SqliteLayerRepository(Path(os.getenv("LIVING_METADATA_PATH", "./data/living.sqlite3")))


def check_anchor(item: LivingLayer) -> None:
    source = item.provenance.source
    manuscript = repository.get(source.manuscript_id)
    if manuscript is None:
        raise HTTPException(404, "Source manuscript not found")
    page = next((page for page in manuscript.pages if page.id == source.page_id), None)
    if page is None:
        raise HTTPException(404, "Source page not found")
    if source.region_id and not any(region.id == source.region_id for region in page.regions):
        raise HTTPException(404, "Source region not found")
    if source.witness_id:
        witness = scholarship_store.get_witness(source.witness_id)
        if witness is None or witness.manuscript_id != source.manuscript_id:
            raise HTTPException(422, "Witness must refer to this source manuscript")
    for point in source.coordinates:
        if point.x < 0 or point.y < 0:
            raise HTTPException(422, "Source coordinates must be non-negative")
        if ((page.image_width and point.x > page.image_width)
                or (page.image_height and point.y > page.image_height)):
            raise HTTPException(422, "Source coordinates exceed the original image")


@router.post("/layers", response_model=LivingLayer)
def append_layer(
    item: LivingLayer,
    actor: Annotated[dict, Depends(require_roles(Role.TRANSCRIBER, Role.EDITOR, Role.REVIEWER, Role.ADMIN))],
    store: Annotated[SqliteLayerRepository, Depends(layer_repository)],
) -> LivingLayer:
    if item.kind == LayerKind.ORIGINAL:
        raise HTTPException(409, "Original images belong to the source page and cannot be overwritten")
    if item.state == ReviewState.VERIFIED:
        if actor["role"] not in {Role.REVIEWER, Role.ADMIN}:
            raise HTTPException(403, "Human verification requires a reviewer")
        if item.provenance.reviewer != actor["sub"]:
            raise HTTPException(403, "Reviewer must match the authenticated actor")
    check_anchor(item)
    # Reject unsupported evidence anchors instead of merely recording a plausible citation.
    for citation in item.provenance.evidence:
        evidence_layer = item.model_copy(deep=True)
        evidence_layer.provenance.source.manuscript_id = citation.manuscript_id
        evidence_layer.provenance.source.page_id = citation.page_id
        evidence_layer.provenance.source.region_id = citation.region_id
        evidence_layer.provenance.source.witness_id = None
        evidence_layer.provenance.source.coordinates = []
        check_anchor(evidence_layer)
    try:
        return store.append(item, actor=actor["sub"])
    except RevisionConflict as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/manuscripts/{manuscript_id}/pages/{page_id}/layers")
def page_layers(
    manuscript_id: str, page_id: str,
    store: Annotated[SqliteLayerRepository, Depends(layer_repository)],
) -> dict:
    manuscript = repository.get(manuscript_id)
    page = next((page for page in manuscript.pages if page.id == page_id), None) if manuscript else None
    if page is None:
        raise HTTPException(404, "Source page not found")
    return {"original_image": page.image, "layers": store.history(manuscript_id, page_id)}


@router.get("/audit", dependencies=[Depends(require_roles(Role.REVIEWER, Role.ADMIN))])
def audit(store: Annotated[SqliteLayerRepository, Depends(layer_repository)]) -> list[dict]:
    return store.audit()
