import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from .auth import Role, require_roles
from .heritage_routes import graph_repository, save
from .living import LayerKind, LivingLayer, ReviewState
from .living_routes import check_anchor
from .museum import Exhibition, MuseumObject, MuseumRepository

router = APIRouter(prefix="/api/v1/museum", tags=["living-museum"])


@lru_cache(maxsize=1)
def museum_repository() -> MuseumRepository:
    return MuseumRepository(Path(os.getenv("MUSEUM_METADATA_PATH", "./data/museum.sqlite3")))


Store = Annotated[MuseumRepository, Depends(museum_repository)]
Curator = Annotated[dict, Depends(require_roles(Role.REVIEWER, Role.ADMIN))]


@router.post("/objects", response_model=MuseumObject)
def add_object(item: MuseumObject, actor: Curator, store: Store):
    known = {e.entity_id for e in graph_repository().current("entity")}
    if not set(item.historical_entity_ids).issubset(known):
        raise HTTPException(422, "Object refers to an unknown historical entity")
    for asset in item.assets:
        if asset.state == ReviewState.VERIFIED and asset.provenance.reviewer != actor["sub"]:
            raise HTTPException(403, "Asset verification requires the authenticated reviewer")
        check_anchor(LivingLayer(kind=LayerKind.ANNOTATIONS, data={"asset":True}, provenance=asset.provenance))
        for evidence in asset.provenance.evidence:
            proxy = LivingLayer(kind=LayerKind.ANNOTATIONS, data={"evidence":True}, provenance=asset.provenance.model_copy(deep=True))
            proxy.provenance.source.manuscript_id = evidence.manuscript_id
            proxy.provenance.source.page_id = evidence.page_id
            proxy.provenance.source.region_id = evidence.region_id
            proxy.provenance.source.witness_id = None
            proxy.provenance.source.coordinates = []
            check_anchor(proxy)
    return save(item, actor, store)


@router.post("/exhibitions", response_model=Exhibition)
def add_exhibition(item: Exhibition, actor: Curator, store: Store):
    return save(item, actor, store)


@router.get("/exhibitions", response_model=list[Exhibition])
def exhibitions(store: Store):
    return store.current("exhibition")


@router.get("/exhibitions/{exhibition_id}")
def exhibition(exhibition_id: str, store: Store):
    item = next((x for x in store.current("exhibition") if x.exhibition_id == exhibition_id), None)
    if item is None:
        raise HTTPException(404, "Exhibition not found")
    by_id = {o.object_id:o for o in store.current("object")}
    return {"exhibition": item, "objects": [by_id[x] for x in item.object_ids],
            "notice": "Reconstruction is interpretive; original source evidence remains accessible."}
