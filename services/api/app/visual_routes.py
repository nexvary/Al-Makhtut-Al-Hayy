from typing import Annotated

from fastapi import APIRouter, Depends

from .auth import Role, require_roles
from .visual_knowledge import (
    Exhibit,
    HistoricalObject,
    RelatedPassage,
    TimelineEvent,
    visual_store,
)

router = APIRouter(prefix="/api/v1/visual", tags=["visual-knowledge"])
Writer = Annotated[dict, Depends(require_roles(Role.REVIEWER, Role.ADMIN))]


@router.get("/objects", response_model=list[HistoricalObject])
def list_objects(manuscript_id: str | None = None) -> list[HistoricalObject]:
    return visual_store.list_objects(manuscript_id)


@router.post("/objects", response_model=HistoricalObject)
def put_object(item: HistoricalObject, actor: Writer) -> HistoricalObject:
    return visual_store.put_object(item,actor=actor["sub"])


@router.get("/timeline", response_model=list[TimelineEvent])
def timeline() -> list[TimelineEvent]:
    return visual_store.list_events()


@router.post("/timeline", response_model=TimelineEvent)
def put_timeline_event(item: TimelineEvent, actor: Writer) -> TimelineEvent:
    return visual_store.put_event(item,actor=actor["sub"])


@router.get("/exhibits", response_model=list[Exhibit])
def exhibits() -> list[Exhibit]:
    return visual_store.list_exhibits()


@router.post("/exhibits", response_model=Exhibit)
def put_exhibit(item: Exhibit, actor: Writer) -> Exhibit:
    return visual_store.put_exhibit(item,actor=actor["sub"])


@router.get("/relations", response_model=list[RelatedPassage])
def relations() -> list[RelatedPassage]:
    return visual_store.relations()


@router.post("/relations", response_model=RelatedPassage)
def add_relation(item: RelatedPassage, actor: Writer) -> RelatedPassage:
    return visual_store.add_relation(item,actor=actor["sub"])
