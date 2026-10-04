from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .auth import Role, require_roles
from .importers import manuscript_from_iiif
from .models import Manuscript
from .repository import repository
from .security import validate_public_http_url

router = APIRouter(prefix="/api/v1/ingestion", tags=["ingestion"])


class IiifImportRequest(BaseModel):
    manifest_url: str
    manifest: dict[str, Any]
    title: str = Field(min_length=1, max_length=500)
    author: str | None = None
    source_institution: str | None = None
    rights: str | None = None


@router.post(
    "/iiif",
    response_model=Manuscript,
)
def import_iiif(request: IiifImportRequest, actor: Annotated[dict, Depends(require_roles(Role.ADMIN))]) -> Manuscript:
    validate_public_http_url(request.manifest_url)
    manuscript = manuscript_from_iiif(
        request.manifest,
        manifest_url=request.manifest_url,
        title=request.title,
        author=request.author,
        source_institution=request.source_institution,
        rights=request.rights,
    )
    try:
        return repository.put(manuscript, actor=actor["sub"])
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
