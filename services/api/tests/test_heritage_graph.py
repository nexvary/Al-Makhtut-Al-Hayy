import pytest
from pydantic import ValidationError

from app.heritage_graph import (
    EntityKind,
    GraphRepository,
    HistoricalEntity,
    HistoricalInterval,
    HistoricalLocation,
    HistoricalRelation,
)
from app.living import LayerProvenance, SourceAnchor
from app.living_store import RevisionConflict


def source():
    return LayerProvenance(source=SourceAnchor(manuscript_id="synthetic",page_id="p"), extraction_method="manual")


def test_graph_persistence_neighbors_and_dangling_links(tmp_path):
    store = GraphRepository(tmp_path / "graph.sqlite3")
    author = HistoricalEntity(entity_id="author", name="Synthetic scholar", kind=EntityKind.SCHOLAR, provenance=source())
    work = HistoricalEntity(entity_id="work", name="Synthetic work", kind=EntityKind.WORK, provenance=source())
    edge = HistoricalRelation(relation_id="authorship", subject="author", predicate="authored", object="work", provenance=source())
    with pytest.raises(ValueError):
        store.append(edge, actor="editor")
    store.append(author, actor="editor")
    store.append(work, actor="editor")
    store.append(edge, actor="editor")
    graph = GraphRepository(store.path).neighbors("author")
    assert {e.entity_id for e in graph["entities"]} == {"author", "work"}
    assert graph["relations"][0].predicate == "authored"
    with pytest.raises(RevisionConflict):
        store.append(author, actor="editor")


def test_time_machine_and_geojson_use_documented_intervals(tmp_path):
    store = GraphRepository(tmp_path / "graph.sqlite3")
    node = HistoricalEntity(entity_id="place", name="Synthetic location", kind=EntityKind.PLACE,
                            interval=HistoricalInterval(start_year=1000,end_year=1050,circa=True),
                            location=HistoricalLocation(latitude=20,longitude=30,label="Synthetic coordinates"), provenance=source())
    unknown = HistoricalEntity(entity_id="undated", name="Unknown date fixture", kind=EntityKind.EVENT, provenance=source())
    store.append(node, actor="editor")
    store.append(unknown, actor="editor")
    assert [e.entity_id for e in store.time_slice(1050,1100)] == ["place"]
    assert not store.time_slice(1051,1100)
    feature = store.geojson(1000,1000)["features"][0]
    assert feature["geometry"]["coordinates"] == [30,20]
    assert feature["properties"]["approximate"]
    with pytest.raises(ValueError):
        store.time_slice(1200,1000)
    with pytest.raises(ValidationError):
        HistoricalInterval(start_year=10,end_year=1)
    with pytest.raises(ValidationError):
        HistoricalLocation(latitude=float("nan"),longitude=0,label="Invalid")


def test_graph_api_authorization_source_and_interval_validation(tmp_path):
    from fastapi.testclient import TestClient

    from app.auth import Role, issue_token
    from app.heritage_routes import graph_repository
    from app.main import app
    from app.models import Manuscript, Page
    from app.repository import repository

    store = GraphRepository(tmp_path / "graph.sqlite3")
    app.dependency_overrides[graph_repository] = lambda: store
    repository.put(Manuscript(id="synthetic", title="QA graph fixture", pages=[Page(id="p",sequence=1,image="original.png")]))
    item = HistoricalEntity(entity_id="api-fixture",name="API fixture",kind=EntityKind.EVENT,provenance=source())
    headers = {"Authorization":"Bearer " + issue_token("editor",Role.EDITOR)}
    try:
        with TestClient(app) as client:
            body = item.model_dump(mode="json")
            assert client.post("/api/v1/heritage/entities",json=body).status_code == 401
            assert client.post("/api/v1/heritage/entities",json=body,headers=headers).status_code == 200
            assert client.get("/api/v1/heritage/entities/api-fixture").json()["entities"][0]["name"] == "API fixture"
            body["id"] = "forged"
            body["state"] = "verified"
            body["provenance"]["reviewer"] = "editor"
            assert client.post("/api/v1/heritage/entities",json=body,headers=headers).status_code == 403
            assert client.get("/api/v1/heritage/time-machine?start=1200&end=1000").status_code == 422
            assert client.get("/api/v1/heritage/map?end=1000").status_code == 422
    finally:
        app.dependency_overrides.pop(graph_repository)
