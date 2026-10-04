from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from .auth import Role, require_roles
from .comparison import word_differences
from .repository import repository
from .scholarly_export import iiif_supplementing_annotation_page, research_bundle, tei_xml
from .scholarship import (
    VariantReading,
    Witness,
    WitnessAlignment,
    Work,
    scholarship_store,
)

router = APIRouter(prefix="/api/v1/scholarship", tags=["scholarship"])
editor_write = Depends(require_roles(Role.REVIEWER, Role.ADMIN))


@router.post("/works", response_model=Work)
def put_work(item: Work, actor: Annotated[dict, editor_write]) -> Work:
    return scholarship_store.put_work(item, actor=actor["sub"])


@router.post("/witnesses", response_model=Witness)
def put_witness(item: Witness, actor: Annotated[dict, editor_write]) -> Witness:
    try:
        return scholarship_store.put_witness(item, actor=actor["sub"])
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/works/{work_id}/witnesses", response_model=list[Witness])
def witnesses(work_id: str) -> list[Witness]:
    return scholarship_store.witnesses(work_id)


@router.post("/variants", response_model=VariantReading)
def put_variant(item: VariantReading, actor: Annotated[dict, editor_write]) -> VariantReading:
    try:
        return scholarship_store.put_variant(item, actor=actor["sub"])
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/works/{work_id}/variants", response_model=list[VariantReading])
def variants(work_id: str) -> list[VariantReading]:
    return scholarship_store.variants(work_id)


@router.get("/works/{work_id}/variants/{variant_id}/compare")
def compare_variant(work_id: str, variant_id: str, left: str, right: str) -> dict:
    variant = next((v for v in scholarship_store.variants(work_id) if v.id == variant_id), None)
    if variant is None:
        raise HTTPException(404, "Variant not found")
    if left == right or left not in variant.readings or right not in variant.readings:
        raise HTTPException(422, "Choose two distinct documented witnesses of this variant")
    return {"work_id": work_id, "locus": variant.locus, "sources": variant.sources,
            "left_witness": left, "right_witness": right,
            "differences": word_differences(variant.readings[left], variant.readings[right]),
            "method": "literal-word-diff", "critical_reading": None}


@router.post("/alignments", response_model=WitnessAlignment)
def put_alignment(item: WitnessAlignment, actor: Annotated[dict, editor_write]) -> WitnessAlignment:
    try:
        return scholarship_store.put_alignment(item, actor=actor["sub"])
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


def _manuscript(manuscript_id: str):
    item = repository.get(manuscript_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Manuscript not found")
    return item


@router.get("/manuscripts/{manuscript_id}/tei")
def export_tei(manuscript_id: str) -> Response:
    return Response(tei_xml(_manuscript(manuscript_id)), media_type="application/xml")


@router.get("/manuscripts/{manuscript_id}/pages/{page_id}/iiif-annotations")
def export_iiif_annotations(manuscript_id: str, page_id: str) -> dict:
    return iiif_supplementing_annotation_page(_manuscript(manuscript_id), page_id)


@router.get("/manuscripts/{manuscript_id}/research-bundle")
def export_research_bundle(manuscript_id: str) -> Response:
    return Response(research_bundle(_manuscript(manuscript_id)), media_type="application/json")
