from fastapi import APIRouter, HTTPException, Response

from .repository import repository
from .scholarship import (
    VariantReading,
    Witness,
    WitnessAlignment,
    Work,
    scholarship_store,
)
from .scholarly_export import iiif_supplementing_annotation_page, research_bundle, tei_xml

router = APIRouter(prefix="/api/v1/scholarship", tags=["scholarship"])


@router.post("/works", response_model=Work)
def put_work(item: Work) -> Work:
    return scholarship_store.put_work(item)


@router.post("/witnesses", response_model=Witness)
def put_witness(item: Witness) -> Witness:
    return scholarship_store.put_witness(item)


@router.get("/works/{work_id}/witnesses", response_model=list[Witness])
def witnesses(work_id: str) -> list[Witness]:
    return scholarship_store.witnesses(work_id)


@router.post("/variants", response_model=VariantReading)
def put_variant(item: VariantReading) -> VariantReading:
    return scholarship_store.put_variant(item)


@router.get("/works/{work_id}/variants", response_model=list[VariantReading])
def variants(work_id: str) -> list[VariantReading]:
    return scholarship_store.variants(work_id)


@router.post("/alignments", response_model=WitnessAlignment)
def put_alignment(item: WitnessAlignment) -> WitnessAlignment:
    return scholarship_store.put_alignment(item)


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
