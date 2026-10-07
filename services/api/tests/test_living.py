import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.auth import Role, issue_token
from app.living import LayerKind, LayerProvenance, LivingLayer, ReviewState, SourceAnchor
from app.living_routes import layer_repository
from app.living_store import RevisionConflict, SqliteLayerRepository
from app.main import app
from app.models import Manuscript, Page, Point, Region
from app.repository import repository


def layer(**overrides):
    data = {"kind": LayerKind.DRAFT, "text": "نص تجريبي غير تاريخي",
                "provenance": LayerProvenance(
                    source=SourceAnchor(manuscript_id="living-m", page_id="living-p", region_id="r"),
                    extraction_method="manual")}
    data.update(overrides)
    return LivingLayer(**data)


@pytest.fixture
def api(tmp_path):
    store = SqliteLayerRepository(tmp_path / "layers.sqlite3")
    app.dependency_overrides[layer_repository] = lambda: store
    repository.put(Manuscript(id="living-m", title="Test fixture", pages=[
        Page(id="living-p", sequence=1, image="original.png", image_width=100,
             image_height=200, regions=[Region(id="r", polygon=[Point(x=1, y=1)])])]))
    with TestClient(app) as client:
        yield client, store
    app.dependency_overrides.pop(layer_repository)


def header(role=Role.TRANSCRIBER, actor="editor"):
    return {"Authorization": "Bearer " + issue_token(actor, role)}


def test_machine_cannot_promote_itself():
    with pytest.raises(ValidationError):
        layer(kind=LayerKind.MACHINE, state=ReviewState.VERIFIED)
    with pytest.raises(ValidationError):
        layer(state=ReviewState.VERIFIED)
    with pytest.raises(ValidationError):
        layer(state=ReviewState.MACHINE)


def test_restart_history_conflict_and_atomic_audit(tmp_path):
    path = tmp_path / "layers.sqlite3"
    store = SqliteLayerRepository(path)
    first = layer()
    store.append(first, actor="a")
    fresh = SqliteLayerRepository(path)
    assert fresh.history("living-m", "living-p")[0].id == first.id
    with pytest.raises(RevisionConflict):
        fresh.append(layer(), actor="b")
    assert len(fresh.audit()) == 1
    second = layer(parent_revision_id=first.id, text="تصحيح تجريبي")
    fresh.append(second, actor="b")
    history = fresh.history("living-m", "living-p")
    assert history[0].text == first.text
    assert fresh.audit()[-1]["previous_revision_id"] == first.id
    with pytest.raises(RevisionConflict):
        fresh.append(second, actor="b")
    assert len(fresh.audit()) == 2


def test_authorization_original_and_source_integrity(api):
    client, store = api
    body = layer().model_dump(mode="json")
    assert client.post("/api/v1/living/layers", json=body).status_code == 401
    assert client.post("/api/v1/living/layers", json=body, headers=header(Role.VIEWER)).status_code == 403
    original = layer(kind=LayerKind.ORIGINAL, asset_uri="changed.png")
    assert client.post("/api/v1/living/layers", json=original.model_dump(mode="json"),
                       headers=header()).status_code == 409
    body["provenance"]["source"]["page_id"] = "missing"
    assert client.post("/api/v1/living/layers", json=body, headers=header()).status_code == 404
    assert store.audit() == []


def test_verification_actor_and_bounded_coordinates(api):
    client, _ = api
    provenance = layer().provenance.model_copy(update={"reviewer": "reviewer"})
    verified = layer(kind=LayerKind.VERIFIED, state=ReviewState.VERIFIED, provenance=provenance)
    body = verified.model_dump(mode="json")
    assert client.post("/api/v1/living/layers", json=body, headers=header()).status_code == 403
    assert client.post("/api/v1/living/layers", json=body,
                       headers=header(Role.REVIEWER, "someone-else")).status_code == 403
    body["provenance"]["source"]["coordinates"] = [{"x": 101, "y": 2}]
    assert client.post("/api/v1/living/layers", json=body,
                       headers=header(Role.REVIEWER, "reviewer")).status_code == 422
    result = client.post("/api/v1/living/layers", json=verified.model_dump(mode="json"),
                         headers=header(Role.REVIEWER, "reviewer"))
    assert result.status_code == 200
    response = client.get("/api/v1/living/manuscripts/living-m/pages/living-p/layers").json()
    assert response["original_image"] == "original.png"
    assert response["layers"][0]["state"] == "verified"
    assert client.get("/api/v1/living/audit").status_code == 401


def test_schema_matches_runtime():
    path = Path(__file__).parents[3] / "packages/manuscript-schema/living-layer.schema.json"
    assert json.loads(path.read_text()) == LivingLayer.model_json_schema()


def test_source_repository_survives_restart(tmp_path):
    from app.repository import ManuscriptRepository
    path = tmp_path / "source.sqlite3"
    first = ManuscriptRepository(path)
    first.put(Manuscript(id="persistent", title="Source fixture"))
    assert ManuscriptRepository(path).get("persistent").title == "Source fixture"


def test_witness_requires_work_and_survives_restart(tmp_path):
    from app.scholarship import (
        BibliographicMetadata,
        SqliteScholarshipStore,
        Witness,
        WitnessKind,
        Work,
    )
    path = tmp_path / "work.sqlite3"
    store = SqliteScholarshipStore(path)
    witness = Witness(id="w", work_id="work", kind=WitnessKind.MANUSCRIPT,
                      label="Test witness", bibliography=BibliographicMetadata(title="Test source"))
    with pytest.raises(ValueError):
        store.put_witness(witness)
    store.put_work(Work(id="work", title="Work fixture"))
    store.put_witness(witness)
    assert SqliteScholarshipStore(path).get_witness("w").work_id == "work"


def test_legacy_editorial_cannot_self_verify():
    with TestClient(app) as client:
        request = {"manuscript_id": "x", "page_id": "y", "region_id": "z",
                   "layer_kind": "verified_transcription", "text": "Fixture",
                   "state": "verified", "created_by": "forged-reviewer"}
        assert client.post("/api/v1/editorial/revisions", json=request,
                           headers=header(Role.TRANSCRIBER)).status_code == 403


def test_source_coordinates_cannot_store_nonfinite_values():
    with pytest.raises(ValidationError):
        Point(x=float("nan"),y=1)
    with pytest.raises(ValidationError):
        Point(x=1,y=float("inf"))
