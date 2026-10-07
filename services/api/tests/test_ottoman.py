import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.auth import Role, issue_token
from app.living import LayerProvenance, ReviewState, SourceAnchor
from app.living_store import RevisionConflict
from app.main import app
from app.models import Manuscript, Page
from app.ottoman import OttomanRecord, OttomanRepository, OttomanStage
from app.ottoman_routes import ottoman_repository
from app.repository import repository


def record(stage=OttomanStage.TRANSCRIPTION, **kwargs):
    return OttomanRecord(stage=stage, text="Synthetic fixture; not Ottoman scholarship",
                         provenance=LayerProvenance(source=SourceAnchor(manuscript_id="ota-test", page_id="p"),
                                                    extraction_method="manual"), **kwargs)


def test_ottoman_stages_do_not_mix_or_self_verify():
    with pytest.raises(ValidationError):
        record(OttomanStage.HTR, state=ReviewState.DRAFT)
    with pytest.raises(ValidationError):
        record(OttomanStage.TRANSLITERATION)
    with pytest.raises(ValidationError):
        record(OttomanStage.LAYOUT, layout={"regions": []})
    with pytest.raises(ValidationError):
        record(state=ReviewState.VERIFIED)


def test_pipeline_persistence_dependencies_and_immutable_history(tmp_path):
    store = OttomanRepository(tmp_path / "ota.sqlite3")
    source = record()
    store.append(source, actor="editor")
    latin = record(OttomanStage.TRANSLITERATION, input_revision_id=source.id)
    store.append(latin, actor="editor")
    modern = record(OttomanStage.MODERNIZATION, input_revision_id=latin.id)
    store.append(modern, actor="editor")
    translation = record(OttomanStage.ARABIC, input_revision_id=modern.id)
    store.append(translation, actor="editor")
    assert len(OttomanRepository(store.path).history("ota-test", "p")) == 4
    with pytest.raises(RevisionConflict):
        store.append(record(), actor="editor")
    with pytest.raises(ValueError):
        store.append(record(OttomanStage.ENGLISH, input_revision_id=source.id), actor="editor")
    foreign = record(OttomanStage.ENGLISH, input_revision_id=modern.id)
    foreign.provenance.source.page_id = "elsewhere"
    with pytest.raises(ValueError):
        store.append(foreign, actor="editor")
    assert len(store.history("ota-test", "p")) == 4


def test_verified_translation_cannot_hide_unreviewed_input(tmp_path):
    store = OttomanRepository(tmp_path / "ota.sqlite3")
    source = record()
    store.append(source, actor="editor")
    latin = record(OttomanStage.TRANSLITERATION, input_revision_id=source.id)
    latin.state = ReviewState.VERIFIED
    latin.provenance.reviewer = "reviewer"
    with pytest.raises(ValueError):
        store.append(latin, actor="reviewer")
    assert len(store.history("ota-test", "p")) == 1


def test_ottoman_api_checks_roles_and_original(tmp_path):
    store = OttomanRepository(tmp_path / "ota.sqlite3")
    app.dependency_overrides[ottoman_repository] = lambda: store
    repository.put(Manuscript(id="ota-test", title="Synthetic fixture", pages=[
        Page(id="p", sequence=1, image="original-ota.png")]))
    try:
        with TestClient(app) as client:
            body = record().model_dump(mode="json")
            assert client.post("/api/v1/ottoman/revisions", json=body).status_code == 401
            headers = {"Authorization": "Bearer " + issue_token("editor", Role.EDITOR)}
            assert client.post("/api/v1/ottoman/revisions", json=body, headers=headers).status_code == 200
            body["id"] = "new-revision"
            body["state"] = "verified"
            body["provenance"]["reviewer"] = "editor"
            assert client.post("/api/v1/ottoman/revisions", json=body, headers=headers).status_code == 403
            response = client.get("/api/v1/ottoman/manuscripts/ota-test/pages/p").json()
            assert response["original_image"] == "original-ota.png"
            assert response["revisions"][0]["stage"] == "transcription"
            assert all(not s["automatic_provider_available"] for s in client.get("/api/v1/ottoman/stages").json())
    finally:
        app.dependency_overrides.pop(ottoman_repository)


def test_ottoman_schema_matches_runtime():
    path = Path(__file__).parents[3] / "packages/manuscript-schema/ottoman-record.schema.json"
    assert json.loads(path.read_text()) == OttomanRecord.model_json_schema()
