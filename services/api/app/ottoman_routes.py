import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from .auth import Role, require_roles
from .living import LayerKind, LivingLayer, ReviewState
from .living_routes import check_anchor
from .living_store import RevisionConflict
from .ottoman import LANGUAGES, OttomanRecord, OttomanRepository, OttomanStage
from .repository import repository

router = APIRouter(prefix="/api/v1/ottoman", tags=["ottoman-lab"])


@lru_cache(maxsize=1)
def ottoman_repository() -> OttomanRepository:
    return OttomanRepository(Path(os.getenv("OTTOMAN_METADATA_PATH", "./data/ottoman.sqlite3")))


@router.get("/stages")
def stages() -> list[dict]:
    return [{"stage": stage, "language": LANGUAGES[stage], "automatic_provider_available": False}
            for stage in OttomanStage]


@router.post("/revisions", response_model=OttomanRecord)
def append_record(item: OttomanRecord,
                  actor: Annotated[dict, Depends(require_roles(Role.TRANSCRIBER, Role.EDITOR, Role.REVIEWER, Role.ADMIN))],
                  store: Annotated[OttomanRepository, Depends(ottoman_repository)]) -> OttomanRecord:
    if item.state == ReviewState.VERIFIED and (
        actor["role"] not in {Role.REVIEWER, Role.ADMIN} or item.provenance.reviewer != actor["sub"]
    ):
        raise HTTPException(403, "Verification requires the authenticated reviewer")
    check_anchor(LivingLayer(kind=LayerKind.ANNOTATIONS, data={"ottoman": True}, provenance=item.provenance))
    for citation in item.provenance.evidence:
        proxy = LivingLayer(kind=LayerKind.ANNOTATIONS, data={"evidence": True}, provenance=item.provenance.model_copy(deep=True))
        proxy.provenance.source.manuscript_id = citation.manuscript_id
        proxy.provenance.source.page_id = citation.page_id
        proxy.provenance.source.region_id = citation.region_id
        proxy.provenance.source.witness_id = None
        proxy.provenance.source.coordinates = []
        check_anchor(proxy)
    try:
        return store.append(item, actor=actor["sub"])
    except RevisionConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/manuscripts/{manuscript_id}/pages/{page_id}")
def page_pipeline(manuscript_id: str, page_id: str,
                  store: Annotated[OttomanRepository, Depends(ottoman_repository)]) -> dict:
    manuscript = repository.get(manuscript_id)
    page = next((p for p in manuscript.pages if p.id == page_id), None) if manuscript else None
    if page is None:
        raise HTTPException(404, "Source page not found")
    return {"original_image": page.image, "revisions": store.history(manuscript_id, page_id)}
