import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from .auth import Role, require_roles
from .heritage_graph import GraphRepository, HistoricalEntity, HistoricalRelation
from .living import LayerKind, LivingLayer, ReviewState
from .living_routes import check_anchor
from .living_store import RevisionConflict

router = APIRouter(prefix="/api/v1/heritage", tags=["historical-knowledge"])
Writer = Annotated[dict, Depends(require_roles(Role.EDITOR, Role.REVIEWER, Role.ADMIN))]


@lru_cache(maxsize=1)
def graph_repository() -> GraphRepository:
    return GraphRepository(Path(os.getenv("HERITAGE_METADATA_PATH", "./data/heritage.sqlite3")))


Store = Annotated[GraphRepository, Depends(graph_repository)]


def save(item: HistoricalEntity | HistoricalRelation, actor: dict, store: GraphRepository):
    if item.state == ReviewState.VERIFIED and (actor["role"] not in {Role.REVIEWER, Role.ADMIN} or item.provenance.reviewer != actor["sub"]):
        raise HTTPException(403, "Graph verification requires the authenticated reviewer")
    proxy = LivingLayer(kind=LayerKind.ANNOTATIONS, data={"heritage": True}, provenance=item.provenance)
    check_anchor(proxy)
    for evidence in item.provenance.evidence:
        linked = proxy.model_copy(deep=True)
        linked.provenance.source.manuscript_id = evidence.manuscript_id
        linked.provenance.source.page_id = evidence.page_id
        linked.provenance.source.region_id = evidence.region_id
        linked.provenance.source.witness_id = None
        linked.provenance.source.coordinates = []
        check_anchor(linked)
    try:
        return store.append(item, actor=actor["sub"])
    except RevisionConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/entities", response_model=HistoricalEntity)
def add_entity(item: HistoricalEntity, actor: Writer, store: Store):
    return save(item, actor, store)


@router.post("/relations", response_model=HistoricalRelation)
def add_relation(item: HistoricalRelation, actor: Writer, store: Store):
    return save(item, actor, store)


@router.get("/entities", response_model=list[HistoricalEntity])
def entities(store: Store, q: str = Query(default="", max_length=200)):
    return [e for e in store.current("entity") if q.casefold() in e.name.casefold() or any(q.casefold() in n.casefold() for n in e.alternate_names)]


@router.get("/entities/{entity_id}")
def entity_context(entity_id: str, store: Store):
    result = store.neighbors(entity_id)
    if not any(e.entity_id == entity_id for e in result["entities"]):
        raise HTTPException(404, "Historical entity not found")
    return result


@router.get("/time-machine", response_model=list[HistoricalEntity])
def time_machine(store: Store, start: int = Query(ge=-10000, le=3000), end: int = Query(ge=-10000, le=3000)):
    try:
        return store.time_slice(start, end)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/map")
def historical_map(store: Store, start: int | None = Query(default=None, ge=-10000, le=3000),
                   end: int | None = Query(default=None, ge=-10000, le=3000)):
    if end is not None and start is None:
        raise HTTPException(422, "Map end year requires a start year")
    try:
        return store.geojson(start, end)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
