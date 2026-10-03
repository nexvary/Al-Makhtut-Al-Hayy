from fastapi import APIRouter

from .visual_knowledge import (
    Exhibit,
    HistoricalObject,
    RelatedPassage,
    TimelineEvent,
    visual_store,
)

router = APIRouter(prefix="/api/v1/visual", tags=["visual-knowledge"])


@router.get("/objects", response_model=list[HistoricalObject])
def list_objects(manuscript_id: str | None = None) -> list[HistoricalObject]:
    return visual_store.list_objects(manuscript_id)


@router.post("/objects", response_model=HistoricalObject)
def put_object(item: HistoricalObject) -> HistoricalObject:
    return visual_store.put_object(item)


@router.get("/timeline", response_model=list[TimelineEvent])
def timeline() -> list[TimelineEvent]:
    return visual_store.list_events()


@router.post("/timeline", response_model=TimelineEvent)
def put_timeline_event(item: TimelineEvent) -> TimelineEvent:
    return visual_store.put_event(item)


@router.get("/exhibits", response_model=list[Exhibit])
def exhibits() -> list[Exhibit]:
    return visual_store.list_exhibits()


@router.post("/exhibits", response_model=Exhibit)
def put_exhibit(item: Exhibit) -> Exhibit:
    return visual_store.put_exhibit(item)


@router.get("/relations", response_model=list[RelatedPassage])
def relations() -> list[RelatedPassage]:
    return visual_store.relations()


@router.post("/relations", response_model=RelatedPassage)
def add_relation(item: RelatedPassage) -> RelatedPassage:
    return visual_store.add_relation(item)
