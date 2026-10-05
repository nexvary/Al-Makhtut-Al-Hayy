import pytest
from pydantic import ValidationError

from app.living import LayerProvenance, SourceAnchor
from app.living_store import RevisionConflict
from app.museum import EvidenceClass, Exhibition, MuseumAsset, MuseumObject, MuseumRepository


def provenance():
    from app.citations import CitationTarget
    return LayerProvenance(source=SourceAnchor(manuscript_id="synthetic-museum",page_id="p",region_id="drawing"),
                           extraction_method="manual", evidence=[CitationTarget(manuscript_id="synthetic-museum",page_id="p",region_id="drawing")])


def test_3d_reconstruction_never_becomes_original_evidence():
    with pytest.raises(ValidationError):
        MuseumAsset(kind="model_3d",url="https://example.org/model.glb",license="test-only",
                    attribution="Synthetic fixture",evidence_class=EvidenceClass.DOCUMENTED,provenance=provenance())
    with pytest.raises(ValidationError):
        MuseumObject(object_id="fixture",name="Synthetic tool",description="Synthetic test object",
                     evidence_class=EvidenceClass.INTERPRETIVE,original_illustration_region="drawing",provenance=provenance())


def test_museum_preserves_source_and_validates_exhibit_members(tmp_path):
    store = MuseumRepository(tmp_path / "museum.sqlite3")
    obj = MuseumObject(object_id="fixture",name="Synthetic tool",description="Synthetic description",
                       evidence_class=EvidenceClass.DOCUMENTED,original_illustration_region="drawing",provenance=provenance())
    exhibit = Exhibition(exhibition_id="exhibit",title="Synthetic exhibit",theme="engineering",
                         description="Synthetic test material",object_ids=[obj.object_id],provenance=provenance())
    with pytest.raises(ValueError):
        store.append(exhibit,actor="reviewer")
    store.append(obj,actor="reviewer")
    store.append(exhibit,actor="reviewer")
    assert MuseumRepository(store.path).current("object")[0].provenance.source.region_id == "drawing"
    with pytest.raises(RevisionConflict):
        store.append(obj,actor="reviewer")


def test_museum_api_requires_curator_and_valid_source(tmp_path):
    from fastapi.testclient import TestClient

    from app.auth import Role, issue_token
    from app.main import app
    from app.models import Manuscript, Page, Region
    from app.museum_routes import museum_repository
    from app.repository import repository

    store = MuseumRepository(tmp_path / "museum.sqlite3")
    app.dependency_overrides[museum_repository] = lambda: store
    repository.put(Manuscript(id="synthetic-museum",title="Synthetic museum fixture",pages=[Page(id="p",sequence=1,image="source.png",regions=[Region(id="drawing")])]))
    item = MuseumObject(object_id="api-object",name="Synthetic object",description="Synthetic description",evidence_class=EvidenceClass.DOCUMENTED,original_illustration_region="drawing",provenance=provenance())
    try:
        with TestClient(app) as client:
            body=item.model_dump(mode="json")
            editor={"Authorization":"Bearer "+issue_token("editor",Role.EDITOR)}
            reviewer={"Authorization":"Bearer "+issue_token("reviewer",Role.REVIEWER)}
            assert client.post("/api/v1/museum/objects",json=body,headers=editor).status_code==403
            assert client.post("/api/v1/museum/objects",json=body,headers=reviewer).status_code==200
            exhibit=Exhibition(exhibition_id="api-exhibit",title="Synthetic museum",theme="engineering",description="Synthetic description",object_ids=[item.object_id],provenance=provenance())
            assert client.post("/api/v1/museum/exhibitions",json=exhibit.model_dump(mode="json"),headers=reviewer).status_code==200
            assert client.get("/api/v1/museum/exhibitions/api-exhibit").json()["objects"][0]["evidence_class"]=="documented_evidence"
    finally:
        app.dependency_overrides.pop(museum_repository)
