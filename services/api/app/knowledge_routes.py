from typing import Annotated

from fastapi import APIRouter, Depends

from .auth import Role, require_roles
from .knowledge import GlossaryTerm, glossary_store

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.get("/glossary", response_model=list[GlossaryTerm])
def list_glossary(manuscript_id: str | None = None) -> list[GlossaryTerm]:
    return glossary_store.list(manuscript_id)


@router.post(
    "/glossary",
    response_model=GlossaryTerm,
)
def upsert_glossary(item: GlossaryTerm, actor: Annotated[dict, Depends(require_roles(Role.REVIEWER, Role.ADMIN))]) -> GlossaryTerm:
    return glossary_store.put(item, actor=actor["sub"])
