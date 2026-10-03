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
    dependencies=[Depends(require_roles(Role.REVIEWER, Role.ADMIN))],
)
def upsert_glossary(item: GlossaryTerm) -> GlossaryTerm:
    return glossary_store.put(item)
