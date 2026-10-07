import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from .auth import Role, require_roles
from .living import LayerKind, LivingLayer, ReviewState
from .living_routes import check_anchor
from .living_store import RevisionConflict
from .ottoman import OttomanRepository
from .ottoman_academy import (
    AcademyRepository,
    DictionaryEntry,
    ReadingExercise,
    normalize_answer,
    validate_exercise,
)
from .ottoman_routes import ottoman_repository
from .repository import repository

router = APIRouter(prefix="/api/v1/ottoman", tags=["ottoman-academy"])


@lru_cache(maxsize=1)
def academy_repository() -> AcademyRepository:
    return AcademyRepository(Path(os.getenv("ACADEMY_METADATA_PATH", "./data/academy.sqlite3")))


@router.get("/dictionary", response_model=list[DictionaryEntry])
def dictionary(store: Annotated[AcademyRepository, Depends(academy_repository)],
               q: str = Query(min_length=1, max_length=200)):
    return store.entries(q)


@router.post("/dictionary", response_model=DictionaryEntry)
def add_entry(item: DictionaryEntry,
              actor: Annotated[dict, Depends(require_roles(Role.EDITOR, Role.REVIEWER, Role.ADMIN))],
              store: Annotated[AcademyRepository, Depends(academy_repository)]):
    if item.state == ReviewState.VERIFIED and (actor["role"] not in {Role.REVIEWER, Role.ADMIN} or item.provenance.reviewer != actor["sub"]):
        raise HTTPException(403, "Dictionary verification requires the authenticated reviewer")
    proxy = LivingLayer(kind=LayerKind.ANNOTATIONS, data={"dictionary": True}, provenance=item.provenance)
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
        return store.append_entry(item, actor=actor["sub"])
    except RevisionConflict as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/manuscripts/{manuscript_id}/pages/{page_id}/exercises", response_model=ReadingExercise)
def create_exercise(manuscript_id: str, page_id: str, item: ReadingExercise,
                    actor: Annotated[dict, Depends(require_roles(Role.REVIEWER, Role.ADMIN))],
                    store: Annotated[AcademyRepository, Depends(academy_repository)],
                    pipeline: Annotated[OttomanRepository, Depends(ottoman_repository)]):
    try:
        chain = validate_exercise(item, pipeline.history(manuscript_id, page_id))
        manuscript = repository.get(manuscript_id)
        if manuscript is None or not manuscript.license or item.source_license != manuscript.license:
            raise ValueError("Teaching material requires the recorded manuscript rights/license")
        check_anchor(LivingLayer(kind=LayerKind.ANNOTATIONS, data={"exercise": True}, provenance=chain[0].provenance))
        return store.put_exercise(item, manuscript_id, page_id, actor=actor["sub"])
    except RevisionConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/manuscripts/{manuscript_id}/pages/{page_id}/exercises")
def exercises(manuscript_id: str, page_id: str,
              store: Annotated[AcademyRepository, Depends(academy_repository)]):
    # Do not disclose answer texts in the question listing; original image stays in the reader.
    return [{"id": e.id, "title": e.title, "rights_note": e.rights_note,
             "source_license": e.source_license} for e in store.exercises(manuscript_id, page_id)]


class Attempt(BaseModel):
    text: str = Field(max_length=100_000)
    reveal_step: int = Field(default=0, ge=0, le=4)


@router.post("/manuscripts/{manuscript_id}/pages/{page_id}/exercises/{exercise_id}/attempt")
def attempt(manuscript_id: str, page_id: str, exercise_id: str, item: Attempt,
            store: Annotated[AcademyRepository, Depends(academy_repository)],
            pipeline: Annotated[OttomanRepository, Depends(ottoman_repository)]):
    exercise = next((e for e in store.exercises(manuscript_id, page_id) if e.id == exercise_id), None)
    if exercise is None:
        raise HTTPException(404, "Exercise not found")
    chain = validate_exercise(exercise, pipeline.history(manuscript_id, page_id))
    exact = normalize_answer(item.text) == normalize_answer(chain[0].text)
    return {"exact_match": exact, "grading_method": "NFC-whitespace-exact",
            "message": "Exact match is practice feedback, not a scholarly verification.",
            "revealed": [{"stage": r.stage, "text": r.text, "provenance": r.provenance}
                         for r in chain[:item.reveal_step]], "available_steps": len(chain)}
