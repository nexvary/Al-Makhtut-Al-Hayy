from fastapi import APIRouter, Depends, HTTPException

from .auth import Role, require_roles
from .editorial import TextRevision, editorial_store

router = APIRouter(prefix="/api/v1/editorial", tags=["editorial"])


@router.post(
    "/revisions",
    response_model=TextRevision,
    dependencies=[Depends(require_roles(Role.TRANSCRIBER, Role.REVIEWER, Role.ADMIN))],
)
def create_revision(revision: TextRevision) -> TextRevision:
    try:
        return editorial_store.add_revision(revision)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get(
    "/revisions/{manuscript_id}/{page_id}/{region_id}",
    response_model=list[TextRevision],
)
def list_revisions(manuscript_id: str, page_id: str, region_id: str) -> list[TextRevision]:
    return editorial_store.history(manuscript_id, page_id, region_id)
