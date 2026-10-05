import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.academy_routes import academy_repository
from app.auth import Role, issue_token
from app.living import LayerProvenance, ReviewState, SourceAnchor
from app.living_store import RevisionConflict
from app.main import app
from app.models import Manuscript, Page
from app.ottoman import OttomanRecord, OttomanRepository, OttomanStage
from app.ottoman_academy import (
    AcademyRepository,
    DictionaryEntry,
    ReadingExercise,
    validate_exercise,
)
from app.ottoman_routes import ottoman_repository
from app.repository import repository


def provenance():
    return LayerProvenance(source=SourceAnchor(manuscript_id="academy-test", page_id="p"),
                           extraction_method="manual", reviewer="reviewer")


def test_dictionary_requires_evidence_for_etymology_and_retains_history(tmp_path):
    store = AcademyRepository(tmp_path / "academy.sqlite3")
    with pytest.raises(ValidationError):
        DictionaryEntry(entry_id="word", spelling="Fixture", linguistic_origin="unverified origin", provenance=provenance())
    first = DictionaryEntry(entry_id="word", spelling="Fixture", arabic="Synthetic meaning", provenance=provenance())
    store.append_entry(first, actor="editor")
    with pytest.raises(RevisionConflict):
        store.append_entry(DictionaryEntry(entry_id="word", spelling="Fixture", provenance=provenance()), actor="editor")
    assert AcademyRepository(store.path).entries("Fixture")[0].arabic == "Synthetic meaning"


def test_exercises_never_teach_machine_output():
    source = OttomanRecord(stage=OttomanStage.TRANSCRIPTION, text="Fixture", provenance=provenance())
    exercise = ReadingExercise(title="Fixture reading", transcription_revision=source.id,
                               rights_note="Synthetic test text", source_license="test-only")
    with pytest.raises(ValueError):
        validate_exercise(exercise, [source])
    source.state = ReviewState.VERIFIED
    assert validate_exercise(exercise, [source])[0].text == "Fixture"


def test_exercise_reveal_rights_roles_and_source(tmp_path):
    academy, pipeline = AcademyRepository(tmp_path / "academy.sqlite3"), OttomanRepository(tmp_path / "pipeline.sqlite3")
    app.dependency_overrides[academy_repository] = lambda: academy
    app.dependency_overrides[ottoman_repository] = lambda: pipeline
    repository.put(Manuscript(id="academy-test", title="Synthetic fixture", license="test-only",
                             pages=[Page(id="p", sequence=1, image="original.png")]))
    source = OttomanRecord(stage=OttomanStage.TRANSCRIPTION, state=ReviewState.VERIFIED, text="Fixture original", provenance=provenance())
    pipeline.append(source, actor="reviewer")
    latin = OttomanRecord(stage=OttomanStage.TRANSLITERATION, state=ReviewState.VERIFIED, text="Fixture Latin", provenance=provenance(), input_revision_id=source.id)
    pipeline.append(latin, actor="reviewer")
    exercise = ReadingExercise(title="Synthetic reading exercise", transcription_revision=source.id,
                               transliteration_revision=latin.id, rights_note="Synthetic QA material", source_license="test-only")
    url = "/api/v1/ottoman/manuscripts/academy-test/pages/p/exercises"
    headers = {"Authorization": "Bearer " + issue_token("reviewer", Role.REVIEWER)}
    try:
        with TestClient(app) as client:
            assert client.post(url, json=exercise.model_dump(mode="json")).status_code == 401
            assert client.post(url, json=exercise.model_dump(mode="json"), headers=headers).status_code == 200
            assert "Fixture original" not in client.get(url).text
            attempt_url = f"{url}/{exercise.id}/attempt"
            result = client.post(attempt_url, json={"text":"Fixture   original", "reveal_step":0}).json()
            assert result["exact_match"] and not result["revealed"]
            result = client.post(attempt_url, json={"text":"wrong", "reveal_step":2}).json()
            assert not result["exact_match"] and [r["text"] for r in result["revealed"]] == ["Fixture original", "Fixture Latin"]
            wrong = exercise.model_copy(update={"id":"wrong-license", "source_license":"invented"})
            assert client.post(url, json=wrong.model_dump(mode="json"), headers=headers).status_code == 422
            assert client.post(url, json=exercise.model_dump(mode="json"), headers=headers).status_code == 409
    finally:
        app.dependency_overrides.pop(academy_repository)
        app.dependency_overrides.pop(ottoman_repository)
